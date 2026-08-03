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

- 📋 **RK131** (deps: —) **The check that a transaction's files have not moved is taken before writes that take it again** — `assert_all_current` reads all three and every `save` reads its own again, so a writer landing between the two is refused on the second file after the first one has already been written. → §RK131
- 📋 **RK133** (deps: —) **Every part of a split delivery carries the base id, so a four-step ship is four contradictions** — RK121 reads the part and does not carry it into identity, so Shio's four SH348 entries became six duplicate findings and three two-files findings against correct history. → §RK133

## Block B — Authoring (insert, never hand-edit)

- 📋 **RK169** (deps: —) **section drop deletes rationale a live line points at, when the anchor is a bullet** — The guard reads the sections under the anchor, so an outline project addressing prose as `- **XIV.8.7 — …**` has its live design deleted with the shipped parent and no refusal. → §RK169

## Block C — Query (consult without reading the file)

- 📋 **RK174** (deps: —) **Listing the tools rebuilds the whole CLI parser fifty-two times and costs a sixth of a second** — `_subparser` calls `build_parser` per lookup and each descriptor needs two — the schema and whether the tool writes — so a client's first message pays 165ms rebuilding what never changed. → §RK174

## Block D — The gate

- 📋 **RK104** (deps: —) **Nothing gates the README block this tool writes, so a stale restatement passes lint** — `export --readme` is the one write no gate holds: a pytest fixture catches it here and an adopting project has none, so the derived table drifts from the files it was derived from. → §RK104
- 📋 **RK105** (deps: —) **A concurrent edit in another repository turns this project's suite red** — The round-trip property reads Shio's and Turing's working trees, so a run went red for a change neither this commit nor this repository made, and a red nobody caused is a red nobody reads. → §RK105
- 📋 **RK114** (deps: —) **A subsection whose task is gone is exempt from the ownership check that would report it** — `_owners` matches the anchor against the id pattern, so `§RK34.1` is read as outline prose like `§0.1` and belongs to nobody — the exemption that let a half-renamed subtree lint clean. → §RK114
- 📋 **RK122** (deps: RK121 ✅) **id.two-files calls a correct half-shipped state a contradiction** — Open in the roadmap and recorded in the ledger is exactly what a partial is, so Shio's SH238 is reported for spelling it plainly while six that hid it behind a parenthetical are not. → §RK122
- 📋 **RK132** (deps: —) **The README block is read and written back with nothing checking the file did not move** — `_splice_into` opens the file, replaces what is between the markers and writes, holding no `Document`, so the one write this tool makes outside a governed file is the one that skips the check. → §RK132
- 📋 **RK134** (deps: —) **A section that four open lines point at is reported stale, and the drop it names is refused** — `_unowned` decides from the ids in the heading while `section drop` decides from the pointers that resolve, so the only door the finding offers is the one the tool closes. → §RK134
- 📋 **RK135** (deps: —) **A rationale section whose task points at a different one is reported by nothing** — `section.orphan` clears because the id in the title is open and no check asks whether the pointer naming it resolves here, so a superseded draft lints clean for ever. → §RK135
- 📋 **RK136** (deps: —) **The section budget charges a measured table exactly what it charges a paragraph** — `words` splits the whole body on whitespace, so a section that is 230 of its 269 words of measurement is judged by a limit written for prose and offered a remedy that fits neither. → §RK136
- 📋 **RK146** (deps: —) **A tab is reported as an invisible character and repaired by nothing, for ever** — suspect reads Unicode categories and a tab is Cc, while --fix withholds it because indentation is part of the model — so a file with one carries a finding no verb can clear. → §RK146
- 📋 **RK147** (deps: —) **A prose file's own limits are enforced by the gate and ignored by the write that creates the text** — section add and amend check the body against config.schema while lint charges schema_for(role), so a project declaring [limits.improvements] has a budget only the backstop holds. → §RK147
- 📋 **RK172** (deps: —) **A pointer resolving to a section in the strategy file is reported as resolving to nothing** — Resolution is charged against the improvements file alone, so Turing's six GEO lines point at STRATEGY `§X.3`/`§X.4`, which exist, and the gate calls the correct pointer unresolved. → §RK172
- 📋 **RK173** (deps: —) **A path a ledger entry names relative to its own module is reported as not in the repository** — Every path is resolved from the repository root, so Turing's `./package.json` and `scripts/prerender.mjs` are reported missing while both exist under the frontend app the entry is about. → §RK173

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

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK175** (deps: —) **An approved shell write leaves a valid line and no record of who wrote it** — The guard asks and the user may say yes, and `review` narrows lint to changed lines, so a `sed` whose output conforms is indistinguishable from a verb's write. → §RK175
- 📋 **RK176** (deps: —) **Widening the matcher to Bash spawns an interpreter per shell command and nothing measured it** — The five decisions in `guarding` were arranged to avoid exactly this cost, and the trade was accepted on an argument rather than on a number. → §RK176
- 📋 **RK177** (deps: —) **The tool list can change mid-session and the client is never told, so it validates against a cached schema** — The config is re-read per message on purpose, so `[ids] suffix` added mid-session changes which arguments exist, and no `notifications/tools/list_changed` is ever sent. → §RK177

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
