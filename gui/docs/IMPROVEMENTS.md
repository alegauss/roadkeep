# Improvements

## Block A — The client (payloads in, types out)

### §RG1 One way in, and where the process rules live

Everything this app knows arrives out of a subprocess, so that one call's shape is what
the whole client rests on: a project root, an argv array, and back an exit code, stdout,
stderr and a duration.

Four properties are not preferences. **No shell** — spawn with `shell: false` and argv
as an array, because a shell is where quoting defects live and this app composes text a
person wrote. **The root is the working directory**, and `-C` is passed too, so an
answer is about the project on screen and never about the directory the app started in.
**Every call is cancellable and bounded**, a screen redrawing while reads are still in
flight. **The two streams stay apart**: `list` prints a marker-bearing line it could not
accept on stderr with the count, so a client merging them cannot tell an answer from a
warning about that answer.

What this is not is a function per verb. A verb is data — the argv it builds and the
shape it returns — so adding one is a table entry and never a new call path. That is the
MCP server's own argument about dispatching through one parser: two code paths that both
add a task is the drift being removed.

The transport is one interface with one method. Nothing above this layer knows a process
was involved, which is what the later service rests on and what a test has to hold
rather than a comment.

### §RG2 Whose roadkeep answered

`roadkeep` on PATH is the one thing `engines` exists to say a project may not be
running. A checkout may be governed by the plugin, a sibling checkout, a pip install or
a committed launcher, and those may sit at different versions and disagree.

So the engine is resolved per project, never per machine. `engines --json` is the first
call made against a candidate and its `invoke` key is the command line every later call
for that project is built from; `version`, `home`, `revision` and `verdict` are kept
beside it, because this block's criterion is that the copy which answered is on screen
and not merely that one was found.

Three states have to be told apart and none is a crash. A project whose engine is a
modified working tree gets an answer that is that tree's, which `lint` says out loud and
this app repeats rather than hides. A project whose copies disagree is drawn as
disagreeing, not as whichever answered first. A machine with no Python resolves nothing,
and that project is shown as unreadable with the reason — the alternative being an app
that quietly substitutes a build of its own for the one the project chose.

Nothing is bundled, which is a non-goal here and the same argument backwards: an engine
shipped inside this app would judge seventeen projects by a version none of them
declared, and the disagreement `engines` surfaces is what the screen would stop seeing.

### §RG3 Types that come off the tool, not off a guess

A payload is JSON with no published schema, produced by a build this app did not choose.
Read as `any` it becomes a runtime `undefined` on the day a key is renamed, on a user's
machine, in the one place nobody is watching.

So the boundary validates. Each read declares a shape and a parser that returns either
the typed value or a named failure, and nothing past the boundary sees an unvalidated
object. What a validator refuses is the payload and never the project: a shape this
build does not recognise is reported as *this app is behind the roadkeep answering
here*, naming the version `engines` gave, which a person can act on. A stack trace is
not.

The shapes are written by hand from the payloads, deliberately. There is no schema to
generate from, and inventing one would be a second declaration of roadkeep's format,
which the non-goals refuse. The safety comes from the other end: the contract test runs
the real command and asserts these shapes against what it prints, so a type that drifts
fails in this project's CI rather than in a window.

Optional is the default reading, not the exception. `standing`, `over`, `picked` and
`section` come back null in ordinary answers, and elision is a real state — the elided
counts and the `[reads]` bounds mean a payload can be a *narrowed* answer. A client
rendering a narrowed answer as complete shows less than there is and says nothing about
it.

### §RG4 Where a rename is allowed to go red

roadkeep's editor surface is held by `tests/test_editor.py` in roadkeep's own tree: the
JavaScript client is stubbed, the tool is real, and the keys that client walks are
asserted from Python, so a rename goes red before it reaches a reader in another
language. This app is a second client in another language and no such test covers it, so
the same rename reaches a user instead.

