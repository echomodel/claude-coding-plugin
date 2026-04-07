---
name: code-reuse
description: "Use when the user wants to, or there's an opportunity to, consolidate, deduplicate, or share code patterns across multiple repos. Triggers on: making code reusable, sharing logic between projects, extracting common utilities, reducing duplication across repos. This skill determines whether to use managed snippet copies or a shared library, and guides placement."
---

# Code Reuse Across Repos

## Decision Tree

When you encounter similar logic across multiple repos, work through these
questions in order:

### 1. Is consolidation actually worth it?

NOT every similarity warrants consolidation. Consolidate when:
- The logic solves the **same problem** and differences are arbitrary
  (e.g., developed at separate times, not intentionally different)
- A single implementation could serve 2+ cases, even if surrounding
  code needs tweaking
- Divergence would cause bugs or confuse contributors

Do NOT consolidate when:
- Implementations look similar but serve **genuinely different domains**
  with different requirements that will diverge further over time
- The "shared" part is trivial (a few lines) and coupling repos
  would cost more than the duplication

### 2. Snippet or library?

**Snippet** (managed copies): A reusable function or two, totaling
<50 or maybe sometimes up to ~100 lines. Too small for the overhead
of a shared package (dependency management, versioning, releases).

**Library** (shared package): Larger than ~100 lines, or multiple
functions with interdependencies, or code with shared types/contracts
that benefit from being co-located.

### 3. Does an existing library already cover this?

Before creating a new snippet or library, check whether the logic
naturally belongs in an existing package in the user's workspace.
If so, add it there rather than creating something new.

## Snippet Pattern

For code that fits the snippet criteria, each snippet is managed as
its own skill containing the canonical implementation.

### Required Comment Block

Every snippet placement MUST include a header comment identifying the
source skill and version (adapted to the target language's comment syntax):

```python
# --- Reusable Snippet: retry-with-backoff v1 ---
# Managed by skill: retry-with-backoff
# Keep consistent with the latest version of this snippet.
# Do not modify without updating the skill definition.
# ------------------------------------------------

def retry_with_backoff(fn, max_retries=3):
    ...
```

### Creating a New Snippet Skill

1. Create the skill locally: `~/.claude/skills/<snippet-name>/SKILL.md`
   (NOT under a collection subdirectory — that structure is only for
   marketplace repos, not local installs)
2. Include proper frontmatter:
   ```yaml
   ---
   name: <snippet-name>
   description: "Short description of what the snippet does and when to use it."
   metadata:
     version: "1"
   ---
   ```
3. Include the canonical implementation with the comment block
4. Document: inputs, outputs, assumptions, version
5. **NEVER reference specific consuming repos or projects in the skill.**
   Usage examples must be generic (e.g., `from my_app.sdk.common...`).
   The skill is reusable — it must not contain references that tie it
   to any particular codebase.

### Reviewing Snippet Consistency

When you encounter code with a snippet comment block:
1. Load the referenced skill by name
2. Compare the placed code against the canonical version
3. If it differs, flag it and offer to update
4. If the local version has improvements, propose updating the skill

## Knowing When to Graduate

Watch for **critical mass** — signs that scattered snippets should
become a shared library:

- **3+ snippets** that operate on the same domain (e.g., config loading,
  config merging, config discovery are all "config management")
- **Snippets calling each other** — if you copy two snippets together
  into every repo because one depends on the other, that's a library
- **Shared types or contracts** — snippets that expect the same data shapes
  suggest a cohesive module
- **Growing combinatorial value** — the snippets are more useful together
  than in isolation

When you observe this, **suggest graduating to a library**. Point to any
existing library in the user's workspace that the snippet naturally belongs
to. A snippet that fits an existing library should go there, not remain a
snippet.

Conversely, **don't create a library preemptively**. One or two unrelated
snippets is not critical mass.
