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

Measured while shipping RG20, which is what makes this urgent rather than tidy. Six live
files in parallel put twenty-odd interpreters on eight cores, and the reads that lost
that race failed for being starved — one test passed alone and failed in a full run,
twice. `fileParallelism: false` fixed it and took the suite from forty seconds to two
minutes. Right for a gate, wrong for something run between edits, which is the split.

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

### §RG75 Ids that stop being true

RG23 shipped, and a test asserting RG23 was in progress failed with nothing changed to
cause it. RG24 fixed that one and found the same shape in three more assertions of its
own. The subject of a live test is this repository's backlog, and every commit moves it.

Two kinds of id are safe to write down. A shipped id stays shipped — nothing unships one
— and an id no file carries stays absent, which is what the refusal test rests on.
Everything else is a claim about today: open, blocked, in progress, carrying a design.

So a live test asks the engine for its subject instead. `brief` with no id picks an open
line, and an open line in this backlog always has a design; `list --marker` names one in
a given state; a state nothing here has — a line taken with `--claim` — is built in a
fixture rather than found. What is left is `RG9`, named twice for a dep pointing outside
this backlog. Exactly two lines carry one, and the fix is to find them by that rather
than to write down which.

The value of these tests is that they read the real thing, so the answer is never to
move them onto fixtures. It is to stop asserting about a line by its number.

### §RG78 One seam for a live read

Five live test files now open with the same twelve lines: resolve the repository root,
build a process transport on the launcher, wrap it in a client, then a helper that calls
one verb, hands the stdout to `readPayload`, and throws a sentence naming the expected
type, the path and what was found. `contract.test.ts` calls its copy `readVerb`;
`detail-live` calls it `detailOf`; `design-live`, `graph-live` and `binding-live` each
carry their own.

The copies have already drifted. Two report `(the answer)` for an empty path and one
reports nothing; the timeout constant is redeclared five times; `binding-live` needed a
second spelling because its verb name is two words. None of that is load-bearing, and
each new Block D task adds another copy.

What belongs in one place is the seam, not the assertions: a module beside `fixture.ts`
that hands back a client already pointed at the launcher and a `read(root, verb, input,
reader)` that fails with the message a person would need. The test files keep what makes
them different — which root, which verb, and what is asserted about the answer.

The failure message is the part worth centralising. It is the reason these helpers exist
at all: a shape that moved upstream has to name the key and the build that moved it, and
a copy that quietly says `undefined` is the one that wastes an afternoon. One
implementation is one place for that sentence to be right.

On ship: `--recorded-in packages/shell/src/live.ts`.

### §RG81 One way to spell a command line

`buildArgv` and `composeWrite` both build `['-C', root, ...verb.split(' '), ...args,
'--json']`, and three non-obvious rules now live in two places. `-C` is passed even
though the transport also sets the working directory, deliberately and for a reason
written down at one of the two sites. `--json` is appended by the composer rather than
declared per verb. A verb name is split on spaces because `non-goal list` is two words
while the table key stays whole, which is what `commands` publishes and what the
capability check matches.

They have already diverged. A read carries a `signal` through `CallOptions` and a write
takes only `timeoutMs` — that one is deliberate, since a write aborted mid-call leaves
the caller unable to say whether it landed, which is exactly the state `unreadable`
exists to name. But it is deliberate nowhere in writing: the asymmetry reads as an
oversight, and the next person to notice it will either document it again or remove it.

The fix is small and worth doing before the write table grows. One composer takes a
root, a verb name and the arguments a builder produced, and both paths call it; the read
and write tables stay separate, because that separation is about which doors may be
offered and not about how a command line is spelled. The signal's absence becomes a
sentence in the write path saying why, rather than a difference a reader has to
interpret.

On ship: `--recorded-in packages/core/src/client.ts`.

### §RG82 A version read three times

`contract.test.ts` reads the engine's version once in `beforeAll` and asserts two later
answers equal it. On a machine where the engine is a working checkout somebody is
editing, those are three reads of a moving number: this suite failed twice in one
afternoon with `expected '0.2.385' to be '0.2.384'`, having changed nothing, while every
shape assertion in the same test passed.

The version is worth asserting and the equality is not. The file promises that a green
run is a claim about one build, so what is useful is that a version was named and
reported — not that two reads of a tree under edit agree. Where identity does matter,
both halves belong to one read: comparing what came back from a single call is a claim
about that call rather than about the interval between two.

