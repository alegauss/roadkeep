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

- 📋 **RK1187** (deps: —) **`symptom` is the one prose field no verb declares as a pipe reader, so `-` lands in the file as the claim** — RK1176 made that declaration the parser's own and `restate` declares none — the verb whose only prose argument is the field that carries a backtick as readily as a why. → §RK1187

## Block C — Query (consult without reading the file)

- 📋 **RK1184** (deps: —) **Nothing states what would prove a task done, so `ship` is a judgement with no artefact behind it** — `remaining` already runs a design's own fenced query, so evidence is that read inverted — sites that must exist rather than sites left, counted and never judged. → §RK1184
- 📋 **RK1185** (deps: RK1184) **`brief` hands over a task's design and deps but never its criterion, so it is read at the ship** — A criterion binds what the work must produce, so one arriving after the code is written is the read `brief` exists to make in a single call. → §RK1185
- 📋 **RK1188** (deps: —) **No verb says what the blocks are called, so choosing where a task goes means reading the file the hook denies** — SKILL.md tells an author to look at what the blocks already are before add; stats answers letters and counts, list and delivered demand a block they cannot enumerate. → §RK1188
- 📋 **RK1190** (deps: —) **budget states the allowance and cannot be handed a draft, so prose three words over is found by being refused** — RK190 made the allowance knowable before the first word; measuring the draft against it still costs a write, and the retry after each refusal is a guess. → §RK1190

## Block D — The gate

- ⏳ **RK1172** (deps: —) **The gate's checks are functions gathered by convention, each with its own signature, so adding one is invisible** — linting.py is 1,618 code lines of hand-wired calls whose scan kind is implicit in the parameters, where the remedy side has been a table keyed by code since RK420. → §RK1172

## Block E — Adoption

- 📋 **RK1186** (deps: —) **`init` scaffolds three files and no flag names the strategy one, so a spec above the task line has no home** — Every reader of a pointer already resolves across both prose roles, so the file is supported everywhere except at the one command that creates a project's files. → §RK1186

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

- ⏳ **RK1170** (deps: —) **A verb's plain answer and its json payload are built in two files, and most of the printing never moved** — rendering.py holds 23 printers against 386 print calls left in the handlers, so the layer buys no rule about where a sentence is and costs every verb a second file. → §RK1170
- 📋 **RK1171** (deps: RK1169 ✅, RK1170 ⏳) **build_parser is one 2,000-line function, so a verb's flags are edited in the file the whole surface is in** — cli.py was split by layer for size and grew back to 2,260 code lines, so the cut that holds is per verb, which the two deps make a move and not a rewrite. → §RK1171

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
