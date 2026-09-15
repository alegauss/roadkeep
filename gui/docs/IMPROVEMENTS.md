# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

### §RG244 Checking the edited files against the disk

**What moved is read off the files**, the rule `Session.tsx` already keeps for the
backlog, so each edited path is asked of the disk. A bridge method `editedAt(key,
paths)` answers per path: whether it resolves inside the session's root, whether it is
there, and when the disk last changed it. Named by the session's key and not by a root,
so main takes the root from its own record and a page cannot aim a stat at a folder it
chose.

**A path outside the root is named and never touched.** An agent can write a memory file
or a sibling checkout; its row says it is outside this project, and the shell stats
nothing there. Resolution is `governedAt`'s, the one inside test this shell already has.

**When the session started.** `SessionRecord` gains `started`, the ISO time main spawned
the process. A row then says when the disk changed the file, or that the disk has not
changed it since the session started although a call reported success, which is the
disagreement a reader opened the section to find. Times go through `useWhen` (RG177).

**Asked again as the list grows and when the session ends**, and never on a timer:
nothing is watched that the stream did not name.

**The shell shortens a path under the root** to the root-relative form with forward
slashes, and the screen draws what it answered.

Tests: `edited-at.test.ts` with a stat stub (inside, outside, missing),
`sessions.test.ts` for `started`, and the section's three states in `session.test.tsx`.

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
