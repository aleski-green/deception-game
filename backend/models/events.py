from pydantic import BaseModel


class Player(BaseModel):
    id: int
    name: str
    role: str
    alive: bool = True
    eliminated_round: int | None = None
    eliminated_phase: str | None = None


class GameState(BaseModel):
    game_id: int | None = None
    phase: str = "waiting"
    round: int = 0
    winner: str | None = None
    players: list[Player] = []
