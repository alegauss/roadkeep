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

- 📋 **RK1512** (deps: —) **pick and brief never name the deferred store, so a set-aside line and the reason it cites go unread** — RK92 resolves a dep on a paused task, which is the only way a deferral reaches an answer here, and a reason can expire while the decision it justified stays put. → §RK1512
- 📋 **RK1513** (deps: —) **brief hands over a line carrying no criteria in silence, and the absence is reported only once part landed** — RK1185 rides the criterion with the brief where one exists and RK1433 reports its absence at the partial marker, so the moment before the first edit says nothing. → §RK1513
- 💭 **RK1519** (deps: —) **a project that declares its own open markers cannot claim a line, and nothing anywhere says so** — The claim machinery writes and compares the package's in-progress marker, and [markers] has no key by which a project could name its own. → §RK1519
- 💭 **RK1520** (deps: —) **the marker-leak gate rewards the repair that renders the same wrong bytes** — It scans the package for a literal codepoint, so interpolating the constant passes it while the reader is told about a glyph their project may not declare. → §RK1520
- 💭 **RK1527** (deps: —) **the near window stayed at three when the corpus it ranks over doubled** — RK1495 put the open lines beside the deliveries and the two halves now compete for the same three rows, with no reading of how often either wins one. → §RK1527
- 💭 **RK1528** (deps: —) **the near row offers the door to the delivered half and none to the open half it now counts** — RK1495 made the corpus two and RK442's guarantee names where the rest of one of them are, leaving the half the task was filed for unfollowable. → §RK1528
- 💭 **RK1529** (deps: —) **an incidental path naming no file is silent, where a budget naming none is a finding** — RK1496 added the key and the gate reads nothing off the tree for it, so a filter that stops matching makes a report louder with nothing having changed in it. → §RK1529
- 💭 **RK1545** (deps: —) **the filings axis reads one per ship over one commit here, which is this session's cadence and not the work's** — RK1510 built the reading to tell a backlog decomposing from one discovering, and on this corpus a commit per thought flattens both to the same shape. → §RK1545

## Block D — The gate

