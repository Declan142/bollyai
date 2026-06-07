"""Wikidata metadata, discovery, and revision helpers for BollyAI.

Wikidata is the primary metadata spine: every film is keyed by QID.  Live
metadata reads are keyless SPARQL GET requests with the same soft-cache and
stale-on-pressure contract used by the rest of the fetcher layer.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

from common import CACHE_DIR, FIXTURE_DIR, parse_datetime, read_json, sha256_text, source_value, utc_now, write_json


SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_REST_BASE = "https://www.wikidata.org/w/rest.php"
WIKIDATA_USER_AGENT = "BollyAI/1.0 (bollyai.in; takedown@bollyai.in)"
SPARQL_ACCEPT = "application/sparql-results+json"
JSON_ACCEPT = "application/json"
INDIC_LANGUAGE_QIDS = {
    "Q1568": "hi",
    "Q5885": "ta",
    "Q8097": "te",
    "Q36236": "ml",
    "Q33673": "kn",
    "Q1860": "en",
}
DISCOVERY_LANGUAGE_VALUES = " ".join(f"wd:{qid}" for qid in INDIC_LANGUAGE_QIDS)
TOP_CAST_LIMIT = 12


class WikidataClient:
    def __init__(
        self,
        *,
        fixture_mode: bool = False,
        cache_dir: Path = CACHE_DIR / "wikidata",
        fixture_dir: Path = FIXTURE_DIR,
        soft_ttl_hours: int = 24,
    ) -> None:
        self.fixture_mode = fixture_mode
        self.cache_dir = cache_dir
        self.fixture_dir = fixture_dir
        self.soft_ttl = timedelta(hours=soft_ttl_hours)

    def fetch_by_qid(self, qid: str) -> dict[str, Any]:
        normalized_qid = normalize_qid(qid)
        raw = self._sparql(
            metadata_query(normalized_qid),
            fixture_name=f"wikidata_entity_{normalized_qid}.json",
        )
        return normalize_metadata(raw, qid=normalized_qid)

    def discover(self, date_from: str, date_to: str) -> dict[str, Any]:
        raw = self._sparql(
            discover_query(date_from, date_to),
            fixture_name=f"wikidata_discover_{date_from}_{date_to}.json",
        )
        return normalize_discovery(raw, date_from=date_from, date_to=date_to)

    def revisions_check(self, qid: str) -> str | None:
        normalized_qid = normalize_qid(qid)
        raw = self._request_json(
            f"{WIKIDATA_REST_BASE}/v1/page/{quote(normalized_qid)}/history",
            params={"limit": 1},
            fixture_name=f"wikidata_revisions_{normalized_qid}.json",
            accept=JSON_ACCEPT,
            source="wikidata_revisions",
        )
        return latest_revision_timestamp(raw)

    def probe(self, qid: str, *, resolve_label: str) -> dict[str, Any]:
        normalized_qid = normalize_qid(qid)
        raw = self._sparql(
            probe_query(normalized_qid, resolve_label),
            fixture_name=f"wikidata_probe_{normalized_qid}.json",
        )
        return normalize_probe(raw, qid=normalized_qid, resolve_label=resolve_label)

    def _sparql(self, query: str, *, fixture_name: str) -> dict[str, Any]:
        return self._request_json(
            SPARQL_ENDPOINT,
            params={"query": query},
            fixture_name=fixture_name,
            accept=SPARQL_ACCEPT,
            source="wikidata",
        )

    def _request_json(
        self,
        url: str,
        *,
        params: dict[str, Any],
        fixture_name: str,
        accept: str,
        source: str,
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
                    "results": {"bindings": []},
                }
            if isinstance(fixture, dict):
                fixture = dict(fixture)
                fixture.setdefault("_fetched_at", utc_now())
                fixture.setdefault("_cache_status", "fixture")
            return fixture

        cache_path = self._cache_path(url, params)
        cached = read_json(cache_path, default=None)
        if cached and self._is_fresh(cached.get("fetched_at")):
            payload = cached.get("payload", {})
            if isinstance(payload, dict):
                payload.setdefault("_cache_status", "fresh")
                payload.setdefault("_fetched_at", cached.get("fetched_at"))
            return payload

        headers = {
            "Accept": accept,
            "User-Agent": WIKIDATA_USER_AGENT,
        }
        if cached:
            if cached.get("etag"):
                headers["If-None-Match"] = cached["etag"]
            if cached.get("last_modified"):
                headers["If-Modified-Since"] = cached["last_modified"]

        request_url = f"{url}?{urlencode(params)}" if params else url
        request = Request(request_url, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=30) as response:
                status = response.status
                if status == 304 and cached:
                    cached["fetched_at"] = utc_now()
                    write_json(cache_path, cached)
                    payload = cached.get("payload", {})
                    if isinstance(payload, dict):
                        payload.setdefault("_cache_status", "not_modified")
                        payload.setdefault("_fetched_at", cached.get("fetched_at"))
                    return payload
                body = response.read().decode("utf-8")
                payload = json.loads(body)
                fetched_at = utc_now()
                write_json(
                    cache_path,
                    {
                        "url": url,
                        "params_hash": sha256_text(urlencode(sorted(params.items()))),
                        "etag": response.headers.get("ETag"),
                        "last_modified": response.headers.get("Last-Modified"),
                        "fetched_at": fetched_at,
                        "payload": payload,
                    },
                )
                if isinstance(payload, dict):
                    payload.setdefault("_cache_status", "live")
                    payload.setdefault("_fetched_at", fetched_at)
                return payload
        except HTTPError as exc:
            if exc.code == 304 and cached:
                cached["fetched_at"] = utc_now()
                write_json(cache_path, cached)
                payload = cached.get("payload", {})
                if isinstance(payload, dict):
                    payload.setdefault("_cache_status", "not_modified")
                    payload.setdefault("_fetched_at", cached.get("fetched_at"))
                return payload
            if exc.code == 429 or exc.code >= 500:
                return self._stale_or_error(cached, f"http_{exc.code}", source=source)
            return {
                "enrichment_skipped": True,
                "source": source,
                "error": f"http_{exc.code}",
                "_fetched_at": utc_now(),
                "results": {"bindings": []},
            }
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            return self._stale_or_error(cached, f"request_error:{exc.__class__.__name__}", source=source)

    def _stale_or_error(self, cached: dict[str, Any] | None, reason: str, *, source: str) -> dict[str, Any]:
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
            "source": source,
            "error": reason,
            "_fetched_at": utc_now(),
            "results": {"bindings": []},
        }

    def _is_fresh(self, fetched_at: str | None) -> bool:
        parsed = parse_datetime(fetched_at)
        if not parsed:
            return False
        return datetime.now(timezone.utc) - parsed <= self.soft_ttl

    def _cache_path(self, url: str, params: dict[str, Any]) -> Path:
        cache_key = sha256_text(f"{url}?{urlencode(sorted(params.items()))}")
        return self.cache_dir / f"{cache_key}.json"


def normalize_qid(value: str) -> str:
    text = str(value).strip()
    if text.startswith("http://www.wikidata.org/entity/") or text.startswith("https://www.wikidata.org/entity/"):
        text = text.rsplit("/", 1)[-1]
    if not text.startswith("Q") or not text[1:].isdigit():
        raise ValueError(f"Invalid Wikidata QID: {value}")
    return text


def metadata_query(qid: str) -> str:
    return f"""
