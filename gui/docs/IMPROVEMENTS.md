# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

### §RG146 The third write, named

The portfolio's hero carries Add a root and Rescan roots, and the rail ends in Settings.
`core/src/roots.ts` has `addRoot`, `removeRoot` and `checkRoot`; the bridge reads the
roots through `settings()` and writes only the theme and the language. Block B's first
criterion is that the list is the person's statement, and today the only way to make it
is to edit a file by hand.

**The third write is the moment `bridge.ts` said to ask again.** `saveTheme` and
`saveLocale` each name one field, and the note on the second says a third reopens the
question of a patch. The answer here is still a method that names what it writes:
`saveRoots` takes the roots, the skip list and the width together, because those three
are one statement about where to look and a patch would hand the renderer the language
too.

**The folder is chosen by the shell.** A native dialog opened from main answers a path;
the renderer never types one, and a web service answers the same call with a text box.

Rescan reruns the scan over the roots already named, nothing wider, and a root that no
longer exists is kept and marked by `withPresence` rather than dropped. The settings
file already exists, so nothing here is a store of this app's own.

## Block C — The portfolio (many backlogs in one view)

### §RG145 The portfolio at the root route

`Main.dc.html` is the screen, and `/` is where it goes: the scaffold `App` naming three
packages is retired by this line, and `AREAS` gains its first entry, Portfolio, the day
the route answers it.

**The hero** says how many projects and how many are read, still reading or unreadable,
from `tally`. **The list** is rows and not tiles, per §RG63, in a `BentoPanel`: project
and path, the backlog counts and markers from `stats`, the next ready line as `pick`
printed it, and the gate as the ledger holds it with its age. A row still answering is
drawn pending and never as zero, which is block C's second criterion, and `coldStart`'s
progress fills rows as they land. An unreadable row spans the counts and says what was
tried, from the `Opening` that refused.

**The engine column is RG15's.** The row draws its first four columns; the version, the
home and the verdict arrive with the read that line files, and the header chip drawn
dashed stays dashed until then.

The filter chips — gate drifted, engine disagrees, unreadable — narrow what is already
loaded and count only what a verb printed. Clicking a row opens the project surface once
it exists; until then it opens nothing rather than a dead link.

`artboards.test.tsx` holds chrome only. This screen's test drives the harness with a
stub bridge answering three rows in three states.

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

If the palette cannot take a second group without being re-declared, that is a finding
for the package, not a component to write here.

## Block D — The project surface (one backlog, read)

### §RG28 The order a pause has no way to state

The store itself landed: `--stale` names the deferred role without a `--role`, the
pauses come back with their marker and the sentence the store spells, and an id now
answers open, shipped, paused or nowhere. What that half is and why it reads the
sentence whole is recorded in `packages/core/src/pauses.ts`.

What is left is the order. `--stale` computes it — how long each pause has stood, in
commits over the governed files, oldest first, with the reason beside it — and prints it
for a terminal, on stderr and never in the listing. A `--json` caller gets the store in
file order and nothing else, so this app has no age to draw and does not pretend to one.

There are two ways to reach it and only one is allowed. Reading `set aside 3 commit(s)
ago:` back out of English is the prose-scraping this client refuses on every other verb,
and a second implementation of a sentence roadkeep is free to reword. The other is for
roadkeep to put `since` and the reason in the payload as it already holds them in
`Standing` — filed as this line's dep, which nothing shipped here satisfies.

The order is not a verdict, and drawing it must not make it one. How long a pause may
stand is a judgement about work — the same one `[claims] held` refuses to make — so the
oldest is first and what that means is the reader's.

### §RG77 The reason a non-goal keeps to itself

`non-goal list --json` answers with the leads, the file, what was elided and which
designs quote each. It does not answer with the reasons, and neither does `brief`, which
prints the same leads. A criterion arrives with its `why`; a non-goal does not.

The reason is the half that decides anything. `No store of its own` is a phrase whose
argument the file spells out in a sentence, and that sentence is what a person about to
file a proposal needs. RG26 shipped the list with `answeredBy` and no `why`, faithful to
the payload rather than half-written.

