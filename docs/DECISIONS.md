# Decisions

## Block A — The model (a task is data before it is a line)

## Block B — Authoring (insert, never hand-edit)

- ✅ **RK1269** **a decision that outlives the work explaining it has no governed file, so an ADR is kept by hand or not at all** — ROLES is closed and named: a role no machinery knows is a file with no schema.

## Block C — Query (consult without reading the file)

- ✅ **RK1270** **nothing prints what `roadkeep.toml` may declare, so its keys live only in the parser that rejects them** — The shape of `roadkeep.toml` is read off the frozensets that refuse it, never a second copy.

## Block D — The gate

## Block E — Adoption

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

## Block G — The editor surface (the backlog where the file is open)

- ✅ **RK1271** **the editor completes nothing in `roadkeep.toml`, so every key is typed from memory** — A reader outside the package renders a payload and never a rule: no list, no limit, no parser.

## Block H — The tool's own shape (what one verb costs to change)
