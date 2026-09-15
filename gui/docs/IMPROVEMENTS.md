# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

### §RG241 Keeping the portfolio's order across launches

**One preference row, the way RG208 added one.** `Settings` gains `portfolioOrder`, a
value naming both the order and its direction, so the reader checks one closed set. An
`isRowOrder` beside `isSessionNotes` is that set, used by `readSettings` and by the
`PREFERENCES` table alike. A value this build does not know resets with a `Lost` code of
its own and a sentence in both catalogues through `RESET_TEXT`, never silently.

**Default: the record's order**, so an upgrade changes nothing on screen.

**Held for the window like the session notes.** `LaunchChoices` carries the value
across, and `preferring.ts` holds it beside `sessionNotes` rather than growing a second
store. `Portfolio.tsx` reads it through a subscription; a click on a column head redraws
first and then calls `savePreference`, and a write that fails raises the toast that says
the next launch will not have it.

**Only the choice is kept, never the ranking.** RG240 holds a list of paths while a read
is in flight; written to disk, that list would be a copy of what `stats` printed, which
`No store of its own` refuses. The next launch ranks afresh when its first read settles.

**The filter chip stays per window.** A narrowing left on hides rows at the next launch
with nothing on screen saying why, and an order hides none.

Tests: the settings round trip and the reset in `settings.test.ts`, the new row in
`preferences.test.ts`, and a portfolio opening in the order the file holds.

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

## Block G — The shell (an executable now, a service later)

### §RG49 The signature, and what it needs that code cannot supply

Signing is not work that can be finished by writing anything: it needs a certificate
somebody bought, held somewhere a build can reach. So the line states the requirement
and is set aside for a caller that says it has one, rather than coming back as the next
ready task forever. What can be built without it is the pipeline that would use it, and
the about surface saying plainly that this build is unsigned — which is the honest half
and is worth having on its own.

## Block H — The look (a design system for governed prose)

### §RG62 Joining the checks the other consoles already answer to

Depending on the design system is half of consuming it. The other half is the two
mechanisms Shio and Dumont run.

**The gate is done.** `viglet-ds-check-duplicates` is wired into `npm run lint` over the
three source roots, and a test plants a duplicate and requires it to be found — because
a gate pointed at the wrong directory reports a clean tree in exactly the same words as
a clean tree, which is what both consoles learned the hard way.

**Registration is not, and is deliberately not.** The package's `consumers.json` is the
declared set it holds itself to, and its own reasoning says prose naming a subset as
though it were the whole is a test failure. The entry this app wants is:

```
{ "id": "roadkeep-gui", "name": "roadkeep", "package": "@rk/ui",
  "framework": "vite", "chrome": "console",
  "entries": [".", "./styles", "./fonts", "./preset"] }
```

`accent` is the field to stop at. Every one of the six consumers records `cool`, and the
file says so on purpose: the accent was made a token so a product could re-key without
forking a header, and none had. This app has — amber, in its own `:root`. So adding it
is not a row, it is the first case that file was written to anticipate, and the parity
digest is then required to carry that set.

That is a commit in somebody else's repository with a consequence for five other apps,
which is why it is written down here rather than made quietly.
