import os
from pathlib import Path
from dotenv import load_dotenv

_backend_dir = Path(__file__).resolve().parent
_project_root = _backend_dir.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path, override=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

SHARED_DB_PATH = DATA_DIR / "shared.sqlite"

def agent_db_path(agent_id: int) -> Path:
    return DATA_DIR / f"agent_{agent_id}.sqlite"

PLAYER_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
PLAYER_PERSONALITIES = [
    "analytical and methodical — you break things down logically",
    "charismatic and persuasive — you rally people to your side",
    "cautious and reserved — you observe carefully before speaking",
    "direct and confrontational — you call out suspicious behavior immediately",
    "empathetic and observant — you read people's emotions and intentions",
]
