"""Honesty fence for the /box-office/ hub page.

Confirmed 2026-08-30: bollyai.in/box-office/ had rendered "0 Films tracked" over an empty
table for 75 days on a top-level nav-linked page, complete with Dataset and ItemList
structured data describing a dataset that does not exist. The blocker is supplier
procurement (SOURCE-PROCUREMENT-20260809.md), not code, so the page must state that it has
no data instead of impersonating a live tracker - and must never be filled with invented rows.
"""
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
PAGE = REPO_ROOT / "site" / "app" / "box-office" / "page.tsx"
SITEMAP_BUILDER = REPO_ROOT / "site" / "scripts" / "build-sitemaps.mjs"
CURRENT_WEEK = REPO_ROOT / "data" / "boxoffice" / "current-week.json"


def page_source() -> str:
    return PAGE.read_text(encoding="utf-8")


def board() -> dict:
    return json.loads(CURRENT_WEEK.read_text(encoding="utf-8"))


def test_page_branches_on_a_published_board_before_rendering_anything():
    source = page_source()

    assert 'const boardIsPublished = board.status === "ready" && board.records.length > 0;' in source
    assert "if (!boardIsPublished) {\n    return <BoxOfficeUnavailable" in source
    assert "function BoxOfficeUnavailable(" in source


def test_unavailable_branch_publishes_no_structured_data_and_no_empty_table():
    source = page_source()
    unavailable = source[source.index("function BoxOfficeUnavailable("):]

    assert "JsonLd" not in unavailable, "structured data must not describe an absent dataset"
    assert "BoxOfficeBoardTable" not in unavailable, "no empty board table"
    assert "BoxOfficeLeaderboard" not in unavailable
    assert "Films tracked" not in unavailable, "a films-tracked count of zero reads as live data"
    assert "Data unavailable" in unavailable


def test_unavailable_branch_is_noindex():
    source = page_source()
    fallback = source[source.index("  : {"):source.index("export default function")]

    assert "robots: { index: false, follow: true }" in fallback


def test_sitemap_drops_box_office_while_it_is_noindex():
    assert "if (p === \"/box-office/\" && !boxOfficeIsPublished) continue;" in SITEMAP_BUILDER.read_text(
        encoding="utf-8"
    )


def test_shipped_board_never_carries_unsourced_rows():
    """The empty state is honest only while the data itself stays honest."""
    payload = board()

    assert payload["status"] in {"ready", "data_pending"}
    if payload["status"] == "data_pending":
        assert payload["records"] == []
    for record in payload["records"]:
        assert record["week_gross_usd"]["value"] is None or record["week_gross_usd"]["sources"]


def test_page_carries_no_hardcoded_gross_figures():
    """No number may be typed into the page - every figure must come from the board data."""
    unavailable = page_source()[page_source().index("function BoxOfficeUnavailable("):]

    assert not re.search(r"\$\s?\d", unavailable)
    assert "million" not in unavailable.lower()
