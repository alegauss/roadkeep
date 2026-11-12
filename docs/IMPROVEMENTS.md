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

## Block L — Product sites on the package

## Block M — Codex integration (one engine, host-specific adapters)

### §RK1737 Native Codex enforcement and compatibility evidence

Observed on Codex CLI 0.167.0-alpha.4.1 (desktop 26.1106), Windows 11, gpt-6.1-sol, via
`codex exec` in a disposable repository: SessionStart runs; apply_patch and a shell
write on the roadmap are denied; the server binds the session's directory. Codex reads
only `.codex-plugin/plugin.json`, expands no variable in server args, passes no plugin
variable to the server, names tools `mcp__roadkeep__*`, and gives hooks `PLUGIN_ROOT`. A
plugin update leaves its hooks untrusted, reported Failed, and the write goes through.

Left: the same in the desktop app and an IDE; Stop reporting lint without a loop; two
worktrees, nested repositories, missing Python, disabled or untrusted hooks, a plugin
update (which re-asks for trust) and uninstall. Record each with its version, and keep
runs and credentials out of the repository.

Limits: hooks are a workflow guardrail, not an operating-system boundary.

Reference: https://learn.chatgpt.com/docs/hooks

### §RK1738 Codex adoption and distribution documentation

Scope: document the tested Codex installation paths in the product README and
documentation area, updating shared copy sources rather than duplicating divergent
prose. Explain the native local plugin, project-scoped fallback, Python requirement,
workspace binding, hook trust, MCP tools, skills, check/update/uninstall and
troubleshooting. Include exact commands tested by the integration task and a versioned
surface matrix for desktop, CLI, IDE and remote execution.

Explain what changes compared with Claude, which engine and Markdown contracts stay
shared, and how to recover when hooks are disabled, untrusted or unavailable. Retain
CI/pre-commit guidance as backstops and distinguish workflow enforcement from a security
boundary.

Distribution: recheck official OpenAI rules at implementation time. Record whether
bundled hooks are eligible for the public directory and whether local stdio submission
needs publisher approval. Present manual/local installation as a separate verified path.
If public submission remains unavailable, document that limitation without claiming an
upcoming approval or creating a hosted service. Provide a concrete maintainer checklist
for identity, assets, package validation and eligibility if submission is later
authorized.

Acceptance: a clean-room adoption follows the guide successfully; all links and commands
resolve; marketing claims match the compatibility report. No directory submission,
account registration, launch campaign or public publication belongs to this task.

Official references to recheck when implementing:
https://developers.openai.com/plugins/deploy/desktop-only
https://developers.openai.com/plugins/build/plugins

## Block N — Branches (one backlog across parallel branches)
