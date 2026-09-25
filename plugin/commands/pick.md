---
description: What to work on next, and the reason it was chosen
argument-hint: "[block]"
allowed-tools: mcp__roadkeep__pick, mcp__plugin_roadkeep_roadkeep__pick, mcp__roadkeep__brief, mcp__plugin_roadkeep_roadkeep__brief, mcp__roadkeep__deps, mcp__plugin_roadkeep_roadkeep__deps, Bash(roadkeep pick:*), Bash(roadkeep brief:*), Bash(roadkeep deps:*)
---

Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/roadkeep.py" pick`, scoped to the block in `$1` when that is not empty (`--block $1`) and
unscoped when it is.

Then print the choice and the tier that answered it — work already in progress, the declared
priority, or the lowest ready id. The tier is the point: a pick without its reason is a
suggestion, and the user cannot tell whether it skipped something.

Two things worth saying afterwards, when they apply:

- **Scope it to finish a block.** Unscoped, the answer may belong to a block the user is not
  working in. Scoped, an answer with no task says which of three states the block is in —
  finished, empty, or a label nothing declares — so report the one it named.
- **`python "${CLAUDE_PLUGIN_ROOT}/scripts/roadkeep.py" brief <id>` starts it in one call** — the line, its rationale, its resolved
  deps, the blocker chain and the non-goals that bind it. Offer that instead of reading the
  files, which costs context and answers less.

Do not begin the work unless the user asks for it. This command answers a question.
