"""Lint checks for agent and skill definition files.

Validates source files in assets/ and plugin/src/ have well-formed
frontmatter and consistent cross-references. No build step required.
"""

import configparser
import json
import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = REPO_ROOT / "assets"
PLUGIN_SRC = REPO_ROOT / "plugin" / "src"


def parse_frontmatter(path):
    text = path.read_text()
    match = re.match(r"^---\n(.+?)\n---", text, re.DOTALL)
    if not match:
        return None
    return yaml.safe_load(match.group(1))


def all_agent_files():
    """All agent .md files across assets/ and plugin/src/."""
    files = []
    for d in [ASSETS_DIR / "agents", PLUGIN_SRC / "agents"]:
        if d.is_dir():
            files.extend(d.glob("*.md"))
    return sorted(files)


def all_skill_dirs():
    """All skill directories in assets/skills/."""
    d = ASSETS_DIR / "skills"
    if not d.is_dir():
        return []
    return sorted(s for s in d.iterdir() if s.is_dir() and (s / "SKILL.md").exists())


def native_skill_names():
    return {d.name for d in all_skill_dirs()}


def vendored_skill_names():
    cfg = configparser.ConfigParser()
    cfg.read(REPO_ROOT / "build.cfg")
    names = set()
    for section in cfg.sections():
        skills_raw = cfg.get(section, "skills", fallback="")
        for line in skills_raw.strip().splitlines():
            name = Path(line.strip()).name
            if name:
                names.add(name)
    return names


def all_available_skill_names():
    return native_skill_names() | vendored_skill_names()


# --- Agent frontmatter ---

@pytest.mark.parametrize("agent_file", all_agent_files(), ids=lambda p: p.stem)
def test_agent_has_valid_frontmatter(agent_file):
    fm = parse_frontmatter(agent_file)
    assert fm is not None, f"No frontmatter in {agent_file.name}"
    assert "name" in fm, f"Missing 'name' in {agent_file.name}"
    assert "description" in fm, f"Missing 'description' in {agent_file.name}"


@pytest.mark.parametrize("agent_file", all_agent_files(), ids=lambda p: p.stem)
def test_agent_skill_refs_resolve(agent_file):
    fm = parse_frontmatter(agent_file)
    if not fm or "skills" not in fm:
        pytest.skip(f"{agent_file.name} has no skills: frontmatter")
    skills = fm["skills"]
    if isinstance(skills, list) and len(skills) == 0:
        pytest.skip(f"{agent_file.name} has empty skills list")
    available = all_available_skill_names()
    missing = [s for s in skills if s not in available]
    assert not missing, (
        f"{agent_file.name} references skills not in assets/skills/ or build.cfg: {missing}"
    )


# --- Skill frontmatter ---

@pytest.mark.parametrize("skill_dir", all_skill_dirs(), ids=lambda p: p.name)
def test_skill_has_valid_frontmatter(skill_dir):
    skill_md = skill_dir / "SKILL.md"
    fm = parse_frontmatter(skill_md)
    assert fm is not None, f"No frontmatter in {skill_dir.name}"
    assert "name" in fm, f"Missing 'name' in {skill_dir.name}"
    assert "description" in fm, f"Missing 'description' in {skill_dir.name}"
    assert fm["name"] == skill_dir.name, (
        f"Frontmatter name '{fm['name']}' doesn't match directory '{skill_dir.name}'"
    )


# --- Plugin src ---

@pytest.mark.parametrize("filename", [
    ".claude-plugin/plugin.json",
    "settings.json",
    "hooks/hooks.json",
    ".mcp.json",
])
def test_plugin_src_file_exists_and_valid(filename):
    path = PLUGIN_SRC / filename
    assert path.exists(), f"Missing plugin/src/{filename}"
    if filename.endswith(".json"):
        content = path.read_text()
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in plugin/src/{filename}: {e}")


def test_settings_agent_ref_resolves():
    settings = json.loads((PLUGIN_SRC / "settings.json").read_text())
    agent_name = settings.get("agent")
    if not agent_name:
        pytest.skip("No agent in settings.json")
    candidates = [
        PLUGIN_SRC / "agents" / f"{agent_name}.md",
        ASSETS_DIR / "agents" / f"{agent_name}.md",
    ]
    assert any(c.exists() for c in candidates), (
        f"settings.json references agent '{agent_name}' but not found in "
        f"plugin/src/agents/ or assets/agents/"
    )
