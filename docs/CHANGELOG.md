# roadkeep — Shipped Ledger

> What has **shipped**, indexed by Block — one entry per task. `git log` is
> authoritative for detail. Active work lives in [ROADMAP.md](ROADMAP.md); design
> rationale for unshipped work lives in [IMPROVEMENTS.md](IMPROVEMENTS.md).
>
> An entry is its roadmap line with the marker set to ✅ and the `deps` and
> `→ §RK<n>` fields dropped — the rationale section is deleted when the task ships,
> so a pointer to it would not resolve. The block headings mirror ROADMAP.md.

## Block A — The model

- ✅ **RK1** **Nothing knows what a task line is, so every check is a regex over prose** — a schema over the six fields (id, status, block, deps, symptom, why, ref) is the only thing that can refuse an over-length line at write time.
- ✅ **RK2** **A parser that cannot re-render what it read corrupts the file it edits** — parse → render → byte-identical is the invariant that lets a CLI own writes to a hand-written Markdown file.
- ✅ **RK3** **Hardcoding one project's vocabulary makes the tool single-use** — `roadmap.toml` carries prefix, file paths, marker set and per-field limits, so Turing's `STRATEGY.md` and Shio's absence of one are both configurations.
- ✅ **RK4** **The next id cannot be inferred from a block header, and a wrong guess collides with a retired one** — take the max across every configured file, in one command, with no counter file to drift.
- ✅ **RK27** **A pointer's target is numbered by hand, and deleting a section leaves a hole nobody renumbers** — keying each rationale section by task id makes the pointer derivable from the line, so shipping costs no renumbering and resolving it costs no reading of the outline.
- ✅ **RK28** **A dep the tool cannot resolve reads exactly like one that is merely pending** — `Block P` and `real design partners` are real deps on work outside the backlog, so a resolver has to name them unresolvable instead of counting them unfinished.
- ✅ **RK31** **The reasoning behind a shipped decision survives only in a commit nobody greps** — the shipping commit is derived from the ledger's own diff, so the reasoning is one lookup away and no stored hash can rot when history is rewritten.
- ✅ **RK37** **A dep on a block that does not exist resolves as satisfied** — a block is declared by a heading and by nothing else, so a dep naming one no heading declares is unresolvable, never a block that happens to have nothing open.

## Block B — Authoring

- ✅ **RK5** **Writing the line by hand is where the prose leaks in** — the fields are refused at input, so the limit is met before a sentence is composed to fill it and the file is only ever touched by a line that renders back to what was written.
- ✅ **RK6** **Shipping a task is four edits across three files, so one is always missed** — the three edits are one command that validates every one of them before a file is touched, and the roadmap line is removed rather than stubbed so status keeps one home.
- ✅ **RK7** **Two files can disagree about one task's status** — the marker is written in the roadmap alone, and a sibling file carrying one for the same id is refused rather than reconciled because nothing says which of the two would be right.
- ✅ **RK8** **A dep annotation goes stale the moment its target ships** — the annotation is derived from the resolver on every write, so a shipped dep never reads as pending and a marker nobody typed is never invented.
- ✅ **RK9** **The four files are not four of the same thing, and prose has no line to validate** — prose is governed by section instead: an anchor a pointer resolves, a budget in words, and a place derived from the block, with drop being the edit ship already calls.
- ✅ **RK38** **A write reports an exit code and nothing about what it changed, so only a human can react to it** — every mutator prints the id, the block and whether that block still holds an open line, which is the whole event a hook needs and the last thing the tool does about it.

## Block C — Query

- ✅ **RK10** **Counting a backlog by grep silently drops the lines it fails to match** — every count prints what it could not read beside what it did, so a broken line, a parked task and a marker this project never declared are visible instead of silently absent.
- ✅ **RK11** **Picking work means reading the whole file to find one task whose deps are shipped** — three tiers answer it and the answer names the one that fired: work already in progress, then the priority a project declares, then the lowest id whose deps all shipped.
- ✅ **RK12** **A task's design lives in a second file and nothing joins them** — one call joins the line, its rationale section and the paths its text names, and an absent section carries the reason it is absent instead of reading as a design that exists.
- ✅ **RK13** **A blocked task looks identical to a ready one, and one that unblocks half the backlog to one that unblocks nothing** — the walk is tested code instead of an ad-hoc traversal: it names the blocker chain, reports a cycle as a group, and counts how many tasks shipping this one unblocks.
- ✅ **RK29** **Starting a task costs reading two whole files to learn one line's worth of context** — one call composes the line, its rationale, its resolved deps, the blocker chain, what shipping it unblocks and the non-goals, bounded to fit a tool result.

## Block D — The gate

## Block E — Adoption

## Block F — The Claude Code plugin
