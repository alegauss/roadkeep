# Improvements

## Block A — The client (payloads in, types out)

### §RG9 Getting a person's words in unchanged

Prose fields go in on stdin wherever the verb offers it: the why, a section body and
restate's symptom all read a dash. The add verb's symptom does not, which is filed
upstream, and until that lands this app composes that one field as argv and says so
rather than pretending it is safe. Spawning without a shell removes the quoting layer
but not the encoding one. What proves it is a round trip: write a symptom carrying an
accent, an apostrophe and an em dash, read it back with show, and compare the bytes.

### §RG135 The fallback that forgets why it fell back

RG122 made a failed handshake a fall-through: an engine too old to have `mcp`, one whose
interpreter cannot start, or one caught mid-save answers nothing at `initialize`, the
root goes into `unheldable`, and every read after it spawns. That was the right call for
the app — slow beats broken — and it is silent in both directions that matter.

**A screen cannot say why a project is slow.** Seven hundred milliseconds a read against
six is the whole reason the held engine exists, and a project that fell back pays the
first number forever with nothing to show that it is the exception. The engine's version
is already on screen from resolution; that this project's engine refused the held
surface, and what it said, is not.

**And a test cannot say it either.** The live gate went red on `mcp-live` with `expected
1 to be +0`: a `list` that should have been answered held was spawned. Alone the file is
23 of 23. Roadkeep's checkout was being edited during the run — a commit three minutes
before it, seven engine modules modified — and a server started mid-save does not
import. That took a `git log` in another repository to learn, because the one place that
knew threw the reason away.

So the transport keeps it: one reason per root it could not hold, readable beside
`held`. The counting test then fails naming the handshake, and an open project can carry
the sentence to a row.

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
so by failing to find what the exception excused.

### §RG133 The icon that arrives over the network

RG124's check found what it was built to find, and it was not the flag CDN. The built
renderer names `api.iconify.design`, `api.simplesvg.com` and `api.unisvg.com` —
Iconify's default resource list, shipped inside `@iconify/react`, which the bento layer
imports.

Nothing fetches today, and the reason is a prop. `BentoNavRail` and the tiles render
`<Icon icon={…}>` when a caller gives an item an `icon` string and a bundled
`@tabler/icons-react` component when it does not. `AREAS` is empty, so no name has ever
been passed. The first screen in blocks C to F that writes `icon: 'mdi:folder'` on a nav
item turns three hosts the packaged policy refuses into a request per icon, and what it
draws instead is nothing at all.

That makes this worse than the flag it was found beside. `LanguageSelect` is a component
somebody has to adopt deliberately; this is one string on a data structure this app
already owns, in a file whose other fields are ordinary.

Two answers and they compose. **Say it where the array is**: `areas.ts` is where an
`icon` would be typed, and its own doc is what the next person reads. **And hold it**:
the icon a bento item carries can be a tabler component rather than a name, so a test
over `AREAS` asserting no item names a string is a check on this repository's own data
rather than on somebody's bundle — cheap, fast, and it fails on the line being written
rather than after a build.

### §RG136 A mark only the drawings have

`Main.dc.html` and `Shell.dc.html` open the header with a 28px amber square — a folder
glyph on the amber gradient — and then the wordmark, 30px apart. The window renders the
wordmark alone: `<span class="font-brand">roadkeep</span>`, and nothing before it.

RG127 redrew the header control for control and held it with `data-control`, and
deliberately left the mark alone: the line named controls and regions, and the mark is
neither. So the check is green over a header whose first 58 pixels are drawn and not
rendered, which is the class of gap RG127 was about, one step to the left.

It is a decision and not a defect, and it has two honest answers. **The mark is the
direction.** `Main` is the direction RG63 adopted, the rows below use the same glyph and
gradient for every project, and the app would carry it too — a small component, and the
header's first element. **Or the mark was the canvas's.** Nothing in the design system
ships one, a desktop app has its own icon in the title bar and the taskbar, and the
drawing drops it to measure like the window.

What should not survive is the third state, the one now: drawn in one place and absent
in the other, with nothing saying which is the intent. Whichever lands, the artboard's
header gains a `data-region="brand"` and the check grows a line, so the next divergence
at that end is a red run and not a person measuring.
