# roadkeep — Development Guide

**What this is.** A CLI that owns writes to a project's `ROADMAP.md`, `CHANGELOG.md`,
`IMPROVEMENTS.md` and `STRATEGY.md`, so the format is a schema at the point of insertion
rather than a convention an author is asked to remember. Shipped as a Claude Code plugin,
because the author to constrain is usually an agent.

**The problem, measured.** In Viglet Shio: 92 roadmap lines averaging **142 words** against a
one-sentence rule; an `agents.md` at **186 KB**. Six of the eight worst lines were written in
the session that diagnosed it — the drift is invited by the process ([§0](docs/IMPROVEMENTS.md)).

**The insight that decides every design question.** *The saving is the analysis, not the
characters.* A linter reports after the prose exists and asks the author to delete work; a
`maxLength` refuses before a sentence is composed to fill it, turning an analytical act
("what would I cut?") into a procedural one ("call `add`").

## The six laws

Compressed; **[§0.3](docs/IMPROVEMENTS.md) is authoritative** — a change breaking one is wrong even if requested.

| # | Law |
|---|---|
| L1 | Schema enforced **where the text is created**; `lint` is only the backstop. |
| L2 | The **store is the repository** — Markdown, greppable, no database, no service. |
| L3 | **Round-trip or don't write** — parse → render → byte-identical, or refuse the file. |
| L4 | The tool **never writes prose** — it validates and renders. |
| L5 | **Query instead of read** — every question is a command, so answering costs no context. |
| L6 | **Configuration, not convention** — prefix, paths, markers, limits are per-project. |

## Layout

```
docs/ROADMAP.md        active backlog, one line per task (RK<n>)
docs/CHANGELOG.md      shipped ledger, indexed by block
docs/IMPROVEMENTS.md   design rationale for UNSHIPPED sections only
agents.md, roadkeep.toml   this file, and this project's own configuration
src/roadkeep/   the package. **Each module's docstring is the authority**; this only locates,
so it carries no task numbers — `origin <id>` answers where a rule came from:
  kernel/{schema,document}  one template, and the file it round-trips; imports nothing
                          above it (tests/test_kernel.py)
  config ids referring  a role's declared shape, the id, the relations a reference resolves in
  authoring blocking shipping markers sections  the writes, whole
  deferring renumbering merging  the doors that are not terminal, and the merge git cannot make
  locking claiming storing  scan-to-save is one span, who holds a line, one grammar
  scoping queueing reverting  the non-goal, the queue, the undone
  backlog counting picking showing graph briefing budgeting exporting history weighing
  ranking remaining  the query surface, plus what git answers
  linting fixing remedying repairing  the gate, the derived-only fixer, the door every
                  finding names, and the verb that runs the whole report back
  adopting installing  `init` scaffolds, `adopt` estimates, `install` wires it in, `engines`
                          says which three copies write, judge and gate
  guarding screening attesting serving provenance  the hook, what it loads for, what no verb
                    wrote, the stdio tools, and which tree answered
  capturing  a defect in this tool, as facts a replay re-runs
  cli.py verbs/ rendering  the parser and dispatch, a module per verb family, every answer
action.yml, .pre-commit-hooks.yaml, .github/   the gate's three surfaces (RK17)
hooks/, skills/, commands/, .claude-plugin/, .mcp.json   the plugin's five, and how it is
                installed (RK22-26); reasoned in tests/test_{plugin,skill,serving,commands}.py
editor/, scripts/, tests/   the editor host and the archive it installs as (RK1011-13), the
                two commands a developer runs, and pytest — docs/ is a fixture, not a mock
```

`Schema.render` is the only writer of the line format, `Schema.validate` the only reader of
the rules, and `Document` the only reader of a file — it keeps every source line verbatim
and **every mutator refuses the whole file** when a line it parsed would render back
differently. Never construct a task line with an f-string. Get documents from
`Config.document(role)` and never by picking a schema at the call site: the changelog is
`schema.as_ledger()` (✅, no deps, no pointer), not a second grammar. A rejected marker line
becomes a `Reject` **with a reason** (`audit` prints them); a dep the parser cannot type
still parses, so the line stays counted — that split is deliberate.

## This repo's own docs are the conformance fixture

`roadkeep lint` **must pass on `docs/`** — the format is proven by the artefact, not asserted
in a README. A limit that cannot express these lines is the wrong limit rather than a set of
wrong lines, so a schema change validates here first. Don't hand-check it: `… lint` **exits 1**
on any violation, line that stopped round-tripping, dep nothing satisfies, pointer or section
nothing answers, over-budget every-turn file or served tool, dead queue entry, or invisible
codepoint — as `file:line:column`, each carrying **the command that closes it**
(RK14/15/30/34/326/420). CI runs the action this repo ships (RK17); `--fix` repairs only the
**derived** (annotation, pointer, dep order, marker codepoint, whitespace, queue entry) (RK16).

## The write path is a skill, not a preamble

[skills/roadkeep/SKILL.md](skills/roadkeep/SKILL.md) is the authority on which command to call,
what it derives, the rules a schema cannot check, the query surface and how work is picked —
loaded when a governed file is in play, free on turns that touch none (RK23). It ships in the
plugin, so it is the same text everywhere and **nothing here repeats it**. The package is not
installed here: read every command in it as `PYTHONPATH=src python -m roadkeep.cli <…>`.

## Build and test

- **Python ≥3.11** (`tomllib` is stdlib there; 3.13.14 here) and **zero runtime deps**:
  `argparse` + `tomllib`, never `click` + `pydantic` — a tool meant to run as `uvx roadkeep`
  in someone else's CI pays for every dependency it takes.
- `uv` is **not** here — `python -m pytest` from repo root (`pythonpath = ["src"]`); deps are
  `pip install --user pytest pytest-xdist`, `-n auto` is on and `-n0` undoes it. Round-trip
  (L3) is a **property test over real files**: `docs/`, plus Shio's and Turing's at the
  revision `tests/corpora.py` pins — absent or unpinnable, they skip (CI).

## Editing and committing

**Never edit source through a shell heredoc.** `python - <<'PY'` turned `\n` in a literal into
a real newline four times in one session, twice also dropping that script's *other* edit
silently (RK1091). Write the whole file, or pass old and new text as data.

**One task → one commit, the instant it is validated.** What `ship` wrote goes in the *same*
commit as the code, so the docs never describe a state that did not ship; a batch of ≥2 tasks
is **not** permission to batch. Use `run-commit.cmd -m "<conventional-commits title>"` from the
repo root, **`-m` always** and ASCII — without it a docs commit's prose about shipped work is
misread as `feat: implement <feature>`. It stages everything, which is why a claim carries a
**scope**: `claim <id> --path …` says what this commit owns and `claim <id>` reads it back
against the tree (RK280), and **`ship` prints the `git add --` line** for what it releases
(RK298) — run that, then commit. **Every commit bumps the patch version** (RK153):
`.githooks/pre-commit` does it, never blocks, wired by `git config core.hooksPath .githooks`.

## Non-goals are binding, and this file is scaffolding

[docs/ROADMAP.md](docs/ROADMAP.md) → "Non-goals", which `brief` prints with every task. The one a
suggestion keeps violating: **no model, no prompts** (L4) — a generator reintroduces this drift.
What loads every turn is only what a turn touching no governed file needs; the budget is
`[budgets]` in `roadkeep.toml`, held by `lint` and not by this sentence (RK30), and the Layout
index is a fifth of it, held by a test, so the prose here is what to compress (RK203).
