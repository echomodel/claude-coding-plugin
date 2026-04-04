# Privacy Guard Output Schema — Proposed Redesign

This documents proposed changes to the structured JSON output.
The current schema is in [SCHEMA.md](SCHEMA.md).

## Motivation

Three drivers for the redesign:

1. **Attribution** — tests need to assert on *why* the agent flagged
   something, not just *what*. The current `source` field is a start
   but the rules/results relationship isn't formalized. (Issue #2)

2. **Scan metadata** — the output should report what was checked (by
   category, count, and source) without revealing actual values, so
   tests can verify the agent used the right inputs. (Issue #2,
   CONTRIBUTING.md containment principle)

3. **Scope narrowing** — the agent currently scans GitHub issues and
   PRs. This should be removed. The agent's core question is "can I
   commit and push safely right now?" — that's a local question.
   Remote content scanning is a separate concern with different
   performance and relevance characteristics.

## SARIF analysis

[SARIF](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)
(Static Analysis Results Interchange Format) is the OASIS standard for
scanner output. It's consumed by GitHub Code Scanning, Azure DevOps,
and major security tools (CodeQL, Semgrep, Trivy, Checkov).

SARIF's core model separates **rules** (what was checked) from
**results** (what was found), with results referencing rules by ID.
This is the same pattern we need.

### What we take from SARIF

| SARIF concept | How we use it |
|---------------|---------------|
| `tool.driver.rules[]` with `id` | Top-level rules array. Each rule has `id`, `category`, `source`, `count`. |
| `ruleId` on results | String foreign key on findings, referencing a rule. Format: `"category:source"` (e.g., `"emails:person_md_frontmatter"`). |
| `version` field | Schema versioning so consumers know which shape to expect. |
| `physicalLocation` (file + line) | Our file-based findings map directly. |
| `logicalLocation` with open `kind` | Non-file findings (commit messages, branch names) use `kind` as the location type. |
| `properties` bag | Extensibility for tool-specific metadata. |

### What we don't take from SARIF

| SARIF concept | Why not |
|---------------|---------|
| Full SARIF envelope (`runs[]`, `invocations[]`, nested structure) | Too deep for test assertions. Our output isn't consumed by SARIF tooling today. |
| `physicalLocation.artifactLocation.uri` + `region.startLine` nesting | We use flat `location` + `location_type`. Direct field access matters for test readability. |
| `matched_value` in `properties` bag | Too important for tests to bury one level deep. Stays as a top-level finding field. |
| `level` instead of `severity` | SARIF's `error`/`warning`/`note`/`none` is coarser than our `high`/`medium`/`low`/`warning`/`info`. |
| SARIF as the output format | No current consumer needs SARIF. If GitHub Code Scanning integration is wanted later, write a transformer at that point. |

### Gap analysis

With issues/PRs removed from scope, almost all findings map to
SARIF concepts:

**Native SARIF fit (file + line):**
- Working tree files
- Staged files
- HEAD files
- Historical commit diffs (file content at a prior commit)
- Gitignored files

These all have a file path and line number. The git state (working
tree, staged, historical commit) is metadata on the finding, not a
different location type.

**Requires `logicalLocation` with custom `kind`:**
- Commit message text (`kind: "commit_message"`)
- Branch names (`kind: "branch_name"`)
- Tag names (`kind: "tag_name"`)
- Stash descriptions (`kind: "stash_entry"`)

Valid SARIF but standard viewers won't render them inline. These are
a small percentage of findings.

