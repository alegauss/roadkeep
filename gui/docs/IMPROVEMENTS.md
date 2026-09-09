# Improvements

## Block A — The client (payloads in, types out)

### §RG9 Getting a person's words in unchanged

Prose fields go in on stdin wherever the verb offers it: the why, a section body and
restate's symptom all read a dash. The add verb's symptom does not, which is filed
upstream, and until that lands this app composes that one field as argv and says so
rather than pretending it is safe. Spawning without a shell removes the quoting layer
but not the encoding one. What proves it is a round trip: write a symptom carrying an
accent, an apostrophe and an em dash, read it back with show, and compare the bytes.

### §RG98 The boundary that is only a rule about imports

`boundaries.test.ts` reads every file in `core` and fails on an import of `node:`,
`electron` or `react`. That catches the loud way in. RG65 found the quiet one: a rule
about paths does not need an import. `left.replace(/\\/g, '/') === right.replace(/\\/g,
'/')` is nine tokens, has no dependency, typechecks under a config with no Node types,
and would have shipped the exact bug RG65 rejected — two different files on Linux
reported as one, in the branch that claims the declared engine was reached.

So `core` has a stated constraint with no gate. It is worth asking what a gate could
honestly hold. A grep for a backslash literal is narrow, cheap and would have caught
RG65's rejected fix; it would also flag prose in a docstring, which is most of what a
backslash is in this package today. `path.sep`, `win32`, `toLowerCase` on something
named like a path and a `..` segment are the other tells, and each is a heuristic rather
than a rule.

The alternative is to accept that this one is held by review and by the decision record,
and to spend nothing. That is a real answer and may be the right one — `core` is small,
and a gate that fires on docstrings gets an exception list, then a second one, and then
nobody reads it. What this line has to decide is which of the two, not how to build the
first.

### §RG99 Two doors into one read

RG66 gave `client.call` the verb's own shape and three answers: a payload, a refusal, a
failure naming the field. What it did not give it is the fourth state, and that is the
one a portfolio is made of — the call that never happened, timed out or was cancelled
still leaves this as a thrown `EngineCallFailed`. A screen drawing twenty projects has
to draw nineteen when one of them hangs, so every caller wraps every call in a `try`.

`attemptRead` is the other door and it has the missing state. It answers `ProjectRead` —
the value, or an `Unreadable` carrying the reason, the elapsed time, the argv and what
the engine said on stderr, which is everything a row needs to explain itself. What it
does not have is the shape: the reader is a parameter, which is the hole RG66 closed for
the client and left open here. Neither has a production caller yet, so nothing has had
to choose.

The shape of the answer is what to decide, not which file wins. `applyWrite` already
returns applied, refused or unreadable for a write, and a read has the same three plus
nothing. Whether that means `call` grows the state, `attemptRead` grows the table, or
the two become one function is open — what is not open is that a screen should not have
to know which door it came in by.

### §RG100 Absent, or never looked for

`filingOf` asks three listings in turn — the roadmap, the ledger, the store — and
answers `unfiled` when none holds the id. That last answer is a strong claim, and
`whereFiled` spells it out: *nothing in this project carries that id*.

RG67 made it possible for that to be false. A project declaring `[reads] list` answers a
listing past the bound with its counts and no lines, so every one of the three lookups
comes back empty and the id is reported as one nobody ever filed. The worst version is
the one this function exists for: a paused line, in a store that was bounded, described
to a person as never having existed.

Four states are three too few. What is missing is *not known* — the listing was narrower
than its file, so this read cannot say. `Filing` carries `open`, `shipped`, `paused` and
`unfiled`, and the fifth is what a bounded or partly refused listing actually supports.
`Backlog.complete` and `Store.complete` already carry the bit; nothing between them and
this function passes it on.

The same doubt applies to a listing with refused lines, which is the older and quieter
case: a line the grammar could not read is in `uncounted` and not in `tasks`, so an id
sitting in one has always come back `unfiled`. Whatever `filingOf` grows should cover
both, since they are one question — *did this read see the whole file?*

### §RG101 The interpreter that could stay

Measured while shipping RG68: an engine call against this repository costs about 1.5
seconds, almost all of it Python starting. The live suite makes roughly six hundred of
them and spends 415 seconds doing so, and the app will pay the same for every read a
screen makes that RG7's cache does not already hold.

