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

- 📋 **RK1632** (deps: —) **add --symptom takes no stdin, the one prose field with no pipe being the one every line leads with** — RK1187 gave restate --symptom the pipe and add kept the literal, so a claim carrying a backtick reaches one verb and lands as text in the other. → §RK1632
- 📋 **RK1634** (deps: —) **a ship deletes the design section and names nothing that was in it, so the last look at it never happens** — Three flags carry a design's durable half and all three are optional, so a section goes to a caller who was never shown it was about to. → §RK1634

## Block C — Query (consult without reading the file)

- 💭 **RK1609** (deps: —) **three scans of one rule reconstruct a composed command three ways, and a value sits in the gap between them** — RK1558 stated where the exemption ends and left the span split across an f-string's parts, so a literal value inside a help command is read by none of them. → §RK1609
- 💭 **RK1618** (deps: —) **delivered and reversals are the reads before an add, and neither holds what was traced and not filed** — pportal keeps twenty-five such findings outside its git; only the premise an entry names can reopen it, and a free-prose reason has no slot for one. → §RK1618
- 💭 **RK1622** (deps: —) **a design can cite a corpus for a ratio it does not have, nothing here reading what shape the pins hold** — RK1566 was designed around a Turing backlog that is three open lines against 901 entries, and the measurement was the first reader to notice. → §RK1622
- 💭 **RK1623** (deps: —) **three tests rebuild the corpus add ranks against, so a change to what add includes leaves every figure passing** — RK1566 added the third hand-built copy of the delivered-then-open list, and the boundary between the halves is what every split figure counts from. → §RK1623
- 💭 **RK1624** (deps: —) **the ranking an add volunteers exists only inside that write, no read answering over a block's whole corpus** — RK1567 left the third way out it named, and the two doors the row prints order by the ledger and by id rather than by the query. → §RK1624
- 📋 **RK1625** (deps: —) **unclosed answers a tree with no git as a backlog with nothing open, the flag that tells those apart never being set** — Nothing in the package makes Unclosed.searched false, so the one state the field was declared for is the one it reports as a clean sweep. → §RK1625
- 📋 **RK1628** (deps: —) **pick offers an idea whose premise a later ship deleted, no answer saying what landed under the line since it was filed** — RK1571 and RK1574 were both designed against a work-list RK1599 emptied, and reading the section was the only way to learn it. → §RK1628
- 📋 **RK1630** (deps: —) **a read payload names neither the root it answered about nor the build that answered** — lint carries root and config carries version; list, show, brief, stats, export and pick carry neither, so a client holding several projects' answers cannot tell whose it holds. → §RK1630
- 📋 **RK1631** (deps: —) **no one call says whether a path is governed and where its root is, so a client reads it off a null** — config answers source = null, engines answers happily about an ungoverned directory, and lint does a whole file's work to report the root a probe needs. → §RK1631

## Block D — The gate

