"""Gates for the Western OTT fetch path (engine/fetchers/ott_western.py + regen wiring).

Born from the 2026-07-07 R0 diagnosis: the Wikidata query shipped with wdt:P4947
(TMDb film ID, a string identifier) where wdt:P449 (original broadcaster) was meant,
so platform originals never matched and the fetch returned 0 rows forever; TMDB
entries shipped a fabricated platform "Streaming". These tests lock both fixes.
"""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "engine" / "fetchers"))
sys.path.insert(0, str(REPO_ROOT / "engine"))

from ott_western import resolve_tmdb_platform, wikidata_ott_query  # noqa: E402
from regen_ott_weekly import merge_announcement_entries  # noqa: E402


def test_wikidata_query_targets_broadcaster_not_tmdb_id():
    query = wikidata_ott_query(start_s="2026-07-06T00:00:00Z", end_s="2026-07-20T00:00:00Z")
    assert "wdt:P449" in query, "originals branch must use P449 (original broadcaster)"
    assert "P4947" not in query, "P4947 is TMDb film ID - it can never bind a platform QID"
    assert "wdt:P750" in query, "distributor branch (films) must stay"
    assert '"2026-07-06T00:00:00Z"' in query and '"2026-07-20T00:00:00Z"' in query


def test_resolve_tmdb_platform_maps_target_provider():
    payload = {"results": {"US": {"flatrate": [{"provider_id": 8, "provider_name": "Netflix"}]}}}
    assert resolve_tmdb_platform(payload) == "Netflix"


def test_resolve_tmdb_platform_prefers_flatrate_bucket():
    payload = {
        "results": {
            "US": {
                "ads": [{"provider_id": 8}],
                "flatrate": [{"provider_id": 337}],
            }
        }
    }
    assert resolve_tmdb_platform(payload) == "Disney+"


def test_resolve_tmdb_platform_refuses_to_guess():
    assert resolve_tmdb_platform(None) is None
    assert resolve_tmdb_platform({}) is None
    assert resolve_tmdb_platform({"results": {}}) is None
    # a provider outside the 8 tracked platforms is not a target platform
    payload = {"results": {"US": {"flatrate": [{"provider_id": 999, "provider_name": "Obscure+"}]}}}
    assert resolve_tmdb_platform(payload) is None
    # rent/buy buckets do not make a title a streaming release
    payload = {"results": {"US": {"rent": [{"provider_id": 8}], "buy": [{"provider_id": 8}]}}}
    assert resolve_tmdb_platform(payload) is None


def test_merge_dedupes_by_qid_and_id_and_appends_fresh():
    existing = [
        {"id": "series-old-show", "qid": "Q111", "platform": "Netflix", "title": "Old Show"},
    ]
    fetched = [
        # dupe by qid, different id: curated entry wins, nothing appended
        {"id": "series-old-show-remaster", "qid": "Q111", "platform": "Netflix", "title": "Old Show"},
        # dupe by id, no qid (TMDB path re-finding a Wikidata entry): skipped
        {"id": "series-old-show", "qid": None, "platform": "Netflix", "title": "Old Show"},
        # same title on a DIFFERENT platform is a real, distinct announcement
        {"id": "series-old-show", "qid": None, "platform": "Hulu", "title": "Old Show"},
        # fresh entry appended
        {"id": "film-new-film", "qid": "Q222", "platform": "Prime Video", "title": "New Film"},
    ]
    merged = merge_announcement_entries(existing, fetched)
    assert merged[0] is existing[0], "curated entries keep their position and identity"
    assert [e["id"] for e in merged] == ["series-old-show", "series-old-show", "film-new-film"]
    assert [e["platform"] for e in merged] == ["Netflix", "Hulu", "Prime Video"]


def test_merge_dedupes_within_a_single_fetch():
    fetched = [
        {"id": "series-x", "qid": "Q1", "platform": "Max", "title": "X"},
        {"id": "series-x", "qid": None, "platform": "Max", "title": "X"},
    ]
    merged = merge_announcement_entries([], fetched)
    assert len(merged) == 1


def test_merge_is_append_only():
    existing = [
        {"id": "series-a", "qid": "Q1", "platform": "Netflix", "title": "A"},
        {"id": "series-b", "qid": "Q2", "platform": "Hulu", "title": "B"},
    ]
    merged = merge_announcement_entries(existing, [])
    assert merged == existing
