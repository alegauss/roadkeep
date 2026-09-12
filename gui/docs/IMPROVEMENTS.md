# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

### §RG147 Lines in the palette

The header's palette trigger reads "Find a line in every backlog" in `Main.dc.html`, and
the palette the shell mounts lists `AREAS`, which is surfaces. RG20 shipped `search`
over every open project, and nothing puts a line into the list a person types at.

**The package's palette, fed a second group.** `BentoCommandPalette` takes items; the
lines `search` answers go in beside the surfaces as their own group, ranked as `search`
ranked them, each showing id, marker and symptom. Choosing one opens the task detail.
Nothing is matched in the renderer: a query is `search`'s, and a line the verb did not
return is not offered, which is block C's first criterion applied to a list.

**Only projects already read are searched.** A project still pending is named at the
foot of the results as not yet searched, never silently absent, which is what
`coversEverything` answers.

**It cannot yet, which is the finding for the package.** `BentoCommandPalette` takes
only nav items and filters them with its own matching, so lines would be matched in the
renderer. The "a grouped palette" dep is that change in the design system: a second
group whose items the product supplies per query. Choosing a line waits on RG150's task
detail.

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
