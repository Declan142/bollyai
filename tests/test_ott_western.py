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


def test_fetch_unions_tmdb_and_wikidata_paths(monkeypatch):
    """2026-07-07 R2 find: TMDB discover is hard-filtered to original-language en, so it
    can NEVER see the Western-European (fr/de/es/it/pt) originals the brand lock keeps.
    Returning TMDB *instead of* Wikidata when TMDB is non-empty made every non-English
    Western original invisible on any run with a TMDB key (i.e. every GHA roll once the
    key is wired). The paths are complements - the fetch must union them."""
    import ott_western as ow

    en_entry = {"id": "film-english-hit", "qid": None, "platform": "Netflix", "title": "English Hit", "date": "2026-07-10"}
    fr_entry = {"id": "film-rien-a-perdre", "qid": "Q999", "platform": "Netflix", "title": "Rien a perdre", "date": "2026-07-08"}
    monkeypatch.setenv("TMDB_API_KEY", "test-key")
    monkeypatch.setattr(ow, "fetch_tmdb_ott", lambda **kw: [dict(en_entry)])
    monkeypatch.setattr(ow, "fetch_wikidata_ott", lambda **kw: [dict(fr_entry)])

    entries = ow.fetch_western_ott(window_start=None, window_end=None)
    ids = sorted(e["id"] for e in entries)
    assert ids == ["film-english-hit", "film-rien-a-perdre"], (
        "TMDB-with-results must not shadow the Wikidata path - Western-European originals live only there"
    )
    assert all(e.get("origin") == "fetched" for e in entries), "fetch-emitted entries must carry origin=fetched"


def test_fetch_union_prefers_wikidata_on_collision(monkeypatch):
    """Same title from both paths: keep ONE entry, and keep the Wikidata one - it carries the QID."""
    import ott_western as ow

    tmdb = {"id": "film-shared", "qid": None, "platform": "Max", "title": "Shared", "date": "2026-07-11"}
    wikidata = {"id": "film-shared", "qid": "Q42", "platform": "Max", "title": "Shared", "date": "2026-07-11"}
    monkeypatch.setenv("TMDB_API_KEY", "test-key")
    monkeypatch.setattr(ow, "fetch_tmdb_ott", lambda **kw: [dict(tmdb)])
    monkeypatch.setattr(ow, "fetch_wikidata_ott", lambda **kw: [dict(wikidata)])

    entries = ow.fetch_western_ott()
    assert len(entries) == 1
    assert entries[0]["qid"] == "Q42"


def test_merge_updates_moved_date_on_fetched_entries():
    """2026-07-07 R2 find: append-only meant a release date that MOVES upstream (platforms
    reschedule constantly) stayed wrong in the registry forever - the dedup key matched, the
    stale date won. Fetched-origin entries must take the corrected date; the update carries
    the newer sources and fetched_at with it."""
    existing = [
        {"id": "film-moved", "qid": None, "platform": "Netflix", "title": "Moved", "date": "2026-07-08",
         "origin": "fetched", "fetched_at": "2026-07-01T00:00:00Z",
         "sources": [{"name": "TMDB", "url": "https://example.com/old", "type": "press"}]},
    ]
    fetched = [
        {"id": "film-moved", "qid": None, "platform": "Netflix", "title": "Moved", "date": "2026-07-15",
         "origin": "fetched", "fetched_at": "2026-07-07T00:00:00Z",
         "sources": [{"name": "TMDB", "url": "https://example.com/new", "type": "press"}]},
    ]
    merged, stats = merge_announcement_entries(existing, fetched)
    assert len(merged) == 1, "a date move is a correction, not a new announcement"
    assert merged[0]["date"] == "2026-07-15"
    assert merged[0]["fetched_at"] == "2026-07-07T00:00:00Z"
    assert merged[0]["sources"][0]["url"] == "https://example.com/new"
    assert stats == {"added": 0, "updated": 1}


