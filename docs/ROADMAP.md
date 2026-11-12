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

## Block D — The gate

## Block E — Adoption

- 📋 **RK1740** (deps: —) **install --vendor deletes the whole .roadkeep/ tree, so the capture reports kept under .roadkeep/reports are lost** — Refreshing seventeen projects erased the reports of three, and the folder is gitignored, so no copy survived to restore them. → §RK1740
- 📋 **RK1741** (deps: —) **A vendored engine falls behind the checkout on the same machine, and nothing refreshes it until a session refuses a line** — Thirteen vendored copies sat at 0.2.473 to 0.2.511 against a 0.2.576 checkout, and four pinned an empty tree, until a hand-run sweep. → §RK1741

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK1739** (deps: —) **A file that fails the grammar wholesale is blamed on its author, even when the running engine predates the format** — A stale MCP server refused winwright's four lines carrying a from clause as another format, and named no engine version against the wired one. → §RK1739

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)

## Block J — Validation (whether a person ever tried it)

## Block K — The desktop app (one installer for the reader and the plugin)

## Block L — Product sites on the package

- ⏳ **RK1729** (deps: a design-system release with VDS243) **Both product sites run a prerender script of their own, and neither is registered with the design system** — The gui landing still runs its own prerender until a design-system release carries prerenderSite's headTags. → §RK1729

## Block M — Codex integration (one engine, host-specific adapters)

- 📋 **RK1734** (deps: RK1732 ✅) **Bundled workflows assume Claude command syntax and tool names** — Give Codex the same Roadkeep workflow through reusable skills with valid invocations and tool references. → §RK1734
- 📋 **RK1735** (deps: RK1730 ✅, RK1731 ✅, RK1733 ✅, RK1734) **Install, check and uninstall cannot manage Codex project wiring** — Provide an explicit Codex installation path that preserves unrelated configuration and can be verified and reversed. → §RK1735
- 📋 **RK1736** (deps: RK1730 ✅, RK1731 ✅, RK1733 ✅, RK1734, RK1735) **The distributed plugin only declares a Claude installation** — Package the shared engine, MCP server and skills for Codex while retaining the existing Claude distribution. → §RK1736
- 📋 **RK1737** (deps: RK1735, RK1736) **No end-to-end evidence shows Roadkeep enforcement inside Codex** — Verify native plugin behavior and host regressions before claiming the Codex integration is supported. → §RK1737
- 📋 **RK1738** (deps: RK1737) **Users have no verified Codex adoption or distribution guide** — Document supported installation, trust and recovery paths using the integration evidence and current distribution rules. → §RK1738

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

## Done when — RK1729

- **Both sites registered with the design system** consumers.json lists the pitch and
  the gui landing, and the hub's projects.json gives roadkeep the amber the pitch uses.

## Done when — RK1734

- **Workflows preserve their contracts** Codex add, ship, pick and lint instructions
  retain required fields, exact-user-word rules and existing safety constraints.
- **Every instruction has a reachable target** Package checks resolve references and CLI
  fallbacks; connected-tool instructions use the actual Codex session names and share
  the authoritative skill text.

## Done when — RK1735

- **Installation is repeatable and reversible** First install, repeat, refresh, check
  and uninstall pass fixture tests while preserving unrelated settings and existing
  Claude wiring.
- **Trust and configuration failures are explicit** Untrusted hooks, malformed TOML and
  missing engines name remedies; check is read-only and no path silently grants trust or
  bypasses review.
- **Committed wiring works on both platforms** A clean project can invoke the selected
  engine with Windows or POSIX paths, including spaces, without relying on a developer
  checkout layout.

## Done when — RK1736

- **Both packages resolve one implementation** Codex and Claude manifests reference
  shipped files and the same engine; schema, version-stamping and package-content checks
  pass.
- **A clean local install loads correctly** The packaged marketplace install works
  outside the checkout, uses the target workspace and preserves explicit hook trust,
  upgrade, disable and removal behavior.

## Done when — RK1737

- **Native enforcement is observed** A packaged Codex session rejects governed patches,
  allows Roadkeep transactions and ordinary edits, and reports Stop findings without
  recursion.
- **Host and workspace regressions are covered** Claude tests pass; isolated projects,
  worktrees, trust states, missing runtimes and plugin update/removal cases have
  reproducible evidence.
- **Compatibility claims match the evidence** The report names tested client versions
  and platforms and distinguishes unsupported or untested surfaces and skipped corpus
  coverage.

## Done when — RK1738

- **A clean adopter can follow the guide** Tested commands cover install, trust, tools,
  skills, workspace selection, update, check, recovery and uninstall from a fresh
  environment.
- **Distribution claims are current and bounded** The guide cites current OpenAI
  requirements and separates verified local use from public submission eligibility and
  untested surfaces.

## Done when — Block M

- **Both agents use the same engine** Codex and Claude share the CLI, schemas,
  repository store and authoritative skills; host-specific adapters do not create a
  second writer.
- **Native enforcement has reproducible evidence** A packaged Codex installation passes
  governed-edit, legal-transaction, workspace-isolation and lifecycle tests, with
  versions and coverage limits recorded.
- **Installation preserves explicit trust and user settings** Clean install, upgrade,
  disable, check and removal preserve unrelated configuration, retain Claude support and
  never grant hook trust automatically.
- **Distribution guidance matches verified support** Adoption instructions reproduce
  tested local installation and distinguish client support from current public-directory
  and local-MCP submission eligibility.

## Non-goals

Deliberately **not** built — check this list before proposing work:

- **No web UI and no server.** Files and a CLI; the store is the repository. A desktop
  reader that only spawns the CLI or MCP server may live here; a service, a database or
  a second writer of the line format may not.
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
