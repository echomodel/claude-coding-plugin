"""Smoke test: verify the plugin loads into Claude Code.

Points --plugin-dir at the real plugin repo and asks Claude to list
its available skills. If plugin-only skills appear in the output,
the plugin loaded successfully.

Run:  make smoke-test-plugin
"""

import re
import subprocess
import tempfile
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PLUGIN_DIR = PLUGIN_ROOT / "plugin" / "dist"

# Skills that only exist in this plugin — if any show up, the plugin loaded
PLUGIN_SKILLS = ["safe-commit"]


class TestPluginLoads:

    def test_plugin_skills_discoverable(self, tmp_path):
        """Claude discovers plugin skills when loaded via --plugin-dir."""
        # Run from a random tmp dir so no local .claude/ context interferes
        work_dir = tmp_path / "workdir"
        work_dir.mkdir()

        cmd = [
            "claude",
            "--plugin-dir", str(PLUGIN_DIR),
            "-p", "List every skill available to you. Just the names, one per line.",
            "--max-turns", "1",
        ]

        result = subprocess.run(
            cmd, cwd=work_dir, capture_output=True, text=True, timeout=60,
        )

        output = (result.stdout + result.stderr).lower()

        found = [s for s in PLUGIN_SKILLS if s in output]

        assert len(found) > 0, (
            f"No plugin skills found in output. "
            f"Looked for: {PLUGIN_SKILLS}\n"
            f"Output: {output[:1000]}"
        )
