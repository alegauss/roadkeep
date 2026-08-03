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

- 📋 **RK191** (deps: —) **The refusal on a second partial names the entry in the way, not the id the step needs** — `_partial` answers a second `ship --part` with the line already recorded, and Shio settled in SH361 that a delivered step gets its own id, so the caller is left to invent it. → §RK191

## Block C — Query (consult without reading the file)

- 📋 **RK174** (deps: —) **Listing the tools rebuilds the whole CLI parser fifty-two times and costs a sixth of a second** — `_subparser` calls `build_parser` per lookup and each descriptor needs two — the schema and whether the tool writes — so a client's first message pays 165ms rebuilding what never changed. → §RK174
- 📋 **RK186** (deps: —) **`brief` reports a pointer into the strategy file as resolving to nothing** — `showing._rationale` reads the improvements file alone, so RK172's widening stopped at the gate and the call that starts a task denies a design the file declares. → §RK186
- 📋 **RK190** (deps: —) **A line's prose budget is discoverable only by writing a sentence and being refused** — RK183 derives what a line has left for prose from fields `add` knows before the first word exists, and no command answers it, so the number arrives as a refusal. → §RK190

## Block D — The gate

- 📋 **RK188** (deps: —) **Every write stales the derived README block, so the gate fails until somebody remembers `export`** — RK104 made `lint` hold the block and no verb refreshes it, so ten consecutive claims and ships each left this repository failing its own gate on a file no task touched. → §RK188
- 💭 **RK189** (deps: —) **A path claim is satisfied by a file of that name anywhere in the tree, and the floor was never measured** — RK173 indexes every tail of every tracked path, so a one-segment token resolves against any file sharing its name, and what that silences was argued rather than counted. → §RK189
- 📋 **RK192** (deps: —) **A pinned corpus hands out a config whose file reads go to the live tree instead** — RK105 pinned every corpus assertion and `corpora.config` still roots at the checkout, so a read through it takes today's bytes while the helper beside it takes the revision. → §RK192

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
- 📋 **RK185** (deps: RK183 ✅) **The budget an author is given is in characters, the one unit a model cannot count** — The MCP field schema and the skill publish 120 and 200, so a first attempt is a guess and the retries converge by feedback, where a word count would land inside on the first call. → §RK185

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
