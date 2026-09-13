# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

### §RG217 A stream region measured to the space it has

RG206 bounded the stream region at `calc(100dvh - 12rem)`. At 1280 by 800 the header and
the session's hero take about 290 pixels, not 192, so the region runs some 150 pixels
past the bottom of the window. RG210's pictures show it: following keeps the region at
its own end, and that end is off screen; scrolled up, *Jump to latest* is drawn below
the fold. A reader still scrolls the page to see the newest act, which is the complaint
RG206 answered.

**The height is measured, not guessed.** A fixed subtraction is wrong for every hero
that wraps differently — a long symptom, a second language, a narrower window. The
region takes the space from its own top to the bottom of the viewport, less the page's
bottom gutter, read with `getBoundingClientRect` on mount and on every resize, and never
less than 20rem, below which the page scrolls instead.

**Against the document, not the viewport**, so a reader who scrolled the page a little
does not shrink it.

jsdom measures nothing, so the rule — top, viewport, gutter and floor in, a height out —
is a pure function beside `follow.ts`, and RG213's browser project is where the layout
is held.

Done when `npm run shots` shows the session's newest act and the jump control inside the
window at 1280 by 800 and at 400 wide.

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

### §RG221 A rail that reaches every area it holds

`BentoNavRail` draws one tile per **section**, from `section.areaRoute` and
`section.icon`, and its first act is `groups.filter((group) =>
!!group.section.areaRoute)`. `AREAS` declares its three sections with an `id` and a
`labelKey` and puts the route and the icon on the *items* inside them — which the rail
never reads. So the rail is the Home tile and nothing else, and the settings and the
sessions are reached by the palette or by typing a route.

The palette does reach them, which is why this has been invisible: `surfacesIn(AREAS)`
flattens the items and the palette lists all three. A reader who has not learnt `Ctrl K`
has one button in a nav that is the design system's primary one.

**Each section carries its own route and icon.** `backlogs` is the portfolio at `/`,
which is where the Home tile already leads — so that group's tile is the duplicate to
drop rather than draw twice. `work` is `SESSIONS_ROUTE` with `IconTerminal2` and `app`
is `SETTINGS_ROUTE` with `IconSettings`, the icons their single items already name.

The label under each tile is `section.labelKey`, which the three sections already
declare and the catalogue already holds.

**Below `md` the rail is gone by contract**, so the palette stays the narrow window's
nav and nothing here changes that.

Done when the rail draws a tile for the sessions and one for the settings, each leading
to its surface and named in both languages, and `artboards.test.tsx` holds the drawings
to the same chrome.

### §RG222 Pictures of the tree the run was asked about

`npm run shots` is `npm run build:app && node packages/shell/dist/shots.js`, and
`build:app` is `tsc -b` plus the shell's own bundle. The renderer is the other half of
`npm run build`, and the window the pictures come from loads it off disk — so a change
to a screen is photographed as it was at the last full build.

Measured on RG215: the header fix was on disk, the tests were green, and two runs of
`shots` photographed the old header. Nothing reported anything; the pictures simply
described an older bundle, which is the failure this gate exists to prevent.

`refuseIfStale` is the guard and it reads the shell's build alone (RG209), so it is
silent about the renderer for the same reason.

**The command builds what it photographs.** `shots` runs `npm run build`, which is
`build:app` plus `@rk/ui`. It is a second or two on a warm tree and it is the whole of
the fix; the `shots` step in the gates table already tells a reader to run it after a
screen change.

**And the guard covers both halves.** `refuseIfStale` compares `packages/ui/dist`
against `packages/ui/src` as it compares the shell's, so a picture taken by something
other than this command — an agent calling `shots.js` directly — is refused rather than
misread.

Done when a screen changed but not built is photographed as it now is, and a stale
`packages/ui/dist` refuses the run.

### §RG223 A line that reads at phone width

A line in the project's roadmap tab is `grid grid-cols-[6rem_minmax(0,1fr)_11rem]`: the
id and marker, the symptom, then the readiness and its button. The two fixed columns are
17rem before the gaps, which at 400 wide leaves the middle one about ten pixels — so
RG215's pictures show the symptom set one letter per line, a column of single characters
running down the card.

It is not an overflow: the page does not scroll sideways, and the phone-width gate RG214
builds would pass it. What it is is the sentence a reader came for, unreadable.

**One column below `sm`.** The row stacks: the id and marker on their own line, the
symptom under them, the readiness last — `grid-cols-1
sm:grid-cols-[6rem_minmax(0,1fr)_11rem]`, with the gap the stack needs. Reading order is
already the order the cells are written in, so nothing moves but the shape.

The same three-column shape appears in the changelog, the improvements and the deferred
tabs, and in the portfolio's table, which has its own answer: `min-w-[56rem]` inside an
`overflow-x-auto` panel, which the contract allows and a reader scrolls. This is about
the rows that are not in that table.

Done when the roadmap tab at 400 wide draws each line's symptom across the card, and the
four tabs of the project surface look like one screen at both widths.

### §RG224 The phone-width run, in the language that overflows

`surfaces.browser.test.tsx` draws each surface at 400 wide in whatever i18next is
speaking, which under the browser project's setup is English. RG215's own defect was
Portuguese: `Acrescentar uma dependência` beside its box is wider than a phone-width
column, and the English `Add a dependency` is not.

Measured while RG214 was built. With RG215's `hero-actions` rule taken out of the
stylesheet, the portfolio and the project surface overflow at 400 in Portuguese — 475
and 461 pixels in a window of 400 — and nothing overflows in English. So the gate that
replaced forty hand-read pictures would not have caught the defect those pictures found.

**Both languages, per surface.** `atSurface` already takes a wording and `LOCALE_TAGS`
names what this build ships, so the run loops over the tags rather than over a second
list: a language added to the catalogue is one this reads the day it ships. Sixteen
measurements instead of eight, each a viewport and a render, on a project that already
starts a browser.

Not the pseudo-locale, though it is longer still: brackets around every value measure a
window nobody opens, and a failure there could not be told from one a reader would meet.
The claim is about the languages this build speaks.

Tab order and the focus ring stay in one language. Neither moves with a translation, and
the walk is the expensive half of the file.

Done when a surface that fits in English and overflows in Portuguese at 400 wide fails
`surfaces.browser.test.tsx`.
