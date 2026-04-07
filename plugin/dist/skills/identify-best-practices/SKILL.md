---
name: identify-best-practices
description: Identify and compare against industry best practices for an approach, design, architecture, or workflow. Use when the user asks "am I doing this right?", "am I thinking about this right?", "how do others solve this?", "what are others doing?", "what am I missing?", "is there a better way to do this?", "are there known pitfalls with my approach?", "am I reinventing the wheel?", "is there an established library, framework, tool, standard, pattern, or even a term for this that I should know about?", or wants to sanity-check or pressure-test their approach.
metadata:
  version: "1.0.0"
---

# Identify Best Practices

When the user invokes this skill, they are saying: "I have an approach to a problem. I want to know how it holds up against what the best people in this space are actually doing."

Identify and compare against industry best practices for an approach, design, architecture, or workflow. Understand the user's perspective, then research how leaders in the relevant problem space think, what patterns and tools they use, what language describes the problem, what's considered an antipattern, and what the user may not be accounting for. Use when the user asks "am I doing this right?", "am I thinking about this right?", "how do others solve this?", "what are others doing?", "what am I missing?", "is there a better way to do this?", "are there known pitfalls with my approach?", "am I reinventing the wheel?", "is there an established library, framework, tool, standard, pattern, or even a term for this that I should know about?", or wants to sanity-check or pressure-test their approach.

## What this skill does

1. **Reconstruct the user's perspective** — not a summary, a reconstruction. Play back what they're trying to accomplish, how they've framed the problem, what solution they're aiming at, and what assumptions are embedded in their approach. Use their language. Get it right before moving on. Ask if the reconstruction is accurate.

2. **Identify the problem space** — name the domain, community, or discipline where this problem lives. It may not be the one the user thinks. A question about "private notes in public repos" might live in DevSecOps, supply chain security, or open-source governance — not just "git workflow."

3. **Map to established thinking** — research and present:
   - What language leaders in this space use to describe this problem
   - What patterns are considered best practice and by whom
   - What is considered an antipattern and why
   - What tools exist that address this problem
   - What communities, standards bodies, or organizations define the norms

4. **Compare honestly** — show where the user's approach aligns with established practice, and where it diverges. For divergences:
   - Is the user reinventing something that already exists?
   - Is the user solving a different problem than they think?
   - Is the user's approach sound but using non-standard terminology that will make it harder to find help or collaborators?
   - Is the user missing a consideration that leaders in this space have already accounted for?
   - Is there a pitfall on the user's current path that experienced practitioners have documented?

5. **Surface what the user hasn't considered** — not as criticism, but as information. What trade-offs are implicit in their approach? What failure modes have others encountered on similar paths? What would change their mind or refine their direction if they knew about it?

6. **Offer the user's approach back, refined** — after the comparison, present what the user's approach would look like if it incorporated the relevant best practices. Don't replace their thinking — augment it. Show what stays, what shifts, and why.

## What this skill is NOT

- **Not sycophantic.** Do not validate the user's approach just because they proposed it. If industry leaders do it differently, say so directly.
- **Not dismissive.** The user's intuition often points at real problems even when the framing is non-standard. Respect the underlying insight while correcting the framing if needed. When the user asks "where might I be wrong," they're inviting critical rethinking from industry practice and first principles — not asking the agent to conclude they're wrong.
- **Not a copycat machine.** The best answer is *usually* a pre-existing standard or academic philosophy that's widely explored and applied. But sometimes the user's context reveals a genuinely nuanced problem where standard answers don't fully fit, or — more rarely — a novel idea with broader applicability. Don't demand conformity. Help the user distinguish between "I'm reinventing the wheel" and "I'm solving a problem the wheel wasn't designed for."
- **Not hostile to creativity.** These explorations sometimes uncover novel problems or novel solutions that are genuinely superior, at least in the user's context. The agent should help develop those without punishing originality — while still being honest about where established practice has already solved the problem better.
- **Not generative.** Do not invent a new approach and present it as the answer. The user is asking you to evaluate *their* approach against *existing* best practices — not to brainstorm alternatives unless the comparison reveals a clearly better path.
- **Not a lecture.** The user is not asking to be taught a subject from scratch. They have context and a direction. Meet them where they are.

