from pathlib import Path
import json
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "engine" / "fetchers"))

from boxoffice import SourceReading, publish_rule


def reading(source: str, value: float) -> SourceReading:
    return SourceReading(
        qid="QBOX",
        date="2026-06-12",
        metric="india_net",
        value=value,
        source=source,
        url=f"https://example.com/{source}",
    )


def test_boxoffice_rule_publishes_trade_estimate_inside_10_percent():
    decision = publish_rule([reading("Sacnilk", 100), reading("TrackTollywood", 108)])

    assert decision["published"] is True
    assert decision["framing"] == "trade_estimate"
    assert decision["net_inr_cr"] == {"low": 100, "high": 108}


def test_boxoffice_rule_publishes_lower_figure_for_10_to_25_percent_gap():
    decision = publish_rule([reading("Sacnilk", 100), reading("TrackTollywood", 120)])

    assert decision["published"] is True
    assert decision["framing"] == "lower_conservative"
    assert decision["net_inr_cr"] == {"low": 100, "high": 100}


def test_boxoffice_rule_tracks_when_sources_diverge_over_25_percent():
    decision = publish_rule([reading("Sacnilk", 100), reading("TrackTollywood", 140)])

    assert decision["published"] is False
    assert decision["framing"] == "awaited"
    assert decision["net_inr_cr"] is None


def test_boxoffice_rule_rejects_pr_only_pairs():
    decision = publish_rule([reading("Bollywood Hungama", 100), reading("Taran Adarsh", 101)])

    assert decision["published"] is False
    assert decision["reason"] == "single_source_or_no_valid_independent_pair"


def test_current_week_schema_stays_tracking_while_data_pending():
    path = REPO_ROOT / "data" / "boxoffice" / "current-week.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["schema"] == "bollyai-boxoffice-week/v1"
    assert payload["DATA_PENDING"] is True
    assert payload["records"]

    rank = {
        "tollywood": 0,
        "kollywood": 1,
        "mollywood": 2,
        "sandalwood": 3,
        "bollywood": 4,
        "hollywood": 5,
        "streaming": 6,
    }
    order = [rank[row["industry"]] for row in payload["records"]]
    assert order == sorted(order)

    for record in payload["records"]:
        assert record["territory"] == "India"
        assert record["week"]["start"] == payload["week"]["start"]
        assert record["week"]["end"] == payload["week"]["end"]
        assert "budget" not in json.dumps(record).lower()
        for key in ("india_net_inr_cr", "worldwide_gross_inr_cr"):
            figure = record[key]
            assert set(("value", "sources", "label")).issubset(figure)
            assert figure["value"] is None
            assert figure["label"] == "tracking"
            for source in figure["sources"]:
                assert source["name"].strip()
                assert source["url"].startswith("https://")
