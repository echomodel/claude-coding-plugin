---
name: sociable-unit-tests
description: "Guide for writing sociable unit tests with directory isolation, no mocks, and transaction-level testing. Use when writing tests, reviewing test quality, or setting up test infrastructure for a Python project."
---

# Unit Testing Philosophy

## Core Principle: Sociable Unit Tests

Write tests that verify complete features or SDK transactions end-to-end. Do NOT
write isolated "solitary" unit tests that mock internal collaborators. Mocking
hides integration bugs — the exact class of bugs tests should catch.

**No mocks unless you ask.** Isolate via temp dirs and env vars.

## What to Mock vs What NOT to Mock

**Mock only at system boundaries:**
- Network calls (APIs, HTTP, external services)
- System clocks (if time precision matters)
- Heavy external processes

**Never mock:**
- Internal helper functions or classes
- File system operations (use temp dirs instead)
- Configuration parsers (write real config files to temp dirs)
- SDK methods called by CLI or MCP layers

## Directory Structure

```
tests/
  unit/            # Fast, offline, no credentials (DEFAULT)
  integration/     # Requires auth/config/infra (NEVER default)
```

**pytest.ini** or **pyproject.toml** must scope default runs to unit tests only:

```ini
# pytest.ini
[pytest]
addopts = -v
testpaths = tests/unit
```

Or in pyproject.toml:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--ignore=tests/integration"
```

Integration tests are only run when explicitly requested. They require real
credentials, network access, or infrastructure.

## Unit Test Rules

- **Fast, local, no network, no credentials.**
- Subprocess calls only to ubiquitous tools (e.g., `git init`, `git commit` — never `git push`).
- Every test must be isolated from every other test and from the real filesystem.

## Environment Variable Isolation

Every project that reads from config or data directories must support env var
overrides for those paths. Tests use these to redirect to temp directories.

**Pattern:**

```python
# In the SDK (config.py or similar):
def get_config_dir() -> Path:
    path_str = os.environ.get("MY_APP_CONFIG_DIR")
    if path_str:
        return Path(path_str)
    return Path.home() / ".config" / "my-app"
```

```python
# In conftest.py:
@pytest.fixture(autouse=True)
def isolate_config(tmp_path, monkeypatch):
    """Auto-isolate every test from real config directories."""
    test_config = tmp_path / "config"
    test_config.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MY_APP_CONFIG_DIR", str(test_config))
```

Key points:
- `autouse=True` — applies to every test automatically, no opt-in needed
- `tmp_path` — pytest built-in, unique per test, auto-cleaned
- `monkeypatch.setenv()` — auto-reverted when test ends
- Place in `conftest.py` — central, no imports needed per test file

**Isolate ALL writable paths:** config, data, cache, XDG directories. If the
SDK writes to it, tests must redirect it.

## Test Names

Test names describe **scenario + outcome**, not implementation details.

Good:
- `test_not_installed_when_no_hooks_path`
- `test_refuses_to_overwrite_foreign_hook`
- `test_init_creates_manifest_and_dockerfile`
- `test_logs_food_to_current_date_directory`

Bad:
- `test_returns_false_when_file_missing`
- `test_respects_config`
- `test_returns_true`

## Test Complete Transaction Flows

Test the full flow of a feature, not individual functions in isolation.

Example: testing a "label email" feature:
1. Search for target email — confirm it exists without the label
2. Read email details (before) — assert label absent
3. Apply label — execute the operation
4. Read email details (after) — assert label present, other fields unchanged

This catches integration bugs between steps that isolated function tests miss.

## SDK-First Testing

All business logic lives in the SDK. CLI and MCP are thin wrappers.

**Test the SDK directly** — don't test through CLI subprocess calls or MCP
tool invocations. This tests the logic without CLI parsing overhead.

```python
# Good: test SDK directly
def test_add_command_creates_toml(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_APP_CONFIG_DIR", str(tmp_path))
    result = sdk.add_command("fix", "Fix the bug")
    assert (tmp_path / "commands" / "fix.toml").exists()

# Bad: test through CLI subprocess
def test_add_command_cli(tmp_path):
    result = subprocess.run(["my-app", "cmds", "add", "fix", "Fix the bug"])
    # Slower, harder to isolate, tests Click parsing not logic
```

## Setting Up Tests for a New Project

1. Create `tests/unit/` and optionally `tests/integration/`
2. Create `pytest.ini` with `testpaths = tests/unit`
3. Create `tests/conftest.py` with `autouse=True` isolation fixture
4. Ensure all SDK config/data paths support env var overrides
5. Add `pytest` to dev dependencies
6. Verify: `pytest` runs only unit tests; `pytest tests/integration` runs integration tests explicitly
