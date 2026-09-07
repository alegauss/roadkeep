# Improvements

## Block A — The client (payloads in, types out)

### §RG9 Getting a person's words in unchanged

Prose fields go in on stdin wherever the verb offers it: the why, a section body and
restate's symptom all read a dash. The add verb's symptom does not, which is filed
upstream, and until that lands this app composes that one field as argv and says so
rather than pretending it is safe. Spawning without a shell removes the quoting layer
but not the encoding one. What proves it is a round trip: write a symptom carrying an
accent, an apostrophe and an em dash, read it back with show, and compare the bytes.

### §RG64 Two suites, because they answer different questions

`npm test` now runs two kinds of test through one command. Most of it is pure: a verb
table, a client over a fake transport, a boundary check over source text, a renderer in
jsdom — all of it finishing in about a second. Four tests spawn a real Python roadkeep
against this repository, and those alone take five.

The ratio is about to get worse rather than better. RG4 exists to assert every payload
this app reads against a live engine, which is one process start per verb, and RG6 adds
another. A gate that takes a minute is one people stop running between edits, and the
tests they stop running are the fast ones that would have caught the mistake.

So this wants two commands over one suite: `npm test` staying the fast one, and a second
— `npm run test:live` — carrying everything that spawns. Vitest's project mechanism
already splits them; what has to be decided is which project a new test lands in and
what makes that obvious, because a live test filed in the fast project is how the split
quietly stops holding.

The live suite also has a dependency the fast one does not: `python` on PATH, plus the
launcher this repository commits. That is worth stating where CI is configured, since a
machine without it fails four tests for a reason that has nothing to do with the code.

### §RG65 One file, two spellings, two process starts

Resolution asks a candidate for `engines --json`, reads the `invoke` it reports, and
where that names a different command line reaches it once to check it is the same copy.
The check is right and should stay: adopting a command line without running it is how an
app answers from an install nobody chose.

What is wrong is how often it fires. `invoke` is built with posix separators, and a
candidate assembled from a filesystem path on Windows holds native ones, so `python
D:/proj/.claude/hooks/roadkeep-launch.py` and `python
D:\proj\.claude\hooks\roadkeep-launch.py` compare as different while naming one file.
Every Windows resolution therefore pays a second interpreter start it did not need —
measured at roughly 2.3 seconds, which is what pushed this repository's own test past
Vitest's default ceiling.

The fix is a comparison that knows two spellings of a path are one, and the awkward part
is where it lives: `core` has no `path` module and must not grow one, since it is the
half a web service keeps. So the comparison is either passed in by whoever has a
filesystem, or done on a normalised copy of both strings with the separator as the only
thing normalised. The second is smaller and is probably right, but it is a rule about
paths sitting in a package that is meant not to know about them, which is worth deciding
rather than assuming.

RG7's cache reduces how often this is paid; it does not make the first read of each
project cheaper.

### §RG66 Two tables that have to stay the same length

A verb is an entry in `VERBS`, which builds its argv. A payload is a shape in
`payloads.ts`, which reads its answer. Nothing connects the two, and they are already
out of step: `brief` builds a perfectly good command line and has no shape, so its
answer would come back as a string somebody parses at the call site — which is the `any`
this block just spent a task removing, arriving one layer up instead.

`engines` is the same gap from the other side. It has a reader, written before the
toolkit existed, that answers `null` rather than a named failure. The information a
refusal is supposed to carry — which field, what was there, which engine version — is
discarded exactly where the first call of every project is made.

What closes it is making the two tables one: a verb declares its argv *and* its reader,
and calling one returns the parsed value or the failure. Then a verb with no shape is a
compile error rather than a hole, and `client.call` stops handing back raw stdout for
anybody to interpret.

RG5 added the last piece and left it disconnected. `readAnswer` turns a result into a
payload or a refusal, and every call should go through it — but `client.call` still
hands back raw stdout, so using it is something each caller remembers. One call is what
makes it unavoidable rather than advisable.

