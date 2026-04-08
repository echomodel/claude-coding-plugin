# Contributing

## FAQ

**Why don't we copy the agent to `~/.claude/agents/` for testing?**
That creates a sync problem — the copy can drift from the source in
`assets/agents/`. Every change would require a re-copy. Instead, tests
create a symlink from each temp repo's `.claude/agents/privacy-guard.md`
back to the source file. Claude discovers it via local project scope. The
test always runs against the current source. See "How agent tests work"
under Testing.

**Why don't tests use `--plugin-dir` to load the agent?**
We don't want tests to depend on the full plugin being functional. The
agent should be testable in isolation. The symlink approach tests the
agent directly without plugin discovery, marketplace install, or any
other machinery.

**What's the difference between `assets/skills/` and `.claude/skills/`?**
`assets/skills/` contains reusable skills that are the source of truth
for this repo. They get copied into `plugin/dist/skills/` by the build
script and shipped with the plugin. `.claude/skills/` is for developing
this repo — project-level skills only available when you open a Claude
session here. They are never shipped. See "Context file architecture"
below.

**Does the plugin inject context into repos that install it?**
The plugin's root CLAUDE.md is for developing the plugin itself — it
does NOT load into other repos. How plugins inject context into
consumer repos (if at all) is an open question — see the tracking
issue. Plugins definitely provide skills, agents, hooks, and MCP
servers. Whether there's a context injection mechanism beyond those
needs investigation against Claude docs and the `claude-plugin-creator`
repo.

**Can users run `claude --agent privacy-guard` from the CLI?**
Yes — if the agent is in `~/.claude/agents/` (user scope) or
`./.claude/agents/` (project scope), use the bare name. If loaded
via a plugin, use the namespaced form:
`--agent claude-coding:privacy-guard`. The `test_via_plugin.py`
integration test verifies plugin-based discovery end-to-end.

## Repository structure

This repo follows the **aggregator plugin pattern** — a plugin that
owns reusable assets (agents, skills), composes them with vendored
marketplace dependencies and plugin-specific infrastructure, and
ships a fully assembled distribution that works with zero build steps
at install time.

### Aggregator plugin pattern

This pattern is reusable across any plugin that aggregates and
composes reusable assets. The key principles:

1. **Source separation** — reusable assets (`assets/`), authored
   plugin infrastructure (`plugin/src/`), and assembled output
   (`plugin/dist/`) never share a directory. Each has a clear role
   and edit policy.

2. **Skills as modular agent extensions** — the default agent preloads
   skills via `skills:` frontmatter. These skills are the agent's
   detailed workflow instructions, modularized so they're independently
   reusable from a marketplace. The agent body stays lean (universal
   rules only); specific workflows live in skills.

3. **Go vendor pattern for distribution** — `plugin/dist/` is
   committed to main so marketplace install works with no build step.
   `make -C plugin/src build` regenerates it from source + vendored
   dependencies. In CI, run the build and `git diff --exit-code
   plugin/dist/` to verify the committed dist is current.

4. **Dependency pinning without a new source of truth** — vendored
   skills are snapshots from the marketplace at a specific ref.
   `build.cfg` declares what to vendor and from where. The vendored
   copies in `plugin/dist/` are the only copies — no duplication
   at repo root. Native skills (in `assets/skills/`) take precedence
   over vendored skills with the same name.

5. **Marketplace-ready assets** — everything in `assets/` can be
   pointed at by a marketplace entry independently of the plugin.
   A skills marketplace can reference `assets/skills/safe-commit`;
   an agents marketplace can reference `assets/agents/privacy-guard`.
   The plugin bundles them, but they stand alone.

6. **Plugin-specific agents are not second-class** — `plugin/src/agents/`
   holds agents that are coupled to this plugin's skill/hook ecosystem
   (e.g., claude-coder depends on safe-commit → privacy-guard). These
   are fully featured agents, just not independently reusable.

