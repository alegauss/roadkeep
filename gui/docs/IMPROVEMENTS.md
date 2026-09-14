# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

### §RG225 The session at phone width, stream first

RG217 gives the stream the room under its own top, never under a 20rem floor. At 1280 by
800 that lands: the region ends inside the window and *Jump to latest* is drawn at about
732. At 400 the columns stack, the region's top is past the middle of an 800-tall
window, and what is under it is less than the floor — so the floor answers and the page
scrolls. RG217's pictures show it.

The floor is right and is not what to change: a scroll region of two hundred pixels is
one a reader fights, and a page that scrolls is the honest answer. What is left is that
the surface puts two panels *above* the stream at that width — what was handed over, and
what moved — so the words a reader opened the screen for start below the fold whatever
the region does.

**So this is about the order, not the height.** Below `lg` the stream comes first and
the other two follow, which is the reading order a person wants: the session's own
words, then what it was handed, then what moved. Above `lg` nothing moves — the three
columns are the drawing.

Reading order is what a Tab walks, so `surfaces.browser.test.tsx` holds it: RG214's rule
is that each next control sits below or to the right of the last, at 400 as well as at
1280.

Done when the session at 400 wide draws the stream's newest act inside the window.

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

### §RG226 A gate assertion that waits on a fact

`carrier.test.ts` turned red once during RG217 on RG166's *gates a project it just
opened, without the opening waiting for it*, and was green on the next four runs — twice
alone and twice whole. Nothing in RG217 touches the carrier, so what moved was timing.

The claim is about a race by construction: the opening hands back before the gate has
run, and the test then waits for the gate to have run. A wait with a ceiling passes on a
fast machine and fails on a loaded one, which is what a suite of 1600 tests on a busy
laptop is.

**What this costs is the gate's meaning.** A red run that means nothing teaches a reader
to run it again, and the next red one — a real one — is read the same way. One flaky
test is how a suite stops being believed.

The fix is to make the wait a fact rather than a deadline: the carrier knows when the
gate it started has settled, so the test waits on that rather than on the answer
appearing within some number of milliseconds. Whether the carrier already exposes it,
and what it would take to, is the first thing to read.

Not a rerun and not a longer timeout: both make the failure rarer and neither makes it
mean something.

Done when the assertion waits on the carrier saying the gate has run, and a hundred runs
of the fast suite are green.
