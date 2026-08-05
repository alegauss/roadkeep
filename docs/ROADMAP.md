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

- 📋 **RK310** (deps: —) **A design section can carry a stale premise and ship drops it in silence** — Twice in one block a section argued from a fact that had stopped being true, and the only reader who could find out is whoever claims the task years later. → §RK310
- 📋 **RK311** (deps: —) **A body refused for one word is discarded whole, so the check costs what the limit saves** — Fifteen refusals in one session, three of them over one or two words, and no add --check exists to price a draft short of attempting the write. → §RK311
- 📋 **RK312** (deps: —) **The refusal that demands a ref names nothing that would produce one** — ref.missing states the rule while anchors answers it, and which family a block's prose lives under is derivable from no command at all. → §RK312

## Block C — Query (consult without reading the file)

- 📋 **RK303** (deps: —) **The section budget picks the first of two prose files declaring one anchor, where every other reader refuses** — It answered improvements about an address strategy declares too, and show calls that state a pointer resolving to neither — so a limit is priced for an unreachable section. → §RK303

## Block D — The gate

## Block E — Adoption

- 📋 **RK305** (deps: —) **The scheme suggestion is suppressed by a majority that shipping erodes** — adopt hides it only while the declared scheme out-counts the other, and this repo's id-anchored sections are deleted at every ship, so a conforming file is told to switch once enough work lands. → §RK305
- 📋 **RK315** (deps: —) **A test asserting on this repository's own docs fails when another session writes them mid-run** — It read docs/IMPROVEMENTS.md live and failed once in three identical runs while a second session shipped into that file, so the red said nothing about the code under test. → §RK315

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK318** (deps: —) **The command the staleness note tells the reader to run is not the act the tool was called for** — It names Tool.command and drops the always flags that make the tool that act, so a claim refusal advises brief, which reads and takes no line. → §RK318
- 📋 **RK319** (deps: —) **A branch that refuses --json cannot be served at all, and nothing states the coupling** — argv appends --json to every call, so RK317's refusal makes a tool over merge servable only while it always-passes --check, and no test holds that. → §RK319

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
