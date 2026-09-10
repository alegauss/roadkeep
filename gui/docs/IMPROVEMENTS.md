# Improvements

## Block A — The client (payloads in, types out)

### §RG9 Getting a person's words in unchanged

Prose fields go in on stdin wherever the verb offers it: the why, a section body and
restate's symptom all read a dash. The add verb's symptom does not, which is filed
upstream, and until that lands this app composes that one field as argv and says so
rather than pretending it is safe. Spawning without a shell removes the quoting layer
but not the encoding one. What proves it is a round trip: write a symptom carrying an
accent, an apostrophe and an em dash, read it back with show, and compare the bytes.

### §RG130 The suite that spawns, and why holding the app's engine did not help it

The live gate takes 436 seconds for 43 files, one at a time. `fileParallelism: false`
was bought by a real failure: half of these build a fixture with a dozen engine calls
and then read it with several more, so running them together puts twenty-odd
interpreters on eight cores, and the reads that lose that race fail for being starved
rather than for being wrong.

RG122 held the engine for the app's own open path and did not touch this. Two files call
`openHere`; the other forty-one read through `live.ts`'s transport, which spawns per
call, and build their fixtures with the same one. Every interpreter the setting exists
for is still started.

What would move it is the suite reading the way the app now does. `live.ts` already
publishes one shared transport and one door, `read`, that most files go through — a held
engine behind those two would answer `list` in six milliseconds instead of seven
hundred, with no test changing.

Two things stand in the way. The fixture builder writes — `init`, `add`, `ship` — and
that surface withholds writes on purpose, so building stays a spawn. And a held engine
per fixture root is a process to give back per file, which nothing here owns: `dispose`
removes a directory, and Windows will not remove one a server stands in.

Measure the suite either side rather than assuming. The win RG122 measured is per call,
and most of this may be the fixture builds.</section_body> </invoke>

### §RG131 The signal the held transport does not read

`EngineRequest` carries a `signal` because a screen redrawing while reads are in flight
is the ordinary case, and two of the three transports honour it. The pool checks it
after the wait, so a call cancelled while queued never becomes a process. The process
transport listens for `abort` and kills the child it started. The held transport does
neither: `send` writes a frame, sets a timer and waits, and a cancellation reaches
nothing.

Since RG122 that is the transport every read goes through, so the app's own open path is
the one that cannot cancel.

What it costs is worth naming rather than guessing at. A held read is about six
milliseconds, so the work a cancelled call finishes is six milliseconds of one server's
time — not an interpreter start, and not a screen anybody waits on. What is left over is
the frame: the reply arrives, `deliver` finds no waiter, and it is dropped, which is
what a timed-out call already does.

So this is a consistency defect before it is a performance one. A caller passing a
signal is told nothing about which transport it landed on, and a portfolio read that
cancels seventeen projects still pays all seventeen — small, but the number a person
predicts from reading `transport.ts` is zero.

The protocol has `notifications/cancelled`. Whether this build's server acts on it is
the first thing to measure, and refusing the promise locally is the floor if it does
not.</section_body> </invoke>

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

The launcher resolves an engine in four steps -- `ROADKEEP_HOME`, a vendored
`.roadkeep/`, the sibling `../roadkeep`, then a clone under the user cache -- and takes
the first that *answers a probe*. Answering is the test, so a checkout being written
while the probe runs is a checkout that does not answer, and resolution falls through.

It happened during RG120. Three commands in a row were served by `0.2.4` out of
`~/.cache/roadkeep-src` while the sibling stood at `0.2.450` and imported in half a
second; a minute later the same command resolved the sibling again. What made it loud
was luck: a copy that old does not know `[install] wired`, so it refused `roadkeep.toml`
and named itself. A cache one minor version behind would have answered, and the session
would have been briefed, linted and shipped by an engine nobody chose -- silently, since
the version is printed only when something goes wrong.

Setting `ROADKEEP_HOME` did not change it, which is the part worth understanding before
proposing a fix: the override is a candidate like the others and is dropped by the same
probe. So the choice is between making a *named* engine fatal rather than skippable, and
`install --vendor`, which copies a pinned engine into `.roadkeep/` and takes the
resolution order out of it. The first is the launcher's own behaviour and belongs
upstream; the second is this project's to decide, and it costs a copy in the tree.

Worth deciding before a second session shares this checkout.

### §RG129 A table that does not carry its own key type

`CALLED` is `{ ...VERBS, ...WRITES }` declared as `Record<string, (input: never) =>
readonly string[]>`, and `CalledName` is `VerbName | WriteName` written separately. The
two agree today because a person kept them agreeing. Nothing checks it, and the file has
to assert its own key type to publish `CALLED_NAMES` -- which is what keeps
`capabilities.ts` on RG121's exempt list while `wording.ts` and `opening.ts`, whose
tables carry their key types, came off it by calling `keysOf`.

Two smaller assertions in the same file have the same root. `flagsFor` widens a builder
to `(input: unknown) => readonly string[]` because the table's value type says `never`,
and `capabilitiesOf` starts its accumulator as an empty object asserted into a full
`Record<CalledName, Capability>`.

The shape is to declare the table by the type it is: `Record<CalledName, (input: never)
=> readonly string[]>`. Then `keysOf` answers `CalledName[]`, the widening in `flagsFor`
has a real type to narrow from, and a verb added to `VERBS` without a name in
`CalledName` is a compile error rather than a key that silently answers `string`. The
accumulator is separate and its own small choice -- `Object.fromEntries` over
`CALLED_NAMES`, or a `Map`.

Worth doing when something else touches this file: the win is a compile error nobody has
needed yet, and the risk is that `never` in the value position makes the spread refuse
to typecheck, which is the thing to find out first.

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

