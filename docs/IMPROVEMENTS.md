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

### §RK1131 The closure that reads one record

RK1123 bound the five fields of `Scope` to the two payloads that carry them, and the
argument was general: a field added reaches one reader and not the other, and nothing
notices. RK1130 then added `wrote` to **six** records — `Insertion`, `StatusChange`,
`Amendment`, `Restatement` and the two the ledger keeps — and to twelve payloads, every
one of them by hand.

Nothing holds any of those. The closure that exists reads one dataclass; the sweep that
needed it read twelve, and the only reason it is right is that a human checked twelve
times.

`test_installing`'s `PLAN_RENAMES` is the shape, and `test_claiming`'s two tables are
the shape refined — a rename map per payload, asserted in **both** directions so a field
with no entry is red and an entry naming no field is red too. What is missing is that
the map exists once per record instead of once per project:

```
RECORDS = {
    "Insertion":    {"entry": "line", "wrote": "wrote", …},
    "StatusChange": {"before": "from", "wrote": "wrote", …},
    …
}
```

Two things need deciding rather than copying. A record carries fields a payload **must
not** have — `document`, `entry`, `prose` are objects, not keys — so the table needs the
`because` column `test_backstop` uses for a code nothing reports, not a silent omission.
And a verb whose payload nests (`ship`'s `scope`, `changelog`, `improvements`) addresses
a key by path, so the map's values are addresses and not names.

What it buys is the next sweep: a seventh field, added by whoever needs it, is refused
by a test rather than caught by a reviewer counting payloads.

## Block C — Query

## Block D — The gate

### §RK1132 One tree, two terminators

Measured across the working tree: **45 of the 56 package modules end CRLF and 11 end
LF**, and eight test files carry **both**. `src/roadkeep/verbs/shipping.py` is one of
the eleven while every file beside it is one of the forty-five.

The cost is not rendering and not bytes. It is that an edit anchored on one terminator
matches nothing in a file that uses the other, **silently** — which is RK1091's defect
one layer down. Twice in one session a scripted patch asserted its anchor and stopped:

```
AssertionError:                     "event": event,
                },
```

The assert is what made it cheap; RK1091 was filed because the same class of edit had
once *succeeded* at writing the wrong bytes. Both times the fix was to notice the file's
endings — a step nothing here declares, so every author rediscovers it.

The repository already owns the file where this is stated: `.gitattributes` carries the
merge driver for the governed files (RK120), so a `*.py text` line lands beside a
declaration this project already made. It changes the **checkout**, which is where the
mixing comes from — the index is normalised to LF either way, so no diff is at stake.

Two decisions worth writing down rather than assuming. Whether the eight mixed files are
normalised in one commit — a diff of every line, once, against a class of silent failure
— and whether anything holds it afterwards: `test_invariants` is where a source-level
property lives, and "one terminator per file" is one it can read off
`surface.modules()`.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
