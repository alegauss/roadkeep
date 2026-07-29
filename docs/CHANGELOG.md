# roadkeep — Shipped Ledger

> What has **shipped**, indexed by Block — one entry per task. `git log` is
> authoritative for detail. Active work lives in [ROADMAP.md](ROADMAP.md); design
> rationale for unshipped work lives in [IMPROVEMENTS.md](IMPROVEMENTS.md).
>
> An entry is its roadmap line with the marker set to ✅ and the `deps` and
> `→ §x.y` fields dropped — the rationale section is deleted when the task ships,
> so a pointer to it would not resolve. The block headings mirror ROADMAP.md.

## Block A — The model

- ✅ **RK1** **Nothing knows what a task line is, so every check is a regex over prose** — a schema over the six fields (id, status, block, deps, symptom, why, ref) is the only thing that can refuse an over-length line at write time.

## Block B — Authoring

## Block C — Query

## Block D — The gate

## Block E — Adoption

## Block F — The Claude Code plugin
