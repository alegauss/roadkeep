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

## Block C — Query (consult without reading the file)

- 📋 **RK1211** (deps: —) **anchors --next on an empty outline names a roman first address by hand, on a project that may number decimally** — The file has no family to read a system off, which is why next_family answers None there; the sentence beside it guesses anyway, and taking it mixes two systems. → §RK1211
- 📋 **RK1216** (deps: —) **remaining reports 0 sites for a pathspec that matched no files, which is what it reports for work that is finished** — The count is the headline and the file tally is beside it, so a mistyped glob reads as a migration complete rather than as a query that never ran. → §RK1216

## Block D — The gate

- 📋 **RK1192** (deps: —) **A launcher and skill older than the version answering are reported by nothing the gate runs** — `install --check` answers it and is a command nobody thinks to run; lint fires every turn through the Stop hook, and a stale launcher is the state that leaves a session with no door in. → §RK1192
- 📋 **RK1202** (deps: —) **guard exits 0 and prints nothing on a payload it could not parse, which is the answer it gives for allowed** — A gate whose refusal and whose failure are the same silence cannot be told apart by testing it, so a probe that misencodes stdin reads as proof the guard is absent. → §RK1202
- 📋 **RK1203** (deps: —) **lint offers amend as the door for a path.missing on a changelog line, and amend refuses every shipped id** — The only remedy named for a ledger entry naming a moved path is a verb that cannot edit the ledger, so the finding has no reachable fix. → §RK1203
- 📋 **RK1206** (deps: —) **Under an outline, the ref.unresolved remedy names the task id where the missing section is the anchor the line points at** — The finding prints the anchor and the command under it prints the id, so running it writes a section the line does not point at. → §RK1206
- 📋 **RK1214** (deps: —) **a resolved engine that fails to import takes the whole command down instead of falling through to the next candidate** — The launcher promises a missing engine degrades to unenforced rather than to a broken session, and a checkout mid-refactor is found and then explodes. → §RK1214
- 📋 **RK1217** (deps: —) **path.missing judges a shipped entry against today's tree, so a file later moved to another repo makes history a finding** — A ledger sentence is true about the tree that shipped it, and the only door offered rewrites that sentence. → §RK1217

## Block E — Adoption

- 📋 **RK1193** (deps: —) **Every adopting repository has to write its own installer to pin the engine it runs** — The launcher resolves an engine but nothing vendors one, so two repos now carry the same 147-line script and it will drift. → §RK1193
- 📋 **RK1200** (deps: —) **The committed launcher reads ROADKEEP_HOME verbatim and lists no candidate inside the repository** — install writes ${CLAUDE_PROJECT_DIR} into every hook command it emits, and a project pointing that same spelling at a vendored copy silently gets the sibling checkout instead. → §RK1200

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK1218** (deps: —) **add cannot carry the section it requires, so every filing is two commands with a dangling pointer between them** — add prints 'the pointer above resolves to nothing until then' and lint agrees: the roadmap is briefly in a state the project's own gate refuses, on every task filed. → §RK1218

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

- 📋 **RK1209** (deps: —) **No test runs the commands this tool composes, so a refusal naming a call that refuses stays green** — Four tasks found one each and three wrote the same harness by hand; invocation() names the 56 sites, and what a sweep adds is filling the placeholders. → §RK1209

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
