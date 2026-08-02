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
- 💭 **RK115** (deps: —) **Where a heading's region ends is re-derived at every call site, under two rules that already differ** — `_span` and `_placement` stop at the next same-or-higher heading while `anchored` and `_after_preamble` stop at any heading, and the one reader of a file is meant to be Document. → §RK115
- 📋 **RK116** (deps: —) **A second write to a governed file erases the first one's line and both commands exit 0** — `Document` reads every byte and `save` writes every byte back with nothing checking the file is still the one that was read, so two agents in one checkout lose a line silently. → §RK116
- 📋 **RK117** (deps: RK116) **Two adds started together mint the same id, and the gate reports it only once both lines exist** — `next_id` derives one past the highest anywhere and nothing holds that maximum between the scan and the write, so the id is a claim two processes can both make. → §RK117
- 📋 **RK118** (deps: —) **A reader can load a governed file truncated, and an interrupted ship leaves two of its three files written** — `save` truncates the target before it fills it and a departure writes three files in sequence, so an interrupted write leaves the state `Closure` was built to repair. → §RK118

## Block B — Authoring (insert, never hand-edit)

- 📋 **RK113** (deps: —) **renumber renames a section's heading and leaves the anchors of everything nested under it** — `renumber RK1 --to RK9` rewrote `§RK1` and left `§RK1.1` claiming a task the backlog no longer has, under a heading that names RK9, and lint called the file clean. → §RK113
- 📋 **RK120** (deps: RK113) **Two branches each spend the same id, and the merge git produces is a conflict in a file only this tool may write** — Every add appends inside the same block heading, so parallel worktrees collide on almost every task and resolving it by hand is the edit the hook denies. → §RK120

## Block C — Query (consult without reading the file)

- 📋 **RK119** (deps: RK117) **Every agent asking what to work on is handed the same line, including one another agent already started** — Tier 1 prefers an in-progress line so one worker finishes what they started, and the file has no way to say a task is taken, so a second caller is sent at work under way. → §RK119

## Block D — The gate

- 📋 **RK104** (deps: —) **Nothing gates the README block this tool writes, so a stale restatement passes lint** — `export --readme` is the one write no gate holds: a pytest fixture catches it here and an adopting project has none, so the derived table drifts from the files it was derived from. → §RK104
- 📋 **RK105** (deps: —) **A concurrent edit in another repository turns this project's suite red** — The round-trip property reads Shio's and Turing's working trees, so a run went red for a change neither this commit nor this repository made, and a red nobody caused is a red nobody reads. → §RK105
- 📋 **RK114** (deps: —) **A subsection whose task is gone is exempt from the ownership check that would report it** — `_owners` matches the anchor against the id pattern, so `§RK34.1` is read as outline prose like `§0.1` and belongs to nobody — the exemption that let a half-renamed subtree lint clean. → §RK114

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
