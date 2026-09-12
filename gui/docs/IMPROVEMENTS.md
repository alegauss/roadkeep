# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

### §RG206 The stream follows its end until the reader scrolls away

`Sessao.dc.html` draws the stream as a region with a height of its own — `flex:1;
overflow:hidden` under a `main` bound to the viewport. `Session.tsx` renders it as a
list the page grows around, so a new act lands below the fold and nothing brings it into
view.

**The stream becomes its own scroll region.** Under the hero the three-column grid is
bound to the viewport's height, the stream panel scrolls inside it, and the side columns
stay put. Below `lg` the columns stack and following scrolls the window instead.

**Following is the reader's state, not a preference.** It starts on, and each new act
scrolls the region to its end, instantly: smooth scrolling under several lines a second
never arrives. Scrolling away turns it off and shows *Jump to latest* at the region's
foot, with the count of acts since. Taking it, or scrolling back to the end, turns it
on. An ended session stops following.

jsdom has no layout and no `scrollIntoView`, so the rule — at the end within a few
pixels, acts since leaving — is a pure function tests call with numbers, and the DOM
half is thin.

Done when a running session keeps its newest act in view and a reader scrolled up is
never pulled down.

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

### §RG207 One settings screen, and one way to write a preference

Two preferences are written today, each by a control in the header and a bridge method
named for it: `saveTheme` and `saveLocale`. `RendererBridge` stops there on purpose — *a
third would be the moment to ask again* — and a session preference is that third.

**The screen.** A `/settings` route in `AREAS`, so the rail and the palette reach it: a
`BentoHero`, then one `BentoFormSection` per group — *Appearance* (ground, language)
first. A control is written as it changes, as the header's already are, so there is no
save bar to morph. The header keeps its ground control, which the shell contract puts
there.

**The write.** Not `Partial<Settings>`, which hands the renderer the roots and the
ignore list. `savePreference(key, value)` over a table in `core` naming each writable
key with the validator `readSettings` applies, as `isTheme` is shared today — so the
main process refuses a key outside it, and a new preference is one row, one reader field
and one catalogue entry. `saveTheme` and `saveLocale` become its first two rows.

**A refused or failed write keeps the old value** and says so through
`settings.unsaved`.

Done when the ground and the language are chosen from the screen and written through the
table, and a key outside it is refused.

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