This is RG75's shape with a different moving part. There the assertion named a task id
and the commit that shipped it broke the test; here it names a version and a rebuild
does. In both the test asserts that the world has not moved, which is not what it was
written to check.

It matters more than a flake, because the failure is indistinguishable from the one this
file exists to produce: a red contract test is supposed to mean roadkeep renamed a key,
and a reader who has learned it also means "the version moved" is a reader who stops
believing it.

On ship: `--recorded-in packages/shell/src/contract.test.ts`.

### §RG83 The second shape a verb answers with

RG66 is about a verb with no shape. This is about a verb with two, which its fix does
not reach: one reader per verb still has to handle both answers, and nothing makes
anybody notice there are two.

Five are already known, every one found by hand at the moment it broke something. `ship`
answers `roadmap` as `{removed}` when it closes a line and as `{line, status, open}`
under `--part`, and a reader taking only the first draws a partial ship as a closure —
this cost a red live test and a shape rewrite. `show --no-body` sends `body` null where
the ordinary call sends a string. `delivered --near` adds `rank` and turns `near` from
null into a sentence. `criterion list --task` answers `empty` and `doors` where the
block form answers neither. `brief` sends `budget` null for a shipped line and an object
for an open one.

The pattern is exact: the flag that narrows or changes the write is the flag that
changes the answer, and it is never the call anybody writes the first test for.

So the contract test declares, per verb, the flag combinations whose answers differ, and
covers each — the way `EVERY_INPUT` already forces every *flag* to be exercised. A verb
whose second shape nobody named is then a gap in a list somebody has to fill in rather
than a reader that works until the day a person clicks the other button.

On ship: `--recorded-in packages/shell/src/contract.test.ts`.

### §RG84 One engine for the length of a run

Thirty-one live files each resolve the engine themselves, as they call it. Where that
engine is a working checkout somebody is editing, the suite reads a different program on
every call — and four runs went red today with nothing here changed.

Three shapes, one cause. Mid-edit the package does not import, so the launcher falls
back to a cached build that refuses this config and every read is unreadable. A rebuild
between two calls fails an equality on the version. A call landing between the states
answers differently from its neighbour. Each is indistinguishable from the failure the
contract test exists to produce, which is the cost: a red suite should mean a renamed
key.

The suite should read the engine once and use that reading throughout. Resolving in one
place — a module beside `fixture.ts`, alongside RG78's shared reader — gives every file
the same program for the length of a run, and a version that moves underneath is then
one answer at the start rather than thirty-one disagreeing.

It also names the engine in the report, which `No engine the reader cannot name` asks
for and no live file does today: a failure would say which revision answered rather than
leaving somebody to guess whether the code moved or the tool did.

This does not make the suite immune to a broken engine, and should not: it makes the
breakage arrive once and named, instead of as an assertion about a key.

On ship: `--recorded-in packages/shell/src/live.ts`.

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

### §RG89 One derivation of the marker set, not two

`openMarkers` was written for the status dropdown: it finds `markers.open`, parses
whatever the file spells there, and hands back a list. RG53 then wrote `markersOf`,
which walks every key in the markers table, folds the codepoints that several keys name
into one entry each, and labels them. The second is a superset of the first —
`markersOf(config).filter(isOpen)` is exactly what `openMarkers` returns.

A live test asserts the two agree against this repository's real config, which is why
this is a tidy-up and not a defect. But it is one config read two ways, and the ways
differ in what they tolerate: only one of them reads a key nobody declared, so a project
that leaves its open set to the default gets a dropdown of nothing from one reading and
a full set from the other. That case is not in any fixture because this project declares
its open set.

The fix is one line — `openMarkers` becomes the filter — plus deciding whether the
dropdown should offer a marker the project left to the default. It probably should, on
the same argument RG53 made about undeclared keys.

Worth doing before a second screen reads either one. Two derivations agreeing by test is
a thing somebody has to keep true; one derivation is a thing nobody has to.

## Block C — The portfolio (many backlogs in one view)

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

### §RG74 The marker and the claim are two different facts

Writing RG23's tests turned up something worth stating before a screen draws it. The
working marker on a line and an entry in the claim registry are separate: this session
moved RG23 to 🛠 and `held` stayed empty, because a claim is dated and released on a
window and a marker is not. A line can therefore be in progress with nobody holding it,
held by somebody with the marker not yet moved, or both.

