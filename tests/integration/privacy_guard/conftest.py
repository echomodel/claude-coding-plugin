"""Fixtures for privacy-guard agent integration tests.

The privacy-guard agent is a lean pre-push scanner. It only checks:
- git diff --staged
- git diff (unstaged tracked changes)
- git log @{upstream}..HEAD (unpushed commits)

It does NOT read individual files, scan full history, check issues/PRs,
or verify git author identity.
"""

import json
import os
import re
import subprocess
import textwrap
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fictitious personal data — deliberately unusual to avoid collisions
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
AGENT_SOURCE = Path(__file__).resolve().parent.parent.parent.parent / "agents" / "privacy-guard.md"

REMOTE_NAME = "origin"
REMOTE_BRANCH = "main"


def _init_git_repo(repo_dir: Path, author_name="Test Bot",
                   author_email=_e("bot", "test.example"),
                   with_upstream=True) -> None:
    """Initialize a git repo with a clean initial commit and optional fake upstream."""
    env = {**os.environ, "GIT_AUTHOR_NAME": author_name, "GIT_AUTHOR_EMAIL": author_email,
           "GIT_COMMITTER_NAME": author_name, "GIT_COMMITTER_EMAIL": author_email}
    subprocess.run(["git", "init", "-b", "main"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", author_name], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", author_email], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "core.hooksPath", "/dev/null"], cwd=repo_dir, check=True, capture_output=True)
    # Symlink agent from repo under test so claude finds it in local context
    agents_dir = repo_dir / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "privacy-guard.md").symlink_to(AGENT_SOURCE)
    # Gitignore .claude/ so the symlink doesn't show as untracked
    (repo_dir / ".gitignore").write_text(".claude/\n")
    subprocess.run(["git", "add", ".gitignore"], cwd=repo_dir, check=True, capture_output=True)
    # Initial commit so HEAD exists
    subprocess.run(["git", "commit", "-m", "initial"],
                   cwd=repo_dir, check=True, capture_output=True, env=env)

    if with_upstream:
        # Create a bare repo as a fake remote so @{upstream} works
        bare_dir = repo_dir.parent / (repo_dir.name + "-bare")
        bare_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "--bare", "-b", "main"], cwd=bare_dir,
                       check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", REMOTE_NAME, str(bare_dir)],
                       cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "push", "-u", REMOTE_NAME, REMOTE_BRANCH],
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


def _stage_file(repo_dir: Path, name: str, content: str) -> None:
    """Write a file and stage it without committing."""
    fpath = repo_dir / name
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)
    subprocess.run(["git", "add", name], cwd=repo_dir, check=True, capture_output=True)


def _modify_tracked_file(repo_dir: Path, name: str, content: str) -> None:
    """Modify a tracked file without staging it."""
    fpath = repo_dir / name
    fpath.write_text(content)


def run_privacy_guard(repo_dir: Path, person_md_path: Path | None = None,
                      extra_prompt: str = "", timeout: int = 180) -> dict:
    """Invoke the privacy-guard agent and return parsed JSON result."""
    prompt_parts = ["Scan this repo for personal information."]
    if person_md_path:
        prompt_parts.insert(0, f"Patterns file at {person_md_path}.")
    if extra_prompt:
        prompt_parts.append(extra_prompt)
    prompt = " ".join(prompt_parts)

    debug = os.environ.get("PRIVACY_GUARD_DEBUG")
    log_dir = Path("/tmp/privacy-guard-tests")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"{repo_dir.name}.log"

    cmd = ["claude", "--agent", "privacy-guard", "-p", prompt]
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
    _log(f"{'='*60}")

    result = subprocess.run(
        cmd, cwd=repo_dir, capture_output=True, text=True, timeout=timeout,
    )

    output = result.stdout + result.stderr

    _log(f"\nDONE: returncode = {result.returncode}")
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
    """A git repo with only clean files — no PII. Has a fake upstream."""
    repo = test_root / "repos" / "clean-repo"
    repo.mkdir(parents=True)
    _init_git_repo(repo, with_upstream=True)
    _add_and_commit(repo, {
        "README.md": "# Clean Project\n\nNothing personal here.\n",
        "src/main.py": "def hello():\n    print('hello world')\n",
    }, "add clean files")
    # Push so these are not unpushed
    subprocess.run(["git", "push"], cwd=repo, check=True, capture_output=True)
    return repo


