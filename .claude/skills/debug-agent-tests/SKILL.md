---
name: debug-agent-tests
description: >-
  Run and debug integration tests for any agent in this plugin. Use when
  the user says "test the agent", "run tests for privacy-guard", "debug
  agent tests", "validate privacy guard", or after modifying any agent
  definition in agents/.
user-invocable: true
argument-hint: "<agent-name> [test-filter]"
---

# Debug Agent Integration Tests

Run integration tests for any agent in this plugin. Each test spawns a
real `claude --agent` process against a temporary git repo with planted
PII and verifies the structured JSON output.

## Available test suites

| Agent | Test dir | What it tests |
|-------|----------|---------------|
| `privacy-guard` | `tests/integration/privacy_guard/` | Pre-push scope: staged diffs, unstaged diffs, unpushed commits |
| `privacy-audit` | `tests/integration/privacy_audit/` | Full audit: git history, pattern detection across files and commits |

## How to run

Use `./agent test` — it handles venv setup, debug logging, filtering,
and parallelism. See `docs/AGENT-CLI.md` for full reference.

### Single test (default — always start here)

```bash
./agent test <agent-name> -k <test_name> --debug
```

Each test takes 15s-3min (spawns a real agent). Run one at a time to
get fast feedback. Stop at the first failure.

### All tests for an agent

```bash
./agent test <agent-name> --debug
```

### Parallel (full regression only)

```bash
./agent test <agent-name> -n 5
```

Only use parallel after individual tests pass. Parallel runs give no
incremental feedback.

## Debug logging

`--debug` writes two log files per test to `/tmp/privacy-guard-tests/`:

| File | Contents |
|------|----------|
| `<repo-name>.log` | Test harness log: commands run, raw agent output, parsed JSON |
| `<repo-name>.claude-debug.log` | Claude internals: tool calls, model responses |

Watch in real time:

```bash
tail -f /tmp/privacy-guard-tests/*.log
```

## Privacy-guard test order

Run cheap tests first to catch problems early:

1. `test_missing_person_md` — agent fails fast, ~15s
2. `test_clean_repo_no_findings` — scans but finds nothing
3. `test_email_in_staged_file` — basic staged detection
4. `test_email_in_unstaged_change` — unstaged detection
5. `test_email_in_unpushed_commit_diff` — unpushed commit detection
6. `test_pii_in_unpushed_commit_message` — commit message detection
7. `test_pushed_pii_not_found` — scope boundary: pushed PII invisible
8. `test_does_not_read_individual_files` — scope boundary: no file reads
9. `test_untracked_files_trigger_warning` — untracked file warning
10. `test_completed_scan_has_required_fields` — JSON structure
11. `test_failed_scan_has_required_fields` — failure JSON structure
12. `test_scan_scope_reflects_what_was_checked` — scan_scope accuracy
13. `test_via_plugin.py::test_agent_runs_via_plugin_dir` — plugin discovery

## After a failure

1. **Check the harness log:**
   ```bash
   cat /tmp/privacy-guard-tests/<repo-name>.log
   ```

2. **Is structured JSON present?** Look for the `privacy-guard-result`
   fenced block in the raw output. If missing, the agent didn't follow
   its output instructions.

3. **JSON present but wrong findings?** Compare `matched_value` and
   `category` fields against what was planted in the test fixture
   (see `conftest.py` for fixture definitions).

4. **Agent doing unexpected things?** Check the Claude debug log:
   ```bash
   cat /tmp/privacy-guard-tests/<repo-name>.claude-debug.log
   ```
   Look for: tool calls the agent made, whether it read files it
   shouldn't have, whether it chained commands with `&&`.

5. **Fix the agent .md or the test fixture, not both at once.**

## What these tests DON'T cover

- Real PERSON.md values (tests use fictitious data only)
- GitHub issues/PRs (test repos have no real remote)
- Private repo inventory (no gh access in test repos)
- Plugin discovery is covered by `test_via_plugin.py` only
