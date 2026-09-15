# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

### §RG248 Rows kept across a catalogue change

**The rows on screen survive a fold.** `usePortfolio` answers a `catalogue` event by
bumping `generation`, and the rerun's `read()` sets `projects.map(pendingRow)` over what
was drawn, though the comment above the rescan branch says the rows stay. A launch that
remembers its list and whose walk moved anything, one project cloned since, watches
every row go back to a skeleton and fill again.

**Merged by path, in the new list's order.** A pure `keepRows(previous, projects)` in
`portfolio.ts`: a project already on screen keeps its payload fields, with its recorded
ones (branch, declared, presence) taken from the new `RecordedProject`; a new project is
pending; one no longer listed is dropped. `coldStart` takes those rows as an optional
start instead of always beginning from `pendingRow`, and each read that lands replaces
in place through `fillRow`, so one that fails leaves the row as RG167 already does.

**Progress still says the reads are under way**, so a kept row is not claimed to be
current while the rerun is in flight.

Tests: `portfolio.test.ts` over `keepRows` (kept, added, dropped, order);
`portfolio.test.tsx` firing a catalogue event after a read and asserting no row returns
to pending.

### §RG249 A deadline on the launch path

**The limit is written and never applied.** `limits.ts` declares
`DEFAULT_LIMITS.timeoutMs` at fifteen seconds and `withLimits` clamps a person's
setting, but `createCarrier` opens with `openHere(root, { width })` and `usePortfolio`
calls `rowStages(reach)` with no `CallOptions`. Resolution, `commands`, `stats` and the
gate's `lint` spawn with no ceiling; only the held `mcp` calls stop, at sixty. A
launcher waiting on a network drive or a lock keeps its row pending for as long as it
waits.

**The stages turn one hang into every row's.** `coldStart` awaits every project's
`counting` before any `next` starts, which is its staging rule and stays: the shape of
the screen before its detail. So the deadline is the fix, not a reorder.

**Two applications.** The carrier passes `withLimits(settings).timeoutMs` to `openHere`,
which already hands it to the held transport, and to the gate's run; `usePortfolio`
passes the same number to `rowStages`, crossing with the settings `launch.ts` already
reads. A read that runs out becomes `unreadable` with reason `timeout`, the state
`limits.ts` describes, and the next stage goes on without it.

Tests: `cold-start.test.ts` with one project whose stage never resolves under a fake
deadline, asserting every other row reaches `next`; `carrier.test.ts` asserting the
deadline reaches `open` and the gate.

### §RG250 One ceiling across projects

**What a launch spends, off the code.** Opening one project resolves its engine (an
interpreter per candidate, 2.3 s for a second one by `engine-candidates.ts`), holds a
`roadkeep mcp`, and spawns `commands` and `stats`, which the held surface does not
publish. `coldStart` hands every project to a stage with `Promise.all`; the only ceiling
is each project's own pool of `width`, so twenty projects are eighty slots. Only the
gate is bounded across projects (RG187).

**A limiter over projects, not calls.** `coldStart` takes an optional `projectsAtOnce`
and runs each stage's projects through `createLimiter`, the one RG187 uses, so the bound
is on projects in flight and a project's pool still decides its calls. Projects start in
the order the screen draws them, so the rows a person sees first fill first.

**The number is the machine's.** The default is one project per four cores, never fewer
than one, which is RG130's rule for the live suite; the shell has the core count, so it
crosses to the renderer with the settings, and a `projectsAtOnce` setting overrides it,
clamped in `limits.ts` beside `width`.

Criterion "A cold start over twenty projects is bounded and says what it is doing" is
what this finishes: the progress line keeps counting stages, never slots.

Tests: `cold-start.test.ts` with a fake stage recording how many projects are in flight,
never above the limit, rows still in record order; `limits.test.ts` for the clamp.

### §RG251 Remembered readings, drawn at launch