There are two ways to get it and only one is allowed here. Reading `docs/ROADMAP.md` and
lifting the bullet is what `No Markdown parsed in this app` refuses, and it is the
second implementation of a grammar this app exists not to hold. The other is for
roadkeep to publish the field, the way `criterion list` already does — a key on the
payload, filed upstream in `d:/Git/alegauss/roadkeep`.

So this line waits on that, and its dep says so: nothing shipped here can ever satisfy
it, and `pick` will not offer it. What lands when the field arrives is small — the key
on `NonGoalsPayload`, the `why` on `NonGoal`, and the tests that assert a reason that is
absent today. The line exists so the gap is a filed state rather than a shape somebody
later reads as an oversight.

On ship: `--recorded-in packages/core/src/binding.ts`.

### §RG148 One backlog, as rows

`Projeto.dc.html` draws one backlog, reached from its portfolio row. `backlogFrom`,
`filterChoices` and the readiness `deps` and `pick` answer shipped under RG21, RG22 and
RG25, and no route reads them.

**The hero** names the project, its path and the counts `stats` printed, with the gate's
state and age beside Run the gate and File a line. Those two buttons belong to the lines
that build what they open, and until then they are absent rather than disabled.

**The block chips** show each block's title and open count, a finished one muted and
still selectable. The titles are `block list`'s, which `VERBS` does not carry yet;
adding that read is part of this line. **The filters** are `filterChoices` — marker, the
requirements the project declares, startable only — and every narrowing goes to the verb
as `filterAsInput`, so the list is what `list` returned for it and never a filter in
React.

**A row** is marker and id, then the symptom and the why at full length, since a symptom
is the field a reader scans and §RG63 chose rows to keep it whole. Below them the block,
each dep as its state, and whether a design is written. On the right, readiness in the
engine's words and, for RG74's case, "marked, unheld" with the sentence that says why.
Open leads to the task.

The route carries the root, so the rail's Backlog entry is offered only while a project
is open. The role tabs are drawn; only Roadmap is this line's.

### §RG149 The four other files, as tabs

The project surface draws five role tabs and the roadmap is the one behind them. The
other four already have readers: `ledgerFrom` and `reversedFrom` for the changelog and
decisions under RG27, `storeFrom` and `whereaboutsOf` for the deferred store under RG28,
and the design sections for improvements.

**Each tab is the same row, read from its own file.** A changelog entry is the shipped
line and what it delivered, grouped by block; a decision is its heading and body, with
what revised or superseded it; a deferred line keeps its id, deps and the reason it was
set aside, with Resume as the door once the write path exists. Improvements lists the
sections of open lines, each linking to its task, since a section is read in the task
and not here.

**The prose is the file's.** A decision body is drawn in the text face with its wrapping
kept, which is block H's criterion and the non-goal about Markdown both, and the same
component the task detail uses for a design section.

The deferred tab orders by file until RG28's payload says how long each pause stood; it
does not invent an order.

### §RG150 The task, as brief joins it

`Tarefa.dc.html` is one `brief`: block D's first criterion is that the screen is one
read and not six, and `detailFrom` already joins it — the line, the resolved deps, the
design whole, what a ship unblocks and the lists that bind it.

**The hero** is the id, marker and block over the symptom, with Copy the brief and Hand
to Claude Code. The second belongs to the session line and is absent until it lands.

**The left panel is the design as the file stores it**: title, the anchor and where it
lives from `whereDesignLives`, the words against the limit from `wordsAgainstLimit`, and
the body in the text face with the file's wrapping kept and `**` and `[[RG88]]` literal.
That is block H's criterion about the face, drawn; no Markdown is parsed. A line with no
section says so with the absence `designOf` returns.

**The right column** is three cards. Readiness in the engine's words, with the chain
`graphOfBrief` routes and how many open lines a ship unblocks. Underway, which is
`underway`: whether the marker and the claim registry agree, naming the holder if one
does. What binds the line: the block's criteria and the non-goals, the ones this line
quotes first.

A paused line opens here too, with the typed fields RG80 made its refusal carry.

## Block E — The write path (the app composes an argv; the command writes)

### §RG151 Filing a line from the window

`Escrita.dc.html` is filing a line, opened by File a line on the project surface. Every
piece shipped in block E: `composeWrite`, `countersOf` over `budget`, `readRefusal` and
the doors `offerable` keeps.

