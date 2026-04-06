# Contributing

## FAQ

**Why don't we copy the agent to `~/.claude/agents/` for testing?**
That creates a sync problem — the copy can drift from the source in
`agents/`. Every change would require a re-copy. Instead, tests create
a symlink from each temp repo's `.claude/agents/privacy-guard.md` back
to the source file. Claude discovers it via local project scope. The
test always runs against the current source. See "How agent tests work"
under Testing.

**Why don't tests use `--plugin-dir` to load the agent?**
We don't want tests to depend on the full plugin being functional. The
agent should be testable in isolation. The symlink approach tests the
agent directly without plugin discovery, marketplace install, or any
other machinery.

**What's the difference between `skills/` and `.claude/skills/`?**
`skills/` is the product — shipped with the plugin, available to users.
`.claude/skills/` is for developing this repo — project-level skills
only available when you open a Claude session here. They are never
shipped. See "Context file architecture" below.

**Does the plugin inject context into repos that install it?**
The plugin's root CLAUDE.md is for developing the plugin itself — it
does NOT load into other repos. How plugins inject context into
consumer repos (if at all) is an open question — see the tracking
issue. Plugins definitely provide skills, agents, hooks, and MCP
servers. Whether there's a context injection mechanism beyond those
needs investigation against Claude docs and the `claude-plugin-creator`
repo.

**Can users run `claude --agent privacy-guard` from the CLI?**
Only if the agent is in `~/.claude/agents/` (user scope) or
`./.claude/agents/` (local scope). Whether plugin-installed agents
resolve via `--agent` from a cold CLI start is unverified — they
definitely appear in `/agents` during interactive sessions where the
plugin is loaded.

## Architecture

This plugin has three types of content:

- **Native skills** — developed here, source of truth is this repo
- **Vendored skills** — sourced from echoskill marketplace, copied at build time
- **Agent definitions** — `.md` files in `agents/`, auto-discovered by the plugin system

## Build process

The build script vendors skills from external marketplaces into `skills/`.
Run it before committing vendored skill updates or tagging a release.

```bash
./build
```

This clones the echoskill repo, copies the listed skills into `skills/`,
and prints a summary. Native skills are never overwritten.

### Dogfooding

The build process is designed to migrate to the `echoskill` CLI
(`eskill`) once it exists. The current raw git clone is a temporary
implementation. When `eskill install --target skills/` is available,
the build script will use it — making this plugin the primary consumer
and validator of the echoskill CLI. Keeping our daily-use plugin
dependent on our own tooling ensures that tooling stays reliable.

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

To add a vendored skill: add it to `build.cfg`, run `./build`, verify
with `pytest tests/`, commit.

To add a native skill: create `skills/<name>/SKILL.md`, reference it
in agent definitions and/or CLAUDE.md as needed.

## Testing

### Unit tests (default)

```bash
pytest tests/
```

Validates plugin structure:
- Every skill referenced in agent definitions exists in `skills/`
- Every SKILL.md has valid frontmatter (name, description)
- Every skill listed in `build.cfg` is present after build
- No empty skill directories

Run after every build and before every commit.

### Integration tests (privacy-guard agent)

These spawn real agent processes against temporary git repos with
planted PII and verify structured JSON output. Each test takes 1-3
minutes.

```bash
# One-time setup
python3 -m venv .venv-test
.venv-test/bin/pip install pytest pytest-xdist

# Run one test at a time (recommended during development)
.venv-test/bin/pytest tests/integration/privacy_guard/ -k <test_name>

# Run all in parallel (full regression)
make test-privacy-guard
```

Set `PRIVACY_GUARD_DEBUG=1` to write per-test logs to
`/tmp/privacy-guard-tests/`. Each test produces a harness log
(`<repo>.log`) and a Claude debug log (`<repo>.claude-debug.log`).
Watch in real time: `tail -f /tmp/privacy-guard-tests/*.log`

Integration tests are excluded from default `pytest` runs via
`pytest.ini`. They only run when explicitly targeted.

The `validate-privacy-guard` project skill (`.claude/skills/`) has
the recommended test execution order and failure diagnosis steps.

#### How agent tests work (symlink isolation)

The agent source lives in `agents/privacy-guard.md` — the same file
shipped with the plugin. Integration tests need to invoke this agent
via `claude --agent privacy-guard`, but without:

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
   `<plugin-repo>/agents/privacy-guard.md`
4. Runs `claude --agent privacy-guard -p "..."` with `cwd` set to
   the temp repo

