---
name: capture-context
description: >-
  Capture all valuable session context before ending a conversation. Use when
  the user wants to quit, wrap up, save progress, or ensure nothing is lost
  from the current session. Also use when the user says "capture context",
  "save session", "wrap up", or "I need to go".
disable-model-invocation: true
---

# Capture Session Context

Guide the user to a safe stopping point where nothing valuable from the current
session is lost. All undone work, decisions, designs, research findings, and
plans must be fully captured in durable, discoverable artifacts before the
session ends.

## Phase 1: Audit

Review the ENTIRE conversation history — every message, tool call, plan,
decision, suggestion, research result, and user request. Then present two
bulleted lists:

### Fully Captured

Items where ALL of the following are true:
- The work is complete in code, configuration, or documentation AND
  committed/pushed, OR
- Every detail needed to resume the work is already recorded in a durable,
  discoverable location (GitHub issue, versioned file, established tracking
  system) — cite the specific location for each item

For each item, state what it is and where it is captured.

### Not Yet Captured

Items where ANY of the following are true:
- Work was discussed, planned, or designed but not implemented and not tracked
- Decisions were reached but not recorded anywhere persistent
- Research was done whose conclusions exist only in conversation context
- A plan or design was agreed upon but not written down outside this session
- A tracking item exists but is missing important details, context, or
  decisions from this session
- Partial work was done but the remaining steps are not documented

For each item, state what is missing and why it matters.

### Suggested session name

After presenting both lists, suggest a short, descriptive name for this session
(e.g., "capture-context-skill-creation", "auth-middleware-refactor"). This
helps the user label or rename the session for future reference before exiting.
If the agent tool supports naming or renaming sessions, include the command.

This is especially useful when List 2 is empty or the proposed actions are
minor — the user may decide the session is safe to exit right here without
waiting for further phases. A good session name makes it findable later.

## Phase 2: Where to Store

For each gap in List 2, choose a capture destination. Present the proposed
destination for each item and ask the user for permission before executing.

### Prefer quick actions over tracking items

If a gap can be closed faster and more reliably by just doing the work right
now, suggest that instead of creating a tracking item. Doing the work eliminates
the risk it gets forgotten. Examples:

- Tests pass and code works but nothing is committed → suggest commit + push
- A config change was made locally but not pushed → suggest push
- A file was created but not added to version control → suggest git add + commit

Present the quick-action option clearly. If the user prefers to just be done
and not do more work in this session, respect that and fall back to capturing
what remains.

### Capture destinations

Not everything belongs in a GitHub issue. Consider these options:

#### 1. Do the work now

If it is quick and safe, just finish it. See examples above.

#### 2. The tracking system already in use this session

If the agent or user has been using a specific tool or file to track TODOs
during this session (a TODOS.md, a task tracker, a personal notes repo, etc.),
propose continuing to use it. Consistency matters more than format.

#### 3. A known personal notes or planning location

If the agent is aware (from memory, context files, or the conversation) that
the user keeps project-related notes, plans, or TODOs in a specific place —
especially a private personal repo — propose saving there. This is often the
safest and most flexible option because personal context, local details, and
unpolished thinking can be captured freely.

#### 4. A workspace TODOS.md file

Create or append to a `TODOS.md` (or `temp/TODOS.md`) in the current workspace
directory. This works well when:
- The repo is private and personal context is acceptable
- The content includes user-specific details, local paths, or unpolished
  reasoning that should not be in a public GitHub issue
- Speed and completeness matter more than presentation

When using a workspace TODOS file:
- If the repo is public or the user prefers to keep tracking artifacts out of
  version history, use `temp/TODOS.md` and ensure `temp/` is listed in
  `.gitignore`
- Link to the TODOS file from the project's agent context file (`CLAUDE.md`,
  `.gemini/settings.json` instructions, or equivalent) so that future agents
  discover it immediately
- If no agent context file exists yet, create one that directs the agent to
  check the TODOS file and alert the user to pending items at the start of
  the next session

#### 5. GitHub issues

Best for well-scoped engineering work on repos with a GitHub remote —
especially public repos or repos with collaborators. When creating or updating
issues, invoke the `author-github-issue` skill and follow its conventions
(temp file + `--body-file`, content rules). Each issue must be self-contained:
a future contributor with no session context should understand the full scope,
decisions, reasoning, and remaining work.

#### 6. Versioned `.md` files in the repo

Only when the content is polished, complete, and appropriate for the repo's
audience — never raw brainstorming or incomplete thoughts.

### Session resume information

When writing to non-public locations (private repos, gitignored files, personal
notes), include a way to resume this agent session if the tool supports it.
This might be a session ID, a session name, or a resume command — whatever the
current agent tool provides. For example:

```
## Resume session
cd ~/projects/my-app && <agent-tool> --resume <session-id>
```

Discovering the session identifier is agent-tool-specific. Use available
skills (e.g., a sessions skill), built-in commands, or ask the user to name
the session if no programmatic method is available. If the session ID cannot
be determined, note that in the artifact and suggest the user add it manually
before closing the session.

