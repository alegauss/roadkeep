# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

### §RG228 The sessions list at phone width

The sessions list is `grid-cols-[8rem_minmax(0,1fr)_8rem]`, on a heading row and on
every session row. The two fixed columns are 16rem before the gaps, so at 400 wide the
middle one is about 70 pixels: RG223's pictures show the headings *Project* and *State*
drawn over each other, and each project's name and root cut to a letter and an ellipsis.

It is RG223's defect on another surface, and it did not take RG223's fix because the
shape is not the same. The project tabs' rows stand alone; this list has a row of column
headings above its rows, and a heading row that stays three columns over rows that stack
names nothing.

**Below `sm` the headings go and each row says its own.** The row stacks — the line's id
as the link, the project under it, the state last — and the heading row is hidden, since
a column is what a heading names and there are none. The state keeps its pill, which
already says what it is; the project keeps its name and root, which read as a project
without a label.

Above `sm` nothing moves.

The link keeps its `aria-label`, which names the line it opens, so a stacked row is
announced the way a gridded one is. `surfaces.browser.test.tsx` holds the sideways
scroll and the Tab order, and neither changes.

Done when the sessions list at 400 wide draws each project's name whole, and no two
words on it are drawn over each other.

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

### §RG226 A close that answers once nothing on its profile stands

Landed: the carrier's gate tests wait on `gatesSettled`, and the source-watch fixture
sets each directory's times before a watch starts — under load a fresh tree reported
`change: deep` with nothing written in 19 rounds of 30, and 0 of 30 once set. Both were
held under two busy loops a core.

**Left: `shots-live.test.ts`, RG220's kill and RG209's close.** Measured on Windows:
`app.process()` is a launcher, the Electron main is its child, and a successful
`taskkill /T /F` left the main, its GPU and its utility process listed with threads and
hundreds of handles seconds later. `close()` returned before the child's `exit` event,
so `exited()` read false.

Tried and not enough. `Wait-Process` returns at once: Chromium's sandboxed children
refuse another process the access a wait needs. Asking `Win32_Process` again until
nothing on the profile is listed, killing whatever remains by id each round, fixed the
kill test — and then in one plain `npm run test:live` of three the close waited its
whole 45-second ceiling with something still standing on the profile. The old close
never looked, so that process may always have outlived a close.

**So the next step is naming it.** When the wait trips its ceiling, log each process
still listed with its parent and its `--type`, over a few full runs, then decide whether
it is Electron's to end or this run's.

Done when a close and a failed launch answer only once nothing on their profile stands,
and three full live runs are green.

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
