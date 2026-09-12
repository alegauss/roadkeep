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

### §RG212 How an agent looks at a screen

No gate in CLAUDE.md opens the window, so a session that changed a screen improvised a
script to see it and looked for whatever occurred to it.

**Two ways to look, both Playwright.** `npm run shots` (RG209), `--only` naming what a
change touched: a gates-table row, the PNGs read before the commit. And
`@playwright/mcp` in `.mcp.json`, `--cdp-endpoint` at the port `npm run dev:inspect`
opens, to click into a state no fixture reaches. Its documentation names no Electron, so
the attach is proved first; failing it, the skill says the shots are the only way.

**A `screens` skill**, loaded when a screen is edited, listing defects this project has
had:

- a state told by colour alone, or a shade under 3:1 (RG207);
- text clipped or overflowing at 400 wide;
- a sentence unwrapped under the pseudo-locale (RG176);
- a stream that grows the page instead of following (RG206);
- one ground checked and the other assumed;
- the `docs/design/` artboard it answers to, and each departure on purpose.

**What pictures cannot show** is named: keyboard order, a screen reader, motion, each
beside the test that covers it.

Done when the skill loads on a screen edit, the gates table carries the shots, and the
MCP either attaches or is recorded as refused.

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

### §RG211 axe through Playwright over every photographed surface

RG54 holds token pairs to AA and asserts keyboard reach in jsdom. Neither sees what a
component draws: RG207's chosen toggle was the package's accent on a panel, 1.35:1, and
passed both.

**`@axe-core/playwright` on every surface.** Each surface `shots.ts` captures, in both
grounds, is scanned with `AxeBuilder` tagged `wcag2a`, `wcag2aa` and `wcag21aa`. The
report lands beside the PNGs as `a11y.json`, and a `serious` or `critical` violation
fails the run. Axe's own documentation says automated checks find some problems and not
most, so a pass is a floor and never a verdict.

**Exceptions expire.** An accepted finding carries its rule, its selector and a reason,
as `advisories.ts` keeps npm's: one nobody excused fails, and one the report no longer
names fails too.

**What axe does not measure, measured beside it.** A chosen option — `aria-checked`,
`aria-pressed`, `aria-selected` or `aria-current` — must differ from an unchosen sibling
by 3:1 in background, or carry a mark the sibling lacks. Read through `page.evaluate`,
with computed colours resolved by `contrast.ts` so an `oklch` token reads as the window
paints it.

`--a11y-only` scans without writing images.

Done when a surface whose chosen state is told by shade alone fails the run, and RG207's
toggle, which carries a mark, passes.

### §RG213 A browser project beside jsdom, for what only a layout answers

The `ui` project runs in jsdom, which lays nothing out and fakes its events. RG206's
follow tests define `scrollHeight` and `clientHeight` on the region by hand, so they
pass whatever the stylesheet says: a region the CSS never bounds passes them and never
scrolls in the window.

**A `ui-browser` project.** Vitest Browser Mode with `@vitest/browser-playwright`,
headless Chromium, over files named `*.browser.test.tsx`, rendered with
`vitest-browser-react`. It sits beside `ui` in the root config rather than replacing it:
jsdom stays the fast half for what has no layout. `npm test` keeps to jsdom; `test:live`
runs the browser project, since it starts a browser, which is the line RG64 drew, and
the gates table says so.

**The same window.** `drawWindow`, the provider stack and `stubBridge` render unchanged,
with the app's CSS imported so a class is a real rule.

**The first file proves the move.** RG206's three follow tests move here with nothing
measured by hand: acts are appended until the bounded region overflows, the reader
scrolls with the wheel, and `page.viewport` narrows the window to 400 wide.

**CI installs the browser**, `npx playwright install chromium`, beside python.

Done when a region the CSS stops bounding fails `session.browser.test.tsx`, and jsdom's
copies of those tests are gone.

### §RG214 Width, Tab order and a visible focus, asserted in a real page

The design system's contract says a page never scrolls sideways at phone width. RG54
asserts keyboard reach as named controls in document order, read off a DOM with no width
and no focus of its own. A table overflowing at 400 wide, or a toolbar whose Tab order
is not its visual order, passes both.

**Every surface, narrow.** For each routed surface, with the stubs `wording.test.tsx`
already builds for the pseudo-locale run, `page.viewport(400, 800)`, and the document's
`scrollWidth` may not exceed the viewport. What the contract lets be wider — a table, a
diagram, a code block — is recognised by its own `overflow-x: auto` container, never by
a list of exceptions.

**Tab walks it.** `userEvent.tab()` from the top of each surface, a real key through the
DevTools protocol: every control RG54 counts is reached, none twice, and inside the page
each next control sits below or to the right of the last.

**The focus is visible in both grounds**, since a ring is a colour and RG107 was one:
the focused control's computed outline or box shadow is not `none`, and differs from its
unfocused style.

Done when a surface that scrolls sideways at 400 wide, tabs out of reading order, or
focuses without a visible ring fails `surfaces.browser.test.tsx`.

### §RG215 A header and hero that fit at phone width

`npm run shots` at 400 wide shows every surface 499 wide. The header keeps each control
at its desktop size — the brand, the palette trigger at `flex-1`, `?`, the language menu
and the ground in words, `fundo: seguindo o sistema` — so the trigger collapses to a
sliver and the ground runs off the edge. The portfolio's hero sets two actions beside
its title, and the second is cut.

The desktop window has a 900-pixel minimum, so nobody sees this in Electron today. The
contract is about the page, not the window: a served build is a browser tab, and RG214's
gate reads 400.

**The header below `sm`.** The palette trigger is its icon and key hint, still named by
`shell.palette`; `?` hides, since a shortcut sheet is for a keyboard; the ground says
the setting without its `ground:` prefix, through short catalogue keys, its `aria-label`
unchanged — words still, never a lone icon, which the header's own comment rules out.

**A hero's actions wrap.** The trailing node a page passes becomes a wrapping row, so
its buttons fall under the title rather than past the edge; `BentoHero` keeps the layout
around it.

Done when every surface `npm run shots` takes at 400 is no wider than 400 in both
languages, and the header at 1280 draws as it does today.

### §RG216 Counted sentences in the forms each language has

The catalogue fills `{count}` into one sentence per key: `portfolio.title` is `{count}
projetos nesta máquina` and `{count} projects on this machine`, so a machine with one
project reads *1 projetos*, and the tally beside it *1 lidos*. RG209's pictures show it,
and the English is as wrong. `backlog.refused.one` is the one key with a singular,
chosen by hand where it is said.

**A plural form is the language's rule, so it comes from `Intl.PluralRules`.** A counted
key may carry siblings named by the categories CLDR gives — `portfolio.title.one` beside
`portfolio.title`, which stays the `other` form — and `fill` picks by the locale's rule
for the value of `count`. Portuguese and English need `one` and `other`; a language with
more forms adds keys and no code.

**Found, not remembered.** A test walks the base catalogue: every sentence holding
`{count}` has a `.one` sibling, or is named in a short list where one already reads
right — `{count} of {total}`, a label beside a number. `untranslated` then holds every
locale to the same keys, and `backlog.refused.one` moves onto the mechanism, its hand
choice gone.

Done when the portfolio with one project says *1 projeto* and *1 project*, and a new
counted key without a singular fails the catalogue test.
