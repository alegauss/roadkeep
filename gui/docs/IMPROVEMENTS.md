# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

### §RG239 Ordering the portfolio by name

**One order rule in core, one control on the table.** `portfolio.ts` gains `RowOrder`,
`'record' | 'name'` here and the count order after it, and `orderRows(rows, order,
locale)`: pure, a new list, the record's order handed back untouched. `Portfolio.tsx`
filters and then orders inside the one `shown` memo, so a chip and an order compose. The
design system's `Table` has no sorting, so the control is this app's: a button inside
the Project `th`, which carries `aria-sort`, cycling A to Z, Z to A and back to the
record's. `portfolio.order` stops being a fixed caption and names the order in force, in
both catalogues (RG125); `Main.dc.html` draws that caption and is redrawn with it.

**Names compared as a person reads them.** `Intl.Collator` over the window's locale,
with `numeric` and `sensitivity: 'base'`, as `orderMembers` chose: `2026.10` follows
`2026.2` and case does not split one name in two.

**Ties keep the record's order, both ways.** Rows sharing a declared name are one
family's worktrees, current version first. The sort is stable and Z to A negates the
comparison rather than reversing the list, so that order survives.

**A name is on the record before any read** (RG203), so this order holds through a cold
start. A name declared since the last scan moves its row once, as it lands.

**Not remembered across launches.** That is a row in RG207's preference table, and a
line of its own when somebody asks.

### §RG240 Ranking the portfolio by open lines

**The key is `counts.total`**, the number `stats` printed for that row and the Backlog
column already draws as open. Ranking by it compares rows and adds nothing up, which
keeps block C's first criterion.

**Most open first, then fewest, then the record's**: RG239's three-state `th` control,
now on Backlog, with `'open'` added to `RowOrder`. Ties keep the record's order.

**A row with no count sorts after every row with one**, in the record's order, whichever
way the ranking runs. A pending row placed as zero breaks block C's second criterion as
an order, and an unreadable row has no count to rank.

**Rows do not move under a read.** `coldStart` refuses completion order because the row
about to be clicked moves, and a count landing would move it the same way. So the
ranking is a list of paths, taken when the order is chosen and again when
`view.progress` goes null. While a read is in flight each row keeps the place that list
gives it, and a row it does not name follows in the record's order. A cold start draws
the record's order and re-ranks once, as the progress line leaves; a rescan keeps the
last ranking until it settles. The test keeping a row where the record put it gains a
twin under this order.

**Filters compose.** `drifted` ranked by open lines says which broken backlog to repair
first, and neither rule knows the other.

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

### §RG238 The ground as the design system's ModeToggle

**The package already ships it.** `ModeToggle`, exported by the installed 2026.3.10, is
a sun and moon trigger opening a menu of light, dark and system, worded from the
package's own `theme.*` catalogue in both locales. Turing's console re-exports it
(`turing-app/src/components/mode-toggle.tsx`) and keeps no copy, so nothing moves into
the package and nothing is bumped. It replaces the outline button in `Shell.tsx`, inside
a `contents` span carrying `data-testid="ground"`, the way the language control is held.

**The write moves off the control.** `ModeToggle` calls the package's `setTheme` itself,
so `keepGround` never runs: the choice reaches the browser cache alone, and the next
launch seeds that cache from the file and loses it. RG116 met the same gap for the
language by hanging the write on i18next's own event. The ground gets that keeper on
`next-themes` changing `theme` inside `GroundProvider`, compared against what the file
holds so the launch is not a write. `cycle`, `THEME_TEXT`, `THEME_SHORT` and
`ground.action` go where nothing else reads them.

**What is traded.** The trigger shows the painted ground, so `system` stops reading off
the header; the menu names all three. That reverses the header comment RG215 left,
"never a glyph", and block H's colour criterion still holds: the icon is a shape and the
menu is words. `Main.dc.html` and `Shell.dc.html` draw `ground: light` and are redrawn
with the icon.
