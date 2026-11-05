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
starts on something else never hears it.

The change: after `ship` has saved and released the write lock, it reads, through
RK1716's resolution, the roadmaps of the projects Turing's `[projects]` declares, and
prints each open line whose dep it just satisfied, `unblocks dumont: D123`. Never inside
the lock: a fetch there makes other writers refuse after 5s, and one slower than 60s
gets the lock reaped. So Turing must declare Dumont too. In Dumont, the session-start
brief names ready lines with a foreign dep, `D123 ready: turing T456 shipped`, from a
`path` or the cache only, never a fetch, since it runs on every start.

Done when shipping T456 in a project declaring dumont prints D123 after the lock is
released, nothing outside the repository is written, and a Dumont session start names
D123 with no network call.

## Block B — Authoring

## Block C — Query

### §RK1722 Dates a build can take from the answer

`history` already resolves both moments of a task from git: the commit that added its id
to the roadmap (proposed) and the one that added it to the ledger (shipped). `origin`
asks one id at a time, but `history.added_ids` already reads a whole file in one `git
log -U0` pass, sha only. alegauss.github.io's `scripts/fetch-records.mjs` keeps its own
`shipDates` instead, a second reader of the format whose id pattern already misses a
partial entry's `**RK1169 (…)**` qualifier, which `added_ids` reads.

The date stays derived. "No dates or quarters" forbids a schedule; a date stored in the
line would also cost characters everywhere, conflict on merges and repeat what git holds
(L2). Derived, it survives a rebase and covers every entry already shipped.

The change: `added_ids` carries the commit's date beside its sha, the same date `origin`
reports, so the two reads never disagree. `list --json` and `export --json` carry
`proposed` and `shipped` per task, each `{commit, date}`. Without git or history the
fields are absent, so a caller can tell "never" from "cannot say".

The site runs roadkeep on a `git archive` extract, which has no history, so it would
always get the absent fields. The read must answer from a repository at a revision with
no working tree, such as a bare clone and `--at <rev>`.

Done when fetch-records.mjs can delete `shipDates` and its extract, two runs at one
commit give identical bytes, and a tree without git answers with the fields absent.

## Block D — The gate

## Block E — Adoption

### §RK1726 init offers everything the tool can set up

`init` writes `roadkeep.toml`, the roadmap, the ledger and the rationale file.
Everything else is a separate command found only by reading help: `--strategy` and
`--deferred` are flags nobody is shown, and the plugin surfaces, the vendored engine,
the merge driver and the CI gate are `install`, `install --vendor`, `merge --register`
and a workflow `install` writes only where `.github/workflows` exists. Stopping after
`init` leaves no guard, no merge driver and no gate, silently.

The change: `init` offers every wiring step the tool has, and runs the chosen ones in
its existing all-or-nothing transaction:

- the optional roles strategy and deferred. Not decisions: RK1269 keeps it out of every
  scaffold, so the report names `declare decisions`;
- the plugin wiring: none (the plugin is installed), `install`, `install --committed`,
  or `install --vendor`;
- the merge driver, as `merge --register` writes it, with the `git config` line printed;
- the gate: `install`'s workflow, creating the directory when asked; a pre-commit hook
  has no writer, so the README's snippet is printed.

Each option is the existing verb, called, never a second copy of what it writes.
Defaults stay minimal for a non-interactive call, so a script that runs `init` today
writes the same bytes. The report ends with what was not chosen and the command that
adds it later.

### §RK1727 A prefix derived from the repository name

`init` without `--prefix` mints `RK`, this repository's own prefix. Every project
scaffolded without the flag gets roadkeep's ids: a Turing line and a roadkeep line both
read `RK12`, a commit subject naming one is ambiguous across the portfolio, and a
sibling dep (RK1716) spells `turing: RK12`, which reads as a roadkeep task. Renaming the
prefix after the first `add` is a `renumber` of every id. Collisions already happen by
hand: claude-tray and Turing both chose `T`.

`--existing` already reads the prefix off the ids a roadmap carries. An empty repository
has no ids, but it has a name.

The change: with no `--prefix` and no ids to read, `init` derives one from the
repository's name: the `origin` remote's last path segment, else the directory. A
worktree layout names the directory after a version (`turing/2026.3`), which is why the
remote comes first. The initials of its words, split on `-`, `_`, `.` and case changes,
uppercased (`claude-tray` gives `CT`), lengthened by letters of the first word to at
least two characters (`polyweave` gives `PO`). A name with no letters derives nothing
and `init` asks for `--prefix`. The report prints the derived prefix and the flag that
overrides it. An interactive `init` offers it as the default. `RK` is never a default.

Done when `init` in a clone of claude-tray declares `CT`, in a worktree named `2026.3`
takes the remote's name, the report names `--prefix` as the override, and an explicit
`--prefix` still wins.

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

### §RK1725 Filing into a sibling project

An agent in Dumont that meets a Turing defect files it in Turing. Each friction skill
(viglet-, polyweave-, winwright-friction) carries its own copy of how, and every copy
drifts and needs a local checkout, though RK1716 can read a remote.

The change: a reference beside `writing.md`, opened from `SKILL.md` when a write targets
a project `[projects]` declares (RK1437's cadence):

- A `path` that exists: `roadkeep -C <path> add`, committed there only if that tree
  holds nothing else.
- Otherwise the `git` remote: a shallow clone at `ref` into a temp directory, the same
  `add`, a commit on a branch named for the id and the filer. Before the push, fetch
  `ref` and rebase with `git -c merge.roadkeep.driver=…`: a temp clone has no config,
  and a host never runs a custom driver. An id spent twice is moved with `renumber` and
  the rebase rerun. Then push and open a merge request (GitLab push options, or
  `gh pr create`), never a push to `ref`: the review is RK1723's re-analysis.
- Either way, the caller's line takes the dep `<name>: <id>`.

roadkeep itself never commits or pushes; the reference names the git commands. A
collision landing after the push is caught by the home project's CI `lint` as
`id.duplicate`.

Done when a friction skill files into Turing with no local checkout, a remote that moved
since the clone yields a request with no duplicate id, and the consumer's line carries
the dep.

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

### §RK1729 Both sites on the package's build

RK1714 moved both sites' chrome onto `./site`; what it left is the build step and the
registry.

**The prerender.** `site/scripts/prerender.mjs` and `gui/site/scripts/prerender.mjs`
each render the routes, patch the head by replace-or-throw, write the Markdown twin, the
manifest, the sitemap and robots. The design system's `./vite` entry ships
`prerenderSite` and `lastAuthoredChange` (VDS215) for exactly this, and claude-tray's
site lists `./vite` among its entries. Move both scripts onto it, keeping each site's
own `markdown.mjs` converter and the assertions in `scripts/prerender.test.mjs`; the
gui's social card can take `renderOgCard` from the same entry in place of
`scripts/og-image.mjs`. Read `prerenderSite`'s options before starting: a twin converter
or a manifest field it has no hook for is the open question, and it is answered in the
design system, not by keeping a private copy.

**The registry**, outside this repository and committed there: the design system's
`consumers.json` gains both sites (`chrome: "product-site"`, `tone: "cool"`, accent
amber, entries `./site`, `./site.css`, `./tokens.css`, `./vite`), and the hub's
`projects.json` changes roadkeep from slate `148,163,184` to the amber the pitch uses,
`245,158,11`.

Done when neither site has a prerender script of its own beyond what `prerenderSite`
cannot do, both tests still pass on the built output, and both registries name both
sites.
