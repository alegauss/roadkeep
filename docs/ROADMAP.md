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

## Priority

## Block A — The model (a task is data before it is a line)

## Block B — Authoring (insert, never hand-edit)

- 📋 **RK1229** (deps: —) **A dep with a parenthesis is written, then no verb can reach the line it made unreadable** — amend accepts it, the rendered deps group closes early, and amend, retire, defer, repair and lint --fix all answer that no task carries the id. → §RK1229
- 📋 **RK1231** (deps: —) **renumber leaves the section heading it wrote, so an outline-ref project keeps a title naming the old id** — add --section writes the heading as title plus id, but renumber moves a section only when the ref IS the id — so under an outline the title keeps the old number. → §RK1231

## Block C — Query (consult without reading the file)

- 📋 **RK1226** (deps: —) **Nothing names the open half of a partial, only the half that shipped** — brief joins line, section and ledger but omits the recorded qualifier, so resuming a partial means subtracting one file from another to recover the remainder. → §RK1226

## Block D — The gate

- 📋 **RK1228** (deps: —) **Nothing reports source changed under an open task while the line stayed open** — lint --since flags a section edited without its line but not the mirror, so work that landed and passed its tests can leave the ledger with no entry at all. → §RK1228
- 🛠 **RK1232** (deps: —) **A full run asks for every core, so the machine has nothing left while the suite is running** — Half the workers cost 176s against 174s on this suite, so `auto` can leave half the machine to the session that started the run instead of taking the last core. → §RK1232

## Block E — Adoption

- 📋 **RK1227** (deps: —) **section amend accepts prose citing an anchor that does not exist, so a docs-only commit turns an adopter's gate red** — It checks the body's length and shape and never resolves the anchors it names, so a section citing one a ship removed is written and found by running the suite. → §RK1227

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK1230** (deps: —) **Nothing tells a shell caller which engine copy is the one wired to this project** — A stale copy in a different plugins root answers plausibly instead of refusing, and the only signal is a note inside an unrelated report. → §RK1230

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

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
- **No supported Python API.** The CLI, the MCP tools and the plugin are the surface; a
  boundary held by a test inside the package is not one, so nothing ships `py.typed` and
  a rename still breaks nobody.
- **No effort or size field.** Nothing can verify a letter, `pick`'s every tier is a
  fact, and what an agent pays is context — median to p90, files vary 1.4× against lines
  2.7×, so the letter prices the axis nobody pays.