`commands` publishes 91 verbs and one of them is `mcp` — a process that starts once and
answers over stdio, which is how the agent in this session reads these files. Both
transports here spawn instead: the process one by design, and the HTTP one by running
the process one behind a handler, so the seam it proves buys no speed. A third transport
speaking to a long-lived `roadkeep mcp` would make a call cost what an in-process call
costs.

Three things make this worth care rather than worth doing straight away. The tool names
are the MCP surface's, not the CLI's, and `commands` reports 23 verbs that run and are
not published there — so this transport answers fewer verbs than the other two, which is
the question RG6's capability report already knows how to ask. A long-lived process is
state this app would own and have to restart. And `fileParallelism: false` exists
because twenty interpreters starve eight cores; one process removes that reason and may
replace it with different contention.

Not a fourth answer either: whichever verbs it serves, the client above it must not be
able to tell which transport replied.

### §RG104 A teardown that reds a green file

Forty-one live files ran and one reported failure: `rows-live.test.ts`, whose five tests
all passed and whose `afterAll` threw `EPERM` removing the temp directory its fixture
built. The next run of the same file was green, and nothing in it had changed.

`dispose` is `rmSync(root, { recursive: true, force: true })`, and `force` forgives a
path that is not there — not one Windows will not let go of yet. A directory the engine
had as its cwd, or one an indexer opened a moment ago, is still held when the last test
returns, and a removal that would have worked a second later throws instead.

Two things are wrong here and only one is the lock. `rmSync` takes `maxRetries` and
`retryDelay` for exactly this — Node documents them as the answer to EBUSY, ENOTEMPTY
and EPERM on Windows — and neither is passed. And a teardown failure is reported as a
test failure, so a file that proved everything it set out to prove reads as broken. That
is the shape RG75 removed from this suite one commit ago, arriving again as a directory
that stopped being removable rather than an id that stopped being true.

Swallowing the error is not the fix: temp directories nothing removes are a leak nobody
sees. Retrying is.

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

### §RG102 The reads either side of the walk

RG71 made the walk asynchronous and stopped there, because the walk was what the line
named. What surrounds it did not move, and it runs over the same paths: `rootExists`
stats every root a person declared, `git-worktree` stats and reads `.git` for every
project the walk found, and `governed-stamp` stats each of five governed files per
project to key the cache. Seventeen projects is around ninety stats, every one of them
synchronous, in the process every IPC call from the window goes through.

So the symptom RG71 was filed for survives it. A sleeping external drive still freezes
the app; the walk simply is not where it happens any more. That is worth saying plainly
rather than counting the line as half done — the fix moved a stall rather than removing
one, and the remaining half is larger in calls than the half that shipped.

The shape is the same three times over and it is the shape RG71 left behind:
`node:fs/promises` in place of `node:fs`, and `createLimiter` where a set of paths is
read together. `withPresence` and `rowsFrom` become async with it, which reaches further
into `catalogue` than the scan did.

What is worth deciding rather than assuming is whether these want one bound between them
or three. Ninety stats against one disk under three separate widths is three answers to
a question that has one.

## Block C — The portfolio (many backlogs in one view)

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

### §RG93 A path into somebody else's package

RG57's dev loop has to run `tsc -b`. Reaching it through `npx` would put PATH and a
shell in the middle of a rebuild, so it spawns the compiler with this process's own Node
instead — which means naming the file.

That file is not nameable through the package. TypeScript 7's `exports` publishes
`./package.json`, `.` as a version module and the unstable API, and nothing else: asking
for `typescript/bin/tsc` throws `ERR_PACKAGE_PATH_NOT_EXPORTED` at load, which is how
this was found — the dev run died before opening a window. So the path is assembled from
the directory `typescript/package.json` resolves in, plus `lib/tsc.js`, which is where
that version happens to keep it.

It works and it is unowned. A TypeScript upgrade that renames or relocates that file
breaks `npm run dev` and nothing says so until somebody runs it — the exact shape RG55
was about, one layer down: an assertion held by a person remembering.

The fix is a line of test. Resolve the same path the dev loop resolves and assert the
file is there, so an upgrade fails a suite rather than a morning. Better still, run it
with `--version` and check the exit code, which also proves the launcher still starts.

Neither is worth a task on its own — it belongs to whichever task next touches the dev
run, or to a sweep of the places this repository reaches into a dependency's layout.

### §RG94 The half of the linter that reads types

RG58's design named four kinds of defect: an unused import, a wrong hook dependency
list, a second spelling of a name, and **a floating promise**. Three are held. The
fourth is not, and this says so rather than letting the ship read as though it were.

