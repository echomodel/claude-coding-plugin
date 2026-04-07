---
name: project-docs
description: >-
  Guidelines for editing project documentation files (.md). Enforces
  audience-appropriate content placement (README vs CONTRIBUTING vs
  docs/), safe refactoring practices that prevent content loss, and
  consistent documentation architecture across repos. Use when
  creating, editing, restructuring, or refactoring any .md files
  in a project.
---

# Project Documentation

Guidelines for how project documentation is structured, what goes
where, and how to safely refactor documentation without losing content.

## Documentation architecture

Every repo has two primary documentation files with distinct audiences:

### README.md — the visitor

The audience is someone evaluating or using the project. They want to
know what this is, why they'd use it, and how to get started.

**Belongs here:**
- What the project does (value proposition)
- Quick setup / installation instructions
- User-facing features and capabilities
- Usage examples
- Prerequisites
- Links to detailed docs

**Does NOT belong here:**
- Design rationale or architecture decisions
- Development workflow or testing instructions
- Internal conventions or guardrails
- Contributor-only context

A visitor should finish the README knowing whether this project solves
their problem and how to start using it. They should not need to
understand the codebase to benefit from the README.

### CONTRIBUTING.md — the contributor

The audience is someone working on the project — a developer, an AI
coding agent, or a future version of yourself. They need to understand
how the project works, why decisions were made, and what guardrails
exist.

**Belongs here:**
- Architecture and design principles
- Directory structure and what goes where
- Build process and development workflow
- Testing strategy and how to run tests
- Safety rules and guardrails
- Design rationale and alternatives considered
- Release workflow

