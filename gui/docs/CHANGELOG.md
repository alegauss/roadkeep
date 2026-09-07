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

## Block B — Discovery (which checkouts on this machine are governed)

- ✅ **RG10** **no root is named, so there is nowhere to look and the project list can only come back empty** — A root is a folder somebody named with a bounded depth, there is no default, and one that stopped existing is kept and marked (design recorded in `packages/core/src/roots.ts`).
- ✅ **RG11** **a scan descends into node_modules and .git, so finding seventeen projects reads a hundred thousand folders** — The walk looks for one filename, refuses an ignored or hidden directory, stops at the declared depth and never enters a project it found (design recorded in `packages/core/src/scanning.ts`).
- ✅ **RG12** **a git worktree family reads as unrelated projects, so one backlog appears once per version folder** — A junction collapses onto the folder it names and two worktrees group by the git directory they share, read off git's own files (design recorded in `packages/core/src/families.ts`).
- ✅ **RG14** **the whole tree is walked again on every launch, so a list the person already approved is rediscovered** — The list is a record a rescan diffs rather than rebuilds, and a project it no longer finds is marked missing and kept (design recorded in `packages/core/src/catalogue.ts`).

## Block C — The portfolio (many backlogs in one view)

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

## Block G — The shell (an executable now, a service later)

- ✅ **RG37** **there is no application at all: no window, no build and no way to run any of this** — A window opens over three packages, with one typecheck spanning them and a headless suite over both halves (design recorded in `packages/core/src/packages.ts`).
- ✅ **RG44** **the renderer holds node powers, so the half a service would serve to a browser can delete a file** — The renderer has a browser's powers and one frozen typed object, and every navigation off the bundle is refused or sent to the system browser (design recorded in `packages/core/src/bridge.ts`).

## Block H — The look (a design system for governed prose)

- ✅ **RG39** **there is no design system, so every screen decides its own type, spacing and colour on the spot** — Every colour, radius and face comes from the design system Turing, Shio and Dumont render with, and a test fails any component that names one.
