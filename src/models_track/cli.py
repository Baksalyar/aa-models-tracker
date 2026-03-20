from models_track.rss import write_new_models
from models_track.scraper import fetch_models
from models_track.storage import load_models, save_models


def run() -> None:
    """Main entry point: fetch, diff, store, and emit RSS."""
    print("Fetching models from Artificial Analysis...")
    fresh = fetch_models(top_n=20)
    print(f"Fetched {len(fresh)} models")

    stored = load_models()

    if not stored:
        print("Empty storage — saving initial snapshot")
        save_models(fresh)
        print(f"Saved {len(fresh)} models to data/models.json")
        return

    stored_urls = {m["url"] for m in stored}
    new_models = [m for m in fresh if m.url not in stored_urls]

    if new_models:
        print(f"Found {len(new_models)} new model(s):")
        for m in new_models:
            print(f"  - {m.model_name} ({m.creator})")
        write_new_models(new_models)
        # Update stored list with all current top 20
        save_models(fresh)
    else:
        print("No new models detected")

    print("Done")


def main() -> None:
    run()


if __name__ == "__main__":
    main()
