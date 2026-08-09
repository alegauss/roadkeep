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

- 📋 **RK438** (deps: —) **A write's event line calls a block empty that every query in the same tool calls finished** — The event asks the roadmap alone whether anything is filed under the label and the four-state answer asks the ledger too, so one word carries two meanings. → §RK438

## Block C — Query (consult without reading the file)

- 📋 **RK441** (deps: —) **Three copies price a lexical duplicate match at 33rd, and re-measuring this ledger does not reproduce it** — BM25 over the 426 shipped symptoms ranks all four superseded-by pairs at #1 to #3, so the figure the refusal argues from is wrong even where the refusal is right. → §RK441
- 📋 **RK442** (deps: RK441) **delivered prints a whole block's ledger to answer whether one proposal collides with it** — The read before an add costs 103 lines and 9773 bytes on Block B, where the five nearest entries by word overlap held every duplicate this ledger records. → §RK442

## Block D — The gate

- 📋 **RK439** (deps: —) **A sub-heading nested under a block's own heading is read as a second declaration of that block** — Shio's ledger files 91 entries under eight '### Block K follow-ups' sub-headings, and block.repeated refuses every write over a nesting whose only other shape strands them. → §RK439

## Block E — Adoption

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK443** (deps: —) **A stored capture that never reached the verb replays as reproducing the symptom it was filed under** — The verdict is the recorded exit code turning up again, which a usage refusal always does, so the triage command says `still reproduces` about evidence the capture calls unreached. → §RK443

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
- **No supported Python API.** The CLI, the MCP tools and the plugin are the surface;
  `from roadkeep import Schema` is how the tests reach the vocabulary, so no `py.typed`
  ships and a rename inside the package breaks nobody.
- **No effort or size field.** Nothing can verify a letter, `pick`'s every tier is a
  fact, and what an agent pays is context — median to p90, files vary 1.4× against lines
  2.7×, so the letter prices the axis nobody pays.
