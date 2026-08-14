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

- 💭 **RK1180** (deps: —) **A block that is a standing category empties whenever it is caught up, and ship reads that as completion** — Shio's Block N was declared, emptied and dropped three times in one session, and each completion asks for a four-surface sweep meant for a block that finishes once. → §RK1180

## Block B — Authoring (insert, never hand-edit)

- 📋 **RK1182** (deps: —) **ship refuses over a dependent line's why, and names the shipping task's own why, which cannot fix it** — A dep annotation grows a tick when the dep ships, so a dependent one character under the limit goes over, and the refusal points at the wrong line. → §RK1182

## Block C — Query (consult without reading the file)

## Block D — The gate

- 📋 **RK1172** (deps: —) **The gate's checks are functions gathered by convention, each with its own signature, so adding one is invisible** — linting.py is 1,618 code lines of hand-wired calls whose scan kind is implicit in the parameters, where the remedy side has been a table keyed by code since RK420. → §RK1172
- 📋 **RK1173** (deps: RK1172) **A rule's remedy is a second table keyed by the same code, kept in step by a test rather than by the record** — Once the check is a record, its door is a field on it, and the totality assertion becomes a thing that cannot be written wrong instead of one a test catches. → §RK1173
- 📋 **RK1181** (deps: —) **ref.dangling reads a section mark citing another document as a pointer into this file, and the first has no spelling** — Prose in a governed file legitimately argues from a spec's numbered sections, and the gate refuses the turn until a correct sentence is rewritten. → §RK1181

## Block E — Adoption

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

- ⏳ **RK1169** (deps: —) **Six tables in serving.py restate per verb what its own parser already declares** — Every property is already derived from the argparse action, so exposure, bounds and the withheld reason are the same kind of fact, and the totality tests exist to hold two places in step. → §RK1169
- ⏳ **RK1170** (deps: —) **A verb's plain answer and its json payload are built in two files, and most of the printing never moved** — rendering.py holds 23 printers against 386 print calls left in the handlers, so the layer buys no rule about where a sentence is and costs every verb a second file. → §RK1170
- 📋 **RK1171** (deps: RK1169 ⏳, RK1170 ⏳) **build_parser is one 2,000-line function, so a verb's flags are edited in the file the whole surface is in** — cli.py was split by layer for size and grew back to 2,260 code lines, so the cut that holds is per verb, which the two deps make a move and not a rewrite. → §RK1171
- 📋 **RK1179** (deps: —) **A checkout whose source does not import answers with a raw Python traceback instead of a sentence** — The screen exists to keep an import error off the turn, and an edit in progress in the answering checkout lands under it as an IndentationError naming a line of backlog.py. → §RK1179

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
