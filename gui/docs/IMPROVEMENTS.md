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
