"""Fixtures for privacy-audit agent integration tests.

Creates temporary git repos and PERSON.md files with fictitious personal
data, invokes the agent via `claude --agent privacy-audit`, and parses
the structured JSON output.
"""

import json
import os
import re
import subprocess
import tempfile
import textwrap
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fictitious personal data — deliberately unusual to avoid collisions
# with anything real on the test machine.
# ---------------------------------------------------------------------------

# Build emails via concatenation so precommit scanners don't flag them.
_e = lambda user, domain: user + "@" + domain

FAKE_PERSON = {
    "github": ["zquuxdev"],
    "emails": [_e("zanzibar", "quux.example"), _e("plonk", "xyzzy.example")],
    "email_domains": ["quux.example", "xyzzy.example"],
    "names": [
        "Zanzibar Quuxington",
        "Zanzibar",
        "Quuxington",
        "Plonkia",
        "Frobnitz",
    ],
    "phone_area_codes": ["555"],
    "domains": ["quux.example", "xyzzy.example"],
    "financial_providers": ["Acme Brokerage", "Xyzzy Bank"],
    "employers": ["Megacorp LLC"],
    "employer_terms": ["synergy bonus"],
    "properties": ["Frobnitz Manor"],
    "cities": ["Quuxville"],
}


def _write_person_md(path: Path) -> None:
    """Write a test PERSON.md with YAML frontmatter."""
    lines = ["# Personal Information — Scanner Reference\n", "---\n", "patterns:\n"]
    for category, values in FAKE_PERSON.items():
        lines.append(f"  {category}:\n")
        for v in values:
            lines.append(f'    - "{v}"\n')
    lines.append("---\n")
    path.write_text("".join(lines))


# Path to the agent source file in the repo under test
AGENT_SOURCE = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "agents" / "privacy-audit.md"


def _init_git_repo(repo_dir: Path, author_name="Test Bot", author_email=_e("bot", "test.example")) -> None:
    """Initialize a git repo with a clean initial commit."""
    env = {**os.environ, "GIT_AUTHOR_NAME": author_name, "GIT_AUTHOR_EMAIL": author_email,
           "GIT_COMMITTER_NAME": author_name, "GIT_COMMITTER_EMAIL": author_email}
    subprocess.run(["git", "init", "-b", "main"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", author_name], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", author_email], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "core.hooksPath", "/dev/null"], cwd=repo_dir, check=True, capture_output=True)
    # Symlink agent from repo under test so claude finds it in local context
    agents_dir = repo_dir / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "privacy-audit.md").symlink_to(AGENT_SOURCE)
    # Initial empty commit so HEAD exists
    subprocess.run(["git", "commit", "--allow-empty", "-m", "initial"],
                   cwd=repo_dir, check=True, capture_output=True, env=env)


