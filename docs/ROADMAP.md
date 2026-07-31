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

- 📋 **RK67** (deps: RK41 ✅) **A ledger entry written twice cannot be removed, so the file states one decision twice** — Give record its inverse for an entry no roadmap line ever left, because Shio carries SH347 on two lines and nothing but a hand-edit can drop one. → §RK67
- 📋 **RK70** (deps: RK3 ✅) **No command can write a non-goal, and the denial names five that cannot** — The hook refuses the edit and offers only commands that write task lines, so a binding constraint is edited by the `sed` the barrier deliberately does not match. → §RK70

## Block C — Query (consult without reading the file)

- 📋 **RK68** (deps: RK29 ✅) **The brief prints a non-goal narrower than the file states** — Turing's first bullet loses seven of its ten items to a line wrap and its second reduces to the word `not`, because the lead is inferred from prose instead of read from a field. → §RK68
- 📋 **RK69** (deps: —) **Non-goals are printed when a task starts, not when one is proposed** — The roadmap says to check the list before proposing work and only `brief <id>` prints it, so the rule that binds an `add` has no command at the moment it binds. → §RK69

## Block D — The gate

## Block E — Adoption

- 💭 **RK21** (deps: RK20 ✅) **A standard adopted by one project is a preference** — roll out to Turing, Dumont and Cursarei, each with its own `roadmap.toml`. → §RK21
- 📋 **RK66** (deps: RK3 ✅) **A project whose convention is no section means no pointer cannot declare it** — Expose ref_required in roadkeep.toml, because Shio documents that a task without design carries no pointer and gets three findings for obeying its own rule. → §RK66

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

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
