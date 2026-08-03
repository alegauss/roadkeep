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

- 📋 **RK143** (deps: —) **A ledger entry filed under the wrong block can be corrected by no verb at all** — record amend leaves the block out because filing an entry elsewhere is a move, and record drop refuses unless the id is stated twice, so the only route left is the hand-edit the hook denies. → §RK143
- 📋 **RK144** (deps: —) **Declaring a block writes three files and nothing takes the heading back out** — block add is the only verb that writes a heading, so a label opened by mistake or emptied by a retirement leaves a heading in every governed file that only a hand-edit removes. → §RK144
- 📋 **RK145** (deps: —) **A block can only be opened last, and where it sits is what every ordered answer reads** — block add places the heading after the last block's subtree, so a phase belonging between two existing ones can only be appended — and the order a list reports is the headings' own. → §RK145

## Block C — Query (consult without reading the file)

- 📋 **RK156** (deps: —) **Renaming an id drops the claim on that line, so work somebody is holding is offered again** — `renumber` moves the line, its section and every dep naming it, and the registry is keyed by id — so the old entry stops matching and the new id reads as started work nobody holds. → §RK156

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

## Block E — Adoption

- 📋 **RK103** (deps: —) **A bullet whose marker holds a space is read as prose and reported by nothing** — GitHub's `- [ ]` task list is the commonest Markdown backlog there is, and cursarei's 16 of them parse as 0 entries and 0 rejects — the silent miss the reject list exists to end. → §RK103
- 📋 **RK107** (deps: RK106 ✅) **A project that declares the format still has nothing enforcing it** — Turing and Dumont each carry a roadkeep.toml and neither runs the gate in CI, so what they adopted is held by the same nobody a convention is held by. → §RK107
- 📋 **RK110** (deps: —) **`adopt` counts the id findings without saying they are one declaration** — The estimate names the prefix delta and the `[markers]` delta but not this one, so measuring `pad = 2` against Dumont's nine findings took the throwaway script the estimate exists to replace. → §RK110
- 📋 **RK125** (deps: —) **Declaring an unmarked ledger takes a whole verb away, and the refusal offers no way through** — Shio sets [ledger] marker = false so its 234 pre-tool entries parse, and that one line makes retire refuse every id: the adoption that made the file readable disabled a door. → §RK125
- 📋 **RK137** (deps: —) **The copied skill names a shell command that does not exist in the project it was copied into** — `install` substitutes the launcher into the hook and into the server and not into the skill's own examples, so a checkout-wired project is told to run `roadkeep`, which is on no PATH here. → §RK137
- 📋 **RK138** (deps: —) **Un-wiring a project is the hand-edit this tool exists to deny** — `install` writes four surfaces and nothing removes them, so moving a project from a checkout to the plugin means deleting a server entry and three hook entries by hand. → §RK138
- 📋 **RK139** (deps: —) **`adopt` measures the task lines and says nothing about the non-goals it will govern** — The estimate reports symptom, why and line against their limits and never the lead and reason it will hold the other bullet to, so nine findings arrived after the commitment. → §RK139
- 📋 **RK140** (deps: —) **The CI workflow `install` writes is red on its first run for every backlog with debt** — The baseline that fails on what a branch added is named in a comment and left unset, so the gate an adopter meets first is one reporting work nobody was going to redo. → §RK140
- 📋 **RK148** (deps: —) **install wires four surfaces and leaves the merge driver to whoever remembers it** — merge --register is the opt-in RK120 shipped, and nothing offers it during adoption — so a wired project gets the tools, the guard and the skill, and its first parallel branch still conflicts by hand. → §RK148

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK111** (deps: —) **The MCP write path cannot write an id the deriver never mints** — `add --id` is withheld because a chosen id is what a schema cannot check, but a sub-letter is derived by nothing, so a project declaring `[ids] suffix` has a shape only the CLI can write. → §RK111
- 📋 **RK128** (deps: —) **The guard denies Edit and Write and answers silence to a shell command writing the same file** — A PreToolUse payload naming Bash is passed through whatever the command does, so sed, python -c or a heredoc rewrites a governed file with no refusal and no record. → §RK128
- 📋 **RK155** (deps: —) **A tool call answers with the code the session started, so a refusal can name a key the config declares** — The stdio server imports the package once per session, so a new config key or an upgrade is invisible to every tool while the CLI beside it agrees with the file. → §RK155

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
