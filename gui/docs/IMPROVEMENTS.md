# Improvements

## Block A — The client (payloads in, types out)

### §RG179 The was of a list field

`AmendPayload.was` is what each changed field held before, and this app declares it a
map of strings. The engine answers a list where the field is one: amending `--requires`
came back as *`amend` answered with an array of 0 where was.requires should have been a
string*, and the write read as unreadable although the file had already been written.
`--dep`, `--add-dep` and `--drop-dep` are the same shape and the same answer.

Measured while RG159 was building a fixture, which is the first time anything in this
app amended either field. Every case that reached `amend` until now changed the `why`,
which is a string, so the reader was right about the only field it had met.

**The `was` of a list field is a list.** The reader takes a value that is either — a
string or a list of them — and the type says so, since a caller drawing *what it was
before* has to handle both anyway. Nothing is flattened into a sentence on the way
through: joining a list here would be this app composing a field, and a screen that
wants one line can join what it draws.

**The contract is where this is held**, with a case that amends a dep and reads
`was.deps` back. RG4 exists for exactly this — a shape that moved, or was never right —
and the reason this one survived is that no case had ever sent the flag.

## Block B — Discovery (which checkouts on this machine are governed)

### §RG169 A depth the window can move

RG146 adds a root at `DEFAULT_DEPTH`, which is two, and the strip draws each root's
depth without a way to change it. Two levels reaches `D:\Git\<org>\<repo>` and stops
before a worktree family's folders one level further down —
`D:\Git\viglet\turing\2026.3` — so the first person to name `D:\Git` from the window had
to open the settings file anyway and write a 3.

**`addRoot` already says how.** Naming a folder that is already a root replaces its
depth in place and keeps its position, so a depth change is a save of the same list with
one number moved. `saveRoots` accepts it without widening, since the folder is one the
file holds.

**A stepper on the chip, bounded by `checkRoot`.** Down to 0, which is the folder
itself, and up to `DEPTH_CEILING`, and the two ends are disabled rather than refused
after a click. Each step saves and walks again, the way adding a root does, so the
effect of a level shows at once.

The depth is the one number in the settings a person picks by looking at what it finds,
and this is where they look.

### §RG180 Hearing the walk land

RG164 made `projects` answer the remembered record at once and run the walk behind it,
which is what a launch wants: eleven rows while the disk is still being read. What it
left is the other half — nothing says when that walk landed. A project cloned an hour
ago, or a folder deleted since, is on screen only after something else asks again, and
on the portfolio that is a reload.

RG164's design said so itself: *until RG144 gives main a way to say something changed,
the next call sees the fold*. RG144 shipped, and RG153 added a second topic to it, so
the way now exists.

**A topic for the catalogue, keyed on nothing.** `governed` is keyed on a root and
`session` on a session; what changed here is the one list this window holds, so the key
is the carrier's own and a screen subscribes to it once. The event carries no record:
the portfolio asks `projects` again, and the answer is then the folded one — the same
shape RG144 chose, where an event is a reason to read rather than a copy of what was
read.

**Published only where the fold changed something.** `reconcile` already answers
`changes`, so a walk that found exactly what the record held is a walk nobody needs to
hear about — and a window that redrew on every walk would redraw on a timer nobody set.

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

### §RG187 Bounding the gate runs a launch starts

RG166 gates a project when the carrier opens it, which is right for one project and is
the whole list at a cold start: the portfolio opens every project it found, and the
ledger is in memory, so on the first launch every one of them is stale and every one of
them is linted. Seventeen projects is seventeen of the most expensive read there is,
started within a second of each other, while `coldStart` is still asking each for its
counts and its next line.

**`coldStart`'s bound does not reach them.** Each project's own pool bounds what that
project runs at once, so nothing is overrun; what is unbounded is the number of projects
doing it, and that is the figure RG17 was built to bound for the reads a row is made of.

**The gate is not a read a row waits for**, which is why this is a cost and not a
defect: the column says `unknown` until a verdict lands, the rows fill from their own
reads, and a gate that finishes in a minute is a column that fills in a minute. What it
costs is the machine — seventeen engines each running a full parse of a governed tree.

**A limiter over the gate runs is the shape.** `createLimiter` bounds work across
projects and `coldStart` uses one; the gate wants its own, narrower, so a launch spends
one engine on verdicts and the rest on what the reader is looking at.

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

