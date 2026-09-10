# Improvements

## Block A — The client (payloads in, types out)

### §RG9 Getting a person's words in unchanged

Prose fields go in on stdin wherever the verb offers it: the why, a section body and
restate's symptom all read a dash. The add verb's symptom does not, which is filed
upstream, and until that lands this app composes that one field as argv and says so
rather than pretending it is safe. Spawning without a shell removes the quoting layer
but not the encoding one. What proves it is a round trip: write a symptom carrying an
accent, an apostrophe and an em dash, read it back with show, and compare the bytes.

### §RG122 The held engine, and who closes it

RG101 built the transport and measured it: eight reads of this repository cost 5904ms
spawned and 45ms held, which is 738ms against 6ms. It is held by `mcp-live.test.ts` over
every read verb and by nothing else. `openProject` still builds `createPooledTransport`
over the process one, so every screen to come pays the spawn.

What stands in the way is not the reading, which is done. It is that a held process is
state this app owns, and three things follow that nobody has settled.

**Who closes it.** `OpenProject` has `invalidate` and no `close`; a window that opened
seventeen projects would hold seventeen engines, and closing that window has to end
them. On Windows that means killing the tree — the launcher spawns rather than `execv`s
— which RG101 records and which the app would now be doing at shutdown.

**Whether the pool still makes sense.** `createPooledTransport` bounds calls in flight
because twenty interpreters starve eight cores. One process per project is a different
shape, and the width that was right for spawning may be wrong or unnecessary here.

**And whether the live suite's `fileParallelism: false` can go**, which exists for the
same reason and is most of why that suite takes ten minutes.

Measure before and after rather than assuming: one process serialises what twenty did in
parallel, and the win above is per call and not per suite.

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

### §RG121 The rule that is off in more places than it needs to be

RG94 turned `typescript/no-unsafe-type-assertion` off across the project, for a real
reason: `reading.ts` checks a value and then asserts the type it just proved, every
payload shape in `payloads.ts` is read through it, and a run made green by suppressing
fifty deliberate assertions would have said less than no rule at all.

The reason does not reach every file the switch does. Among those fifty were three of a
different kind — `session.ts` and two tests asserting *from `any`*, which the rule
reports with its own sentence and which no validator argument covers: an `any` has been
proved nothing about. Those are exactly the ones worth seeing, and today nothing shows
them.

The shape is an `overrides` entry rather than a project-wide switch. The reader files
are a short, nameable list — `reading.ts`, `payloads.ts`, and whichever of `acts.ts`,
`capabilities.ts`, `settings.ts`, `cold-start.ts`, `opening.ts` and `session.ts` turn
out to be reading rather than converting — and the rule stays on everywhere else. Which
is which is the work: each of the fifty has to be read once, and a file that lands on
the exempt list because it was easier is the outcome this is trying to avoid.

Worth doing while the findings are cheap to reproduce: `oxlint --type-aware` with the
rule back on prints the whole list in a second.

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

### §RG123 The strings the pseudo-locale run cannot see

RG115 put the settings notices on screen and left two holes of the same shape.

**The sentences are not translatable.** `readSettings` composes one per field it reset —
*the pool width was not a whole number, so it is back to 4* — in `core`, as prose rather
than as a `MessageKey`. RG115 shows them under a translated frame, so a window in
Portuguese says the frame in Portuguese and the detail in English. Each carries an
interpolated value, which is why they are not four more keys and are instead a small
shape: a code and its fields, resolved through the catalogue the way `THEME_TEXT`
resolves a marker.

**And the run that holds this cannot see them.** RG51's pseudo-locale test renders the
window under a locale where every catalogue value is bracketed and fails on anything
unwrapped — but it reads `container`, and a toast renders in a portal outside it. So
does a dialog, and the shortcuts sheet is already one. A literal typed into any of them
is invisible to the one test that exists to find literals.

The second is the one to fix first: it is a line of scope in a test that already works,
and it is what would have caught the first. `document.body` rather than `container`,
with the portalled surfaces opened — which means the run has to open them, and that is
the work.

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