The half that can live here is the whole of it. A fixture repository is scaffolded by
`init`, populated by `add`, `ship`, `defer` and `non-goal add`, and every read this
client makes is run against it with the real engine. What is asserted is not the values
— those are the fixture's — but the *shape*: which keys exist, which are optional, which
carry a marker the config declared, and which paths are relative to which root.

Three findings this catches and nothing else does. A key renamed upstream. A payload
that began coming back narrowed because the fixture crossed a `[reads]` bound. And a
flag removed from a verb, which a version check alone reports as *newer* rather than as
*broken here*.

It runs against whichever engine the fixture resolves, which makes it honest about the
same thing `engines` is: this CI proves the reading against one build, and which build
is recorded with the run. A green suite is a claim about a version and never about
roadkeep in general.

### §RG5 A refusal that lands on the box it is about

Every write refused under --json returns a refused list, each entry carrying a code, the
field and the message the terminal printed, plus the whole refusal as prose. The app
reads the pair: the field decides which input is marked, the code decides whether there
is a door, and the prose is what a person sees when neither resolves. What it must not
do is parse that prose — the message is written for a reader and the code is the
contract. The doors table explain publishes is the same map one layer over, so a refusal
and a gate finding are handled by one reader.

### §RG6 Telling an old build from a broken one

The commands read is the only one that names this build and every argument each verb
takes on this project. Called once when a project is first opened, it answers three
questions no other read can: which version answered, whether a flag this app composes
exists here, and which verbs are published at all. What it produces is a capability
record kept beside the engine record, so a screen can withhold a door rather than offer
one that will be refused. A project too old to answer is drawn as unsupported with its
version, which is a state and not a failure.

### §RG7 What invalidates an answer

A read is keyed by the project root, the argv and the modification times of the governed
files roadkeep.toml declares. Anything else is a guess. The watcher is what expires an
entry, so a write by this app, by a terminal or by an agent all invalidate the same way
and no answer outlives the file it came off. Nothing persists across launches: the
non-goals refuse a store, and a cache surviving a restart is one that can be wrong about
a repository somebody edited while the app was closed.

### §RG8 The ceiling on a read

Every call carries a deadline and an abort signal, and a portfolio read runs through a
pool of fixed width so a hundred candidates never become a hundred processes. A read
that times out becomes a state on that project — unreadable, with the elapsed time and
the argv — never a spinner that resolves for nobody. The width and the deadline are
settings, because a slow disk and a fast one are different machines and this is the one
number a person may have to raise.

### §RG9 Getting a person's words in unchanged

Prose fields go in on stdin wherever the verb offers it: the why, a section body and
restate's symptom all read a dash. The add verb's symptom does not, which is filed
upstream, and until that lands this app composes that one field as argv and says so
rather than pretending it is safe. Spawning without a shell removes the quoting layer
but not the encoding one. What proves it is a round trip: write a symptom carrying an
accent, an apostrophe and an em dash, read it back with show, and compare the bytes.

## Block B — Discovery (which checkouts on this machine are governed)

### §RG10 Where the app is allowed to look

A root is a folder a person named, with a depth. Nothing is found outside one and no
default is invented from a home directory: an app that scans a drive on first launch is
an app that reads somebody's whole disk to draw a list. Roots and their depths are the
settings this app owns rather than reads, and the first run asks instead of assuming. A
root that has stopped existing is kept and marked, because a disconnected drive is not a
project somebody deleted.

### §RG11 The walk, and what it refuses to enter

The scan looks for one filename and nothing else. It never descends into .git,
node_modules, dist, build, target, a virtualenv or any hidden directory, and it stops at
the declared depth. A directory holding a config is a project and is not descended into
further, a governed repository not containing another. Those rules are configuration and
not constants, because a machine laid out differently needs a different list — and the
ignore set is the one part of a scan a person can be wrong about cheaply.

### §RG12 One backlog, several paths

Turing and Shio are kept as a git worktree per version under a stable junction, so two
version folders and the junction are three paths over one project family. Drawn flat
they are three rows with overlapping counts, one of them pointing at another. What tells
them apart is git itself: the common directory a worktree shares. So the grouping is
read and never guessed, and the app draws a family with its versions instead of either
merging them or repeating them.