**Does NOT belong here:**
- User-facing feature descriptions (that's README)
- Installation instructions for end users (that's README)
- Content that only serves a single session (use tasks or temp files)

### docs/ — detailed reference

For content too long for CONTRIBUTING.md but needed by contributors:
- Design documents (`docs/design/`)
- Agent documentation (`docs/agents/`)
- Pattern documentation (`docs/patterns/`)
- API or schema references

Link to these from CONTRIBUTING.md. They extend it, not replace it.

### The overlap test

When content could go in either README or CONTRIBUTING, ask: **who
benefits from reading this?**

- "How to install the plugin" → README (user benefits)
- "What agents are included" → README (user benefits)
- "How to register in a marketplace" → README (user who curates a marketplace benefits)
- "How agent tests use symlink isolation" → CONTRIBUTING (contributor benefits)
- "How the build script assembles plugin/dist/" → CONTRIBUTING (contributor benefits)

### When internals matter to users

Some implementation details that are ostensibly contributor-only have
real impact on product selection, installation, or usage. These deserve
at least a mention in README even though the full explanation lives in
CONTRIBUTING:

- **Dependency footprint** — "pure stdlib, no external dependencies"
  tells users they can run this anywhere without worrying about what
  gets installed, whether it works in locked-down environments without
  PyPI access, and what vulnerability surface they're adding.
- **Distribution pattern** — "no build step at install time" tells
  users they can clone and use immediately. The *why* (Go vendor
  pattern) is CONTRIBUTING material, but the *consequence* (zero
  install friction) is README material.
- **Architecture choices that affect UX** — if read-only by design,
  say so in README (users care about safety). The architectural
  rationale belongs in CONTRIBUTING.

The rule: don't go out of your way to surface every internal detail.
But when an implementation choice provides meaningful signal for
product selection, installation, or usage, touch on the **user-facing
consequence** in README and leave the **rationale and mechanics** in
CONTRIBUTING.

### Minimizing duplication across README and CONTRIBUTING

Assume contributors read the README first. Do not repeat README
content in CONTRIBUTING — instead, link back to README for details
that are already covered there. CONTRIBUTING should build on the
README, not restate it.

Conversely, if all relevant details for a topic belong in README
(because they serve users), don't duplicate them in CONTRIBUTING
just to be thorough. The goal is a single source of truth for each
piece of information with links between documents.

### Modularized README

When README grows long, split user-facing content into `docs/<topic>.md`
files and link from README. This keeps README succinct and digestible,
especially in early sections (value prop, quick start, install).

**Important:** do not just link — include enough summary in README to
serve two audiences:

1. **Users scanning the README** — they should get the gist without
   clicking through. A bare link with no context is a dead end for
   someone deciding whether to use the project.
2. **Agents with README loaded as context** — agents typically load
   README.md and CONTRIBUTING.md at session start but NOT every
   `docs/*.md` file. The summary in README gives the agent enough
   awareness to know what exists and where to find details when needed.

Example — instead of:
```markdown
See [docs/authentication.md](docs/authentication.md) for details.
```

Write:
```markdown
Authentication uses OAuth 2.0 with PKCE for browser-based flows and
API keys for service-to-service calls. Tokens are stored in the
system keychain, never on disk. See
[docs/authentication.md](docs/authentication.md) for full
documentation including supported providers, token lifecycle, and
error handling.
```

Be mindful that modularization means some content won't be in the
agent's default context. The summaries in README bridge this gap —
they give the agent enough to work with for most tasks and tell it
where to look for deeper detail.

## Agent context loading

README.md and CONTRIBUTING.md should be loaded into agent context at
session start so the agent has full project awareness. If a
`setup-agent-context` skill is available, invoke it to configure:

- `CLAUDE.md` with `@README.md` and `@CONTRIBUTING.md` imports
- `.gemini/settings.json` with context file declarations

This ensures every coding session — human or agent — starts with the
same foundational understanding of the project. Note that `docs/*.md`
files are NOT auto-loaded — the agent reads them on demand when it
needs more detail on a topic summarized in README or CONTRIBUTING.

## Safe documentation refactoring

When restructuring documentation (splitting files, moving sections
between files, consolidating), follow these rules to prevent content
loss:

### Never remove before confirming capture

1. **Write the destination content FIRST** — create the new file or
   section where content is moving to
2. **Verify coverage line by line** — not just conceptually, but every
   detail, nuance, example, and caveat from the source
3. **Only THEN remove from the source** — after the destination is
   confirmed complete
4. **Diff old vs new** — if doing a full rewrite, compare the original
   against the replacement and account for every removed section

### Prefer duplication over loss

If you can't verify complete coverage in one step, leave the content
in both places temporarily. Inconsistency is recoverable — lost content
is not. Treat it like a database migration: new schema up, migrate
data, only then drop old columns.

### What gets lost in rewrites

Common content lost during documentation restructuring:
- YAML examples with specific field names and values
- Edge case notes and caveats ("this only works when...")
- CLI flags and their explanations
- Links to other docs or issues
- Nuanced explanations that seem obvious but aren't
- Security warnings and "must never" rules

### Atomic edits

When moving a section from file A to file B:
1. Add to file B (with any updates/corrections)
2. Verify B covers everything from A's version
3. Replace A's section with a link to B (or remove if redundant)
4. All three steps in one commit — never leave a gap between removing
   from A and adding to B

## Cross-repo references

Before mentioning a file, resource, module, repo, or document outside
the current repo in any artifact (documentation, code comments, test
cases, commit messages, issue bodies, examples), verify:

1. **Does the current repo have a declared dependency on it?** Check
   dependency manifests, build configuration files, or equivalent.
   Does it import from or vendor from that repo?
2. **Is there existing precedent?** Does the current repo already
   reference that external resource elsewhere?
3. **Visibility check:** if the current repo is public and the
   referenced resource is in a private repo, this is **never correct**.
   The reference will be a dead link for anyone without access. Same
   applies to GitHub issues, PRs, and comments — never reference
   private resources from public artifacts.
4. **No reverse references:** a dependency must never refer back to
   something that depends on it. References flow downstream (depender
   → dependency), never upstream. A reusable library should not
   mention the applications that consume it. A skill should not name
   the plugins that load it. This is a specific case of a broader
   principle: **reference direction follows dependency direction.**
   Circular references between repos, documents, or modules create
   maintenance burdens and coupling that defeats the purpose of
   separation.
5. **Even in examples:** avoid using real external file names, repo
   names, or module names as illustrative examples in code comments,
   markdown, test cases, or commit messages. Use obviously
   hypothetical names instead. A "harmless example" referencing a
   real resource can confuse readers, create false expectations of
   a dependency, or leak the existence of private resources.
6. **No local workspace paths:** never use paths that reveal the
   author's workspace layout. Use universal placeholders like
   `~/projects/my-app` or describe abstractly ("project root",
   "workspace directory"). This includes examples — write
   `cd ~/projects/my-app` not `cd ~/my-particular-workspace/repo`.

**These rules apply to the agent's own output too.** When writing or
editing documentation, code comments, examples, commit messages, or
issue bodies, the agent must follow these same cross-repo reference
rules — not just enforce them on existing content. Use generic terms
(e.g., "dependency manifests" not a specific filename from another
repo) and hypothetical examples (not real external resources).

## When this skill applies

This guidance applies whenever working with `.md` files in a project,
including:
- Creating new documentation files
- Editing existing README.md or CONTRIBUTING.md
- Moving content between documentation files
- Restructuring a repo's documentation architecture
- Reviewing documentation changes for completeness
