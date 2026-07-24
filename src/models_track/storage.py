import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from models_track.scraper import Model

DATA_DIR = Path("data")
MODELS_FILE = DATA_DIR / "models.json"
HISTORY_FILE = DATA_DIR / "history.jsonl"


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


def load_history() -> list[dict[str, Any]]:
    """Load all history snapshots."""
    if not HISTORY_FILE.exists():
        return []
    snapshots: list[dict[str, Any]] = []
    for line in HISTORY_FILE.read_text().splitlines():
        if line.strip():
            snapshots.append(json.loads(line))
    return snapshots


def append_history(models: list[Model], prev_urls: set[str]) -> dict[str, Any]:
    """Append a new snapshot to history and return the diff summary."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()

    snapshot = {
        "timestamp": timestamp,
        "models": [
            {
                "rank": i + 1,
                "model_name": m.model_name,
                "creator": m.creator,
                "intelligence": m.intelligence,
                "url": m.url,
            }
            for i, m in enumerate(models)
        ],
    }

    with HISTORY_FILE.open("a") as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")

    current_urls = {m.url for m in models}
    entered = current_urls - prev_urls
    exited = prev_urls - current_urls

    return {
        "timestamp": timestamp,
        "entered": [m.url for m in models if m.url in entered],
        "exited": list(exited),
    }
