---
name: safe-commit
description: >-
  Stage, review, scan, commit, and optionally push changes safely. Use
  EVERY TIME the user says "commit", "git commit", "push", "git push",
  "stage and commit", "commit this", "commit all", "commit and push",
  "safe commit", "ready to commit", "let's commit", or any variation
  of committing or pushing code. Also use when you (the agent) decide
  to commit on the user's behalf after completing a task.
user-invocable: true
argument-hint: "[commit message]"
---

# Safe Commit

Commit first, scan after, push only if clean. The commit happens
BEFORE the privacy scan because the scan needs to see the final commit
content including the commit message.

## Step 1: Check for gitignored violations

```bash
git status
```

Review the output. Are there files that SHOULD be gitignored but aren't?
Look for:
- `.env`, `credentials.json`, `secrets/`, `*.pem`, `*.key`
- `node_modules/`, `__pycache__/`, `.venv/`, `venv/`
- IDE files: `.idea/`, `.vscode/settings.json` (local, not shared)
- OS files: `.DS_Store`, `Thumbs.db`

If any should be gitignored, ask the user. Add them to `.gitignore`
and re-run `git status`. Repeat until clean.

## Step 2: Stage files individually

Do NOT use `git add .` — stage files by name:

```bash
git add <file1> <file2> ...
```

Stage only the files the user intends to commit. If unsure, ask.

Run `git status` again to confirm:
- Everything intended is staged
- Nothing unintended is staged
- No untracked files that should be staged or gitignored

If untracked files remain that aren't gitignored, ask the user: stage
them, gitignore them, or leave them (the scan will flag them).

## Step 3: Review staged diff

```bash
git diff --staged
```

Read the full diff. Check for:
- Secrets, credentials, API keys, tokens
- Personal information (names, emails, paths, employer references)
- Unintended changes mixed in
- Debug code, TODO comments with personal context

If anything looks wrong, stop and ask the user.

## Step 4: Confirm git hooks are active

```bash
git config core.hooksPath
```

If this returns a path (not empty), hooks are active and will scan on
commit. If empty or `/dev/null`, warn the user that no precommit
scanner will run — the commit proceeds without deterministic scanning.

## Step 5: Commit

Draft a commit message if the user didn't provide one:
- Summarize the nature of the changes (new feature, bug fix, refactor)
- Focus on the "why" not the "what"
- Keep it concise (1-2 sentences)

```bash
git commit -m "<message>"
```

If the precommit hook fails, review the findings. Fix issues and
retry. Do NOT use `--no-verify` unless the user explicitly approves.

## Step 6: Verify clean state

```bash
git status
```

Confirm:
- Working tree is clean (nothing dirty, nothing untracked that matters)
- Only unpushed commit(s) remain

If anything is dirty or untracked, go back to Step 1.

## Step 7: Run privacy-guard agent

Invoke the privacy-guard agent with EXACTLY this prompt and nothing
else:

```
scan this repo
```

Do NOT add instructions about what to scan, how to scan, what to look
for, or any other context. The agent has its own instructions. Adding
to the prompt risks overriding the agent's behavior and will cause
the scan verification to fail.

## Step 8: Interpret scan results

Parse the `privacy-guard-result` JSON from the agent's output.

The scan result is binary:

| Condition | Result | Action |
|-----------|--------|--------|
| `status: completed`, `findings` empty | **pass** | Offer push |
| `status: completed`, `findings` non-empty | **fail** | Show findings, no push, user must fix and recommit |
| `status: failed` | **fail** | Show error, no push |

No discretion. No partial. The content at this SHA either passes or
it doesn't. If there are findings, the user fixes them, amends or
creates a new commit (new SHA), and runs the flow again from Step 1.

## Step 9: Advise and offer push

**Pass:** Tell the user the scan passed. Ask if they want to push.

**Fail:** Show every finding. Tell the user what needs to be fixed.
Do NOT offer to push.

If the user believes a finding is a false positive, try workarounds
to avoid tripping it (reword, restructure, use placeholders). If no
workaround is possible, the user will need to obtain and install a
new release of the privacy-guard agent or the plugin and restart the
session.

## Step 10: Push (if approved)

Capture HEAD SHA and push that exact commit:

```bash
sha=$(git rev-parse HEAD)
git push origin $sha:refs/heads/$(git symbolic-ref --short HEAD)
```

Push the SHA, not HEAD — this prevents TOCTOU issues where HEAD moves
between the scan and the push.

## When privacy-guard is not available

If the privacy-guard agent is not installed or fails to run, tell the
user. No scan means no push. There is no fallback. Install the agent
and retry.

## When privacy-guard fails with "person_md_not_found"

The privacy-guard agent requires `~/.config/ai-common/PERSON.md` to
load personal patterns. This file lives outside any project directory,
so sandbox restrictions may block access.

**If running as a subagent (Step 7):** The subagent inherits the
parent session's working directory permissions. If the parent session
was started from a project directory, the
subagent cannot read `~/.config/`. Tell the user to run the scan
from the terminal instead:

```bash
cd <repo-path> && claude --agent privacy-guard --add-dir ~/.config/ai-common -p "scan this repo"
```

**If running from the terminal:** Use `--add-dir` to grant access:

```bash
claude --agent privacy-guard --add-dir ~/.config/ai-common -p "scan this repo"
```

The `--add-dir` flag grants the agent read access to the specified
directory for that session only. The prompt must still be exactly
"scan this repo" — do not modify it.

## Post-push rescan

If commits were pushed without a scan — because the push happened in
an environment without scanning enabled, a newer agent version needs
to re-evaluate previously pushed content, or a push slipped through
due to permission or tooling gaps — use this workflow to retroactively
scan what was pushed.

### Setup

Create a temporary branch at the pre-push baseline, push it to
establish a remote tracking point, then merge main so the pushed
commits appear as "unpushed" relative to the branch's remote:

```bash
# Find the last commit that was on remote before the unscanned push
git log --oneline -10   # identify the baseline commit

# Create and push baseline branch
git checkout -b rescan-basis <baseline-sha>
git push -u origin rescan-basis

# Merge main — the pushed commits are now "unpushed" on this branch
git merge main
```

### Run the scan

The scan must be run by the user from a shell, not from within an
existing agent session (subprocesses may lack file permissions):

```bash
claude --agent privacy-guard --add-dir ~/.config/ai-common -p "scan this repo"
```

If the repo being scanned is different from the current working
directory, `cd` to it first. The `--add-dir ~/.config/ai-common`
grants access to PERSON.md (required for scanning). The prompt must
always be exactly "scan this repo" without modifications.

### Interpret and clean up

If the scan passes, clean up:

```bash
git checkout main
git branch -D rescan-basis
git push origin --delete rescan-basis
```

If the scan finds issues, the content is already pushed. Fix the
findings in a new commit on main, then push the fix. The rescan
branch can be deleted either way — it was only scaffolding to make
the already-pushed commits visible to the scanner.
