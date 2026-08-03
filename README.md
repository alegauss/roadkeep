<p align="center">
  <img src="https://raw.githubusercontent.com/alegauss/roadkeep/main/docs/assets/roadkeep-banner.png" alt="roadkeep — a schema at the point of insertion" width="840">
</p>

<!--
  Assets in docs/assets/ — the mark is task lines cut at a gate, with the refused
  remainder faded beyond it. The SVGs follow the reader's light/dark theme; a PNG
  cannot, so each carries a fixed dark palette.

    roadkeep-mark.svg     160x160   icon
    roadkeep-logo.svg     520x160   mark + wordmark
    roadkeep-banner.svg  1200x300   source for the header above
    roadkeep-banner.png  1200x300   the header above. Raster and absolute because this
                                    file is also the PyPI project page (RK19): a
                                    relative path resolves against pypi.org and an SVG
                                    is served as text/plain, so both render as broken.
    roadkeep-social.svg  1280x640   source for the link preview
    roadkeep-social.png  1280x640   upload at Settings > General > Social preview.
                                    This is what renders when the repo URL is pasted
                                    into LinkedIn, Slack or a link card anywhere else.
                                    Re-render either PNG after editing its SVG:
                                    msedge --headless=new --window-size=1200,300 \
                                      --screenshot=docs/assets/roadkeep-banner.png \
                                      file:///.../docs/assets/roadkeep-banner.svg
-->


**A CLI that owns the writes to your `ROADMAP.md`, `CHANGELOG.md`, `IMPROVEMENTS.md`
and `STRATEGY.md`, so the format is a schema at the point of insertion instead of a
convention an author is asked to remember.**

Shipped as a Claude Code plugin, because the author to constrain is usually an agent.

---

## The problem, measured

This did not start as an idea. It started as three readings from a real production
repository, where all three files declared a format and none enforced it:

| Artefact | Declared rule | Actual reading |
|---|---|---|
| `docs/ROADMAP.md` | one sentence per task | 92 lines, **142 words** average, worst **1406 characters** |
| `agents.md` | index only, loaded every turn | grew to **186 KB (~46k tokens)** |
| `docs/IMPROVEMENTS.md` | rationale for *unshipped* work | a sibling project's reached **539 KB** |

The finding that decided the design: **six of the eight worst lines were written in the
session that then diagnosed the problem.** This is not inattention. An author — human or
model — who has the whole design in working memory will write it where the reader is,
and an instruction to be terse does not survive the moment its author knows more than
the line allows.

## Why a linter was the wrong answer

A linter reports *after* the prose exists. By then the tokens are spent, and the author
is being asked to delete work they just did. A field with `maxLength: 200` refuses at
the point of insertion, before a sentence is composed to fill it.

