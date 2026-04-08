"""Build script for claude-coding plugin.

Assembles plugin/dist/ from:
  - plugin/src/          -> plugin/dist/  (dirs + *.json only)
  - assets/agents/       -> plugin/dist/agents/  (overlay)
  - assets/skills/       -> plugin/dist/skills/  (native)
  - build.cfg            -> plugin/dist/skills/  (vendored from marketplace)

Usage:
  python3 build.py             Build dist from current source
  python3 build.py 0.3.0       Bump version in src, then build
"""

import configparser
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent          # plugin/src/
PLUGIN_DIR = SCRIPT_DIR.parent                        # plugin/
REPO_ROOT = PLUGIN_DIR.parent                         # repo root
DIST_DIR = PLUGIN_DIR / "dist"
ASSETS_DIR = REPO_ROOT / "assets"
PLUGIN_SRC_JSON = SCRIPT_DIR / ".claude-plugin" / "plugin.json"


def bump_version(new_version):
    """Stamp new version into src plugin.json."""
    data = json.loads(PLUGIN_SRC_JSON.read_text())
    old = data.get("version", "0.0.0")
    if old == new_version:
        print(f"Version already {new_version}")
        return
    data["version"] = new_version
    PLUGIN_SRC_JSON.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Version: {old} -> {new_version}")


def get_native_skills():
    """Skills in assets/skills/ — source of truth is this repo."""
    skills_dir = ASSETS_DIR / "skills"
    if not skills_dir.is_dir():
        return set()
    return {d.name for d in skills_dir.iterdir() if d.is_dir()}


def load_config():
    cfg = configparser.ConfigParser()
    cfg.read(REPO_ROOT / "build.cfg")
    return cfg


def clean_dist():
    """Remove and recreate plugin/dist/."""
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)


def copy_plugin_src():
    """Copy dirs and *.json from plugin/src/ to plugin/dist/."""
    for item in SCRIPT_DIR.iterdir():
        dst = DIST_DIR / item.name
        if item.is_dir():
            shutil.copytree(item, dst)
        elif item.is_file() and item.suffix == ".json":
            shutil.copy2(item, dst)

    print("  Plugin infra: copied from plugin/src/")


def copy_reusable_agents():
    """Overlay reusable agents from assets/agents/ into dist."""
    dst = DIST_DIR / "agents"
    dst.mkdir(parents=True, exist_ok=True)

    agents_src = ASSETS_DIR / "agents"
    if agents_src.is_dir():
        for f in agents_src.iterdir():
            if f.is_file():
                target = dst / f.name
                if target.exists():
                    print(f"  CONFLICT: assets/agents/{f.name} would overwrite "
                          f"plugin/src/agents/{f.name}", file=sys.stderr)
                    sys.exit(1)
                shutil.copy2(f, target)

    count = len(list(dst.glob("*.md")))
    print(f"  Agents: {count} total")


def copy_native_skills():
    """Copy native skills from assets/skills/ to plugin/dist/skills/."""
    dst = DIST_DIR / "skills"
    dst.mkdir(parents=True, exist_ok=True)

    skills_src = ASSETS_DIR / "skills"
    if skills_src.is_dir():
        for skill_dir in skills_src.iterdir():
            if skill_dir.is_dir():
                shutil.copytree(skill_dir, dst / skill_dir.name)

    count = len([d for d in dst.iterdir() if d.is_dir()]) if dst.exists() else 0
    print(f"  Native skills: {count} copied")


def vendor_skills(cfg):
    """Clone marketplace repos and copy listed skills into plugin/dist/skills/."""
    native = get_native_skills()
    skills_dst = DIST_DIR / "skills"
    skills_dst.mkdir(parents=True, exist_ok=True)
    total = 0

    for section in cfg.sections():
        url = cfg.get(section, "url")
        ref = cfg.get(section, "ref", fallback="main")
        skills_raw = cfg.get(section, "skills", fallback="")
        skill_paths = [s.strip() for s in skills_raw.strip().splitlines() if s.strip()]

        if not skill_paths:
            print(f"  [{section}] No skills listed, skipping.")
            continue

        with tempfile.TemporaryDirectory() as tmp:
            print(f"  [{section}] Cloning {url} (ref: {ref})...")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", ref, url, tmp],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                print(f"  FAILED: {result.stderr.strip()}", file=sys.stderr)
                sys.exit(1)

            for skill_path in skill_paths:
                skill_name = Path(skill_path).name
                src = Path(tmp) / skill_path / "SKILL.md"
                dst = skills_dst / skill_name / "SKILL.md"

                if skill_name in native:
                    print(f"    SKIP {skill_name} (native takes precedence)")
                    continue

                if not src.exists():
                    print(f"    MISSING {skill_path}/SKILL.md", file=sys.stderr)
                    sys.exit(1)

                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                print(f"    {skill_path} -> skills/{skill_name}/")
                total += 1

    return total


def build():
    """Assemble plugin/dist/ from all sources."""
    print("Assembling plugin/dist/...")
    clean_dist()
    copy_plugin_src()
    copy_reusable_agents()
    copy_native_skills()

    cfg = load_config()
    vendor_skills(cfg)

    # Summary
    all_skills = sorted(d.name for d in (DIST_DIR / "skills").iterdir() if d.is_dir())
    native = get_native_skills()
    native_list = sorted(s for s in all_skills if s in native)
    vendored_list = sorted(s for s in all_skills if s not in native)
    agents = sorted(f.stem for f in (DIST_DIR / "agents").glob("*.md"))

    print(f"\n--- Build complete ---")
    print(f"Agents:   {', '.join(agents)} ({len(agents)})")
    print(f"Native:   {', '.join(native_list)} ({len(native_list)})")
    print(f"Vendored: {', '.join(vendored_list)} ({len(vendored_list)})")
    print(f"Total:    {len(agents)} agents, {len(all_skills)} skills")


def main():
    if len(sys.argv) > 1:
        bump_version(sys.argv[1])
    build()


if __name__ == "__main__":
    main()
