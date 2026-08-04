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

- 📋 **RK294** (deps: —) **Nothing calls the scope at the moment the commit is made** — `ship` runs at exactly that second and says nothing about the tree, so RK280's mechanism is reached only by prose in agents.md — the shape RK1 says does not hold. → §RK294
- 📋 **RK295** (deps: —) **A scope naming a path the tree does not have is recorded in silence** — `claim --path` takes the path verbatim and never asks the disk, so a typo is a file the commit will not stage and a scope that reads as complete. → §RK295
- 📋 **RK296** (deps: —) **An undeclared-block refusal still lists every label the file declares** — RK257 gave it the file and the verb and left the list, so a project with 90 blocks answers a question nobody asked and buries the two clauses that are the remedy. → §RK296

## Block C — Query (consult without reading the file)

- 📋 **RK265** (deps: —) **budget omits the pointer under an outline ref scheme, so it over-reports the room by the anchor width** — It answered 182 characters left for a why `add` then refused at 174, the 8 being ` → §XX.2` — a limit found after the prose exists, which this verb exists to prevent. → §RK265
- 📋 **RK283** (deps: —) **budget answers for the task line only, so the two largest prose limits are discoverable only by failing** — A non-goal why took two refusals at 286 and 234 against 200, and a section body one at 366 words against 300 — the verdict-after-the-prose this verb exists to prevent. → §RK283
- 📋 **RK287** (deps: —) **A section's word count includes its subsections, so it names a figure no limit is measured against** — show and amend answered 310 for a section whose own prose is 48 and whose subsection is 255, against a declared 300 that lint passes — a verdict the author cannot act on. → §RK287
- 📋 **RK293** (deps: —) **anchors names the next address under every family and not the next family** — A reused block needs a fresh top-level to file under, and the read built for that question answers per family in an order where IX follows IV, so the maximum is not on the listing either. → §RK293

## Block D — The gate

- 💭 **RK269** (deps: —) **A block emptying is stated once to the console and recorded nowhere a later verb can read** — `ship` printed `event T282 Block AI empty`, `lint` then called the tree clean, and the repo kept an index row claiming that block active — caught only by a test of its own. → §RK269
- 📋 **RK271** (deps: —) **The capture offer closes the gate's own answer as though the tool had failed** — `_may_offer` fires on every non-zero exit but `report`, `guard` and `mcp`, so a `lint` naming one problem in CI ends with two lines inviting a capture, on the exit that is never about this tool. → §RK271

## Block E — Adoption

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK267** (deps: —) **A staleness note lists every changed module and hands relevance back** — The server appends `engine().stale` to any refusal, so one `schema.py` decided arrives naming three modules that did not, and the reader re-runs on a guess about which mattered. → §RK267
- 📋 **RK275** (deps: —) **No MCP tool asks whether git would run this driver** — `merge --check` is a pure query the server does not expose, so the agent the plugin exists for reaches it only by shelling out — the read L5 says a command should replace. → §RK275

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
- **No multi-line task line.** A task whose text wraps across paragraphs, with its deps
  on a `↳` line of their own, is a second grammar; reading only the first line would
  ship a truncated why and orphan the rest.
- **No supported Python API.** The CLI, the MCP tools and the plugin are the surface;
  `from roadkeep import Schema` is how the tests reach the vocabulary, so no `py.typed`
  ships and a rename inside the package breaks nobody.
