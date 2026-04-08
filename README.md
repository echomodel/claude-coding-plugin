# claude-coding

Claude Code plugin with privacy-gated commits, session lifecycle
management, and reusable agent/skill composition.

## Two ways to use this

1. **As a plugin** — install once, get everything: agents, skills, hooks,
   safety gates. The plugin activates the **claude-coder** agent by
   default, which preloads skills for safe commits, issue authoring,
   session capture, and testing guidelines.
2. **As standalone agents** — clone the repo, run one command, use any
   agent from the CLI without installing the plugin. Reusable agents
   live in `assets/agents/`.

## What's included

### Agents

- **privacy-guard** — pre-push PII scanner (staged, unstaged, unpushed)
- **privacy-audit** — full-repo PII audit (git history, optionally issues/PRs)
- **claude-coder** — default coding agent with privacy-gated commit workflow

### Skills (8 total — 1 native, 7 vendored from echoskill)

- **safe-commit** — commit-first workflow with privacy-guard scan gate
- author-github-issue, capture-context, sociable-unit-tests,
  identify-best-practices, check-feature-support, code-reuse,
  setup-agent-context

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
claude plugin install claude-coding@claude-plugins --scope user
```

## Standalone agents (no plugin required)

Clone and install any agent in two commands — no plugin, no venv, no
dependencies beyond Python 3:

```bash
git clone https://github.com/echomodel/claude-coding.git
cd claude-coding
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

### Testing agents

See [docs/AGENT-CLI.md](docs/AGENT-CLI.md) for full `./agent` CLI
documentation including install, test, filtering, parallelism, and
debug logging.

```bash
./agent test privacy-guard
./agent test privacy-guard -k test_email_in_staged_file
./agent test privacy-guard -n 5 --debug
```

## Repository structure

```
assets/              <- reusable, marketplaceable (source of truth)
  agents/            <- portable agent definitions
  skills/            <- portable skills (agentskills.io standard)
plugin/
  src/               <- authored plugin infrastructure
  dist/              <- assembled output (committed, Go vendor pattern)
build.cfg            <- marketplace URLs for vendored skills
```

- **`assets/`** — reusable agents and skills that can be published to
  a marketplace independently. Marketplace entries can point directly
  to paths here (e.g., `assets/agents/privacy-guard`).
- **`plugin/src/`** — plugin-specific config, hooks, agents, and build
  tooling. Includes `build.py`, `Makefile`, and `.claude-plugin/plugin.json`
  (the version source of truth).
- **`plugin/dist/`** — fully assembled plugin. **Never edit directly.**
  Run `make -C plugin/src build` to regenerate. Committed to main so
  marketplace install works with no build step (Go vendor pattern).

## Building and distributing

### Build

`make -C plugin/src build` assembles `plugin/dist/` from source files,
plugin infrastructure, and vendored marketplace skills. You must run
it before:

- Using `--plugin-dir plugin/dist/` for local testing
- Committing and pushing for marketplace references to work
- Tagging a release

```bash
make -C plugin/src build
```

### Local testing (no marketplace)

```bash
claude --plugin-dir plugin/dist/
```

### Marketplace registration

To make this plugin installable via a Claude Code plugin marketplace,
add an entry to the marketplace's `marketplace.json` pointing to the
`plugin/dist` subdirectory:

```json
{
  "name": "claude-coding",
  "source": {
    "source": "git-subdir",
    "url": "https://github.com/echomodel/claude-coding.git",
    "path": "plugin/dist"
  },
  "description": "Coding agent with privacy-gated commits and skill composition."
}
```

After committing and pushing the marketplace repo, users install with:

```bash
claude plugin marketplace update <marketplace-name>
claude plugin install claude-coding@<marketplace-name> --scope user
```

### Release workflow

```bash
# 1. Build with version bump
make -C plugin/src build VERSION=X.Y.Z

# 2. Test
pytest tests/lint/ tests/build/

# 3. Commit, tag, push
git add -A
git commit -m "Release vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main --tags
```

The `VERSION` argument stamps the new version in
`plugin/src/.claude-plugin/plugin.json` before building. The build
propagates it to `plugin/dist/`. Without `VERSION`, builds use the
current version in src.

After pushing, update the marketplace ref and reinstall the plugin.

### Marketplace updates

Marketplace solutions like Claude Code's `plugin install` resolve
plugins by git ref. If the marketplace entry has no `ref`, it uses
the default branch (main). If it specifies `ref: "v1.2.0"`, it uses
that tag. Either way, the committed `plugin/dist/` at that ref must
be current — there is no build step at install time.

After pushing a new tag, update the marketplace entry's `ref` if it
pins to a specific tag.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for testing tiers, architecture,
and development workflow.
