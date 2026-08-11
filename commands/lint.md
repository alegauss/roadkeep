---
description: Check every governed line, and say where it drifted
allowed-tools: mcp__roadkeep__lint, mcp__plugin_roadkeep_roadkeep__lint, mcp__roadkeep__show, mcp__plugin_roadkeep_roadkeep__show, Bash(roadkeep lint:*), Bash(roadkeep show:*)
---

The gate, on this project's governed files:

!`python "${CLAUDE_PLUGIN_ROOT}/scripts/roadkeep.py" lint`

Exit 0 means every line validates, round-trips and points at something that exists. Exit 1
names each finding as `file:line:column` — the location, not the consequence.

Report the findings as they came, and then help with the ones that need a decision:

- A field over its limit, a `symptom` named after its fix, a `why` that grew a second
  sentence: those are editorial, and the fix is the user's words. Say what has to shrink and
  by how much. Never rewrite their line for them.
- A dep nothing satisfies, a pointer resolving to nothing, a section nothing points at: those
  are structural, and `python "${CLAUDE_PLUGIN_ROOT}/scripts/roadkeep.py" show <id>` prints the line with its section and its paths.
- Whitespace, a marker's codepoint, dep order, an annotation, a derived pointer, a dead queue
  entry: those are **derived**, and `python "${CLAUDE_PLUGIN_ROOT}/scripts/roadkeep.py" lint --fix` repairs them without touching a
  word. Offer it; do not run it unasked, because it writes.

An over-budget instruction file is not a formatting complaint: it is the budget in
`roadkeep.toml` saying a file loaded on every turn grew past what it may cost.
