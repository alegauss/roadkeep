# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

### §RG208 System notes hidden by choice, and counted where hidden

`actsIn` reads a line it has no use for as a `note` — `system` (init, thinking token
counts), `rate_limit_event`, an empty thinking turn, a `user` turn carrying no tool
result — and `Session.tsx` draws each as a row with its raw line. `acts.ts` says why
they are kept: returning nothing would make the act list quietly shorter than the stream
it was read from.

**A preference, not a filter somebody forgets.** `Settings.sessionNotes`: `shown` or
`hidden`, default `shown`, so an upgrade changes nothing on screen. `readSettings` reads
it with a `Lost` code of its own — an absent field takes the default, so no version bump
— and the settings screen writes it under a *Sessions* group.

**Hidden is never silent.** `actsIn` stays whole and the choice applies where the stream
is drawn. Consecutive notes fold into one quiet row — *3 system notes hidden* — whose
disclosure lists them with their raw lines, so the count on screen still accounts for
the stream and each note is one click away. The session record, the published lines and
*What moved* are untouched.

**Only `note`.** A failed tool, a result or anything the session said is never folded.

Done when a reader who chose hidden sees the acts plus one folded row per run of notes,
and the default still draws every note as today.

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
