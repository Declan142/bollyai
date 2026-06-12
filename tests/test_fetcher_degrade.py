from pathlib import Path
import sys
from urllib.error import HTTPError


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "engine" / "fetchers"))

import boxoffice  # noqa: E402
import wikidata  # noqa: E402
from common import write_json  # noqa: E402


def test_wikidata_429_returns_stale_cached_payload(monkeypatch, tmp_path):
    client = wikidata.WikidataClient(fixture_mode=False, cache_dir=tmp_path)
    query = wikidata.metadata_query("Q1")
    cache_path = client._cache_path(wikidata.SPARQL_ENDPOINT, {"query": query})
    write_json(
        cache_path,
        {
            "fetched_at": "2026-01-01T00:00:00Z",
            "payload": {
                "results": {
                    "bindings": [
                        {
                            "filmLabel": {"value": "Cached Film"},
                            "film": {"value": "http://www.wikidata.org/entity/Q1"},
                        }
                    ]
                }
            },
        },
    )

    def raise_429(*_args, **_kwargs):
        raise HTTPError("https://query.wikidata.org/sparql", 429, "Too Many Requests", None, None)

    monkeypatch.setattr(wikidata, "urlopen", raise_429)

    result = client.fetch_by_qid("Q1")

    assert result["enrichment_skipped"] is True
    assert result["title"]["value"] == "Cached Film"
    assert result["_provenance"]["cache_status"] == "stale"


def test_wikidata_missing_fixture_degrades_to_skipped_metadata():
    client = wikidata.WikidataClient(fixture_mode=True, fixture_dir=Path("/tmp/bollyai-missing-fixtures"))

    result = client.fetch_by_qid("Q999999")

    assert result["enrichment_skipped"] is True
    assert result["title"]["value"] is None
    assert result["qid"]["value"] == "Q999999"


def test_boxoffice_primary_403_returns_empty_readings(monkeypatch):
    class Response:
        status_code = 403
        text = ""

    class Requests:
        @staticmethod
        def get(*_args, **_kwargs):
            return Response()

    monkeypatch.setattr(boxoffice, "requests", Requests)

    readings = boxoffice.fetch_sacnilk_primary(qid="QBOX", url="https://example.com/blocked")

    assert readings == []


def test_boxoffice_empty_feed_returns_empty_readings():
    assert boxoffice.parse_sacnilk_payload({"html": ""}, qid="QBOX") == []
