from pathlib import Path
import json
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "engine" / "fetchers"))

from boxoffice import BOXOFFICE_FIGURES, SourceReading, publish_rule


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

    assert payload["schema"] == "bollyai-boxoffice-week/v1"

    # Western-only brand (2026-06): a week with no source-gated Western box-office is a
    # valid empty/pending board. DATA_PENDING models exactly this state. The honesty
    # invariant (every published figure has >=2 source-gated readings, below) is unchanged.
    pending = payload.get("DATA_PENDING", False)
    if not pending:
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

    published_figures = 0
    for record in payload["records"]:
        assert record["territory"] == "India"
        assert record["week"]["start"] == payload["week"]["start"]
        assert record["week"]["end"] == payload["week"]["end"]
        assert "budget" not in json.dumps(record).lower()
        for key, metric in BOXOFFICE_FIGURES.items():
            figure = record[key]
            assert set(("value", "sources", "label")).issubset(figure)
            for source in figure["sources"]:
                assert source["name"].strip()
                assert source["url"].startswith("https://")
            if figure["value"] is None:
                assert figure["label"] == "tracking"
                continue

            published_figures += 1
            numeric_sources = [source for source in figure["sources"] if isinstance(source.get("value"), (int, float))]
            assert len(numeric_sources) >= 2, "ZERO figures without >=2-source envelopes"
            readings = [
                SourceReading(
                    qid=record["film"]["qid"] or "unknown",
                    date=source.get("as_of") or payload["generated_at"][:10],
                    metric=source.get("metric") or metric,
                    value=float(source["value"]),
                    source=source["name"],
                    url=source["url"],
                    fetched_at=source.get("fetched_at"),
                    territory=source.get("territory") or record["territory"],
                    week_start=record["week"]["start"],
                    week_end=record["week"]["end"],
                )
                for source in numeric_sources
            ]
            decision = publish_rule(readings)
            assert decision["published"] is True
            assert figure["value"] == decision["net_inr_cr"]
            assert figure["label"] == decision["label"]

    assert payload["DATA_PENDING"] is (published_figures == 0)
    if not pending:
        assert published_figures >= 1