### §RG170 Readiness off the listing

RG148 draws each row's readiness from `deps`, one read per listed line, because `list`
prints the lines and not their readiness. A held engine answers each in milliseconds and
the carrier's pool bounds them, so a backlog of forty lines is cheap. One of eight
hundred is eight hundred reads to draw a screen, and the cache holds two hundred
answers.

The same gap removed a filter the design asked for. "Startable only" narrows by
readiness, and block D says readiness is never derived here. Every narrowing on that
screen is also an argument `list` takes, and `list` takes none for this. So the filter
is not offered, rather than being computed in React.

**The fix is roadkeep's, and the dep says so.** When `list --json` carries each line's
readiness beside its status, the row reads it off the listing and the `deps` reads go.
When `list` takes a `--startable`, the filter is one more chip handed to
`filterAsInput`. Neither is this app's to build: a resolver written into the client is
the one that disagrees with the engine without anyone noticing.

Until then the per-line reads stay. They are correct, just slow on a long list, and a
project that large can narrow by block first.

### §RG171 A design named by its heading

RG149's improvements tab lists the open lines that carry a design, each as its symptom
and its `§` pointer. The design asked for the sections themselves, and a section's
heading is the name its author gave the design, which neither the symptom nor the
pointer is. A reader looking for a design by what it is called has to know its id first.

The heading is one `section show` away, now that RG149 added the verb, but `list` does
not carry it. So drawing one per row is a read per designed line, which is the same cost
RG170 files against readiness.

**Asked when the tab opens, bounded by the carrier's pool.** Each designed row asks
`section show <ref>` with `--role improvements` and draws the title when it lands. Until
then it shows the pointer, as it does today, so the tab is never blank while it reads.
The body is not asked for, since a design is read in its task and not here, and a tab
that held every body would be the whole file this app exists not to reproduce.

If RG170's listing grows the heading as well as the readiness, this becomes a field read
off the list, and the per-row reads go with it.

### §RG173 An id that opens its own line

RG150's task screen draws each dep as a pill with the engine's word beside it, the
chains as routes, and the ids a ship frees as a count. None of them is a way to the line
it names. A reader following a blocker goes back to the project, finds the row and opens
it, which is what RG25 laid the graph out to spare them.

**An id the brief calls a task here is a link to its own route.** `taskPath(root, id)`
is the whole of it, and the answer on the far side is another brief. A shipped dep still
briefs, so it opens as the ledger's entry and not as a dead end. What the brief says
about each dep decides what is linked, and nothing is recognised by its shape, since an
id's shape is the project's.

**An edge whose standing is `never` stays text.** A dep in another repository, or on
work roadkeep has not published, has no route in this window, and a link that opened a
refusal would draw it as a line that is merely missing. The same holds for a route's
last hop when the chain ends outside.

### §RG174 A line's own finish line

A brief sends two lists of criteria: `done_when` for the line's block and
`done_when_own` for the line itself, each with its elided count, and `done_when_folded`
names which of the own leads came from another line. The reader declares the first pair
only, so RG150's task screen draws the block's finish line and none of the line's own.

The own leads are the ones that bind hardest. They are what `ship --checked` names, and
a lead nobody names at the ship reads in the ledger as unchecked. A person opening the
line is the one who has to verify them, and the screen they open shows none.

**Read the three keys, and draw them as their own group above the block's.** The engine
keeps them apart (a caller merging the two would assert the block's finish line about
this line), so the screen does too. A folded lead names the line it came from beside it.
The elided count is said as the non-goals' is, and an engine that sends no own list
reads as empty.

## Block E — The write path (the app composes an argv; the command writes)

### §RG181 A keep with a bound

RG165's keep drops a batch when the project's governed files move, which is the rule
that matters: a door offered against a state that has gone must not run. It has no rule
for a project nobody is writing to. Every answer carrying doors — a refusal, a gate
finding, an `explain` — adds a batch, and where the files sit still nothing takes any
away. A window left open on a failing gate holds one batch per read for as long as it
runs.

Each batch is small and this is memory rather than a wrong answer, which is why it is a
line and not a defect in the one above.

**The last batch per root is the one a screen can still reach.** A window draws the
doors of the answer it is showing, and an answer two reads ago is one no page has a
button for — so keeping the most recent batch per root, and dropping the batch it
replaces, bounds the table at one per open project without taking away anything a reader
could still press.

