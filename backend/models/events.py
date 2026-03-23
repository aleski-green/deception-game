from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel


class Player(BaseModel):
    id: int
    name: str
    role: str
    alive: bool = True
    eliminated_round: Optional[int] = None
    eliminated_phase: Optional[str] = None


class GameState(BaseModel):
    game_id: Optional[int] = None
    phase: str = "waiting"
    round: int = 0
    winner: Optional[str] = None
    players: List[Player] = []
