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

- 💭 **RK385** (deps: —) **Nothing notices that a new line asks for what a shipped entry already delivered** — RK378 was filed the day after RK340 shipped the same namespace and nothing refused it, so a duplicate costs a claim, a brief and a retirement before anyone reads the ledger. → §RK385
- 📋 **RK399** (deps: —) **One field is spelled --status on add and --marker on resume** — The open marker is a single declared field, and a caller who learns its flag name on one verb is refused by the other. → §RK399
- 📋 **RK400** (deps: —) **Shipping a family's last child leaves its parent describing deleted work** — The introduction a subtree was written under survives every ship that emptied it, so the file's most-read paragraph is the one nothing checks. → §RK400
- 📋 **RK401** (deps: —) **A line the gate calls clean is refused by the door that corrects it** — amend, restate, status and renumber validate against Config.schema, so a file whose [rules.<role>] excuses a field is judged by the roadmap's rules and the correction has no door. → §RK401
- 📋 **RK407** (deps: —) **A refusal blames the author for a character its own shell wrote** — PowerShell expands a backtick, so prose quoting an identifier arrives carrying a carriage return and the answer is why.newline, which names a newline nobody typed. → §RK407
- 📋 **RK408** (deps: —) **The ship that empties a block reports it and names no verb for it** — It already prints `Block <x> empty`, so a caller whose project drops a heading with its last line has to know `block drop` from somewhere other than the answer telling them to run it. → §RK408
- 📋 **RK414** (deps: —) **A slip of the pen in a symptom has to borrow the verb for a false premise** — amend refuses the field by design and restate is documented as the correction for a claim that turned out wrong, so a typo is repaired by a door that means something else. → §RK414

## Block C — Query (consult without reading the file)

- 📋 **RK409** (deps: —) **The machine-readable brief answers a finished block in prose** — It exits 2 with an empty stdout and an English sentence on stderr, so a caller who asked for JSON to detect "nothing is open" is the one caller that gets none. → §RK409
- 📋 **RK410** (deps: —) **The free address is the last line of a listing of spent ones** — Asking `anchors` which child to write next prints every anchor the family ever had, so under a 27-anchor family the one number wanted is 28 rows down. → §RK410

## Block D — The gate

- 📋 **RK412** (deps: —) **The seam every line write passes is told which file it is writing into twice** — The path is rendered by the caller and the role is spelled beside it at five call sites, so a door passing one and forgetting the other prints a remedy that refuses. → §RK412
- 📋 **RK415** (deps: —) **Three engines write and judge one project and none names the others** — A checkout CLI wrote this repo at 0.1.418-modified while its hook ran the 0.1.285 plugin and CI gated on @main, and no verb says the writer and the gate disagree. → §RK415

## Block E — Adoption

- 📋 **RK402** (deps: —) **The tree that ships the plugin is told to wire the guard a second time** — install --check names two surfaces this checkout provides as a plugin and skips them, and asks to write the same hooks into .claude/settings.json, so the read never reports clean here. → §RK402

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