**The alternative is a count, and it is worse.** A cap of twenty batches is a number
nobody can derive and a rule that drops the batch a slow reader is about to use; the
per-root rule answers the same question with a fact about the screen rather than a guess
about the pace.

### §RG182 The duplicate read, beside the symptom

The read before an `add` is `delivered <block> --near "<the sentence about to be
filed>"`: it ranks that block's nearest deliveries against the proposal, which is the
duplicate question asked before an id is spent. The window's form asks it of nobody. A
person filing from the terminal is told to run it; a person filing from the window is
not told anything, and the id is spent either way.

**It belongs beside the symptom, not behind a button.** The symptom is the field a
duplicate collides with, so the read is the one the symptom itself triggers — asked when
the draft settles, like `budget` already is, and drawn as the five lines it ranked.
Nothing is refused by it and nothing could be: `delivered` publishes no score because no
threshold separates a true duplicate from a stranger, so the answer is a list to read
and the judgement stays with the person reading it.

**Each line it ranks opens.** A duplicate is only recognised by reading the other line,
so the ranked ids are routes to the task surface, and an open one and a delivered one
are marked differently — `--open` ranks both corpora and says which is which.

**The count is the block's, so the call needs a block.** Until one is typed there is
nothing to rank against, and the panel says that rather than ranking the wrong block:
the form's first field is what makes the read possible.

### §RG185 Opening on the verdict already held

The gate surface runs `lint` as it opens, every time. `gate.ts` already answers whether
that is worth doing — `needsGate` compares the verdict on record against the stamp the
files have now — and nothing calls it. Opening one project's gate twice in a minute runs
the most expensive read there is twice, for an answer the ledger held, and the second
run is the one a person waits through.

**The verdict on record is what the screen opens with.** It is dated and it says whether
the files have moved since, so a fresh one is an answer and not a guess: draw it, say
when it was taken, and run only where `needsGate` says the stamp has moved — or where
somebody presses Run the gate, which is a person saying they want it run whatever the
ledger holds.

**Stale is the interesting state and it has a screen already.** The portfolio's column
says stale; this surface has the room to say what moved, since the carrier watches the
governed files for exactly this (RG144) and can tell an open window that the report it
is showing is about a state that has gone.

**Nothing here caches an answer.** The ledger holds the verdict and its date, never the
findings, so a screen opening on a fresh one shows the count and the date and offers the
run. A report held in memory and drawn later would be this app answering about files it
has not read.

## Block F — The agent surface (handing one task to Claude Code)

### §RG175 The line a session already has

A claim `brief --claim` makes names nobody: the marker moves and `held` stays empty,
which is what the live handover measured against a real fixture. So the task screen,
which offers Hand to Claude Code while readiness is ready and nobody holds the line,
offers it again for a line this window started a minute ago. Pressing it reaches the
engine's own second guard — *was claimed 0m ago … read it without the claim* — and that
refusal is drawn beside the button, so nothing is taken twice. What is wrong is the
offer and not the outcome.

**The window already knows.** `sessions` answers every session this process started, and
the task screen asks it to draw the way back to one. A line whose session is still
running is a line this window will not offer again: the button gives way to Open the
session, which is the control a reader wanted anyway.

**A session that ended holds nothing.** It left the marker where the agent put it and
the claim expires on its own, so the offer returns when the state does — read from the
record's outcome, never from a timer kept here. A line held by somebody else is the
other case and is unchanged: the holder is named, which is the block's own criterion.

### §RG178 A list that hears what it lists

The list of what this window started asks `sessions` once, when it opens. A session's
own screen hears its topic and follows it line by line; the list hears nothing, so one
that ends while the list stands still says running, and one started from another screen
is missing until somebody navigates away and back.

**Nothing here should poll.** The events already exist: every line and every ending is
published on the session topic, keyed on the session. What the list lacks is that it
does not know which keys to subscribe to until it has asked — and a session started
after it asked has a key it never heard of.

**So the topic needs a key that is every session.** `subscribe` takes one source of a
topic, and a list wants the lot: either the topic carries a key that means all of them,
or the sessions the record answered are each subscribed and a new one arrives some other
way. The first is one subscription and one shape; the second is a subscription per row
and still blind to a session that started elsewhere.

