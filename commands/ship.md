---
description: "Ship one task: ledger entry, line gone, rationale dropped"
argument-hint: <id>
allowed-tools: mcp__roadkeep__ship, mcp__plugin_roadkeep_roadkeep__ship, mcp__roadkeep__show, mcp__plugin_roadkeep_roadkeep__show, mcp__roadkeep__lint, mcp__plugin_roadkeep_roadkeep__lint, Bash(roadkeep ship:*), Bash(roadkeep show:*), Bash(roadkeep lint:*)
---

Shipping `$1`:

!`roadkeep ship $1`

That is one transaction across three files — the ledger entry, the roadmap line, the rationale
section — plus the dependents' annotations. It happened or none of it did, so there is nothing
to finish by hand.

Report what it printed. Then:

- If it refused, say what it refused on and stop. A missing id means the user did not name
  one: ask which task, and do not guess from the conversation.
- If it wrote, remind the user that the docs now describe a state their code has to be in:
  the same commit carries both, or the ledger is ahead of the repository.
- Do not restate the counts. `roadkeep list` and `roadkeep stats` answer that, and a number
  retyped here is one that goes stale.