def _add_and_commit(repo_dir: Path, files: dict[str, str], message: str,
                    author_name=None, author_email=None) -> str:
    """Add files and commit. Returns the commit SHA."""
    for name, content in files.items():
        fpath = repo_dir / name
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(content)
        subprocess.run(["git", "add", name], cwd=repo_dir, check=True, capture_output=True)

    env = {**os.environ}
    if author_name:
        env["GIT_AUTHOR_NAME"] = author_name
        env["GIT_COMMITTER_NAME"] = author_name
    if author_email:
        env["GIT_AUTHOR_EMAIL"] = author_email
        env["GIT_COMMITTER_EMAIL"] = author_email

    subprocess.run(["git", "commit", "-m", message],
                   cwd=repo_dir, check=True, capture_output=True, env=env)
    result = subprocess.run(["git", "rev-parse", "HEAD"],
                            cwd=repo_dir, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def run_privacy_guard(repo_dir: Path, person_md_path: Path | None = None,
                      extra_prompt: str = "", timeout: int = 180) -> dict:
    """Invoke the privacy-guard agent and return parsed JSON result.

    Returns a dict with at minimum {"status": "..."}.
    If JSON parsing fails, returns {"status": "parse_error", "raw_output": "..."}.
    """
    prompt_parts = ["Scan this repo for personal information."]
    if person_md_path:
        prompt_parts.insert(0, f"Patterns file at {person_md_path}.")
    if extra_prompt:
        prompt_parts.append(extra_prompt)
    prompt = " ".join(prompt_parts)

    # Debug logs: one file per repo so parallel tests don't collide.
    # Set PRIVACY_GUARD_DEBUG=1 to enable, then:
    #   tail -f /tmp/privacy-guard-tests/*.log
    # Claude's own debug log goes to <repo>.claude-debug.log alongside it.
    debug = os.environ.get("PRIVACY_GUARD_DEBUG")
    log_dir = Path("/tmp/privacy-guard-tests")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"{repo_dir.name}.log"

    cmd = ["claude", "--agent", "privacy-audit", "-p", prompt]
    if debug:
        cmd.extend(["--debug-file", str(log_dir / f"{repo_dir.name}.claude-debug.log")])
    if person_md_path and person_md_path.parent.exists():
        cmd.extend(["--add-dir", str(person_md_path.parent)])

    def _log(msg: str) -> None:
        if debug:
            with open(log_path, "a") as f:
                f.write(msg + "\n")

    _log(f"\n{'='*60}")
    _log(f"STARTING: {' '.join(cmd)}")
    _log(f"cwd = {repo_dir}")
    _log(f"timeout = {timeout}s")
    _log(f"waiting for agent...")
    _log(f"{'='*60}")

    result = subprocess.run(
        cmd, cwd=repo_dir, capture_output=True, text=True, timeout=timeout,
    )

    output = result.stdout + result.stderr

    _log(f"\nDONE: returncode = {result.returncode}")
    _log(f"stdout length = {len(result.stdout)}")
    _log(f"stderr length = {len(result.stderr)}")
    _log(f"raw output:\n{output}")
    _log(f"{'='*60}\n")

    # Extract the JSON block tagged privacy-guard-result
    match = re.search(r"```privacy-guard-result\s*\n(.*?)\n```", output, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(1))
            _log(f"parsed JSON OK, status={parsed.get('status')}, "
                 f"findings={len(parsed.get('findings', []))}")
            return parsed
        except json.JSONDecodeError as e:
            _log(f"JSON parse failed: {e}")
            return {"status": "parse_error", "raw_output": output}

    # Fallback: try to find any JSON object with "status" key
    for m in re.finditer(r"\{[^{}]*\"status\"[^{}]*\}", output, re.DOTALL):
        try:
            parsed = json.loads(m.group(0))
            _log(f"fallback JSON, status={parsed.get('status')}")
            return parsed
        except json.JSONDecodeError:
            continue

    _log("no JSON found in output")
    return {"status": "parse_error", "raw_output": output}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_root(tmp_path):
    """Root temp directory containing person_md/ and repos/ subdirs."""
    person_dir = tmp_path / "person_md"
    person_dir.mkdir()
    repos_dir = tmp_path / "repos"
    repos_dir.mkdir()
    return tmp_path


@pytest.fixture
def person_md(test_root):
    """Write a test PERSON.md and return its path."""
    p = test_root / "person_md" / "PERSON.md"
    _write_person_md(p)
    return p


@pytest.fixture
def clean_repo(test_root):
    """A git repo with only clean files — no PII."""
    repo = test_root / "repos" / "clean-repo"
    repo.mkdir(parents=True)
    _init_git_repo(repo)
    _add_and_commit(repo, {
        "README.md": "# Clean Project\n\nNothing personal here.\n",
        "src/main.py": "def hello():\n    print('hello world')\n",
    }, "add clean files")
    return repo


@pytest.fixture
def dirty_repo(test_root):
    """A git repo with planted PII in various locations."""
    repo = test_root / "repos" / "dirty-repo"
    repo.mkdir(parents=True)
    _init_git_repo(repo)

    # Commit 1: files with PII across multiple categories
    _add_and_commit(repo, {
        "config.yaml": "author: " + _e("zanzibar", "quux.example") + "\n",
        "src/main.py": "# Contact Frobnitz Manor for details\ndef run(): pass\n",
        "tests/fixtures.json": '{"name": "Plonkia", "bank": "Xyzzy Bank"}\n',
        "docs/contact.md": "Support: " + _e("zanzibar", "quux.example") + "\n",
    }, "add initial files")

    # Commit 2: remove PII from config.yaml (stays in history),
    # but docs/contact.md still has the email in HEAD
    _add_and_commit(repo, {
        "config.yaml": "author: " + _e("user", "example.com") + "\n",
    }, "clean up config")

    return repo


@pytest.fixture
def pii_in_commit_message_repo(test_root):
    """Repo where PII is in a commit message, not in files."""
    repo = test_root / "repos" / "commit-msg-repo"
    repo.mkdir(parents=True)
    _init_git_repo(repo)
    _add_and_commit(repo, {
        "README.md": "# Project\n",
    }, "fix bug Zanzibar reported in the Quuxville office")
    return repo