### §RG67 The answer shape nobody here has produced

`list --json` was read from real output and its shape demands a `tasks` array. The
engine's own documentation says something else can arrive: where a project declares
`[reads] list`, a listing past that bound comes back as its blocks and counts with the
narrowing that fits, rather than as the lines. That is a different shape, and the reader
written here would refuse it — reporting *this app is behind the engine* for a project
that is simply large and has said so.

It could not be modelled when the shape was written, and that is worth stating plainly
rather than guessing around: this repository declares no `[reads]`, so no payload of
that shape exists to read one off. Inventing it from the sentence that describes it is
exactly the second declaration of roadkeep's format the non-goals refuse, and a shape
invented that way fails silently in the direction nobody tests.

So the work is: declare a read bound in a scratch project, capture the answer, write the
shape from it, and make `list` return one of two readings. The narrowing helper already
means "smaller than the file", and a blocks-and-counts answer is the strongest case of
that, so it should arrive through that door and not as a refusal. "No engine the reader
cannot name" is not reached: the reader here reads a payload, and which roadkeep answers
is not in question.

Until then the failure is loud, which is the right way round for a hole this size.

### §RG68 One fixture, many reads, one interpreter start each

The contract test builds a governed project with the real write verbs — `init`, a
non-goal, a criterion, five `add`s, a `ship`, a `defer` — and then reads it with every
verb this client calls. Every one of those is a Python interpreter start of roughly two
seconds, and the file now accounts for most of the suite's wall clock.

Two things would help and they differ in kind. The fixture is built once per file
already, so what is left is the reads: several ask for a listing purely to find an id to
show, which could be one call. That is ordinary tidying and worth doing first.

The larger one is that the fixture is rebuilt every run even though nothing about it
changes between runs. It could be built once into a directory keyed by the engine
version and reused until that moves — the key `engines` already answers. What makes that
worth care is that a stale fixture is a contract passing against a project the current
engine did not build, which is worse than a slow suite.

RG64 splits this file out of the fast suite, which stops the cost being paid on every
edit. This line is about the cost itself, and the two are worth doing in that order:
moving something slow is cheaper than making it fast, and it may turn out to be enough.

### §RG69 The verbs that are two words

Reading `commands --json` turned up something the verb table cannot currently express.
Twenty-three of the eighty-nine entries are not top-level verbs at all: `section show`,
`capture filed` and `capture sweep` arrive as single names with a space, and the
families behind them — `section`, `block`, `non-goal`, `criterion`, `priority`,
`record`, `refs` — are exactly where the write path is going. Every rationale section
this app will file goes through `section add`.

Today a verb is one key in `VERBS` and one word on the command line, and the capability
check looks a verb up by that word. A two-word verb would be looked up under the wrong
key, reported as one this build cannot run, and its door withheld — which is the failure
mode this read exists to prevent, arriving through the read itself.

The fix is small and worth doing before block E rather than during it: a verb's key
stays a single identifier this app uses, and the table carries the words that go on the
command line as an array. `commands` is then looked up by joining them, and `buildArgv`
spreads them. What it must not become is a string split on spaces, because the point of
argv being an array is that nothing in this app ever splits a command line into
arguments.

## Block B — Discovery (which checkouts on this machine are governed)

### §RG13 The cheap no

A candidate has to be rejected without reading a file. Until roadkeep answers that in
one call, this app uses the narrowest thing that exists: the presence of the config
decides the candidate, and the config read decides whether it is governed, its source
coming back null when it is not. What it must never do is walk up looking for a config
itself, which is roadkeep's own discovery rule reimplemented here and wrong the day that
rule moves. The upstream line is a dep on this one for exactly that reason.

### §RG15 The disagreement, drawn rather than resolved

The engines read answers per project with the writing copy, the plugin, the vendored
one, the gates and a verdict over the set. This block is finished when that verdict is
on the row: agreed, split, or swapped. A row that is split is not an error and must not
be drawn as one; it is a repository where two copies could write and the person needs to
know which did. What is refused is showing a count with no engine beside it, because
that count is an answer whose author has been dropped.