### §RG13 The cheap no

A candidate has to be rejected without reading a file. Until roadkeep answers that in
one call, this app uses the narrowest thing that exists: the presence of the config
decides the candidate, and the config read decides whether it is governed, its source
coming back null when it is not. What it must never do is walk up looking for a config
itself, which is roadkeep's own discovery rule reimplemented here and wrong the day that
rule moves. The upstream line is a dep on this one for exactly that reason.

### §RG14 A list that survives the window closing

The project list is a record: the roots that produced it, each project's path, its
family and when it was last confirmed. A launch draws that record immediately and
rescans behind it, so the first screen is never empty and a rescan is a diff rather than
a rebuild. A project the rescan no longer finds is marked missing and kept, since the
two reasons for that — deleted, or a drive not mounted — look identical and only one of
them is a removal.

### §RG15 The disagreement, drawn rather than resolved

The engines read answers per project with the writing copy, the plugin, the vendored
one, the gates and a verdict over the set. This block is finished when that verdict is
on the row: agreed, split, or swapped. A row that is split is not an error and must not
be drawn as one; it is a repository where two copies could write and the person needs to
know which did. What is refused is showing a count with no engine beside it, because
that count is an answer whose author has been dropped.

## Block C — The portfolio (many backlogs in one view)

### §RG16 The row, and what it is allowed to hold

One row per project: its name, its path, the block and marker counts stats printed, the
next ready line pick chose, whether the gate passes, and the engine that answered. Every
one of those comes off a payload — nothing is computed across projects, since a total no
single repository could reproduce is a number nobody can audit. Sorting and grouping are
the view's, and are the only things here derived rather than read. A project still being
read is a row in a pending state, never a row of zeroes.

### §RG17 The first screen, and what it costs

A cold start is the only moment every project is read at once and the one with no cache
to answer from. So the fan-out is bounded, results stream in as they arrive, and the
order is the recorded list rather than whichever process finished first — a list that
reorders while a person reads it is worse than one that fills in slowly. The cheapest
read that fills a row comes first and the expensive ones follow, so the shape of the
screen exists before its detail does.

### §RG18 Gate health, and what it costs to know it

The lint verb is the most expensive read there is and the only one that answers whether
a project drifted, so running it across a portfolio on every draw is not affordable. It
runs once per project per change, driven by the watcher rather than by the screen, and
the row shows the last verdict with when it was taken. A stale verdict says it is stale.
What the row must not do is imply clean where nothing has been run: unknown is a third
state and it is the honest one on first launch.

### §RG19 Picking across seventeen backlogs

Each project's pick applies three tiers inside its own file, and that ranking is
roadkeep's and stays roadkeep's. What this app may do is show those answers side by side
with the tier each was chosen by, so a person compares seventeen candidates rather than
remembering them. What it may not do is rank the projects against each other by any rule
of its own: an ordering nothing printed is exactly the fiction the non-goals refuse, and
there is no field in the format that would justify one.

### §RG20 Finding a line by the words on it

Search runs over the payloads already held, not over the files, so it costs nothing on a
warm list and never re-reads a repository to answer. What it matches is the symptom, the
why and the id, which are the three things a person remembers a task by. A project not
yet read is named as unsearched rather than silently excluded, since a search that
quietly covers eleven of seventeen backlogs is one whose empty answer means nothing.

## Block D — The project surface (one backlog, read)

### §RG21 The lines, and the order they arrive in

The list read prints the lines a filter selects, verbatim, and reports on stderr any
marker-bearing line the grammar refused, with a count. Both halves are drawn: the
rejected ones are what a person has to see, and a listing that looks complete when it is
not is the failure that read was built to avoid. Order is the file's own order — the
blocks as the headings run and the ids under them — because that is the order every
other roadkeep answer speaks in.

### §RG22 Filters that are arguments, not predicates

