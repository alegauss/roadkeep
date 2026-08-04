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

- 📋 **RK280** (deps: —) **Two sessions each ship a commit carrying the other's code** — `claim` holds a roadmap line and the lock holds a write, but the commit step is guarded by nothing, so RK244 and RK279 each landed carrying the other's source and tests. → §RK280

## Block C — Query (consult without reading the file)

- 📋 **RK265** (deps: —) **budget omits the pointer under an outline ref scheme, so it over-reports the room by the anchor width** — It answered 182 characters left for a why `add` then refused at 174, the 8 being ` → §XX.2` — a limit found after the prose exists, which this verb exists to prevent. → §RK265
- 📋 **RK283** (deps: —) **budget answers for the task line only, so the two largest prose limits are discoverable only by failing** — A non-goal why took two refusals at 286 and 234 against 200, and a section body one at 366 words against 300 — the verdict-after-the-prose this verb exists to prevent. → §RK283
- 📋 **RK287** (deps: —) **A section's word count includes its subsections, so it names a figure no limit is measured against** — show and amend answered 310 for a section whose own prose is 48 and whose subsection is 255, against a declared 300 that lint passes — a verdict the author cannot act on. → §RK287
- 📋 **RK293** (deps: —) **anchors names the next address under every family and not the next family** — A reused block needs a fresh top-level to file under, and the read built for that question answers per family in an order where IX follows IV, so the maximum is not on the listing either. → §RK293

## Block D — The gate

- 📋 **RK239** (deps: —) **Two prose files declaring one anchor is silent until a line points at it** — `ref.ambiguous` is reported from the pointer end alone, so 12 of Turing 13 doubled anchors pass a gate four verbs already decline to resolve them by. → §RK239
- 📋 **RK263** (deps: —) **A test asserting about the live checkout fails the same way whether code or the tree moved** — Six failed and then 1940 passed on unchanged source, the six being exactly the ones reading this repository, so git activity beside a run is indistinguishable from a defect. → §RK263
- 📋 **RK268** (deps: —) **A cached derivation survives the test that monkeypatched what it read** — Six process-lifetime caches are cleared by hand at call sites with no fixture, so a test failing before its trailing `cache_clear` leaves later ones asserting about a `tmp_path` that is gone. → §RK268
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
