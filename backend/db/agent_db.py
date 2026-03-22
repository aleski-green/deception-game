import aiosqlite
from pathlib import Path
from .schema import AGENT_SCHEMA


class AgentDB:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def init(self):
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(AGENT_SCHEMA)
        await self._db.commit()

    async def close(self):
        if self._db:
            await self._db.close()

    @property
    def db(self) -> aiosqlite.Connection:
        assert self._db is not None
        return self._db

    async def add_thought(self, game_id: int, round_num: int, phase: str, content: str):
        await self.db.execute(
            "INSERT INTO thoughts (game_id, round, phase, content) VALUES (?, ?, ?, ?)",
            (game_id, round_num, phase, content),
        )
        await self.db.commit()

    async def get_thoughts(self, game_id: int) -> list[dict]:
        cursor = await self.db.execute(
            "SELECT * FROM thoughts WHERE game_id = ? ORDER BY id", (game_id,)
        )
        return [dict(r) for r in await cursor.fetchall()]

    async def add_suspicion(self, game_id: int, round_num: int, target_id: int, level: float, reasoning: str | None = None):
        await self.db.execute(
            "INSERT INTO suspicions (game_id, round, target_id, level, reasoning) VALUES (?, ?, ?, ?, ?)",
            (game_id, round_num, target_id, level, reasoning),
        )
        await self.db.commit()

    async def get_latest_suspicions(self, game_id: int) -> list[dict]:
        cursor = await self.db.execute(
            """SELECT s.* FROM suspicions s
               INNER JOIN (
                   SELECT target_id, MAX(id) as max_id FROM suspicions WHERE game_id = ? GROUP BY target_id
               ) latest ON s.id = latest.max_id""",
            (game_id,),
        )
        return [dict(r) for r in await cursor.fetchall()]

    async def add_strategy(self, game_id: int, round_num: int, phase: str, plan: str):
        await self.db.execute(
            "INSERT INTO strategy (game_id, round, phase, plan) VALUES (?, ?, ?, ?)",
            (game_id, round_num, phase, plan),
        )
        await self.db.commit()

    async def add_known_fact(self, game_id: int, round_num: int, fact_type: str, about_id: int | None, content: str):
        await self.db.execute(
            "INSERT INTO known_facts (game_id, round, fact_type, about_id, content) VALUES (?, ?, ?, ?, ?)",
            (game_id, round_num, fact_type, about_id, content),
        )
        await self.db.commit()

    async def get_known_facts(self, game_id: int) -> list[dict]:
        cursor = await self.db.execute(
            "SELECT * FROM known_facts WHERE game_id = ? ORDER BY id", (game_id,)
        )
        return [dict(r) for r in await cursor.fetchall()]

    async def get_all(self, game_id: int) -> dict:
        return {
            "thoughts": await self.get_thoughts(game_id),
            "suspicions": await self.get_latest_suspicions(game_id),
            "known_facts": await self.get_known_facts(game_id),
        }
