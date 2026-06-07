#!/usr/bin/env python3
"""Ping IndexNow with changed URLs or every URL from a sitemap."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE = REPO_ROOT / "data/_state/indexnow_ping_state.json"
DEFAULT_ENDPOINT = "https://api.indexnow.org/indexnow"
DEFAULT_HOST = "bollyai.in"
USER_AGENT = "BollyAI-IndexNow/1.0 (+https://bollyai.in)"
MAX_URLS_PER_REQUEST = 10000


def die(message: str) -> int:
    print(f"indexnow_ping.py: {message}", file=sys.stderr)
    return 1


def load_state(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_urls(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    clean: list[str] = []
    for raw in urls:
        url = str(raw).strip()
        if not url or url in seen:
            continue
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            continue
        seen.add(url)
        clean.append(url)
    return sorted(clean)


def urls_from_delta(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return [line.strip() for line in raw.splitlines() if line.strip()]

    if isinstance(payload, list):
        return [str(item) for item in payload]

    if isinstance(payload, dict):
        for key in ("urls", "changed_urls", "changedUrls", "urlList", "delta"):
            value = payload.get(key)
            if isinstance(value, list):
                return [str(item) for item in value]

    return []


def read_location(location: str, timeout: int) -> bytes:
    parsed = urllib.parse.urlparse(location)
    if parsed.scheme in ("http", "https"):
        request = urllib.request.Request(location, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    return Path(location).read_bytes()


def xml_tag_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def urls_from_sitemap(location: str, timeout: int, depth: int = 0) -> list[str]:
    if depth > 3:
        raise ValueError("sitemap recursion exceeded 3 levels")

    content = read_location(location, timeout)
    root = ET.fromstring(content)
    tag = xml_tag_name(root.tag)

    urls: list[str] = []
    if tag == "urlset":
        for loc in root.iter():
            if xml_tag_name(loc.tag) == "loc" and loc.text:
                urls.append(loc.text.strip())
        return urls

    if tag == "sitemapindex":
        for loc in root.iter():
            if xml_tag_name(loc.tag) != "loc" or not loc.text:
                continue
            child = loc.text.strip()
            urls.extend(urls_from_sitemap(child, timeout, depth + 1))
        return urls

    raise ValueError(f"unsupported sitemap root: {tag}")


def fingerprint(urls: list[str], host: str) -> str:
    digest = hashlib.sha256()
    digest.update(host.encode("utf-8"))
    digest.update(b"\n")
    for url in urls:
        digest.update(url.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def retry_after_seconds(headers: Any) -> int:
    value = headers.get("Retry-After") if headers else None
    if not value:
        return 900
    try:
        return max(300, int(value))
    except ValueError:
        return 900


def post_indexnow(
    endpoint: str,
    host: str,
    key: str,
    url_batch: list[str],
    timeout: int,
) -> tuple[bool, int | None]:
    payload = {
        "host": host,
        "key": key,
        "keyLocation": f"https://{host}/{key}.txt",
        "urlList": url_batch,
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if 200 <= response.status < 300:
                return True, None
            print(f"IndexNow returned HTTP {response.status}", file=sys.stderr)
            return False, None
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            return False, retry_after_seconds(exc.headers)
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"IndexNow HTTP {exc.code}: {detail}", file=sys.stderr)
        return False, None
    except urllib.error.URLError as exc:
        print(f"IndexNow network error: {exc}", file=sys.stderr)
        return False, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--delta", help="JSON or newline file with changed URLs.")
    group.add_argument("--all", dest="sitemap", help="Sitemap XML path or URL.")
    parser.add_argument("--host", default=os.environ.get("INDEXNOW_HOST", DEFAULT_HOST))
    parser.add_argument("--key", default=os.environ.get("INDEXNOW_KEY", ""))
    parser.add_argument("--endpoint", default=os.environ.get("INDEXNOW_ENDPOINT", DEFAULT_ENDPOINT))
    parser.add_argument("--state", default=str(DEFAULT_STATE))
    parser.add_argument("--floor-seconds", type=int, default=300)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.delta:
            urls = urls_from_delta(Path(args.delta))
        else:
            urls = urls_from_sitemap(args.sitemap, args.timeout)
    except (OSError, ET.ParseError, ValueError, urllib.error.URLError) as exc:
        return die(str(exc))

    urls = normalize_urls(urls)
    if not urls:
        print("IndexNow: no URLs to ping.")
        return 0

    current_hash = fingerprint(urls, args.host)
    state_path = Path(args.state)
    state = load_state(state_path)
    now = time.time()

    backoff_until = float(state.get("backoff_until", 0) or 0)
    if not args.force and backoff_until > now:
        wait = int(backoff_until - now)
        print(f"IndexNow: in 429 backoff for {wait}s; skipping.")
        return 0

    if not args.force and state.get("last_hash") == current_hash:
        print("IndexNow: content hash unchanged; skipping.")
        return 0

    last_ping_at = float(state.get("last_ping_at", 0) or 0)
    elapsed = now - last_ping_at
    if not args.force and elapsed < args.floor_seconds:
        wait = int(args.floor_seconds - elapsed)
        print(f"IndexNow: 5-minute floor active for {wait}s; skipping.")
        return 0

    if args.dry_run:
        print(f"IndexNow dry-run: {len(urls)} URL(s) for host {args.host}.")
        for url in urls[:10]:
            print(url)
        if len(urls) > 10:
            print(f"... {len(urls) - 10} more")
        return 0

    if not args.key:
        return die("INDEXNOW_KEY is required unless --dry-run is used")

    for index, url_batch in enumerate(chunks(urls, MAX_URLS_PER_REQUEST), start=1):
        ok, retry_after = post_indexnow(args.endpoint, args.host, args.key, url_batch, args.timeout)
        if not ok:
            if retry_after is not None:
                state["backoff_until"] = now + retry_after
                save_state(state_path, state)
                print(f"IndexNow: HTTP 429; backing off for {retry_after}s.")
                return 0
            return 1
        print(f"IndexNow: submitted batch {index} with {len(url_batch)} URL(s).")

    state.update(
        {
            "last_hash": current_hash,
            "last_ping_at": now,
            "last_count": len(urls),
            "host": args.host,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            "backoff_until": 0,
        }
    )
    save_state(state_path, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
