import json
from pathlib import Path
from typing import Any

from models_track.scraper import Model

DATA_DIR = Path("data")
MODELS_FILE = DATA_DIR / "models.json"


def load_models() -> list[dict[str, Any]]:
    """Load stored models from JSON file."""
    if not MODELS_FILE.exists():
        return []
    data: list[dict[str, Any]] = json.loads(MODELS_FILE.read_text())
    return data


def save_models(models: list[Model]) -> None:
    """Save models to JSON file."""
    DATA_DIR.mkdir(exist_ok=True)
    data = [
        {
            "model_name": m.model_name,
            "context_window": m.context_window,
            "creator": m.creator,
            "intelligence": m.intelligence,
            "url": m.url,
        }
        for m in models
    ]
    MODELS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