## Document the journey

After the exploration, help the user produce a concise decision record. This is not a novel — it's a structured reference so future sessions (or future humans) can understand the reasoning without re-exploring. The document should include:

1. **Decided approach** — what we're doing and why
2. **How it contrasts with common intuitions** — without naming individuals, describe how someone might naturally frame this problem or solution differently, and why we diverged
3. **How it aligns with established practice** — where our approach matches industry standards and which standards
4. **Alternatives considered** — what else was on the table, with pros and cons of each
5. **What was confirmed** — assumptions that held up under scrutiny
6. **What was challenged** — assumptions that didn't, and how the approach shifted
7. **Go-forward plan** — concrete next steps, detailed layout of the decided solution

The tone should be confident and direct — "here is our approach and why" — not hedging or apologetic. A reader should finish it knowing what to do, not wondering what was decided.

## Where to put the documentation

All documentation produced by this skill should ideally be versioned. Where it goes depends on the repo's visibility and who benefits from each piece.

### Determine repo visibility

If the work pertains to a git repo, check whether it's safe to document freely there:
- Is there a GitHub remote? (`git remote -v`)
- If so, is it private? (`gh repo view --json visibility -q '.visibility'`)
- A private repo *may* be safe for personal context, use cases, and full research notes — but ask first. The user may intend to open-source it later or may not want exploratory notes polluting the git history of a pre-release product.
- A public repo requires splitting documentation into what belongs in the repo vs. what belongs elsewhere.

### Splitting documentation by audience

The exploration often produces two kinds of output:

**Repo-appropriate documentation** (benefits contributors, agents, and sometimes users):

- **CONTRIBUTING.md** — decided approach, design rationale, alternatives considered, antipatterns to avoid. This is the primary home for implementation and architectural decisions. Anyone contributing to the project — including coding agents — should have this as context. Most design decisions belong here because they affect only contributors.
- **README.md** — only when findings affect the perception of a repo's visitor or evaluator: value, risk, usability, trust. Examples: "works offline with no account required," "no dependencies outside the project directory," "deterministic output." Most implementation decisions have no bearing on README content.
- **Supplemental docs** (e.g., `docs/*.md`) — for research, detailed comparisons, or reference material too long for CONTRIBUTING.md but needed by contributors.

**Personal/private documentation** (benefits only the developer):

- First-party perspective, personal use cases, examples drawn from personal projects
- Research notes that frame findings in terms of the developer's specific needs
- Machine-specific details, workspace paths, personal project references
- The "why I was looking at this in the first place" context

For public repos, this second category belongs in a private repo (e.g., a personal notes or projects repo). For private repos, both categories can coexist.

### The overlap

Often the same research produces both kinds. The approach, alternatives, and conclusions are abstractly valuable to any contributor (→ CONTRIBUTING.md). The personal motivation, specific use cases, and how-I-got-here narrative are valuable only to the developer (→ private repo). Document both, in the appropriate location and tone. The public version is abstract and impersonal. The private version is specific and contextual. Neither is a subset of the other — they serve different readers.

### Review context against documentation — continuously

Not just at the end. Before every write — every file save, every commit, every GitHub issue creation or update — ask whether the content being written belongs in that artifact for that audience. This is foremost a continuous discipline throughout the process, and also a final pass — with iteration as needed until all is captured in the right places.

**Critical tollbooths:** The highest-stakes moments for re-evaluation are immediately before any action that is difficult to reverse or that could lead to improper exposure — even indirectly. This includes:
- **Committing to a local git repo** — even unpushed commits pollute git history and may be pushed later in a broader set of changes during a future session the agent has no control over.
- **Pushing to a remote or writing to GitHub** via `gh` CLI, APIs, or git commands (issues, PRs, comments, releases).
- **Writing to any shared or eventually-shared resource** — a Google Doc currently limited to a small audience but intended to be shared later retains edit history that may be painful to clean even if caught in time.