`no-floating-promises` cannot be decided from syntax — it needs to know that an
expression is a `Promise`, which means the type checker. oxlint puts that behind
`oxlint-tsgolint`, a peer package built on TypeScript-Go: the same engine TypeScript 7
is, which is why it works here at all where `typescript-eslint` does not.

It matters more in this codebase than in most. The transport is asynchronous everywhere,
the dev loop builds in the background, the watcher fans out to listeners, and `void` is
used deliberately in several places to say *this promise is not awaited on purpose*. A
rule that reads types is what tells those apart from the ones that are a mistake — and
an unawaited engine call is a read whose failure lands nowhere, which is the defect
class hardest to see in a review.

The work is installing the peer, turning on the type-aware category, and then reading
the findings honestly: some of the `void`s will be right and some will not, and a sweep
that silences the rule to make the run green would leave this worse than not having it.

### §RG95 Advisories nobody is told about

Nothing in this repository reads a security advisory. `npm ci` does not audit,
roadkeep's gate is about governed files, and the suite has no opinion. So the one
advisory this project knows about was found by somebody installing a linter for an
unrelated task — which is the shape of finding this block exists to stop.

That advisory is [[RG61]]'s and this line is not about it. This is about the next one: a
dependency added six months from now that arrives with something known, and nobody
hears.

The likely shape is `npm audit --audit-level=high` as a CI step. What makes it a task
rather than a line of YAML is the exception, because an advisory with no published fix
is the ordinary case and a gate that cannot be satisfied is a gate somebody adds a flag
to silence. So the exception has to be a list somebody wrote deliberately — an advisory
id, why it does not reach this executable, and the date that was established — and a
*third* advisory has to be what breaks the build.

The alternative is Dependabot, which this repository already configures and which
reports without gating. That is worth reading before building anything: if its alerts
are seen, the gate adds a fail and not a discovery, and the exception list is the only
part actually missing.

### §RG96 A test whose subject is on disk

RG60 put a test in the suite that starts the built app. Everything else in there
compiles from source through Vitest, so `npm test` has always been a statement about the
working tree. This one is a statement about `packages/ui/dist` and
`packages/shell/dist`, which are whatever the last build left.

CI is fine: the workflow builds before it tests, deliberately. A developer is not. `npm
test` after editing a renderer file runs the new unit tests against the new source and
the RG60 questions against the old bundle, and reports one number for both. The failure
mode is the bad one — a green run that is partly about code nobody is looking at.

Three shapes, none obviously right. Make `npm test` depend on a build, which costs every
run a build and makes the fast inner loop slower. Have the test build what it needs,
which puts a build inside a test and makes one test cost what a build costs. Or have it
*notice*: compare the bundle's timestamp against the newest source file and fail with a
sentence naming `npm run build`, which is cheap and turns a false green into an
instruction.

The third is probably it. A test that refuses to run against a stale subject is honest
in a way that a test which silently rebuilds is not, and it costs a `stat`.

### §RG115 What happens when a setting does not stick

RG47 built the recovery carefully: a settings file that is not JSON, one from a future
build, a pool width typed as a word — each takes the default, and each composes a
sentence saying what was lost and why. `wasReset` exists to ask whether any of them
fired. `LaunchSettings` carries the list across the bridge with the settings themselves.
Nothing in `ui` or `shell` reads either. Grep for `wasReset` outside a test and there is
one definition and no caller.

So the careful half is done and the visible half is missing, which is the worst of the
three states: somebody whose roots were dropped finds out by opening the app and
noticing the list is short, and the sentence that would have told them was composed and
thrown away.

RG87 added the mirror of this and left it the same way. A ground the person chose is
written back through the bridge, and the write is fire-and-forget: a rejection is
swallowed in `keepGround` because there is nowhere to put it. A choice that was not kept
looks kept until the next launch.

Both want one surface and neither should invent it separately — which is why this is an
idea and not a design. What it should be is bounded by two things already here: the
design system ships a `Toaster`, and page chrome is RG63's. A notice belongs in
whichever of those two arrives first, and the answer to *which* is the design still to
write.

### §RG118 The build the window is, said on screen

Block G's own criterion is that a user can say which build they are running and where it
came from, and every part of the answer is already in hand. `readStamp` composes it in
the main process, `identify` carries it across the bridge beside the transport name, and
a live test asserts the field is there. Nothing renders it. So the criterion is unmet by
a screen and not by a mechanism.

