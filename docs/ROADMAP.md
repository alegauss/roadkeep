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

- 📋 **RK1112** (deps: —) **section show prints the subtree and section amend takes only the own body, so the obvious round-trip is refused** — Feeding show's output straight back reports 1692 words against a 300 limit, which reads as prose written too long rather than as the wrong extent. → §RK1112

## Block C — Query (consult without reading the file)

## Block D — The gate

## Block E — Adoption

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK1113** (deps: —) **`install --check` reports drift on a `--committed` project and names the plain `install`, which downgrades the wiring** — The committed launcher exists for a session that installs no plugin, so a refresh replacing it with a checkout path leaves that environment with no guard. → §RK1113
- 📋 **RK1114** (deps: —) **`pick` offers a partially shipped line that `--claim` then refuses, the partial ledger entry reading as a ship** — A partial leaves the line open at ⏳ by design, so the one verb that starts a task cannot take the line the picker just named. → §RK1114
- 📋 **RK1115** (deps: —) **defer refuses any line whose why already fills its budget, because the wrapped reason is charged to the same limit** — A line written to its why budget can never be paused: the prefix alone needs 14 characters the limit has no room for, so the only doors are terminal. → §RK1115

## Block G — The editor surface (the backlog where the file is open)

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
