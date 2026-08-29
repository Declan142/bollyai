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


def deploying_workflows() -> list[Path]:
    return sorted(
        path
        for path in WORKFLOW_DIR.glob("*.yml")
        if "cloudflare/wrangler-action" in path.read_text(encoding="utf-8")
    )


def steps_of(payload: dict) -> list[dict]:
    return [step for job in payload["jobs"].values() for step in job["steps"]]


def test_deploy_steps_are_dry_run_guarded_but_never_silently_skippable():
    """Regression fence for the 2026-08-30 false green.

    The deploy step used to carry ``env.CLOUDFLARE_* != ''`` in its ``if:``. With
    ``CLOUDFLARE_ACCOUNT_ID`` absent from the repository secrets that guard was false on
    every run, so 232 consecutive green runs built the site and published nothing while
    bollyai.in stayed frozen for 29 days. A missing deploy credential must fail the run,
    never quietly disable the deploy.
    """
    paths = deploying_workflows()

    assert paths, "no workflow deploys the site any more"

    for path in paths:
        text = path.read_text(encoding="utf-8")
        steps = steps_of(load_workflow(path))
        names = [step.get("name") for step in steps]
        deploy = next(step for step in steps if step.get("id") == "deploy")

        assert "github.event.inputs.dry_run != 'true'" in deploy["if"]
        assert "env.CLOUDFLARE_API_TOKEN" not in deploy["if"]
        assert "env.CLOUDFLARE_ACCOUNT_ID" not in deploy["if"]
        assert "pages deploy site/out --project-name=bollyai-in --branch=main" in text
        assert names[0] == "Preflight deploy credentials"
        assert "Verify deploy landed" in names


def test_preflight_fails_loudly_when_deploy_credentials_are_missing():
    for path in deploying_workflows():
        preflight = steps_of(load_workflow(path))[0]
        body = preflight["run"]

        assert "CLOUDFLARE_API_TOKEN" in body
        assert "CLOUDFLARE_ACCOUNT_ID" in body
        assert "::error" in body
        assert "exit 1" in body
        assert "|| true" not in body


def test_verify_deploy_landed_fails_when_a_successful_build_published_nothing():
    for path in deploying_workflows():
        steps = steps_of(load_workflow(path))
        build = next(step for step in steps if step.get("id") == "build")
        verify = next(step for step in steps if step.get("name") == "Verify deploy landed")

        assert build["name"] == "Build static site"
        assert "always()" in verify["if"]
        assert "steps.build.outcome == 'success'" in verify["if"]
        assert "exit 1" in verify["run"]
        assert "scripts/ops/verify_pages_deploy.py" in verify["run"]


def test_indexnow_stays_embedded_not_standalone_and_accepts_relative_urls():
    assert not (WORKFLOW_DIR / "indexnow-ping.yml").exists()

    urls = indexnow_ping.normalize_urls(["/ott/calendar/", "https://bollyai.in/series/squid-game/"], host="bollyai.in")

    assert urls == [
        "https://bollyai.in/ott/calendar/",
        "https://bollyai.in/series/squid-game/",
    ]