It matters most in the case it was written for. A person reporting that a read came back
wrong has a version, a commit and a signed-or-not to quote, and without a surface they
quote none of them — which is when the report becomes a conversation about which build
they have rather than about the defect.

RG63 gave it a home and left it empty. The bento layer's own answer is `AppFooter` — a
hairline, then the product name, its version and a few links — and its guidance is
explicit that the choice is the shell's: either every page carries the footer or the
chrome has none, and what must not happen is one page growing its own. That is the
decision to make here, and the alternative worth weighing is the header's trailing edge,
where `BentoUserMenu` would have gone and where `docs/design/Main.dc.html` draws a
version.

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

### §RG120 The surfaces that drift, and the gate that would not let them

`roadkeep lint` reports `install.stale` against `.claude/skills/roadkeep/SKILL.md` and
`.claude/skills/roadkeep/writing.md` on every run, and has for long enough that the
sentence reads as part of a clean answer. It is not: it says a session is reading a
skill older than the engine that will answer it, which is the same defect RG92 fixed one
layer out — instructions that are not what is actually running.

The fix has two halves and only the second is work. `roadkeep install` rewrites the
copied surfaces from the checkout it runs from, which closes today's drift. `roadkeep
install --check` writes nothing and exits non-zero on anything that would change; the
CLI's own help calls it the gate for a CI job or a pre-commit hook. Adding it to the
`gate` job is the half that stops the drift coming back.

Two things to settle while doing it. The gate job runs `alegauss/roadkeep@main`, so the
engine it checks against moves without this repository changing — which is already true
of the gate and is a cost this project accepted deliberately, but it means this check
can go red on a day nobody edited a skill. And the refresh belongs in its own commit: it
rewrites files this repository ships, and a diff of copied bytes should not ride along
with something a reader is meant to review.

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

### §RG90 A token pair that fails before anything uses it

RG54's contrast test computes every pair this app renders. It also found one it does
not: `--vg-muted-foreground` on `--vg-muted` is 4.33:1 in light, under the 4.5:1 AA
needs for body text. In dark the same pair is comfortable, so it is a light-ground
defect only.

The pair is not enforced, and deliberately: nothing on any screen puts those two
together today, and a test defending a number nobody renders is a number somebody will
eventually weaken to make an unrelated change land. What is on screen is muted text on a
card, which clears in both grounds and is enforced.

But the tokens are *named* as a pair — what the shadcn convention means by `x` and
`x-foreground` — so the first muted panel anybody builds reaches for both, and the label
is too pale in exactly the way nobody notices in review. `docs/design/Fundos.dc.html`
draws it on both grounds.

**The fix goes upstream, not into this app's `:root`.** The pair is the package's, and
Turing, Shio and Dumont render the same 4.33: an override here leaves three consoles
with the defect and this one out of step with them.

**`--vg-muted-foreground` becomes `oklch(0.52 0 0)`** — 5.05:1 on the muted surface and
5.51:1 on the ground. Break-even is 0.547, so this buys margin rather than sitting on
the line. Dark is untouched, the package re-pointing that token there already.

What is left here is adopting the release that carries it, and enforcing the pair.

### §RG105 The colour that says where you are

`bento.css` draws the rail's active item from `--primary`, and says why: a shared
component picking that colour itself is "the clearest case of a shared component making
one product look wrong". Turing is blue and Shio is orange because each keyed the token.
This app keyed `--vg-accent-from`, `-to` and `-text` to amber and left `--vg-primary` at
the package's neutral, so the mark for where you are is grey — drawn that way on purpose
in `docs/design/Shell.dc.html`.

The token is not the rail's alone. `bg-primary` is the default `Button` fill, the
progress bar and the slider track, and `bento.css` reads it again for the tile's hover
glow, the inline-edit border, the new-tile hover and the focus ring. Keying it moves all
of them together, which is the point rather than the cost: those are the places a
product is supposed to look like itself.

One value per ground, because the fill and its foreground swap roles: `#b45309` under
white on light, `#fbbf24` under near-black on dark. Both are the accent this app already
declares, and both were measured rather than judged — 5.02:1 and about 11:1, past AA.
The button gives up contrast it had, near-black on white being about 17:1, and that is
the trade this makes knowingly.

RG54's contrast test is where the two pairs are asserted, so a value that moves is
caught by a run rather than by somebody looking at it.

### §RG106 Mounting when the bridge does not answer

