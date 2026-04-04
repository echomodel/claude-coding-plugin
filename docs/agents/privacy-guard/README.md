# Privacy Guard Agent

An AI agent that scans repositories for personal information leaks.
Unlike regex-based scanners, privacy-guard reasons about context — it
catches things no pattern matcher can.

## Current scope

Privacy-guard scans local git state and GitHub remote metadata:

| Scope | Default | On request |
|-------|---------|------------|
| Working tree (tracked + untracked files) | Yes | |
| Staged changes | Yes | |
| Unpushed commits (messages + diffs) | Yes | |
| Open GitHub issues (titles, bodies, comments) | Yes | |
| Open GitHub PRs (titles, bodies, comments) | Yes | |
| Full git history (all commits, branches, tags) | | Yes |
| Stash entries and reflog | | Yes |
| Closed issues and PRs | | Yes |

## What it catches

**Pattern-based** — matches personal values from PERSON.md
configuration and OS-discovered identifiers (`$USER`, `$HOME`).

**Judgment-based** — contextual leaks no regex can catch: personal
framing in documentation, real IDs in example code, family names in
test fixtures.

**Built-in patterns** — credential formats (API keys, tokens, private
keys), structural IDs (GCP project IDs, Google Doc IDs), and other
recognized PII patterns — with or without PERSON.md.

## Containment model

The agent exists to **contain** PII exposure. It reads PERSON.md so
the parent agent doesn't have to. See
[CONTRIBUTING.md](../../../CONTRIBUTING.md) ("Subagent containment
principle") for the full model.

Key rule: findings include matched values (the parent needs them to
fix issues). Scan targets (the universe of values checked) never
appear in output — only counts and source categories.

## Structured output

Every scan produces machine-parseable JSON. See:

- [SCHEMA.md](SCHEMA.md) — current output schema
- [SCHEMA-PROPOSAL.md](SCHEMA-PROPOSAL.md) — proposed redesign
  (SARIF-inspired rules/results model, scope changes, attribution)

## Configuration and usage

See the [root README](../../../README.md) for PERSON.md setup,
installation, and CLI usage.