This contrasts with the **simple plugin pattern** where the repo root
IS the plugin directory — no build step, no asset separation, no
vendoring. Simple plugins are appropriate when the plugin is
self-contained with no reusable assets to share.

### Directory layout

```
claude-coding/
  assets/              <- reusable, marketplaceable (source of truth)
    agents/            <- portable agent definitions
    skills/            <- portable skills (agentskills.io standard)
    README.md
  plugin/
    src/               <- authored plugin infrastructure (tracked)
      .claude-plugin/plugin.json
      agents/          <- plugin-specific agents (e.g., claude-coder)
      hooks/
      settings.json
      .mcp.json
    dist/              <- assembled output (committed, Go vendor pattern)
      ...              <- everything from assets/ + plugin/src/ + vendored
  build                <- assembles plugin/dist/ from all sources
  build.cfg            <- marketplace URLs for vendored skills
```

### Directory roles

| Directory | Edit directly? | Committed? | Role |
|-----------|---------------|------------|------|
| `assets/agents/` | Yes | Yes | Reusable agents — marketplace candidates |
| `assets/skills/` | Yes | Yes | Reusable skills — marketplace candidates |
| `plugin/src/` | Yes | Yes | Authored plugin infrastructure |
| `plugin/src/agents/` | Yes | Yes | Plugin-specific agents (not reusable) |
| `plugin/dist/` | **Never** | Yes | Assembled by `make -C plugin/src build` — Go vendor pattern |

### Why `plugin/dist/` is committed (Go vendor pattern)

The marketplace constraint: `claude plugin install` clones from git and
expects a working plugin at that ref. No build runs at install time.
This matches Go's `vendor/` directory and protobuf generated code
patterns — generated output committed for consumer convenience.

In CI, verify dist is current with `make -C plugin/src build && git diff --exit-code plugin/dist/`.

### What goes where

