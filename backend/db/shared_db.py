from __future__ import annotations

import aiosqlite
from pathlib import Path
from .schema import SHARED_SCHEMA


class SharedDB:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def init(self):
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SHARED_SCHEMA)
        await self._db.commit()

    async def close(self):
        if self._db:
            await self._db.close()

    @property
    def db(self) -> aiosqlite.Connection:
        assert self._db is not None
        return self._db

    async def create_game(self) -> int:
        cursor = await self.db.execute("INSERT INTO games DEFAULT VALUES")
        await self.db.commit()
        return cursor.lastrowid

    async def add_player(self, game_id: int, player_id: int, name: str, role: str):
        await self.db.execute(
            "INSERT INTO players (id, game_id, name, role) VALUES (?, ?, ?, ?)",
            (player_id, game_id, name, role),
        )
        await self.db.commit()

    async def get_players(self, game_id: int) -> list[dict]:
        cursor = await self.db.execute(
            "SELECT * FROM players WHERE game_id = ? ORDER BY id", (game_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_alive_players(self, game_id: int) -> list[dict]:
        cursor = await self.db.execute(
            "SELECT * FROM players WHERE game_id = ? AND alive = 1 ORDER BY id",
            (game_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def eliminate_player(self, game_id: int, player_id: int, round_num: int, phase: str):
        await self.db.execute(
            "UPDATE players SET alive = 0, eliminated_round = ?, eliminated_phase = ? WHERE game_id = ? AND id = ?",
            (round_num, phase, game_id, player_id),
        )
        await self.db.commit()

    async def add_freechat(self, game_id: int, round_num: int, sender_id: int, receiver_id: int, content: str):
        await self.db.execute(
            "INSERT INTO freechat_messages (game_id, round, sender_id, receiver_id, content) VALUES (?, ?, ?, ?, ?)",
            (game_id, round_num, sender_id, receiver_id, content),
        )
        await self.db.commit()

    async def get_freechats(self, game_id: int, round_num: int) -> list[dict]:
        cursor = await self.db.execute(
            "SELECT * FROM freechat_messages WHERE game_id = ? AND round = ? ORDER BY id",
            (game_id, round_num),
        )
        return [dict(r) for r in await cursor.fetchall()]

    async def add_pitch(self, game_id: int, round_num: int, speaker_id: int, content: str):
        await self.db.execute(
            "INSERT INTO pitch_messages (game_id, round, speaker_id, content) VALUES (?, ?, ?, ?)",
            (game_id, round_num, speaker_id, content),
        )
        await self.db.commit()

    async def get_pitches(self, game_id: int, round_num: int) -> list[dict]:
        cursor = await self.db.execute(
            "SELECT * FROM pitch_messages WHERE game_id = ? AND round = ? ORDER BY id",
            (game_id, round_num),
        )
        return [dict(r) for r in await cursor.fetchall()]

    async def add_vote(self, game_id: int, round_num: int, voter_id: int, target_id: int):
        await self.db.execute(
            "INSERT INTO votes (game_id, round, voter_id, target_id) VALUES (?, ?, ?, ?)",
            (game_id, round_num, voter_id, target_id),
        )
        await self.db.commit()

    async def get_votes(self, game_id: int, round_num: int) -> list[dict]:
        cursor = await self.db.execute(
            "SELECT * FROM votes WHERE game_id = ? AND round = ? ORDER BY id",
            (game_id, round_num),
        )
        return [dict(r) for r in await cursor.fetchall()]

    async def add_vote_result(self, game_id: int, round_num: int, eliminated_id: int | None, revealed_role: str | None):
        await self.db.execute(
            "INSERT INTO vote_results (game_id, round, eliminated_id, revealed_role) VALUES (?, ?, ?, ?)",
            (game_id, round_num, eliminated_id, revealed_role),
        )
        await self.db.commit()

    async def add_night_result(self, game_id: int, round_num: int, killed_id: int | None, saved: bool):
        await self.db.execute(
            "INSERT INTO night_results (game_id, round, killed_id, saved) VALUES (?, ?, ?, ?)",
            (game_id, round_num, killed_id, 1 if saved else 0),
        )
        await self.db.commit()

    async def get_night_results(self, game_id: int) -> list[dict]:
        cursor = await self.db.execute(
            "SELECT * FROM night_results WHERE game_id = ? ORDER BY round", (game_id,)
        )
        return [dict(r) for r in await cursor.fetchall()]

    async def get_vote_results(self, game_id: int) -> list[dict]:
        cursor = await self.db.execute(
            "SELECT * FROM vote_results WHERE game_id = ? ORDER BY round", (game_id,)
        )
        return [dict(r) for r in await cursor.fetchall()]

    async def set_winner(self, game_id: int, winner: str):
        await self.db.execute(
            "UPDATE games SET winner = ?, ended_at = datetime('now') WHERE id = ?",
            (winner, game_id),
        )
        await self.db.commit()

    async def get_game(self, game_id: int) -> dict | None:
        cursor = await self.db.execute("SELECT * FROM games WHERE id = ?", (game_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_all_freechats(self, game_id: int) -> list[dict]:
        cursor = await self.db.execute(
            "SELECT * FROM freechat_messages WHERE game_id = ? ORDER BY id", (game_id,)
        )
        return [dict(r) for r in await cursor.fetchall()]

    async def get_all_pitches(self, game_id: int) -> list[dict]:
        cursor = await self.db.execute(
            "SELECT * FROM pitch_messages WHERE game_id = ? ORDER BY id", (game_id,)
        )
        return [dict(r) for r in await cursor.fetchall()]

    async def get_all_votes(self, game_id: int) -> list[dict]:
        cursor = await self.db.execute(
            "SELECT * FROM votes WHERE game_id = ? ORDER BY id", (game_id,)
        )
        return [dict(r) for r in await cursor.fetchall()]