Every filter on this screen is an argument the list verb already takes: the block, the
marker, the role, and the requirement a caller says it has. Choosing one re-runs the
read rather than filtering an array, so the answer is the tool's answer and a narrowing
this app invented can never disagree with one it did not. The cost is a call per change,
which is what the cache is for. What stays in the client is only text search, which no
argument covers.

### §RG23 One read, and the whole cost of starting

The detail is the brief payload and nothing beside it. That one read carries the line,
its deps and what resolves them, the design section whole, what shipping it unblocks,
the criteria and non-goals that bind it, whether it is held by a claim, and what the
ledger already shipped citing this id. Six reads composed here would be six chances to
compose them differently from the way the tool does. The screen's job is to lay that
payload out, and where it comes back narrowed, to say so.

### §RG24 Prose shown as the file keeps it

The section arrives as a body string, wrapped at the width the project declared, with
its own paragraphs, lists and tables. It is rendered as Markdown and never reflowed, so
what a reviewer reads is what the gate measured and what a commit will diff. The word
count and the limit are shown beside it, because a section near its budget is a design
about to need splitting and that is worth knowing before somebody adds to it.

### §RG25 A chain, drawn once

The deps read resolves blockers, chains, the transitive set and any cycle, and names the
deps nothing can resolve — work outside the backlog, which never becomes ready. That is
a graph the tool computed, so the screen draws it and derives nothing: no readiness
recomputed, no edge inferred from an id appearing in prose. What earns its place
visually is the distinction between a blocker inside the backlog, which shipping clears,
and one outside it, which shipping never will.

### §RG26 The two lists that decide what may be proposed

A non-goal says what is not built and a criterion says what would finish a block, and
between them they are what a proposal is checked against before it becomes a line. Both
are one read each. They belong where a person is about to write, not on a page somebody
would have to remember to open: the non-goals sit beside the add form and the block's
criteria sit at the head of its list, where the question of whether the block is
finished is actually asked.

### §RG27 What shipped, and what was weighed

Three files this app shows and never writes prose into: the ledger, which the delivered
read answers per block and is the read before an add; the decisions file, where the
reversals read names what was already decided and undone, with the argument; and
whichever prose file holds the sections. Together they are the memory a proposal is
tested against. They are reads and not screens of their own — reached from a block and
from a task, because that is where the question comes up.

### §RG28 The pause, and how long it has stood

A deferred line kept its id, its deps, its symptom and its section, and only left the
block. The stale listing prints those with how long each pause has stood, measured in
commits over the governed files, oldest first, with the reason beside it. That order is
not a verdict and must not be drawn as one — how long a pause may stand is a judgement
about work. What the screen adds is the door back, which is the direction the ledger has
none of.

**No store of its own** bounds this line without forbidding it, and so does **No
account, no auth and no remote store in the desktop build**: the deferred store is
roadkeep's, one of the roles the config declares, and this app reads it exactly as it
reads the roadmap. A second copy of it here would be the thing those two refuse.

## Block E — The write path (the app composes an argv; the command writes)

### §RG29 The write path, and where it stops

This app composes an argv and runs it. It never opens a governed file, never renders a
line, never fills a field. What it adds over a terminal is the schema arriving before
the prose: the budget for each field, the markers this project declared, the blocks that
exist, the deps that resolve — all read, none remembered. The verb still decides and its
refusal is what the person sees. That is the same argument roadkeep's editor surface
makes, and the reason a write here cannot drift from a write there.

### §RG30 Moving a marker, and what moves with it

The status verb sets a marker in the roadmap and nowhere else, and the in-progress one
takes a claim with it — refused where somebody already holds that line, and given back
by any other marker. So this is not a dropdown over an enum. The markers offered are the
ones the project declared, a move to the working one is a claim and is drawn as one, and
a refusal because another caller holds the line is a sentence about a person and not a
validation error.

### §RG31 The four ways a line leaves