def test_merge_never_touches_curated_entries():
    """Curated entries (no origin field, or origin != fetched) are hand-verified - a fetched
    date NEVER overwrites them, matching the append-only 'curated wins' law."""
    existing = [
        {"id": "film-curated", "qid": None, "platform": "Netflix", "title": "Curated", "date": "2026-07-08",
         "sources": [{"name": "Wikipedia", "url": "https://en.wikipedia.org/wiki/X", "type": "press"}]},
    ]
    fetched = [
        {"id": "film-curated", "qid": None, "platform": "Netflix", "title": "Curated", "date": "2026-07-20",
         "origin": "fetched", "fetched_at": "2026-07-07T00:00:00Z",
         "sources": [{"name": "TMDB", "url": "https://example.com/t", "type": "press"}]},
    ]
    merged, stats = merge_announcement_entries(existing, fetched)
    assert len(merged) == 1
    assert merged[0]["date"] == "2026-07-08", "curated wins, always"
    assert merged[0]["sources"][0]["name"] == "Wikipedia"
    assert stats == {"added": 0, "updated": 0}


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
    merged, stats = merge_announcement_entries(existing, fetched)
    assert stats == {"added": 2, "updated": 0}
    assert merged[0] is existing[0], "curated entries keep their position and identity"
    assert [e["id"] for e in merged] == ["series-old-show", "series-old-show", "film-new-film"]
    assert [e["platform"] for e in merged] == ["Netflix", "Hulu", "Prime Video"]


def test_merge_dedupes_within_a_single_fetch():
    fetched = [
        {"id": "series-x", "qid": "Q1", "platform": "Max", "title": "X"},
        {"id": "series-x", "qid": None, "platform": "Max", "title": "X"},
    ]
    merged, _ = merge_announcement_entries([], fetched)
    assert len(merged) == 1


def test_doubled_run_does_not_grow_registry(tmp_path, monkeypatch):
    """Two rolls delivering the same fetch must leave the registry byte-stable - the
    append-only merge holds across RUNS, not just within one (real file I/O, no mocks
    below the fetch boundary)."""
    import regen_ott_weekly as regen

    registry = tmp_path / "ott" / "announcements.json"
    registry.parent.mkdir(parents=True)
    registry.write_text("[]")
    entry = {"id": "film-stable", "qid": "Q7", "platform": "Netflix", "title": "Stable",
             "date": "2026-07-10", "origin": "fetched", "fetched_at": "2026-07-07T00:00:00Z",
             "sources": [{"name": "Wikidata", "url": "https://www.wikidata.org/wiki/Q7", "type": "press"}]}
    monkeypatch.setattr(regen, "fetch_western_ott", lambda **kw: [dict(entry)])

    from datetime import date as _date
    stats1 = regen.refresh_registry(tmp_path, _date(2026, 7, 6), _date(2026, 7, 20))
    after_first = registry.read_text()
    stats2 = regen.refresh_registry(tmp_path, _date(2026, 7, 6), _date(2026, 7, 20))
    after_second = registry.read_text()

    assert stats1 == {"fetched": 1, "added": 1, "updated": 0}
    assert stats2 == {"fetched": 1, "added": 0, "updated": 0}
    assert after_first == after_second, "same fetch twice must not grow or rewrite the registry"


def test_no_fetch_rebuild_is_stamped_in_provenance(tmp_path, monkeypatch):
    """A registry-only rebuild must say so in the artifact - before 2026-07-07 a --no-fetch
    (or network-dead) run wrote a calendar indistinguishable from a fetch-refreshed one."""
    import json as _json
    import regen_ott_weekly as regen

    (tmp_path / "ott").mkdir(parents=True)
    (tmp_path / "ott" / "announcements.json").write_text("[]")
    monkeypatch.setattr(
        regen, "fetch_western_ott",
        lambda **kw: (_ for _ in ()).throw(AssertionError("--no-fetch must not fetch")),
    )
    monkeypatch.setattr(regen, "repo_path", lambda p: tmp_path)

    rc = regen.main(["--data-dir", str(tmp_path), "--no-fetch", "--today", "2026-07-07"])
    assert rc == 0
    calendar = _json.loads((tmp_path / "ott" / "calendar.json").read_text())
    refresh = calendar["_provenance"]["refresh"]
    assert refresh["mode"] == "no-fetch"
    assert refresh["fetched"] == 0 and refresh["added"] == 0 and refresh["updated"] == 0


def test_merge_is_append_only():
    existing = [
        {"id": "series-a", "qid": "Q1", "platform": "Netflix", "title": "A"},
        {"id": "series-b", "qid": "Q2", "platform": "Hulu", "title": "B"},
    ]
    merged, stats = merge_announcement_entries(existing, [])
    assert merged == existing
    assert stats == {"added": 0, "updated": 0}