The detail carries both already. What it does not do is say what the pair means, and the
two obvious readings are both wrong. Treating the marker as the claim makes every line
somebody started look taken forever, which is what the sixty-minute window exists to
avoid. Treating the claim as the only truth makes a line whose claim expired look free
while a session is still working it.

The honest reading is that they answer different questions — the marker says what state
the *work* is in, and the claim says whether a *worker* is on it right now — so a screen
shows both and never one as a proxy for the other. Where they disagree is exactly where
somebody needs to look, which makes the disagreement worth drawing rather than
resolving.

This becomes urgent at RG41, where an agent is handed a line: starting one that somebody
else is on is the failure that costs two people an afternoon.

### §RG76 The chain a brief already sent

`brief` sends `chains` on every line and this app's shape does not declare the key, so
RG25's graph is fetched with a second subprocess for a fact the first one already
answered. Block D's own criterion says a task opens in one read, and it does not today.

The two answers are not the same, which is the part worth getting right. A brief's chain
carries `path`, `end` and `detail`; `deps` adds `via` — the dep the file actually wrote,
which differs from the path wherever a block label or a range expanded into its members.
`deps` also carries `blockers` and `cycle`, and a brief carries neither.

So the read is not replaced, it is deferred. The chains a brief already has are declared
in its shape and drawn from it, which covers the ordinary open task; `deps` is what a
screen asks for when somebody wants the dep behind a hop, the cycle, or the blockers
named as a list rather than inferred from the chains. One is the page loading, the other
is a person asking a second question.

The reader is the one already written: `readDepChain` defaults `via` to empty, so the
brief's narrower chain parses against it without a second shape. What is missing is the
key on `BriefPayload` and a `graphFrom` that takes what a brief has — which is the same
lay-out over a payload with two of its lists absent, not a second module.

On ship: `--recorded-in packages/core/src/graph.ts`.

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

### §RG80 The refusal that knows where the line went

`brief FX1` and `show FX1` on a set-aside line both refuse, and the refusal payload
comes back with `refused`, `beside` and `about` all empty and everything in `said`. RG5
shipped the reader that turns a refusal into the field it is about; there is no field
here, so it turns into nothing. A screen calling the detail path on a paused id gets a
failed read and no reason it can act on.

The sentence itself is complete — it names the store, the line number, the listing that
prints the reason and the verb that brings the line back. It is also English, and
reading `is paused in` back out of it is the prose-scraping this client refuses
everywhere else.

RG28 already shipped the answer and nothing calls it. `filingOf` takes the three
listings and says open, shipped, paused or nowhere, off facts each listing states. So a
refused task read asks that question rather than reading the sentence: paused draws the
store entry and the door back, nowhere draws that nothing in this project carries the
id, and the two stop looking alike at the one moment they matter.

What that costs is the reads. `filingOf` wants three listings where the detail path made
one call, so this belongs behind the refusal and not in front of it: the ordinary open
task pays nothing, and only a read that already failed goes looking for why.

On ship: `--recorded-in packages/core/src/pauses.ts`.

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

### §RG50 Updating, and what has to exist first

An update check reads a release that exists on the internet, so this line needs a
published artifact and not merely code. What it must do is state which version it is on
and which it found, and never install anything without being asked — an app that
replaces itself while somebody is reading a backlog is one that loses their place. What
it must not do is phone anywhere on launch by default: this app reads a person's
repositories, and a network call it did not need is one that has to be explained.

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

### §RG85 What the seam's handler is allowed to be

RG48 built an HTTP handler in front of the process transport so the seam is proven by
two real transports rather than by a mock. That handler reads `{root, argv, timeoutMs}`
off a socket and runs it — any argv, against any root, with no authentication and no
allowlist. It binds to loopback and its own comment says it is a test's surface, which
is true today and is exactly the kind of true that stops being true quietly.

The observation worth keeping is not that the test handler is unsafe. It is that the
guard is the whole difference between the test's half and a service, and nothing
currently states what that guard is. The seam says the reads travel as data; it says
nothing about which reads a server should agree to run for whom, what a root is allowed
to be, or whether the write verbs cross at all.

So the day a service line is picked up, the first question is not the transport — that
part is done and held by a test. It is: what does the server refuse? A design that
starts from the working handler will inherit its permissions by default, because the
handler already works.

What would settle this is a short list of refusals written before the service is built,
not after it runs.

## Block H — The look (a design system for governed prose)

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

### §RG86 Carrying a locale from the settings to the screen

