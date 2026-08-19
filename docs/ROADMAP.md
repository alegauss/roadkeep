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

- 📋 **RK1261** (deps: —) **a ship refusal blames --why for characters that came from --superseded-design** — The two render as one sentence and are reported as one field, so the count never matches what was passed and the remedy points at the half that has to survive. → §RK1261
- 📋 **RK1262** (deps: —) **a refused --remainder is reported as a why, so the retry has to guess which of the two strings was short a full stop** — one message naming the wrong flag costs a whole ship call, and the two arguments it could mean are adjacent on the same command line. → §RK1262
- 📋 **RK1263** (deps: —) **section amend replaces the whole body, so fixing one citation means re-emitting every table and code fence verbatim** — The edit is one clause and the risk is the other 200 lines, which a retyped fence loses silently. → §RK1263
- 📋 **RK1265** (deps: —) **a non-goal states what is not built, and nothing states what must be true for a block to be finished** — So a criterion is written into a rationale section that ship deletes, and the only test for doneness left is a line count reaching zero. → §RK1265

## Block C — Query (consult without reading the file)

## Block D — The gate

## Block E — Adoption

- 📋 **RK1264** (deps: —) **the scaffold is the only writer of [files], so a project past init cannot declare a role it turns out to want** — init --deferred refuses on a configured tree, so the store stays a hand edit there and no earlier surface can offer a door it has no verb to open. → §RK1264

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 🛠 **RK1260** (deps: —) **the MCP schemas offer '-' and stdin, an input channel no MCP client can provide** — The MCP verbs still expose no --section-body-file or --body-file, withheld as a path this transport does not share — which a stdio server always does. → §RK1260

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
