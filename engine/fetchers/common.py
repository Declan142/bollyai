"""Shared helpers for the BollyAI data fetchers.

The fetchers are intentionally plain Python: stdlib plus optional requests in
the live modules.  They can be run directly from the repo root or by GitHub
Actions without installing a package.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
FIXTURE_DIR = CACHE_DIR / "fixtures"
STATE_DIR = DATA_DIR / "_state"

USER_AGENT = "BollyAI-DataBot/1.0 (+https://bollyai.in/bot; data@bollyai.in)"

INDUSTRY_URL_SEGMENTS = {
    "bombay": "bollywood",
    "kollywood": "kollywood",
    "tollywood": "tollywood",
    "mollywood": "mollywood",
    "sandalwood": "sandalwood",
    "hollywood": "hollywood",
    "streaming": "streaming",
    # Blueprint aliases used by older seat files.
    "bollywood": "bollywood",
    "tamil": "kollywood",
    "telugu": "tollywood",
    "malayalam": "mollywood",
    "kannada": "sandalwood",
    "ott": "streaming",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any, *, sort_keys: bool = True) -> None:
    ensure_parent(path)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(path.parent),
        delete=False,
    ) as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2, sort_keys=sort_keys)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(payload: Any) -> str:
    return sha256_text(canonical_json(payload))


def source_value(
    value: Any,
    source: str,
    *,
    fetched_at: str | None = None,
    confidence: str = "verified",
) -> dict[str, Any]:
    return {
        "value": value,
        "source": source,
        "fetched_at": fetched_at or utc_now(),
        "confidence": confidence,
    }


def unwrap_value(value: Any) -> Any:
    if isinstance(value, dict) and set(("value", "source", "fetched_at", "confidence")).issubset(value):
        return value.get("value")
    return value


def repo_path(path_text: str | Path, *, base: Path = REPO_ROOT) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return base / path


def film_url(industry: str | None, page_type: str, slug: str | None) -> str | None:
    if not industry or not slug:
        return None
    segment = INDUSTRY_URL_SEGMENTS.get(str(industry), str(industry))
    if page_type == "review":
        return f"/{segment}/reviews/{slug}/"
    if page_type == "box-office":
        return f"/{segment}/box-office/{slug}/"
    if page_type == "upcoming":
        return f"/{segment}/upcoming/{slug}/"
    return f"/{segment}/{slug}/"


def stable_unique(items: Iterable[str | None]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output
