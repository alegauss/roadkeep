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

- 🛠 **RK499** (deps: —) **Every prose door accepts a tab, a zero-width codepoint and a space that is not one, and the gate refuses all three** — The same field refuses a leading or trailing space at the write, so one whitespace rule is held there and the neighbouring one is not. → §RK499
- 📋 **RK500** (deps: —) **A dep flag naming an id nothing carries is written, and so is one on the block the line is being filed into** — Both are decidable against the backlog the write has already loaded, and the second files a line that no amount of shipping anything else can start. → §RK500

## Block C — Query (consult without reading the file)

## Block D — The gate

- 📋 **RK1000** (deps: —) **A limit, prefix or marker written into the package instead of read from config is found by an adopting project** — L6's row carries an empty holder because nobody wrote the scan, not because no set exists: it is the one of the three a source scan decides. → §RK1000
- 📋 **RK1001** (deps: —) **A second defect in a class an invariant already holds reads like new work, so a gap in a holder is filed as a fix** — Twelve of the fifteen rows carry a holder and nothing says which of them a task instantiates, so a recurrence and a rung nobody had climbed are one shape. → §RK1001
- 📋 **RK1002** (deps: —) **An id named only as an example in prose is read as spent, and nothing refuses it where the prose is composed** — `section add` validated the body and said nothing; the cost surfaced two sessions later in a non-blocking warning, and the gate carries no code for it. → §RK1002

## Block E — Adoption

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

## Non-goals

Deliberately **not** built — check this list before proposing work:

- **No web UI and no server.** Files and a CLI. The store is the repository.
- **No model and no prompts.** The tool validates and renders; it never writes the
  symptom or the rationale. A generator would reintroduce exactly the prose drift
  this exists to stop.
- **No enforced id scheme beyond `<prefix><n>`.** Non-contiguous, retired-never-reused
  is a property of real backlogs, not a defect to normalize.
- **No dates or quarters.** A marker is maturity, not a schedule.
- **No backlog in an issue tracker** (Jira, Linear, GitHub Issues.) A backlog that lives
  in a service is one an agent cannot `Grep`; a one-way report about this tool, sent
  explicitly, moves nothing out of the files.
- **No multi-line task line.** A task whose text wraps across paragraphs, with its deps
  on a `↳` line of their own, is a second grammar; reading only the first line would
  ship a truncated why and orphan the rest.
- **No supported Python API.** The CLI, the MCP tools and the plugin are the surface;
  `from roadkeep import Schema` is how the tests reach the vocabulary, so no `py.typed`
  ships and a rename inside the package breaks nobody.
- **No effort or size field.** Nothing can verify a letter, `pick`'s every tier is a
  fact, and what an agent pays is context — median to p90, files vary 1.4× against lines
  2.7×, so the letter prices the axis nobody pays.
