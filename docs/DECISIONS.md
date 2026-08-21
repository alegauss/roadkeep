# Decisions

## Block A — The model (a task is data before it is a line)

## Block B — Authoring (insert, never hand-edit)

- ✅ **RK1269** **a decision that outlives the work explaining it has no governed file, so an ADR is kept by hand or not at all** — ROLES is closed and named: a role no machinery knows is a file with no schema.
- ✅ **RK1274** **a decision is never marked superseded, so the file records that one was made and not that it stopped holding** — A decision is superseded once, and both entries stay: the marker says which one is live.

## Block C — Query (consult without reading the file)

- ✅ **RK1270** **nothing prints what `roadkeep.toml` may declare, so its keys live only in the parser that rejects them** — The shape of `roadkeep.toml` is read off the frozensets that refuse it, never a second copy.
- ✅ **RK1286** **the read that exists to fit in a tool result is the one thing here with no budget, and it grew four rows** — The read that replaces reading the file is bounded by the widest brief, never the median.

## Block D — The gate

## Block E — Adoption

- 🗑 **RK1272** **`[limits]`, `[budgets]` and `[markers]` have no verb, so the file governing every write is the ungoverned one** — The argument for a limit goes in the commit that wrote it, never in a comment beside the number (superseded by RK1293).
- ✅ **RK1293** **the argument for a limit is ruled into the commit body, which a tool this project does not own composes** — The argument for a governed number is written above the key by the verb that declares it, never in the commit body.

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

## Block G — The editor surface (the backlog where the file is open)

- ✅ **RK1271** **the editor completes nothing in `roadkeep.toml`, so every key is typed from memory** — A reader outside the package renders a payload and never a rule: no list, no limit, no parser.

## Block H — The tool's own shape (what one verb costs to change)
