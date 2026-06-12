from pathlib import Path
import sys

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import indexnow_ping  # noqa: E402


EXPECTED_WORKFLOWS = {
    "daily-refresh.yml": "30 4 * * *",
    "friday-surge.yml": "0 4,7,11 * * 5",
    "ott-calendar-roll.yml": "0 3 * * 1,4",
    "tentpole-live.yml": "0 */3 * * 5,6,0,1",
    "health-digest.yml": "0 2 * * 0",
}


def load_workflow(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def on_block(payload: dict) -> dict:
    return payload.get("on") or payload.get(True) or {}


def test_workflow_set_is_explicit_and_split():
    names = {path.name for path in WORKFLOW_DIR.glob("*.yml")}

    assert names == set(EXPECTED_WORKFLOWS)


def test_workflows_safe_load_and_have_dispatch_concurrency_and_healthchecks():
    for name, cron in EXPECTED_WORKFLOWS.items():
        path = WORKFLOW_DIR / name
        text = path.read_text(encoding="utf-8")
        payload = load_workflow(path)
        events = on_block(payload)

        assert "workflow_dispatch" in events
        assert events["schedule"][0]["cron"] == cron
        assert payload["concurrency"]["cancel-in-progress"] is False
        assert payload.get("jobs")
        assert "HC_URL_" in text


def test_writer_workflows_share_single_writer_group():
    for name in EXPECTED_WORKFLOWS:
        payload = load_workflow(WORKFLOW_DIR / name)
        group = payload["concurrency"]["group"]
        if name == "health-digest.yml":
            assert group == "bollyai-health-digest"
        else:
            assert group == "bollyai-writer"
            assert payload["permissions"]["contents"] == "write"


def test_deploy_steps_are_secret_and_dry_run_guarded():
    for path in WORKFLOW_DIR.glob("*.yml"):
        text = path.read_text(encoding="utf-8")
        if "cloudflare/wrangler-action" not in text:
            continue

        assert "github.event.inputs.dry_run != 'true'" in text
        assert "env.CLOUDFLARE_API_TOKEN != ''" in text
        assert "env.CLOUDFLARE_ACCOUNT_ID != ''" in text
        assert "pages deploy site/out --project-name=bollyai-in --branch=main" in text


def test_indexnow_stays_embedded_not_standalone_and_accepts_relative_urls():
    assert not (WORKFLOW_DIR / "indexnow-ping.yml").exists()

    urls = indexnow_ping.normalize_urls(["/ott/calendar/", "https://bollyai.in/series/squid-game/"], host="bollyai.in")

    assert urls == [
        "https://bollyai.in/ott/calendar/",
        "https://bollyai.in/series/squid-game/",
    ]
