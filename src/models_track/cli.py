from datetime import datetime, timedelta, timezone
from pathlib import Path

from models_track.rss import write_new_models
from models_track.scraper import fetch_models
from models_track.storage import append_history, load_models, save_models

MIN_INTERVAL = timedelta(hours=1)
LAST_RUN_FILE = Path("data/.last_run")


def _check_rate_limit() -> bool:
    """Return True if enough time passed since last run."""
    if not LAST_RUN_FILE.exists():
        return True
    last_run = datetime.fromtimestamp(float(LAST_RUN_FILE.read_text().strip()), tz=timezone.utc)
    return datetime.now(timezone.utc) - last_run >= MIN_INTERVAL


def _touch_last_run() -> None:
    """Record current timestamp."""
    LAST_RUN_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_RUN_FILE.write_text(str(datetime.now(timezone.utc).timestamp()))


def run() -> None:
    """Main entry point: fetch, diff, store, and emit RSS."""
    if not _check_rate_limit():
        print("Skipping — last run less than 1 hour ago")
        return

    print("Fetching models from Artificial Analysis...")
    fresh = fetch_models(top_n=50)
    print(f"Fetched {len(fresh)} models")

    stored = load_models()

    if not stored:
        print("Empty storage — generating initial RSS entries for all models")
        write_new_models(fresh[:20])
        save_models(fresh[:20])
        append_history(fresh, set())
        print(f"Saved {len(fresh[:20])} models to data/models.json")
        print("Done")
        return

    stored_urls = {m["url"] for m in stored}
    new_models = [m for m in fresh[:20] if m.url not in stored_urls]

    if new_models:
        print(f"Found {len(new_models)} new model(s):")
        for m in new_models:
            print(f"  - {m.model_name} ({m.creator})")
        write_new_models(new_models)
        save_models(fresh[:20])
    else:
        print("No new models detected")

    diff = append_history(fresh, stored_urls)
    if diff["exited"]:
        print(f"Exited top 20: {diff['exited']}")

    _touch_last_run()
    print("Done")


def main() -> None:
    run()


if __name__ == "__main__":
    main()