A row need not carry the stream to be right: what the list draws is the state, so an
ending is the event that matters and a line only says it is still going. The record
stays the read that opens the screen, and the topic is what keeps it true.

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

### §RG154 The first release, read by the check

RG50's check has been read against answers described by hand, and GitHub's own is the
part nobody has seen yet: the shape of `releases/latest` for this repository, a 404
while every release is a draft, and the page it names.

**The first published release is the test.** Push a `v` tag whose version matches the
manifest, publish the draft `ci.yml` leaves, then run the packaged app of the version
before it and choose Help, Check for updates: it has to name both versions and open that
page. Then the same from the new build, which has to say it is current.

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

### §RG184 The byte no gate looks for

Five NUL bytes sat inside a template literal in `packages/ui/src/useFiling.ts` — the
separators of a key built from a draft's fields — and every gate passed: `tsc -b`
compiled it, `oxlint` read it, `prettier --check` called it formatted, and the suite
went green. It was found by `file` calling the source `data` instead of JavaScript,
which is not a gate and nobody runs.

**What the byte does is worse than being invisible.** It was a separator that worked, so
nothing misbehaved; but the file cannot be grepped for the line it is in, an `Edit`
against that text does not match, and a diff shows the change as a rewrite of a line
that looks identical. A tool writing the file through a shell heredoc is how it arrived,
and that is a path this project uses often.

**The gate is the repository's own lint, over the files it owns.** No source file may
carry a control character other than tab, carriage return and newline — a single pass
over the tree, reported by path and byte offset, refusing rather than warning. It is
cheap because it reads bytes and parses nothing.

**Prose is bound by the same rule.** The governed files are prose a person reads, and an
invisible byte in one of them survives every roadkeep read too, since none of them is
looking for a character that is not there.

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

### §RG168 A reason in the window's language

An unreadable row draws `Unreadable.message`. Where the engine explained itself, that
message is the engine's own prose and is right to show untranslated. Where this app
composed it, it is English whatever the window speaks. Examples are resolution's "no
candidate answered `engines --json`", the opening's "`config` was refused", and
`openingUnreadable`'s ungoverned sentence. A Portuguese window then prints an English
sentence in the middle of a translated row. This is the defect RG123 fixed for the
settings toasts, found again on the portfolio.

**The same fix RG123 made: a code and its fields, and the sentence in the catalogue.**
`Unreadable` gains a `code` naming which of this app's sentences applies, with the
values it fills, beside the `message` kept for a log. The row looks the sentence up the
way `RESET_TEXT` is looked up, as `UNREADABLE_TEXT[code]` through `say`. `said`, the
engine's stderr, stays as the engine wrote it.

**The pseudo-locale run should find it.** RG51's run draws the window with no project on
it, so no row reason has ever been on the screen it reads. Drawing one unresolved
project there turns this defect into a red run the day it is written.

### §RG172 A narrowed listing in the window's language

RG148's backlog draws `refusedSummary` under the chips when a listing is narrower than
its file. The sentence is composed in core, in English, so a Portuguese window prints it
untranslated. RG168 files the same defect for a row's `Unreadable.message`, and this is
its twin on the project surface.

**The update dialog says the same kind of thing** (RG156). A failed check shows
`reason`: the network's own words where the network spoke, which is right to quote, and
this app's English where it did not — *GitHub answered 403*, *not JSON*, *the answer had
no tag_name*, *is not a version this can compare*.

**And five helpers in core compose sentences no screen draws yet**: `saidOfUnderway`,
`whyNotStartable`, `wordsAgainstLimit`, `whereFiled` through `Whereabouts.sentence`, and
`saidOfHandover`. RG150's task screen needed three of them and said each again in
catalogue keys, so a helper and a key now say one thing twice and can drift.

**RG168's fix, applied at each: a code and its fills, and the sentence in the
catalogue.** `refusedSummary` becomes a reader answering which case applies and the
numbers it fills, and the screen looks the sentence up through `say`. A helper a screen
already replaced with keys is deleted with its tests, since keeping it keeps the English
copy.

**The pseudo-locale run should see a narrowed listing**, which RG176 is about: no row
reason and no narrowed list has ever been on the screen that run reads.

### §RG176 Every surface under the pseudo-locale