### §RG71 A scan that does not hold the process still

The walk reads each directory with `readdirSync`. On the machine it was written for that
is a few milliseconds for the whole tree, which is why it was the right first version —
the bounds are what make a scan cheap, and proving those was the task.

What it does not survive is a slow root. A network share, a sleeping external drive or a
directory behind a virus scanner turns one read into hundreds of milliseconds, and every
one of them is time the main process spends doing nothing else. The window is drawn by
another process so it keeps painting, but every IPC call behind it queues, so the app
stops answering while a drive spins up.

The change is small and the shape is already there: `Look` is the only thing that
touches a disk, so an asynchronous one is a second implementation of one function. What
has to change with it is `scan`, which becomes async, and the bound on how many
directories are open at once — the same argument as RG8's pool, for the same reason, and
probably the same mechanism.

Worth keeping while doing it: the walk stays breadth first and still reports `looked`,
because that count is what makes the bounds checkable and it is the first thing that
would quietly stop being true.

### §RG72 Which version of a family reads first

Grouping keeps scan order all the way down, which is right for the families themselves —
the walk is shallow-first and that is the order somebody is watching a list build in.
Inside a family it is arbitrary. `2026.2` and `2026.3` are returned in whichever order
the directory listing produced, so the same machine can draw a family newest-first today
and newest-last after a folder is touched.

What a person means by a family is a current version and some older ones, and the
junction already says which is current: `latest` points at one of them, and that member
is the one carrying an alias. That is a fact the grouping already has and throws away.

So the ordering is: the member the stable name points at first, then the rest. The rest
by what, is the open question. Folder names sort correctly for `2026.2` before `2026.3`
and stop doing so at `2026.10`, which is the version-sorting trap every tool falls into
once. Modification time is available and means something different — the one worked on
most recently, not the newest version — and may be the more honest answer for a list
somebody is choosing from.

Not urgent while the app draws no list. It becomes visible the moment block C does, and
it is cheaper to decide now than to notice from a screenshot.

## Block C — The portfolio (many backlogs in one view)

### §RG20 Finding a line by the words on it

Search runs over the payloads already held, not over the files, so it costs nothing on a
warm list and never re-reads a repository to answer. What it matches is the symptom, the
why and the id, which are the three things a person remembers a task by. A project not
yet read is named as unsearched rather than silently excluded, since a search that
quietly covers eleven of seventeen backlogs is one whose empty answer means nothing.

### §RG73 Four reads to draw one row

A filled row wants counts, the next line, the gate and the engine, and each is its own
verb. Four interpreter starts per project is sixty-eight over seventeen, and at roughly
360 ms each that is most of what a cold start costs — before RG17 has run any of them
concurrently or RG18 has decided how often the gate is worth paying for.

Three ways out, and they are not alternatives so much as an order. **Not every read is
needed to draw a row**: counts and the engine are what a list is scanned for, and the
gate and the next line can arrive after, which turns a cold start into one call per
project and three later. **The reads are independent**, so within one project they can
go out together, which is RG17's pool doing what it already does. And **the engine read
is already done** by resolution, so asking again per row is a call this app makes twice
for one answer.

What would remove the problem rather than manage it is a verb that answers all four, and
this app does not get to invent one — that is roadkeep's decision and a request rather
than a task here. Worth writing down because the measurement belongs with it:
sixty-eight calls is the number that makes the case, and nobody will have it later.

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

Two things the runner has to have, learned by shipping RG1. **Python, plus the launcher
this repository commits**, because the tests that fetch a real payload spawn `python
.claude/hooks/roadkeep-launch.py`; without it four tests fail for a reason that is not
the code. And **a display for whatever RG60 launches**, which on a Linux runner means a
virtual framebuffer and on Windows or macOS means nothing at all.

### §RG56 What a session is told, and what it costs

