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

- 📋 **RK109** (deps: —) **The id's shape is declared once and read by two parsers that answer differently** — `id_pattern` refuses the `D1` that `number_of` reads as 1, and the sub-letter half is a flag four call sites pass by hand, so a fifth caller is a sort nobody checks. → §RK109

## Block B — Authoring (insert, never hand-edit)

- 💭 **RK112** (deps: RK78 ✅) **section drop deletes a section an open line points at** — RK78 refuses when a NESTED section has another owner, and the standalone verb never asks who points at the anchor it was given. → §RK112

## Block C — Query (consult without reading the file)

## Block D — The gate

- 📋 **RK104** (deps: —) **Nothing gates the README block this tool writes, so a stale restatement passes lint** — `export --readme` is the one write no gate holds: a pytest fixture catches it here and an adopting project has none, so the derived table drifts from the files it was derived from. → §RK104
- 📋 **RK105** (deps: —) **A concurrent edit in another repository turns this project's suite red** — The round-trip property reads Shio's and Turing's working trees, so a run went red for a change neither this commit nor this repository made, and a red nobody caused is a red nobody reads. → §RK105

## Block E — Adoption

- 📋 **RK103** (deps: —) **A bullet whose marker holds a space is read as prose and reported by nothing** — GitHub's `- [ ]` task list is the commonest Markdown backlog there is, and cursarei's 16 of them parse as 0 entries and 0 rejects — the silent miss the reject list exists to end. → §RK103
- 📋 **RK107** (deps: RK106 ✅) **A project that declares the format still has nothing enforcing it** — Turing and Dumont each carry a roadkeep.toml and neither runs the gate in CI, so what they adopted is held by the same nobody a convention is held by. → §RK107
- 📋 **RK110** (deps: —) **`adopt` counts the id findings without saying they are one declaration** — The estimate names the prefix delta and the `[markers]` delta but not this one, so measuring `pad = 2` against Dumont's nine findings took the throwaway script the estimate exists to replace. → §RK110

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK111** (deps: —) **The MCP write path cannot write an id the deriver never mints** — `add --id` is withheld because a chosen id is what a schema cannot check, but a sub-letter is derived by nothing, so a project declaring `[ids] suffix` has a shape only the CLI can write. → §RK111

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
