---
description: Check every governed line, and say where it drifted
allowed-tools: Bash(roadkeep lint:*), Bash(roadkeep show:*)
---

The gate, on this project's governed files:

!`roadkeep lint`

Exit 0 means every line validates, round-trips and points at something that exists. Exit 1
names each finding as `file:line:column` — the location, not the consequence.

Report the findings as they came, and then help with the ones that need a decision:

- A field over its limit, a `symptom` named after its fix, a `why` that grew a second
  sentence: those are editorial, and the fix is the user's words. Say what has to shrink and
  by how much. Never rewrite their line for them.
- A dep nothing satisfies, a pointer resolving to nothing, a section nothing points at: those
  are structural, and `roadkeep show <id>` prints the line with its section and its paths.
- Whitespace, a marker's codepoint, dep order, an annotation: those are **derived**, and
  `roadkeep lint --fix` repairs them without touching a word. Offer it; do not run it
  unasked, because it writes.

An over-budget instruction file is not a formatting complaint: it is the budget in
`roadkeep.toml` saying a file loaded on every turn grew past what it may cost.
