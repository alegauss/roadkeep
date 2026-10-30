# roadkeep — Design rationale

> Rationale for **unshipped** sections only. Status markers live in
> [ROADMAP.md](ROADMAP.md); shipped work is described in
> [CHANGELOG.md](CHANGELOG.md) and `git log`. When a section ships, delete it here.

## §0 — Why this exists

### §0.1 The measured problem

Three files in the Viglet Shio repository declare a format and none enforces it:

| Artefact | Rule | Reading |
|---|---|---|
| `docs/ROADMAP.md` | one sentence per task | 92 active lines, **142 words** average, worst **1406 characters** (7× the best) |
| `agents.md` | index only, resident every turn | grew to **186 KB (~46k tokens)** before it was split |
| `docs/IMPROVEMENTS.md` | rationale for *unshipped* work | accreted shipped implementation reports; the sibling project's reached **539 KB** |

The pattern is identical in all three: an author with the whole design in working
memory writes it where the reader will be, and the reader is a file that gets loaded
every turn. Shio measured this in SH341 and found **six of the eight worst lines were
written in the session that then diagnosed the problem** — so this is a drift the
process invites, not a lapse of attention. An instruction to be terse does not survive
the moment its author knows more than the line allows.

### §0.2 Why the fix is a write path, not a linter