RG51 built the catalogue and the fallback, and proved both with a locale nobody speaks.
What it did not build is the path a real locale travels: `Settings.locale` holds a
BCP-47 tag, `localeFor` can choose among tags that exist, and nothing connects them
because no second locale exists to choose.

Three pieces are missing and they are small. A locale is a file — a partial map of the
same keys — and something has to list which ones this build ships, since `localeFor`
takes that list rather than discovering it. The shell has to read the chosen one and
hand it across the bridge, alongside the settings it already holds. And
`WordingProvider` has to take it, which it already does.

The question worth deciding first is where a locale file lives and who reads it. Bundled
with the renderer is the simple answer and makes a translation a release. Read from disk
beside the settings would let somebody add one without a build, which is a different
product and probably not this one.

`untranslated` and `stale` exist and nothing runs them, so a locale can drift from the
base without anybody hearing about it. Whatever holds the second locale should run both,
because the first thing that goes wrong with a translation is a key that moved
underneath it.

Nothing here is urgent while English is the only locale. It stops being small the moment
there are two.

### §RG87 Which copy of the ground setting is the real one

RG52 handed the switch to the design system, which is right — its own `Toaster` reads
the same library, and a second theme system writing the class from a second key is the
defect that package was consolidated to fix. What comes with that is `next-themes`
persisting the choice to `localStorage` under `vite-ui-theme`.

Meanwhile `Settings.theme` has been in settings.json since RG47, validated on read and
reset field by field with a sentence when it is wrong. Nothing reads it. So the choice a
person makes is remembered by the browser storage of one window, and the field this app
declared for it does nothing.

Two homes is not automatically wrong — one is a cache for the first paint, which is what
it is for, and `next-themes` injects a blocking script to use it before React runs. What
is wrong is that neither is stated to be the source. The shape that works is the file
being the source and storage being the cache: settings load, the loaded theme is handed
to the provider, and a change writes back through the bridge.

That is the same shape as the locale in [[RG86]] and probably the same piece of work:
one call that carries the settings across and hands both to their providers. Until then,
a person who sets the ground and reinstalls loses it, which is small, and a person who
edits the field by hand sees nothing happen, which is worse because it looks broken.

### §RG88 Two translation systems on one screen

RG51 built a small typed catalogue in `core` and it does what it was built for: the base
is the type, the fallback is per key, and a pseudo-locale fails the run a literal is
typed into a screen. None of that is in doubt.

What was not checked is that `i18next`, `react-i18next` and
`i18next-browser-languagedetector` are already dependencies of `@rk/ui`, declared when
the design system was adopted, because that package translates its own components with
them. So a screen mixing this app's components with the package's has two translation
systems on it, each with its own idea of the current locale — which is exactly the shape
of the theme problem in [[RG87]], and the package's own notes describe the harm: two
systems agreeing only by luck.

The question is not which library is better. It is which one holds *the locale*, since
there can only be one answer to what language this window is in. The likely shape is
that i18next holds the locale because the package's components read it from there, and
this app's catalogue is fed the same tag — its own lookup is fifty lines and does not
need replacing to stop being a second source.

Worth settling with [[RG86]], which is the line that first has to choose a locale at
all. Deciding it there costs nothing; deciding it after two locales exist means moving
both.

### §RG90 A token pair that fails before anything uses it

RG54's contrast test computes every pair this app renders. It also found one it does
not: `--vg-muted-foreground` on `--vg-muted` is 4.33:1 in light, under the 4.5:1 AA
needs for body text. In dark the same pair is comfortable, so it is a light-ground
defect only.

The pair is not enforced, and deliberately: nothing on any screen puts those two
together today, and a test defending a number nobody renders is a number somebody will
eventually weaken to make an unrelated change land. What is on screen is muted text on a
card, which clears in both grounds and is enforced.

But the tokens are *named* as a pair — that is what the shadcn convention means by `x`
and `x-foreground` — so the first muted panel anybody builds will reach for both, and
the label will be a little too pale in exactly the way nobody notices in review.

Three ways out, in order of how much they cost. Override `--vg-muted-foreground` in this
app's `:root`, the way RG54 overrode the ring — one line, and it darkens every muted
label everywhere, which may be right. Or never use `--vg-muted` as a text surface and
say so where somebody would look. Or take it upstream, since the pair is the package's
and every console using it has the same 4.33.

Whichever, the pair goes into the enforced list the moment a screen renders it.