A ship writes the ledger entry, clears the roadmap line and drops the section, in one
transaction or none. A retire records a departure without a ship. A defer moves the line
to the deferred store keeping every slot. A resume brings it back. Each takes a sentence
the person writes and this app never drafts. Each is irreversible in the direction that
matters, so each is confirmed against what it will do — which the verb itself already
prints, including the paths a live claim declared.

### §RG32 Writing the design where the pointer points

Every line carries a pointer that resolves to nothing until a section exists, and the
add verb says so in its own answer. So the section is offered in the same flow as the
line, with its word budget shown before the first paragraph — which is what the add
verb's own section flag does in one transaction. Amending is the other half: a section
is read back and corrected as a fragment, since the stored copy is wrapped and matching
it by hand is the caller's problem the verb already solved.

### §RG33 A finding that can be run

Every gate finding carries a code, a file, a line and column, and the complete argv that
closes it, and a repair pass spends a whole report in one call. The explain read says
what a code means and which doors it has. So this surface is a translation and decides
nothing: a door the tool marked complete becomes one action, an incomplete one opens the
form with the blank a person has to fill, and the repair pass is offered whole with its
dry run first.

### §RG34 The command, on screen

Before a write runs, the argv it will run is shown as a line a person could paste into a
terminal, and after it runs it stays in a log with its exit code and what it wrote. Two
things this buys that a confirmation dialog does not: a person can check the flags
against what they meant, and a defect in this app is reportable as a command rather than
as a description of a screen. The verbs already print what they staged, so that line is
kept beside the argv rather than re-derived.

### §RG35 The corrections that keep the id

Three verbs exist because retiring and re-adding spends an id and deletes a design that
was right. Amend corrects a why, the deps or the pointer. Restate corrects a symptom
whose claim turned out false, keeping the id, the deps, the marker and the design.
Renumber moves a line to a free id with its section and its dependents. Each is a narrow
door with a narrow form, and the reason each exists belongs on the screen offering it,
since the wrong one is the expensive one.

### §RG36 The budget, before the sentence

The budget read prices every field of the line that does not exist yet: what the symptom
has, what the why has after the structure and the deps are counted, what the section has
in words, and the aim each is composed towards. It is called when the form opens and
again when a dep or a block changes the arithmetic. The counter counts down against the
tool's number and never against one this app derived, and it is an aim rather than a
gate — the verb still decides.

## Block F — The agent surface (handing one task to Claude Code)

### §RG38 What a session is handed, and what starts it

Claude Code runs headless — `claude -p <prompt> --output-format stream-json`, a child
process writing one JSON object per line. That call is the whole integration, and
everything difficult about it sits on either side of it.

What goes in is not a prompt somebody typed. It is the payload `brief` returned for the
task: the tier it was chosen by, its deps, its design section, what shipping it
unblocks, and the criteria and non-goals that bind it. That is the read roadkeep's own
skill tells an agent to start from, and re-composing it here in English would be this
app paraphrasing the tool. The prompt is a short frame around a payload.

Where it runs decides what it can do. The session's working directory is the project
root, so the project's own wiring answers: its `roadkeep.toml`, its guard, its skill,
its `.mcp.json`. This app passes no configuration and installs nothing, which is the
engine rule again — the session runs the project's roadkeep and not this app's idea of
one.

Three failures are certain and each needs a state rather than a crash: no `claude` on
the machine, a session that exits non-zero, and a session cancelled from the window. The
process is owned, killable, and its exit is drawn.

What this app never does is write the backlog on the session's behalf. The agent writes
through the same verbs a person does, and the app watches the files change.

### §RG40 The stream, and what a person needs from it

A headless session emits one JSON object per line: turns, tool calls, results and a
final message. Rendered raw it is a log nobody reads. What matters while a session runs
is which tool it is calling and on what, and whether it has touched a governed file — so
the stream is drawn as a sequence of acts with the text between them, and the roadkeep
calls are marked. The raw form stays reachable, since a session that went wrong is
diagnosed from what it actually emitted.

### §RG41 Taking the line, not just reading it

