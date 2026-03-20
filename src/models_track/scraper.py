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

    # Find the chunk containing the full models array (some chunks have sparse data)
    models_json = None
    for chunk in chunks:
        unescaped = chunk.encode().decode("unicode_escape")
        if '"models":[{' not in unescaped:
            continue
        arr_start = unescaped.index('"models":[{') + 9
        depth = 0
        arr_end = arr_start
        for i in range(arr_start, len(unescaped)):
            if unescaped[i] == "[":
                depth += 1
            elif unescaped[i] == "]":
                depth -= 1
            if depth == 0:
                arr_end = i + 1
                break
        candidate = unescaped[arr_start:arr_end]
        # Prefer the chunk where models have intelligence_index populated
        try:
            probe = json.loads(candidate)
            if probe and probe[0].get("intelligence_index") is not None:
                models_json = candidate
                break
        except (json.JSONDecodeError, IndexError):
            continue
        # Fallback: keep the first valid one
        if models_json is None:
            models_json = candidate

    if models_json is None:
        raise RuntimeError("Could not find models data in the page")

    raw = json.loads(models_json)

    # Sort by display_order and take top N
    raw.sort(key=lambda m: m.get("display_order", 9999))
    top = raw[:top_n]

    return [
        Model(
            model_name=m["name"],
            context_window=m.get("context_window_tokens", 0),
            creator=m.get("model_creators", {}).get("name", "Unknown"),
            intelligence=m.get("intelligence_index", 0),
            url=BASE_URL + m.get("model_url", ""),
        )
        for m in top
    ]
