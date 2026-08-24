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

## Block C — Query (consult without reading the file)

- 📋 **RK1320** (deps: —) **one drafted flag answers two ways about the same prose, so a number is labelled the caller's on a line the file holds** — It is derived from open_line, which was a proxy for a caller-composed line and stopped being one when brief began pricing a ship. → §RK1320

## Block D — The gate

- 📋 **RK1322** (deps: —) **the tree is split between two line terminators and nothing reads which a file is, so an append lands in the wrong one** — The gate refuses a file that mixes them and says nothing about 47 of 148 sources being CRLF, so the split is found by breaking it. → §RK1322
- 📋 **RK1323** (deps: —) **this repository declares no [criteria], so the fixture that proves the format does not exercise a table init now writes** — The law is that a schema change validates here first, and the one list added since is proven by tests alone rather than by the artefact. → §RK1323

## Block E — Adoption

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK1325** (deps: —) **a project wiring no plugin is told its doors arrive under one, so a payload names a tool nothing there answers** — served_by falls back past the project it was handed, and RK449's rule is that a door nothing serves publishes its argv alone. → §RK1325
- 📋 **RK1326** (deps: —) **a project with no plugin wired is told its doors arrive under one, so every call the payload names is uncallable there** — served_by falls back to the running session when the project declares nothing, and the payload it feeds is about the project. → §RK1326

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

- 📋 **RK1321** (deps: —) **budget serves seven subjects on one tool and is now the largest, so every subject added re-argues a shared ceiling** — Two ceilings moved for it in one session, and a per-tool limit calibrated against one-subject verbs is binding on the wrong thing. → §RK1321
- 📋 **RK1324** (deps: —) **four key names carry the same runnable command across the payloads, so a consumer needs four readers for one idea** — RK1307 held that a door the text names is in the payload and never that it is findable, so each verb chose a name as it was written. → §RK1324

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
