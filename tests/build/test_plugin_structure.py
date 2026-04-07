"""Post-build structural validation of plugin/dist/.

Verifies the assembled plugin artifact contains all expected files.
Requires ./build to have been run first.
"""

import configparser
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DIST_DIR = REPO_ROOT / "plugin" / "dist"
ASSETS_DIR = REPO_ROOT / "assets"
PLUGIN_SRC = REPO_ROOT / "plugin" / "src"


def _skip_if_no_dist():
    if not DIST_DIR.exists():
        pytest.skip("plugin/dist/ does not exist — run ./build first")


# --- Agents ---

def _expected_agents():
    """All agents that should be in dist: assets/ + plugin/src/agents/."""
    agents = []
    for d in [ASSETS_DIR / "agents", PLUGIN_SRC / "agents"]:
        if d.is_dir():
            agents.extend(f.stem for f in d.glob("*.md"))
    return sorted(set(agents))


@pytest.mark.parametrize("agent_name", _expected_agents())
def test_agent_in_dist(agent_name):
    _skip_if_no_dist()
    path = DIST_DIR / "agents" / f"{agent_name}.md"
    assert path.exists(), f"Agent '{agent_name}' missing from plugin/dist/agents/"


# --- Native skills ---

def _native_skills():
    d = ASSETS_DIR / "skills"
    if not d.is_dir():
        return []
    return sorted(s.name for s in d.iterdir() if s.is_dir())


@pytest.mark.parametrize("skill_name", _native_skills())
def test_native_skill_in_dist(skill_name):
    _skip_if_no_dist()
    path = DIST_DIR / "skills" / skill_name / "SKILL.md"
    assert path.exists(), f"Native skill '{skill_name}' missing from plugin/dist/skills/"


# --- Vendored skills ---

def _vendored_skills():
    cfg = configparser.ConfigParser()
    cfg.read(REPO_ROOT / "build.cfg")
    names = []
    for section in cfg.sections():
        skills_raw = cfg.get(section, "skills", fallback="")
        for line in skills_raw.strip().splitlines():
            name = Path(line.strip()).name
            if name:
                names.append(name)
    return sorted(set(names))


@pytest.mark.parametrize("skill_name", _vendored_skills())
def test_vendored_skill_in_dist(skill_name):
    _skip_if_no_dist()
    path = DIST_DIR / "skills" / skill_name / "SKILL.md"
    assert path.exists(), (
        f"Vendored skill '{skill_name}' missing from plugin/dist/skills/ — "
        f"run ./build to vendor from marketplace"
    )


# --- Plugin infrastructure ---

@pytest.mark.parametrize("filename", [
    ".claude-plugin/plugin.json",
    "settings.json",
    "hooks/hooks.json",
    ".mcp.json",
])
def test_plugin_infra_in_dist(filename):
    _skip_if_no_dist()
    path = DIST_DIR / filename
    assert path.exists(), f"Missing plugin/dist/{filename}"
    if filename.endswith(".json"):
        content = path.read_text()
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in plugin/dist/{filename}: {e}")
