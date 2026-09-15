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
