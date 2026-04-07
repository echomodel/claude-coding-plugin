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
