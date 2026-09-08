# Shipped Ledger

## Block A — The client (payloads in, types out)

- ✅ **RG1** **nothing here invokes roadkeep, so every payload this design rests on is one no code can fetch** — A verb table builds one argv, one transport spawns it with no shell, and four tests fetch real payloads from a live roadkeep (design recorded in `packages/core/src/transport.ts`).
- ✅ **RG2** **the engine is assumed to be a roadkeep on PATH, which is the one thing engines says it may not be** — Each project is asked which copy writes for it, and a modified tree, a disagreement and a machine resolving nothing are answers (design recorded in `packages/core/src/engine-resolution.ts`).
- ✅ **RG3** **a payload arrives as any, so a key renamed upstream is an undefined at run time and never a red build** — Each read declares a shape that yields the typed value or names the field that drifted, blaming the version gap rather than the project (design recorded in `packages/core/src/payloads.ts`).
- ✅ **RG4** **the client's reading of a payload is asserted by nothing, so a rename upstream breaks a user and not a build** — A fixture built by the write verbs is read by every verb this client calls, and two over-strict shapes failed here first (design recorded in `packages/shell/src/contract.test.ts`).
- ✅ **RG5** **a refusal is prose on stderr, so the field it is about has to be read back out of English** — A refused write comes back as its code and field, and the doors that close it read through one shape shared with the gate (design recorded in `packages/core/src/refusals.ts`).
- ✅ **RG6** **nothing checks which build answered, so a project on an older roadkeep fails at the first flag it lacks** — A project is asked once what its build runs and which flags it takes, so a door is withheld rather than refused later (design recorded in `packages/core/src/capabilities.ts`).
- ✅ **RG7** **every read costs an interpreter start, so a screen over twenty projects pays twenty of them to redraw** — A read is keyed by the project, the argv and a stamp of the files it declares, so an unchanged project is not read twice (design recorded in `packages/core/src/cache.ts`).
- ✅ **RG8** **a read has no ceiling, so one project whose engine hangs stops the screen that was drawing it** — Calls run through a pool of settable width under a settable deadline, and one that runs out becomes a state on that project (design recorded in `packages/core/src/limits.ts`).
- 🗑 **RG70** **twenty projects stamped and read in turn wait on each other, because nothing runs two calls at once** — superseded by RG8: Filed before RG8 was read: its design already names the pool, and one pool both introduces concurrency and bounds it.
- ✅ **RG69** **a subcommand is a verb with a space in it, and the verb table has no way to spell one** — A verb's key is an identifier and its spelling is an array, so a two-word verb is looked up and sent under the name commands publishes (design recorded in `packages/core/src/verbs.ts`).
- ✅ **RG79** **an unreadable answer reports not JSON and drops stderr, where the engine explained itself in full** — An answer this app cannot read now carries what the engine wrote, so the sentence naming the cause reaches the person (design recorded in `packages/core/src/limits.ts`).

## Block B — Discovery (which checkouts on this machine are governed)

- ✅ **RG10** **no root is named, so there is nowhere to look and the project list can only come back empty** — A root is a folder somebody named with a bounded depth, there is no default, and one that stopped existing is kept and marked (design recorded in `packages/core/src/roots.ts`).
- ✅ **RG11** **a scan descends into node_modules and .git, so finding seventeen projects reads a hundred thousand folders** — The walk looks for one filename, refuses an ignored or hidden directory, stops at the declared depth and never enters a project it found (design recorded in `packages/core/src/scanning.ts`).
- ✅ **RG12** **a git worktree family reads as unrelated projects, so one backlog appears once per version folder** — A junction collapses onto the folder it names and two worktrees group by the git directory they share, read off git's own files (design recorded in `packages/core/src/families.ts`).
- ✅ **RG14** **the whole tree is walked again on every launch, so a list the person already approved is rediscovered** — The list is a record a rescan diffs rather than rebuilds, and a project it no longer finds is marked missing and kept (design recorded in `packages/core/src/catalogue.ts`).

