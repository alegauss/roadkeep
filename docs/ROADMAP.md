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

- 🛠 **RK1269** (deps: —) **a decision that outlives the work explaining it has no governed file, so an ADR is kept by hand or not at all** — A `decisions` role is the line-and-section pair whose one departure is being superseded, so a decision record is a schema at insertion instead of a convention. → §RK1269

## Block C — Query (consult without reading the file)

- 📋 **RK1270** (deps: —) **nothing prints what `roadkeep.toml` may declare, so its keys live only in the parser that rejects them** — A verb answers the config's own shape — table, key, type, default, declared or not — so a reader outside the package compiles no second copy. → §RK1270

## Block D — The gate

## Block E — Adoption

- 📋 **RK1272** (deps: —) **`[limits]`, `[budgets]` and `[markers]` have no verb, so the file governing every write is the ungoverned one** — A verb declares one, printing the reading it is chosen against first, so a limit is measured where it is typed instead of guessed and lowered later. → §RK1272

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

## Block G — The editor surface (the backlog where the file is open)

- 📋 **RK1271** (deps: RK1270) **the editor completes nothing in `roadkeep.toml`, so every key is typed from memory** — The panel offers the keys the package printed and hovers their reason, so a declaration is composed against its shape instead of checked after it exists. → §RK1271

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
