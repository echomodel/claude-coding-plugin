# Reusable Assets

Everything in this directory is a reusable, portable asset that can be
published to a marketplace independently. These are the source of truth —
the build script copies them into `plugin/dist/` for the assembled plugin.

## Agents

Standalone agent definitions. Each `.md` file is a complete agent body
with frontmatter. These can be consumed by any agent platform that reads
markdown agent definitions.

## Skills

Skills following the [agentskills.io](https://agentskills.io) standard.
Each skill is a directory containing a `SKILL.md` file.

## Rules

- Only reusable, platform-agnostic content belongs here.
- Plugin-specific agents (e.g., `claude-coder`) belong in `plugin/src/agents/`.
- Do not edit `plugin/dist/` directly — run `./build` to assemble it.