**No SARIF equivalent — our domain entirely:**
- `status` / `failure_reason` (richer than SARIF's boolean)
- `scan_scope` (git-specific: commits, staged files)
- `author_check` (git author identity analysis)
- `hooks` (pre-commit hook status)
- Rules with `source` and `count` (multi-source provenance)

> **Remove this section** once the schema redesign is complete and
> the gap analysis is no longer needed for decision-making.

## Proposed schema

### Top level

```json
{
  "version": "2.0",
  "status": "completed | failed | partial",
  "failure_reason": "person_md_not_found | skill_not_loaded | not_a_git_repo | null",
  "repo": "repo-name or null",
  "visibility": "public | private | unknown",
  "tier": "strict | relaxed",
  "tool": {
    "name": "privacy-guard",
    "rules": []
  },
  "scan_scope": {},
  "findings": [],
  "author_check": {},
  "hooks": {},
  "warnings": [],
  "summary": ""
}
```

### Rules

Rules describe what the agent checked for — categories, how many
values, and where those values came from. **Never the values
themselves** (containment principle).

A category can have rules from multiple sources:

```json
"rules": [
  {
    "id": "emails:person_md_frontmatter",
    "category": "emails",
    "source": "person_md_frontmatter",
    "count": 3
  },
  {
    "id": "names:person_md_frontmatter",
    "category": "names",
    "source": "person_md_frontmatter",
    "count": 3
  },
  {
    "id": "names:person_md_body",
    "category": "names",
    "source": "person_md_body",
    "count": 2
  },
  {
    "id": "names:prompt",
    "category": "names",
    "source": "prompt",
    "count": 1
  },
  {
    "id": "credentials:builtin_pattern",
    "category": "credentials",
    "source": "builtin_pattern",
    "count": 0
  },
  {
    "id": "os_system:os_runtime",
    "category": "os_system",
    "source": "os_runtime",
    "count": 2
  }
]
```

The `id` is `category:source` — deterministic, greppable, serves as
the foreign key from findings.

Source values:
- `person_md_frontmatter` — YAML `patterns:` block
- `person_md_body` — extracted from prose below frontmatter
- `prompt` — provided by user or parent agent in scan prompt
- `builtin_pattern` — agent's own knowledge (credential formats, structural IDs)
- `os_runtime` — discovered from `$USER`, `$HOME`
- `contextual_judgment` — agent judgment, no specific configured value

### Findings

```json
"findings": [
  {
    "ruleId": "emails:person_md_frontmatter",
    "matched_value": "user@example.com",
    "location": "src/config.py:42",
    "location_type": "file_content",
    "severity": "high",
    "note": "optional context"
  }
]
```

`location` and `location_type` vary by finding type:

**File-based findings** (working tree, staged, HEAD, historical, gitignored):

```json
{
  "ruleId": "emails:person_md_frontmatter",
  "matched_value": "user@example.com",
  "location": "src/config.py:42",
  "location_type": "file_content",
  "severity": "high"
}
```

Historical commit diff — same shape, with `commit` field:

```json
{
  "ruleId": "emails:person_md_frontmatter",
  "matched_value": "user@example.com",
  "location": "src/config.yaml:3",
  "location_type": "commit_diff",
  "commit": "a1b2c3d",
  "severity": "high",
  "note": "Removed from HEAD but present in history"
}
```

Gitignored file:

```json
{
  "ruleId": "credentials:builtin_pattern",
  "matched_value": "ghp_abc123...",
  "location": "secrets/keys.txt:1",
  "location_type": "gitignored_file",
  "severity": "warning"
}
```

**Non-file findings** (commit messages, branch names, stash):

```json
{
  "ruleId": "names:person_md_frontmatter",
  "matched_value": "Zanzibar Quuxington",
  "location": "commit:a1b2c3d",
  "location_type": "commit_message",
  "severity": "high",
  "note": "Name in commit subject line"
}
```

```json
{
  "ruleId": "names:person_md_frontmatter",
  "matched_value": "zanzibar",
  "location": "branch:feature/zanzibar-fix",
  "location_type": "branch_name",
  "severity": "medium"
}
```

### Scan scope (revised)

With issues/PRs removed:

```json
"scan_scope": {
  "working_tree_files": 42,
  "staged_files": 3,
  "commits_scanned": 5,
  "full_history": false,
  "stash_entries": 0,
  "branches_checked": 1,
  "tags_checked": 0
}
```

### Test ergonomics

The schema is designed for direct field access in assertions:

```python
# Find all commit message findings
msg = [f for f in result["findings"] if f["location_type"] == "commit_message"]

# Assert on matched value
assert any("Zanzibar" in f["matched_value"] for f in msg)

# Assert on attribution — the agent found this via frontmatter, not builtin
assert msg[0]["ruleId"] == "names:person_md_frontmatter"

# Look up the rule to verify source and count
rule = next(r for r in result["tool"]["rules"] if r["id"] == msg[0]["ruleId"])
assert rule["source"] == "person_md_frontmatter"
assert rule["count"] > 0
```

No `properties` bags, no nested `physicalLocation` drilling, no
string parsing beyond the `ruleId` format which is `category:source`.

## Changes from current schema

| Current | Proposed | Reason |
|---------|----------|--------|
| `category` + `source` on finding | `ruleId` string (e.g., `"emails:person_md_frontmatter"`) | SARIF-inspired foreign key. Flat, greppable, one field instead of two. |
| `configured_categories` / `unconfigured_categories` / `os_discovered` | `tool.rules[]` with `category`, `source`, `count` | Unified. One array replaces three fields. Counts without values (containment). |
| Issues/PRs in scan scope | Removed | Local-only scope. Different concern. |
| `location_type: "issue"` / `"pr"` | Removed | Follows scope change. |
| No schema version | `version: "2.0"` | Consumers need to know which shape. |
| Flat `source` on finding | Encoded in `ruleId`, detailed in `tool.rules[]` | Attribution lives on the rule, finding references it. |

## Open questions

- Should `category` remain as a convenience field on findings
  alongside `ruleId`? It avoids parsing the string or looking up the
  rule for simple category-based filtering.
- Should there be a SARIF export option (transformer that converts
  this output to SARIF for GitHub Code Scanning) tracked as a
  separate issue?
- How should the parent-facing skill (agent interface documentation
  for callers) be structured? See discussion in issue #3.

## Related issues

- #2 — Agent should own PII categories and reason from any input
- #3 — Update validate-privacy-guard skill: log review as verification
