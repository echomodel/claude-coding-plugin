# Privacy Guard Output Schema (Current)

This documents the structured JSON output as currently defined in
`agents/privacy-guard.md`. The agent emits this as a fenced code block
tagged `privacy-guard-result` at the end of every run.

## Top-level fields

```json
{
  "status": "completed | failed | partial",
  "failure_reason": "person_md_not_found | skill_not_loaded | not_a_git_repo | null",
  "repo": "repo-name or null",
  "visibility": "public | private | unknown",
  "tier": "strict | relaxed",
  "configured_categories": ["github", "emails", "names", "..."],
  "unconfigured_categories": ["cloud_ids", "..."],
  "os_discovered": {
    "username": "...",
    "home": "...",
    "workspace_root": "..."
  },
  "scan_scope": {
    "files_scanned": 0,
    "staged_files": 0,
    "commits_scanned": 0,
    "issues_checked": 0,
    "prs_checked": 0,
    "full_history": false,
    "private_repos_checked": true
  },
  "findings": [],
  "author_check": {},
  "hooks": {},
  "warnings": [],
  "summary": ""
}
```

## Finding schema

```json
{
  "category": "emails | names | github | domains | employers | financial_providers | properties | cities | os_system | phone | employer_terms | private_repo_ref | contextual | author_mismatch | ...",
  "source": "person_md_frontmatter | person_md_body | prompt | builtin_pattern | os_runtime | contextual_judgment",
  "matched_value": "actual matched text",
  "location_type": "file_content | commit_message | commit_author | issue | pr | branch_name | tag_name | gitignored_file | stash | reflog | ...",
  "location": "path/to/file:line or commit:sha or issue:#N or branch:name",
  "severity": "high | medium | low | warning | info",
  "note": "optional context"
}
```

## Author check

```json
{
  "configured_name": "...",
  "configured_email": "...",
  "all_commit_authors": [{"name": "...", "email": "..."}],
  "mismatched_authors": [{"name": "...", "email": "...", "expected_domain": "...", "actual_domain": "..."}]
}
```

## Hooks

```json
{
  "global_configured": true,
  "repo_inherits_global": true,
  "local_override": "null or path",
  "precommit_ran": true,
  "precommit_result": "pass | fail | skipped | unavailable"
}
```

## Design notes

- `findings` is always an array, even if empty
- `category` and `location_type` use suggested values but are open
  strings — the agent can report findings that don't fit predefined
  categories
- `source` indicates where the agent learned the matched value was
  sensitive — never the actual PERSON.md pattern value
- `warnings` captures non-finding observations (unconfigured
  categories, skipped scopes, permission issues)
- The schema is intentionally open — extra fields are allowed

## Containment rules

- Findings include `matched_value` (the parent needs it to act)
- Scan targets from PERSON.md never appear in output — only category
  names and counts
- See [CONTRIBUTING.md](../../../CONTRIBUTING.md) "Subagent
  containment principle" for the full model
