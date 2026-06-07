"""TMDB metadata, changes-feed, and watch-provider fetcher.

Live mode reads TMDB_API_KEY from the environment.  If the key is absent,
fixture mode is used automatically and data is loaded from data/cache/fixtures.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

try:
    import requests
except ImportError:  # pragma: no cover - fixture mode still works without it.
    requests = None

from common import (
    CACHE_DIR,
    FIXTURE_DIR,
    JUSTWATCH_ATTRIBUTION,
    JUSTWATCH_COUNTRY_LINKS,
    USER_AGENT,
    parse_datetime,
    read_json,
    sha256_text,
    source_value,
    utc_now,
    write_json,
)


TMDB_BASE_URL = "https://api.themoviedb.org/3"
DEFAULT_REGION = "IN"


class TMDBClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        fixture_mode: bool | None = None,
        cache_dir: Path = CACHE_DIR / "tmdb",
        fixture_dir: Path = FIXTURE_DIR,
        soft_ttl_hours: int = 24,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("TMDB_API_KEY")
        self.fixture_mode = bool(fixture_mode) if fixture_mode is not None else not bool(self.api_key)
        self.cache_dir = cache_dir
        self.fixture_dir = fixture_dir
        self.soft_ttl = timedelta(hours=soft_ttl_hours)

    def movie_metadata(self, tmdb_id: int, *, region: str = DEFAULT_REGION) -> dict[str, Any]:
        raw = self._request_json(
            f"/movie/{tmdb_id}",
            params={
                "append_to_response": "credits,translations,release_dates,keywords,external_ids",
                "language": "en-US",
            },
            fixture_name=f"tmdb_movie_{tmdb_id}.json",
        )
        watch = self.watch_providers(tmdb_id, region=region)
        return normalize_movie_metadata(raw, watch_providers=watch, region=region)

    def watch_providers(self, tmdb_id: int, *, region: str = DEFAULT_REGION) -> dict[str, Any]:
        raw = self._request_json(
            f"/movie/{tmdb_id}/watch/providers",
            params={},
            fixture_name=f"tmdb_movie_{tmdb_id}_watch_providers.json",
        )
        return normalize_watch_providers(raw, tmdb_id=tmdb_id, region=region)

    def changes_feed(
        self,
        *,
        media_type: str = "movie",
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
    ) -> dict[str, Any]:
        if media_type not in {"movie", "tv"}:
            raise ValueError("media_type must be movie or tv")
        params: dict[str, Any] = {"page": page}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        raw = self._request_json(
            f"/{media_type}/changes",
            params=params,
            fixture_name=f"tmdb_{media_type}_changes.json",
        )
        return {
            "schema": f"tmdb-{media_type}-changes/v1",
            "fetched_at": raw.get("_fetched_at", utc_now()) if isinstance(raw, dict) else utc_now(),
            "source": "tmdb",
            "media_type": media_type,
            "enrichment_skipped": bool(isinstance(raw, dict) and raw.get("enrichment_skipped")),
            "results": raw.get("results", []) if isinstance(raw, dict) else [],
            "raw_page": raw.get("page") if isinstance(raw, dict) else None,
        }

    def _request_json(
        self,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        fixture_name: str,
    ) -> dict[str, Any]:
        params = params or {}
        if self.fixture_mode:
            fixture = read_json(self.fixture_dir / fixture_name, default=None)
            if fixture is None:
                return {
                    "enrichment_skipped": True,
                    "source": "fixture",
                    "_fixture_missing": fixture_name,
                    "_fetched_at": utc_now(),
                    "results": {},
                }
            if isinstance(fixture, dict):
                fixture.setdefault("_fetched_at", utc_now())
            return fixture

        if requests is None:
            return {
                "enrichment_skipped": True,
                "source": "tmdb",
                "error": "requests is not installed",
                "_fetched_at": utc_now(),
            }

        request_params = dict(params)
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "User-Agent": USER_AGENT,
        }
        if self.api_key and looks_like_bearer_token(self.api_key):
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.api_key:
            request_params["api_key"] = self.api_key

        url = f"{TMDB_BASE_URL}{endpoint}"
        cache_path = self._cache_path(url, request_params)
        cached = read_json(cache_path, default=None)
        if cached and self._is_fresh(cached.get("fetched_at")):
            payload = cached.get("payload", {})
            if isinstance(payload, dict):
                payload.setdefault("_cache_status", "fresh")
                payload.setdefault("_fetched_at", cached.get("fetched_at"))
            return payload

        if cached:
            if cached.get("etag"):
                headers["If-None-Match"] = cached["etag"]
            if cached.get("last_modified"):
                headers["If-Modified-Since"] = cached["last_modified"]

        try:
            response = requests.get(url, params=request_params, headers=headers, timeout=20)
        except requests.RequestException as exc:
            return self._stale_or_error(cached, f"request_error:{exc.__class__.__name__}")

        if response.status_code == 304 and cached:
            cached["fetched_at"] = utc_now()
            write_json(cache_path, cached)
            payload = cached.get("payload", {})
            if isinstance(payload, dict):
                payload.setdefault("_cache_status", "not_modified")
                payload.setdefault("_fetched_at", cached.get("fetched_at"))
            return payload

        if response.status_code == 429 or response.status_code >= 500:
            return self._stale_or_error(cached, f"http_{response.status_code}")

        if response.status_code >= 400:
            return {
                "enrichment_skipped": True,
                "source": "tmdb",
                "error": f"http_{response.status_code}",
                "_fetched_at": utc_now(),
            }

        payload = response.json()
        fetched_at = utc_now()
        cache_record = {
            "url": url,
            "params_hash": sha256_text(urlencode(sorted(request_params.items()))),
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "fetched_at": fetched_at,
            "payload": payload,
        }
        write_json(cache_path, cache_record)
        if isinstance(payload, dict):
            payload.setdefault("_cache_status", "live")
            payload.setdefault("_fetched_at", fetched_at)
        return payload

    def _stale_or_error(self, cached: dict[str, Any] | None, reason: str) -> dict[str, Any]:
        if cached:
            payload = cached.get("payload", {})
            if isinstance(payload, dict):
                payload = dict(payload)
                payload["enrichment_skipped"] = True
                payload["_cache_status"] = "stale"
                payload["_stale_reason"] = reason
                payload.setdefault("_fetched_at", cached.get("fetched_at", utc_now()))
                return payload
        return {
            "enrichment_skipped": True,
            "source": "tmdb",
            "error": reason,
            "_fetched_at": utc_now(),
        }

    def _is_fresh(self, fetched_at: str | None) -> bool:
        parsed = parse_datetime(fetched_at)
        if not parsed:
            return False
        return datetime.now(timezone.utc) - parsed <= self.soft_ttl

    def _cache_path(self, url: str, params: dict[str, Any]) -> Path:
        safe_params = {key: value for key, value in params.items() if key != "api_key"}
        cache_key = sha256_text(f"{url}?{urlencode(sorted(safe_params.items()))}")
        return self.cache_dir / f"{cache_key}.json"


def looks_like_bearer_token(value: str) -> bool:
    return value.startswith("eyJ") or value.count(".") >= 2


def normalize_movie_metadata(
    raw: dict[str, Any],
    *,
    watch_providers: dict[str, Any] | None,
    region: str = DEFAULT_REGION,
) -> dict[str, Any]:
    fetched_at = raw.get("_fetched_at", utc_now())
    release_date = choose_release_date(raw, region=region)
    credits = raw.get("credits") or {}
    keywords = raw.get("keywords") or {}
    external_ids = raw.get("external_ids") or {}
    crew = credits.get("crew") or []
    cast = credits.get("cast") or []

    return {
        "schema": "tmdb-metadata/v1",
        "tmdb_id": source_value(raw.get("id"), "tmdb", fetched_at=fetched_at),
        "wikidata_qid": source_value(
            external_ids.get("wikidata_id"),
            "tmdb_external_ids",
            fetched_at=fetched_at,
            confidence="verified" if external_ids.get("wikidata_id") else "unverified",
        ),
        "imdb_id": source_value(
            external_ids.get("imdb_id"),
            "tmdb_external_ids",
            fetched_at=fetched_at,
            confidence="verified" if external_ids.get("imdb_id") else "unverified",
        ),
        "title": source_value(raw.get("title") or raw.get("name"), "tmdb", fetched_at=fetched_at),
        "original_title": source_value(raw.get("original_title"), "tmdb", fetched_at=fetched_at),
        "original_language": source_value(raw.get("original_language"), "tmdb", fetched_at=fetched_at),
        "release_date": source_value(release_date, "tmdb_release_dates", fetched_at=fetched_at),
        "status": source_value((raw.get("status") or "").lower(), "tmdb", fetched_at=fetched_at),
        "runtime_min": source_value(raw.get("runtime"), "tmdb", fetched_at=fetched_at),
        "genres": source_value(
            [genre.get("name") for genre in raw.get("genres", []) if genre.get("name")],
            "tmdb",
            fetched_at=fetched_at,
        ),
        "keywords": source_value(
            [item.get("name") for item in keywords.get("keywords", []) if item.get("name")],
            "tmdb",
            fetched_at=fetched_at,
        ),
        "crew": source_value(
            {
                "director": compact_people(crew, job="Director"),
                "writer": compact_people(crew, department="Writing"),
            },
            "tmdb_credits",
            fetched_at=fetched_at,
        ),
        "cast": source_value(
            [
                {
                    "name": person.get("name"),
                    "character": person.get("character"),
                    "order": person.get("order"),
                    "tmdb_person_id": person.get("id"),
                }
                for person in sorted(cast, key=lambda item: item.get("order", 9999))[:12]
                if person.get("name")
            ],
            "tmdb_credits",
            fetched_at=fetched_at,
        ),
        "watch_providers": watch_providers or {},
        "enrichment_skipped": bool(raw.get("enrichment_skipped")),
        "_provenance": {
            "source": "tmdb",
            "fetched_at": fetched_at,
            "cache_status": raw.get("_cache_status", "fixture"),
            "tmdb_cache_expires": cache_expiry_date(fetched_at),
        },
        "_quarantine": [],
    }


def normalize_watch_providers(raw: dict[str, Any], *, tmdb_id: int, region: str) -> dict[str, Any]:
    fetched_at = raw.get("_fetched_at", utc_now())
    results = raw.get("results") or {}
    region_data = results.get(region) or {}
    providers: dict[str, list[dict[str, Any]]] = {}
    for bucket in ("flatrate", "rent", "buy", "ads", "free"):
        providers[bucket] = [
            {
                "provider_name": source_value(item.get("provider_name"), "tmdb_watch_providers", fetched_at=fetched_at),
                "provider_id": source_value(item.get("provider_id"), "tmdb_watch_providers", fetched_at=fetched_at),
                "logo_path": source_value(item.get("logo_path"), "tmdb_watch_providers", fetched_at=fetched_at),
            }
            for item in region_data.get(bucket, [])
        ]
    return {
        "schema": "tmdb-watch-providers/v1",
        "tmdb_id": tmdb_id,
        "country": region,
        "country_link": JUSTWATCH_COUNTRY_LINKS.get(region, f"https://www.justwatch.com/{region.lower()}"),
        "attribution": JUSTWATCH_ATTRIBUTION,
        "link": source_value(region_data.get("link"), "tmdb_watch_providers", fetched_at=fetched_at),
        "providers": providers,
        "as_of": fetched_at[:10],
        "enrichment_skipped": bool(raw.get("enrichment_skipped")),
        "_provenance": {"source": "tmdb_watch_providers", "fetched_at": fetched_at},
    }


def choose_release_date(raw: dict[str, Any], *, region: str) -> str | None:
    release_dates = ((raw.get("release_dates") or {}).get("results") or [])
    country_record = next((item for item in release_dates if item.get("iso_3166_1") == region), None)
    if not country_record:
        return raw.get("release_date")
    dated = [
        item.get("release_date", "")[:10]
        for item in country_record.get("release_dates", [])
        if item.get("release_date") and item.get("type") in {2, 3}
    ]
    return sorted(dated)[0] if dated else raw.get("release_date")


def compact_people(
    people: list[dict[str, Any]],
    *,
    job: str | None = None,
    department: str | None = None,
) -> list[dict[str, Any]]:
    output = []
    for person in people:
        if job and person.get("job") != job:
            continue
        if department and person.get("department") != department:
            continue
        output.append({"name": person.get("name"), "tmdb_person_id": person.get("id"), "job": person.get("job")})
    return output[:10]


def cache_expiry_date(fetched_at: str) -> str | None:
    parsed = parse_datetime(fetched_at)
    if not parsed:
        return None
    return (parsed + timedelta(days=183)).date().isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch TMDB metadata, changes, or watch providers.")
    parser.add_argument("--fixture-mode", action="store_true", help="Read from data/cache/fixtures instead of TMDB.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    metadata = subparsers.add_parser("metadata")
    metadata.add_argument("--tmdb-id", type=int, required=True)
    metadata.add_argument("--region", default=DEFAULT_REGION)

    watch = subparsers.add_parser("watch-providers")
    watch.add_argument("--tmdb-id", type=int, required=True)
    watch.add_argument("--region", default=DEFAULT_REGION)

    changes = subparsers.add_parser("changes")
    changes.add_argument("--media-type", choices=("movie", "tv"), default="movie")
    changes.add_argument("--start-date")
    changes.add_argument("--end-date")
    changes.add_argument("--page", type=int, default=1)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = TMDBClient(fixture_mode=args.fixture_mode or not bool(os.environ.get("TMDB_API_KEY")))
    if args.command == "metadata":
        payload = client.movie_metadata(args.tmdb_id, region=args.region)
    elif args.command == "watch-providers":
        payload = client.watch_providers(args.tmdb_id, region=args.region)
    else:
        payload = client.changes_feed(
            media_type=args.media_type,
            start_date=args.start_date,
            end_date=args.end_date,
            page=args.page,
        )
    import json

    json.dump(payload, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
