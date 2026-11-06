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
the top and the design argument below, but it was not measured against that test.
Decided (2026-11-05): the deliverable here is a proposal in visibility's `drafts/`, as
VS4 was for claude-tray, which Alexandre approves before the README changes. It settles:

- The one sentence. Is it what a Claude Code user searches for, or the tool's own vocabulary?
- A demo. claude-tray gained a GIF (VS5); here the moment is the hook denying an `Edit` on
  the roadmap and naming the `add` to call.
- What returns from the old README. The comparison with markdownlint, Vale and Backlog.md
  left with no page in the docs to hold it.
- The visibility strategy keeps roadkeep to cheap actions tied to claude-tray, so this stays
  one pass, not a launch.

## Block J — Validation (whether a person ever tried it)

## Block K — The desktop app (one installer for the reader and the plugin)

## Block L — Product sites on the package

### §RK1729 Both sites on the package's build

The pitch prerenders through the design system's `prerenderSite` (VDS215), keeping only
its `markdown.mjs` converter and a `robots.txt` naming the docs sitemap; its output was
byte-identical.

**The gui landing** (`gui/site/scripts/prerender.mjs`) cannot follow yet: its head
carries `<link rel="alternate" type="text/markdown">` per route, and `prerenderSite` has
no hook for it. Patching the HTML afterwards would leave the manifest's byte counts
stale. The hook belongs in the design system (an option that adds head tags per route);
then the gui moves the same way, and its social card can take `renderOgCard` from
`./vite` in place of `scripts/og-image.mjs`.

**The registry**, outside this repository and committed there: the design system's
`consumers.json` gains both sites (`chrome: "product-site"`, `tone: "cool"`, accent
amber, entries `./site`, `./site.css`, `./tokens.css`, `./vite`), and the hub's
`projects.json` changes roadkeep from slate `148,163,184` to the amber the pitch uses,
`245,158,11`.

Done when the gui has no prerender of its own beyond what `prerenderSite` cannot do,
both sites' tests pass on the built output, and both registries name both sites.
