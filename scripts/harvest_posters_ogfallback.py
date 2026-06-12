#!/usr/bin/env python3
"""Compatibility wrapper for the v2 official-only series poster harvester."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.fetchers.image_harvester import run_series_poster_cli


if __name__ == "__main__":
    raise SystemExit(run_series_poster_cli())
