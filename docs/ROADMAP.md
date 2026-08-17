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

- 📋 **RK1223** (deps: —) **block add says nothing to open when the label is in the ledger but the roadmap, where the work goes, has none** — The refusal is true per file and wrong about the move, and the verb that names the fix is a different one you reach by failing again. → §RK1223
- 📋 **RK1229** (deps: —) **A dep with a parenthesis is written, then no verb can reach the line it made unreadable** — amend accepts it, the rendered deps group closes early, and amend, retire, defer, repair and lint --fix all answer that no task carries the id. → §RK1229

## Block C — Query (consult without reading the file)

- 📋 **RK1221** (deps: —) **budget on an id the roadmap holds reads the four fields describing a line and discards them without a word** — The arm that finds the entry answers off the file, so a draft symptom or a dep passed beside an id narrows nothing and the caller reads a number believing it did. → §RK1221
- 📋 **RK1225** (deps: —) **budget publishes every width a field has and not the one sentence it accepts** — A why that fits every number budget reported is still refused by why.sentences, so the verb that exists to save a composition costs one anyway. → §RK1225
- 📋 **RK1226** (deps: —) **Nothing names the open half of a partial, only the half that shipped** — brief joins line, section and ledger but omits the recorded qualifier, so resuming a partial means subtracting one file from another to recover the remainder. → §RK1226

## Block D — The gate

- 📋 **RK1214** (deps: —) **a resolved engine that fails to import takes the whole command down instead of falling through to the next candidate** — The launcher promises a missing engine degrades to unenforced rather than to a broken session, and a checkout mid-refactor is found and then explodes. → §RK1214
- 📋 **RK1217** (deps: —) **path.missing judges a shipped entry against today's tree, so a file later moved to another repo makes history a finding** — A ledger sentence is true about the tree that shipped it, and the only door offered rewrites that sentence. → §RK1217
- 📋 **RK1222** (deps: —) **The gate reads a declared query for a grammar it cannot parse and never for a pathspec that answers about nothing** — RK1216 gave the read the words; the typo is in a governed file, and a claim nothing answers is what lint refuses for a pointer, a dead queue entry and a bad fence. → §RK1222
- 📋 **RK1228** (deps: —) **Nothing reports source changed under an open task while the line stayed open** — lint --since flags a section edited without its line but not the mirror, so work that landed and passed its tests can leave the ledger with no entry at all. → §RK1228

## Block E — Adoption

- 📋 **RK1224** (deps: —) **A refusal on one over-long field discards the section body sent with it, so the retry re-sends every word** — add validates the whole transaction and writes nothing, so a three-character why overflow cost three round trips carrying the same 250-word body. → §RK1224
- 📋 **RK1227** (deps: —) **section amend accepts prose citing an anchor that does not exist, so a docs-only commit turns an adopter's gate red** — It checks the body's length and shape and never resolves the anchors it names, so a section citing one a ship removed is written and found by running the suite. → §RK1227

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK1218** (deps: —) **add cannot carry the section it requires, so every filing is two commands with a dangling pointer between them** — add prints 'the pointer above resolves to nothing until then' and lint agrees: the roadmap is briefly in a state the project's own gate refuses, on every task filed. → §RK1218
- 📋 **RK1230** (deps: —) **Nothing tells a shell caller which engine copy is the one wired to this project** — A stale copy in a different plugins root answers plausibly instead of refusing, and the only signal is a note inside an unrelated report. → §RK1230

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

- 📋 **RK1209** (deps: —) **No test runs the commands this tool composes, so a refusal naming a call that refuses stays green** — Four tasks found one each and three wrote the same harness by hand; invocation() names the 56 sites, and what a sweep adds is filling the placeholders. → §RK1209
- 📋 **RK1220** (deps: —) **A refusal preamble is spelled with the invocation, so the test that walks the stair it prints reads it as a step** — Any stderr line starting with the invocation is taken for a command, and where the console script is on PATH so is the preamble — green by whether one is installed. → §RK1220

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