**What is kept is what a verb printed, never a row.** A `readings.json` beside
`catalogue.json` holds, per root key, the `stats` and `pick` payloads, the `engines`
payload the opening resolved, the governed files `config` named, and the stamp
`stampGoverned` took when they were read. Rows are rebuilt by `readRow`, so every number
is still one a verb printed. A versioned `readingsFrom` in `core` refuses a shape this
build does not know, as `catalogueFrom` does; `readings-file.ts` in `shell` writes by
rename. The carrier fills it off the `stats` and `pick` answers passing through `run`,
as `noting` dates the gate (RG152).

**`No store of its own` bounds this and does not forbid it**: its reason says a cache
mirrors files and is invalidated by them. At launch the carrier retakes each stamp, six
stats and no interpreter, and a `readings()` bridge call answers only entries whose
stamp still matches. Nothing writes, claims or offers a door off an entry; those need an
opening.

**A remembered row says so.** A `RowState` `remembered` draws counts and next line with
the engine that printed them, which criterion "Which copy of roadkeep answered is on
screen" asks, and a quiet mark instead of a skeleton. The cold start runs behind it and
replaces it in place, which RG248 makes possible.

Rewritten in this commit: the "nothing persists" paragraphs of `cache.ts` and
`catalogue.ts`.

Tests: `readings.test.ts`, `readings-file.test.ts`, `portfolio.test.tsx` drawing
remembered rows.

### §RG252 Checking a remembered row instead of reading it

**Checked behind the screen, under RG250's ceiling.** Once RG251's rows draw, a
background pass takes each remembered project in the order the screen draws them and
asks a carrier `check(root)` over the bridge. The carrier runs `resolveEngine` alone,
the one read that names which copy would answer, and compares its `engines` payload
(version, home, revision, invoke) and a fresh stamp with the entry's.

**Both equal: the row stands** and turns `read`. No `roadkeep mcp` starts, and no
`config`, `commands`, `stats` or `pick` runs. **Either differs: the row is read in
full** through the opening as today, replaced in place by `fillRow`, and the entry
rewritten. `No engine the reader cannot name` is why the engine is asked and not
assumed: an upgrade while the app was closed changes answers without moving a file.

**The opening becomes lazy** for a row that stood. The carrier opens it on the first
thing that needs one: the project screen, a write, a door, the palette's `list`, a
watched change. `follow` watches the governed files the entry names, so a checkout
edited later still rereads (RG167) with no engine held since launch.

**Rescan reads everything.** The button skips the check, so a person who distrusts the
record has one action that ignores it.

Tests: a core `check` over stands, stamp moved and engine moved with a fake resolver;
`carrier.test.ts` asserting no opening for a row that stood until `open` is called.

### §RG253 Gate verdicts that survive a restart

**`gate.ts` refuses this for a reason that no longer holds.** Its ledger comment says a
saved verdict "would still match nothing it could check", but the stamp is
`mtimeMs:size` of `roadkeep.toml` and the governed files, retaken after a restart in six
stats. What a stamp cannot see is the engine, and RG252 already asks that.

**Kept in the readings file, beside the payloads**: the `GateRecord` as `recordGate`
wrote it (verdict, problems, taken, stamp) and the `engines` payload of the engine that
ran `lint`. At launch the carrier seeds its ledger from entries whose stamp still
matches, and RG252's check drops a seeded verdict whose engine differs, so `gateIfStale`
finds nothing stale and runs no `lint` for a project nobody touched. An entry that does
not match is dropped, never seeded as stale: a verdict about another tree or another
engine is not an old verdict about this one.

**The row stays honest as `gate.ts` makes it**: `taken` dates the verdict, and a file
that moves makes it stale and reruns the gate (RG166).

`No store of its own` bounds this on RG251's terms: invalidated by the files and the
engine, and never a source for a write.

Rewritten in this commit: the "in memory only" comments of `gate.ts` and `carrier.ts`.

Tests: `gate.test.ts` seeding a ledger; `carrier.test.ts` asserting no `lint` at open
for a seeded root whose stamp and engine match, and one for a root whose stamp moved.

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

### §RG245 Viewing an edited file