Every tier of a pick is a function of the file, so a second caller reading an unchanged
backlog is handed the line the first one took. The brief verb with its claim flag
answers and moves the marker in one transaction, which is the call that starts a task
anyway. So handing a task to a session takes it in the same act. A claim is an expiry
and not a lock: it is stepped over once the declared time has passed, it carries no
owner, and this app never re-dates one to keep it.

### §RG42 What the session did, beside what it said

An agent writes through the same verbs a person does, so the evidence a session worked
is the governed files changing. While one runs, those files are watched and the task on
screen is re-read as they change — the marker moving, the section appearing, the line
leaving for the ledger. That is drawn beside the stream rather than inside it, since one
is what the agent said and the other is what the repository now holds, and the second is
the one that is true.

### §RG43 The other command this app runs

This app resolves a roadkeep engine per project and says what it found; it does none of
that for the command that runs a session. So the same treatment: resolve it once, record
which binary and which version answered, and show a machine without one as a stated
condition rather than a failure at the moment work starts. Nothing is bundled here
either, and for the same reason — the session runs the person's own installation, with
their own authentication and their own settings.

## Block G — The shell (an executable now, a service later)

### §RG37 Three packages, and why the split is the design

Three packages, and the split is the whole design. **core** is TypeScript with no
Electron and no React: the transport interface, the verb table, the payload shapes and
their parsers. **ui** is React and TypeScript over Tailwind and shadcn, and it receives
payloads and renders them. **shell** is the Electron main process: it spawns, it watches
files, it holds settings, and it is the only place a path or a process appears.

Electron rather than a native toolkit because the second life of this project is a web
service, and in that life **ui** is served to a browser and **core** runs behind an HTTP
handler with a different transport under the same interface. The cost is honest and
worth stating: a large runtime, a heavier executable, and a renderer that has to be
locked down because it is a browser. Tauri would spend less and would leave the same
seam; it was not chosen because the toolchain here is already the one the site is built
with.

Vite and React 19, matching roadkeep's own site, so the build conventions already exist
in a repository beside this one.

What the scaffold has to produce before anything else can be built is a window that
opens, a renderer that hot-reloads, a typecheck that runs over all three packages at
once, and a test command that runs without a display. Everything after this is filed
against it.

### §RG44 A renderer with a browser's powers, on purpose

Context isolation on, node integration off, remote module off, and one preload exposing
a narrow typed channel. That is a security posture and it is also the whole web port:
the renderer already runs with exactly what a browser would give it, so serving it later
changes the transport behind the channel and nothing in front of it. Navigation is
refused to anything but the app's own origin, and external links open in the system
browser — a renderer that can navigate is a renderer that can be navigated.

### §RG45 What to watch, and who is told

The config declares every governed role, so what to watch is read and never guessed:
those files, per project, plus the config itself. A change expires that project's cached
reads and tells the screens holding them. Writes made by this app are watched the same
way as writes made by anything else, so there is one path to a redraw and no special
case that can go out of step. Watchers cost a handle each, so only projects on screen or
running a session hold one.

### §RG46 The executable, and what it says about itself

A packaged build has to answer three questions from inside itself: which version it is,
which commit it came from, and whether it was signed. Those go on an about surface and
into whatever a defect report carries, because a bug from a packaged app is otherwise a
screenshot with no build attached. Packaging is also where the security posture stops
being configuration: a build is checked against the settings it claims, so a renderer
that gained a power during development does not ship with it.

### §RG47 The one thing this app owns

Everything on screen is read from a repository except this: the roots, their depths, the
ignore set, the pool width, the theme and the locale. That file is small, versioned, and
validated on read — a settings file that fails to parse resets to defaults and says so,
rather than taking the window down. It holds no project data and no cached answer, which
is the non-goal about a store of its own restated as a file format.

### §RG48 Proving the seam instead of describing it

