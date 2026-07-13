"""Single LLM transport seam for the subtitle-intelligence engine.

The production transport is the local Empire Codex bridge.  Callers keep their
system/user prompt split, so an OpenAI-compatible HTTP transport can later
implement ``ChatTransport.ask`` without changing extraction or review call sites.

Configuration (read for every request):
  BOLLYAI_LLM_MODEL   gpt-5.6-luna (default) or gpt-5.6-terra
  BOLLYAI_LLM_EFFORT  low (default), forwarded to ``gpt ask --effort``
"""
from __future__ import annotations

import os
import json
import re
import subprocess
from dataclasses import dataclass
from typing import Protocol


DEFAULT_MODEL = "gpt-5.6-luna"
DEFAULT_EFFORT = "low"
ALLOWED_MODELS = frozenset({"gpt-5.6-luna", "gpt-5.6-terra"})


class ChatTransport(Protocol):
    """Stable transport contract for a future HTTP provider implementation."""

    def ask(self, system: str, user: str, *, model: str | None = None,
            timeout: int = 600) -> tuple[str, int]: ...


def configured_model(model: str | None = None) -> str:
    """Return the approved model, rejecting the expensive flagship lane explicitly."""
    selected = (model or os.environ.get("BOLLYAI_LLM_MODEL", DEFAULT_MODEL)).strip()
    if selected not in ALLOWED_MODELS:
        raise ValueError(
            "BOLLYAI_LLM_MODEL must be gpt-5.6-luna or gpt-5.6-terra; "
            f"got {selected!r}"
        )
    return selected


def configured_effort() -> str:
    effort = os.environ.get("BOLLYAI_LLM_EFFORT", DEFAULT_EFFORT).strip()
    if not effort:
        raise ValueError("BOLLYAI_LLM_EFFORT must not be empty")
    return effort


def _prompt(system: str, user: str) -> str:
    """Carry both existing prompt halves intact through the single-string bridge API."""
    return f"SYSTEM INSTRUCTIONS:\n{system}\n\nUSER REQUEST:\n{user}"


@dataclass(frozen=True)
class CodexBridgeTransport:
    """Synchronous local bridge transport; stdout is already final-model text."""

    executable: str = "gpt"

    def ask(self, system: str, user: str, *, model: str | None = None,
            timeout: int = 600) -> tuple[str, int]:
        selected_model = configured_model(model)
        effort = configured_effort()
        argv = [self.executable, "ask", "-m", selected_model, "--effort", effort,
                _prompt(system, user)]
        try:
            proc = subprocess.run(
                argv, capture_output=True, text=True, timeout=timeout, check=False,
            )
        except subprocess.TimeoutExpired:
            print(f"  codex bridge timeout after {timeout}s", file=os.sys.stderr)
            return "", 1
        if proc.returncode:
            detail = (proc.stderr or "bridge call failed").strip().replace("\n", " ")
            print(f"  codex bridge rc={proc.returncode}: {detail[:300]}", file=os.sys.stderr)
            return "", proc.returncode
        # ask.sh emits its `codex exec -o` file directly, which is only final model text.
        return proc.stdout.strip(), 0


TRANSPORT: ChatTransport = CodexBridgeTransport()


def gpt_ask(instruction: str, stdin_text: str, timeout: int = 600,
            model: str | None = None, budget: int = 9000) -> tuple[str, int]:
    """Compatibility facade; budget remains accepted while bridge owns output sizing."""
    del budget
    return TRANSPORT.ask(instruction, stdin_text, model=model, timeout=timeout)


def coerce_json(text: str) -> dict | None:
    """Parse a strict JSON reply while tolerating an accidental Markdown fence."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None
