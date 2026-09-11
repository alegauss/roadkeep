# Improvements

## Block A — The client (payloads in, types out)

### §RG158 Two assertions that stopped asserting

Two live assertions pass without checking what they name, both loosened by RG141.

- **The contract's "which tier answered"** case reads a fixture that has lines ready, and after `tier` became nullable its assertion accepts a pick that arrives with no tier — the one regression it exists to catch.
- **"Combines two arguments into one read"** narrows to a found block and the `💭` marker, and that pair currently selects nothing, so `every` over an empty list passes.

**The fix.** The contract asserts a non-empty tier wherever a line was picked. The
combined filter chooses a marker actually present in the chosen block and asserts there
are lines before asserting each one matches.

Found by the adversarial review; the first confirmed by both skeptics, the second split.

### §RG159 A lacking line, actually read

The contract case for a brief with nothing to hand over asserts
`Array.isArray(brief.lacking)` on a fixture with no open line at all. `lacking` defaults
to `[]` when absent, so the assertion cannot fail, and that fixture never produces an
entry — the reader of `LackingLine` has never met one.

**The fix.** A fixture whose only open line requires something the caller lacks (`add
--requires macos-machine`, or `amend --requires`), so `brief` with no id answers empty
*with* `lacking`. The case asserts the entry names that line and what it misses.

Found by the adversarial review of RG142; the skeptics split.

### §RG160 The wiring the test rebuilt

RG137's live test builds its own `openProject` call around a broken engine and wires
`unheld: () => unheldAmong(made, root)` by hand. The one line that matters in production
— `openHere`'s own `unheld` option — is never run by any test, though the test's comment
says the reason is held end to end.

**The fix.** Give `openHere` a seam for the transport it builds per candidate,
defaulting to today's `createMcpTransport` with the process fallback, so a test can hand
it a surface whose engine cannot hold a session while resolution still works — and
assert `opened.project.unheld()` through `openHere` itself. The default path stays byte
for byte the same.

Found by the adversarial review of RG137; the skeptics split.

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

**The engine column is this line's too** (RG15 was retired into it). The version, the
home and the verdict already ride on every row, off the `engines` read resolution made,
so the column draws them beside the counts — a split row as information, never as an
error.

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
id the same `budget` read says `add` would write next. Beside the symptom, the non-goals
`boundsFrom` reads, each lead with the reason RG77 carries, since that list decides
whether the line may be filed.

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

### §RG154 The first release, read by the check

RG50's check has been read against answers described by hand, and GitHub's own is the
part nobody has seen yet: the shape of `releases/latest` for this repository, a 404
while every release is a draft, and the page it names.

**The first published release is the test.** Push a `v` tag whose version matches the
manifest, publish the draft `ci.yml` leaves, then run the packaged app of the version
before it and choose Help, Check for updates: it has to name both versions and open that
page. Then the same from the new build, which has to say it is current.

### §RG155 A path, not a prefix

`isReleasePage` (packages/shell/src/updates.ts) trusts any URL that starts with
`https://github.com/alegauss/roadkeep-gui/releases/`. A string prefix is not a path:
`…/releases/../../other/repo` passes it, and the browser `openExternal` hands it to
normalises the dot segments into another repository's page. The URL comes off a network
answer, so it is somebody else's word.

**The fix.** Parse it with `URL`: `https:` only, host `github.com`, no credentials, and
the normalised `pathname` starting with `/alegauss/roadkeep-gui/releases/`. Tests hold a
dot-segment URL, an encoded one and a lookalike host to `false`.

Found by the adversarial review of RG50, confirmed by both skeptics.

### §RG156 Sentences the update check gets wrong

The adversarial review of RG50 confirmed three places where the check says something
untrue.

- **A build ahead of every release** reads `current` and the dialog says it is "the newest published", dropping the version it found. Between tagging and publishing, every build of the new version is in that state.
- **An offline check** says only `fetch failed`: undici keeps the real cause (`ENOTFOUND`, a refused connection) on `error.cause`, and the test used an error shape fetch never throws.
- **A failure while the body is read** — a timeout, a dropped connection — is reported as "not JSON".

**The fix.** An `ahead` verdict with a sentence naming both versions (a new catalogue
key in both locales); the reason reads `error.cause`; only a `SyntaxError` is "not
JSON". The bound test proves the timeout aborts, and the fakes use the error shapes
fetch really throws.

### §RG157 Running the refusal it claims

`release.test.ts` holds the tag-against-manifest check in `ci.yml` by finding its text:
the step's name, `GITHUB_REF_NAME#v` and `require('./package.json').version`. A step
that kept those strings and inverted its condition, or lost its `exit 1`, would pass.
The refusal itself is never run.

**The fix.** Extract the step's `run` script from the workflow and execute it with bash
in a temporary directory holding a `package.json`: a matching `GITHUB_REF_NAME` exits 0,
a mismatching one exits non-zero and names both versions. Fast and self-cleaning, so it
stays in `npm test`.

Found by the adversarial review of RG50, confirmed by both skeptics.

### §RG161 What the signing procedure gets wrong

The adversarial review found `docs/SIGNING.md` would fail the person following it on two
routes.

- **Certum:** the snippet puts `certificateSubjectName` in `electron-builder.yml`. Committed, it makes the Windows package job look for a certificate the runner does not have, and the release draft never happens. It belongs on the local command line, not in the file.
- **SignPath:** signing the NSIS installer leaves the app executable inside it unsigned, yet step 5 stamps the build signed. The app has to be signed before the installer is built from the prepackaged directory, then the installer signed.
- SignPath's prerequisites also omit the code-signing-policy page and MFA its terms require.

And three sentences beside it are false: `electron-builder.yml`'s comment on what the
builder logs and which `rcedit` it uses, the RG49 ledger entry naming two routes where
the doc lists three, and RG49's open criterion, which no recommended route can meet
because each signs under a name other than the manifest's.

### §RG162 Cutting v0.1.0

The maintainer decided to cut v0.1.0, and two things stand in the way. `package.json`
declares MIT and ships no `LICENSE` file, so GitHub detects no licence — and SignPath's
open-source route (RG161, RG49) requires a recognised one. And every build says `0.0.0`,
the version the stamp reads from the manifest, while `ci.yml` refuses a tag that names
another.

**The steps, in order.** Add `LICENSE` with the MIT text and the manifest's author,
Alexandre Oliveira. Set `version` to `0.1.0` in the root `package.json` (and the
lockfile). Commit, push, then push the tag `v0.1.0`: the package job checks the tag
against the manifest, builds both installers, and the release job leaves a draft. A
person reads the draft and publishes it.

That publish is what RG154 needs to read the update check against a real release, and
what SignPath's "already released" condition asks for.

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