A linter reports after the prose exists, and by then the cost is already paid: the
tokens were spent generating it, and the author is being asked to delete work. A field
with `maxLength: 200` refuses at the point of insertion, before a sentence is composed
to fill it. Same rule, two orders of magnitude cheaper — and it converts an analytical
act ("is this line too long, and what would I cut?") into a procedural one ("call
`add`"). **The saving is the analysis, not the characters.**

### §0.3 The six laws

| # | Law |
|---|---|
| L1 | **The format is a schema, enforced where the text is created** — `add` refuses; `lint` is the backstop for what bypassed it. |
| L2 | **The store is the repository** — Markdown, greppable, diffable, no database and no service. |
| L3 | **Round-trip or don't write** — parse → render → byte-identical, or the tool may not own the file. |
| L4 | **The tool never writes prose** — it validates and renders. A generator would reintroduce the drift. |
| L5 | **Query instead of read** — every question a maintainer asks the file is a command, so answering it costs no context. |
| L6 | **Configuration, not convention** — prefix, paths, markers and limits are declared per project. |

L5 is the one that pays for the rest. `pick` replaces loading 558 lines to find one
task; `stats` replaces a grep whose misses are silent; `show` replaces joining two
files by hand. Those three are most of what an agent currently spends a roadmap
session doing.

### §0.4 The limits, measured against a live corpus

§0.1 asked whether the limits are right or the lines are. Shio's 78 active lines answer
it, and the answer is split in a way that only a real backlog could have produced — the
reading RK20 took:

| Field | Limit | p50 | p90 | max | Over |
|---|---|---|---|---|---|
| `symptom` | 120 | 58 | 86 | 111 | **0 of 78** |
| `why` | 200 | 481 | 900 | 1251 | **70 of 78** |

The same authors, in the same lines, met one limit every single time and missed the
other 89% of the time. So 89% is not evidence that 200 is too small — `symptom` is the
control, and it shows compliance is available. The difference is that "what does not
work" is one clause by construction and a `why` has no natural end, which is L1 stated
as a measurement: the field whose scope is unbounded is the one that needs the bound at
the write path.

And the migration is smaller than that task assumed. **74 of the 78 pointers resolve,
and none dangle**; 67 of the 70 over-length lines point at a section that already exists
and makes the same argument — compared line-against-section on SH295 and SH309, the
`why` is a recompression of the paragraph, same examples and all. The rationale is not
homeless. The line is a second copy of it, so the edit is compression against a text
already written, not authorship.

## Block A — The model

### §RK1716 Deps on a sibling project

A dep on another repository's task can only be written as free text, for example
`viglet-design-system: VDS213` or `claude-tray: T389`. RK28 resolves such a dep as
unresolvable, which is honest, but it means `deps`, `pick` and `blocked` can never tell
whether VDS213 shipped. The alegauss product sites were filed this way in October 2026,
each task waiting on viglet-design-system Block H and on the claude-tray pilot, and no
command in any of those repositories can say which tasks are unblocked.

Every repository involved is governed by roadkeep, so the answer exists on disk: the
other project's CHANGELOG either holds the id with the shipped marker or does not.

The change: `roadkeep.toml` declares sibling projects by name and path, for example
`[projects] viglet-design-system = "../../viglet/viglet-design-system/latest"`. A dep
written `<name>: <id>` or `<name>: <id>–<id>` then resolves by reading that project's
config and ledger, read-only. An undeclared name stays free text, as today. A declared
path that is missing is reported as unresolvable with the path, never counted as
shipped.

Done when a dep on a declared project's shipped id lets `pick` offer the task, an
unshipped one keeps it blocked with the foreign id named, and nothing is written outside
this repository.

## Block B — Authoring

### §RK1715 A label already taken under another title

`block add` checks each governed file for the label, writes the heading where it is
missing, and reports the files that already declare it as skipped. It does not compare
the title. Seen in viglet-design-system: `docs/CHANGELOG.md` had `## Block G — The
package knows one chrome` (VDS146, VDS147 shipped), and

    roadkeep block add G --title "Sites that take the look without a build"

wrote the new heading into ROADMAP, IMPROVEMENTS and DEFERRED, printed `not
docs/CHANGELOG.md: already declares it`, and exited 0. One label then had two titles
across the files. The next `ship` into G would have filed new work under a block that
the ledger says is about something else. The heading was reverted by hand and the work
refiled as Block H.

The skip is right when the title matches: that is RK1223's case, a block in the ledger
that the roadmap has not opened yet. It is wrong when the title differs, because the
label is already taken.

The change: before writing anything, read every governed file's heading for the label.
If any of them carries a different title, refuse the whole call, name the file and its
title, and suggest the next free label. A matching title keeps today's behaviour.

Done when the call above exits non-zero with no file written, the refusal names
`docs/CHANGELOG.md` and the title it holds, and a label declared with the same title in
the ledger alone still opens in the roadmap.

### §RK1718 A defer refusal that hides the reason's room

Found in quickshell on 2026-10-23, deferring QS373. A 147-character reason was refused
with `line.too-long`: "the rendered line is 456 characters ... no field is over the
budget this line left it, so what does not fit is the structure around them". The door
it named was `budget --symptom <draft> --why <draft>`. A 66-character reason was then
refused the same way at 348. Only `budget --id QS373 --defer` gave the number that
mattered, `reason_room: 37`, because a deferred line carries the open line's why and
wraps the reason inside it.

So the refusal blames "the structure" when the field being written is the reason, and
its door goes to a read that does not price that field.

What to build: when `defer` (and `retire`, which wraps a reason the same way) is refused
for line length, the message names the reason as the field that has to shrink, says how
many characters it may take, which is the same `reason_room` that `budget --defer`
already computes, and the door is `budget --id <id> --defer`.

## Block C — Query

## Block D — The gate

## Block E — Adoption

### §RK1720 Every version reaches PyPI without a dispatch

The last release on PyPI and on GitHub is v0.2.0, of 28/08/2026. The plugin, which
carries the package inside it, is at 0.2.532: the pre-commit hook bumps the patch on
every commit, and `publish.yml` only runs when someone dispatches it. So `uvx roadkeep`,
`pip install roadkeep` and the Action pinned in the README at `alegauss/roadkeep@v0.2.0`
all hand an adopter the August tool, while the README describes the October one. The
portfolio review of 30/10/2026 (visibility repo, `estrategia/portfolio.md` and
`produtos/roadkeep.md`) found this is the first thing a Show HN commenter would hit; the
author confirmed the release stopped only for lack of a habit, so the fix is to remove
the habit from the path.

The design:

- **No dispatch to remember.** A trigger publishes from `main` without a person: on a schedule (weekly, skipped when nothing changed since the last tag), or on each push whose `__version__` differs from the newest tag. The second matches "every plugin version" literally but means one PyPI release per commit; the weekly cadence is the proposal, and the choice is the author's.
- **The guards stay.** The same `build` job (gate, tests, wheel probe) runs first; only the trigger changes.
- **A moving `v0` tag** follows each release, and the README pins the Action to `@v0`, so the snippet never goes stale again.
- **The desktop installers** keep their own cadence if building them per release is too heavy.

## Block F — The plugin

### §RK1719 Um lock de processo morto

A linha RK1719 entrou no roadmap no commit 85b0ad60 sem a seção para onde aponta; esta
seção só registra o que a própria linha já diz, para o lint voltar a passar, e o desenho
fica para quem pegar a tarefa.

O sintoma: o lock que serializa as escritas guarda o pid de quem o tomou. Se esse
processo morre sem soltá-lo, toda escrita seguinte espera 5 segundos e recusa, sem
conferir se o pid ainda existe, e a recusa chegava truncada como "refused, nothing
written", sem dizer que o motivo era o lock nem como sair dele. O caminho hoje é apagar
o arquivo à mão.

O que a tarefa precisa decidir: conferir se o pid gravado ainda vive (no Windows e no
POSIX) e tomar o lock de um processo morto, dizendo isso na saída; e, quando o dono
estiver vivo, a recusa nomear o lock, o pid e há quanto tempo ele o segura, por inteiro.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)