- 💭 **RK1610** (deps: —) **a config key typed under the wrong table is refused as unknown, where the tool knows exactly which table it belongs to** — RK1064 spells the refusal for a key nothing declares, and a misplaced one is neither a typo nor an upgrade, so both clauses point away from the edit. → §RK1610
- 💭 **RK1612** (deps: —) **a verb writing an answer and a note in one run has to flush between the streams, and nothing says which verbs those are** — RK1561 met the ordering a second time and the first fix carries a bare flush with no reason, so the rule is rediscovered rather than read. → §RK1612
- 💭 **RK1620** (deps: —) **the note census prices one row per note, so it reports what the gate composed and not what it printed** — RK1565 folded a run of notes into one sentence, and the figure claiming to be what a session pays never learnt about it. → §RK1620
- 💭 **RK1621** (deps: —) **the summary and the folded note row now both carry the count of surfaces behind the engine** — The clause arguing the summary is not a second sentence rested on the notes carrying no count, which RK1565 changed. → §RK1621
- 📋 **RK1626** (deps: —) **the field sweep skips its whole assertion where a corpus is absent, including this repository's own 2,246 fields** — RK1569 split ours from theirs in the prose half, and the field half still requires both corpora to say anything about the files in this tree. → §RK1626
- 💭 **RK1627** (deps: —) **nothing enumerates the fields a caller composes, so which of them has a validator is answered by remembering** — RK1570 found the block title because a design named it, and the same gap in any other composed field would be as invisible as that one was. → §RK1627
- 📋 **RK1635** (deps: —) **the composer sweep runs every door through shlex, which is the assumption the door was wrong about** — RK1580 was invisible for a year because the instrument reads a line with the parser whose POSIX default put the bad quote there. → §RK1635
- 📋 **RK1637** (deps: —) **seven cost subjects each argued they were the Nth cadence nobody counted, and nothing enumerates the cadences** — RK1424, RK1428, RK1491, RK1524 and RK1582 each made that case from scratch and none could say how many were left. → §RK1637
- 📋 **RK1638** (deps: —) **a prose check finds its span by splitting on a sentence, so a reworded clause empties the test instead of failing it** — RK1585's two readers both address the comment by a phrase somebody wrote, which is the drift they were built to catch one level up. → §RK1638
- 📋 **RK1639** (deps: —) **one closed set of prose was swept for stale figures and the three a caller actually meets were not** — RK1588 found two of nine withholding reasons resting on numbers nothing re-takes, and remedies, notes and refusals are the same shape unread. → §RK1639
- 💭 **RK1640** (deps: —) **421 verb-leading spans sit in messages carrying no sibling door, so the pair that decides one reads none of them** — RK1590 fires on a message spelling one verb both ways and the mixed shape numbers zero, so what is unread is every span with nothing beside it. → §RK1640
- 💭 **RK1641** (deps: —) **the sweep that runs every door the gate offers reaches one of eighty-four dispatchable rows** — RK472, RK1015 and RK1591 each corrected runnable on a door found refusing in the field, and the test written to catch that reads whatever one fixture happens to emit. → §RK1641
- 💭 **RK1642** (deps: —) **the preventive read a refusal names for seven codes is in the sentence and in no field of the payload** — RK1600 published the retry and left the other runnable row of the same refusal as prose, so a caller reading fields gets the rule and never the read that prevents it. → §RK1642
- 💭 **RK1643** (deps: —) **the orientation is held at a ceiling and the two pages it points at, six times its size, are held by nothing** — RK1437 split them off on a cadence argument and gave the ceiling to the half that shrank, so RK1601 added 2,437 code units to the unbounded half and nothing asked. → §RK1643
- 💭 **RK1644** (deps: —) **nine guards over this package's source read its characters where twenty-two read its syntax** — RK1602's read lines and missed a compiled pattern, then matched the docstring recording that removal, which is the failure a scan over characters has and one over calls has not. → §RK1644
- 💭 **RK1645** (deps: —) **config publishes three lists of objects and the promise table holds one slot per verb, so one list's rows are unpromised** — RK1603 added a second list and a second table beside it, and the third — fixed, published since RK1381 — has never been named at all. → §RK1645
- 💭 **RK1646** (deps: —) **the guard against the folded idiom sweeps the package and not the suite, where two sites still spell it out** — RK1542's equivalent sweeps both and this one copies half of it, so the shape RK1604 took out of forty-one call sites can grow back in a test. → §RK1646
- 💭 **RK1647** (deps: —) **three walkers in the suite each rebuild which function a node sits in, and one of them spells the address differently** — RK1605 added the third, and surface.py is where a shared reading of the layout belongs. → §RK1647
- 💭 **RK1649** (deps: —) **answers() spells at most one of a verb's flags and nothing spells exactly one, so a required choice stays a raise** — RK1607 moved four pairs to the parser and left criterion add's, where argparse's required group answers on a command line and says nothing over MCP. → §RK1649

## Block E — Adoption

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 💭 **RK1611** (deps: —) **uninstall keeps a server declaration it did not write and takes away the approval that made it run** — RK1560 stopped the withdrawal at the declaration, and the approval is a second key in a file the same command deletes. → §RK1611
- 💭 **RK1619** (deps: —) **the note sweep names the first call in an answer, so a helper before the note would take its kind** — RK1564 fixed the clause after a note and left the mirror case, where the exact reading is the separator the site already spells. → §RK1619
- 💭 **RK1648** (deps: —) **verifying a vendored engine runs it, so Python writes three megabytes of bytecode into an artefact just measured at four** — RK1606 took the copy to 3.89 MiB and the --version that proves it imports leaves it at 7.24, which no rule about what is copied can reach. → §RK1648

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

- 📋 **RK1629** (deps: —) **two modules walk back from a file's last blank line under two names, and the kernel that owns blank has no name for it** — RK1573 gave scoping a heading to open and the answer criteria had already written, so the copy was made by reading it. → §RK1629
- 📋 **RK1633** (deps: —) **one verb handler writes a governed file itself, and it is the writer every enumeration of the config's has missed** — RK1576 counted five and the sweep found six: the extra one is the single write in verbs that is not a save the domain module owns. → §RK1633
- 📋 **RK1636** (deps: —) **a name a module imports and then defines is bound by the later one, and nothing here reports the dead import** — RK1581 imported config.declares into a module that already declared its own, and the wrong function was called until a TypeError three frames away. → §RK1636

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
