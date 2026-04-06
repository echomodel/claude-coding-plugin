# `./agent` CLI

Pure-stdlib Python script for managing plugin agents. No venv, no pip,
no dependencies beyond Python 3. Runnable immediately after clone.

We use `./agent` instead of a Makefile because:
- Makefiles can't pass arguments cleanly (`make test ARGS="-k foo"`)
- Makefiles duplicate prefix logic (`python3 -m venv ...` repeated)
- A Python script can auto-create the test venv once and reuse it
- Subcommands with argparse give proper `--help` and validation

## Commands

### `./agent install <name>`

Copy an agent definition to user scope (`~/.claude/agents/`) so it's
available via `claude --agent <name>` from any directory.

```bash
./agent install privacy-guard
./agent install privacy-audit
```

Options:

| Flag | Description |
|------|-------------|
| `--local PATH` | Install to `PATH/.claude/agents/` instead of user scope |
| `--force` | Install even if the plugin already provides the agent |

If the plugin is installed and already providing the agent, `install`
warns and exits. Use `--force` to install anyway (needed for CLI
`claude --agent` usage outside interactive sessions).

### `./agent test <name>`

Run integration tests for an agent. Auto-creates `.venv-test/` with
pytest and pytest-xdist on first run.

```bash
# Run all tests for an agent
./agent test privacy-guard

# Run a single test
./agent test privacy-guard -k test_email_in_staged_file

# Run in parallel (5 workers)
./agent test privacy-guard -n 5

# With debug logging
./agent test privacy-guard --debug
./agent test privacy-guard --debug -k test_missing_person_md
```

Options:

| Flag | Description |
|------|-------------|
| `-k PATTERN` | pytest `-k` filter (test name or expression) |
| `-n N` | Number of parallel workers (requires pytest-xdist) |
| `--debug` | Write logs to `/tmp/privacy-guard-tests/` |

Debug logs include per-test harness logs and Claude debug logs. Watch
them in real time:

```bash
tail -f /tmp/privacy-guard-tests/*.log
```

## Agent name resolution

The CLI resolves agent names by looking for `agents/<name>.md`. Test
directories are found with hyphen/underscore normalization — both
`privacy-guard` and `privacy_guard` resolve to the same test dir.

## Available agents

Run `./agent --help` to see the current list, or check `agents/*.md`.