@pytest.fixture
def repo_with_staged_pii(test_root):
    """Repo with PII in staged (but not committed) changes."""
    repo = test_root / "repos" / "staged-pii-repo"
    repo.mkdir(parents=True)
    _init_git_repo(repo, with_upstream=True)
    _add_and_commit(repo, {"README.md": "# Project\n"}, "init")
    subprocess.run(["git", "push"], cwd=repo, check=True, capture_output=True)
    # Stage a file with PII
    _stage_file(repo, "config.yaml",
                "author: " + _e("zanzibar", "quux.example") + "\n")
    return repo


@pytest.fixture
def repo_with_unstaged_pii(test_root):
    """Repo with PII in unstaged changes to a tracked file."""
    repo = test_root / "repos" / "unstaged-pii-repo"
    repo.mkdir(parents=True)
    _init_git_repo(repo, with_upstream=True)
    _add_and_commit(repo, {"config.yaml": "author: nobody\n"}, "init")
    subprocess.run(["git", "push"], cwd=repo, check=True, capture_output=True)
    # Modify tracked file without staging
    _modify_tracked_file(repo, "config.yaml",
                         "author: " + _e("zanzibar", "quux.example") + "\n")
    return repo


@pytest.fixture
def repo_with_unpushed_pii(test_root):
    """Repo with PII in an unpushed commit."""
    repo = test_root / "repos" / "unpushed-pii-repo"
    repo.mkdir(parents=True)
    _init_git_repo(repo, with_upstream=True)
    _add_and_commit(repo, {"README.md": "# Project\n"}, "init")
    subprocess.run(["git", "push"], cwd=repo, check=True, capture_output=True)
    # Commit with PII — don't push
    _add_and_commit(repo, {
        "docs/contact.md": "Support: " + _e("zanzibar", "quux.example") + "\n",
    }, "add contacts")
    return repo


@pytest.fixture
def repo_with_pii_in_commit_message(test_root):
    """Repo where PII is in an unpushed commit message, not file content."""
    repo = test_root / "repos" / "commit-msg-pii-repo"
    repo.mkdir(parents=True)
    _init_git_repo(repo, with_upstream=True)
    _add_and_commit(repo, {"README.md": "# Project\n"}, "init")
    subprocess.run(["git", "push"], cwd=repo, check=True, capture_output=True)
    # Commit with PII in message
    _add_and_commit(repo, {
        "src/fix.py": "def fix(): pass\n",
    }, "fix bug Zanzibar reported in the Quuxville office")
    return repo


@pytest.fixture
def repo_with_untracked_files(test_root):
    """Repo with untracked files present."""
    repo = test_root / "repos" / "untracked-repo"
    repo.mkdir(parents=True)
    _init_git_repo(repo, with_upstream=True)
    _add_and_commit(repo, {"README.md": "# Project\n"}, "init")
    subprocess.run(["git", "push"], cwd=repo, check=True, capture_output=True)
    # Create untracked file (don't git add)
    (repo / "scratch.txt").write_text("some notes\n")
    return repo


@pytest.fixture
def repo_pii_already_pushed(test_root):
    """Repo where PII was committed AND pushed — not in any diff."""
    repo = test_root / "repos" / "pushed-pii-repo"
    repo.mkdir(parents=True)
    _init_git_repo(repo, with_upstream=True)
    _add_and_commit(repo, {
        "config.yaml": "author: " + _e("zanzibar", "quux.example") + "\n",
    }, "add config with PII")
    subprocess.run(["git", "push"], cwd=repo, check=True, capture_output=True)
    return repo