| Content | Belongs in |
|---------|-----------|
| Reusable agent (works standalone, marketplace candidate) | `assets/agents/` |
| Reusable skill (agentskills.io, marketplace candidate) | `assets/skills/` |
| Plugin-specific agent (coupled to this plugin's skills/hooks) | `plugin/src/agents/` |
| Plugin config (plugin.json, settings.json, hooks, .mcp.json) | `plugin/src/` |
| Vendored skills from external marketplaces | `build.cfg` → `plugin/dist/skills/` |

### Reusable vs plugin-specific agents

An agent is reusable if it works standalone without depending on this
plugin's skills, hooks, or other agents. `privacy-guard` and
`privacy-audit` are reusable — they scan independently.

`claude-coder` is plugin-specific — its `skills:` frontmatter references
`safe-commit`, which invokes `privacy-guard`, creating a dependency
chain that only works with this plugin installed.

### Skills as modular agent extensions

The claude-coder agent's `skills:` frontmatter preloads skills that
are effectively modular extensions of the agent body itself:

```yaml
skills:
  - safe-commit          # commit workflow with privacy gate
  - author-github-issue  # issue authoring conventions
  - capture-context      # session wrap-up and context preservation
  - sociable-unit-tests  # testing philosophy and patterns
  - project-docs         # documentation structure and safe refactoring
```

These skills are independently reusable — any agent or user can invoke
them. But for this plugin, they function as the agent's detailed
instructions for specific workflows, modularized so they can also be
used outside the plugin context.

This pattern is valuable because:

- **Reuse without duplication** — the same skill body serves both the
  plugin's default agent and standalone use via marketplace install.
- **Independent evolution** — a skill can be updated in the marketplace
  without changing the agent definition. The plugin vendors the latest
  version at build time.
- **Composability** — different agents can compose different skill sets.
  A minimal agent might load only `safe-commit`; the full claude-coder
  loads all five.
- **The agent itself may or may not be reusable** — claude-coder is
  plugin-specific (coupled to safe-commit → privacy-guard), but the
  skills it preloads are all independently reusable assets published
  to the marketplace.

## Build process

The build script assembles `plugin/dist/` from all sources:

```bash
make -C plugin/src build          # assemble plugin/dist/
```

Sources assembled into `plugin/dist/`:
1. `plugin/src/` — plugin infrastructure (plugin.json, hooks, settings, .mcp.json)
2. `plugin/src/agents/` — plugin-specific agents (claude-coder)
3. `assets/agents/` — reusable agents (privacy-guard, privacy-audit)
4. `assets/skills/` — native skills (safe-commit)
5. `build.cfg` — vendored skills from echoskill marketplace

Native skills (from `assets/skills/`) take precedence over vendored
skills with the same name.

### Dogfooding

The build process is designed to migrate to the `echoskill` CLI
(`eskill`) once it exists. The current raw git clone is a temporary
implementation. When `eskill install --target plugin/dist/skills/` is
available, the build script will use it — making this plugin the primary
consumer and validator of the echoskill CLI.

### Configuration

`build.cfg` lists which skills to vendor and from where:

```ini
[echoskill]
url = https://github.com/echo-skill/echoskill.git
ref = main
skills =
    coding/author-github-issue
    coding/sociable-unit-tests
    ...
```

To add a vendored skill: add it to `build.cfg`, run `make -C plugin/src build`, commit
the updated `plugin/dist/`.

To add a native skill: create `assets/skills/<name>/SKILL.md`, run
`make -C plugin/src build`, commit both the source and the updated `plugin/dist/`.

## Testing

Three test tiers, from fast/free to slow/expensive:

### Lint (default — runs without build)

```bash
pytest tests/lint/
```

Static validation of source files. No build step required:
- Agent `.md` files have valid frontmatter (name, description)
- Agent `skills:` refs resolve to `assets/skills/` or `build.cfg`
- Skill SKILL.md files have valid frontmatter
- Plugin src files exist and are valid JSON
- `settings.json` agent ref resolves to a real agent file

### Build structural (requires `make -C plugin/src build` first)

```bash
make -C plugin/src build
pytest tests/build/
```

Validates the assembled `plugin/dist/` artifact:
- Every agent from `assets/agents/` and `plugin/src/agents/` is present
- Every native skill from `assets/skills/` is present
- Every vendored skill from `build.cfg` is present
- Plugin infrastructure files exist and are valid JSON

These tests auto-skip with a clear message if `plugin/dist/` is
missing or stale (source files newer than last build).

### CI staleness check

In CI, verify committed `plugin/dist/` is current:

```bash
make -C plugin/src build
git diff --exit-code plugin/dist/
```

If the diff is non-empty, someone changed source without rebuilding.

### Integration tests (privacy-guard agent)

These spawn real agent processes against temporary git repos with
planted PII and verify structured JSON output. Each test takes 1-3
minutes.

```bash
# Run one test at a time (recommended during development)
./agent test privacy-guard -k <test_name>

# Run all in parallel (full regression)
./agent test privacy-guard
```

Set `PRIVACY_GUARD_DEBUG=1` to write per-test logs to
`/tmp/privacy-guard-tests/`. Each test produces a harness log
(`<repo>.log`) and a Claude debug log (`<repo>.claude-debug.log`).
Watch in real time: `tail -f /tmp/privacy-guard-tests/*.log`

Integration tests are excluded from default `pytest` runs via
`pytest.ini`. They only run when explicitly targeted.

The `debug-agent-tests` project skill (`.claude/skills/`) has
the recommended test execution order and failure diagnosis steps.

#### How agent tests work (symlink isolation)

The agent source lives in `assets/agents/privacy-guard.md`. Integration
tests need to invoke this agent via `claude --agent privacy-guard`, but
without:

- Installing the plugin (via marketplace or `--plugin-dir`)
- Copying the agent to `~/.claude/agents/` (creates a sync problem)
- Depending on any plugin machinery to resolve the agent

Claude resolves `--agent <name>` by looking in:
1. `~/.claude/agents/<name>.md` (user scope)
2. `./.claude/agents/<name>.md` (local project scope)

The test harness exploits option 2. For each test, `conftest.py`:

1. Creates a temporary git repo in an OS-managed temp directory
2. Creates `.claude/agents/` inside that temp repo
3. Symlinks `.claude/agents/privacy-guard.md` → the source file at
   `<repo>/assets/agents/privacy-guard.md`
4. Runs `claude --agent privacy-guard -p "..."` with `cwd` set to
   the temp repo

When Claude starts in the temp repo directory, it discovers the agent
via the local `.claude/agents/` path. The symlink guarantees the test
always runs against the **current source code** of the agent — edits
to `assets/agents/privacy-guard.md` are immediately reflected in the next
test run without any copy, sync, or install step.

This approach:

- **Isolates each test** — every test gets its own temp repo with its
  own `.claude/agents/` symlink, independent of all other tests
- **Tests the real agent** — the symlink points to the actual source
  file, not a copy or fixture
- **Has no external dependencies** — doesn't need the plugin installed,
  doesn't need `~/.claude/agents/` populated, doesn't need `--plugin-dir`
- **Works in parallel** — each test's temp dir is unique (pytest
  `tmp_path`), so parallel workers don't collide
