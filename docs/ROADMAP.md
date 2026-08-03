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

- 📋 **RK193** (deps: —) **Completing a partial rewrites the first line of an entry whose sentence runs past it** — RK179 gave the correction a span and `_complete` still calls `replace_task`, so on 10 of Shio's 12 partial entries the qualifier goes and the half's old sentence stays below it. → §RK193
- 💭 **RK195** (deps: —) **The roadmap's own amend would strand the same tail, and nobody has counted whether a line wraps there** — RK179 gave the ledger a span-aware correction and `authoring` still rewrites the first line, while both pinned roadmaps carry 0 wrapped entries — so the shape is uncounted. → §RK195
- 📋 **RK196** (deps: —) **A pointer into the strategy file survives the ship that deletes the line pointing at it** — `_dropped` asks the improvements file alone, so shipping reports "no §X.1 section" and leaves one the config declares — and `lint` exits 0, so nothing says a shipped design stayed. → §RK196
- 📋 **RK197** (deps: —) **`add` asks for a rationale section that another declared prose file already holds** — `_unresolved` reads the improvements file alone, so a line pointing into the strategy file is told its pointer resolves to nothing, and the second copy that invites is `ref.ambiguous`. → §RK197
- 📋 **RK214** (deps: —) **A ledger that declares no marker closes one of the three doors out of the roadmap** — retire refuses when [ledger] marker = false because a retired entry cannot be told from a shipped one, so a project with reconstructed history has no exit for abandoned work. → §RK214
- 📋 **RK215** (deps: —) **A top-level section's own prose cannot be corrected once it has subsections** — amend measures the whole subtree against the section limit, so a two-sentence intro reports 934 words and is refused, while the guard denies the hand-edit that would fix it. → §RK215
- 📋 **RK216** (deps: —) **A refusal named a block the caller never mentioned, and it is a prefix of theirs** — ship on a task in Block AJ refused with 'no heading declares Block A', from a list that contains AJ, so the sentence asks for a heading that is already there under another letter. → §RK216

## Block C — Query (consult without reading the file)

- 📋 **RK200** (deps: —) **Which governed files no verb wrote is answerable only by trying to end the turn** — RK175 records a digest per write and states one change once at the `Stop` hook, so the only way to ask is to be blocked — and it re-baselines as it reports, so the fact is gone. → §RK200

## Block D — The gate

- 💭 **RK212** (deps: —) **A citation of a shipped design cannot be told from a citation of one that never existed** — as_ledger keeps no pointer, so once a line is in the changelog nothing records which anchor its rationale had, and 37 such references across four trees are unreadable either way. → §RK212
- 📋 **RK213** (deps: —) **A gate that is green for whoever just built and red for a bare checkout** — lint asks whether the repository has the artefact a line names, and a build output is tracked by nobody, so an adopter's own CI has been failing on a path that is correct. → §RK213

## Block E — Adoption

- 📋 **RK103** (deps: —) **A bullet whose marker holds a space is read as prose and reported by nothing** — GitHub's `- [ ]` task list is the commonest Markdown backlog there is, and cursarei's 16 of them parse as 0 entries and 0 rejects — the silent miss the reject list exists to end. → §RK103
- 📋 **RK107** (deps: RK106 ✅) **A project that declares the format still has nothing enforcing it** — Dumont carries a roadkeep.toml and runs the gate nowhere, so what it adopted is held by the same nobody a convention is held by — Turing's own was wired in with `install` and a baseline. → §RK107
- 📋 **RK110** (deps: —) **`adopt` counts the id findings without saying they are one declaration** — The estimate names the prefix delta and the `[markers]` delta but not this one, so measuring `pad = 2` against Dumont's nine findings took the throwaway script the estimate exists to replace. → §RK110
- 📋 **RK125** (deps: —) **Declaring an unmarked ledger takes a whole verb away, and the refusal offers no way through** — Shio sets [ledger] marker = false so its 234 pre-tool entries parse, and that one line makes retire refuse every id: the adoption that made the file readable disabled a door. → §RK125
- 📋 **RK137** (deps: —) **The copied skill names a shell command that does not exist in the project it was copied into** — `install` substitutes the launcher into the hook and into the server and not into the skill's own examples, so a checkout-wired project is told to run `roadkeep`, which is on no PATH here. → §RK137
- 📋 **RK138** (deps: —) **Un-wiring a project is the hand-edit this tool exists to deny** — `install` writes four surfaces and nothing removes them, so moving a project from a checkout to the plugin means deleting a server entry and three hook entries by hand. → §RK138
- 📋 **RK139** (deps: —) **`adopt` measures the task lines and says nothing about the non-goals it will govern** — The estimate reports symptom, why and line against their limits and never the lead and reason it will hold the other bullet to, so nine findings arrived after the commitment. → §RK139
- 📋 **RK140** (deps: —) **The CI workflow `install` writes is red on its first run for every backlog with debt** — The baseline that fails on what a branch added is named in a comment and left unset, so the gate an adopter meets first is one reporting work nobody was going to redo. → §RK140
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
