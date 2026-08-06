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

- 📋 **RK378** (deps: —) **Two prose files must share one outline, with no way to give either its own** — every declared prose file numbers into a single anchor space, so a project whose STRATEGY and IMPROVEMENTS each keep their own outline collides by construction rather than by mistake. → §RK378

## Block B — Authoring (insert, never hand-edit)

- 💭 **RK368** (deps: —) **A non-goal whose reason changes has no door but drop and re-add, which moves the bullet to the end of the list** — `record amend` exists so a ledger correction is not a move; the non-goal list has no equivalent, and `add` appends, so a reworded reason reads as a deletion elsewhere. → §RK368
- 📋 **RK377** (deps: —) **A doubled anchor has no verb that repairs it** — lint reports section.ambiguous and the write path refuses a doubling, but no verb changes a section's address, so the only repair left is the hand edit the hook denies. → §RK377

## Block C — Query (consult without reading the file)

## Block D — The gate

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
