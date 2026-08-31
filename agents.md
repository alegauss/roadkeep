# roadkeep — Development Guide

**What this is.** A CLI owning the writes to a project's `ROADMAP.md`, `CHANGELOG.md`,
`IMPROVEMENTS.md` and `STRATEGY.md`, so the format is a schema at insertion and not a
convention an author must remember. A Claude Code plugin: the author to constrain is an agent.

**The problem, measured.** In Viglet Shio: 92 roadmap lines averaging **142 words** against a
one-sentence rule; an `agents.md` at **186 KB**. Six of the eight worst lines were written in
the session that diagnosed it — the drift is invited by the process ([§0](docs/IMPROVEMENTS.md)).

**The insight that decides every design question.** *The saving is the analysis, not the
characters.* A linter reports after the prose exists and asks the author to delete work; a
`maxLength` refuses before a sentence is composed to fill it, so "what would I cut?" becomes
"call `add`".

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
  scoping criteria queueing reverting  the non-goal, what finishes a block, the queue, the undone
  backlog counting picking showing graph briefing budgeting exporting history weighing
  ranking remaining describing commanding governing  the query surface, what git answers,
                     what `roadkeep.toml` may say, what the parser itself takes and the verb
                     that declares a number in it
  linting fixing remedying repairing  the gate, the derived-only fixer, the door every
                  finding names, and the verb that runs the whole report back
  adopting installing  `init` scaffolds, `declare` retrofits a role, `adopt` estimates,
                    `install` wires it in, `engines` says which copies write, judge, gate and merge
  guarding screening attesting serving provenance  the hook, what it loads for, what no verb
                    wrote, the stdio tools, and which tree answered
  capturing  a defect in this tool, as facts a replay re-runs and a sweep deletes once
                the ledger answers for them
  cli.py verbs/ rendering  the parser and dispatch, a module per verb family, every answer
action.yml, .pre-commit-hooks.yaml, .github/   the gate's three surfaces (RK17)
hooks/, skills/, commands/, .claude-plugin/, .mcp.json   the plugin's five, how it is installed
                (RK22-26), and the launcher an adopter commits where no plugin can be (RK1108);
                reasoned in tests/test_{plugin,skill,serving,commands,launching}.py
site/   the two builds that make one site — the pitch, whose copy is one module, and site/docs/,
                the area building into its dist/; joins held in tests/test_area.py
editor/, scripts/, tests/   the editor host and the archive it installs as (RK1011-13), the
                three commands a developer runs, and pytest — docs/ is a fixture, not a mock
```

`Schema.render` is the only writer of the line format, `Schema.validate` the only reader of the
rules, `Document` the only reader of a file: it keeps every source line verbatim and **every
mutator refuses the whole file** when a line it parsed would render back differently. Never
build a task line with an f-string. Get documents from `Config.document(role)`, never by picking
a schema at the call site: the changelog is `schema.as_ledger()` (✅, no deps, no pointer), not a
second grammar. A rejected marker line becomes a `Reject` **with a reason** (`audit` prints
them); a dep the parser cannot type still parses, so the line stays counted — deliberately.

## This repo's own docs are the conformance fixture

`roadkeep lint` **must pass on `docs/`** — the format is proven by the artefact, not asserted in
a README. A limit these lines cannot express is the wrong limit rather than a set of wrong
lines, so a schema change validates here first. Don't hand-check: `… lint` **exits 1** on any
violation, line that stopped round-tripping, dep nothing satisfies, pointer or section nothing
answers, over-budget every-turn file or served tool, dead queue entry, or invisible codepoint —
as `file:line:column`, each carrying **the command that closes it** (RK14/15/30/34/326/420). CI
runs the action this repo ships (RK17); `--fix` repairs only the **derived** — annotation,
pointer, dep order, marker codepoint, whitespace, queue entry, an orphaned criteria
heading (RK16).

## The write path is a skill, not a preamble

[skills/roadkeep/SKILL.md](skills/roadkeep/SKILL.md) is the authority on which command to call,
what it derives, the rules a schema cannot check and how work is picked — loaded when a
governed file is in play, free on turns that touch none (RK23). It is an **orientation**, and
`writing.md` and `asking.md` beside it are the reference the turn that needs one opens: RK23's
argument again, one cadence in (RK1437). It ships in the
plugin, so it is one text everywhere and **nothing here repeats it**. The package is not
installed here: read its every command as `PYTHONPATH=src python -m roadkeep.cli <…>`.

## Building and committing is a skill too

[.claude/skills/roadkeep-dev/SKILL.md](.claude/skills/roadkeep-dev/SKILL.md) is the authority on
running the tests here, editing a source file and composing a commit — **≥3.11 and zero runtime
deps**, no heredoc into source (RK1091), one task per commit, and `run-commit.cmd -m` always.
Twenty-six lines that a turn touching neither the tests nor a commit was paying for, moved for
RK23's reason and by its shape (RK1136). Nothing here repeats it.

## Non-goals are binding, and this file is scaffolding

[docs/ROADMAP.md](docs/ROADMAP.md) → "Non-goals", which `brief` prints with every task. The one a
suggestion keeps violating: **no model, no prompts** (L4) — a generator reintroduces this drift.
What loads every turn is only what a turn touching no governed file needs. The budget is
`[budgets]` in `roadkeep.toml`, held by `lint` and not by this sentence (RK30); the index is a
fifth of it, held by a test, so the prose is what to compress (RK203, RK1135).