When Claude starts in the temp repo directory, it discovers the agent
via the local `.claude/agents/` path. The symlink guarantees the test
always runs against the **current source code** of the agent — edits
to `agents/privacy-guard.md` are immediately reflected in the next
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

The symlink setup is in `conftest.py` inside `_init_git_repo()`. It
also symlinks the `pre-publish-privacy-review` skill if the agent's
`skills:` frontmatter references it (pending — see open issues).

#### What the tests use (fictitious data)

Tests do NOT use real personal information. The test PERSON.md contains
obviously fictitious values (`Zanzibar Quuxington`, `Xyzzy Bank`,
`Frobnitz Manor`) that will never collide with real PII on any machine
or trigger real privacy scanners. The agent treats the file as real —
it has the same structure and YAML frontmatter as a real PERSON.md but
with no "this is a test" hints that might cause the agent to behave
differently.

## Release workflow

1. Run `./build` to sync vendored skills
2. Run `pytest tests/` to validate
3. Bump, commit, and tag:
   ```bash
   ./version bump            # patch: 0.1.0 → 0.1.1
   ./version bump --minor    # minor: 0.1.1 → 0.2.0
   ./version bump --major    # major: 0.2.0 → 1.0.0
   ```
   This updates `.claude-plugin/plugin.json`, commits the change,
   and creates an annotated tag `v<new>`. Use `--no-tag` to skip
   the tag if you need to amend or adjust before tagging.
4. Push: `git push origin main --tags`
5. Update marketplace `ref` in the claude-plugins repo

The `./version` script is pure stdlib Python — no venv needed. Run
`./version` with no arguments to show the current version.

### Why not just edit plugin.json by hand?

The script ensures the version in plugin.json, the git commit message,
and the git tag all agree. Manual edits risk version/tag mismatches
that break marketplace installs.

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

Agent `.md` files live in `agents/` and are automatically discovered
when the plugin is installed. They update when the plugin version is
bumped and the user refreshes. No manual copying is needed.

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

1. **Agent-scoped hooks** — Block `git push`, `gh pr create`, and direct
   API calls at the harness level. The agent cannot bypass these.
2. **Agent system prompts** — Non-negotiable workflow with hard stops
   before any GitHub write.
3. **Skills** — privacy-scan and publish-pull-request enforce mechanical
   review steps.

The publish-agent provides an independent clean-room review as the final
gate before any content reaches GitHub.

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

- **Never push directly.** All pushes go through `publish-agent`.
- **Never create PRs directly.** Use the `publish-pull-request` skill
  via `publish-agent`.
- **Run privacy scan before any GitHub write.** Use `/privacy-scan` or
  delegate to `publish-agent`.
- **PULL-REQUEST.md workflow:** Commit it to the feature branch with
  frontmatter (title, closes) and a markdown body. It's consumed by
  `publish-pull-request` and dropped during squash-merge.

## Context file architecture

This repo has multiple layers of context files that serve different
purposes. Understanding which file does what is critical.

### Shipped with the plugin (users get these)

| Path | Purpose |
|------|---------|
| `agents/*.md` | Agent definitions. Auto-discovered when plugin is installed. Users invoke them via `--agent <name>` or `/agents`. |
| `skills/*/SKILL.md` | Plugin skills. Available to users as `/plugin-name:skill-name`. Native or vendored. |
| `hooks/hooks.json` | Lifecycle hooks. Fire on Claude Code events in any repo where the plugin is active. |
| `.claude-plugin/plugin.json` | Plugin manifest. Name, version, description. |

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

### Key distinction: `skills/` vs `.claude/skills/`

- **`skills/`** — the product. Shipped with the plugin. Available to
  anyone who installs it. These are what users interact with.
- **`.claude/skills/`** — developer tools. Only available when you open
  a Claude session in this repo. For internal workflows like testing,
  validation, and development. Never shipped.

### What goes where

| Content | Belongs in |
|---------|-----------|
| How to use the plugin | `README.md` |
| Architecture, testing, dev workflow | `CONTRIBUTING.md` |
| `@` imports of README + CONTRIBUTING | `CLAUDE.md` (root) |
| Agent behavior and scan logic | `agents/*.md` |
| User-facing skills | `skills/*/SKILL.md` |
| Dev-only skills (testing, validation) | `.claude/skills/*/SKILL.md` |
| Safety rules for this repo's development | `CONTRIBUTING.md` (safety section) |
