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

## Block B — Authoring

## Block C — Query

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)

## Block J — Validation (whether a person ever tried it)

## Block K — The desktop app (one installer for the reader and the plugin)

### §RK1700 One installer: the app, then the plugin

electron-builder already produces NSIS on Windows and an AppImage on Linux; the dmg is
declared and has never been built. None of them touches Claude Code, so a person gets
the reader and still has to run `claude plugin marketplace add alegauss/roadkeep` and
`claude plugin install roadkeep@alegauss` by hand.

The installer runs those two commands after placing the app: an NSIS `customInstall`
macro on Windows, a postinstall step in the dmg flow on macOS, and a first-run step in
the app for the AppImage, which has no install phase. It installs through the `claude`
CLI and never copies plugin files itself, so an update to the plugin is Claude Code's
and not the installer's. Declining the step leaves the app working as a reader of
projects whose engine is already present.

### §RK1701 Prerequisites the installer names

The plugin's MCP server is `python scripts/roadkeep.py mcp`, so it needs Python 3.11 or
newer on PATH, and the install step needs the `claude` executable. A machine missing
either gets an installer that reports success and a plugin that fails on its first call,
far from the cause.

Before the plugin step, the installer checks both and names what is missing and how to
get it; it does not install Python or Claude Code itself. The app repeats the check on
start, since either can be removed later. The resolution already has a place to say
this: an unresolved engine carries its reason.

"No supported Python API." does not bind this: the check runs the interpreter and reads
its version, and imports nothing from the package.

### §RK1702 One tag, the CLI and the installers

Here a release is a version bump and PyPI; in roadkeep-gui a `v*` tag packages Windows
and Linux. Once they share a tree, one tag should give the CLI and an installer built
against that same commit, so the app a person downloads was tested against the engine it
ships beside.

The `package` job moves in with its matrix (Windows, Linux, and macOS if a runner builds
the dmg), and the installers attach to the tag's GitHub release. Unsigned builds stay
unsigned and say so, as the gui's own `electron-builder.yml` already does; signing is a
certificate somebody buys and stays out of this block.

RK1697 moved the gui's `ci.yml` to `.github/workflows/gui.yml` unchanged, `v*` tag and
all, because RG50 and RG157 read its tag check and draft release. So today a roadkeep
`v*` tag also starts the gui's package job, whose check refuses a tag that is not
gui/package.json's version (0.1.0 against 0.2.x): the job goes red and nothing is
drafted. Settling which version a tag names settles that check too.
