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

### §RG237 A session takes the window's width

The shell's reading column is `max-w-5xl` on every page, and the session draws three
columns inside it, two of them 18rem. At 1280 wide that leaves the stream about 360
pixels, and the stream is where tool calls, their arguments and their output are read.

A session is a workspace, not a page read top to bottom, and the arrangement a reader
already knows for one is an editor's: a side bar on each edge at a fixed width, the
middle taking the rest. So the session takes the window's full width. From `xl` its
columns are what was handed over on the left, the stream in the middle and what moved on
the right. Between `lg` and `xl` the two side panels share one column on the left, since
three at 1024 would squeeze the stream back to where it was. Below `lg` nothing changes:
the stream first, as RG225 placed it.

The page does not set the width. `authoring.md` makes a variant of the column the
shell's to offer by name, never a class a page repeats, so the shell keeps a table of
the routes that take the full width, and the session's route is its one entry.

The side bars neither collapse nor remember a width, which the same contract names as
the console-era sidebar it refuses.

Held by a test on the class `main` carries per route, and by `npm run shots` on the
session at 1280 and 400.
