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

- 📋 **RK1459** (deps: —) **The read that prices a body and the write that files it name the same argument differently, so the loop costs a refusal** — budget takes --body-file and add takes --section-body-file, so a caller moving from the price to the write is refused for the flag it was just told to use. → §RK1459
- 📋 **RK1460** (deps: —) **A criterion checked by running something ships looking exactly like one nobody looked at** — ship lists every criterion as unmet, so the ledger cannot tell a verified claim from an ignored one. → §RK1460
- 💭 **RK1474** (deps: —) **a decision's symptom is a copy of a roadmap line that is gone, and no verb in any of the three files can correct it** — revise reaches the sentence and restate reached the line before it shipped, so a claim mangled by a shell is now permanent in two files at once. → §RK1474
- 💭 **RK1475** (deps: —) **the ship that finishes a block offers a block drop the decisions file will refuse, on every project that files decisions** — RK1454 made the refusal name the ending and left the offer that sends a sweep into it, though the same ship just wrote the entry that blocks it. → §RK1475

## Block C — Query (consult without reading the file)

- 📋 **RK1455** (deps: —) **a changelog listing cannot be asked for its blocks, so the only way to see them is to read the file** — An unscoped ledger listing is 117k characters and a scoped one needs a block label the caller does not have, so finding what the blocks are means reading the governed file. → §RK1455
- 📋 **RK1456** (deps: —) **budget says what a why is allowed and nothing measures the why about to be written** — A section can be measured before it is sent and a line's fields cannot, so a caller either hand-counts code units or spends a refusal per attempt. → §RK1456
- 📋 **RK1458** (deps: —) **budget prices a why against the roadmap line's limit while the ship about to be written is held to the ledger's** — brief quoted 190 for the shipping sentence and budget quoted 171 for the same field, so the read meant to prevent a refusal answered about a write nobody was making. → §RK1458
- 📋 **RK1461** (deps: —) **budget cannot price a line that will carry a requires, so the number it quotes is 21 characters too generous** — add takes --requires and budget does not, so a sentence priced without one is refused for the exact width of the (requires: word) the write adds. → §RK1461
- 📋 **RK1463** (deps: —) **brief spends four fifths of its answer on deps that are all shipped and settled long ago** — Each resolved dep carries two full commit subjects, so starting a six-dep task costs thousands of tokens of history nobody asked about. → §RK1463
- 📋 **RK1466** (deps: —) **a project numbering by id gets every address in one answer, which at this repository's size is 961 rows and 175 KB** — RK1450 replaced a count nothing could open with a listing nothing bounds, because the register it stood in for was also what held the rows back. → §RK1466
- 💭 **RK1467** (deps: —) **A requirement gates the whole line, so the half of a task that needs nothing is never offered** — `ship --part` records that a half landed, and `pick` has no matching idea beforehand: a caller that could build that half is told there is nothing to pick. → §RK1467
- 📋 **RK1472** (deps: —) **`budget` takes no --requires, so it prices a line the requirement group has not been charged to** — It reports the why limit as 185 where `add --requires` enforces 164, and the refusal's own foresee line points back at the call that said 185. → §RK1472
- 📋 **RK1473** (deps: —) **`unclosed` counts roadkeep's own prose edits as evidence a line shipped, so its report is mostly its own writes** — It drops the commit that filed an id and no other, though `amend` and `section amend` name one too and touch only files it governs. → §RK1473

## Block D — The gate

- 📋 **RK1457** (deps: —) **non-goal.reaches fires on every lint and nothing clears it, so a project that decided reads the same note forever** — Its own remedy is non-goal amend; a project named both bounded lines inside the rule's paragraph and both are still flagged, so the gate carries unanswerable notes. → §RK1457
- 💭 **RK1468** (deps: —) **the gate's engine note reads the plugin alone, so a project running two local copies at two versions passes it clean** — engines exits 1 on a vendored copy at another version and the once-per-commit note never asks, so the split is found only by whoever ran that read on purpose. → §RK1468

## Block E — Adoption

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK1462** (deps: —) **install rewrites a surface with an older engine's copy, so the remedy lint names undoes a fix that shipped** — The vendored engine is 0.2.4 and the committed launcher carried RK1446; install --check called it stale and install wrote the pre-fix version back over it. → §RK1462
- 📋 **RK1464** (deps: —) **install --vendor writes the surfaces before it replaces the engine, so one run leaves the outgoing engine's copy on disk** — Vendoring 0.2.60 over 0.2.4 said updated then vendored, and the launcher left behind was 0.2.4's; a second install wrote the right bytes. → §RK1464
- 📋 **RK1465** (deps: —) **the launcher spends a whole extra Python start proving an engine runs, doubling how long connecting takes** — The probe was justified by an execv that cannot be taken back, and on Windows there is none: the parent waits on the child already. → §RK1465
- 💭 **RK1469** (deps: —) **engines --invoke restates the launcher's order and knows two of its four entries, so a ROADKEEP_HOME pin is missed** — The launcher resolves the override, the vendored tree, a sibling and a cache clone, and the line a shell pastes only ever names the plugin or the vendored one. → §RK1469
- 💭 **RK1470** (deps: —) **the served staleness note reads mtimes, so an engine replaced under the session looks like somebody saving a file** — engines now tells a swapped home from an edited one and the note that fires on every refusal still lists modules and names a bump. → §RK1470
- 💭 **RK1471** (deps: —) **a write from an engine whose home was swapped is allowed, on rules no disk holds and with no pin to compare against** — RK1235 refuses a copy behind the pin and RK1452 named a copy that is on no disk at all, which nothing in front of a write asks about. → §RK1471

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
