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

- 📋 **RK201** (deps: —) **A length refusal states its surplus in the one unit the author composing the retry cannot count** — RK185 published every budget in words as well as characters and left RK184's refusal in characters alone, so the retry after an overrun is the guess the aim exists to remove. → §RK201

## Block B — Authoring (insert, never hand-edit)

- 📋 **RK229** (deps: —) **`defer` reports the carried design as kept in a file it never asked declares it** — `pause.carried` is the anchor alone, so the CLI prints the improvements path beside it — the assumption RK196 removed from the ship, still made by the door that keeps a section. → §RK229
- 📋 **RK230** (deps: —) **`add --section` cannot write into the only prose file a project declares** — `_with_section` names the improvements role outright, so a project declaring strategy alone is refused `NoProseFile` and left with the two commands and the dangling pointer RK93 removed. → §RK230
- 📋 **RK231** (deps: —) **A paused task's rationale cannot be corrected, the door refusing it as prose nothing owns** — `_task_for` reads the roadmap alone, so `section amend RK1` on a deferred line answers `anchor.unknown` — no open task points at the section RK96 deliberately kept for it. → §RK231
- 💭 **RK232** (deps: —) **Writer and gate part company again on an anchor two prose files declare** — `_pointed_at` asks only whether a line names the anchor, while `lint` charges own prose where two roles declare one — so RK215's agreement holds everywhere except the state `ref.ambiguous` reports. → §RK232

## Block C — Query (consult without reading the file)

- 📋 **RK200** (deps: —) **Which governed files no verb wrote is answerable only by trying to end the turn** — RK175 records a digest per write and states one change once at the `Stop` hook, so the only way to ask is to be blocked — and it re-baselines as it reports, so the fact is gone. → §RK200

## Block D — The gate

## Block E — Adoption

- 📋 **RK148** (deps: —) **install wires four surfaces and leaves the merge driver to whoever remembers it** — merge --register is the opt-in RK120 shipped, and nothing offers it during adoption — so a wired project gets the tools, the guard and the skill, and its first parallel branch still conflicts by hand. → §RK148
- 💭 **RK205** (deps: —) **The package publishes annotations that no checker is allowed to read** — Every module is annotated and `pyproject.toml` ships no `py.typed`, so PEP 561 makes a consumer's checker ignore all of it — and RK199 dropped a TYPE_CHECKING block on exactly that ground. → §RK205

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

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