An instruction file is loaded on every turn, including the ones that touch none of this,
so it is an index and not a manual: what the three packages are, where the seam is, and
which rules are not negotiable. Everything longer belongs in a skill that loads when it
is needed — which is the argument roadkeep makes about its own, and the reason its
budget table exists. That budget is declared here too, in lines and bytes, so the file
is held by the gate rather than by a sentence at the bottom of itself.

### §RG57 Watching the half that does not hot-reload

`npm run dev` runs `tsc -b` once and hands the Vite URL to Electron. The renderer
hot-reloads from there, so a change to `ui` is on screen before the file is saved twice;
a change to `shell` is on screen only after the window is closed, the run killed and
started again. The asymmetry is the whole defect, and it gets worse exactly as the main
process gets interesting: settings, the file watcher and the spawn all live there, and
each is a thing somebody iterates on.

What this needs is a watch over `packages/shell/src` and `packages/core/src` that
recompiles and restarts the Electron child without touching the Vite server, because
restarting the server throws away the renderer state that made the change worth looking
at. The restart has to be debounced — `tsc -b` writes several files per build and a
watcher that fires per file restarts the app four times — and it has to wait for the
compile to succeed, since restarting into a broken build replaces a useful error with a
crash.

Worth stating what this is not: it is not `electron-vite`. Adopting a framework to get a
file watcher would put the three-package split under a tool that assumes one package,
and the split is the design.

### §RG58 The gate a typecheck is not

`npm run typecheck` and `npm test` between them say the code compiles and behaves.
Neither says anything about an import nobody uses, a React hook whose dependency list is
wrong, a floating promise, or a second spelling of a name that already exists two
packages over. Those are the defects that accumulate quietly in a repository worked by
agents, because each one is individually below the threshold anybody would raise it at.

What belongs here is a flat ESLint config at the root with three overlays — `core`
forbidding any import of `electron` or `react`, `ui` forbidding `node:` and `electron`,
and `shell` allowed both — so the package split is enforced by the gate rather than by
the paragraph that describes it. That import boundary is the part worth the setup; the
stylistic rules are the cheap half that comes with it. Formatting is Prettier's, run as
a check and not as a commit hook, because a hook that rewrites files under a commit is
how a diff acquires changes nobody made.

One command, `npm run lint`, added to the table in the roadmap skill and to whatever
RG55 makes CI run. It fails the build or it is advice.

### §RG59 The half of the posture that is about loading, not calling

Context isolation, the sandbox and the navigation guard together settle what the
renderer can *do*. None of them settles what it can *fetch*. A page that ends up with a
remote `<script>` — an injected tag, a dependency that grew a CDN call, a payload
rendered as HTML — runs that script with the bridge sitting on `window`, and the guard
never fires because nothing navigated.

A Content-Security-Policy is the missing half: `default-src 'self'`, no remote script,
no inline script, images limited to `self` and `data:`. The reason it is a task rather
than a line in `index.html` is that the dev server needs its own policy — Vite injects
an inline preamble for React Refresh and talks to itself over a websocket, so one policy
strict enough to be worth having in a packaged build breaks `npm run dev`. Two policies,
chosen by whether `ROADKEEP_GUI_RENDERER_URL` is set, is the shape; the packaged one is
the one that matters and the dev one exists so nobody turns the mechanism off to get
work done.

What proves it is a test, not a header: a run that loads the bundle and asserts that a
remote script is refused. Reading a policy string tells you it was written, not that it
applies.

### §RG60 Asking the running window instead of reading its configuration

The suite asserts the navigation policy as pure functions and the renderer against a
stubbed bridge. Both are worth having and neither starts Electron, so nothing catches
the failures that live in the wiring: a preload path that stopped resolving, `sandbox`
dropped from `webPreferences`, a handler registered on a channel the preload no longer
invokes. Each of those leaves every existing test green.