RG51's run opens the window with no project on it, opens the shortcuts sheet and the
palette, and reads every leaf of the document and every name a screen reader would say.
Three surfaces have arrived since and none of them is in it: a project's backlog, a
line, and the session a line was handed to — about a hundred keys between them. A string
typed into any of those three passes the one run written to catch it, and the guard's
own claim, that nothing on the screen was typed into a component, is now about one
screen out of four.

**Draw every surface at its own route, in the same pseudo-locale window.** The harness
already takes a route and those screens' own tests already stub a bridge that opens a
project and answers a brief; what this needs is that bridge beside this run and one
render per surface, each asked the same two questions — nothing bare in the text,
nothing bare in the names.

**One render per surface, not per state.** A state a person cannot reach without a
refusal is one this run would have to arrange, and chasing them would be a second suite
of the screens' own tests. What it holds is that every surface a reader can route to has
been read once, which is the claim RG51 makes and the one that quietly stopped being
true.

### §RG177 A time in the window's language

The session's file stamps are the first times this app draws. Each crosses as ISO-8601,
which is right — a fact and not a rendering — and the screen writes it with
`toLocaleString` and no locale, so what a reader gets is the desktop's. RG86 made the
window's language a person's choice, and a window set to one language on a machine set
to another writes its sentences in the first and its times in the second.

**The tag is already resolved**, at launch, by the side that can ask the desktop, and it
reaches the renderer as `LaunchSettings.locale`. So one place takes a stamp and the
locale in force and answers the string, and every screen that ever draws a time uses
that. A stamp this app cannot read is drawn as it arrived, since a blank where a time
should be is worse than an unfamiliar one.

***No dates, estimates, velocity or burndown* bounds this and does not forbid it.** What
that refuses is a schedule this app would have to invent: a date roadkeep does not
store, a rate, a line drawn through time. A file's last change is the filesystem's own
answer about a file the project governs, read and never computed.

The pseudo-locale run cannot see this: a time is not a catalogue value, so nothing wraps
it and nothing reports it bare. One test that draws a stamp under a locale and reads the
string back is what would.

### §RG183 The key nobody says

RG125 compares the two locales and reports a key one declares and the other misses.
Nothing compares either of them against the screens. A key declared in both and said by
neither passes every gate: the pseudo-locale run walks the catalogue and asserts each
key answers, which a dead key does, and the duplicate check reads the bundles alone.

That is how `filing.id` and `filing.section` sat in both locales through a whole task
with no screen saying them — the form was built without the id the engine names, and the
catalogue already had the sentence for it. The cost is not the dead string: it is that
the catalogue stops being the list of what the app says, so reading it tells you about
screens that do not exist.

**The read is the sources, and it is the same one the duplicate check already does.**
Every key reaches a screen as a literal in `say('<key>')` or as a `Translate` call with
the key spelled out, so a scan of `packages/ui/src` for that shape is the used set, and
the catalogue less that set is the dead one. A key composed at runtime would be
invisible to it — none is today, and a guard that refuses one is a guard that keeps it
that way.

**It belongs with the locale comparison, failing the same run.** A second command is a
second thing to remember; the existing wording test already owns the question of what
the catalogue holds.

### §RG186 The copy nobody exported

RG62's gate reads a file for the names it exports: the pattern is anchored on `export`
before `const`, `function`, `class` or `type`, plus what an `export { … }` list carries.
A screen declaring `function Label()` for its own use and never exporting it is a copy
the gate cannot see — the ordinary shape of the mistake here, a component private to one
surface having no reason to be exported.

It was found by moving one: a caption used by two screens became an exported helper, and
the gate reported it the moment it crossed that line. It had been sitting unexported in
a screen for weeks, with the same name the design system publishes, and every run
passed.

**Unexported is where the drift is worse, not better.** A copy nobody exports is one
nobody can be pointed at from elsewhere, so it diverges quietly: the design system's
`Label` is a real `<label>` and the local one was a caption span, two different things
sharing a name in one repository. A reader moving between the two screens has to know
which is which.

**The fix is the pattern, not a second tool.** Without the `export` requirement it
reports every declaration whose name the package publishes, and the escape hatch it
already has — `viglet-ds-allow-duplicate <Name> -- <reason>` — is what a deliberate
collision uses. The correction belongs in the package, every consumer having the same
hole; here it is a line saying so and the run that proves it.