- **Cleans up automatically** — pytest removes temp dirs after the run

The symlink setup is in `conftest.py` inside `_init_git_repo()`.

#### What the tests use (fictitious data)

Tests do NOT use real personal information. The test PERSON.md contains
obviously fictitious values (`Zanzibar Quuxington`, `Xyzzy Bank`,
`Frobnitz Manor`) that will never collide with real PII on any machine
or trigger real privacy scanners. The agent treats the file as real —
it has the same structure and YAML frontmatter as a real PERSON.md but
with no "this is a test" hints that might cause the agent to behave
differently.

#### Template repo and PII injection

Tests use a template repo (`tests/fixtures/template_repo/`) containing
~20 clean Python files — a realistic widget service with models, API
handlers, tests, config, and docs. Each test copies the template into
a temp git repo, then injects PII into specific locations (staged
files, unstaged modifications, commit messages, code comments, config
files, test fixtures). This ensures:

- **Needle in a haystack** — PII is <5% of repo content, not 50%
- **Varied injection points** — different tests put PII in different
  file types and git states (staged, unstaged, committed)
- **No scanner tripping** — credentials and secrets are built via
  string concatenation at runtime (`"ghp_" + "a" * 36`), never
  hardcoded as complete strings. This prevents precommit scanners
  from flagging the test code itself.
- **Same base, different injections** — all tests share the template
  so adding new test scenarios is cheap

The template files live in `tests/fixtures/template_repo/` as real
files on disk (not zipped, not generated). Edit them directly to
change the baseline content all tests inherit.

#### Why we split agents instead of parameterizing

Privacy-guard and privacy-audit are separate agents rather than modes
of one agent. Claude Code agents receive inputs only through the
prompt (unstructured text), the agent `.md` definition (static), and
files the agent reads at runtime. There is no structured input
contract — no typed parameters, no schema for inputs.

In testing we observed that the prompt can override config file
settings (a parent agent requesting "deep scan" overrode the user's
`pre-push` config). Until Claude Code supports formal agent input
schemas, splitting by usage pattern is more reliable than runtime
parameterization. See the open issues for agent contract research.

## Release workflow

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

