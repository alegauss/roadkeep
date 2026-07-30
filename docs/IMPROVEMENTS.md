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

### §0.4 The limits, measured against a live corpus (RK20)

§0.1 asked whether the limits are right or the lines are. Shio's 78 active lines answer
it, and the answer is split in a way that only a real backlog could have produced:

| Field | Limit | p50 | p90 | max | Over |
|---|---|---|---|---|---|
| `symptom` | 120 | 58 | 86 | 111 | **0 of 78** |
| `why` | 200 | 481 | 900 | 1251 | **70 of 78** |

The same authors, in the same lines, met one limit every single time and missed the other
89% of the time. So 89% is not evidence that 200 is too small — `symptom` is the control,
and it shows compliance is available. The difference is that "what does not work" is one
clause by construction and a `why` has no natural end, which is L1 stated as a
measurement: the field whose scope is unbounded is the one that needs the bound at the
write path.

And the migration is smaller than §RK20 assumed. **74 of the 78 pointers resolve, and none
dangle**; 67 of the 70 over-length lines point at a section that already exists and already
makes the same argument — compared line-against-section on SH295 and SH309, the `why` is a
recompression of the paragraph, same examples and all. The rationale is not homeless. The
line is a second copy of it, so the edit is compression against a text that is already
written, not authorship.

## Block A — The model

## Block B — Authoring

## Block C — Query

## Block D — The gate

### §RK58 The advice has to be runnable

The denial's whole value is that it names what to call instead. Since RK57 the plugin
runs without `pip install roadkeep`, so the machine that just refused an `Edit` may have
no `roadkeep` on PATH at all — and the refusal still says "Call instead, from the
project root: roadkeep add …". An agent that follows it gets `command not found`, which
is the one outcome worse than the original hand-edit: it teaches that the tool's advice
does not work.

The same plugin that installs the hook installs the four MCP tools (RK24), so on exactly
the machines where the shell command is uncertain, `mcp__roadkeep__add` is present and
carries the field schema. So the refusal names the tool first and the command second,
and says which is which. Both stay, because a project that pip-installed is real too,
and CI has no MCP client.

What the guard cannot know is whether the client actually connected. That is fine for a
message: naming two routes, one of which is certainly there, beats naming one that may
not be.

## Block E — Adoption

### §RK21 Rollout

Turing, Dumont and Cursarei, each with its own `roadkeep.toml`. Four projects sharing
one format is what makes cross-project context transferable; one project with a format
is a preference.

## Block F — The plugin

### §RK59 Four is not the surface

RK24 exposed `add`, `ship`, `pick` and `lint` because the roadmap line named those four,
and the reasoning held at the time: the reads were "one `Bash` call away and cost
nothing to get wrong". RK57 changed the arithmetic. A plugin now installs with no `pip
install` and no PATH entry, so on that machine the four tools are the *only* route that
certainly runs — and starting a task needs `brief`, writing a rationale needs `section
add`, a line that leaves without shipping needs `retire`, unplanned work needs `record`,
and answering "what is open" needs `list`. Every one of those falls back to a shell
command that may not exist.

So the surface is decided by what a task needs end to end, not by what one roadmap line
listed. The four write commands and the reads a session actually calls become tools,
derived from the same parser and the same config as the first four (that machinery is
already generic: a tool is a subcommand name plus which of its arguments an agent may
set).

Two stay out. `init` and `adopt` are what somebody runs *once*, before the project is
governed, and `guard` and `mcp` are the harness's own entry points — a tool that started
a second server inside the first is not a capability.

`section add` is the interesting one, because its prose arrives on stdin: over MCP it is
a string argument bounded by the project's word budget, which is the same refusal by
another door.
