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

- 💭 **RK1474** (deps: —) **a decision's symptom is a copy of a roadmap line that is gone, and no verb in any of the three files can correct it** — revise reaches the sentence and restate reached the line before it shipped, so a claim mangled by a shell is now permanent in two files at once. → §RK1474
- 💭 **RK1475** (deps: —) **the ship that finishes a block offers a block drop the decisions file will refuse, on every project that files decisions** — RK1454 made the refusal name the ending and left the offer that sends a sweep into it, though the same ship just wrote the entry that blocks it. → §RK1475
- 📋 **RK1480** (deps: —) **amend replaces the whole dep group, so adding one means retyping every dep the line already carries** — The retyped group is also wider, so a why that fitted before the add is refused after it, and one edit becomes two failures. → §RK1480
- 📋 **RK1481** (deps: —) **the CLI and the MCP surface spell several verbs and flags differently, so a call copied between them is refused** — next-id against next_id and --with against replacement each cost a refusal, and the caller cannot tell which surface a remembered spelling came from. → §RK1481
- 💭 **RK1483** (deps: —) **budget and the writes it prices disagree about arguments in both directions, and nothing enumerates the pairs** — RK1459 aliased one by hand and RK1458 and RK1461 added two the read never had, and nothing pairs a write parser against the read that prices it. → §RK1483
- 💭 **RK1484** (deps: —) **a ship recording a checked criterion wraps the entry, so correcting its sentence costs a span this tool wrote** — record amend refuses a wrapped entry without --lines, and after RK1460 the wrap is derived prose the caller would have to read back and retype. → §RK1484

## Block C — Query (consult without reading the file)

- 📋 **RK1472** (deps: —) **`budget` takes no --requires, so it prices a line the requirement group has not been charged to** — It reports the why limit as 185 where `add --requires` enforces 164, and the refusal's own foresee line points back at the call that said 185. → §RK1472
- 📋 **RK1473** (deps: —) **`unclosed` counts roadkeep's own prose edits as evidence a line shipped, so its report is mostly its own writes** — It drops the commit that filed an id and no other, though `amend` and `section amend` name one too and touch only files it governs. → §RK1473
- 💭 **RK1476** (deps: —) **an unscoped list over a ledger is bounded by nothing, so the transport refuses an answer this tool already composed** — RK1455 pointed a caller at the structure and left the listing at 117,815 characters, and no ceiling here is declared, measured or read. → §RK1476
- 💭 **RK1477** (deps: —) **a re-filing of shipped work in other words ranks 7th, outside both windows, so the add that wrote it agreed it was new** — The corpus is symptoms alone and the pair that proves it shares a subject and no words, which is what a second author writing the same defect produces. → §RK1477
- 💭 **RK1479** (deps: —) **a pause's reason is the one departure budget cannot price, its field holding a wrapper and the design carried forward** — RK1458 shipped --ship beside --retire and left --defer, because the carry is neither a derived prefix nor a replaced field and Budget has no third reading. → §RK1479
- 💭 **RK1486** (deps: —) **the brief ceiling was argued from a backlog with no deps at all, so the lists that grow with the graph are outside it** — This repository's lines carry no deps, and deps, settled deps and chains are the three parts of a brief that grow with the graph rather than the prose. → §RK1486
- 💭 **RK1490** (deps: —) **a caller who can see a withheld line is worth starting still has no way to take it, only to disbelieve the refusal** — RK1467 made the gate legible and left the half unreachable, so ship --part is the only place this tool says a line has parts, and it says it afterwards. → §RK1490

## Block D — The gate

- 💭 **RK1478** (deps: —) **a settled constraint-line pair is a sentence in one design and no read names it, so the gate's silence has no witness** — RK1457 answers the note from the line and nothing answers from the rule, so a clause somebody tidies away brings a note back with no clue what removed it. → §RK1478
- 💭 **RK1488** (deps: —) **a ship deletes the clause that answered a constraint and says nothing, so the answer ages out unremarked** — RK1457 put the answer in the design because it ages out with the work, and the ship that deletes it reports the section and never what the section settled. → §RK1488
- 💭 **RK1489** (deps: —) **the pair sweep reads a flag as swallowed where its fixture cannot hold the state the flag is about** — anchors --retired reads git diffs and the fixture inits no repository, so a correct flag was proved honoured by a payload key echoing the request. → §RK1489
- 💭 **RK1491** (deps: —) **the note a wired project reads on every turn is 475 characters at full length and no cadence prices it** — cost has five subjects and a note is in none of them, so engine.disagreement grew a clause in each of three tasks against no number at all. → §RK1491

