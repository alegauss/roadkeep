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

A dep on another repository's task can only be written as free text, such as `turing:
T456`. RK28 resolves it as unresolvable, so `deps`, `pick` and `blocked` never tell
whether it shipped, and the user relays every Turing ship to Dumont's agent by hand. The
other project is governed by roadkeep too: its ledger holds the answer.

The change: `roadkeep.toml` declares sibling projects by path, git remote, or both; a
bare string is a path:

    [projects.turing]
    path = "D:/Git/viglet/turing/latest"
    git = "https://gitlab.com/viglet/turing.git"
    ref = "2026.3"

A dep written `<name>: <id>` or `<name>: <id>–<id>` then resolves by reading that
project's config and ledger, read-only. A `path` that exists wins: fast and offline.
Otherwise `git` is fetched shallow into a cache, two files at `ref` (the default branch
when omitted), so CI and other machines answer too. Git is the transport, not a host
API, so GitHub, GitLab or any git host works, private ones through git's own
credentials. A remote answers for what was pushed, never an uncommitted ship.

The fetch has a timeout and runs once per process. A missing path, failed fetch or
unknown id is unresolvable with the reason, never shipped. `lint` never fetches: a gate
must not depend on the network.

Done when a shipped id in a declared project lets `pick` offer the task through either
source, an unshipped one keeps it blocked naming the foreign id, an unreachable remote
answers unresolvable within the timeout, and nothing but the cache is written outside
this repository.

### §RK1723 Which project filed a line

A friction skill working in Dumont files into Turing with `roadkeep -C <turing> add`.
The line is identical to one Turing's own session filed, and the git author is the same
person either way, so neither the file nor `origin` tells them apart. Yet a line filed
from a consumer saw the symptom, not the product: it is a report to re-analyse, not a
design to execute. Today the user says so by hand.

The fact is observable at the write and nowhere else: when the process's directory
resolves to a governed project other than the target, `add` knows both. A flag the
caller must remember would make it a convention again (L1).

The change: `add` writes one derived continuation under the line when the two projects
differ, `filed **dumont**`, in the grammar `checked` and `validated` already use. The
name is the caller's declared project name, else its directory. No date and no person;
`origin` answers those. `ship` carries it into the ledger entry, so a site can show
which product asked. A read, `foreign`, lists open lines whose filer the home project
has not reviewed; like `unvalidated`, a report and never a gate. Confirming a line
rewrites the continuation to `filed **dumont** reviewed`.

Done when an `add -C` from a second governed project writes the continuation and one
from inside the target writes none, `foreign` lists the first until confirmed, and the
line round-trips through amend and ship.

### §RK1724 What a ship unblocks next door

RK1716 makes Dumont's `pick` resolve `turing: T456` by reading Turing's ledger, so
Dumont finds the unblock itself the next time it asks. That keeps each project the only
writer of its own files. The alternative, Turing's `ship` editing Dumont's roadmap,
would write into another repository's working tree, possibly under a parallel session
with uncommitted edits, and leave a change no commit there accounts for. It is rejected.

Two gaps remain. Turing's agent finishes T456 without knowing anyone waited on it, so it
cannot tell the user. And Dumont's agent learns only when it runs `pick`; a session that
starts on something else never hears it, which is why the user relays it by hand today.

The change: `ship` reads, read-only and through RK1716's path-or-remote resolution and
timeout, the roadmaps of the projects `[projects]` declares, and prints each open line
there whose dep it just satisfied, `unblocks dumont: D123`. In the dependent project,
the session-start brief names ready lines that have a foreign dep, as `D123 ready:
turing T456 shipped`. That is derived on every start rather than stored, so it needs no
state about what was seen before, and it is bounded like the brief's other lists.

Done when shipping T456 in a project that declares dumont prints D123, nothing outside
the repository is written, and a Dumont session start names D123 as ready through
turing: T456.

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

### §RK1722 Dates a build can take from the answer

`history` already resolves both moments of a task from git: the commit that added its id
to the roadmap (proposed) and the one that added it to the ledger (shipped). It does so
one id at a time, through `origin <id>`. A build that dates every entry cannot pay one
`git log -S` per id, so alegauss.github.io's `scripts/fetch-records.mjs` carries its own
`shipDates`, one `git log -p` over the ledger with its own id pattern. That is a second
reader of the format, and it breaks when the grammar changes.

The date stays derived. "No dates or quarters" forbids a schedule; a date stored in the
line would also cost characters everywhere, conflict on merges and repeat what git holds
(L2). Derived, it survives a rebase and covers every entry already shipped.

The change: `list --json` and `export --json` carry `proposed` and `shipped` per task,
each `{commit, date}`, from one `git log -p` pass per governed file. Without git or
history the fields are absent, so a caller can tell "never" from "cannot say". The site
reads a bare clone through `git archive`, so the payload must be answerable for a
revision of a repository.

Done when fetch-records.mjs can delete `shipDates` and read the same dates from
roadkeep's JSON, two runs at one commit give identical bytes, and a tree without git
answers with the fields absent rather than refusing.

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

### §RK1726 init offers everything the tool can set up

`init` writes `roadkeep.toml`, the roadmap, the ledger and the rationale file.
Everything else a working setup needs is a separate command run afterwards, found by
reading help: `--strategy` and `--deferred` are flags nobody is shown, `decisions` is a
role `init` cannot scaffold at all, and the plugin surfaces, the vendored engine, the
merge driver and the CI gate are `install`, `install --vendor`, `merge --register` and a
workflow written by hand. Stopping after `init` leaves no guard, no merge driver and no
gate, silently.

The change: `init` offers every role and every wiring step the tool has, and runs the
chosen ones in the same all-or-nothing transaction it already uses:

- the prose and line roles beyond the three: strategy, decisions, deferred;
- the plugin wiring: none (the plugin is installed), `install`, `install --committed`,
  or `install --vendor`;
- the merge driver, as `merge --register` writes it, with the `git config` line printed;
- the gate: the action workflow, the pre-commit hook, or neither.

Each option is the existing verb, called, never a second copy of what it writes.
Defaults stay minimal for a non-interactive call, so a script that runs `init` today
writes the same bytes. The report ends with what was not chosen and the command that
adds it later.

Done when one `init` with every option yields a tree on which `lint`, `install --check`
and `merge --check` all pass, and an `init` with none writes what it writes today.

### §RK1727 A prefix derived from the repository name

`init` without `--prefix` mints `RK`, this repository's own prefix. Every project
scaffolded without the flag gets roadkeep's ids: a Turing line and a roadkeep line both
read `RK12`, a commit subject naming one is ambiguous across the portfolio, and a
sibling dep (RK1716) spells `turing: RK12`, which reads as a roadkeep task. Renaming the
prefix after the first `add` is a `renumber` of every id.

`--existing` already reads the prefix off the ids a roadmap carries. An empty repository
has no ids, but it has a name.

The change: with no `--prefix` and no ids to read, `init` derives one from the
repository directory: the initials of its words split on `-`, `_`, `.` and case changes,
uppercased (`claude-tray` gives `CT`, `polyweave` gives `P`), lengthened by letters of
the first word to at least two characters (`PO`). The report prints the derived prefix
and the flag that overrides it, so the choice is visible before the first id exists. An
interactive `init` offers it as the default answer. `RK` is never a default anywhere but
in this repository's own `roadkeep.toml`.

Done when `init` in `D:/tmp/claude-tray` declares `CT`, the report names `--prefix` as
the override, and an explicit `--prefix` still wins.

### §RK1728 init asks, from one list of questions

Every choice `init` takes is a flag, so a person setting up a project reads the help,
guesses, and finds the rest after the first `lint`. Making `init` prompt is not enough
on its own: the usual caller is an agent, whose shell has no terminal to answer from,
and the desktop app (gui/) would need the same questions again. Three surfaces that each
list the options drift apart.

The change: the questions are data. `init --questions --json` prints each one with its
flag, its choices and its default, computed for this directory: prefix, blocks, optional
roles, plugin wiring, merge driver, gate. Three readers take that list:

- **A terminal.** `init` with no options and stdin a TTY asks each question, then prints
  the equivalent non-interactive command before running it, so the setup can be
  repeated. Without a TTY nothing is asked and today's behaviour holds.
- **The skill.** `SKILL.md` tells an agent setting up roadkeep to read the list, ask the
  user (AskUserQuestion) and call `init` with the flags. No question text lives there.
- **The desktop app**, through the same JSON.

The prompts use `input()` alone, keeping zero runtime deps, and are rendered from the
list, so a new option is one entry.

Done when `--questions --json` lists every `init` option, a TTY run and the printed
command produce byte-identical trees, a non-TTY run never blocks on input, and the skill
names no option the list does not carry.

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

### §RK1725 Filing into a sibling project

An agent in Dumont that meets a Turing defect files it in Turing. Each friction skill
(viglet-, polyweave-, winwright-friction) carries its own copy of how: which checkout,
which launcher, when to commit, how the consumer's line records the wait. The copies
live outside this repository, drift apart, and all need a local checkout, though RK1716
can already read a project from its git remote.

The mechanics belong to the plugin; a friction skill keeps only what to file and where.
The change: a reference beside `writing.md`, opened from `SKILL.md` when a write targets
a project `[projects]` declares (RK1437's cadence):

- A `path` that exists: `roadkeep -C <path> add`, committed there only if that tree
  holds nothing else.
- Otherwise the `git` remote: a shallow clone at `ref` into a temp directory, the same
  `add`, a commit on a branch named for the id and the filer, pushed, and a merge
  request through push options (GitLab) or `gh pr create` (GitHub). Never a push to
  `ref`: the review is the re-analysis RK1723 asks for.
- Either way, the caller's line takes the dep `<name>: <id>`.

roadkeep itself still never commits or pushes; the reference names the git commands. An
id minted from the remote can collide with an unpushed one there, and the request is
where `renumber` answers it.

Done when a friction skill files into Turing through this reference with no local
checkout, a merge request names the new id, and the consumer's line carries the dep.

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
