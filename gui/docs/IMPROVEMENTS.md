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

### §RG234 Transforms kept between runs

`npm test` prints its own measurement at the end of every run: `core` spends 17.99s
transforming modules, 78% of its tracked time, and `shell` 16.69s — both re-done from
scratch on the next run. A whole run measured between 18s and 37s here, so that is no
rounding error inside it.

Vitest names the flag itself: `fsModuleCache: true` persists transformed modules across
runs. RG64 split this suite precisely so `npm test` would stay what somebody runs
between edits, and this is the part of that cost nothing spends on a test.

**The question is not whether it is faster but whether it is still true.** A cache keyed
wrong answers with yesterday's module, and a suite green about code nobody changed is
worse than a slow one. So the work is three measurements and not one flag: a cold run, a
warm one, then an edit — change a source file, run again, and watch the assertion that
depended on it go red.

Where the cache lands is part of it. `.vitest/` is already ignored by git and by
Prettier and holds the browser screenshots and the failure reports; anywhere else is a
directory somebody has to add to both.

Only `core` and `shell` were measured, the two the banner named. The renderer transforms
`.tsx` through the React plugin and is the likelier winner of the three.

Done when a warm run is measurably cheaper than a cold one and an edited file still
fails the test that covers it.