The test is not "is this public right now?" but "if the user walked away this minute, could this content find its way to exposure through normal subsequent actions?"

**If something leaks despite this:** Do not simply edit and move on. Editing a GitHub issue leaves the original in notification emails and API caches. Amending a commit leaves the original in reflog and potentially in remote history. If the leaked content is a privacy concern:
- **Local commit not yet pushed:** Amend or rebase to remove it from history entirely.
- **Already pushed:** Force-push the cleaned history to the remote. If the repo is public and time has passed, assume the content has been cached or indexed — the exposure cannot be fully reversed, but the source should still be cleaned.
- **GitHub issue or comment:** Delete it entirely rather than editing, since edit history may be visible or cached. Recreate with clean content if needed.
- **Release assets:** Delete the release, not just the asset.

Alert the user to the exposure and what remediation was taken or is needed.

Before considering the documentation complete, also review the full conversation context — every question asked, research done, alternative explored, assumption tested, conclusion reached — against what has been captured in documentation.

For each uncaptured piece of context, ask on a piece-by-piece basis:

- **Who does this serve?** A product user? A contributor? The developer privately? A future agent session?
- **Where would that person ideally encounter this?** In a README quickstart? In CONTRIBUTING.md design rationale? In a private notes repo? In an inline code comment?
- **Does this piece fit the audience and purpose of the target artifact?** If the answer is no — if it serves a different reader or a different moment — find another home for it rather than forcing it into the wrong document.
- **Is this captured at all?** If not, it will be lost when the session ends.

This is not a bulk operation. Each piece of uncaptured context may belong in a different place for a different audience. A research finding might go in CONTRIBUTING.md. The personal confusion that led to that research might go in private notes. The clean conclusion might go in the README. The rejected alternative might go in a design doc. Evaluate each one individually.

This review is often the point where the split between locations becomes clear. The nature of the content determines its home:

- A user's personal story of confusion, failed attempts, or gradual understanding is valuable as a private learning record but does not belong in a public product repo. A README's quickstart section is not served by a pedantic account of someone's journey to discovering how simple the product is to use.
- The *conclusions* from that journey — the clean install steps, the caveats to avoid, the recommended approach — belong in the public docs.
- The *process* of arriving there — initial assumptions, what was tried and failed, what felt unintuitive and why — belongs in private notes. Not just for privacy or brand reasons, but because it's a different audience with different needs.
- Research findings and alternatives considered often belong in CONTRIBUTING.md (they help future contributors understand why the current approach was chosen), but the personal motivation for the research does not.

This isn't just about privacy. A public product repo is a tool for its users and contributors. Personal narrative, however instructive to the author, is noise to that audience. The private repo is where the full story lives — the public repo gets the distilled result.

### Ask before writing

Before creating or modifying documentation files, confirm the plan with the user: what goes where, which files, and whether the split between public and private makes sense for their situation.

## How to use context

Draw on:
- The current conversation — what the user has said, what they've built, what decisions they've made
- The codebase and project state — what exists, what conventions are in place
- **Model training and web search — both, emphasizing each as appropriate.** Some topics (software architecture patterns, common tool usage, established design philosophies) are well-represented in training data from millions of public repos and may be hard to find authoritative web articles on. Other topics (current tool versions, recent community standards, emerging best practices) require fresh web search. Rarely if ever rely exclusively on just pretraining or just web search — cross-reference both.
- Memory — what you know about the user's goals, preferences, and prior decisions

## When to use this skill

When the user says things like:
- "Am I thinking about this right?"
- "How do others solve this?"
- "Is this how it's done?"
- "What am I missing?"
- "Help me think through whether this approach makes sense"
- "I have a way I want to do this but I want to sanity-check it"
- Or explicitly invokes `/identify-best-practices`