- ⏳ **RK1498** (deps: RK1532) **thirty of the thirty-six sites that compose a door are accounted for as a work-list, so nothing ever runs one** — Thirty of the sites are still accounted for as a work-list rather than run, one fixture family at a time. → §RK1498
- 💭 **RK1515** (deps: —) **a design quoting a constraint to describe somebody else's case reads as having settled it** — RK1488 printed that claim on its own shipment, so a substring sized for a note falling silent now carries two assertions it was never measured for. → §RK1515
- 💭 **RK1516** (deps: —) **section drop deletes a design and never says the constraint answer went with it** — RK1488 taught the three departure doors that a deletion is the last reading, and the verb whose whole job is deleting a section inherited nothing. → §RK1516
- 💭 **RK1517** (deps: —) **a served flag that only shapes the terminal form is inert, and nothing asks that of the eighteen** — The server appends --json to every call, so origin --why shaped nothing for as long as it was served and was found only when a test fixture grew a git history. → §RK1517
- 💭 **RK1518** (deps: —) **adopt refuses two answers inside its estimator, so the dispatcher and the served surface read them as compatible** — RK489 replaced exactly those hand-written refusals with one declaration, and this one survived where nothing but a call can discover it. → §RK1518
- 💭 **RK1521** (deps: —) **the note cadence prices what fired and cannot say what it left out, no list of note codes existing** — RK1491 measured one note of an unknown number, and the remedy table that knows every code does not separate a note from a finding. → §RK1521
- 💭 **RK1522** (deps: —) **one record is a file section, a reference page and a note row, and its docstring describes only the first** — RK1491 filled Part's heading with a note code and its lines and bytes with numbers nobody reads, because the record demanded them. → §RK1522
- 💭 **RK1526** (deps: —) **the read that lets a reader choose between four rows is repeated on each of them** — RK1494 split the note so each row carries its own move, and a note's message is the only place the gate renders a door, so the shared read went four ways. → §RK1526
- 💭 **RK1530** (deps: —) **the corpus reading a refusal was drawn from lives in a docstring and nothing re-takes it** — RK1497 measured 18 false positives over prose against zero over fields and threw the probe away, so the number that decided the boundary cannot be checked. → §RK1530
- 💭 **RK1531** (deps: —) **a section title takes the mangled bytes the line's own fields refuse** — RK1497's boundary is field and not body, and a title is a bounded composed field that lands as a permanent heading with no door in front of it. → §RK1531
- 💭 **RK1532** (deps: —) **thirty rows of the composer work-list share one reason, so none of them says what it would cost** — RK1498 took four out in a sitting at two lines of fixture each, and the constant they all carried is why nobody had started at any. → §RK1532
- 💭 **RK1533** (deps: —) **govern writes a number the config parser then refuses, leaving every verb unable to read the file** — Violated guards a number the corpus breaks and nothing guards one two keys in a table forbid, so the repair is the hand edit the guard denies. → §RK1533
- 💭 **RK1535** (deps: —) **nothing records which volunteered rows an author acted on, so the population that could score the read has none** — RK1500 proved the retirement corpus cannot score the query half, and the answers given before the answer was known are printed and dropped. → §RK1535
- 💭 **RK1536** (deps: —) **a decision can only be filed by a departure, so the moment its answer is lost is the moment nothing can be done** — RK1501 had to say it in brief because --decides is a flag on the ship, and the ledger has record add for exactly the route the decisions role lacks. → §RK1536
- 💭 **RK1537** (deps: —) **a pause is not held to the why limit a project declared, and nothing at the number says so** — RK1502's sweep read that as the defect RK1479 repaired, because a field nothing measures and one measured against another key look the same from outside. → §RK1537
- 💭 **RK1538** (deps: —) **the flag saying which ceiling refused a field reaches neither the remedy table nor a payload** — RK1503 made the fact structural for three readers and only the write path uses it, so the other two still match on prose. → §RK1538
- 💭 **RK1539** (deps: —) **the comment explaining the respelling guard names a verb this CLI does not have** — RK1504's enumeration found one collision where two were described, both examples having been written from the tool table and neither checked against the parser. → §RK1539
- 💭 **RK1540** (deps: —) **a reference page now opens with two lines addressed to the gate, and nothing prices them** — RK1505 put the declaration in the page so the page states its own claim, on files RK1437 split off precisely for what opening one costs. → §RK1540
- 💭 **RK1541** (deps: —) **the served budget has no room for a tenth subject, and which of its sixteen arguments callers use is unmeasured** — RK1506's flag was withheld at 97 characters over, and the split RK1321 made to buy that room has no obvious seam left. → §RK1541
- 💭 **RK1542** (deps: —) **the retirement prefix every ranking figure is measured through is split by hand in two tests** — RK1507 paired the carried line's two readers and this is the same shape one field over, with the composer in shipping and the readers in a test. → §RK1542
- 💭 **RK1544** (deps: —) **the brief an estimate prices has no deps and no design, and the row does not say so** — RK1509 reads the file adopt was handed because the tree has declared nothing, so every part of a brief that lives in another role is absent from the figure. → §RK1544

## Block E — Adoption

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 💭 **RK1514** (deps: —) **uninstall leaves the vendored engine on disk and its own kept field never mentions it** — RK1487 made a refusal name the copy nothing points at, and the successful removal one verb over leaves the same copy with the same silence. → §RK1514
- 💭 **RK1523** (deps: —) **a declaration whose program engines cannot name is silent, and reads exactly like a project that declares none** — RK1492 made the reader refuse to guess, and the report has no row for the one command the harness literally runs. → §RK1523
- 💭 **RK1524** (deps: —) **the four notes this server appends to a tool result are priced by nothing, on a heavier cadence than the gate's** — RK1491 gave the gate's notes a number and RK1493 enumerated a second population, and two of these were already cut by reading rather than against a figure. → §RK1524
- 💭 **RK1525** (deps: —) **the kinds sweep is total over the notes that make a call and silent over the ones that do not** — RK1493 reads the literals passed to _said_once, so the per-call kind is in the table by hand and a second one arrives as invisibly as the four did. → §RK1525
- 💭 **RK1534** (deps: —) **the orientation an install prints names five commands in an order the tree it is printed to cannot run** — RK1498 pointed the sweep at it and every command refuses there, so a test asserting what is printed would be asserting the defect. → §RK1534
- 💭 **RK1543** (deps: —) **a version here names one commit and the surfaces that consume one speak of it as a release, with nothing saying which** — RK1508 assumed a walk over tags and found one tag against 1650 commits, every one of which the hook stamps a version into. → §RK1543

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

## Done when — RK1498

- **Every site is run or deliberate** No row of composing.SITES states unreached, so the
  work-list is empty and each composer has had its command executed.

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
