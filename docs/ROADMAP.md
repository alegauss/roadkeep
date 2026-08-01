# roadkeep — Roadmap (active backlog)

> **Single source of truth for task status.** Flat, one line per task.
> Only **unshipped** work lives here (📋 designed · 💭 idea · ⏳ partial · 🛠 in-progress).
> Shipped work moves to [CHANGELOG.md](CHANGELOG.md); design rationale lives in
> [IMPROVEMENTS.md](IMPROVEMENTS.md).
>
> **What this is.** A CLI that owns writes to a project's roadmap, changelog,
> improvements and strategy files, so the format is a schema at the point of
> insertion instead of a convention an author is asked to remember — shipped as a
> Claude Code plugin, because the author to constrain is usually an agent.
>
> **The one law.** *A field limit enforced only by a reviewer is a limit discovered
> after the prose is written.* `add` refuses an over-length field; `lint` refuses a
> file that drifted anyway. The tool validates — it never writes prose.
>
> **An entry here is one sentence: what + why + `→` pointer** — ≤320 characters,
> symptom in bold (what does not work), never a solution name. This file is the
> tool's own conformance fixture: if `lint` cannot pass it, `lint` is wrong.
>
> **How to pick work:** the lowest-numbered task whose `deps` are all shipped.

## Block A — The model (a task is data before it is a line)

- 💭 **RK90** (deps: —) **There is no state for a task set aside but neither shipped nor abandoned** — Every marker is an open one the roadmap keeps or a terminal one the ledger owns, so the data cannot hold work that is paused but still alive. → §RK90

## Block B — Authoring (insert, never hand-edit)

- 📋 **RK78** (deps: —) **ship deletes the sections nested under the one it drops** — A section body runs to the next heading of the same depth, so dropping a level-2 took its four level-3 children with it, two of them belonging to open tasks. → §RK78
- 💭 **RK91** (deps: RK90) **Pausing a task means retiring it, losing its id, rationale section and every dependent that named it** — retire is the only non-ship exit and the resolver reads it as never, while a re-add cannot reclaim the id, so a pause and an abandonment are recorded the same way. → §RK91
- 💭 **RK93** (deps: —) **add exits 0 on a line whose derived pointer fails lint at once, and names no follow-up** — Under ref_scheme=id every line carries a derived pointer lint requires to resolve, but the section is a second command, so a successful add always leaves a gate failure it never mentions. → §RK93

## Block C — Query (consult without reading the file)

- 💭 **RK83** (deps: —) **pick offers an idea when a designed task is ready** — The tiers rank by id and never by marker, so a caller asking to execute a block is handed the one task that still needs designing. → §RK83
- 💭 **RK92** (deps: RK90) **The dep resolver has no answer for a dep blocked on paused work** — Its outcomes are shipped, open, unknown and unresolvable, so a task waiting on a deferred one reads as ready or blocked-forever and pick offers or buries it wrongly. → §RK92
- 💭 **RK94** (deps: —) **weight gives one commit's whole size to every task it shipped, so a bulk import pins the percentiles to itself** — Cost comes from the commit that wrote each entry, but one that shipped 47 tasks charges all its lines to each, so the median advertised for granularity has no signal here. → §RK94

## Block D — The gate

- 💭 **RK84** (deps: —) **lint cannot answer whether this change made it worse** — On a corpus with 317 standing problems the absolute count carries no signal, and the only way to attribute a delta was to stash the files and run it twice. → §RK84

## Block E — Adoption

- ⏳ **RK21** (deps: RK20 ✅) **A standard adopted by one project is a preference** — roll out to Turing, Dumont and Cursarei, each with its own `roadmap.toml`. → §RK21
- 📋 **RK77** (deps: RK74 ✅, RK75 ✅) **A backlog whose marker, heading and ledger all differ cannot be adopted at all** — cursarei needs four unrelated keys the format has none of, so 0 of its 16 open lines and 9 of its 12 ledger entries stay unread. → §RK77

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK89** (deps: RK85 ✅) **A capture survives the command that produced it and not the session that ran it** — It is printed and then gone unless the caller thought to redirect it, which is the second step the same block already documents an agent not taking. → §RK89

## Non-goals

Deliberately **not** built — check this list before proposing work:

- **No web UI and no server.** Files and a CLI. The store is the repository.
- **No model and no prompts.** The tool validates and renders; it never writes the
  symptom or the rationale. A generator would reintroduce exactly the prose drift
  this exists to stop.
- **No enforced id scheme beyond `<prefix><n>`.** Non-contiguous, retired-never-reused
  is a property of real backlogs, not a defect to normalize.
- **No dates or quarters.** A marker is maturity, not a schedule.
- **No effort or size field.** Nothing can verify a letter, `pick`'s every tier is a
  fact, and what an agent pays is context: 4 to 14 files a task, against lines that vary
  27-fold, so the letter prices the axis nobody pays.
- **No backlog in an issue tracker** (Jira, Linear, GitHub Issues.) A backlog that lives
  in a service is one an agent cannot `Grep`; a one-way report about this tool, sent
  explicitly, moves nothing out of the files.