## Block E — Adoption

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 💭 **RK1471** (deps: —) **a write from an engine whose home was swapped is allowed, on rules no disk holds and with no pin to compare against** — RK1235 refuses a copy behind the pin and RK1452 named a copy that is on no disk at all, which nothing in front of a write asks about. → §RK1471
- 📋 **RK1482** (deps: —) **a finding about the reader's own stale tooling sits in lint's list at the same weight as a line over its limit** — One reads as work in the project and the other as a fact about the session, and a whole session read past three of the second kind. → §RK1482
- 💭 **RK1485** (deps: —) **the record that stops a downgrade arrives on the write it guards, so an already-wired project is unprotected until then** — RK1462 reads [install] wired and nothing writes it before an install, which on the trees the defect was measured in is the very write being refused. → §RK1485
- 💭 **RK1487** (deps: —) **a vendor that lands and then fails to wire leaves a copy nothing points at, and no refusal says it is there** — RK1464 accepted that hazard to stop the downgrade and left it silent, so the caller reads what stopped the surfaces and not what is now on disk. → §RK1487
- 💭 **RK1492** (deps: —) **the invoke line finds the program by a .py suffix, which is a guess about a file this tool merges into** — RK1469 reads the argv the harness runs and has to stop before its mode, and a wrapper, an interpreter flag or uv run puts the program somewhere the suffix does not. → §RK1492

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)

## Done when — Block D

- **The gate passes on this repository's own docs** the format is proven by the artefact
  and not asserted in a README, so a limit these lines cannot express is the wrong limit
  rather than a set of wrong lines.
- **Every finding names the command that closes it** a report a reader cannot act on is
  one they skip, so each carries a complete argv and `--fix` runs the derived half of
  them (RK420, RK16).

## Done when — Block F

- **One install wires every surface a session reads** five of them — hook, skill,
  commands, manifest, server — and a launcher where no plugin can be, so an adopter runs
  one command and none of them drifts.
- **The guard denies a hand edit and names the verb** a refusal that stops at no is a
  detour; this boundary exists to turn an agent toward the command rather than away from
  the file.

## Done when — Block H

- **One verb's change is read in one module** each module's docstring is the authority
  and `origin <id>` answers where a rule came from, so what a change costs is bounded by
  where the answer lives.
- **Every served tool answers one question** a verb answering eight subjects is refused
  by whichever arrived last, and the seam is the tense: what a write may spend is not
  what a surface does (RK1321).

## Done when — Block A

- **One parser reads a line and one renderer writes it** the format is a schema and not
  a regex over prose, so a line that would render back differently refuses the whole
  file rather than being normalised (L1, L3).
- **An id is spent once, whatever holds it** a number two writes could mint is one two
  designs share in the history, so what derives an id reads every file a project
  declares and prose counts as carrying one.

## Done when — Block B

- **Every write a governed file takes has a verb** a hand edit is the drift this tool
  exists to refuse, so the guard denies one and names the command — and a state
  reachable only by editing the file is a verb that is missing.
- **A write lands whole or leaves the tree untouched** three files change on a ship and
  whichever is done last is the one forgotten, so every field is validated before
  anything is written and a refusal costs a retry and never a deletion.

## Done when — Block C

- **Every question is a command, and its answer is bounded** reading the file to answer
  costs the context this tool exists to save, so a read fits a tool result and says what
  it left out rather than inheriting a guarantee it gave up (L5).
- **One reading, two registers** the printed answer and the payload come off one record,
  because a printer and a payload builder agreeing by hand is how an agent comes to be
  told less than the person at the terminal.

## Done when — Block E

- **A project that already has a backlog can adopt this** a tool that needs an empty
  repository cannot be adopted by the repository that needs it, so drift is measured and
  forgiven by name against a baseline rather than refusing the file.
- **One command wires it, and one read says what is wired** three copies of this tool
  can answer at once and they are allowed to differ, so what is not survivable is being
  unable to say which of them wrote, judged or gated.

## Done when — Block G

- **The backlog is legible where the file is open** a format an author meets only in a
  terminal is one they edit by hand in the editor, so the surface holding the file
  offers the same writes under the same limits.
- **A surface in another language is gated in this tree** CI proving the Python and
  nothing else is a client that breaks on a renamed key with nobody reporting it, so the
  payload is asserted here as an outside client reads it.

## Done when — Block I

- **A reader with no checkout can answer an adopter's question** evaluation comes before
  installation, so an answer that needs an installed copy is one the reader who most
  needs it cannot reach.
- **Every reference page is generated from this package** a page retyping a flag, a code
  or a config key is wrong at the first rename and reports nothing, so the build derives
  them and fails where the two disagree.
- **No page restates prose another file owns** an area with room on every page invites
  the accretion this tool refuses, so a page renders the file that owns the words or
  carries no version of them.

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
