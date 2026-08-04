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

- 📋 **RK244** (deps: —) **A paused id cannot be named as what supersedes a retired line** — `retire --superseded-by` reads the roadmap and the ledger, so the deferred store is invisible to it and a live findable id is refused as `in neither file`, which is two false claims. → §RK244
- 📋 **RK249** (deps: —) **The add answer names the id it derived and not the pointer** — The payload carries `rendered` and a `needs` command, so the anchor a follow-up `section add` takes is readable only by parsing one of those, and by neither where a section was written. → §RK249
- 📋 **RK257** (deps: —) **A ship refusal names the missing block heading but not the verb that writes it** — It lists every declared label and warns about the prefix, so an author whose roadmap declares the block learns nothing about which file lacks the heading or that block add writes it. → §RK257
- 📋 **RK262** (deps: —) **A section add writes a heading ship will later decline to delete** — The title is taken verbatim, so one without the id it was written for stops binding to the task, and ship keeps the rationale as prose belonging to none. → §RK262

## Block C — Query (consult without reading the file)

- 📋 **RK200** (deps: —) **Which governed files no verb wrote is answerable only by trying to end the turn** — RK175 records a digest per write and states one change once at the `Stop` hook, so the only way to ask is to be blocked — and it re-baselines as it reports, so the fact is gone. → §RK200
- 📋 **RK245** (deps: —) **The number that binds an amend is the one figure `budget` states only in characters** — A line reads `182 written, 18 left  aim 30 words`, so the only unit the author can count names the whole field while the room they actually have is 18 characters. → §RK245
- 📋 **RK247** (deps: —) **Nothing says which outline anchors history still cites** — `section add` lists only what exists, so reopening a shipped family reuses an anchor the changelog still points at and silently rewrites its meaning. → §RK247
- 📋 **RK264** (deps: —) **The cost query spends 95% of its answer on records its own percentiles summarise** — `weight` ships 250 per-task entries beside six percentiles, 22.7k of 23.7k characters, and `--block F` only moves that to 89% — so the read priced to save context is the one that spends it. → §RK264
- 📋 **RK265** (deps: —) **budget omits the pointer under an outline ref scheme, so it over-reports the room by the anchor width** — It answered 182 characters left for a why `add` then refused at 174, the 8 being ` → §XX.2` — a limit found after the prose exists, which this verb exists to prevent. → §RK265

## Block D — The gate

- 📋 **RK239** (deps: —) **Two prose files declaring one anchor is silent until a line points at it** — `ref.ambiguous` is reported from the pointer end alone, so 12 of Turing 13 doubled anchors pass a gate four verbs already decline to resolve them by. → §RK239
- 📋 **RK263** (deps: —) **A test asserting about the live checkout fails the same way whether code or the tree moved** — Six failed and then 1940 passed on unchanged source, the six being exactly the ones reading this repository, so git activity beside a run is indistinguishable from a defect. → §RK263
- 📋 **RK268** (deps: —) **A cached derivation survives the test that monkeypatched what it read** — Six process-lifetime caches are cleared by hand at call sites with no fixture, so a test failing before its trailing `cache_clear` leaves later ones asserting about a `tmp_path` that is gone. → §RK268
- 💭 **RK269** (deps: —) **A block emptying is stated once to the console and recorded nowhere a later verb can read** — `ship` printed `event T282 Block AI empty`, `lint` then called the tree clean, and the repo kept an index row claiming that block active — caught only by a test of its own. → §RK269
- 📋 **RK271** (deps: —) **The capture offer closes the gate's own answer as though the tool had failed** — `_may_offer` fires on every non-zero exit but `report`, `guard` and `mcp`, so a `lint` naming one problem in CI ends with two lines inviting a capture, on the exit that is never about this tool. → §RK271

## Block E — Adoption

- 📋 **RK276** (deps: —) **One write reports a skip on only one of its two surfaces** — `install --register-merge` prints added and present but not `left_alone`, so adoption hides the file `merge --register` names as skipped — under a comment claiming the two print the same lines. → §RK276
- 📋 **RK277** (deps: —) **The check demands a driver in a repository that routes nothing to it** — `--check` reads the two halves independently, so where every governed file is claimed by another driver the config half still exits 1 asking for a value no merge would ever reach. → §RK277

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
