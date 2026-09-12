# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

### §RG210 A scripted agent the unpackaged app can be pointed at

`agentCandidates` looks on PATH and under the install folders, and `fake-claude.ts`
lives only inside the live suite. RG206 and RG208 shipped with the session screen seen
by jsdom alone: following, the jump control and a folded run have never been drawn in a
real layout.

**`ROADKEEP_AGENT`, read only unpackaged.** A JSON argv put first among the candidates
when `app.isPackaged` is false, and ignored otherwise, so a shipped window never runs an
agent a variable chose. The session screen already names the command it started, so a
fake shows as one.

**The fake answers what resolution asks.** `--version` prints a version line and `auth
status` a login, so RG43 and RG205 resolve it like the real one. Its session replays a
stream file, `captured/session-stream.jsonl` by default, one line per interval, with
notes, tool calls and a long tail, so a run is mid-stream when it is photographed.

**Shots take a session.** `shots.ts` hands a fixture line over through the bridge, waits
for a number of lines, and captures the session surface following, scrolled up with the
jump control showing, and with notes folded.

Done when `npm run shots` leaves session screens mid-run in both note choices, and a
packaged build ignores the variable.

## Block G — The shell (an executable now, a service later)

### §RG49 The signature, and what it needs that code cannot supply

Signing is not work that can be finished by writing anything: it needs a certificate
somebody bought, held somewhere a build can reach. So the line states the requirement
and is set aside for a caller that says it has one, rather than coming back as the next
ready task forever. What can be built without it is the pipeline that would use it, and
the about surface saying plainly that this build is unsigned — which is the honest half
and is worth having on its own.

### §RG209 Every surface photographed, in both grounds, both languages and two widths

`running-app.ts` starts the built app and speaks the DevTools protocol, and only the
live suite uses it. RG207's toggle was checked by a scratch script that launched it, set
a hash and called `Page.captureScreenshot`: the chosen option sat at 1.35:1 against its
panel, which no jsdom test can see.

**`npm run shots`.** `shots.ts` refuses a stale build as the live suite does, builds a
fixture project with the live engine, seeds a throwaway profile naming it, and starts
the app. Each routed surface, its parameters filled from the fixture, is visited in both
grounds, in `en` and `pt-BR`, at 1280 by 800 and at 400 wide. Each PNG lands in
`.shots/`, gitignored, beside an `index.json` naming route, ground, language, width,
build and whether it settled.

**Settled is measured, not slept.** Nothing `aria-busy` and no DOM change for 400 ms,
bounded at 10 s; a surface that never settles is captured anyway and says so.

**One list of surfaces.** The route patterns move to `core`, `areas.ts` re-exports them
and `routes.tsx` keeps the elements, so a surface routed without a shot fails
`shots.test.ts`.

`--only <route>` narrows a run to what a change touched.

Done when one command leaves a PNG per surface, ground, language and width, and an index
saying which settled.

### §RG212 How an agent looks at a screen

CLAUDE.md is an index of gates, and none of them opens the window. A session that
changed a screen so far improvised a script to see it, and looked for whatever occurred
to it.

**A row in the gates table.** `npm run shots` for any change under `packages/ui/src`
that draws, `--only` naming the surfaces touched, and the PNGs read before the commit.

**A `screens` skill**, loaded when a screen is edited, holding what the pictures are
checked for. Each item is a defect this project has had:

- a state told by colour alone, or by a shade under 3:1 (RG207);
- text clipped, overflowing or wrapping into a control at 400 wide;
- a sentence left unwrapped under the pseudo-locale (RG176);
- a stream that grows the page instead of following in its region (RG206);
- one ground checked and the other assumed;
- the artboard in `docs/design/` the surface answers to, and each departure from it on purpose.

**What the pictures cannot show** is named too: keyboard order, a screen reader's
reading, motion, and a state no fixture reaches, each beside the test that covers it
instead.

Done when the skill loads on a screen edit naming the command, the checklist and the
limits, and the gates table carries the row.

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

### §RG211 An accessibility pass over every photographed surface

RG54 holds token pairs to AA and asserts keyboard reach in jsdom. Neither sees what a
component draws: RG207's chosen toggle was the package's accent on a panel, 1.35:1, and
passed both.

**axe over the running page.** `axe-core`, a dev dependency, is injected over the
DevTools protocol into each surface `shots.ts` visits, in both grounds, and its report
is written beside the PNGs as `a11y.json`. A `serious` or `critical` finding fails the
run.

**Exceptions expire.** An accepted finding carries its rule, its selector and a reason,
as `advisories.ts` keeps npm's: one nobody excused fails, and one the report no longer
names fails too, so the list stays a record of what is true.

**What axe does not measure, measured here.** A chosen option — `aria-checked`,
`aria-pressed`, `aria-selected` or `aria-current` — must differ from an unchosen sibling
by 3:1 in background, or carry a mark the sibling lacks: an element or text of its own.
Computed colours go through `contrast.ts`, so an `oklch` token reads as the window
paints it.

`--a11y-only` runs the pass without writing images.

Done when a surface whose chosen state is told by shade alone fails the run, and RG207's
toggle, which carries a mark, passes.
