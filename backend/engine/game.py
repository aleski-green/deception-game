import asyncio
import glob as glob_mod
import os
from pathlib import Path

from config import PLAYER_NAMES, PLAYER_PERSONALITIES, DATA_DIR, agent_db_path, SHARED_DB_PATH
from db.shared_db import SharedDB
from db.agent_db import AgentDB
from engine.roles import assign_roles
from engine.phase_day import run_freechat, run_pitches, run_vote
from engine.phase_night import run_night
from agents.agent import Agent


class GameEngine:
    def __init__(self, broadcast_fn):
        self.broadcast = broadcast_fn
        self.shared_db: SharedDB | None = None
        self.agent_dbs: dict[int, AgentDB] = {}
        self.agents: dict[int, Agent] = {}
        self.game_id: int = 0
        self.round_num: int = 0
        self.phase: str = "waiting"
        self.winner: str | None = None
        self.running: bool = False
        self.paused: bool = False

    async def cleanup_old_dbs(self):
        for f in glob_mod.glob(str(DATA_DIR / "*.sqlite")):
            os.remove(f)

    async def start_game(self) -> dict:
        await self.cleanup_old_dbs()

        # Init shared DB
        self.shared_db = SharedDB(SHARED_DB_PATH)
        await self.shared_db.init()
        self.game_id = await self.shared_db.create_game()

        # Assign roles
        roles = assign_roles(5)

        # Create agents
        for i in range(5):
            db = AgentDB(agent_db_path(i))
            await db.init()
            self.agent_dbs[i] = db

            agent = Agent(i, PLAYER_NAMES[i], roles[i], PLAYER_PERSONALITIES[i],
                         db, self.shared_db)
            agent.set_game(self.game_id)
            self.agents[i] = agent

            await self.shared_db.add_player(self.game_id, i, PLAYER_NAMES[i], roles[i])

        self.round_num = 0
        self.phase = "started"
        self.winner = None
        self.running = False

        players = await self.shared_db.get_players(self.game_id)

        await self.broadcast({
            "type": "game_start",
            "data": {
                "gameId": self.game_id,
                "players": [{"id": p['id'], "name": p['name'], "role": p['role']} for p in players],
            }
        })

        return {
            "gameId": self.game_id,
            "players": [{"id": p['id'], "name": p['name'], "role": p['role']} for p in players],
        }

    def _check_win(self, alive_players: list[dict]) -> str | None:
        alive_roles = [p['role'] for p in alive_players]
        if "impostor" not in alive_roles:
            return "civilians"
        if len(alive_players) <= 2 and "impostor" in alive_roles:
            return "impostor"
        return None

    async def run_game(self):
        self.running = True
        self.paused = False

        while self.running and self.winner is None:
            if self.paused:
                await asyncio.sleep(0.5)
                continue

            self.round_num += 1
            alive = await self.shared_db.get_alive_players(self.game_id)
            alive_ids = [p['id'] for p in alive]

            # === DAY PHASE ===
            self.phase = "freechat"
            await self.broadcast({
                "type": "phase_change",
                "data": {"round": self.round_num, "phase": "freechat",
                         "alivePlayers": [{"id": p['id'], "name": p['name']} for p in alive]}
            })

            await run_freechat(self.agents, alive_ids, self.shared_db,
                             self.game_id, self.round_num, self.broadcast)

            if not self.running:
                break

            # Pitches
            self.phase = "pitch"
            await self.broadcast({
                "type": "phase_change",
                "data": {"round": self.round_num, "phase": "pitch",
                         "alivePlayers": [{"id": p['id'], "name": p['name']} for p in alive]}
            })

            await run_pitches(self.agents, alive_ids, self.shared_db,
                            self.game_id, self.round_num, self.broadcast)

            if not self.running:
                break

            # Vote
            self.phase = "vote"
            await self.broadcast({
                "type": "phase_change",
                "data": {"round": self.round_num, "phase": "vote",
                         "alivePlayers": [{"id": p['id'], "name": p['name']} for p in alive]}
            })

            eliminated = await run_vote(self.agents, alive_ids, self.shared_db,
                                        self.game_id, self.round_num, self.broadcast)

            # Check win after vote
            alive = await self.shared_db.get_alive_players(self.game_id)
            self.winner = self._check_win(alive)
            if self.winner:
                break

            if not self.running:
                break

            # === NIGHT PHASE ===
            alive_ids = [p['id'] for p in alive]
            self.phase = "night"
            await self.broadcast({
                "type": "phase_change",
                "data": {"round": self.round_num, "phase": "night",
                         "alivePlayers": [{"id": p['id'], "name": p['name']} for p in alive]}
            })

            killed = await run_night(self.agents, alive_ids, self.shared_db,
                                    self.game_id, self.round_num, self.broadcast)

            # Check win after night
            alive = await self.shared_db.get_alive_players(self.game_id)
            self.winner = self._check_win(alive)
            if self.winner:
                break

        # Game over
        if self.winner:
            await self.shared_db.set_winner(self.game_id, self.winner)
            self.phase = "game_over"
            all_players = await self.shared_db.get_players(self.game_id)
            await self.broadcast({
                "type": "game_over",
                "data": {
                    "winner": self.winner,
                    "players": [{"id": p['id'], "name": p['name'], "role": p['role'],
                                "alive": bool(p['alive'])} for p in all_players],
                }
            })

        self.running = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def stop(self):
        self.running = False

    async def get_state(self) -> dict:
        if not self.shared_db or not self.game_id:
            return {"phase": "waiting", "round": 0, "players": [], "winner": None}

        players = await self.shared_db.get_players(self.game_id)
        return {
            "gameId": self.game_id,
            "phase": self.phase,
            "round": self.round_num,
            "winner": self.winner,
            "players": [{"id": p['id'], "name": p['name'], "role": p['role'],
                        "alive": bool(p['alive']),
                        "eliminatedRound": p['eliminated_round'],
                        "eliminatedPhase": p['eliminated_phase']} for p in players],
        }

    async def get_agent_history(self, agent_id: int) -> dict:
        if agent_id not in self.agent_dbs:
            return {"thoughts": [], "suspicions": [], "known_facts": []}
        return await self.agent_dbs[agent_id].get_all(self.game_id)

    async def close(self):
        if self.shared_db:
            await self.shared_db.close()
        for db in self.agent_dbs.values():
            await db.close()