## Block C — The portfolio (many backlogs in one view)

- ✅ **RG16** **nothing shows more than one project, which is the single thing this app exists to do** — One row per project holding only numbers a verb printed, pending until read, and nothing added up across them (design recorded in `packages/core/src/portfolio.ts`).
- ✅ **RG17** **twenty projects are read one after another, so the first screen is a wait with nothing drawn on it** — Every project goes out at once through the pool, rows stream in as they land in recorded order, and the cheap read fills the screen first (design recorded in `packages/core/src/cold-start.ts`).
- ✅ **RG18** **whether a project's gate passes is unknown until it is opened, so the list cannot say which one needs attention** — A row shows the last verdict with when it was taken, unknown until a run has earned one, and stale the moment the files move (design recorded in `packages/core/src/gate.ts`).
- ✅ **RG19** **what to work on is asked one repository at a time, so there is no answer that ranges over all of them** — Every project's candidate is laid out together with the tier that chose it, in the person's own project order and ranked by nothing here (design recorded in `packages/core/src/candidates.ts`).
- ✅ **RG20** **finding a line by its words means opening each project and reading its list in turn** — Search runs over held payloads across every backlog, matches id, symptom and why, and names any project it could not cover (design recorded in `packages/core/src/search.ts`).

## Block D — The project surface (one backlog, read)

- ✅ **RG21** **opening a project shows counts and no lines, so the backlog it governs is still only in the file** — A project opens into its blocks in heading order, with the lines the grammar refused drawn beside the ones it accepted (design recorded in `packages/core/src/backlog.ts`).
- ✅ **RG22** **a list of eight hundred lines has no filter, so a block or a marker is found by scrolling to it** — Every filter is an argument the read already takes, so a narrowed list is the command's own answer and the choices are read from the project (design recorded in `packages/core/src/filters.ts`).
- ✅ **RG23** **a task has no detail, so the why, the deps and the design are read in the file this app exists to replace** — One brief read carries the line, its resolved deps, the design whole, what a ship unblocks and the lists that bind it, composed by nothing here (design recorded in `packages/core/src/detail.ts`).
- ✅ **RG24** **the rationale section is not shown, so the half of a task that explains it stays invisible** — A task's rationale opens with it: the prose byte for byte, where it lives, and what it has left of the word budget the gate will use (design recorded in `packages/core/src/design.ts`).
- ✅ **RG25** **deps and what a ship unblocks are a list of ids, so following a chain means reading ids one at a time** — A line's deps open as the graph the engine resolved: blockers, chains drawn whole, the cascade a ship frees, and a dep outside told apart (design recorded in `packages/core/src/graph.ts`).
- ✅ **RG26** **the non-goals and the criteria are off screen, so the two lists that bind a proposal are the two nobody reads** — Both binding lists are reads: the non-goals with the designs answering each, and criteria grouped whole, three empties apart (design recorded in `packages/core/src/binding.ts`).
- ✅ **RG27** **the ledger and the decisions file are unreachable, so what shipped and what was weighed live outside this app** — The ledger and the reversals are reads: what a block delivered, the five nearest a sentence, and what the ledger undid (design recorded in `packages/core/src/memory.ts`).
- ✅ **RG28 (the store, read)** **the deferred store is invisible, so a paused line cannot be told from one that was never filed** — The deferred store is a listing like any other, and an id now answers open, shipped, paused or nowhere.

## Block E — The write path (the app composes an argv; the command writes)

