# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

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

**A cache and never the truth about a backlog**: the repository stays the store, and an
entry is invalidated by the files it came off. At launch the carrier retakes each stamp,
six stats and no interpreter, and a `readings()` bridge call answers only entries whose
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

Held on RG251's terms: invalidated by the files and the engine, and never a source for a
write.

Rewritten in this commit: the "in memory only" comments of `gate.ts` and `carrier.ts`.

Tests: `gate.test.ts` seeding a ledger; `carrier.test.ts` asserting no `lint` at open
for a seeded root whose stamp and engine match, and one for a root whose stamp moved.

### §RG256 The verdict on a row opens the gate

**The gate cell is the one cell on a row that counts something and leads nowhere.**
`GateCell` in `Portfolio.tsx` draws the verdict pill and "6 findings" as text. The row's
only link is the project name (RG148), and the screen it opens draws no verdict (RG255),
so a reader holding a count has no path that names it.

**The pill and the count become one link to `gatePath(row.path)`**, which stays the
gate's address whether it remains a screen or becomes RG255's tab. Its accessible name
carries the project, since every drifted row reads the same words: a
`portfolio.gate.open` key, "Open the gate for {name}: {count} findings", with its `.one`
form. It is offered on a read row whatever the verdict, since an unknown one opens on a
run, which is what the gate does with nothing held. A pending or unreadable row has
nothing to open into and keeps text, by the rule its name already follows.

**The filter chip is not the door.** "Gate drifted 3" narrows the list, which is what a
chip in that strip does, and making it lead to several gates would give one control two
meanings.

Tests: `portfolio.test.tsx`, under RG152's gate column: a read row's verdict links to
its gate, and pending and unreadable rows draw no link.

On ship: --recorded-in packages/ui/src/Portfolio.tsx

### §RG257 A verdict word the window uses elsewhere

**`divergente` is `portfolio.gate.drifted` in `pt-br.ts`**, and the filter chip reads
"Verificação divergente {count}". Nothing past the row uses the word: the column is
"Verificação", the count is "achados", the gate screen is "A verificação" and its rows
are "achados". In a window whose rows carry worktree and branch badges (RG199), a thing
that diverged reads as a branch, and the reader who reported this took six findings for
six items that had diverged.

**The Portuguese verdict becomes `reprovada`**, and the chip "Verificação reprovada
{count}". `reprovar` is already this catalogue's verb for what the gate does, since
`gate.notes` is "Dito sem reprovar por isso", so the pill, the chip and the gate screen
share one family of words, and "reprovada · 6 achados" says a check failed and how much
it found.

**English keeps `drifted`**, the word `docs/design/Main.dc.html` draws and `gate.ts` is
written around. There the column and the screen already share "gate", so the pill sits
under the name of the check it reports.

Tests: none new. `wording.test.ts` and `locales.test.ts` hold both catalogues' keys, and
`portfolio.test.tsx` reads the base language. The check is `npm run shots` in pt-BR,
reading the portfolio row and the chip.

## Block D — The project surface (one backlog, read)

### §RG255 The gate as a tab of the project

**The project screen reaches the gate through a button and says nothing of it.**
`Project.tsx` offers Run the gate in the hero and draws a tab per governed file (RG149).
`docs/design/Projeto.dc.html` draws the verdict beside that button, "gate clean · 4 min
ago", and the build dropped it. A reader who saw six findings on the row looks along the
tabs, and a verb reads as a run to start rather than as the place the findings are.

**The gate becomes the last tab**, labelled with the portfolio column's word and the
count the ledger holds, heard on the gate topic the way a row hears it (RG166), in the
error intent while drifted. Its panel is what `Gate.tsx` draws today: the held verdict,
the counted read, findings and notes apart. Run the gate moves from the hero to above
the report.

**`GATE_ROUTE` stays the gate's address** and renders the project with that tab chosen,
so a link from a portfolio row and the screenshot run keep one path. Entering or leaving
the gate tab replaces the address rather than pushing one, so Back leaves the project
instead of stepping through tabs.

**The tablist's name widens** from the governed files to the project: the gate is what
those files say of themselves, not one of them.

Tests: `project.test.tsx` for the tab's count off `gates` and the route opening on it;
`gate.test.tsx` re-pointed at the tab.

On ship: --recorded-in packages/ui/src/Project.tsx

## Block E — The write path (the app composes an argv; the command writes)

### §RG254 A drifted verdict opens on its rows

**RG185 opens the gate on the verdict the ledger holds**, and runs only where that
verdict is unknown or stale (`worthRunning` in `Gate.tsx`). For a clean verdict that is
the whole answer. For a drifted one it is a count and a date, "6 findings when it last
ran", with no row, no code and no door: the rows arrive only when a person presses Run
the gate again.

**A drifted verdict runs as the screen opens.** RG185's own rule is to run where a run
says something new, and the rows are exactly what the ledger never held. A clean, fresh
verdict still opens without a run. The held sentence stays drawn while `lint` runs, so
the count does not vanish for the seconds the rows take.

**Holding the report in the carrier was weighed and refused.** Its doors are one batch
per root (RG181), so any later read that carries doors replaces them, and a held row
would offer doors that name nothing. RG253 also plans to write the ledger to disk, and a
held report would grow what that file carries from a count to every message the gate
wrote.

Tests: `gate.test.tsx`, where RG185's opening case splits in two: a held clean verdict
runs nothing, and a held drifted one runs once and draws its rows.

On ship: --recorded-in packages/ui/src/useGate.ts

### §RG258 What a finding's code means, asked of explain

**A finding row draws its code as a pill and the gate's message beside it** (`Finding`
in `Gate.tsx`). The message is about one line. What the class is, why `ref.unresolved`
exists and whether it means different things in different places, is what `explain
<code>` answers. `readExplanation` in `refusals.ts` reads that into `cause` and
`varies`, a live contract test holds it, and nothing draws it.

**The code becomes a disclosure.** Opening it runs `explain` through the read table for
that code, once per code per screen, so a report of six findings over three codes costs
at most three reads, and only for the codes a person opened. What comes back is drawn in
the engine's words, untranslated, as every payload's prose is.

**Its doors are not drawn.** The finding's own remedy already draws them, filled in for
this line, while `explain`'s doors are the class's, with `…` wherever the finding has a
value.

**A build that cannot run it offers nothing.** `capabilities.ts` answers
`byVerb.explain.callable`, and where that is false the code stays a pill: a disclosure
that opens on a refusal is a control that lies.

Tests: `gate.test.tsx`: opening a code reads `explain` once and draws its cause, a
second finding with the same code reads nothing, and no disclosure is drawn where the
capability is off.

On ship: --recorded-in packages/ui/src/Gate.tsx

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