### §RG124 A control that reaches the network for a picture

`LanguageSelect` and the `BadgeLocale` inside it draw every row's flag as `<img
src="https://flagcdn.com/w40/br.png">`. That is a request per row to a host RG59's
policy refuses, so what a screen adopting one draws is the component's own fallback -- a
globe -- after a load that failed, and on a machine with no network it is the same
picture and a slower one.

Nothing is broken today: RG116 tried that control, found this, and took
`LanguageSwitcher` instead, which draws no image. What is missing is anything that would
tell the next person before they spend an afternoon on it. The vendored page reference
does not say which components fetch; the duplicate check reads exports and not hosts;
and the refusal lands in a console during a dev run served from a host the dev policy
allows, which is the one run where it may not appear at all.

Three answers, in the order they are worth trying. A note beside those components in the
bento reference is the cheap one, and RG110 already keeps that file current. A check is
the one that generalises: the renderer is a single bundle, and a test reading it for an
absolute `https://` inside an image source would catch any adopted component that
reaches out. The third is upstream -- a flag set shipped in the package, or a prop to
draw none -- which is the only fix that also helps Turing and Shio.

### §RG125 The other half of the wording has no completeness check

The wording is two halves and only one is held complete. `PT_BR` is a `Partial` of the
base and a test walks every key of `BASE` to find one nobody translated, which is what
makes adding a string safe. `AREA_WORDING` is the other half -- this app's strings that
the design system's own components resolve -- and it is two hand-written objects, `en`
and `pt`, that nothing compares.

RG88 created that half and left it empty, so the gap cost nothing. RG116 put a string in
it: the language menu names itself with `language.toggle`, in both languages, because
the package ships no `language` namespace and its fallback is an English sentence. A
second key added to `en` alone would draw English inside a Portuguese window, and the
guard that would otherwise catch it does not look here -- RG51's pseudo-locale run wraps
the bundle for the base locale, which is the language it renders in.

The answer has the shape of the one that already works: walk the keys of `en`, require
each in `pt`, and fail with the path of the one that is missing. Two details are worth
deciding rather than assuming: whether a value identical in both is an error, since an
endonym is the same word in either; and where the check goes, the catalogue's own being
in `core` while this object lives in `ui`.

### §RG126 The window above the routes is still written twice

RG117 made the routes one array and left the tree above them written twice. `main.tsx`
mounts `GroundProvider`, `WordingProvider` and a router; `harness.tsx` mounts the same
three so a test renders the same window. The harness's own note says why that matters --
it exists precisely so a piece added to the shell is not missing from half the suite --
and the stack it renders is the one thing it restates rather than reads.

The failure is quiet in the direction that matters. A provider added to `main` and
missed here fails nothing: every test renders a window slightly unlike the one that
ships, and the assertions keep passing against the smaller tree.

Two differences are deliberate and have to survive any fix. `main` wraps in `StrictMode`
and the harness does not, because a double mount is what the launch notices are guarded
against and a test asserting one toast would see two. And the routers differ:
`HashRouter` because a packaged build is loaded from `file://`, `MemoryRouter` because a
test has no location bar. So the shape is a component taking the router as its child --
everything common inside, the two differences passed in -- rather than a flag naming
which caller it is, which is the version that grows a second flag.

Worth doing when a third provider arrives, or sooner if one is ever missed.

### §RG127 The drawings are behind the chrome they drew

`docs/design/Main.dc.html` draws the header as a wordmark, the palette, a pill, `EN` and
a ground button. The window now draws a wordmark, the palette, a `?` button, a language
menu and a ground button, and carries a footer naming the build under every page. RG63
added the first of those, RG116 the second, RG118 the third; none of them redrew the
artboard.

That is the same class RG109 closed once and it will recur, because the drawings are the
input to work and the chrome is the output of it. It matters more than a stale picture
usually would: these files are what the next screen is designed against, so a person
laying out the project surface measures a header that has one control fewer than the one
their screen will open inside.

One correction is already known rather than guessed. The pill on that trailing edge is
`roadkeep 0.2.411` behind an amber dot -- the *engine*'s version and its agreement
state, which RG118's own design misread as the app's build and nearly put in the header
for that reason. A redraw should keep it and label it, because that chip is a real thing
this app will need and it is not this one.

The cheap fix is to redraw the two artboards that carry chrome, `Main` and `Shell`. The
question worth answering first is whether anything can hold them:
`viglet-ds-page-reference --check` keeps the vendored `vds-` pages current, and nothing
at all watches this repository's own.

### §RG132 The one word this app cannot translate

RG123 pointed the pseudo-locale run at the whole document with the shortcuts sheet and
the command palette open. It found one bare string: `Close`.

It is the dialog's close button, and the package writes it as `<span
class="sr-only">Close</span>` rather than resolving a key —
`vigDesignSystemTranslations` has no entry for it. So a window in Portuguese has a
control whose only name, and the only thing a screen reader says for it, is English. It
is small, and it is exactly the class of defect that run exists to find; what is unusual
is that this repository cannot fix it.

Three ways out, in the order they should be tried. **Ask the package** — the wording
lives there, `bento.shortcuts` and `common` are already full of strings, and one more
key is the whole change. **Or pass a label**, if the component takes one: RG124 is the
shape of that answer for the flags, where a prop turned out to be the door. **Or stop
using its dialog**, which costs a screen and should lose.

Until one of them lands, `wording.test.tsx` carries the word in a named set with the
reason on it, so the guard stays green about the one string it can do nothing about and
red about every other. That set is the thing to delete: when this is fixed, the run says
so by failing to find what the exception excused.</section_body> </invoke>