The claim is that the client's transport is one interface, so the same reads answer over
a process today and over an HTTP handler later. Nothing tests that, and an interface
only one implementation ever uses is one that has quietly grown a dependency on that
implementation. What holds it is a second transport in the test suite — not a mock, a
real one that carries the same argv somewhere else and returns the same payload — and
the whole read surface run across both. What that catches is the thing a review never
does: a path, a working directory or an exit code leaking upward.

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

### §RG55 Where the promises are actually kept

Four things run on every change and each closes a hole this plan would otherwise have:
the typecheck across all three packages, the contract test against a real roadkeep,
roadkeep's own gate over this project's docs, and the contrast and keyboard assertions.
The gate is the one worth naming twice — this repository is governed, so a change that
drifts its own backlog has to fail here for the same reason it fails anywhere else. What
CI must not become is the only place any of them runs: each is a command a person can
run locally, and CI is what refuses to forget.

### §RG56 What a session is told, and what it costs

An instruction file is loaded on every turn, including the ones that touch none of this,
so it is an index and not a manual: what the three packages are, where the seam is, and
which rules are not negotiable. Everything longer belongs in a skill that loads when it
is needed — which is the argument roadkeep makes about its own, and the reason its
budget table exists. That budget is declared here too, in lines and bytes, so the file
is held by the gate rather than by a sentence at the bottom of itself.

## Block H — The look (a design system for governed prose)

### §RG39 Editorial, light-first, and sized to the format

What this app renders is governed prose, and the format already decided its shapes. A
task line is up to 320 characters. A section is up to 250 words, wrapped at 88 columns
in the file. A non-goal is a bold lead and a reason. Those are what the type must serve,
and none is a card with four words in it.

So the direction is editorial and light-first: a generous measure, one clear reading
size, and space used to separate a claim from its reason rather than to decorate.
Density belongs to the two list surfaces — the portfolio and the backlog — and reading
belongs to the detail. One theme, two densities, and no third mode invented per screen.

The tokens are the contract: a colour ramp, a type scale, spacing, radius and a
monospace face for ids, markers and argv. Every component takes them and no component
names a hex value. Dark is the same tokens re-pointed and never a second stylesheet.

shadcn is copied in rather than depended on, which is what it is for: the components
live in this repository and are edited here, so a variant this app needs is a change and
not a fork. Tailwind carries them as CSS variables, so one value reaches a component and
a chart alike.

What is refused is a look that makes 320 characters feel like an overflow, since that
length is the format working correctly.

### §RG51 One catalogue, from the first screen

Every string a person reads comes from a catalogue keyed by an identifier, with English
as the base and a second locale as a file beside it. Doing this from the first screen
costs almost nothing and doing it later costs every screen twice. Two things stay out of
it: what a payload printed, which is the project's own prose in whatever language it was
written, and a refusal message, which is the tool's words and is quoted rather than
translated. What is translated is this app's own voice.

### §RG52 The same tokens, re-pointed

Dark is not a second stylesheet: it is the same tokens with different values, so a
component names a role and never a shade. Which ground is drawn follows the system by
default and is overridable, and the choice is a setting like every other one. What has
to hold in both is the thing this app is for — a 320-character line and a 250-word
section have to stay comfortable to read, which is a contrast and a measure question
rather than a palette one.

### §RG53 Rendering a set this app does not own

The markers are whatever the project declared, arriving as codepoints, so nothing here
may map them to icons of its own — that is a rule compiled into a reader. What this app
owns is how they are drawn: one font stack chosen for coverage, a fixed box so a row
does not jump when a glyph is wider, and a readable label beside each taken from the
config rather than from a table here. A codepoint with no glyph on this machine falls
back to the label and is still a status somebody can read.

### §RG54 The half a screenshot cannot show

Two properties are held by tests rather than by intent. Contrast is computed over the
token pairs in both grounds, so a palette change that dims a label is a red build and
not a review comment. And every surface is reachable and dismissable from a keyboard,
with focus visible, which is the part that breaks silently as dialogs and menus
accumulate. Beyond that: a status carries a shape or a word as well as a hue, and text
is text rather than an image of one.