RG86 moved the first render behind one bridge call, and that was the right trade against
a window that repaints every sentence a frame after it opens. What it did not buy is a
bound: `localeFromBridge` resolves on an answer and on a rejection, and a promise that
does neither is a promise React never hears about. Electron shows the window on
`ready-to-show`, which fires on the first paint of an empty page, so the failure is a
window sized and titled and holding nothing.

Nothing observed this. It is reachable, though, and the shape of it is known: a handler
that throws before replying rejects, but a main process wedged in a synchronous read
never settles the channel at all, and `loadSettings` reads a file.

**A deadline, not a retry.** The base catalogue is complete and English is a correct
window, so the answer when the shell is slow is to mount in English — the same answer
already given for no bridge and for a refusal. What the deadline is worth arguing about
is its length: long enough that an ordinary IPC round trip never loses the locale, short
enough that nobody watches an empty frame.

**It belongs to the ask and not to the caller.** Every later reader of `settings()`
wants the same bound, so it is the reader in `ui/src/locale.ts` that carries it, not
`main.tsx`.

### §RG107 The override that reached both grounds

RG54 overrode `--vg-ring` in this app's `:root` because the package's light ring is a
grey that does not clear 3:1. The comment beside it says the package already makes the
ring the accent in dark, so this is that decision applied to the ground where it was
left a grey.

It does not hold. `index.css` imports the package and then declares `:root`, so this
app's block is the last one in the sheet. The package re-points `--vg-ring` under
`.dark, [data-theme="dark"]`, and that selector and `:root` are unlayered and equally
specific -- so the later declaration wins and the light value applies in dark as well.

What renders in dark is `#b45309` on `#171717`: 3.57:1. What was meant to render is the
package's own dark ring, `#fbbf24`, at about 10.7:1. Nothing failed, because WCAG 1.4.11
asks a focus indicator for 3:1 and 3.57 clears it. The ring is legal, and it is not the
ring anybody chose.

The contrast test does not see it because it models the cascade the other way: `LIGHT`
is the package's `:root` then this app's, and `DARK` is that map re-pointed by the
package's dark block. That is the order a reader expects and the opposite of the one a
browser applies.

So there are two defects here and the second is the one that matters: a value, and a
guard that agrees with the intent rather than with the sheet. Any token this app
overrides that the package re-points in dark has the same shape.

### §RG116 The language has a setting, a source and no switch

RG86 made `Settings.locale` reach every screen and RG88 made i18next the one place the
tag lives, so the reading half is finished. Nothing writes it. A person who wants
Portuguese opens `settings.json`, types a tag and restarts, which is the state the
ground was in before RG87.

Three of the four pieces are already here, which is why this is worth stating rather
than discovering later. `changeLanguage` moves both catalogues at once and a screen
follows it — `speaking.test.tsx` holds that. The write back has a shape to copy:
`saveTheme` on the bridge, validated in the main process against `core`'s own set, the
file re-read so no other field is lost. And the control itself is the design system's:
it ships `LanguageSelect` and `LanguageSwitcher`, so building one here would be the
duplicate [[RG39]] exists to refuse.

What is undecided is the fourth. `saveTheme` was deliberately one field, and its own
note says widening the bridge to a settings patch is a decision for whoever needs the
second write — this is that caller. A second narrow method keeps the surface honest and
starts a list; a patch method hands the renderer the roots as well. Neither is obviously
right, and the answer wants to be given once rather than twice.

Where the control sits is [[RG63]]'s, since there is no chrome to put it in yet.

### §RG117 One route table, read three ways

RG63 left the routes written out in three files. `main.tsx` mounts them, `harness.tsx`
mounts them again so a test renders the same window, and `Shell.test.tsx` keeps a
`ROUTES` set to check that every nav entry points at one this app serves. Only the first
is what runs, and the third is the one that decides whether the check passes — so a
surface added to the router and forgotten in the set makes the guard weaker without
failing anything, and one added to the set alone makes it pass against a screen nobody
wrote.

Harmless while there is one route, which is why it is filed rather than fixed inside the
task that made it: with a single entry all three agree by inspection, and building the
mechanism before the second surface is the shape of speculative work.

The shape is a `routes.tsx` beside `areas.ts`, exporting the pairs — a path and the
element that answers it — as data. `main` maps it into `Route`s, the harness maps the
same array, and the test reads the paths off it rather than restating them. `.tsx`
because an element is JSX; that is the whole reason it cannot live in `areas.ts` as it
stands.

What it should not become is a route the map does not know about. The two lists are
different questions — what the router serves, and what a reader is offered — and the
check is that the second is a subset of the first.
