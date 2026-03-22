import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from engine.game import GameEngine
from api.ws import manager
from agents.llm import set_api_key

router = APIRouter(prefix="/api/game")

engine: GameEngine | None = None
game_task: asyncio.Task | None = None


def get_engine() -> GameEngine:
    global engine
    if engine is None:
        engine = GameEngine(manager.broadcast)
    return engine


class ConfigRequest(BaseModel):
    api_key: str | None = None


@router.post("/config")
async def set_config(req: ConfigRequest):
    if req.api_key:
        set_api_key(req.api_key)
    return {"status": "ok"}


@router.post("/start")
async def start_game():
    global engine, game_task
    eng = get_engine()
    if eng.running:
        eng.stop()
        await asyncio.sleep(0.5)
    result = await eng.start_game()
    return result


@router.post("/run")
async def run_game():
    global game_task
    eng = get_engine()
    if not eng.game_id:
        raise HTTPException(400, "No game started. Call /start first.")
    if eng.running:
        eng.resume()
        return {"status": "resumed"}
    game_task = asyncio.create_task(eng.run_game())
    return {"status": "running"}


@router.post("/pause")
async def pause_game():
    eng = get_engine()
    eng.pause()
    return {"status": "paused"}


@router.post("/stop")
async def stop_game():
    eng = get_engine()
    eng.stop()
    return {"status": "stopped"}


@router.get("/state")
async def get_state():
    eng = get_engine()
    return await eng.get_state()