# 4. Update marketplace ref and reinstall
```

The `VERSION` argument stamps the new version in
`plugin/src/.claude-plugin/plugin.json` before building. The build
propagates it to `plugin/dist/`. Without `VERSION`, builds use the
current version.

After pushing, update the marketplace entry's `ref` field to the new
tag, commit and push the marketplace repo, then reinstall the plugin.

### Agent parameterization note

Privacy-guard and privacy-audit are split into separate agents rather
than parameterized modes of one agent. Claude Code agents receive
inputs only through the prompt (unstructured text from the caller or
user), the agent `.md` definition (static), and files the agent reads
at runtime. There is no structured input contract — no typed parameters,
no JSON schema for inputs, no equivalent of function arguments.

This means the caller's prompt can override config file settings (as
we observed: a parent agent requesting "deep scan" overrode the user's
`pre-push` config). Until Claude Code supports formal agent input
schemas (e.g., A2A Agent Cards, MCP tool wrapping, or frontmatter
parameter declarations), splitting agents by usage pattern is more
reliable than runtime parameterization.

## Agent definitions

Reusable agent `.md` files live in `assets/agents/`. Plugin-specific
agents live in `plugin/src/agents/`. Both are assembled into
`plugin/dist/agents/` by `make -C plugin/src build` and automatically discovered when
the plugin is installed.

Plugin agents cannot use `hooks`, `mcpServers`, or `permissionMode`
frontmatter (security restriction). Agents that need hooks must be
installed to `~/.claude/agents/` separately.

### Memory settings

Each agent can have a `memory` field in its frontmatter (`user`,
`project`, `local`). Memory settings are intentional — each agent's
memory scope is decided case-by-case based on whether the agent should
learn and what scope that learning applies to.

## Safety architecture

Three reinforcement layers protect against accidental PII exposure:

1. **Agent definitions** — privacy-guard scans diffs and unpushed
   commits with LLM judgment. Built-in patterns catch credentials
   and secrets. Employer context table catches contextual leaks.
2. **Plugin hooks** — PostToolUse(Agent) verifies subagent input/output.
   PreToolUse(Bash) blocks uncertified pushes. See
   `docs/design/scan-cert-chain.md`.
3. **Deterministic scanners** — git pre-commit hooks (consult precommit,
   git-scan) catch known patterns with regex. Defense in depth.

### Subagent containment principle

The privacy-guard agent exists to **contain** PII exposure. It reads
PERSON.md so the parent agent doesn't have to. The containment boundary
is between what the agent **scanned for** (the universe of sensitive
values from PERSON.md, OS discovery, built-in patterns) and what it
**found** (specific values that already exist in the repo). These two
categories have opposite output rules.

**Matched values: MUST be reported.** The parent agent already has
access to these values — they are in the code, commits, issues, or
other artifacts the parent can see. The parent agent is responsible
for fixing them, which it cannot do without knowing the specific value
and its location. Reporting a matched value also makes the parent
agent less likely to repeat it in the same session — being told "this
email in src/config.py:42 is PII" is a corrective signal.

**Scan targets: MUST NOT be reported.** The full set of values the
agent checked for — every email, name, financial provider, etc. from
PERSON.md — must never appear in the output. The parent agent has no
need for these values and may not even be aware they exist. Exposing
them expands the parent's knowledge of the user's personal information
beyond what is already in the repo, increasing the risk of accidental
inclusion in commits, issues, PR descriptions, or conversation.

**Rules for subagent output:**

- **Never echo PERSON.md contents** — the agent already has this rule
  (Hard Rules in the agent definition). The structured JSON and
  human-readable report must not include the patterns being scanned
  for, only the values that were actually found.
- **Findings include matched values and locations** — a finding says
  "found email `user@example.com` in src/config.py:42". The parent
  needs both the value and the location to take action.
- **Scan metadata reports counts and sources, not values** — the
  structured output should include metadata about what categories were
  scanned, how many values per category, and where those values came
  from (PERSON.md frontmatter, PERSON.md body, OS runtime, prompt,
  built-in patterns). But it reports **counts and sources only**.
  For example: `{"category": "emails", "values_count": 3, "source":
  "person_md_frontmatter"}` — not the actual email addresses that
  were searched for.
- **Attribution per finding** — each finding should indicate where the
  agent learned that the matched value was sensitive: `person_md_frontmatter`,
  `person_md_body`, `prompt`, `builtin_pattern`, `os_runtime`, or
  `contextual_judgment`. This enables tests to assert on *why* the agent
  flagged something, not just *what*.
- **The parent agent context is the threat model** — any value in the
  subagent's output enters the parent agent's context window. Matched
  values are already in the parent's accessible scope (the repo), so
  reporting them adds no new exposure. But scan targets from PERSON.md
  may include values the parent has never seen — family names not in
  any code, financial providers with no repo reference, etc. Leaking
  those expands the parent's PII surface for no benefit.

### Safety rules for interactive sessions

When working on this repo interactively (not through an agent):

- **Run privacy-guard before pushing.** Use `/safe-commit` or invoke
  the privacy-guard agent directly.
- **Review the scan output** before pushing. The agent reports findings
  with matched values and locations.

## Context file architecture

This repo has multiple layers of context files that serve different
purposes. Understanding which file does what is critical.

### Shipped with the plugin (users get these)

Everything in `plugin/dist/` is what the user gets when they install
the plugin. This directory is assembled by `make -C plugin/src build` — never edit it
directly.

| Path | Purpose |
|------|---------|
| `plugin/dist/agents/*.md` | Agent definitions. Assembled from `assets/agents/` (reusable) and `plugin/src/agents/` (plugin-specific). |
| `plugin/dist/skills/*/SKILL.md` | Plugin skills. Native from `assets/skills/` + vendored from echoskill marketplace. |
| `plugin/dist/hooks/hooks.json` | Lifecycle hooks. Sourced from `plugin/src/hooks/`. |
| `plugin/dist/.claude-plugin/plugin.json` | Plugin manifest. Sourced from `plugin/src/.claude-plugin/`. |
| `plugin/dist/settings.json` | Default agent activation. Sourced from `plugin/src/`. |

**Plugins do NOT inject context into other repos.** They provide
tools, skills, agents, and hooks — not CLAUDE.md content. The user's
repo has its own CLAUDE.md for project context.

### For developing this repo (devs get these)

| Path | Purpose |
|------|---------|
| `CLAUDE.md` (repo root) | `@` imports README.md and CONTRIBUTING.md so agents working on this repo have full context. |
| `.claude/CLAUDE.md` | Not used. Root `CLAUDE.md` handles context. |
| `.claude/skills/*/SKILL.md` | Project-level skills for repo development. NOT shipped with the plugin. Example: `validate-privacy-guard` for running integration tests. |
| `CONTRIBUTING.md` | Architecture, testing, design constraints, safety rules — everything an agent or developer needs to work on this repo. |

### Key distinction: `assets/skills/` vs `plugin/dist/skills/` vs `.claude/skills/`

- **`assets/skills/`** — reusable skills, source of truth. Marketplace
  candidates. Copied into `plugin/dist/skills/` by `make -C plugin/src build`.
- **`plugin/dist/skills/`** — assembled plugin output. Contains native
  skills from `assets/skills/` plus vendored skills from marketplace.
  Never edit directly.
- **`.claude/skills/`** — developer tools. Only available when you open
  a Claude session in this repo. For internal workflows like testing,
  validation, and development. Never shipped.

### What goes where

| Content | Belongs in |
|---------|-----------|
| How to use the plugin | `README.md` |
| Architecture, testing, dev workflow | `CONTRIBUTING.md` |
| `@` imports of README + CONTRIBUTING | `CLAUDE.md` (root) |
| Reusable agent definitions | `assets/agents/*.md` |
| Reusable skills | `assets/skills/*/SKILL.md` |
| Plugin-specific agents | `plugin/src/agents/*.md` |
| Plugin infrastructure (hooks, config) | `plugin/src/` |
| Dev-only skills (testing, validation) | `.claude/skills/*/SKILL.md` |
| Safety rules for this repo's development | `CONTRIBUTING.md` (safety section) |