SELECT ?film ?filmLabel ?originalLanguage ?originalLanguageLabel ?publicationDate ?director ?directorLabel
       ?cast ?castLabel ?castOrder ?company ?companyLabel ?country ?countryLabel ?duration
WHERE {{
  VALUES ?film {{ wd:{qid} }}
  OPTIONAL {{ ?film wdt:P364 ?originalLanguage. }}
  OPTIONAL {{ ?film wdt:P577 ?publicationDate. }}
  OPTIONAL {{ ?film wdt:P2047 ?duration. }}
  OPTIONAL {{ ?film wdt:P57 ?director. }}
  OPTIONAL {{
    ?film p:P161 ?castStatement.
    ?castStatement ps:P161 ?cast.
    OPTIONAL {{ ?castStatement pq:P1545 ?castOrder. }}
  }}
  OPTIONAL {{ ?film wdt:P272 ?company. }}
  OPTIONAL {{ ?film wdt:P495 ?country. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,hi,ta,te,ml,kn". }}
}}
ORDER BY ?castOrder ?castLabel
LIMIT 300
""".strip()


def discover_query(date_from: str, date_to: str) -> str:
    return f"""
SELECT ?film ?filmLabel ?publicationDate ?originalLanguage ?originalLanguageLabel ?country ?countryLabel
WHERE {{
  ?film wdt:P31/wdt:P279* wd:Q11424;
        wdt:P577 ?publicationDate;
        wdt:P364 ?originalLanguage.
  VALUES ?originalLanguage {{ {DISCOVERY_LANGUAGE_VALUES} }}
  FILTER(?publicationDate >= "{date_from}T00:00:00Z"^^xsd:dateTime)
  FILTER(?publicationDate <= "{date_to}T23:59:59Z"^^xsd:dateTime)
  OPTIONAL {{ ?film wdt:P495 ?country. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,hi,ta,te,ml,kn". }}
}}
ORDER BY ?publicationDate ?filmLabel
LIMIT 500
""".strip()


def probe_query(qid: str, resolve_label: str) -> str:
    safe_label = resolve_label.replace("\\", "\\\\").replace('"', '\\"')
    return f"""
SELECT ?kind ?film ?filmLabel ?originalLanguage ?originalLanguageLabel ?publicationDate ?director ?directorLabel
       ?cast ?castLabel ?castOrder ?company ?companyLabel ?country ?countryLabel ?duration
WHERE {{
  {{
    BIND("metadata" AS ?kind)
    VALUES ?film {{ wd:{qid} }}
    OPTIONAL {{ ?film wdt:P364 ?originalLanguage. }}
    OPTIONAL {{ ?film wdt:P577 ?publicationDate. }}
    OPTIONAL {{ ?film wdt:P2047 ?duration. }}
    OPTIONAL {{ ?film wdt:P57 ?director. }}
    OPTIONAL {{
      ?film p:P161 ?castStatement.
      ?castStatement ps:P161 ?cast.
      OPTIONAL {{ ?castStatement pq:P1545 ?castOrder. }}
    }}
    OPTIONAL {{ ?film wdt:P272 ?company. }}
    OPTIONAL {{ ?film wdt:P495 ?country. }}
  }}
  UNION
  {{
    BIND("label_match" AS ?kind)
    ?film rdfs:label "{safe_label}"@en;
          wdt:P31/wdt:P279* wd:Q11424.
    OPTIONAL {{ ?film wdt:P364 ?originalLanguage. }}
    OPTIONAL {{ ?film wdt:P577 ?publicationDate. }}
    OPTIONAL {{ ?film wdt:P495 ?country. }}
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,hi,ta,te,ml,kn". }}
}}
ORDER BY ?kind ?castOrder ?filmLabel
LIMIT 350
""".strip()


def normalize_metadata(raw: dict[str, Any], *, qid: str) -> dict[str, Any]:
    fetched_at = raw.get("_fetched_at", utc_now())
    bindings = list((raw.get("results") or {}).get("bindings") or [])
    first = bindings[0] if bindings else {}
    title = binding_value(first, "filmLabel")
    language_qid = entity_qid(binding_value(first, "originalLanguage"))
    release_date = date_value(binding_value(first, "publicationDate"))
    duration = numeric_value(binding_value(first, "duration"))

    return {
        "schema": "wikidata-metadata/v1",
        "qid": source_value(qid, "wikidata", fetched_at=fetched_at),
        "title": source_value(title, "wikidata", fetched_at=fetched_at, confidence="verified" if title else "unverified"),
        "original_language": source_value(
            INDIC_LANGUAGE_QIDS.get(language_qid, language_qid),
            "wikidata",
            fetched_at=fetched_at,
            confidence="verified" if language_qid else "unverified",
        ),
        "release_date": source_value(
            release_date,
            "wikidata",
            fetched_at=fetched_at,
            confidence="verified" if release_date else "unverified",
        ),
        "duration_min": source_value(duration, "wikidata", fetched_at=fetched_at, confidence="verified" if duration else "unverified"),
        "crew": source_value(
            {"director": people_from_bindings(bindings, entity_key="director", label_key="directorLabel")},
            "wikidata",
            fetched_at=fetched_at,
        ),
        "cast": source_value(cast_from_bindings(bindings), "wikidata", fetched_at=fetched_at),
        "production_companies": source_value(
            people_from_bindings(bindings, entity_key="company", label_key="companyLabel"),
            "wikidata",
            fetched_at=fetched_at,
        ),
        "countries": source_value(
            people_from_bindings(bindings, entity_key="country", label_key="countryLabel"),
            "wikidata",
            fetched_at=fetched_at,
        ),
        "enrichment_skipped": bool(raw.get("enrichment_skipped")),
        "_provenance": {
            "source": "wikidata",
            "fetched_at": fetched_at,
            "cache_status": raw.get("_cache_status", "fixture"),
        },
        "_quarantine": [],
    }


def normalize_discovery(raw: dict[str, Any], *, date_from: str, date_to: str) -> dict[str, Any]:
    fetched_at = raw.get("_fetched_at", utc_now())
    films: dict[str, dict[str, Any]] = {}
    for binding in (raw.get("results") or {}).get("bindings") or []:
        qid = entity_qid(binding_value(binding, "film"))
        if not qid:
            continue
        country = entity_payload(binding, "country", "countryLabel")
        record = films.setdefault(
            qid,
            {
                "qid": qid,
                "title": binding_value(binding, "filmLabel"),
                "release_date": date_value(binding_value(binding, "publicationDate")),
                "original_language": INDIC_LANGUAGE_QIDS.get(entity_qid(binding_value(binding, "originalLanguage")) or ""),
                "countries": [],
            },
        )
        if country and country not in record["countries"]:
            record["countries"].append(country)
    return {
        "schema": "wikidata-discovery/v1",
        "source": "wikidata",
        "fetched_at": fetched_at,
        "date_from": date_from,
        "date_to": date_to,
        "enrichment_skipped": bool(raw.get("enrichment_skipped")),
        "results": sorted(films.values(), key=lambda item: (item.get("release_date") or "", item.get("title") or "")),
    }


def normalize_probe(raw: dict[str, Any], *, qid: str, resolve_label: str) -> dict[str, Any]:
    bindings = list((raw.get("results") or {}).get("bindings") or [])
    metadata_bindings = [binding for binding in bindings if binding_value(binding, "kind") == "metadata"]
    label_bindings = [binding for binding in bindings if binding_value(binding, "kind") == "label_match"]
    return {
        "schema": "wikidata-live-probe/v1",
        "metadata": normalize_metadata({**raw, "results": {"bindings": metadata_bindings}}, qid=qid),
        "resolved_label": resolve_label,
        "label_matches": normalize_label_matches(label_bindings),
        "enrichment_skipped": bool(raw.get("enrichment_skipped")),
    }


def normalize_label_matches(bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        qid = entity_qid(binding_value(binding, "film"))
        if not qid:
            continue
        country = entity_payload(binding, "country", "countryLabel")
        record = matches.setdefault(
            qid,
            {
                "qid": qid,
                "title": binding_value(binding, "filmLabel"),
                "release_date": date_value(binding_value(binding, "publicationDate")),
                "original_language": INDIC_LANGUAGE_QIDS.get(entity_qid(binding_value(binding, "originalLanguage")) or ""),
                "countries": [],
            },
        )
        if country and country not in record["countries"]:
            record["countries"].append(country)
    return sorted(matches.values(), key=lambda item: (item.get("release_date") or "", item.get("title") or ""))


def binding_value(binding: dict[str, Any], key: str) -> str | None:
    value = binding.get(key)
    if isinstance(value, dict):
        return value.get("value")
    return None


def entity_qid(value: str | None) -> str | None:
    if not value:
        return None
    text = value.rsplit("/", 1)[-1]
    return text if text.startswith("Q") and text[1:].isdigit() else None


def date_value(value: str | None) -> str | None:
    return value[:10] if value else None


def numeric_value(value: str | None) -> int | float | None:
    if not value:
        return None
    try:
        numeric = float(value)
    except ValueError:
        return None
    return int(numeric) if numeric.is_integer() else numeric


def people_from_bindings(bindings: list[dict[str, Any]], *, entity_key: str, label_key: str) -> list[dict[str, str]]:
    seen: set[str] = set()
    output: list[dict[str, str]] = []
    for binding in bindings:
        qid = entity_qid(binding_value(binding, entity_key))
        label = binding_value(binding, label_key)
        if not qid or qid in seen:
            continue
        seen.add(qid)
        output.append({"name": label or qid, "qid": qid})
    return output


def cast_from_bindings(bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_qid: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        qid = entity_qid(binding_value(binding, "cast"))
        if not qid or qid in by_qid:
            continue
        order = cast_order(binding_value(binding, "castOrder"))
        by_qid[qid] = {
            "name": binding_value(binding, "castLabel") or qid,
            "qid": qid,
            "order": order,
        }
    return sorted(
        by_qid.values(),
        key=lambda item: (item["order"] is None, item["order"] if item["order"] is not None else 9999, item["name"]),
    )[:TOP_CAST_LIMIT]


def cast_order(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def entity_payload(binding: dict[str, Any], entity_key: str, label_key: str) -> dict[str, str] | None:
    qid = entity_qid(binding_value(binding, entity_key))
    if not qid:
        return None
    return {"name": binding_value(binding, label_key) or qid, "qid": qid}


def latest_revision_timestamp(raw: dict[str, Any]) -> str | None:
    if raw.get("enrichment_skipped"):
        return None
    for key in ("revisions", "latest"):
        value = raw.get(key)
        if isinstance(value, list) and value:
            timestamp = value[0].get("timestamp") or value[0].get("time")
            if timestamp:
                return timestamp
        if isinstance(value, dict):
            timestamp = value.get("timestamp") or value.get("time")
            if timestamp:
                return timestamp
    items = raw.get("items")
    if isinstance(items, list) and items:
        timestamp = items[0].get("timestamp") or items[0].get("time")
        if timestamp:
            return timestamp
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch Wikidata metadata, discovery windows, or revision timestamps.")
    parser.add_argument("--fixture-mode", action="store_true", help="Read from data/cache/fixtures instead of Wikidata.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    metadata = subparsers.add_parser("metadata")
    metadata.add_argument("--qid", required=True)

    discover = subparsers.add_parser("discover")
    discover.add_argument("--date-from", required=True)
    discover.add_argument("--date-to", required=True)

    revisions = subparsers.add_parser("revisions")
    revisions.add_argument("--qid", required=True)

    probe = subparsers.add_parser("probe")
    probe.add_argument("--qid", required=True)
    probe.add_argument("--resolve-label", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = WikidataClient(fixture_mode=args.fixture_mode)
    if args.command == "metadata":
        payload: Any = client.fetch_by_qid(args.qid)
    elif args.command == "discover":
        payload = client.discover(args.date_from, args.date_to)
    elif args.command == "probe":
        payload = client.probe(args.qid, resolve_label=args.resolve_label)
    else:
        payload = {
            "schema": "wikidata-revision-check/v1",
            "qid": normalize_qid(args.qid),
            "latest_revision_timestamp": client.revisions_check(args.qid),
        }

    json.dump(payload, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
