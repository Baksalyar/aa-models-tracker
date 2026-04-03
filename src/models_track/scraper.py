import json
import re
from dataclasses import dataclass

import requests

URL = "https://artificialanalysis.ai/leaderboards/models"
BASE_URL = "https://artificialanalysis.ai"


@dataclass
class Model:
    model_name: str
    context_window: int
    creator: str
    intelligence: float
    url: str


def fetch_models(top_n: int = 20) -> list[Model]:
    """Scrape top N models from the Artificial Analysis leaderboard."""
    resp = requests.get(URL)
    resp.raise_for_status()

    # Extract RSC chunks from the Next.js page
    chunks = re.findall(
        r"<script>self\.__next_f\.push\(\[1,\"(.*?)\"\]\)</script>",
        resp.text,
        re.DOTALL,
    )

    # Find chunks with model data
    models_basic = None
    models_metrics = None

    for chunk in chunks:
        unescaped = chunk.encode().decode("unicode_escape")
        if '"models":' not in unescaped:
            continue

        # Try to extract models array
        try:
            idx = unescaped.index('"models":') + 9
            # The value is an array starting with [{ or [
            if unescaped[idx] == "[":
                depth = 0
                end = idx
                for i in range(idx, len(unescaped)):
                    if unescaped[i] == "[":
                        depth += 1
                    elif unescaped[i] == "]":
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            break

                models_json = unescaped[idx:end]
                models = json.loads(models_json)

            # Check what type of data this chunk has
            if models and "creator" in models[0] and models_basic is None:
                models_basic = models
            elif models and "intelligenceIndex" in models[0] and models_metrics is None:
                models_metrics = models
        except (json.JSONDecodeError, KeyError, ValueError):
            continue

    if models_metrics is None:
        raise RuntimeError("Could not find models metrics data")

    # Use metrics data as primary (has all the info we need)
    raw = models_metrics

    # If we have basic data, merge creator info
    if models_basic:
        basic_by_slug = {m["slug"]: m for m in models_basic}
        for m in raw:
            if m.get("slug") in basic_by_slug:
                basic = basic_by_slug[m["slug"]]
                if "creator" in basic and "creator" not in m:
                    m["creator"] = basic["creator"]

    # Sort by intelligenceIndex (descending) to match the visual leaderboard
    raw.sort(key=lambda m: m.get("intelligenceIndex") or 0, reverse=True)

    top = raw[:top_n]

    return [
        Model(
            model_name=m.get("name", "Unknown"),
            context_window=m.get("context_window_tokens", 0),
            creator=m.get("creator", {}).get("name")
            if isinstance(m.get("creator"), dict)
            else m.get("modelCreatorName", "Unknown"),
            intelligence=m.get("intelligenceIndex", 0),
            url=BASE_URL + "/models/" + m.get("slug", ""),
        )
        for m in top
    ]


def fetch_model_description(url: str, model_name: str = "") -> str:
    """Scrape the short description paragraph from a model's page."""
    resp = requests.get(url)
    resp.raise_for_status()

    chunks = re.findall(
        r"<script>self\.__next_f\.push\(\[1,\"(.*?)\"\]\)</script>",
        resp.text,
        re.DOTALL,
    )

    # Look for a paragraph that starts with the model name
    if model_name:
        for chunk in chunks:
            unescaped = chunk.encode().decode("unicode_escape")
            matches: list[str] = re.findall(r'"children":"([^"]{80,})"', unescaped)
            for text in matches:
                if text.startswith(model_name):
                    return text

    # Fallback: meta description
    for chunk in chunks:
        unescaped = chunk.encode().decode("unicode_escape")
        m = re.search(r'"name":"description","content":"([^"]+)"', unescaped)
        if m:
            result: str = m.group(1)
            return result

    return ""
