---
name: roadkeep-dev
description: "How to build, test and commit in the roadkeep repository itself, and what a shipped task may file behind it. Use when running pytest here, editing a source file, staging a change, or writing a commit — and whenever a scripted edit to source is about to be made, a task is about to be shipped or filed, or a commit message is about to be composed. Trigger words: pytest, run the tests, commit, stage, git add, heredoc, version bump, run-commit, ship, file a task, add --block."
---

# roadkeep — building and committing in this repository

Trigger-loaded, and that is the whole reason it is a file (RK23, RK1136). `agents.md` is
resident on **every** turn and holds a `[budgets]` ceiling that `lint` enforces (RK30); these
twenty-six lines are needed on a turn that runs the tests or writes a commit, and were paid
for by every turn that did neither. What is here is what that turn needs, in full — the
budget these sentences were squeezed against is not this file's.

## Build and test

- **Python ≥3.11** (`tomllib` is stdlib there; 3.13.14 here) and **zero runtime deps**:
  `argparse` + `tomllib`, never `click` + `pydantic` — a tool meant to run as `uvx roadkeep`
  in someone else's CI pays for every dependency it takes.
- `uv` is **not** installed here. Run `python -m pytest` from the repo root, where
  `pythonpath = ["src"]` is already declared; the package is not installed, so every command
  in the plugin's own skill reads as `PYTHONPATH=src python -m roadkeep.cli <…>`.
- Test dependencies are `pip install --user pytest pytest-xdist`. `-n auto` is on by default
  and `-n0` undoes it, which is what a test reading captured output wants.
- Round-trip (L3) is a **property test over real files**: this repository's `docs/`, plus
  Shio's and Turing's at the revision `tests/corpora.py` pins. Absent or unpinnable, they
  skip — which is what CI does, and why a green run there proves less than a green run here.

## Editing source

**Never edit source through a shell heredoc.** `python - <<'PY'` turned `\n` in a literal into
a real newline four times in one session, twice also dropping that script's *other* edit
silently (RK1091). Write the whole file, or pass old and new text as data.

**Anchor on bytes, not on a guess.** `.gitattributes` pins the terminator so an anchor cannot
match nothing (RK1132), and a test refuses a file that mixes the two. A scripted patch still
carries an `assert` on its anchor before it writes: that assert is the difference between a
patch that stops and a patch that silently writes the wrong bytes.

## Shipping: file a defect, never a design question

**A task that revealed nothing wrong files nothing.** Measured over one session working this
backlog: 5 tasks shipped and **10 filed**, 37 → 42 open — a loop told to stop when nothing
remains could never stop. The rule that produced it was "archive what the task revealed", read
as *anything I noticed*.

File a line only where something is **wrong now and the cost is nameable**: a figure that is
false, a door that refuses, a reading that drops data. Three of those ten qualified — a
per-block reading dropping 846 of 901 entries, every `reopen` leaving a dangling pointer, a dep
resolving as unknown against a file that answers exactly. The other seven were observations
(*the set argues for none of the split*, *two payloads say `notes` about two populations`*) and
belonged in the commit body.

The corpus invites the mistake: every design section here ends on an open question and the
backlog is full of 💭 ideas, so noticing reads as filing. It is not — a design question filed as
a task is work somebody now owes.

**A defect the task exposes in its own work is fixed in that commit, never filed.**

## Committing

**One task → one commit, the instant it is validated.** What `ship` wrote goes in the *same*
commit as the code, so the docs never describe a state that did not ship. A batch of two or
more ready tasks is **not** permission to batch the commits.

Use `run-commit.cmd -m "<conventional-commits title>"` from the repo root, **`-m` always** and
ASCII. Without it, a docs commit's prose about already-shipped work is misread as `feat:
implement <feature>` — the title is yours and only the body is generated.

**It stages everything.** That is why a claim carries a **scope**: `claim <id> --path …` says
what this commit owns, and `claim <id>` reads it back against the tree (RK280) — naming what
some other session is holding, what no claim accounts for, and which ids moved inside a file
this commit stages (RK1117, RK1120). Every write also **prints the `git add --` line** for
what it wrote, projections included (RK298, RK1129, RK1130). Run that line, then commit.

**Every commit bumps the patch version** (RK153). `.githooks/pre-commit` does it and never
blocks; it is wired by `git config core.hooksPath .githooks`, which a fresh clone has to run.