**A row opens the file as the disk holds it now**, in the design system's `Sheet`, over
the session so the stream keeps running beside it. Nothing routes, and closing it
forgets the text.

**Read by the side with the disk.** A bridge method `fileText(key, path)` resolves under
the session's root as RG244 does, and refuses a path outside it, a file that is not
there, one above a byte ceiling named in `limits.ts` and stated in the refusal, and one
that is not text, judged by a NUL in its first block. Each refusal is a code with a
sentence in both catalogues, never an error's English (RG168).

**Drawn as the file stores it**: the text face, line numbers, the file's own wrapping
kept, nothing interpreted. A Markdown file is its characters, which is `No Markdown
parsed in this app`. No highlighting either: a grammar per language is a second parser,
and the question here is what changed, not how the code reads.

**Current, never remembered.** Read when the sheet opens, again from a reload button,
and again on each new act that edits the same path while it is open. Kept nowhere after
it closes, which is `No store of its own`.

Tests: `file-text.test.ts` over each refusal with a fake disk; `session.test.tsx`
opening a row, a refusal's sentence, and a reread when the stream edits the open file.

### §RG246 What the session changed inside a file

**The before comes from the session, never from git.** `No git command run by this app`
refuses `git diff`, and `No store of its own` refuses a copy of the file taken at
handover. What is left is enough: an `Edit` carries `old_string` and `new_string`, a
`MultiEdit` a list of those pairs, and a `Write` the whole content. A reader in
`acts.ts`, `editsOf(acts, path)`, returns them in stream order, each with the result
that answered it.

**Drawn in the viewer, above the file.** Each edit is two blocks in the text face, what
it replaced and what it put there, with its seq leading to the act in the stream and a
failed pill where its result failed. A `Write` is one block, the text it wrote. A block
past a line count folds and opens where it stands.

**Checked against the file, not believed.** Each `new_string` is looked for in the text
RG245 read. Found, the edit is in the file; absent, it is not in the file now, whether a
later edit overwrote it, something reverted it or it never applied. A plain substring
test over two strings the screen already holds: nothing is parsed and nothing is diffed.

**The input is Claude Code's schema.** A call whose input lacks those keys draws no
block and keeps its raw line, the fallback `subjectOf` already takes.

Tests: `acts.test.ts` for each tool's shape and a malformed input; `session.test.tsx`
for an edit found, one gone, and one whose call failed.

### §RG247 Files changed on disk while a session ran

**What the stream cannot name.** A session that runs `sed`, a formatter, a generator or
`npm run format` through Bash changes files no edit call names, so RG243's list misses
them, and asking git which files moved is `No git command run by this app`.

**Watched while it runs.** From spawn to outcome, the shell watches the session's root
recursively and keeps, on the session record, each root-relative path that moved with
the first and last time it did. Paths and times only, never contents: this run's
filesystem events, gone with the process, and no mirror of a file. The walk's `skip`
names from the settings are skipped, `.git` always, and a burst is held the way
`governed-watch.ts` holds one.

**The policy is core's, the handle the shell's**, split as `watching.ts` and
`governed-watch.ts` are: which moves count, how a burst folds and the path ceiling, past
which a count stands in for the rest, all tested with a fake watcher and clock.

**Said as unattributed.** The section lists the moved paths RG243 did not already name,
under a caption saying they changed on disk while the session ran. An editor saving a
file in that time counts too, and the caption does not pretend otherwise. Each row opens
in RG245's viewer.

**Recursive `fs.watch`** holds on Windows and macOS, and on Linux from the Node this
repo requires.

Tests: the fold in `core` with fakes, and a live test writing into a temporary root.

## Block G — The shell (an executable now, a service later)

### §RG49 The signature, and what it needs that code cannot supply

Signing is not work that can be finished by writing anything: it needs a certificate
somebody bought, held somewhere a build can reach. So the line states the requirement
and is set aside for a caller that says it has one, rather than coming back as the next
ready task forever. What can be built without it is the pipeline that would use it, and
the about surface saying plainly that this build is unsigned — which is the honest half
and is worth having on its own.

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
