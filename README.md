# claude-coding-plugin

Claude Code plugin for autonomous, safety-gated coding work. Takes GitHub
issues as input, works in isolated worktrees, enforces privacy review on
every artifact, and gates all GitHub writes behind human approval.

## Two ways to use this

1. **As a plugin** — install once, get everything: agents, skills, hooks,
   safety gates. Agents appear in `/agents` during interactive sessions.
2. **As standalone agents** — clone the repo, run one command, use any
   agent from the CLI without installing the plugin.

## What's included

- **privacy-guard** — AI-powered PII and privacy scanner
- **refactoring-agent** — Issue-driven autonomous refactoring
- **publish-agent** — Clean-room branch reviewer and publisher
- **Skills** — publish-pull-request, privacy-scan, delegate-refactoring,
  check-feature-support, plus vendored coding skills from echoskill
- **Hooks** — Pre-push safety gates, test skill injection
- **Safety architecture** — Three-layer enforcement (hooks + agent prompts + skills)

## Privacy Guard Agent

An AI agent that scans repositories for personal information leaks.
Unlike regex-based scanners, privacy-guard reasons about context — it
catches things no pattern matcher can.

- Pattern-based detection from configurable PERSON.md
- OS-level discovery (`$USER`, `$HOME`) at runtime
- Judgment-based detection of contextual leaks
- Git author identity and visibility-aware scan tiers
- Read-only by design — cannot modify your repository

See [docs/agents/privacy-guard/](docs/agents/privacy-guard/README.md)
for full documentation including scan scope, detection categories,
containment model, and output schema.

### Prerequisite: personal patterns file

Before first use, create `~/.config/ai-common/PERSON.md` with your
personal information. The agent reads this file to know what to scan
for. Without it, the agent refuses to run.

The file uses YAML frontmatter for machine-parseable patterns:

```yaml
---
patterns:
  github:
    - your-github-username
  emails:
    - your-email@example.com
  email_domains:
    - your-domain.com
  names:
    - Your Name
    - Spouse Name
    - Child Name
  workspace_roots:
    - ~/src
    - ~/projects
  financial_providers:
    - Your Bank
  employers:
    - Your Employer
  properties:
    - Property Name
  cities:
    - Your City
---
```

A markdown body below the frontmatter provides judgment guidance —
false positive rules, employer-specific detection nuances, financial
amount thresholds, and context for city/property names that are also
common words.

The agent discovers OS-level identifiers (username, home directory)
at runtime — those do not go in this file.

**This file must never be committed to any repository.** It lives
only on your machine.

## Install as plugin

```bash
claude plugin marketplace add https://github.com/krisrowe/claude-plugins.git
claude plugin marketplace update claude-plugins
claude plugin install claude-coding-plugin@claude-plugins --scope user
```

### Quick start

```
/delegate-refactoring owner/repo#42
```

The refactoring agent will:
1. Read the issue
2. Create an isolated worktree
3. Make changes, write tests
4. Prepare PULL-REQUEST.md
5. Run privacy scan
6. Present everything for your review
7. On approval, hand off to publish-agent for merge + push

## Standalone agents (no plugin required)

Clone and install any agent in two commands — no plugin, no venv, no
dependencies beyond Python 3:

```bash
git clone https://github.com/krisrowe/claude-coding-plugin.git
cd claude-coding-plugin
./agent install privacy-guard
```

The agent is now available globally:

```bash
claude --agent privacy-guard -p "scan this repo"
```

The agent can scan any repo — just `cd` into it and run. To grant
access to directories outside the repo (e.g., a sibling project):

```bash
cd ~/src/my-project-a
claude --agent privacy-guard --add-dir ~/src/my-project-b -p "scan both this repo and ~/src/my-project-b"
```

If the plugin is already installed, `./agent install` will warn you
that the agent is redundant (use `--force` to install anyway for CLI
`--agent` usage).

**Project-local install** (`--local`) installs the agent to a single
repo's `.claude/agents/` instead of user scope. This is rarely
needed — the user-scope install already works from any directory. The
only case is if you want the agent available for one specific repo and
don't want it showing up in the global agent list:

```bash
./agent install privacy-guard --local ~/src/my-only-project-i-care-about
```

### All agents

| Agent | Description |
|-------|-------------|
| `privacy-guard` | Pre-push PII scanner — staged diffs, unstaged diffs, unpushed commits |
| `privacy-audit` | Full-repo PII audit — git history, optionally issues/PRs |
| `refactoring-agent` | Autonomous issue-driven refactoring in isolated worktrees |
| `publish-agent` | Clean-room branch review and merge+push |

### Testing agents

See [docs/AGENT-CLI.md](docs/AGENT-CLI.md) for full `./agent` CLI
documentation including install, test, filtering, parallelism, and
debug logging.

```bash
./agent test privacy-guard
./agent test privacy-guard -k test_email_in_staged_file
./agent test privacy-guard -n 5 --debug
```

## Build

See [CONTRIBUTING.md](CONTRIBUTING.md) for build process, context file
architecture, and development workflow.
