"""Official-only image harvester for BollyAI.

This module accepts official press-kit, official og:image, and
official-trailer thumbnail candidates, rejects obvious watermark/paparazzi
sources, and creates local variants only when Pillow is available.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import requests
except ImportError:  # pragma: no cover - dry runs can still validate candidates.
    requests = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover - expected in stdlib-only installs.
    Image = None

from common import FIXTURE_DIR, REPO_ROOT, USER_AGENT, read_json, repo_path, utc_now, write_json


ALLOWED_SOURCE_TYPES = {
    "studio_press_kit",
    "official_og_image",
    "youtube_official_trailer_thumbnail",
    "platform_press_kit",
}
OFFICIAL_HOST_HINTS = (
    "youtube.com",
    "ytimg.com",
    "netflix.com",
    "primevideo.com",
    "aboutamazon.",
    "hotstar.com",
    "jiocinema.com",
    "zee5.com",
    "sonyliv.com",
    "aha.video",
    "sunnxt.com",
    "lionsgateplay.com",
    "apple.com",
    "press",
    "media",
    "studio",
    "pictures",
    "films",
)
REJECT_HINTS = (
    "paparazzi",
    "watermark",
    "watermarked",
    "getty",
    "shutterstock",
    "alamy",
    "pinterest",
    "reddit",
    "instagram.com",
    "facebook.com",
    "x.com",
    "twitter.com",
    "fanpage",
)
VARIANT_WIDTHS = (185, 342, 500)


def validate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    url = str(candidate.get("url") or "")
    source_type = str(candidate.get("source_type") or "")
    lower_url = url.lower()
    host = urlparse(url).netloc.lower()
    reasons = []

    if not url.startswith(("https://", "http://")):
        reasons.append("not_http_url")
    if source_type not in ALLOWED_SOURCE_TYPES:
        reasons.append("source_type_not_official")
    if any(hint in lower_url for hint in REJECT_HINTS) or any(hint in host for hint in REJECT_HINTS):
        reasons.append("rejected_host_or_watermark_hint")
    if not any(hint in host or hint in lower_url for hint in OFFICIAL_HOST_HINTS):
        reasons.append("no_official_host_hint")

    return {
        "candidate": candidate,
        "accepted": not reasons,
        "reasons": reasons,
    }


def fetch_image_bytes(url: str) -> bytes | None:
    if requests is None:
        return None
    response = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept": "image/*"}, timeout=30)
    if response.status_code >= 400:
        return None
    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("image/"):
        return None
    return response.content


def write_variants(
    *,
    slug: str,
    image_bytes: bytes,
    source_url: str,
    output_root: Path = REPO_ROOT / "public" / "img" / "films",
) -> dict[str, Any]:
    output_dir = output_root / slug
    if Image is None:
        return {
            "slug": slug,
            "source_url": source_url,
            "pil_available": False,
            "variants": [],
            "degraded": True,
            "reason": "PIL unavailable; image variant generation skipped.",
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(io.BytesIO(image_bytes))
    variants = []
    for width in VARIANT_WIDTHS:
        copy = image.copy()
        height = max(1, round(copy.height * (width / copy.width)))
        copy = copy.resize((width, height))
        for extension, pil_format in (("webp", "WEBP"), ("avif", "AVIF")):
            path = output_dir / f"w{width}.{extension}"
            try:
                copy.save(path, format=pil_format, quality=82)
            except Exception as exc:  # Pillow builds commonly lack AVIF.
                variants.append({"width": width, "format": pil_format, "skipped": True, "reason": exc.__class__.__name__})
                continue
            variants.append({"width": width, "format": pil_format, "path": str(path.relative_to(REPO_ROOT))})
    manifest = {
        "schema": "bollyai-image-harvest/v1",
        "slug": slug,
        "source_url": source_url,
        "generated_at": utc_now(),
        "pil_available": True,
        "variants": variants,
    }
    write_json(output_dir / "manifest.json", manifest)
    return manifest


def harvest_candidates(
    *,
    slug: str,
    candidates: list[dict[str, Any]],
    write: bool = False,
) -> dict[str, Any]:
    checked = [validate_candidate(candidate) for candidate in candidates]
    accepted = [item["candidate"] for item in checked if item["accepted"]]
    manifest: dict[str, Any] | None = None
    if write and accepted:
        first = accepted[0]
        image_bytes = fetch_image_bytes(first["url"])
        if image_bytes is None:
            manifest = {
                "slug": slug,
                "source_url": first["url"],
                "degraded": True,
                "reason": "Image fetch unavailable or failed.",
                "variants": [],
            }
        else:
            manifest = write_variants(slug=slug, image_bytes=image_bytes, source_url=first["url"])
    return {
        "schema": "bollyai-image-harvest-check/v1",
        "slug": slug,
        "checked_at": utc_now(),
        "accepted_count": len(accepted),
        "checks": checked,
        "manifest": manifest,
        "attribution_line": build_attribution_line(accepted[0]) if accepted else None,
    }


def build_attribution_line(candidate: dict[str, Any]) -> str:
    credit = candidate.get("credit") or candidate.get("source_name") or "official source"
    return f"Image via {credit}; used for analysis under BollyAI editorial policy."


def load_fixture_candidates(slug: str) -> list[dict[str, Any]]:
    fixture = read_json(FIXTURE_DIR / "image_candidates.json", default={"films": {}})
    return fixture.get("films", {}).get(slug, [])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and optionally harvest official film images.")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--film-json", help="Film JSON containing image_candidates.")
    parser.add_argument("--fixture-mode", action="store_true")
    parser.add_argument("--write", action="store_true", help="Fetch and write variants when accepted and PIL exists.")
    parser.add_argument("--emit", help="Optional JSON output path for the harvest report.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.fixture_mode:
        candidates = load_fixture_candidates(args.slug)
    elif args.film_json:
        film = read_json(repo_path(args.film_json), default={})
        candidates = film.get("image_candidates", [])
    else:
        candidates = []
    payload = harvest_candidates(slug=args.slug, candidates=candidates, write=args.write)
    if args.emit:
        write_json(repo_path(args.emit), payload)
    json.dump(payload, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
