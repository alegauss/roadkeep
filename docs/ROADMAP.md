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

## Block C — Query (consult without reading the file)

## Block D — The gate

## Block E — Adoption

- 📋 **RK18** (deps: RK3 ✅, RK14 ✅) **A tool that requires an empty repo cannot be adopted by the repo that needs it** — `init` scaffolds the files and config, and `adopt` reports what an existing backlog must change to pass. → §RK18
- 📋 **RK19** (deps: RK18) **Installing from a git clone keeps a standard local** — publish to PyPI so `uvx roadmap-lint` runs with no checkout. → §RK19
- 💭 **RK20** (deps: RK16 ✅, RK19) **Shio's 92 active lines average 142 words against a one-sentence rule** — migrating a real backlog is the only test of whether the schema fits a live project. → §RK20
- 💭 **RK21** (deps: RK20) **A standard adopted by one project is a preference** — roll out to Turing, Dumont and Cursarei, each with its own `roadmap.toml`. → §RK21

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK22** (deps: RK5 ✅, RK14 ✅) **An agent can hand-edit the file the CLI is supposed to own** — a `PreToolUse` hook that denies `Edit`/`Write` on the governed files and names the command to call instead is the only barrier an agent cannot route around. → §RK22
- 📋 **RK23** (deps: RK22) **Rules resident every turn spend the budget they exist to protect** — package the format as a skill with trigger phrases so it loads when a governed file is in play, and not before. → §RK23
- 📋 **RK24** (deps: RK5 ✅, RK10 ✅) **Shelling out puts argument names in prose, where they are guessed** — expose `add`/`ship`/`pick`/`lint` as MCP tools so the field schema *is* the tool's input schema. → §RK24
- 📋 **RK25** (deps: RK23) **A human driving the same standard should not have to learn the CLI** — `/roadkeep:add`, `/roadkeep:ship`, `/roadkeep:pick` and `/roadkeep:lint` over the one engine. → §RK25
- 💭 **RK26** (deps: RK19, RK22) **A plugin installed by hand is a plugin one project has** — publish a `marketplace.json` so `/plugin install` reaches it. → §RK26

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
