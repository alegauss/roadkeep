---
name: roadkeep-gui-roadmap-docs
description: How to work a task in this project's roadmap — the three docs/ files (ROADMAP.md, CHANGELOG.md, IMPROVEMENTS.md) owned by the roadkeep CLI and never hand-edited, and above all the one-task-one-commit rule: every finished roadmap task ends with `run-commit.cmd -m "<title>"` from the repo root, code plus doc sync in that single commit. Use whenever adding a task, picking the next RK-number, marking a task shipped, retiring, linting, editing any of those files, executing a block or a list of RK ids, or finishing any task that touches this repo.
---

# Roadmap tasks & committing

## ⛔ READ FIRST — one task, one `run-commit.cmd` (non-negotiable)

**A task is not finished until the commit landed.** The commit tool is
`run-commit.cmd` (on the OS PATH, in `D:\Dev\bin`) — never `git commit` by hand:

```
cd d:\Git\alegauss\roadkeep-gui
run-commit.cmd -m "<conventional-commits title, ASCII>"
```

- **Always pass `-m`.** It stages everything and generates the body from the staged
  diff; without a title it infers one, and for a docs/ROADMAP commit that means prose
  about already-shipped work gets misread as `feat: implement <feature>`.
- **`cd` to the repo root first** — `run-commit.cmd` stages relative to CWD.
- **The doc sync rides in the same commit as the code**, so `ROADMAP.md` /
  `CHANGELOG.md` / `IMPROVEMENTS.md` never describe a state that did not ship.
- **You may NOT do more than one task before committing.** A multi-task request
  (a whole block, or a list of `RK<n>`s) is *not* permission to batch: it is a request
  to run them one at a time, committing after each. One giant diff spanning many tasks
  is the failure this rule exists to prevent.
- **A batch of ≥2 tasks runs under the `/loop` skill** (self-paced): exactly one task
  per iteration, `run-commit.cmd` at the end of that iteration, then advance. Do not
  hand-roll a loop that defers commits to the end.
- **Self-check before starting task N+1:** `git status` / `git log -1`. If the previous
  task's work is still in the working tree, stop and commit it first.
- **Declare your paths, then read them back at the moment of committing.** A claim is dated
  by a marker write and released when the marker moves (`[claims] held = 60` minutes).
  `roadkeep claim RK<n> --path <p>` says what the task will touch; **`roadkeep claim RK<n>`
  with no `--path` answers what you declared plus what the tree holds that another live claim
  says is its own — the analysis `git add -A` cannot make.** `roadkeep claims` lists held,
  expired and stale. This matters wherever two sessions run against one checkout: in the
  sibling `pportal` repo a commit made with no live claim swallowed four files of unrelated
  work under its own title.

The same rule applies to any finished unit of work in this repo, roadmap task or not:
when the work is done and validated, commit it with `run-commit.cmd -m "…"` rather than
leaving it in the tree.

## The gate before the commit

Validated means the project's own build and test were run, not that the edit looked right.

**This repo has no build or test entry point yet** — it is a fresh tree holding
`roadkeep.toml` and the three governed files. Until one exists, the gate is `roadkeep lint`
(non-zero exit is the whole point of it) plus whatever the task itself can be checked
against, and a task that *adds* the build is the task that fills this section in with the
commands and when to run each. Do not invent a `compile.cmd` or `test.cmd` here because the
sibling `pportal` repo has them.

When a test suite does arrive: **name EVERY task id an assertion holds, not just the one you
are working.** A test written under one id often ends up holding the task that finished the
work, and naming both is four characters, while the alternative is a second test file
written to move a number.

## ⛔ READ SECOND — the three files are owned by `roadkeep`

[`roadkeep.toml`](../../../roadkeep.toml) declares this project's format (prefix `RK`,
`ref_scheme = "id"`, the markers and the limits) and the roadkeep plugin — declared in
[`.claude/settings.json`](../../settings.json), so a clone gets it — carries the rest: a
hook that **denies a hand-edit** to any of the three files and names the command, the
`mcp__*roadkeep__*` tools whose input schema *is* the format, and its own skill with the
write path. Start a task with `brief`, not by reading the files; `lint` is the gate.

Each file has one job — never duplicate content between them:

| File | Single responsibility |
|---|---|
| [`docs/ROADMAP.md`](../../../docs/ROADMAP.md) | **Task status** — active backlog only (📋 designed · 💭 idea · ⏳ partial · 🛠 in-progress), one line per task, plus block headings and non-goals. Nothing else. |
| [`docs/CHANGELOG.md`](../../../docs/CHANGELOG.md) | What has **shipped** — the ledger, indexed by block. Authoritative for the highest block letter. |
| [`docs/IMPROVEMENTS.md`](../../../docs/IMPROVEMENTS.md) | **Design rationale** for *unshipped* work only. No status tables, no shipped implementation reports. |

- **Shipping is `ship <id>`** — one transaction (ledger entry, roadmap line deleted,
  `§RK<n>` dropped, dependents re-annotated) or none of it. Then commit (rule above).
- **The read BEFORE an add is `delivered <block> --near "<the sentence you would file>"`.**
  It ranks that block's nearest deliveries against the sentence you are about to propose,
  which is the duplicate question asked *before* an id is spent. `add` prints the same
  ranking as `near`, but only after the line exists — that is the difference between
  catching a duplicate and recording one. `non-goal list` is the other read, and non-goals
  are binding.
- **Adding is `add --block <x> --symptom "…" --why "…"`.** `ref_scheme = "id"` means the
  `§RK<n>` pointer is derived, not hand-numbered; the section prose is `section add`.
  **Reuse an existing block** — `stats` lists the ones still holding open lines,
  `grep -nE '^## Block' docs/CHANGELOG.md` lists every block ever opened. A new block
  needs a job no existing heading can honestly hold, and is titled for the *capability*,
  not for the task in hand.
- **The next id is `roadkeep next-id`** — it scans all three files and never fills a gap.
  Retired ids are never reused.
- **Status lives in exactly one file.** If a marker in `IMPROVEMENTS.md` disagrees with
  the roadmap files, the roadmap files win.
- **Keep a task line terse** — one sentence: symptom + why + `→ §RK<n>` pointer. The
  reasoning belongs in `IMPROVEMENTS.md`, which is what the pointer addresses.
- **Non-goals are binding.** They are refused at input like every other line — check them
  before proposing new work.
- **Order is `priority` in `roadkeep.toml`**, not opinion. It is currently empty, so the
  order is the block headings' own and then the lowest ready id.
