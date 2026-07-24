from datetime import datetime, timedelta, timezone
from typing import Any

from models_track.scraper import fetch_models
from models_track.storage import load_history

GREEN = "\033[32m"
RED = "\033[31m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

PERIODS = [
    ("week", timedelta(weeks=1)),
    ("month", timedelta(days=30)),
    ("year", timedelta(days=365)),
]


def _find_snapshot(history: list[dict[str, Any]], target_time: datetime) -> dict[str, Any] | None:
    best = None
    best_diff = None
    for snap in history:
        ts = datetime.fromisoformat(snap["timestamp"])
        diff = abs((ts - target_time).total_seconds())
        if best_diff is None or diff < best_diff:
            best = snap
            best_diff = diff
    if best is None or best_diff is None:
        return None
    ts = datetime.fromisoformat(best["timestamp"])
    if abs((ts - target_time).total_seconds()) > timedelta(days=2).total_seconds():
        return None
    return best


def _rank_map(snapshot: dict[str, Any]) -> dict[str, int]:
    return {m["url"]: m["rank"] for m in snapshot["models"]}


def _format_change(current_rank: int, prev_rank: int | None) -> str:
    if prev_rank is None:
        return f"{DIM}new{RESET}"
    delta = prev_rank - current_rank
    if delta > 0:
        return f"{GREEN}↑{delta}{RESET}"
    elif delta < 0:
        return f"{RED}↓{abs(delta)}{RESET}"
    return f"{DIM}—{RESET}"


def run() -> None:
    print("Fetching current top 50 models...")
    fresh = fetch_models(top_n=50)
    history = load_history()

    now = datetime.now(timezone.utc)

    snapshots_by_period: list[tuple[str, dict[str, int] | None]] = []
    for label, delta in PERIODS:
        snap = _find_snapshot(history, now - delta)
        snapshots_by_period.append((label, _rank_map(snap) if snap else None))

    max_name = max(len(m.model_name) for m in fresh)

    for m in fresh:
        parts: list[str] = []
        for label, ranks in snapshots_by_period:
            prev_rank = ranks.get(m.url) if ranks else None
            parts.append(f"{label}: {_format_change(fresh.index(m) + 1, prev_rank)}")
        dynamics = ", ".join(parts)
        rank = fresh.index(m) + 1
        print(f"{rank:>2}. {m.model_name:<{max_name}}  ({dynamics})")

    if not history:
        print(f"\n{DIM}No history yet — dynamics will appear after subsequent runs.{RESET}")


def main() -> None:
    run()


if __name__ == "__main__":
    main()
