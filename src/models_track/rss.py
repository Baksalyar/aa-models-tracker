from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

from feedgen.feed import FeedGenerator  # type: ignore[import-untyped]

from models_track.scraper import Model, fetch_model_description

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


def _add_old_entries(fg: FeedGenerator) -> None:
    """Parse existing feed.xml and add entries to the new feed."""
    if not FEED_FILE.exists():
        return

    tree = ElementTree.parse(FEED_FILE)
    root = tree.getroot()

    # Find all item elements (handle RSS namespace if present)
    items = root.findall(".//item")
    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = root.findall(".//item")

    for item in items:
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        guid = item.findtext("guid", "")
        description = item.findtext("description", "")
        pub_date = item.findtext("pubDate", "")

        fe = fg.add_entry()
        if title:
            fe.title(title)
        if link:
            fe.link(href=link)
        if guid:
            fe.id(guid)
        if description:
            fe.description(description)
        if pub_date:
            fe.published(pub_date)
            fe.updated(pub_date)


def write_new_models(new_models: list[Model]) -> None:
    """Append new model entries to the RSS feed."""
    if not new_models:
        return

    DATA_DIR.mkdir(exist_ok=True)
    fg = _load_or_create_feed()

    for m in new_models:
        description = fetch_model_description(m.url, model_name=m.model_name)
        now = datetime.now(timezone.utc)

        fe = fg.add_entry()
        fe.title(f"New model: {m.model_name} from {m.creator}, intel index {m.intelligence}")
        fe.link(href=m.url)
        fe.id(m.url)
        fe.published(now)
        fe.updated(now)
        if description:
            fe.description(description)

    # Merge old entries from existing feed
    _add_old_entries(fg)

    fg.rss_file(str(FEED_FILE))
