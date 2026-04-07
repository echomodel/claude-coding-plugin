---
name: check-feature-support
description: >-
  Verify whether a feature, syntax, or convention used in code or config is
  actually supported by the relevant standard and product. Use when assuming
  a frontmatter field works, a CLI flag exists, a config key is honored, or
  any capability that depends on external support. Triggers on: "does this
  actually work?", "is this supported?", "will Claude Code / Gemini honor
  this?", "is this in the spec?", "are we assuming something that isn't real?"
allowed-tools: Agent WebSearch WebFetch Read Grep Glob
---

# Check Feature Support

When invoked, the user or agent is saying: "We're about to build on an
assumption that a feature exists and works. Verify it before we commit."

## What this skill does

Launch a sub-agent to check the feature from both angles:

### 1. Standards check

Research whether the feature is defined in a governing open standard.

- **agentskills.io** — the skill definition standard. Check for frontmatter
  fields, naming conventions, directory structure requirements.
- **MCP specification** — for tool definitions, server config, transport.
- **Other relevant specs** — JSON Schema, YAML spec, OpenAPI, etc.

The agent should:
1. Identify which standard governs the feature
2. Fetch or search the standard's documentation
3. Report whether the feature is: **specified**, **unspecified but allowed**
   (extension point), or **contradicts the spec**
4. Quote the relevant section if found

### 2. Product support check

Research whether the products that need to support (or at least ignore)
the feature actually do.

- **Claude Code** — check docs at code.claude.com, the anthropics/claude-code
  repo, and web sources for whether the feature is implemented
- **Gemini CLI** — check docs, the google-gemini/gemini-cli repo, and web
  sources
- **Other relevant products** — if the feature spans tools (e.g., a YAML
  frontmatter field that multiple consumers parse)

The agent should:
1. Check official documentation first
2. Search for usage examples, issues, or discussions
3. Report per product: **supported**, **ignored** (safe to use, won't break
   anything), **unsupported** (will cause errors), or **unknown**
4. If unknown, note what was searched and not found

## How to present results

Combine both agents' findings into a clear verdict:

```
Feature: `skills:` list in agent frontmatter
Standard: agentskills.io — not specified (extension field)
Claude Code: supported — preloads listed skills into agent context
Gemini CLI: ignored — parses frontmatter but skips unknown fields
Verdict: SAFE TO USE — standard allows extensions, both products handle it
```

Or:

```
Feature: `allowed-tools` restricting tool access in skills
Standard: agentskills.io — not specified
Claude Code: PARTIALLY SUPPORTED — pre-approves tools but does NOT restrict
Gemini CLI: unsupported — ignores the field entirely
Verdict: WORKS DIFFERENTLY THAN ASSUMED — does not restrict, only pre-approves
```

## When to use this

- Before building on an assumed capability (e.g., "skills can restrict tools")
- When a feature works locally but needs to work across platforms
- When using non-standard extensions to a spec (custom frontmatter fields)
- When the agent or user says "I think this works but I'm not sure"
- When validating features referenced in build output or test assertions

## What this skill is NOT

- Not a general research tool — it answers "does X work in Y?" not "what
  should I use for Z?"
- Not a substitute for testing — it checks documentation and standards, not
  runtime behavior. If the docs say it works but it doesn't, that's a bug
  to report, not a skill failure.
- Not exhaustive by default — it checks the most likely standard and the
  primary products. If the user needs broader coverage, they should specify
  which products or standards to check.

## Handling ambiguity

If the feature is undocumented in both the standard and the product:

1. Search for GitHub issues or discussions about it
2. Search for usage in public repos (especially official examples)
3. If still unknown, report honestly: "Cannot confirm support. Recommend
   testing before building on this assumption."

Do not guess. Do not infer support from the absence of errors. Absence of
documentation is not evidence of support.
