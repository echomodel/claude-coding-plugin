---
name: setup-agent-context
description: "Configure coding agent context for a repo by setting up CLAUDE.md, .gemini/settings.json, and .gitignore rules. Use when starting a new project, onboarding a repo for AI-assisted development, or when asked to set up agent context, configure Claude/Gemini for a repo, or make a repo AI-ready."
---

Set up the standard agent context files so that Claude Code and Gemini CLI
both automatically load the repo's README.md and CONTRIBUTING.md as context.

## What this skill creates/updates

1. **`CLAUDE.md`** (repo root) — a short pointer file
2. **`.gemini/settings.json`** (repo root) — context file declarations
3. **`.gitignore`** — exclude `.gemini/` but include `!.gemini/settings.json`

## Step 1: Read existing files

Before making changes, read these files if they exist:
- `CLAUDE.md`
- `.gemini/settings.json`
- `.gitignore`
- `README.md` (to confirm it exists)
- `CONTRIBUTING.md` (to confirm it exists)

If README.md or CONTRIBUTING.md don't exist, tell the user and ask whether
to proceed anyway or create them first.

## Step 2: Create or update CLAUDE.md

The file should use Claude Code's `@path` import syntax to pull README.md
and CONTRIBUTING.md into context at session start. Do not put project-specific
instructions here — those belong in CONTRIBUTING.md. The CLAUDE.md content
should be:

```markdown
@README.md
@CONTRIBUTING.md
```

If additional lines already exist in CLAUDE.md (e.g., PII warnings for
public repos), preserve them. Only add the `@` imports if missing.

### What belongs where

CLAUDE.md tells agents where to look. The actual content lives in:

- **README.md** — what the project is, how to install and use it
- **CONTRIBUTING.md** — architecture, design principles, constraints, testing
  conventions, SDK structure, how to add features

This separation means both Claude Code and Gemini CLI get identical context
from the same source files, with no duplication.

## Step 3: Create or update .gemini/settings.json

```json
{
  "context": {
    "fileName": [
      "README.md",
      "CONTRIBUTING.md"
    ]
  }
}
```

If the file already exists, merge the context entries — don't overwrite
other settings that may be present.

## Step 4: Update .gitignore

Ensure these entries exist in `.gitignore`:

```
.gemini/
!.gemini/settings.json
```

The `.gemini/` exclusion prevents committing local Gemini state files.
The `!.gemini/settings.json` exception ensures the context configuration
IS committed so all contributors and agents benefit from it.

## Step 5: Security scan before committing

Before staging `.gemini/settings.json` for commit, verify it contains no
sensitive content: no absolute paths with usernames, no API keys, no
credentials, no user-specific identifiers. The file should contain ONLY
the `context.fileName` array pointing to standard repo files.

## Step 6: Report

Tell the user what was created or updated. Mention that both Claude Code
and Gemini CLI will now load README.md and CONTRIBUTING.md as context, and
that project-specific instructions belong in CONTRIBUTING.md.
