# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

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

### §RG230 The class pair that cannot win, found

`index.css` imports Tailwind and then `@viglet/viglet-design-system/styles`, which carries its
own compiled utilities in the same `utilities` layer, declared after the app's. So on one
element, a base class the package also ships beats a responsive class for the same property,
at every width. RG229 measured it three ways: `grid-cols-1 sm:grid-cols-[…]` stayed one
column at 1280, `hidden sm:grid` stayed hidden, and `grid max-sm:hidden` stayed visible at
400. Nothing reported any of it — the classes read correctly, and RG223's own test asserted
them.

Layout tests see it only where a surface is measured at both widths. The pair is
findable.

**A scan of the renderer's class strings, beside `check-duplicates`.** For every class
attribute, split the classes into base and responsive (`sm:`, `md:`, `lg:`, `xl:`,
`max-*:`); map each to the CSS property it sets; and fail a responsive class whose
property is also set by a base class that appears in the package's compiled stylesheet.
The package stylesheet is on disk, so which classes it ships is read rather than listed.
The answer names the file, the two classes and the form that works: the desktop value as
a class the package cannot hold, and `max-sm:` over it, or a wrapper that carries the
responsive class alone.

Property mapping is the part to keep small: display, grid-template-columns, gap, and the
alignment utilities are what this app varies by width today.

Done when `grid-cols-1 sm:grid-cols-[…]` in any renderer file fails the lint with its
fix named.
