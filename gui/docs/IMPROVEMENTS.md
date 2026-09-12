# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

### §RG204 A picture from a repository this app does not own

An emoji is recognisable and it is not a logo. Where a project declares `project.logo`
the row should draw the file — and that file lives in an arbitrary repository on this
machine, which is what makes this its own line rather than a clause in the icon's.

**The renderer never gets a path.** A `file://` URL from the portfolio into an Electron
renderer widens what the window can read to whatever a path can reach, and the path was
written by a repository rather than by this app. The shell resolves it against the
project root, refuses anything that climbs out, reads the bytes, checks they are an
image it agreed to draw, and hands back a data URL over the transport that already
exists. The renderer receives a picture or it receives nothing.

**A size ceiling, enforced on the bytes and not on a declaration.** A logo here is a
list-row icon at thirty-two pixels; a repository pointing at a four-megabyte PNG should
get the emoji and a note on the row, not a portfolio that stalls on seventeen reads.

Every failure — missing file, wrong type, too large, outside the root — falls back to
`project.icon`, and that to `IconFolder`. The chain is why the emoji stays worth
declaring even where a logo exists, and it means a broken logo is a cosmetic outcome
rather than an empty cell.

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
