import json
import re
from db.agent_db import AgentDB
from db.shared_db import SharedDB
from agents.llm import chat
from agents.prompts import (
    build_persona, build_game_state, build_private_knowledge,
    build_public_history, FREECHAT_TASK, PITCH_TASK, VOTE_TASK,
    NIGHT_KILL_TASK, NIGHT_INVESTIGATE_TASK, NIGHT_HEAL_TASK, THOUGHT_TASK,
)


class Agent:
    def __init__(self, player_id: int, name: str, role: str, personality: str,
                 agent_db: AgentDB, shared_db: SharedDB):
        self.id = player_id
        self.name = name
        self.role = role
        self.personality = personality
        self.agent_db = agent_db
        self.shared_db = shared_db
        self.game_id: int = 0
        self.last_healed: int | None = None  # for doctor role

    def set_game(self, game_id: int):
        self.game_id = game_id

    async def _build_system_prompt(self, round_num: int, phase: str) -> str:
        persona = build_persona(self.name, self.role, self.personality)
        alive = await self.shared_db.get_alive_players(self.game_id)
        all_players = await self.shared_db.get_players(self.game_id)
        eliminated = [p for p in all_players if not p['alive']]
        player_names = {p['id']: p['name'] for p in all_players}

        game_state = build_game_state(round_num, phase, alive, eliminated)

        private_data = await self.agent_db.get_all(self.game_id)
        private_knowledge = build_private_knowledge(
            private_data['known_facts'], private_data['suspicions'], player_names
        )

        freechats = await self.shared_db.get_all_freechats(self.game_id)
        pitches = await self.shared_db.get_all_pitches(self.game_id)
        vote_results = await self.shared_db.get_vote_results(self.game_id)
        night_results = await self.shared_db.get_night_results(self.game_id)
        public_history = build_public_history(freechats, pitches, vote_results, night_results, player_names)

        return f"{persona}\n\n{game_state}\n\n{private_knowledge}\n\n{public_history}"

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Try extracting from markdown code block
        match = re.search(r'```(?:json)?\s*(.*?)```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        # Try finding first { to last }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
        return {}

    async def think(self, round_num: int, phase: str, alive_player_ids: list[int]) -> dict:
        system = await self._build_system_prompt(round_num, phase)
        all_players = await self.shared_db.get_players(self.game_id)
        player_names = {p['id']: p['name'] for p in all_players}

        suspicion_parts = []
        for pid in alive_player_ids:
            if pid != self.id:
                suspicion_parts.append(f'"{pid}": <0.0 to 1.0 for {player_names.get(pid, "?")}>')
        suspicion_template = ", ".join(suspicion_parts)

        task = THOUGHT_TASK.format(suspicion_template=suspicion_template)

        response = await chat(system, [{"role": "user", "content": task}], max_tokens=256)
        data = self._parse_json(response)

        thought = data.get("thought", response[:200])
        strategy = data.get("strategy", "")
        suspicions = data.get("suspicions", {})

        await self.agent_db.add_thought(self.game_id, round_num, phase, thought)
        await self.agent_db.add_strategy(self.game_id, round_num, phase, strategy)

        for target_str, level in suspicions.items():
            try:
                target_id = int(target_str)
                level_f = float(level)
                await self.agent_db.add_suspicion(self.game_id, round_num, target_id, level_f)
            except (ValueError, TypeError):
                pass

        return {"thought": thought, "suspicions": suspicions, "strategy": strategy}

    async def freechat(self, round_num: int, other_name: str, conversation_so_far: list[dict]) -> str:
        system = await self._build_system_prompt(round_num, "freechat")

        context = ""
        if conversation_so_far:
            context = "Conversation so far:\n" + "\n".join(
                f"  {m['sender']}: {m['content']}" for m in conversation_so_far
            )

        task = FREECHAT_TASK.format(other_name=other_name, context=context)
        messages = [{"role": "user", "content": task}]

        response = await chat(system, messages, max_tokens=128)
        result = response.strip().strip('"')
        return result[:250]

    async def pitch(self, round_num: int) -> str:
        system = await self._build_system_prompt(round_num, "pitch")
        messages = [{"role": "user", "content": PITCH_TASK}]
        response = await chat(system, messages, max_tokens=256)
        result = response.strip().strip('"')
        return result[:500]

    async def vote(self, round_num: int, alive_player_ids: list[int]) -> int:
        system = await self._build_system_prompt(round_num, "vote")
        messages = [{"role": "user", "content": VOTE_TASK}]
        response = await chat(system, messages, max_tokens=256)
        data = self._parse_json(response)

        target = data.get("vote_for")
        reasoning = data.get("reasoning", "")

        if target is not None:
            target = int(target)
        # Validate: can't vote for self, must be alive
        if target == self.id or target not in alive_player_ids:
            # Pick a random valid target
            import random
            valid = [p for p in alive_player_ids if p != self.id]
            target = random.choice(valid) if valid else alive_player_ids[0]

        await self.agent_db.add_thought(self.game_id, round_num, "vote",
                                         f"Voted for #{target}: {reasoning}")
        return target

    async def night_kill(self, round_num: int, alive_player_ids: list[int]) -> int:
        system = await self._build_system_prompt(round_num, "night")
        messages = [{"role": "user", "content": NIGHT_KILL_TASK}]
        response = await chat(system, messages, max_tokens=256)
        data = self._parse_json(response)

        target = data.get("kill_target")
        reasoning = data.get("reasoning", "")

        if target is not None:
            target = int(target)
        valid = [p for p in alive_player_ids if p != self.id]
        if target not in valid:
            import random
            target = random.choice(valid)

        await self.agent_db.add_thought(self.game_id, round_num, "night_kill",
                                         f"Chose to kill #{target}: {reasoning}")
        return target

    async def night_investigate(self, round_num: int, alive_player_ids: list[int]) -> int:
        system = await self._build_system_prompt(round_num, "night")
        messages = [{"role": "user", "content": NIGHT_INVESTIGATE_TASK}]
        response = await chat(system, messages, max_tokens=256)
        data = self._parse_json(response)

        target = data.get("investigate_target")
        reasoning = data.get("reasoning", "")

        if target is not None:
            target = int(target)
        valid = [p for p in alive_player_ids if p != self.id]
        if target not in valid:
            import random
            target = random.choice(valid)

        await self.agent_db.add_thought(self.game_id, round_num, "night_investigate",
                                         f"Investigating #{target}: {reasoning}")
        return target

    async def night_heal(self, round_num: int, alive_player_ids: list[int]) -> int:
        system = await self._build_system_prompt(round_num, "night")

        heal_constraint = ""
        if self.last_healed is not None:
            all_players = await self.shared_db.get_players(self.game_id)
            names = {p['id']: p['name'] for p in all_players}
            heal_constraint = f"You CANNOT heal {names.get(self.last_healed, '?')} (#{self.last_healed}) — you healed them last night."

        task = NIGHT_HEAL_TASK.format(heal_constraint=heal_constraint)
        messages = [{"role": "user", "content": task}]
        response = await chat(system, messages, max_tokens=256)
        data = self._parse_json(response)

        target = data.get("heal_target")
        reasoning = data.get("reasoning", "")

        if target is not None:
            target = int(target)
        # Validate
        if target == self.last_healed or target not in alive_player_ids:
            import random
            valid = [p for p in alive_player_ids if p != self.last_healed]
            target = random.choice(valid) if valid else alive_player_ids[0]

        self.last_healed = target
        await self.agent_db.add_thought(self.game_id, round_num, "night_heal",
                                         f"Healing #{target}: {reasoning}")
        return target