What answers it is a test that launches the built app with `--remote-debugging-port`,
attaches over the DevTools protocol and asks the page four questions: that
`window.roadkeep` holds exactly the methods the interface declares and no others, that
`identify()` round-trips, that `require`, `process`, `module` and `ipcRenderer` are all
undefined, and that assigning `location.href` to a path outside the bundle leaves the
page where it was. Those are the checks that were run by hand when RG44 shipped, which
is the argument for automating them: they were run once, against one build, by somebody
who happened to think of it.

It needs a display-less run to be worth putting in CI, so the Linux job wants a virtual
framebuffer; Windows and macOS runners have a desktop session already. That is the cost,
and it is why this is its own line rather than a paragraph inside RG55.

## Block H — The look (a design system for governed prose)

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

### §RG61 An advisory that arrives with somebody else's package

Installing the design system brought one finding: `xlsx` is reported high severity and
reaches this app as a transitive dependency of `@viglet/viglet-design-system`. The
package on npm is the unmaintained SheetJS build, whose advisories are prototype
pollution and a regular-expression denial of service, and no patched version exists on
that registry.

What is actually exposed here is narrow and should be established before anything is
done. This app parses no spreadsheet, and the renderer that would run the code has no
filesystem and no process. If the bundle does not include `xlsx` at all — Vite
tree-shakes what nothing imports — then the advisory is about the install tree and not
about the executable, and the answer is a documented note rather than a change. That
measurement is the first half of this task and it may be the whole of it.

If it does ship, the fix is not this repository's: it is a line in the design system,
either dropping the dependency or moving to the maintained `xlsx` distribution SheetJS
publishes outside npm. That makes this a line that ends in somebody else's release, so
it wants the wait-watcher the sibling consoles use — a test pinning the installed
design-system version, which fails when it moves so the wait is read again rather than
sitting unnoticed.

### §RG62 Joining the checks the other consoles already answer to

Depending on the design system is half of consuming it. The other half is the two
mechanisms Shio and Dumont run, and this app has neither.

The first is `viglet-ds-check-duplicates`, a gate shipped in the package's own bin. It
reads `exports.json` through the consumer's module graph and fails on any component
declared here that the package already exports, naming the import that replaces it.
Dumont found nineteen such collisions with nothing failing anywhere. What both consoles
learned the hard way is that the gate has to be tested against a planted duplicate: a
gate wired to the wrong root reports a clean tree in exactly the same words as a clean
tree.

The second is registration in the package's `consumers.json`. It is the declared set the
design system holds itself to — six apps today, each recording its framework, chrome,
accent and the subpaths its source imports. A consumer that is not in it is one whose
parity claims were never checked, and the file's own reasoning says prose naming a
subset as though it were the whole is a test failure. That entry is a change to the
sibling checkout and wants its own commit there, which is why it is named here rather
than done quietly.

The word that trips the gate here is the JavaScript one. "No issue tracker, and no
export to one" forbids sending this backlog somewhere else; what this check reads is a
module's named exports, and nothing here moves a task anywhere.

### §RG63 The shell before the pages

The design system's page vocabulary is its bento layer: a nav rail, a user menu, a
command palette, a hero, a list mosaic and the save-bar morph, extracted from Turing and
shared with Shio. It is a separate entry point, so importing the tokens does not bring
it, and this app currently has none of it.

Its own authoring guide names the failure directly: the first mistake is a page that
looks bento inside a console that does not. So this is the shell, not a screen — a root
layout holding `BentoNavRail`, `BentoUserMenu`, `BentoCommandPalette`,
`BentoShortcutsDialog` and `BentoBackToTop`, with `bento-rail-gutter` around the routed
outlet and `bento.css` imported beside the tokens.

Three things it drags in that are worth knowing before starting. `./bento` needs
`react-router-dom`, so routing arrives with it rather than later. `BentoUserMenu` calls
the package's own `useCurrentUser`, and a local provider is a different context object
that renders the shell blank behind an error boundary. And jsdom implements neither
`matchMedia` nor `ResizeObserver` nor `scrollIntoView`, all three of which these
components use, so the suite needs the same polyfills the package sets up for itself.

The keybinding for the palette is this app's to choose; the component takes only open
state and items.