### §RK1717 The README's first screen, held to the visibility test

The README is the PyPI page and the first page a Claude Code user opens, and the
visibility repository (`D:\Git\alegauss\visibility`) judges every alegauss product's
first screen by one test, set in its `drafts/VS4-primeira-tela.md` for claude-tray:
someone who never heard of the tool knows **what it does**, **why install it** and **how
to install it** without scrolling.

The rewrite of 2026-10-22 (75a2c90e, 0db5ee0f) moved the install and a first session to
the top and the design argument below, but it was not measured against that test. What
is left to decide:

- The one sentence. Is it what a Claude Code user searches for, or the tool's own vocabulary?
- A demo. claude-tray gained a GIF (VS5); here the moment is the hook denying an `Edit` on
  the roadmap and naming the `add` to call.
- What returns from the old README. The comparison with markdownlint, Vale and Backlog.md
  left with no page in the docs to hold it.
- The visibility strategy keeps roadkeep to cheap actions tied to claude-tray, so this stays
  one pass, not a launch.

Done when the first screen passes the test as visibility states it, and the row for
roadkeep in visibility's `actions.json` records the change, so its effect on PyPI
downloads and repository visitors is measured.

## Block J — Validation (whether a person ever tried it)

## Block K — The desktop app (one installer for the reader and the plugin)

## Block L — Product sites on the package

### §RK1714 Both sites on the package

The pitch (`site/`) and the roadkeep-gui landing (`gui/site/`, built here by
`build:gui`) each keep a copy of the product sites' template. `site/src` carries
`components/Nav.tsx`, `Footer.tsx`, `sections/Hero.tsx`, `ui/Ad.tsx` and `ui/Rich.tsx`;
`gui/site/src` carries those plus `sections/FeatureIndex.tsx`, `sections/NonGoals.tsx`,
`pages/Feature.tsx`, `ui/CopyButton.tsx` and `ui/ThemeToggle.tsx`. Both prerender with
`scripts/prerender.mjs`, and `gui/site` draws its card with `scripts/og-image.mjs`. The
tokens are hand-written in each `src/index.css` (541 and 1645 lines).

Neither `package.json` has Tailwind, which VDS214 assumes all eight sites have. The
first step is a choice: add Tailwind v4 and the package's preset, or style the `./site`
components from `site.css` (VDS216) with no new build dependency.

The move: `data-tone="cool"` on both, because both grounds are slate-blue (`#0a0f1b`
dark, `#f7f8fb` light). The accent comes from `projects.json`: roadkeep-gui's
`245,158,11` / `#fbbf24` is its amber, but roadkeep is listed as slate `148,163,184` /
`#cbd5e1` while the pitch is amber, so one of the two changes, decided here. Shared
components come from `./site`; `Terminal`, `Mark`, `CopyLine`, `HeroWindow` and the
pitch's sections stay local. Both builds call the `./vite` helpers. Google Analytics
loads only after consent, as the hub's AG1. The pitch stays dark-only. The Starlight
area in `site/docs` is out of scope. The pilot is claude-tray T389.

Done when `site/src` and `gui/site/src` have none of the files `./site` provides; the
prerendered HTML of every route holds the same text as before; screenshots of each route
(dark for the pitch, light and dark for gui) are compared before and after, with the
differences listed in the commit; both sites appear in `consumers.json`.
