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

- 📋 **RK5** (deps: RK1 ✅, RK2 ✅, RK3 ✅) **Writing the line by hand is where the prose leaks in** — `add` takes the fields, refuses over-length at input, renders the canonical line and inserts it under its block. → §RK5
- 📋 **RK6** (deps: RK5) **Shipping a task is four edits across three files, so one is always missed** — `ship` moves the entry to the changelog under its block, drops its improvements section, and leaves the roadmap a pointer or nothing. → §RK6
- 📋 **RK7** (deps: RK5) **Two files can disagree about one task's status** — `status` writes the marker in the roadmap only, and fails if a sibling file carries one. → §RK7
- 📋 **RK8** (deps: RK6) **A dep annotation goes stale the moment its target ships** — derive the `(deps: RK1 ✅)` markers on every write so a shipped dep never reads as pending. → §RK8
- 📋 **RK9** (deps: RK5) **The four files are not four of the same thing, and prose has no line to validate** — strategy and improvements are sections, not bullets, so `section` governs them by heading and word budget. → §RK9

## Block C — Query (consult without reading the file)

- 📋 **RK10** (deps: RK2 ✅) **Counting a backlog by grep silently drops the lines it fails to match** — `list` and `stats` report per block and marker with `--json`, and `audit` prints every marker-bearing line *not* counted, with the reason. → §RK10
- 📋 **RK11** (deps: RK10) **Picking work means reading the whole file to find one task whose deps are shipped** — `pick` applies the priority queue, then the lowest id with satisfied deps, and prints why it chose that one. → §RK11
- 📋 **RK12** (deps: RK2 ✅) **A task's design lives in a second file and nothing joins them** — `show` prints the line, its improvements section and its spec path together. → §RK12
- 📋 **RK13** (deps: RK10) **A blocked task looks identical to a ready one, and one that unblocks half the backlog to one that unblocks nothing** — `deps` resolves the graph, names the blocker chain, detects a cycle, and counts what shipping each task unblocks. → §RK13
- 📋 **RK29** (deps: RK11, RK12) **Starting a task costs reading two whole files to learn one line's worth of context** — one call returns the line, its rationale, its deps' status and the paths it touches, which is the entire cost of starting work for an agent. → §RK29
- 📋 **RK32** (deps: RK2 ✅, RK4 ✅) **An id that exists in neither file was retired for a reason nobody recorded** — a line leaves by three doors and only shipping is recorded, so mark a superseded id at the moment it is replaced and resolve the unrecorded gaps against the commit that deleted them. → §RK32

## Block D — The gate

- 📋 **RK14** (deps: RK1 ✅, RK2 ✅) **A format that is documented but not enforced is a format that drifts** — `lint` validates every line against the schema and exits non-zero, which is what makes it a gate rather than advice. → §RK14
- 📋 **RK15** (deps: RK14) **A pointer to a section that does not exist reads as a design that does** — resolve every `→ §RK<n>` against the improvements file and every spec path against disk. → §RK15
- 📋 **RK16** (deps: RK14) **A report of ninety-two violations is a report nobody acts on** — `lint --fix` normalizes what is mechanical (ordering, dep markers, whitespace) and reports only what needs a human decision. → §RK16
- 📋 **RK17** (deps: RK14) **A gate that runs only on a developer's machine is not a gate** — ship a GitHub Action and a pre-commit hook that both call the same exit code. → §RK17
- 📋 **RK30** (deps: RK14) **The instruction file loaded every turn has a budget nothing enforces** — `agents.md` reached 186 KB in Shio under exactly this rule, so the gate checks the declared line and byte budget of every always-loaded file. → §RK30
- 📋 **RK34** (deps: RK14) **An invisible character reports a visible error about something else** — a no-break space renders as a space and a variation selector renders as nothing, so the gate names the codepoint and its offset instead of the downstream violations it caused. → §RK34
- 📋 **RK35** (deps: RK14) **A dep on a range or a block hides how much work it actually names** — `Block P` resolved to 48 open tasks in Shio, so a reader who trusts the annotation is reading one dep where the graph holds dozens. → §RK35
- 📋 **RK36** (deps: RK14, RK31 ✅) **A rationale section can gain a requirement the line carrying its status never mentions** — the section is deleted on ship and the line is the only thing `pick` reads, so the gate flags a commit that edits §RK<n> without touching RK<n>. → §RK36

## Block E — Adoption

- 📋 **RK18** (deps: RK3 ✅, RK14) **A tool that requires an empty repo cannot be adopted by the repo that needs it** — `init` scaffolds the files and config, and `adopt` reports what an existing backlog must change to pass. → §RK18
- 📋 **RK19** (deps: RK18) **Installing from a git clone keeps a standard local** — publish to PyPI so `uvx roadmap-lint` runs with no checkout. → §RK19
- 💭 **RK20** (deps: RK19, RK16) **Shio's 92 active lines average 142 words against a one-sentence rule** — migrating a real backlog is the only test of whether the schema fits a live project. → §RK20
- 💭 **RK21** (deps: RK20) **A standard adopted by one project is a preference** — roll out to Turing, Dumont and Cursarei, each with its own `roadmap.toml`. → §RK21

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK22** (deps: RK5, RK14) **An agent can hand-edit the file the CLI is supposed to own** — a `PreToolUse` hook that denies `Edit`/`Write` on the governed files and names the command to call instead is the only barrier an agent cannot route around. → §RK22
- 📋 **RK23** (deps: RK22) **Rules resident every turn spend the budget they exist to protect** — package the format as a skill with trigger phrases so it loads when a governed file is in play, and not before. → §RK23
- 📋 **RK24** (deps: RK5, RK10) **Shelling out puts argument names in prose, where they are guessed** — expose `add`/`ship`/`pick`/`lint` as MCP tools so the field schema *is* the tool's input schema. → §RK24
- 📋 **RK25** (deps: RK23) **A human driving the same standard should not have to learn the CLI** — `/roadkeep:add`, `/roadkeep:ship`, `/roadkeep:pick` and `/roadkeep:lint` over the one engine. → §RK25
- 💭 **RK26** (deps: RK22, RK19) **A plugin installed by hand is a plugin one project has** — publish a `marketplace.json` so `/plugin install` reaches it. → §RK26

## Non-goals

Deliberately **not** built — check this list before proposing work:

- **No web UI and no server.** Files and a CLI. The store is the repository.
- **No issue-tracker sync** (Jira, Linear, GitHub Issues). A backlog that lives in a
  service is a backlog an agent cannot `Grep`.
- **No model and no prompts.** The tool validates and renders; it never writes the
  symptom or the rationale. A generator would reintroduce exactly the prose drift
  this exists to stop.
- **No dates, quarters or estimates.** A marker is maturity, not a schedule.
- **No enforced id scheme beyond `<prefix><n>`.** Non-contiguous, retired-never-reused
  is a property of real backlogs, not a defect to normalize.