**The form** is block, marker and deps, then symptom, why and the design body, each with
a counter against what `budget` says this line leaves — which moves as deps are added,
so the counter asks again rather than holding a number. Over the limit the box turns and
says by how much; the aim is drawn as a tick, not a limit. The `BentoFormHero` names the
id the same `budget` read says `add` would write next.

**The right column is the command before it runs.** The argv `composeWrite` built,
copyable, with the prose elided in the middle so it stays readable; the full argv is
what Copy takes. Beneath it, what a refusal offers: its code on the field it names,
never a toast, then each door `explain` gave. A complete door runs as one action; an
incomplete one shows what it needs and waits for the words, and a door that writes a
governed file says so.

The body goes in the same call as the line, as RG32 made possible, so nothing filed here
points at a missing section. Save runs `applyWrite` and reopens the task it wrote.

### §RG152 The gate as a surface

Run the gate is drawn on the project surface, and block E's third criterion is that the
gate is a surface and not a report. RG33 shipped `actionableFrom` and `offerOf`; no
artboard draws the findings, so this line reuses the right column of `Escrita.dc.html`
rather than inventing a second shape.

**A finding is a row**: its code, the file and line it names, and the sentence lint
wrote. Under it, the doors, drawn exactly as the write path draws a refusal's — complete
ones run, incomplete ones ask for the words, each shows its argv first. After any door
runs, the gate runs again and the row goes when the finding does.

**The result is recorded where the portfolio reads it.** The pass or the count goes into
the gate ledger with its time, so the row's gate column and this screen never disagree
about when it last ran.

`repair` spending a whole report is one action here only if it is one command there;
this app does not batch doors the engine offered one by one.

## Block F — The agent surface (handing one task to Claude Code)

### §RG153 The session beside its task

`Sessao.dc.html` is block F on a screen. Hand to Claude Code on the task detail takes
the line with `brief --claim` and starts the session from that payload through
`promptFor`, which RG38 and RG41 shipped; if `claimingBrief` finds a live claim, the
holder is named and nothing is offered, which is block F's third criterion.

**The hero** is the task, whose claim it is and since when, read from the registry, with
Open the task and Stop the session.

**Three columns.** What was handed over: the design, the deps, the criteria and the
non-goals `handoverOf` counts, and the command that started it. The stream, as `actsOf`
reads it: prose, then each tool on what it touched, roadkeep calls marked, and an act
that touched a governed file edged in the accent; every raw line stays reachable. What
moved: `landingBetween` before and after, the five governed files `watchedFiles` names
with when each last changed, and claims held elsewhere.

The stream and the file changes arrive over RG144's subscription; nothing polls.
Stopping kills the process and leaves the claim to the registry's own expiry rather than
releasing a line the session may have moved. The rail's Sessions entry lists the ones
running.

## Block G — The shell (an executable now, a service later)

### §RG49 The signature, and what it needs that code cannot supply

Signing is not work that can be finished by writing anything: it needs a certificate
somebody bought, held somewhere a build can reach. So the line states the requirement
and is set aside for a caller that says it has one, rather than coming back as the next
ready task forever. What can be built without it is the pipeline that would use it, and
the about surface saying plainly that this build is unsigned — which is the honest half
and is worth having on its own.

### §RG50 Updating, and what has to exist first

An update check reads a release that exists on the internet, so this line needs a
published artifact and not merely code. What it must do is state which version it is on
and which it found, and never install anything without being asked — an app that
replaces itself while somebody is reading a backlog is one that loses their place. What
it must not do is phone anywhere on launch by default: this app reads a person's
repositories, and a network call it did not need is one that has to be explained.

### §RG119 The build nobody has made

`electron-builder.yml` declares a `dmg` target with a category beside it, and that is
the whole of what this project knows about a macOS build. Nobody has run it. RG91
packaged Windows and Linux in CI and left this out deliberately: a runner is a poor
place to find out what a platform needs, because every answer arrives as a red job with
a log and no way to try the next thing without another push.

