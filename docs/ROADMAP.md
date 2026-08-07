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

- 💭 **RK368** (deps: —) **A non-goal whose reason changes has no door but drop and re-add, which moves the bullet to the end of the list** — `record amend` exists so a ledger correction is not a move; the non-goal list has no equivalent, and `add` appends, so a reworded reason reads as a deletion elsewhere. → §RK368
- 📋 **RK381** (deps: —) **A refusal on a short field costs the whole rationale a second time** — the section body arrives on stdin, so a why over the limit by three words discards a prose block the author must resend verbatim, which is the expense the pre-write validation was meant to avoid. → §RK381
- 📋 **RK382** (deps: —) **A symptom that discovery widens has no verb, only retire and refile** — amend refuses the field because a different claim is a different task, but a claim found to hold in four places rather than one is the same task with a symptom that has become false. → §RK382
- 📋 **RK385** (deps: —) **Nothing notices that a new line asks for what a shipped entry already delivered** — RK378 was filed the day after RK340 shipped the same namespace and nothing refused it, so a duplicate costs a claim, a brief and a retirement before anyone reads the ledger. → §RK385
- 📋 **RK388** (deps: —) **A heading that parsed with its sigil is rewritten without one by a verb amending a different part of the file** — Round-trip is held over task lines only, so under an outline scheme a section verb re-renders a heading nobody named, and lint and the estimate both call the file clean. → §RK388
- 📋 **RK395** (deps: —) **A shipped entry that gets reverted stays in the ledger saying it shipped** — retire needs a roadmap line the ship already removed and record drop refuses a non-duplicate, so the revert can only be a second unlinked entry and the first still reads as delivered. → §RK395

## Block C — Query (consult without reading the file)

- 📋 **RK379** (deps: —) **The refusal for a missing anchor does not name the anchor to use** — under ref_scheme outline every add without --ref is refused by a fixed sentence, while `anchors` already computes the next free address in the family the line is going into. → §RK379
- 📋 **RK383** (deps: —) **The free-address help says one outline spans both files, which a declared namespace makes false** — anchors --role and its comment predate [refs], so a project whose prose files each declare a namespace reads a promise of a shared free address the command no longer computes. → §RK383
- 📋 **RK389** (deps: —) **A dep naming two real ids is accepted as one thing outside the backlog** — the value falls through to the free-text arm when it does not parse as a single id, so a compound spelling becomes an unresolvable external and the line reads blocked on work that does not exist. → §RK389
- 📋 **RK396** (deps: —) **A dep on a partially shipped task is annotated as satisfied** — ship --part writes a ledger entry and leaves the line open, but the dep annotation reads the ledger, so a dependent is marked unblocked by the half that landed rather than by the half it needs. → §RK396

## Block D — The gate

- 📋 **RK380** (deps: —) **A block can carry open lines for months and be found missing only by the first ship** — add writes a line under a roadmap block without checking the changelog declares it, so the heading a ship needs is discovered at the end of the first task in the block rather than at the start. → §RK380
- 📋 **RK391** (deps: —) **The gate holds no one-heading-per-label rule, and the write path resolves a repeated one by position** — RK390 closed the scaffold, and a hand edit, an adoption or a merge reaches the same state: lint calls it clean and add files under the last of the two headings. → §RK391

## Block E — Adoption

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 💭 **RK366** (deps: —) **The skill every adopting project loads has 24 body lines past 110 characters against a file otherwise wrapped at 90** — One pattern made them all — text appended to a line instead of the paragraph re-wrapped — so an edit arrives as a whole-paragraph diff and nothing holds the shape. → §RK366

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
- **No supported Python API.** The CLI, the MCP tools and the plugin are the surface;
  `from roadkeep import Schema` is how the tests reach the vocabulary, so no `py.typed`
  ships and a rename inside the package breaks nobody.
- **No effort or size field.** Nothing can verify a letter, `pick`'s every tier is a
  fact, and what an agent pays is context — median to p90, files vary 1.4× against lines
  2.7×, so the letter prices the axis nobody pays.