Same rule, two orders of magnitude cheaper — and it converts an analytical act (*"is
this too long, and what would I cut?"*) into a procedural one (*"call `add`"*).

> **The saving is the analysis, not the characters.**

## What makes it different

The space around this is not empty, and the honest comparison is narrow:

| | What it does well | Why roadkeep is not it |
|---|---|---|
| **markdownlint** | structure and style of Markdown | explicitly not prose — it will not tell you a sentence is too long |
| **Vale** | prose rules, style guides | a linter: it reports after the text exists, which is the cost being avoided |
| **Backlog.md**, taskmd, and the markdown-task-for-agents family | mature task management, kanban, MCP | one `.md` **file per task**, with acceptance criteria and DoD — more room, and more room invites more prose |
| **ADR / MADR** | rationale that survives, superseded never deleted | an ADR set grows monotonically; that curve *is* the 539 KB above |

Four properties are the actual differentiator:

1. **Enforced at the write path, not the review.** The refusal happens before the prose
   exists. Everything else in this space reports afterwards.
2. **It governs the file you already have.** One line in your existing `ROADMAP.md` —
   not a new store you migrate into. A repository with a hand-written backlog is the
   target, not the obstacle.
3. **Round-trip or refuse.** Parse → render → byte-identical, or the tool declines to
   write the file at all. A tool that owns writes to a hand-edited file has to prove it
   cannot corrupt one.
4. **Query instead of read.** Every question a maintainer asks the file is a command,
   so answering it costs no context. Reading a backlog end-to-end to find one ready
   task cost ~5k tokens in this very repository.

## The six laws

A change that breaks one is wrong even if requested.
[docs/IMPROVEMENTS.md §0.3](https://github.com/alegauss/roadkeep/blob/main/docs/IMPROVEMENTS.md)
is authoritative.

| # | Law |
|---|---|
| L1 | The format is a schema, **enforced where the text is created**; `lint` is the backstop. |
| L2 | **The store is the repository** — Markdown, greppable, diffable. No database, no service. |
| L3 | **Round-trip or don't write** — parse → render → byte-identical. |
| L4 | **The tool never writes prose** — it validates and renders. |
| L5 | **Query instead of read** — every question is a command. |
| L6 | **Configuration, not convention** — prefix, paths, markers and limits are per project. |

L4 is the one people try to relax first. A generator that writes the `symptom` for you
would reintroduce exactly the drift this exists to stop.

## Status

The table below is **not written by hand** — `roadkeep export --readme` derives it from
`docs/`, which is the point of RK39: a README that restates a backlog it cannot re-read is
stale from the first ship, and this one claimed "8 of 36" while four of the commands it
called unbuilt were already in the ledger.

<!-- roadkeep:begin -->
<!-- generated by `roadkeep export --readme`; edit the governed files instead -->

| Block | Open | Shipped | Retired |
| --- | --- | --- | --- |
| A — The model (a task is data before it is a line) | 2 | 21 | 0 |
| B — Authoring (insert, never hand-edit) | 5 | 30 | 0 |
| C — Query (consult without reading the file) | 0 | 33 | 0 |
| D — The gate | 10 | 15 | 0 |
| E — Adoption | 9 | 18 | 1 |
| F — The Claude Code plugin (the guardrail at the agent boundary) | 3 | 18 | 1 |
| **Total** | 29 | 135 | 2 |

**Next ready:**

- 📋 **RK103** (deps: —) **A bullet whose marker holds a space is read as prose and reported by nothing** — GitHub's `- [ ]` task list is the commonest Markdown backlog there is, and cursarei's 16 of them parse as 0 entries and 0 rejects — the silent miss the reject list exists to end. → §RK103
<!-- roadkeep:end -->

Every command takes `--json`, which carries provenance — which file and line the answer
came from — because an answer an agent cannot audit gets verified by reading the file,
which is the cost the command existed to remove.

Open work, and where to look:
[docs/ROADMAP.md](https://github.com/alegauss/roadkeep/blob/main/docs/ROADMAP.md) — the count
and the next ready line are in the derived block above, so this sentence states neither. The
same file carries the **non-goals**, which is the half of it that binds: `brief` prints them
with every task, and they are what a proposal is checked against before it becomes a line.

Four projects are adopted and governed — this one, Shio, Turing and Dumont — each with its own
`roadkeep.toml` and the measurement that produced it. A fifth candidate was measured and
**retired** rather than adopted: its tasks are wrapped paragraphs with their deps on a line of
their own, and reading those is a second grammar rather than a configuration key. That refusal
is the one worth reading, because a tool that stretched to fit it would have stopped being
able to promise the round-trip.

## Adopt it in a project — two commands, and the repository carries the rest

Nothing is installed and nothing is added to `PATH`. The plugin ships this package, so the
only thing the machine needs is a Python ≥3.11 interpreter — which is what runs the tool
either way. Run these in the project you want governed:

```sh
claude plugin marketplace add alegauss/roadkeep --scope project
claude plugin install roadkeep@alegauss --scope project
```

`--scope project` writes both declarations into that repository's `.claude/settings.json`:

```jsonc
"extraKnownMarketplaces": { "alegauss": { "source": { "source": "github", "repo": "alegauss/roadkeep" } } },
"enabledPlugins": { "roadkeep@alegauss": true }
```

Commit that file and **every clone is wired** — no per-machine step, no OS-specific path. What
arrives with it: the hook that denies a hand-edit and names the tool, the twelve MCP tools
whose input schema is *your* project's schema, the four `/roadkeep:*` commands, and the skill
that loads only when a governed file is in play (~300 tokens per session, all in).

Then declare the format once. `init` and `adopt` run before the project is governed, so they
are the one thing that wants a shell — the plugin's own copy answers, with no install:

```sh
# the plugin's launcher, wherever the marketplace was cloned
R=~/.claude/plugins/marketplaces/alegauss/scripts/roadkeep.py

python $R adopt docs/ROADMAP.md --prefix SH   # measures first: what would change, and where
python $R adopt docs/IMPROVEMENTS.md --sections   # the other half: sections, and the width
python $R init                                # writes roadkeep.toml and the files it declares
```

Both halves, because both are limits you have to declare. The backlog run reports the longest
`symptom`, `why` and rendered line; the `--sections` run reports the longest section in words
and the width your prose is already wrapped to — the numbers `[limits]` gets set from, taken
from your corpus rather than copied from this one.

Everything a *task* needs afterwards is already in the tools the plugin installed: `add`,
`status`, `ship`, `retire`, `record_add`, `record_drop`, `section_add`, `section_drop`,
`brief`, `pick`, `list`,
`deps`, `lint`. No shell, no `PATH`, and the schema each of them validates against is the one
`roadkeep.toml` just declared.

**[Viglet Shio](https://github.com/openviglet/shio) is the reference adoption**: 80 task
lines, a 618 KB ledger of 233 entries written years before this tool, and a `roadkeep.toml`
that declares exactly what that history is — `[ledger]` for the two slots its lines never
carried, `[limits.changelog]` for a file whose median line is 1038 characters, and
`[rules.changelog]` for the two prose rules history cannot obey.

### Or from a checkout beside it

A project adopting an *unreleased* version runs a sibling checkout rather than the published
plugin — and then the hook, the tools and the skill arrive with nothing, because those ship
with the plugin. `install` writes them itself, translated from the files the plugin carries,
with the launcher's path as the only substituted fact:

```sh
python ../roadkeep/scripts/roadkeep.py -C . install
python ../roadkeep/scripts/roadkeep.py -C . install --check   # in CI: still in step?
```

`.mcp.json`, the guard on its three hook events in `.claude/settings.json`, a verbatim
`.claude/skills/roadkeep/SKILL.md`, and — only where the repository already has workflows — a
job calling the action above. The skill is **refreshed on every run** and `--check` exits 1
once it drifts, which is what a vendored copy otherwise has nothing to keep it in step with.
Declarations are merged, so what another tool wrote in either file survives; the workflow is
written once and tuned by you thereafter. The fifth surface is named and not written: the line
in `CONTRIBUTING.md` is prose about your project, and this tool writes none (L4).

### Or just the CLI

```sh
uvx roadkeep lint                                      # no install, no checkout
pip install roadkeep

pip install git+https://github.com/alegauss/roadkeep   # an unreleased commit
```

Python ≥3.11, **zero runtime dependencies** — `argparse` and `tomllib`, not `click` and
`pydantic`. A tool meant to run in someone else's CI pays for every dependency it takes,
and that is also what makes the first line above viable: there is nothing to resolve.

## Run it as a gate

`roadkeep lint` exits **1** on a file that drifted and **0** on one that did not — that exit
code is the whole contract, so every surface calls the same command rather than a copy of it.
A gate that runs in only one place is a gate with a documented bypass.

```yaml
# .github/workflows/gate.yml — the action this repository ships
steps:
  - uses: actions/checkout@v4
  - uses: alegauss/roadkeep@main        # with: {directory: .}

# .pre-commit-config.yaml — the same command, one step earlier
repos:
  - repo: https://github.com/alegauss/roadkeep
    rev: v0.1.0                        # or main, to track an unreleased commit
    hooks:
      - id: roadkeep-lint              # or roadkeep-lint-fix, which normalizes first
```

`--fix` repairs only what the format *derives* — the dep annotation, the pointer, dep order,
an invisible codepoint, whitespace around a field — and leaves every editorial finding to a
human, which is what keeps a first run on a real backlog down to a report somebody reads.

Two things it reports **without** failing, because refusing them would fail an honest file
and a gate that gets bypassed is worth nothing: what a `Block X` dep expands to (one token
named 41 open tasks in the backlog measured above), and — with `--since HEAD`, which the
pre-commit hook passes — a rationale section edited while the line carrying its status was
not. The line is the only thing `pick` reads and the section is deleted on ship, so a
requirement written only into the reasoning cannot be picked, shipped, or kept.

The gate also holds the files nobody edits on purpose. An instruction file loaded on every
turn spends the resource this tool exists to protect, and `agents.md` reached **186 KB** in
the project measured above while declaring a 150-line rule at the bottom of itself — so the
budget moves out of its prose and into the configuration, in both units a reader pays:

```toml
[budgets]
"agents.md" = { lines = 125, bytes = 8400 }   # this repository's own, held by `lint`
```

## Run it as a Claude Code plugin

The store is Markdown (L2), so an agent can bypass the entire format with one `Edit` — and
will, because `Edit` is cheaper than reading a `--help`. A gate at the commit catches that a
whole turn of prose too late: the tokens are already spent, and the report asks for a
deletion. So the plugin installs the one enforcement point an agent cannot route around.

```jsonc
// hooks/hooks.json, shipped in this repository — `roadkeep guard` answers both events
"PreToolUse": [{ "matcher": "Edit|MultiEdit|NotebookEdit|Write", … }]   // deny, and say what to call
"Stop":       [{ … }]                                                  // `lint`, before the turn ends
```

A write to a file some project's `roadkeep.toml` declares is **denied with the command that
does it properly**, flags included — a refusal that names no alternative is one an agent
routes around, and one that names the command makes the denial the cheapest path forward:

```
Edit refused: docs/ROADMAP.md is this project's roadmap, and roadkeep owns its writes.
…
Call instead, from the project root:
  roadkeep add --block <x> --symptom "…" --why "…"  a new task line, fields refused at input
  roadkeep status <id> <marker>                     a marker, and only in this file
  roadkeep ship <id>                                shipped: ledger entry, line gone, section dropped
```

Three properties are load-bearing, and each is a test rather than an intention. The config is
discovered **from the file** and not from the working directory, so one hook process answers
correctly for every repository a session touches. **Silence is the allow** — `deny` is the only
decision it ever returns, because `allow` in this protocol *grants* the write and would wave
through the permission rules you set for every file the tool has no opinion about. And **every
failure allows**: a broken `roadkeep.toml`, a payload that is not JSON, a tool input with no
path. A guard that denies on its own errors turns one typo into a repository nobody can edit,
and the gate is still there at the commit.

`Bash` is deliberately not matched: `sed -i` on the roadmap is a real bypass, and matching every
shell command to catch it taxes every command in the session. The `Stop` hook runs `lint`
instead — so the bypass is caught before the turn ends, by the agent that can still fix it.

The denial is one surface of four; the other three are what make calling the command cheaper
than typing it. The plugin ships an **MCP server** — `roadkeep mcp`, JSON-RPC on stdio, no
port and no state — exposing `add`, `ship`, `pick` and `lint` as tools whose input schema is
*derived*: `maxLength` is this project's `symptom` and `why` limits, `enum` is its declared
markers, `pattern` is its id shape, and the description is the subcommand's own help. So a
misspelt `--deps` is refused by the protocol with the arguments that exist, instead of costing
a round trip to a usage string, and every call is dispatched through the same parser a
terminal uses — one engine, one refusal.

The same four are **slash commands** — `/roadkeep:add`, `/roadkeep:ship`, `/roadkeep:pick`,
`/roadkeep:lint` — for the person driving the standard, who reads `/help` and not a JSON
Schema. `/roadkeep:add F | what does not work | one sentence.` passes those words *verbatim*:
the command files are written so that every instruction about the user's text is a
prohibition, because a prompt that said "write a concise symptom" would have moved the prose
generation one file to the left while keeping L4's letter. That is asserted, not intended —
`tests/test_commands.py` refuses the phrasing.

The fourth is a **skill**, `skills/roadkeep/SKILL.md`, holding which command to call, what it
derives, the two rules a schema cannot check, and how work is picked. It is a skill and not a
paragraph in the
project's instruction file because instructions are loaded on *every* turn, including the ones
that touch no roadmap — the budget above exists because that is how the 186 KB happened. The
skill is read when a governed file is in play and costs nothing otherwise, and it ships with
the plugin, so the standard is the same text in every project rather than a copy per repo.

All four install with the two commands at the top of this file, and both surfaces the harness
starts run `python "${CLAUDE_PLUGIN_ROOT}/scripts/roadkeep.py"` — the package the plugin
already copied. There is no console script to install and no `PATH` entry to add, because a
plugin that installs cleanly and then starts nothing is the failure that taught this (RK57).

One more property makes the gate usable on a repository that adopts the tool late: the `Stop`
hook judges **only the lines the working tree changed**. Shio joined with 278 findings in it,
and a gate that blocked the end of every turn over somebody else's history is a gate that gets
switched off — so `lint`, the pre-commit hook and the Action still judge every line, and the
hook answers the narrower question it was installed to answer (RK60).

## Non-goals

These are binding, and half the point. Check before proposing work:

- **No web UI and no server.** Files and a CLI — the MCP server above is one stdio process
  speaking JSON-RPC to the CLI, which binds nothing and stores nothing.
- **No issue-tracker sync.** A backlog that lives in a service is one an agent cannot `grep`.
- **No model and no prompts inside the tool.** It validates and renders; it never writes
  the symptom or the rationale.
- **No dates, quarters or estimates.** A marker is maturity, not a schedule.

## This repository is the conformance fixture

`roadkeep lint` must pass on `docs/` here. The format is proven by the artefact rather
than asserted in a README — including this one. A limit that cannot express these lines
is the wrong limit, not a set of wrong lines, and the test suite asserts it against
`docs/ROADMAP.md` under this repository's own `roadkeep.toml`.
