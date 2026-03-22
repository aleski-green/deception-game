import sys
from pathlib import Path

# Add backend dir to path
sys.path.insert(0, str(Path(__file__).parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from api.routes_game import router as game_router, get_engine
from api.routes_history import router as history_router
from api.ws import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    eng = get_engine()
    await eng.close()


app = FastAPI(title="Impostor Game", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router)
app.include_router(history_router)


@app.websocket("/ws/game")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # Keep connection alive, receive any client messages
            data = await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
