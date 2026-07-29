<p align="center">
  <img src="docs/assets/roadkeep-banner.svg" alt="roadkeep — a schema at the point of insertion" width="840">
</p>

<!--
  Assets in docs/assets/ — the mark is task lines cut at a gate, with the refused
  remainder faded beyond it. The SVGs follow the reader's light/dark theme; the PNG
  cannot, so it carries a fixed dark palette.

    roadkeep-mark.svg     160x160   icon
    roadkeep-logo.svg     520x160   mark + wordmark
    roadkeep-banner.svg  1200x300   the header above
    roadkeep-social.svg  1280x640   source for the link preview
    roadkeep-social.png  1280x640   upload at Settings > General > Social preview.
                                    This is what renders when the repo URL is pasted
                                    into LinkedIn, Slack or a link card anywhere else.
                                    Re-render after editing the SVG:
                                    msedge --headless=new --window-size=1280,640 \
                                      --screenshot=docs/assets/roadkeep-social.png \
                                      file:///.../docs/assets/roadkeep-social.svg
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
[docs/IMPROVEMENTS.md §0.3](docs/IMPROVEMENTS.md) is authoritative.

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

| Block | Open | Shipped |
| --- | --- | --- |
| A — The model (a task is data before it is a line) | 0 | 8 |
| B — Authoring (insert, never hand-edit) | 0 | 6 |
| C — Query (consult without reading the file) | 0 | 8 |
| D — The gate | 6 | 2 |
| E — Adoption | 4 | 0 |
| F — The Claude Code plugin (the guardrail at the agent boundary) | 5 | 0 |
| **Total** | 15 | 24 |

**Next ready:**

- 📋 **RK16** (deps: RK14 ✅) **A report of ninety-two violations is a report nobody acts on** — `lint --fix` normalizes what is mechanical (ordering, dep markers, whitespace) and reports only what needs a human decision. → §RK16
<!-- roadkeep:end -->

Every command takes `--json`, which carries provenance — which file and line the answer
came from — because an answer an agent cannot audit gets verified by reading the file,
which is the cost the command existed to remove.

Still open, and where to look: [docs/ROADMAP.md](docs/ROADMAP.md). The gate (`lint`) and
the plugin hook that denies an agent the hand-edit are Blocks D and F.

## Install

Python ≥3.11, **zero runtime dependencies** — `argparse` and `tomllib`, not `click` and
`pydantic`. A tool meant to run in someone else's CI pays for every dependency it takes.

```sh
pip install git+https://github.com/alegauss/roadkeep   # PyPI: not yet (RK19)
```

## Non-goals

These are binding, and half the point. Check before proposing work:

- **No web UI and no server.** Files and a CLI.
- **No issue-tracker sync.** A backlog that lives in a service is one an agent cannot `grep`.
- **No model and no prompts inside the tool.** It validates and renders; it never writes
  the symptom or the rationale.
- **No dates, quarters or estimates.** A marker is maturity, not a schedule.

## This repository is the conformance fixture

`roadkeep lint` must pass on `docs/` here. The format is proven by the artefact rather
than asserted in a README — including this one. A limit that cannot express these lines
is the wrong limit, not a set of wrong lines, and the test suite asserts it against
`docs/ROADMAP.md` under this repository's own `roadkeep.toml`.
