import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "ops"))

from series_lifecycle_audit import audit_series, evaluate, load_baseline  # noqa: E402


def write_series(directory: Path, *, note: str, seasons: list[int]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": "test-show",
        "renewal": {"note": note},
        "seasons": [{"number": number} for number in seasons],
    }
    (directory / "test-show.json").write_text(json.dumps(payload), encoding="utf-8")


def test_dated_renewal_without_season_shell_is_reported(tmp_path):
    series_dir = tmp_path / "data" / "series"
    write_series(
        series_dir,
        note="Season 2 premieres August 28, 2026 on Apple TV.",
        seasons=[1],
    )

    findings = audit_series(series_dir, repo_root=tmp_path)

    assert [finding.finding_id for finding in findings] == [
        "dated-season-missing-shell:test-show:s2:2026-08-28"
    ]


def test_matching_season_shell_clears_finding(tmp_path):
    series_dir = tmp_path / "data" / "series"
    write_series(
        series_dir,
        note="Season 2 began airing August 28, 2026 on Apple TV.",
        seasons=[1, 2],
    )

    assert audit_series(series_dir, repo_root=tmp_path) == []


def test_parser_does_not_borrow_a_date_from_another_season(tmp_path):
    series_dir = tmp_path / "data" / "series"
    write_series(
        series_dir,
        note="Season 3 was renewed; Season 2 premiered January 18, 2026.",
        seasons=[1, 2],
    )

    assert audit_series(series_dir, repo_root=tmp_path) == []


def test_baseline_allows_known_debt_but_rejects_new_debt():
    known_id = "dated-season-missing-shell:known:s2:2026-08-28"
    from series_lifecycle_audit import Finding

    known = Finding("dated-season-missing-shell", "known", 2, "2026-08-28", "known.json")
    new = Finding("dated-season-missing-shell", "new", 3, "2027-01-01", "new.json")

    report = evaluate([known, new], {known_id})

    assert report["known_debt"] == [known_id]
    assert report["unexpected"] == [new.finding_id]


def test_repository_has_no_unexpected_lifecycle_debt():
    baseline_path = REPO_ROOT / "scripts" / "ops" / "series-lifecycle-baseline.json"
    findings = audit_series(REPO_ROOT / "data" / "series", repo_root=REPO_ROOT)

    report = evaluate(findings, load_baseline(baseline_path))

    assert report["unexpected"] == []
    assert report["resolved_debt"] == []
    assert len(report["known_debt"]) == 7
