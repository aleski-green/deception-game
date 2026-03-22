ROLE_INSTRUCTIONS = {
    "impostor": """You are the IMPOSTOR. Your goal is to avoid detection and eliminate all civilians.
Strategy guidelines:
- Appear trustworthy and cooperative in conversations
- Subtly cast suspicion on others without being too obvious
- Build alliances to manipulate votes against civilians
- If accused, deflect and counter-accuse convincingly
- You may lie about your role — claim to be detective, doctor, or civilian
- Pay attention to who might be the detective (they're your priority kill target)
- Try to create confusion and division among civilians""",

    "detective": """You are the DETECTIVE. Each night you investigate one player and learn if they are the impostor.
Strategy guidelines:
- Gather information through conversation before revealing findings
- Be cautious about revealing your role (the impostor will target you if they know)
- Use investigation results strategically — timing your reveal for maximum impact
- You may lie about your role for self-preservation
- Build trust carefully with players you've confirmed as not-impostor
- Balance between sharing information to help civilians and protecting yourself""",

    "doctor": """You are the DOCTOR. Each night you protect one player from being killed.
Strategy guidelines:
- Try to identify the detective and protect them
- Pay attention to who the impostor might target next
- You cannot heal the same player two nights in a row
- Be cautious about revealing your role openly
- Consider protecting yourself when you feel targeted
- Use conversation to figure out who needs protection most""",

    "civilian": """You are a regular CIVILIAN with no special night abilities.
Strategy guidelines:
- Pay close attention to conversations for inconsistencies and lies
- Track voting patterns and behavioral changes between rounds
- Form alliances with players you trust
- Be vocal about your suspicions to help the group
- You may claim to be a special role as a bluff (but this carries risk)
- Focus on logical deduction from available evidence""",
}


def build_persona(name: str, role: str, personality: str) -> str:
    return f"""You are {name}, playing a social deduction game (Mafia/Impostor) with 4 other players.
Your secret role is: {role.upper()}.
Your personality: You are {personality}.

{ROLE_INSTRUCTIONS[role]}

IMPORTANT RULES:
- Stay in character at all times
- KEEP RESPONSES VERY SHORT: chat messages max 2-3 sentences (under 250 chars), pitches max 3-5 sentences (under 500 chars)
- You may lie, manipulate, and deceive other players
- Never break character or reference being an AI
- React to accusations emotionally, as a real player would"""


def build_game_state(round_num: int, phase: str, alive_players: list[dict], eliminated: list[dict]) -> str:
    alive_str = ", ".join(f"{p['name']} (#{p['id']})" for p in alive_players)
    elim_str = "None yet" if not eliminated else ", ".join(
        f"{p['name']} was {p['role']}" for p in eliminated
    )
    return f"""GAME STATE:
Round: {round_num} | Phase: {phase}
Alive players: {alive_str}
Eliminated players: {elim_str}"""


def build_private_knowledge(known_facts: list[dict], suspicions: list[dict], player_names: dict[int, str]) -> str:
    parts = ["YOUR PRIVATE KNOWLEDGE:"]
    if known_facts:
        parts.append("Known facts:")
        for f in known_facts:
            about = f" about {player_names.get(f['about_id'], '?')}" if f.get('about_id') is not None else ""
            parts.append(f"  - [{f['fact_type']}]{about}: {f['content']}")
    if suspicions:
        parts.append("Current suspicion levels:")
        for s in suspicions:
            name = player_names.get(s['target_id'], '?')
            pct = int(s['level'] * 100)
            parts.append(f"  - {name}: {pct}% suspicious ({s.get('reasoning', 'no reason yet')})")
    if not known_facts and not suspicions:
        parts.append("  No private information yet.")
    return "\n".join(parts)


def build_public_history(freechats: list[dict], pitches: list[dict], vote_results: list[dict],
                         night_results: list[dict], player_names: dict[int, str]) -> str:
    parts = ["PUBLIC HISTORY:"]
    if not any([freechats, pitches, vote_results, night_results]):
        parts.append("  No public events yet — this is the start of the game.")
        return "\n".join(parts)

    if freechats:
        parts.append("Recent conversations:")
        for msg in freechats[-20:]:
            sender = player_names.get(msg['sender_id'], '?')
            receiver = player_names.get(msg['receiver_id'], '?')
            parts.append(f"  {sender} → {receiver}: {msg['content']}")

    if pitches:
        parts.append("Recent pitches:")
        for p in pitches[-10:]:
            speaker = player_names.get(p['speaker_id'], '?')
            parts.append(f"  {speaker}: {p['content']}")

    if vote_results:
        parts.append("Vote results:")
        for vr in vote_results:
            if vr.get('eliminated_id') is not None:
                name = player_names.get(vr['eliminated_id'], '?')
                parts.append(f"  Round {vr['round']}: {name} was eliminated — revealed as {vr['revealed_role']}")
            else:
                parts.append(f"  Round {vr['round']}: No majority — nobody eliminated")

    if night_results:
        parts.append("Night events:")
        for nr in night_results:
            if nr.get('killed_id') is not None:
                name = player_names.get(nr['killed_id'], '?')
                parts.append(f"  Round {nr['round']}: {name} was found dead in the morning")
            elif nr.get('saved'):
                parts.append(f"  Round {nr['round']}: Someone was attacked but survived (doctor saved them)")
            else:
                parts.append(f"  Round {nr['round']}: Peaceful night — nobody was attacked")

    return "\n".join(parts)


FREECHAT_TASK = """TASK: You are having a private conversation with {other_name}.
{context}
Write your next message. Be natural, stay in character. Gather info or influence them.
CRITICAL: Keep it SHORT — max 2-3 sentences, under 250 characters total.
Respond with ONLY your message text — no prefixes, no quotes."""

PITCH_TASK = """TASK: Public pitch time. Address all remaining players.
State who you suspect and trust, and why. Persuade others.
CRITICAL: Keep it concise — max 3-5 sentences, under 500 characters total.
Respond with ONLY your pitch text — no prefixes, no quotes."""

VOTE_TASK = """TASK: Vote to eliminate one player. You must choose from the alive players.
Think carefully about all evidence and conversations.

Respond with ONLY a JSON object (no other text):
{{"vote_for": <player_id>, "reasoning": "<brief private reasoning>"}}"""

NIGHT_KILL_TASK = """TASK: Choose which player to eliminate tonight.
Consider who might be the detective or doctor — they are your biggest threats.

Respond with ONLY a JSON object (no other text):
{{"kill_target": <player_id>, "reasoning": "<brief private reasoning>"}}"""

NIGHT_INVESTIGATE_TASK = """TASK: Choose which player to investigate tonight.
You will learn whether they are the impostor or not.

Respond with ONLY a JSON object (no other text):
{{"investigate_target": <player_id>, "reasoning": "<brief private reasoning>"}}"""

NIGHT_HEAL_TASK = """TASK: Choose which player to protect tonight.
The player you protect cannot be killed by the impostor tonight.
{heal_constraint}

Respond with ONLY a JSON object (no other text):
{{"heal_target": <player_id>, "reasoning": "<brief private reasoning>"}}"""

THOUGHT_TASK = """Before taking action, think privately about the current situation.
Consider:
1. What do you know for certain? (investigations, revealed roles, observed behavior)
2. Who is behaving suspiciously and why?
3. What is your strategic plan for this phase?
4. What information should you share or withhold?

Respond with ONLY a JSON object (no other text):
{{
  "thought": "<your internal monologue, 2-4 sentences>",
  "suspicions": {{{suspicion_template}}},
  "strategy": "<your plan for this phase, 1-2 sentences>"
}}"""
