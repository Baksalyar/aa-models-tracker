import json
import re
from dataclasses import dataclass
from typing import Any

import requests

URL = "https://artificialanalysis.ai/leaderboards/models"
BASE_URL = "https://artificialanalysis.ai"
RSC_SCRIPT_RE = re.compile(r"<script\b[^>]*>(.*?)</script>", re.DOTALL)
RSC_PUSH_PREFIX = "self.__next_f.push("
MODEL_ARRAY_KEYS = ("initialModels", "models")


@dataclass
class Model:
    model_name: str
    context_window: int
    creator: str
    intelligence: float
    url: str


def _extract_rsc_chunks(html: str) -> list[str]:
    """Decode Next.js RSC chunks embedded in the page's script tags."""
    chunks: list[str] = []
    for script in RSC_SCRIPT_RE.findall(html):
        script = script.strip()
        if not script.startswith(RSC_PUSH_PREFIX) or not script.endswith(")"):
            continue

        try:
            payload = json.loads(script[len(RSC_PUSH_PREFIX) : -1])
        except json.JSONDecodeError:
            continue

        if (
            isinstance(payload, list)
            and len(payload) == 2
            and payload[0] == 1
            and isinstance(payload[1], str)
        ):
            chunks.append(payload[1])

    return chunks


def _extract_json_array(chunk: str, key: str) -> list[dict[str, Any]] | None:
    """Extract a JSON array assigned to a key inside an RSC chunk."""
    marker = f'"{key}":'
    start = chunk.find(marker)
    if start == -1:
        return None

    try:
        value, _ = json.JSONDecoder().raw_decode(chunk[start + len(marker) :])
    except json.JSONDecodeError:
        return None

    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        return None

    return value


def _extract_model_arrays(
    chunks: list[str],
) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]] | None]:
    """Return basic and metrics model arrays from old or current page formats."""
    models_basic: list[dict[str, Any]] | None = None
    models_metrics: list[dict[str, Any]] | None = None

    for chunk in chunks:
        for key in MODEL_ARRAY_KEYS:
            models = _extract_json_array(chunk, key)
            if not models:
                continue

            if any("intelligenceIndex" in model for model in models) and models_metrics is None:
                models_metrics = models
            elif any("creator" in model for model in models) and models_basic is None:
                models_basic = models

    return models_basic, models_metrics


def _model_creator(model: dict[str, Any]) -> str:
    creator = model.get("creator")
    if isinstance(creator, dict):
        creator = creator.get("name")
    return str(creator or model.get("modelCreatorName") or "Unknown")


def _context_window(model: dict[str, Any]) -> int:
    context_window = model.get("context_window_tokens")
    if context_window is None:
        context_window = model.get("contextWindowTokens")
    return context_window if isinstance(context_window, int) else 0


def fetch_models(top_n: int = 20) -> list[Model]:
    """Scrape top N models from the Artificial Analysis leaderboard."""
    resp = requests.get(URL)
    resp.raise_for_status()

    chunks = _extract_rsc_chunks(resp.text)
    models_basic, models_metrics = _extract_model_arrays(chunks)

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
            context_window=_context_window(m),
            creator=_model_creator(m),
            intelligence=m.get("intelligenceIndex") or 0,
            url=BASE_URL + "/models/" + m.get("slug", ""),
        )
        for m in top
    ]


def fetch_model_description(url: str, model_name: str = "") -> str:
    """Scrape the short description paragraph from a model's page."""
    resp = requests.get(url)
    resp.raise_for_status()

    chunks = _extract_rsc_chunks(resp.text)

    # Look for a paragraph that starts with the model name
    if model_name:
        for chunk in chunks:
            matches: list[str] = re.findall(r'"children":"([^"]{80,})"', chunk)
            for text in matches:
                if text.startswith(model_name):
                    return text

    # Fallback: meta description
    for chunk in chunks:
        m = re.search(r'"name":"description","content":"([^"]+)"', chunk)
        if m:
            result: str = m.group(1)
            return result

    return ""
