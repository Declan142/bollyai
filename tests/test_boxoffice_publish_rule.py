from pathlib import Path
import json
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "engine" / "fetchers"))

from boxoffice import SourceReading, publish_rule
from boxoffice_week_schema import validate_board


def reading(source: str, value: float, *, metric: str = "india_net", territory: str = "India") -> SourceReading:
    return SourceReading(
        qid="QBOX",
        date="2026-06-12",
        metric=metric,
        value=value,
        source=source,
        url=f"https://example.com/{source}",
        territory=territory,
    )


def test_boxoffice_rule_publishes_trade_estimate_inside_10_percent():
    decision = publish_rule([reading("Sacnilk", 100), reading("TrackTollywood", 108)])

    assert decision["published"] is True
    assert decision["framing"] == "trade_estimate"
    assert decision["net_inr_cr"] == {"low": 100, "high": 100}
    assert decision["caveat"] is False


def test_boxoffice_rule_publishes_lower_figure_for_10_to_25_percent_gap():
    decision = publish_rule([reading("Sacnilk", 100), reading("TrackTollywood", 120)])

    assert decision["published"] is True
    assert decision["framing"] == "lower_conservative"
    assert decision["net_inr_cr"] == {"low": 100, "high": 100}
    assert decision["caveat"] is True


def test_boxoffice_rule_tracks_when_sources_diverge_over_25_percent():
    decision = publish_rule([reading("Sacnilk", 100), reading("TrackTollywood", 140)])

    assert decision["published"] is False
    assert decision["framing"] == "awaited"
    assert decision["net_inr_cr"] is None


def test_boxoffice_rule_rejects_pr_only_pairs():
    decision = publish_rule([reading("Bollywood Hungama", 100), reading("Taran Adarsh", 101)])

    assert decision["published"] is False
    assert decision["reason"] == "single_source_or_no_valid_independent_pair"


def test_boxoffice_rule_rejects_budget_and_salary_metrics():
    decision = publish_rule(
        [
            reading("Sacnilk", 100, metric="budget"),
            reading("TrackTollywood", 101, metric="salary"),
        ]
    )

    assert decision["published"] is False
    assert decision["reason"] == "budget_or_salary_metric"


def test_boxoffice_rule_requires_same_metric_and_territory():
    decision = publish_rule(
        [
            reading("Sacnilk", 100, metric="india_net", territory="India"),
            reading("TrackTollywood", 102, metric="worldwide_gross", territory="Worldwide"),
        ]
    )

    assert decision["published"] is False
    assert decision["reason"] == "single_source_or_no_valid_independent_pair"


def test_current_week_schema_and_published_figures_are_source_gated():
    path = REPO_ROOT / "data" / "boxoffice" / "current-week.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    validate_board(payload)
    assert payload["schema"] == "bollyai-boxoffice-week/v3"
    assert payload["territory"] == "Worldwide"
    records = payload["records"]
    assert payload["status"] == ("data_pending" if len(records) == 0 else "ready")

    for record in records:
        assert record["territory"] == "Worldwide"
        assert record["industry"] in {"hollywood", "streaming"}
        assert record["week"]["start"] == payload["week"]["start"]
        assert record["week"]["end"] == payload["week"]["end"]
        assert "budget" not in json.dumps(record).lower()
        assert "salary" not in json.dumps(record).lower()

        figure = record["week_gross_usd"]
        assert figure["measurement"] == "exact_week"
        assert figure["period"] == payload["week"]
        assert figure["currency"] == "USD"
        if figure["value"] is None:
            assert figure["label"] == "tracking"
            continue

        assert isinstance(figure["value"], (int, float))
        assert len(figure["sources"]) >= 2
        assert len({source["group"] for source in figure["sources"]}) >= 2
        for source in figure["sources"]:
            assert source["name"].strip()
            assert source["url"].startswith("https://")
            assert source["metric"] == "week_gross_usd"
            assert source["measurement"] == "exact_week"
            assert source["period"] == payload["week"]
