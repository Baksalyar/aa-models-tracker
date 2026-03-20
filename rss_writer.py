from datetime import datetime, timezone
from pathlib import Path

from feedgen.feed import FeedGenerator

from scraper import Model

DATA_DIR = Path("data")
FEED_FILE = DATA_DIR / "feed.xml"

BASE_URL = "https://artificialanalysis.ai"


def _load_or_create_feed() -> FeedGenerator:
    """Load existing feed or create a new one."""
    fg = FeedGenerator()
    fg.title("AI Model Tracker")
    fg.link(href=BASE_URL)
    fg.description("New additions to the Artificial Analysis LLM Leaderboard")
    fg.language("en")
    return fg


def write_new_models(new_models: list[Model]) -> None:
    """Append new model entries to the RSS feed."""
    if not new_models:
        return

    DATA_DIR.mkdir(exist_ok=True)
    fg = _load_or_create_feed()

    for m in new_models:
        fe = fg.add_entry()
        fe.title(f"New model: {m.model_name} from {m.creator}, intel index {m.intelligence}")
        fe.link(href=m.url)
        fe.id(m.url)
        fe.published(datetime.now(timezone.utc))

    # If feed exists, merge old entries
    if FEED_FILE.exists():
        old_fg = FeedGenerator()
        old_fg.rss_file(str(FEED_FILE))
        for old_fe in old_fg.entry():
            fe = fg.add_entry()
            fe.title(old_fe.title())
            fe.link(href=old_fe.link()[0]["href"] if old_fe.link() else "")
            fe.id(old_fe.id())
            if old_fe.published():
                fe.published(old_fe.published())

    fg.rss_file(str(FEED_FILE))
