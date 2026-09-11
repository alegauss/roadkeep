# Improvements

## Block A — The client (payloads in, types out)

### §RG188 The key an assignment swallows

`dictionaryOf` accumulates into a plain `{}` with `built[key] = parsed.value`. A source
key spelled `__proto__` does not become a property: the assignment reaches
`Object.prototype`'s own accessor, which rejects a non-object silently, and the reader
still answers `ok`. So the key is gone, the read says it succeeded, and nothing anywhere
reports it.

**The keys are the project's, not this app's.** `dictionaryOf` is used for `markers` on
the stats and on each block, and for `non_goals_quoted` and `non_goals_why`, which are
keyed by a project's own marker set and by the free prose of its non-goal leads. A
backlog may declare whatever markers it likes, so nothing stops one of them from being
that word.

**What a reader sees is a number that does not add up.** The marker chips are drawn from
`Object.entries(counts.markers)` beside the total the verb printed, so they stop summing
to it — the one thing every count on that screen is supposed to be. Worse where a lead
is read by key: `boundsFrom` takes `nonGoalsWhy[lead]`, which falls through to the
inherited accessor and survives a `?? ''` guard as an object, so a screen draws `[object
Object]`.

**The fix is the one the file already uses.** `tableOf`, two functions above, builds
with `Object.fromEntries` and has none of this. A null-prototype accumulator or
`fromEntries` is a line's change, and the assertion that holds it is a payload with that
key in it.

### §RG189 The refresh eviction punishes

The caching transport evicts by iteration order: the oldest key a `Map` holds goes
first. A hit keeps that honest — it deletes the key and sets it again, with a comment
saying why — and the path that writes a fresh answer does not. `entries.set(key, …)` on
a key already present updates the value in place and leaves the key where it was, which
is what `Map` guarantees and what the hit branch is written around.

**So a refresh is punished for being one.** A project whose files moved has its entries
re-run against the new stamp, and each keeps the position it had when first read — at
the front, where eviction takes them. What survives is what nobody has asked for since,
the opposite of least-recently-used and of what the comment above promises.

**It is silent, and it costs a spawn.** Nothing reports an eviction; the answer is
simply not there next time and the engine runs again. On the project being edited — the
one somebody is working in — the hottest entries are the ones thrown away.

**The fix is the line the hit branch already has.** Delete before setting, so a write
moves the key to the end whether it is the first for that key or the fifth. What holds
it is a test that fills the cache past its bound, refreshes an early key against a new
stamp, and asks which key the next insertion evicted.

## Block B — Discovery (which checkouts on this machine are governed)

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

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

### §RG190 The screen a handover moves after it is gone

Hand to Claude Code starts a session and then navigates to it. The call is a promise,
and nothing between the press and its answer checks that the person is still on the task
screen. Handing over takes as long as resolving an agent and starting a process, which
is long enough to press Back — and when the answer lands the window moves to the session
anyway.

**Every read on this screen already guards, and this one does not.** The effects around
it take a `live` flag and give it up in their cleanup, which is what the task screen was
built around; the handover is a callback rather than an effect, so it was written
without one and nobody noticed, the failure needing a person to leave a screen inside a
second.

**What it costs is a screen nobody asked for.** The session did start, and it is on the
sessions list — but a reader who went back to the project is taken somewhere they did
not choose, with nothing saying what moved them.

**A ref the screen clears is the whole of it.** The callback reads it before navigating
and does nothing where the screen has gone; the session it started is still listed and
still reachable. The state writes beside it are harmless — React drops them — so the
navigation is the one thing to hold, and a test that unmounts between the press and the
answer holds it.

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

### §RG191 The field a run has to reach to catch

The pseudo-locale run reads what is on the screen, so it catches an English sentence
only in a state the run puts the window into. RG168 fixed the unreadable row and added
the state that shows it — but a screen drawing `unreadable.message` again, or another
field this app wrote in English, passes every run that does not reach it. The window has
four surfaces and a dozen states each; the run reaches a handful.

**The fields are nameable, and that is what makes a guard possible.**
`Unreadable.message` is kept for a log and says so; `Opening.unresolved.reason` and
`Withheld.reason` are the same; each has a code beside it that a screen is meant to use
instead. A read of the renderer's sources for those field accesses is a guard that does
not depend on reaching a state: it fails on the line, not on the screen.

**A rule about a field, not about a string.** It says nothing about English prose in
general — `Refusal.said` and a finding's message are the engine's, and drawing them is
right. What it refuses is exactly the accessors whose own docstrings say a code should
be used instead, which is a list that grows with the codes and never with the screens.

**It belongs with the duplicates check, not in a test.** Both are one pass over the
sources for a shape nothing else can see, both name the replacement in the failure, and
both are cheap enough to run on every lint.