**Only include session resume info in private locations** — never in GitHub
issues, public docs, or any artifact that may be visible to others.

### Safety requirements for all destinations

Whatever destination is chosen, it must be:

- **Durable** — not in `/tmp/` or other ephemeral locations that disappear
  on reboot
- **Discoverable** — a future session (human or agent) can find it without
  remembering this conversation. Either it is in a well-known location, or
  a pointer to it exists in an agent context file or established workflow.
- **Version-controlled or backed up** — unless the user explicitly accepts
  the risk of a local-only file

If a proposed destination does not meet these criteria, flag the risk to the
user and suggest a safer alternative.

## Phase 3: Sensitive Content Rules for Public Destinations

These rules apply to GitHub issues (titles, bodies, comments), versioned files
(code, config, `.md`, any file tracked by git), commit messages, and any other
content that is or may become public. Anything that enters git commit history
or a GitHub issue is effectively permanent and potentially public, even on
private repos (collaborators, future open-sourcing, forks).

**Private tracking locations are exempt** — gitignored files (`temp/TODOS.md`),
personal private repos (especially those with a `personal-` prefix), and
personal notes systems. Capture freely there, including local paths, personal
use cases, session IDs, and unpolished reasoning. The goal in private locations
is completeness, not presentation.

### What must NEVER appear in public-facing artifacts

The following must never appear in any versioned file, commit message, or
GitHub issue — on public repos or private repos without a `personal-` prefix:

| Category | Examples |
|----------|----------|
| **PII** | Real names, email addresses, phone numbers, physical addresses |
| **Usernames** | OS login names, GitHub usernames, `$USER` values |
| **Credentials** | API keys, tokens, secrets, passwords, OAuth tokens, private keys |
| **Cloud/service IDs** | GCP project IDs, Google Doc/Sheet/Drive IDs, client IDs, service account emails |
| **Financial data** | Real income/tax amounts, bank account numbers, credit card numbers |
| **Tax identifiers** | SSNs, EINs |
| **Workspace paths** | Absolute paths containing usernames (`/home/user/...`), workstation-specific workspace roots. Use generic placeholders: `~/projects/my-app`, "project root", "workspace directory" |
| **Personal context** | The user's employer, personal banks, properties, personal use cases that motivated the work. Describe needs from the repo's perspective, not the user's workflow |
| **High-entropy strings** | Tokens, hashes, or encoded values that may be secrets — if in doubt, leave it out |

**Use placeholders instead:** `your-project-id`, `user@example.com`,
`YOUR_USERNAME`, `~/projects/my-app`.

**Write in abstract, reusable terms.** A GitHub issue should read as if any
contributor wrote it. Instead of "I need this for my deployment", write
"deployments with auth enabled need...".

### When in doubt

If you are unsure whether content is safe for a given destination, choose a
more private destination. A raw but complete TODOS.md in a gitignored folder
is better than a sanitized GitHub issue that lost critical context in the
cleaning process.

## Phase 4: Execute

Carry out the approved actions.

When creating GitHub issues, follow the `author-github-issue` skill for
workflow and content rules. Additional guidance:

- Each issue must be self-contained and actionable by someone with no knowledge
  of this session
- Include relevant technical detail — architecture decisions, rejected
  alternatives and why, dependencies, acceptance criteria
- Prefer fewer well-structured issues over many tiny ones, but split genuinely
  independent work items into separate issues
- Update issue bodies (not comments) when adding scope or context to existing
  issues

When creating or updating TODOS files or personal tracking artifacts, capture
context liberally — the goal is completeness, not polish. Include decision
rationale, rejected alternatives, session-specific observations, and anything
that would help the user (or an agent) resume without loss.

## Phase 5: Re-audit (mandatory loop)

After completing Phase 4, return to Phase 1 and repeat the full audit from
scratch. Review the entire conversation again, including the capture work just
performed. Present updated Fully Captured and Not Yet Captured lists.

If anything remains in Not Yet Captured, repeat Phases 2–5.

Continue looping until Not Yet Captured is completely empty — every item of
value from the session is verified as captured. Only then report that the
session is safe to exit.

**Do not skip this loop.** The first pass routinely misses items. Common things
missed on first pass:
- Decisions about what NOT to do (and why)
- Alternative approaches that were considered and rejected
- Dependencies or prerequisites discovered during research
- Edge cases or failure modes discussed
- Follow-up work that was mentioned in passing
- Context that makes a tracking item actionable vs. just a title

## General Rules

- **Be thorough, not verbose.** Capture detail that would be lost, not detail
  that is obvious from the code.
- **Every tracking item must be actionable.** A future agent or developer
  should be able to pick it up and execute without guessing.
- **Verify capture.** After creating or updating any artifact, read it back
  to confirm the content is complete and correct.
- **Respect the user's desire to stop.** If the user wants to be done, do not
  push for more work — fall back to the fastest safe capture method available.
