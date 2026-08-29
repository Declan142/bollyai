"""Unit fence for the deploy-landed verifier (scripts/ops/verify_pages_deploy.py).

DELIVERED is not LANDED: these cases pin the two ways production can be stale while a
workflow reports success - no production deployment at all, and a production deployment
that predates the run which claimed to publish one.
"""
from datetime import datetime, timezone
from pathlib import Path
import importlib.util
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "ops" / "verify_pages_deploy.py"

_spec = importlib.util.spec_from_file_location("verify_pages_deploy", MODULE_PATH)
verify_pages_deploy = importlib.util.module_from_spec(_spec)
sys.modules["verify_pages_deploy"] = verify_pages_deploy
_spec.loader.exec_module(verify_pages_deploy)


FRESH = {
    "id": "fresh-1",
    "environment": "production",
    "created_on": "2026-08-30T09:00:00.123456Z",
    "latest_stage": {"status": "success"},
}
STALE = {
    "id": "stale-1",
    "environment": "production",
    "created_on": "2026-07-31T21:38:46.252989Z",
    "latest_stage": {"status": "success"},
}
PREVIEW = {
    "id": "preview-1",
    "environment": "preview",
    "created_on": "2026-08-30T09:30:00Z",
    "latest_stage": {"status": "success"},
}
FAILED = {
    "id": "failed-1",
    "environment": "production",
    "created_on": "2026-08-30T09:30:00Z",
    "latest_stage": {"status": "failure"},
}


def test_parse_cf_timestamp_handles_variable_fractional_precision():
    assert verify_pages_deploy.parse_cf_timestamp("2026-07-13T05:41:42.7984Z") == datetime(
        2026, 7, 13, 5, 41, 42, 798400, tzinfo=timezone.utc
    )
    assert verify_pages_deploy.parse_cf_timestamp("2026-08-30T09:30:00Z") == datetime(
        2026, 8, 30, 9, 30, 0, tzinfo=timezone.utc
    )


def test_newest_successful_production_ignores_preview_and_failed_deployments():
    picked = verify_pages_deploy.newest_successful_production(
        {"result": [STALE, PREVIEW, FAILED, FRESH]}
    )

    assert picked["id"] == "fresh-1"


def test_newest_successful_production_is_none_when_nothing_ever_succeeded():
    assert verify_pages_deploy.newest_successful_production({"result": [PREVIEW, FAILED]}) is None
    assert verify_pages_deploy.newest_successful_production({}) is None


def test_main_fails_on_a_stale_production_deployment(monkeypatch, capsys):
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "token")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "account")
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setattr(
        verify_pages_deploy, "fetch_deployments", lambda *a, **k: {"result": [STALE]}
    )

    code = verify_pages_deploy.main(
        ["--project", "bollyai-in", "--max-age-minutes", "30", "--now", "2026-08-30T09:00:00Z"]
    )

    assert code == 1
    assert "Deploy did not land" in capsys.readouterr().err


def test_main_passes_on_a_fresh_production_deployment(monkeypatch, capsys):
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "token")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "account")
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setattr(
        verify_pages_deploy, "fetch_deployments", lambda *a, **k: {"result": [STALE, FRESH]}
    )

    code = verify_pages_deploy.main(["--now", "2026-08-30T09:10:00Z"])

    assert code == 0
    assert "production deploy landed: id=fresh-1" in capsys.readouterr().out


def test_main_refuses_to_verify_without_credentials(monkeypatch, capsys):
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "token")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "")

    assert verify_pages_deploy.main([]) == 1
    assert "Cannot verify deploy" in capsys.readouterr().err