- ✅ **RG29** **the app reads and never writes, so a correction is typed in the terminal this app exists to replace** — A write is a composed argv this app never runs against a file: applied, refused with its fields, or unreadable (design recorded in `packages/core/src/writing.ts`).
- ✅ **RG30** **a marker cannot be moved, so starting work is a shell command run beside the window that shows it** — A marker moves through the verb: the open set comes from config, and the answer says whether the claim was taken or given back (design recorded in `packages/core/src/marking.ts`).
- ✅ **RG31** **there is no door for ship, retire, defer or resume, so a task is read here and closed elsewhere** — Ship, retire, defer and resume are doors, each answering with the edits it made across the files it touched (design recorded in `packages/core/src/leaving.ts`).
- ✅ **RG32** **a rationale section cannot be written, so a line filed here points at nothing until a terminal is opened** — A rationale is written where the pointer points, and corrected as a fragment the verb matches rather than the caller (design recorded in `packages/core/src/sections.ts`).
- ✅ **RG33** **a lint finding is a line of text, so a report naming its own doors arrives as something to read and not to run** — A finding is offered as the door that closes it: run where complete, a form where not, and the repair pass dry first (design recorded in `packages/core/src/repairing.ts`).
- ✅ **RG34** **the argv the app composed is never shown, so a write cannot be read before it runs or repeated after it** — The argv is a line a person can read before it runs and paste after it, and a transcript keeps what ran with its exit code (design recorded in `packages/core/src/transcript.ts`).
- ✅ **RG35** **amend, restate and renumber have no door, so the corrections that keep an id are terminal-only** — The three corrections that keep an id are doors, each offered with the sentence the engine publishes for it (design recorded in `packages/core/src/correcting.ts`).
- ✅ **RG36** **an input has no budget, so a field is typed to whatever length and refused after the sentence exists** — Every field is priced before a word is typed, counted against what the line allows rather than what the limit says (design recorded in `packages/core/src/budgeting.ts`).

## Block F — The agent surface (handing one task to Claude Code)

- ✅ **RG38** **nothing starts Claude Code, so a task and the session that does it are two windows and a copied prompt** — A session starts from the brief payload itself, owned and killable, with no claude on the machine its own state (design recorded in `packages/core/src/session.ts`).
- ✅ **RG40** **a session's output is a stream nothing renders, so what the agent is doing is invisible while it does it** — A session reads as acts: which tool on what, the roadkeep calls marked, and every raw line still reachable (design recorded in `packages/core/src/acts.ts`).
- ✅ **RG41** **a line is handed over without being taken, so two sessions can be started on the same task** — Handing a task to a session takes it: brief and claim are one call, and a held line is named instead of offered (design recorded in `packages/core/src/handover.ts`).
- ✅ **RG43** **the claude binary is assumed to exist, so a machine without it fails at the moment work starts** — The command that runs a session is resolved and named like the engine, and a machine without one is a stated condition (design recorded in `packages/core/src/agent.ts`).
- ✅ **RG42** **what a session wrote to the governed files is not watched, so the screen shows the backlog from before it ran** — What a session did is read off the files it changed: the marker, the design and the ledger, beside what it said (design recorded in `packages/core/src/landing.ts`).

## Block G — The shell (an executable now, a service later)

- ✅ **RG37** **there is no application at all: no window, no build and no way to run any of this** — A window opens over three packages, with one typecheck spanning them and a headless suite over both halves (design recorded in `packages/core/src/packages.ts`).
- ✅ **RG44** **the renderer holds node powers, so the half a service would serve to a browser can delete a file** — The renderer has a browser's powers and one frozen typed object, and every navigation off the bundle is refused or sent to the system browser (design recorded in `packages/core/src/bridge.ts`).
- ✅ **RG45** **nothing watches the governed files, so a write by an agent or a terminal leaves the screen stale** — The governed files a project declares are watched while somebody holds it, and a burst of writes tells the screen once (design recorded in `packages/core/src/watching.ts`).

## Block H — The look (a design system for governed prose)

- ✅ **RG39** **there is no design system, so every screen decides its own type, spacing and colour on the spot** — Every colour, radius and face comes from the design system Turing, Shio and Dumont render with, and a test fails any component that names one.
