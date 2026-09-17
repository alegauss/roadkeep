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

### §RG264 A width no route can miss

RG237 gave the session the window's width, because its three regions inside a 64rem
column left the stream about 360 pixels. RG263 added a second route to the same screen
and the table did not follow, so a session handed a gate finding is drawn in the reading
column — the exact defect RG237 named, back on a route nobody listed.

`FULL_WIDTH` names routes one at a time, which is why. That is the right shape for a
table about layout and the wrong one to leave unguarded: a third session route would be
narrow the same way and nothing would fail. So the guard is the point. Every route the
`Session` element answers takes the full width, checked against the router's own table
rather than a second list beside it — `SURFACES` already pairs each path with its
element, so a route added without a width is a red run instead of a narrow screen.

The table stays a list and does not become a rule about path shapes. A route is
full-width because of what it draws, not because its pattern contains a word: matching
on `session` would make the width depend on a spelling, and a screen renamed would
silently change column.

Nothing else moves. `reading` is still every other page at 64rem, and the session's own
grid — two side bars from `xl`, beside the stream below it — is what RG237 settled and
this does not reopen.
