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

### §RG231 The shortcuts button, hidden by a wrapper

RG215 hid the shortcuts button below `sm`, since a sheet of keyboard shortcuts is for a
window with a keyboard. It wrote `className="max-sm:hidden"` on the design system's
`Button` — and every 400-wide picture since draws the `?` beside the palette trigger.

RG230's measurement says why. The `Button` merges its own classes onto the same element,
and `inline-flex` is one: the package's stylesheet ships `inline-flex`, declared after
this app's utilities, and ships no `max-sm:hidden`. So `inline-flex` wins at every
width. The class pair is real, but half of it is inside the component, which is the one
shape RG230's scan of this app's source says it cannot see.

**A wrapper carries the width, and the button carries nothing about it.** The same form
the sessions list's heading row took: `<span className="max-sm:hidden">` around the
`Button`, holding no `display` class for the package to outrank. The header's flex row
lays a span out as it laid the button out, so the wide header does not move.

`surfaces.browser.test.tsx`'s Tab walk reads only what is visible and would pass either
way, so the claim goes in beside it: at 400 wide the shortcuts control is not visible,
and at 1280 it is.

The header's other width-dependent parts are spans and work today; hold them in the same
test, so the next one gets a line rather than a picture somebody happens to read.

Done when the `?` is gone at 400 wide and still there at 1280, measured.
