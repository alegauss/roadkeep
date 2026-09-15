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

### §RG236 The unpackaged window names its icon

RG138 put roadkeep's mark into the executable: `build/icon.png`, rendered from
`build/icon.svg`, reaches the .exe through `buildResources` and the resource edit. An
unpackaged window never sees either. `npm run dev` and `npm start` run `electron.exe`,
whose own resources are the atom, and `createWindow` names no icon, so the title bar and
the taskbar button wear Electron's mark on exactly the runs a developer looks at most.

The window names the PNG, and only unpackaged. The SVG is the source and not what the
window can take: Electron's native image reads PNG and ICO, never SVG, and the PNG is
the committed render of it, which is the file `npm run icon` exists to keep in step.
Packaged, the option is left out: `buildResources` is not copied into the app, so the
path would name a file that is not there, and the executable already carries the icon
Windows draws.

Where the path is decided is a function of the directory the compiled main process lives
in and whether the app is packaged, the shape `readStamp` and `agentOverride` already
have, so a test in `shell` asserts both halves without starting Electron: unpackaged, a
path that exists and is the 1024 PNG RG138 holds; packaged, nothing.

Checked by eye on `npm run dev`, where the taskbar button is the thing that was wrong.

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

### §RG235 A hero's actions meet at their tops

Each action on the task's hero is a column: the button, and under it the line that says
what happened when it was pressed. Copy the brief reserves that line's height with
`min-h-4`, so "copied" arriving does not move the button. Hand to Claude Code writes its
line with no floor, and an empty `output` in a flex column is zero high. The columns
differ by that line, and `HeroActions` centres them on the row's middle, so the shorter
column's button sits eight pixels lower than its neighbour.

The fix belongs to `HeroActions` and not to either page: the columns meet at their tops.
A button is the first thing in every column a hero carries and the notes under it are
what differ, so the top is the one edge two columns always share. Centring was right
while every hero held a lone button, which is what RG215 wrote it for.

A floor on every note was weighed instead: it aligns these two, and the next action
written without one misaligns again, a defect that exists only between two components.
The row's own rule holds wherever an action is added.

Held by a test that reads the class the row is drawn with, since jsdom measures nothing,
and by `npm run shots` on the task at 1280, where the two buttons are read against one
line.

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
