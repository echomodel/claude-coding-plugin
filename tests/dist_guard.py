"""Shared guard: check if plugin/dist/ is current relative to source.

Used by conftest.py in tests/build/ and tests/integration/plugin/.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = REPO_ROOT / "plugin" / "dist"
SOURCE_PATHS = [
    REPO_ROOT / "assets",
    REPO_ROOT / "plugin" / "src",
    REPO_ROOT / "build.cfg",
]


def _newest_mtime(paths):
    newest = 0
    for p in paths:
        if p.is_file():
            newest = max(newest, p.stat().st_mtime)
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    newest = max(newest, f.stat().st_mtime)
    return newest


def skip_if_dist_stale(items):
    """Mark all items as skipped if plugin/dist/ is missing or stale."""
    if not DIST_DIR.exists():
        skip = pytest.mark.skip(reason="plugin/dist/ does not exist — run ./build first")
        for item in items:
            item.add_marker(skip)
        return

    # Compare newest source file against the dist directory's own mtime.
    # ./build wipes and recreates plugin/dist/, so the directory mtime
    # reflects when the last build ran.
    source_newest = _newest_mtime(SOURCE_PATHS)
    dist_dir_mtime = DIST_DIR.stat().st_mtime

    if source_newest > dist_dir_mtime:
        skip = pytest.mark.skip(
            reason="plugin/dist/ appears stale (source files are newer) — run ./build first"
        )
        for item in items:
            item.add_marker(skip)
