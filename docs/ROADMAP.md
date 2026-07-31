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

## Block B — Authoring (insert, never hand-edit)

- 📋 **RK78** (deps: —) **ship deletes the sections nested under the one it drops** — A section body runs to the next heading of the same depth, so dropping a level-2 took its four level-3 children with it, two of them belonging to open tasks. → §RK78

## Block C — Query (consult without reading the file)

- 💭 **RK83** (deps: —) **pick offers an idea when a designed task is ready** — The tiers rank by id and never by marker, so a caller asking to execute a block is handed the one task that still needs designing. → §RK83

## Block D — The gate

- 💭 **RK84** (deps: —) **lint cannot answer whether this change made it worse** — On a corpus with 317 standing problems the absolute count carries no signal, and the only way to attribute a delta was to stash the files and run it twice. → §RK84

## Block E — Adoption

- ⏳ **RK21** (deps: RK20 ✅) **A standard adopted by one project is a preference** — roll out to Turing, Dumont and Cursarei, each with its own `roadmap.toml`. → §RK21
- 📋 **RK75** (deps: RK3 ✅, RK37 ✅) **A backlog that files work under any other word cannot declare its headings** — Dumont writes Track, Turing writes bare sub-blocks and cursarei writes Fase, so 34 of 34 entries read as filed under nothing. → §RK75
- 📋 **RK77** (deps: RK74 ✅, RK75) **A backlog whose marker, heading and ledger all differ cannot be adopted at all** — cursarei needs four unrelated keys the format has none of, so 0 of its 16 open lines and 9 of its 12 ledger entries stay unread. → §RK77

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK79** (deps: —) **The plugin cache and the developer checkout are two engines, and both answer 0.1.0** — The launcher puts the cache's own src first on sys.path, so hooks and MCP run one engine while the CLI runs another, and the version cannot tell them apart. → §RK79
- 📋 **RK81** (deps: RK79) **The MCP server is declared and no tool reaches the client** — A whole session drove the CLI through Bash because no roadkeep tool was offered, which is the surface that would have made the flags discoverable without reading help. → §RK81
- 💭 **RK82** (deps: —) **Nothing announces the write path at the moment a session starts reading the files** — The hook refuses a hand-edit and the skill names the read verbs, but both arrive after the first grep, so the rule is learned by breaking it. → §RK82

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
