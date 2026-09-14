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

### §RG226 Gate assertions that wait on a fact

Three, one task apart each. `carrier.test.ts` during RG217, on RG166's *gates a project
it just opened*; `shots-live.test.ts` during RG221, on RG211's axe scan, which took 39
seconds that run; `source-watch.test.ts` during RG222, on RG57's *ignores a tree nobody
asked for*. Each was green on every run after, and no task touched what its test is
about.

All three are races by construction: the opening hands back before the gate runs, the
scan is a browser working, the watch is the filesystem saying so — and each waits with a
ceiling. A ceiling passes on a fast machine and fails on a loaded one, which is what
1600 tests make.

**What this costs is the gate's meaning.** A red run that means nothing teaches a reader
to run it again, and the next red one — a real one — is read the same way. A flaky test
is how a suite stops being believed.

The fix is to wait on a fact rather than on a deadline: the carrier knows when the gate
it started has settled, the scan knows when axe has answered, the watch knows when it
has fired. Whether each already says so, and what it would take, is the first thing to
read.

Not a rerun and not a longer timeout: both make it rarer and neither makes it mean
something.

Done when each assertion waits on the thing it is about having happened, and a hundred
runs of the fast suite are green.

### §RG227 The rail, held to its drawing

RG127 holds the drawings to the window by marking each drawn control with `data-control`
and each region with `data-region`, and `artboards.test.tsx` renders the window and asks
the two to agree. It reaches the header, control for control. It does not reach the
rail: no tile in `Shell.dc.html` carries a mark, so the drawing's rail and the window's
are never compared.

They differ. The drawing gives the rail five tiles — a grid, a list, a document, an
arrow, and a gear at the foot — and the window draws three: Home, the sessions and the
settings, which is what RG221 made it draw. Before RG221 it drew one, and the drawing
said five then too.

Neither is marked *planned* by the file's own convention, which is a dashed border:
these are drawn solid, so the drawing asserts a rail that has never existed.

**So mark the rail's tiles and let the test fail, then redraw.** The mark is the
section's own id — `data-control="rail-work"` and the like. `BentoNavRail` renders the
package's markup, so the window's side reads the rail's links by their route rather than
by a `data-testid` this app cannot add.

The two tiles the drawing has and the window does not are the interesting half: whether
either is a surface somebody meant to build is a question for whoever redraws it.

Done when `artboards.test.tsx` compares the rail as it compares the header, and the
drawing draws the three tiles the window draws.
