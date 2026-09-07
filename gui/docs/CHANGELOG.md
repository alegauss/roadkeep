# Shipped Ledger

## Block A — The client (payloads in, types out)

- ✅ **RG1** **nothing here invokes roadkeep, so every payload this design rests on is one no code can fetch** — A verb table builds one argv, one transport spawns it with no shell, and four tests fetch real payloads from a live roadkeep (design recorded in `packages/core/src/transport.ts`).
- ✅ **RG2** **the engine is assumed to be a roadkeep on PATH, which is the one thing engines says it may not be** — Each project is asked which copy writes for it, and a modified tree, a disagreement and a machine resolving nothing are answers (design recorded in `packages/core/src/engine-resolution.ts`).
- ✅ **RG3** **a payload arrives as any, so a key renamed upstream is an undefined at run time and never a red build** — Each read declares a shape that yields the typed value or names the field that drifted, blaming the version gap rather than the project (design recorded in `packages/core/src/payloads.ts`).
- ✅ **RG4** **the client's reading of a payload is asserted by nothing, so a rename upstream breaks a user and not a build** — A fixture built by the write verbs is read by every verb this client calls, and two over-strict shapes failed here first (design recorded in `packages/shell/src/contract.test.ts`).

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

## Block G — The shell (an executable now, a service later)

- ✅ **RG37** **there is no application at all: no window, no build and no way to run any of this** — A window opens over three packages, with one typecheck spanning them and a headless suite over both halves (design recorded in `packages/core/src/packages.ts`).
- ✅ **RG44** **the renderer holds node powers, so the half a service would serve to a browser can delete a file** — The renderer has a browser's powers and one frozen typed object, and every navigation off the bundle is refused or sent to the system browser (design recorded in `packages/core/src/bridge.ts`).

## Block H — The look (a design system for governed prose)

- ✅ **RG39** **there is no design system, so every screen decides its own type, spacing and colour on the spot** — Every colour, radius and face comes from the design system Turing, Shio and Dumont render with, and a test fails any component that names one.