Three things are likely to want settling, and none of them is knowable from here. An
unsigned `.app` is refused by Gatekeeper on the machine that downloads it, which is a
different problem from RG49's Windows one and is not solved by the same certificate.
`spawnElectron` strips `ELECTRON_RUN_AS_NODE` and resolves a binary by a path this
project has only ever resolved on two platforms. And the live suite starts the built app
with a remote debugging port, which on macOS is the same mechanism and a different
sandbox.

So this carries `macos-machine` rather than a CI job: whoever has one runs `npm run
package`, opens what comes out, and writes down what it took. Adding `macos-latest` to
the package matrix is the last step and not the first — it is how the answer is kept,
not how it is found.

### §RG128 The engine a session actually got

The launcher resolves an engine in four steps — `ROADKEEP_HOME`, a vendored
`.roadkeep/`, the sibling `../roadkeep`, then a clone under the user cache — and takes
the first that *answers a probe*. A checkout being written while the probe runs does not
answer, so resolution falls through. During RG120 three commands were served by `0.2.4`
out of `~/.cache/roadkeep-src` while the sibling stood at `0.2.450`; `ROADKEEP_HOME` did
not help, being a candidate the same probe drops.

**Decided, and the half left is upstream's.** Three levers, measured on 2026-09-10:

- **Vendoring is rejected here.** `.roadkeep/` outranks the sibling, and this project's live suite tests the roadkeep checkout under development on purpose (`live.ts`, RG84). A pin would change what that suite tests without anything saying so, and freeze the engine on the one machine where it moves daily.
- **The launcher is not this repository's to change.** It is identical to what `roadkeep install` writes today, so an edit here is overwritten by the next refresh. Making a *named* engine fatal rather than skippable is its behaviour, and the dep names it.
- **The cache is the hazard on this machine.** It still answers — `0.2.4`, from 2026-08-28 — and is the candidate a busy sibling falls to. Removing `~/.cache/roadkeep-src` turns a stale answer into a refusal naming the missing engine: louder, and never wrong. It is a directory outside this repository, so it is named here for whoever owns the machine rather than removed.

### §RG143 A transport the renderer holds

`RendererBridge` has four methods, and none of them reaches an engine. Every reader the
five artboards need shipped into `core`, and `openHere`, `scanRoots` and the held
transport are called by live tests alone: `main.ts` still says no process is spawned
there.

**Two methods, not one per screen.** `projects()` answers the catalogue `scanRoots`
builds from the person's roots, and `run(root, request)` hands an `EngineRequest` to the
transport `openHere` holds for that root. The renderer builds `core`'s client over a
transport whose `run` is that method, so opening, cold start and the cache run where the
screens are, and a web service implements the same two methods. A method per screen is a
second client the port would have to write again.

**Main refuses what it did not catalogue.** A root that is not in `projects()`, or an
argv whose verb is in neither `VERBS` nor `WRITES`, is refused before anything spawns.
The transport already spawns with shell false; this is the half that says which calls
exist at all.

The stamp and the candidates stay in `shell`, where the filesystem is. Whether the
renderer asks for them per open or main opens the project and the renderer only runs
through it is worth deciding here rather than assuming: the second keeps held engines
owned by the process that has to close them.

A test drives the window through the harness against a stub bridge, and the live suite
runs one read over IPC.

### §RG144 A subscription the port can serve

Every bridge method is `ipcRenderer.invoke`, a question with one answer. Three things
the artboards draw are not questions: a session's stream in `Sessao.dc.html`, a governed
file changing under it, and the cache a write elsewhere made stale. `startSession` has
`onEvent` and `onLine`, `createGovernedWatcher` fires on a disk change, and neither has
anywhere to send what it heard.

**One subscription, typed by topic.** `subscribe(topic, listener)` returns the function
that ends it, and the topics are a table in `core` beside `BRIDGE_CHANNELS`, so main and
the preload cannot drift on a name. Two topics to start: a session's lines, keyed by the
session it belongs to, and a root whose governed files changed. The second is also what
calls `invalidate` on the renderer's client, so a screen rereads after an agent or a
terminal writes, without polling.

**The port is why it is a subscription and not an IPC detail.** Over HTTP this is a
server sent stream, and a listener shape that only `ipcRenderer.on` could satisfy is the
coupling `bridge.ts` exists to refuse.

A subscription that outlives its screen is a leak a test can see: the harness unmounts a
screen and requires the preload to have removed its listener.

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
