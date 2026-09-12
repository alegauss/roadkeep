# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

### §RG199 Which branch this member is on

`git-worktree.ts` already reads git's own files to find a common directory, and
`families.ts` is explicit that nothing here runs git. The branch arrives the same way:
`HEAD` in the worktree's git directory is one line, either `ref: refs/heads/2026.3` or a
bare sha. No spawn, no library, no second reading of a format this app does not own.

**The declared name is what makes this necessary rather than pleasant.** Today the
folder name separates the members of a family by accident: `2026.3` and `2026.2` are
different words. A declared name is one word for a whole repository — the same
`roadkeep.toml` reached by three paths — so every worktree of Turing renders as
**Turing**, identical rows under a badge that says only _worktree_. The name solves one
problem by making another, and the branch is what answers the second.

So the branch goes where that badge is. `portfolio.worktree` states what two rows
sharing a name already imply; the branch says which of them this is, which is the
question actually being asked.

**A detached HEAD is not an error.** It is a bisect, a tag checkout, a shallow clone,
and the row shows the short sha rather than going blank. A folder that is not a git
checkout has no branch and shows none — which is not the same as a checkout whose `HEAD`
would not read, and the two do not share a rendering.

### §RG200 The chip is already drawn

The chip is already drawn: `size-8`, `rounded-[10px]`, tinted by `toneOf(row.name)`,
holding `IconFolder` at seventeen pixels. Every row holds the same glyph, so the chip
carries one bit — _this is a folder_ — that was never in doubt. The tone varies, but a
hash over a name is not something a person learns to read.

**The declared emoji goes in that slot and nothing else about the cell moves.** The
tinted square stays, because it is what gives the emoji an edge and a consistent
footprint against both themes; the emoji replaces the glyph inside it. No new layout, no
new size, no second element to align.

Three things this has to get right. It is **presentational**, so the `aria-hidden` on
the chip stays: an emoji announced before the project's name is noise, and the name is
already there for anyone reading by ear. It is rendered as **text and never parsed** —
no grapheme splitting, no codepoint arithmetic, no attempt to decide whether a ZWJ
sequence counts as one emoji. And a project declaring nothing keeps `IconFolder`, which
is what makes this safe to ship before a single repository has adopted the key.

Whether the tint should still come from the name once an emoji sits on it is a question
for the screen. Keeping it costs nothing and a flat chip loses its edge, so the tint
stays until something argues otherwise.

### §RG201 What a row is for, not where it is

A row's second line is `row.path` in mono, truncated, with the full path in `title`.
Seventeen rows of that is seventeen paths, and a path answers _where_ when the question
a portfolio screen is open to answer is _which_. Nothing on the row says what the
project is for.

**The declared description takes that line and the path keeps the tooltip it already
has.** Not a third line: the cell is one row of a table beside counts, a next line, a
gate and an engine, and a row that grows by a line for some projects and not others
makes the table ragged. The path is not lost — `title={row.path}` is there today and
stays, which is where a path belongs once something better can be shown in its place.

**One line, truncated, never wrapped.** The limit is the engine's, declared in
`[limits]` and reported by `budget`, so the refusal happens where the description is
written rather than where it is drawn. This app does not enforce it; it draws what it
was given and lets CSS cut the overflow. A screen that silently shortens prose is a
screen that disagrees with the file it is reading.

Where nothing is declared the path stays on the line, which is what it does today. The
change is visible only on projects that opted in, and a mixed portfolio is readable in
both states.

### §RG203 A missing project keeps its name

A declared name is read out of the checkout that declares it. A missing project is one
the rescan did not find, so nothing can be read from it — and a row built the obvious
way falls back to the folder name at exactly the moment the project disappears. The row
changes its identity as it goes grey, which is the worst possible moment for it: _last
seen on Tuesday_ about a name nobody recognises is not the sentence this was built to
say.

**The catalogue records the last name it saw.** That is not a second copy of roadkeep's
data — the bound this file states is against caching a backlog, and the record already
holds `aliases`, `commonDir` and `confirmed` for the same reason. They are facts about a
machine's folders that have to survive the folder being unreachable, and a name last
seen is the same kind of fact. `confirmed` already dates it.

`CATALOGUE_VERSION` goes to 2. `catalogueFrom` refuses a version this build does not
know and answers null, which is a rebuild behind a screen rather than an error, so the
bump costs one scan on the first launch after an upgrade. The reader takes the new
fields as optional with an empty default, so nothing about the refusal path changes.

A returning project takes whatever it now declares, including nothing: the record is a
memory, never an override.

### §RG204 A picture from a repository this app does not own

An emoji is recognisable and it is not a logo. Where a project declares `project.logo`
the row should draw the file — and that file lives in an arbitrary repository on this
machine, which is what makes this its own line rather than a clause in the icon's.

**The renderer never gets a path.** A `file://` URL from the portfolio into an Electron
renderer widens what the window can read to whatever a path can reach, and the path was
written by a repository rather than by this app. The shell resolves it against the
project root, refuses anything that climbs out, reads the bytes, checks they are an
image it agreed to draw, and hands back a data URL over the transport that already
exists. The renderer receives a picture or it receives nothing.

**A size ceiling, enforced on the bytes and not on a declaration.** A logo here is a
list-row icon at thirty-two pixels; a repository pointing at a four-megabyte PNG should
get the emoji and a note on the row, not a portfolio that stalls on seventeen reads.

Every failure — missing file, wrong type, too large, outside the root — falls back to
`project.icon`, and that to `IconFolder`. The chain is why the emoji stays worth
declaring even where a logo exists, and it means a broken logo is a cosmetic outcome
rather than an empty cell.

## Block D — The project surface (one backlog, read)

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
