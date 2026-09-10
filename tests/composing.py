"""Every place this tool composes a command, and the one instrument that runs one (RK1209).

Four tasks found the same defect and no test found any of them. RK1149: the retry a refusal
offered had to be retyped. RK1198: the path into a fresh block was six calls discovered one at
a time. RK1205: the `section add` an `add` handed over was refused. RK1207: the refusal for
that family named no verb. Two more since: RK1203, whose `path.missing` door named a verb that
refuses every shipped id, and RK1206, whose pointer door named the task id where the missing
section was the anchor.

Each was covered. `test_the_command_offers_a_follow_up_that_runs` is the sharpest reading —
named for the claim, asserting the sentence was *printed*, never running it, green for as long
as the command it described refused. **Matching a composed command tests the composer against
itself**, which is the whole finding.

Two halves live here, and neither works alone.

:data:`SITES` is the census. `invocation()` is the one function every composed command goes
through, so the population is enumerable by an AST walk, and what this adds is a **reason per
site**: exercised, or unreached and why. The shape `test_surfaces` uses for a write that is
wired or exempted, for its reason — an exemption nobody can see reads exactly like a rule
being kept.

**The work-list is empty** (RK1599). Every site is `run` or `deliberate`, and the sixteen
sittings that emptied it found eleven defects on the way: doors spelled with no invocation,
with no backtick, with an apostrophe for one; a remedy whose command refuses on the state that
emits it; three sentences describing behaviour this tool does not have. Every one was found by
executing a message rather than reading it, which is the argument the file was opened on.
`unreached` stays sayable, because a site added tomorrow is not covered by that history.

:func:`commands` and :func:`runs` are the instrument. The three tasks that fixed one defect
each wrote this by hand — RK1149 executes its retry, RK1198 walks its four steps, RK1207 runs
the chain it names — three copies of one shape, with the next composed command covered by
whichever session remembers to write a fourth.

**Commands are found by their backticks and never by a line prefix**, which is RK1220's
finding taken at the start rather than after: this tool spells its own errors `roadkeep:
refused, …`, so on a machine where the console script is on PATH a prefix scan reads the
preamble as a step and the suite is green or red by whether somebody ran `pip install`.

**The placeholders are filled and never stripped.** `…` and `<its title>` stand for prose only
the author writes (L4), so a harness that dropped them would run a different command from the
one printed; :data:`FILLS` supplies one value per flag, which is what makes the printed
sequence executable without changing it.
"""

from __future__ import annotations

import argparse
import ast
import base64
import json
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from roadkeep.provenance import invocation, quoted
from surface import MODULE, Module, modules, owners, scoped


@dataclass(frozen=True, slots=True)
class Site:
    """One function that composes a command, and how this suite accounts for it."""

    #: `module.py:Function.method`, as :func:`census` spells one.
    where: str
    #: `run` — a test in this suite executes what it composes. `exempt` — it does not, and
    #: :attr:`why` says what makes that honest.
    state: str
    why: str = ""


#: Reasons a site is not executed here. Shared where the cause genuinely is the same, and the
#: point of naming them at all is that a reader can see which: `unreached` is a work-list and
#: `deliberate` is a decision, and a table that spelled both as "no" would hide the difference.
def unreached(state: str) -> str:
    """A row's reason, as **the state its fixture wants** (RK1532).

    Thirty-one rows shared one sentence — *the message needs a state no fixture in this suite
    builds yet* — true of every one of them and useful about none: an item whose cost is
    unstated reads as open-ended, and a work-list of thirty-one open-ended items is a list
    nobody starts at. RK1498 started at it anyway and took four out in a sitting, each wanting
    **two lines of fixture**, which is what that constant had been hiding.

    `_UNMEASURED` in `test_pairs` is the same table one file over and says what each row wants
    — *no `[non_goals]` table*, *no deferred store*, *a clean tree* — which is what makes a row
    there something somebody can act on. So this composes the kind word with the state, one
    spelling of the first and a sentence per row of the second.
    """
    return f"unreached: {state}, and the command it composes is runnable once a fixture has it"
NOT_A_STEP = (
    "deliberate: what it composes is the capture offer, which every refusal ends with and "
    "which is a defect report about the run being tested rather than a step of anything"
)
NOT_A_COMMAND = (
    "deliberate: what it composes is the **engine** and not a call — the notice names what "
    "else answers where a session's tools never arrive (RK1242), so running it as printed "
    "would be running the invocation with no verb"
)
FOREIGN = (
    "deliberate: the command it names is another tool's — git, or the harness — so running "
    "it here would be this suite asserting somebody else's contract"
)
A_REWRITE = (
    "deliberate: it composes nothing — the invocation is read to **find** commands other "
    "sites composed, and what goes back in is a tool name, which is not an argv this CLI "
    "takes (RK1599). `test_serving` holds it in the vocabulary it belongs to: that the "
    "rewrite is the report's own spelling (RK488), that it reaches both argv-bearing keys, "
    "and that a `why` opening with a verb is left alone"
)
UNASKABLE = (
    "deliberate: the branch composing it is the one where `anchors` itself could not answer, "
    "and `anchors` falls back to the file rather than raising — a non-repository, a checkout "
    "with no git and this repository all take the branch that states the address instead "
    "(RK1594). Building the state would mean removing git from the machine or patching the "
    "read, and a mock here is a fixture asserting its own return value"
)


#: Every function in the package that composes a command, and how this suite accounts for it
#: (RK1209). Held total against :func:`census`, so a site added tomorrow is a red here until
#: somebody says which of the three it is.
#:
#: It began at six executed and thirty a **work-list**, which is what the census bought before
#: it bought coverage: four separate tasks had each found one broken composed command by
#: meeting it, and what was missing was not a test for any one of them but the statement that
#: thirty-six others had never been run. The work-list is empty now (RK1599) — every row is
#: `run` or `deliberate` — and the reason a row carries still says which.
SITES: tuple[Site, ...] = (
    # RK1498, the `declare` family (RK1532). `test_composing` takes the scaffold's one door —
    # `add --block A …`, an ellipsis standing for the caller's own fields — and runs it filled,
    # which is the shape `abridged` exists to tell from a blank.
    Site("adopting.py:Created.stated", "run"),
    # RK1264, and the row above it is the same shape one door over: what `declare` composes is
    # the verb the role it just wrote opens, with the id and the reason left as placeholders —
    # so `test_adopting` builds the state and asserts the line, and running it as printed is
    # what a filled argv would have to buy first.
    # The role beside it: `declare deferred` opens the file and names the verb that role exists
    # for. Parsed and not run, the door taking an id the caller chooses (L4).
    Site("adopting.py:Retrofitted.stated", "run"),
    # RK1328, and the row above it one axis over: `declare` now opens an opt-in table too, and
    # what this composes is the verb that table gates — `criterion add` for one, `non-goal add`
    # for the other — with the lead and the reason left as placeholders, which is the same
    # reason the role's row is unreached.
    # And the table (RK1328), which is the one of the three that found something: the door it
    # names refused on a project whose roadmap has no `## Non-goals` heading, and no verb past
    # `init` wrote one. RK1573 closed it at the door rather than in the fixture — writing the
    # first non-goal opens the list, as `criterion add` and `priority add` already did — so
    # this now runs against the bare project, which is the population the table is opened for.
    Site("adopting.py:Opened.stated", "run"),
    # RK1668, the census's own thirteen. `init` on a configured tree sends the caller to the
    # estimate instead, with the backlog file left as theirs — run by `test_adopting`, which
    # substitutes the roadmap it wrote and takes it: `adopt` writes nothing and never fails,
    # so the whole of what the door owes is landing.
    Site("adopting.py:AlreadyConfigured.__init__", "run"),
    # And the row beside it, whose door was `govern {table}.lead <n>` and whose command did not
    # exist: `governing.GOVERNED` held neither opt-in table, so the sentence named a call that
    # exited 2. Bare, which is why nothing had run it. RK1668 pointed it at `config`; RK1673
    # put both tables in `govern`, and `test_adopting` runs the read the door names now.
    Site("adopting.py:TableDeclared.__init__", "run"),
    # RK1223. Run by `test_blocking`, which executes the `--organise` call this refusal names
    # rather than matching it — the reading this whole file is about.
    Site("blocking.py:BlockExists.__init__", "run"),
    # RK1668. The catalogue's two rows, and they went opposite ways: the label declared
    # everywhere but the roadmap names a `block add` that lands, and `test_blocking` runs it.
    # The empty answer named the same call and it refuses by name there — no file carries a
    # heading to read the level off — so that branch now names no door at all, which is the
    # other thing running a printed line can find.
    Site("blocking.py:Catalogue.stated", "run"),
    # RK1668. Two prose files declaring one anchor, where `--role` is the only thing that can
    # resolve it (L4). Run by `test_budgeting` against the doubled fixture it already had:
    # `FILLS` fills the flag, so the printed line is taken as printed.
    Site("budgeting.py:AmbiguousAnchor.__init__", "run"),
    # The `add` that files a task prints the `section add` closing the pointer it just made —
    # composed in `owed_rows` since RK1655, which is where the second door that leaves a
    # pointer owing reads it from. Run by `test_authoring` through `add` and by
    # `test_dismissing` through `reopen`, which is the whole reason it is one function.
    Site("authoring.py:owed_rows", "run"),
    # And the flag that would have needed neither call, refused where this one places no line
    # (RK1655): a reconciling `reopen` has no pointer of its own, so the design belongs to the
    # line already there and the refusal names the verb that writes it. Run by
    # `test_composing`, against the state a crash between two saves leaves.
    Site("dismissing.py:NoSectionHere.__init__", "run"),
    # The two doors under the neighbours an `add` volunteers — `delivered <block>` for the
    # shipped half and `list --block <block>` for the open one (RK1528). Its own site since
    # RK1582 lifted the rows out of `Insertion.added` so `cost --near` could price them
    # without a second spelling, and run by the same tests: every `add` in this suite that
    # ranks anything prints these lines, and `runs()` executes them where it reads that answer.
    Site("authoring.py:volunteered_rows", "run"),
    # RK1498. The `add` that files a capture, run by `test_composing` — and RK1599 is what
    # made it runnable: the path was the one token appended outside `filing`'s `shlex.join`,
    # so a directory with a space split it in two and a Windows separator did not survive
    # being read back. One quoting closes both, the row having been a work-list item about
    # the splitter rather than about the door.
    Site("capturing.py:Capture.filing", "run"),
    # Not work, and never was (RK1579): what it composes is `report … --issue | gh issue
    # create`, a pipeline into another tool — and the half that is ours files a capture about
    # the run being tested, which is `NOT_A_STEP`'s own argument one verb over.
    Site("capturing.py:handoff", "deliberate", FOREIGN),
    # Still not a step, and since RK1635 the one door whose **line** is executed anyway:
    # `argv_after` hands it to each shell on the machine with this tool swapped for an argv
    # echoer, so the quoting is run for real without the report being filed.
    Site("capturing.py:offer", "deliberate", NOT_A_STEP),
    # RK1394. The one door in this family that is takeable here: `--check` prints the delete it
    # would make, and `test_capturing` runs exactly that line — which is the whole reason the
    # offer is composed rather than described, the two runs being one table and one command.
    Site("capturing.py:Sweep.stated", "run"),
    # RK1395, and the one composer both readers that only *report* a stamp now call. Run where
    # the capture recorded where it went, which is when the argv is complete: `test_capturing`
    # types the printed line back and the state moves to the delivery it always was. Where the
    # capture recorded none the repository is a placeholder — the half no project can derive.
    Site("capturing.py:qualifying", "run"),
    # RK1668, and :data:`KEPT_BECAUSE` is why it is a function: a door written into a row of a
    # module-level table is a string no composer reaches, so the `unfiled` reason offered a
    # bare `capture filed <path> --as ID` — a line a caller pastes to `command not found`, and
    # one no sweep here could see. Run by `test_capturing`, which types the printed line back
    # with the id supplied and reads the state move off the next sweep.
    Site("capturing.py:recording", "run"),
    # RK1668. A claim carries a scope and the read prints it back, so a task holding none is
    # offered the declaration — the one door here on a **successful** read of an in-progress
    # line. Run by `test_claiming`, which takes it and reads the path back.
    Site("claiming.py:Claimed.stated", "run"),
    # RK1235. Run by `test_installing`, which executes the read this refusal names — the
    # door that keeps a pinned project's guard from being a wall.
    Site("cli.py:_behind", "run"),
    # RK1236. Run by `test_budgeting`, which executes the ranking this refusal names when a
    # tool it does not serve is asked about.
    Site("verbs/querying.py:_tools_budget", "run"),
    # RK1424. The absent answer names `engines`, which is the verb that reads the copies this
    # one deliberately does not resolve — and `test_budgeting` runs exactly that line, which
    # is the whole reason it is composed rather than described.
    Site("budgeting.py:Skilled.stated", "run"),
    # RK1501. The one door that carries a design's answer past the ship that deletes it, named
    # by `brief` because `--decides` is a flag on the departure and nothing files a decision
    # afterwards. Run by `test_briefing` as far as a door with an author's blank in it can be:
    # filled, and parsed by the real parser — composing the sentence would be the synthesis L4
    # forbids, so the argv is proved and the words stay the caller's.
    Site("briefing.py:_quoting_rows", "run"),
    # RK1513. The absence said before the work rather than at the ship: a line with no criteria
    # is offered the door that writes one, with the two fields left as the author's (L4). Run by
    # `test_briefing`, as far as a door with two blanks in it can be — filled, and parsed by the
    # real parser, which is `_quoting_rows`' own arrangement one row over.
    Site("briefing.py:Brief.stated", "run"),
    # RK1286. Both name `cost --brief`, which `test_budgeting` executes — the gate's finding
    # composes the door with the id substituted and the read composes the sentence a backlog
    # with nothing open gets, and `remedying.Door` is what renders the first for a terminal.
    # RK1482. The summary's own clause about the reader's tooling, and it is `run` for the
    # reason the note beside it is: `test_installing` deletes a page this checkout ships and
    # reads the last line of the report, which is where a skimming reader looks.
    Site("linting.py:_wiring_line", "run"),
    Site("linting.py:_reads", "run"),
    Site("verbs/querying.py:_brief_budget", "run"),
    # RK1238. Run by `test_installing`, which executes the read this note names — the command
    # that says which of three copies answered, on the report that qualifies.
    Site("linting.py:_judged", "run"),
    # RK1242. The one row whose composed text is the engine alone, and it says so.
    Site("guarding.py:Notice.__str__", "deliberate", NOT_A_COMMAND),
    # RK1481. Run by `test_capturing`, which types the MCP name and then reads the note: the
    # composed line is not a step to take but the spelling this CLI used, and the call it
    # names has already run — so what proves it is the answer that came back.
    Site("cli.py:_accepting", "run"),
    # RK1498, over RK1026/RK1032/RK1254. Four shapes, run by `test_composing`: the verb's own
    # surface, the top level's where the flag was typed before a verb, and the position beside
    # it where the flag named an argument taken by order. What kept them out of the census was
    # the instrument — `--help` opens by ending the process, and `runs` read that as a failure
    # until RK1595 taught it to read the code a `SystemExit` carries.
    Site("cli.py:_unrecognised", "run"),
    # RK1498. The read offered for a key this build cannot parse, run by `test_composing`
    # against a config holding one. It did not run: the config load is ahead of every handler,
    # so the door gave back the identical refusal — `engines` now tolerates a broken config
    # the way `guard` and `report` do, needing the root and nothing else (RK1598).
    # RK1670. The refusal every read and write that resolves a file comes through, which named
    # the absence and what stands in its place and not the verb that answers it — `declare`'s
    # own description says *reach for it when a verb refuses over an undeclared role*, and this
    # is that refusal. Run by `test_config`, which takes the door and then makes the read that
    # was refused answer, which is the only proof it was the right command (RK393).
    Site("config.py:Config.path", "run"),
    Site("config.py:_skew", "run"),
    # RK1652, and the door RK1610's refusal did not have: a key this build declares one table
    # away named the header to move it under, by hand, in the file no other verb can read past
    # it. Run by `test_composing`, which reads the refusal off a config holding one, runs the
    # `declare --move` it names, and asks the same config to load — the only proof a door is
    # the right command (RK393).
    Site("config.py:_reject_unknown", "run"),
    # The other half of that write, and the read a caller has next: whether the file parses
    # now, which this write cannot claim on its own — every key it did not touch may be
    # misplaced too. Run by the same test, on the config the move above repaired.
    Site("adopting.py:Moved.stated", "run"),
    # RK1498, over RK10. The read that shows what a count could not take, run by
    # `test_composing` against a roadmap holding one marker-bearing line that is not a task.
    # It was quoted with apostrophes rather than backticks (RK1597) — the same class as a
    # door spelled with no delimiter at all, and invisible to this scan for the same reason.
    Site("counting.py:Census.notes", "run"),
    Site("counting.py:Census.select", "run"),
    Site("history.py:Addresses.withheld", "run"),
    # RK1498. The refusal a `--marker` on the reconciling path gets, run by `test_composing`
    # against a roadmap and a store that both hold the id. What running it found is RK1593:
    # the one command it named refuses there, the store still holding the line, so the same
    # call without the flag is the step before it and the refusal now names both in order.
    # RK1670, the same defect one verb over. `dismissing.NoStore` cites this class for its rule
    # and carries the door RK1264 built; this one still read out a toml key and a skeleton by
    # hand, which over MCP is the edit the guard denies. Run by `test_deferring`, which opens
    # the store the refusal names and then makes the refused `defer` land.
    Site("deferring.py:NoStore.__init__", "run"),
    Site("deferring.py:NoPlacement.__init__", "run"),
    # RK1618. The second store's four, all run by `test_composing`: the refusal a project with
    # no store meets and the verb that opens one, the `reopen` row every filed entry ends with,
    # the two reads an id nobody can find otherwise answers with, and the same `--marker`
    # refusal one file over — which is `NoPlacement`'s sentence and its two steps in order.
    Site("dismissing.py:NoStore.__init__", "run"),
    Site("dismissing.py:NoPlacement.__init__", "run"),
    Site("dismissing.py:Dismissal.stated", "run"),
    Site("showing.py:_ruled_out", "run"),
    # RK1498, RK327's offer. The rank is the half a pause cannot keep, so a resume names the
    # command that puts the line back in the order rather than choosing a place for it —
    # run against a roadmap that declares one, an offer nothing refuses being an offer only
    # the reader who pasted it would ever find broken.
    Site("deferring.py:Resumption.requeue", "run"),
    # RK1498, the outline family (RK1532). Two doors, both run by `test_composing`: the one a
    # block spanning two families prints, and the narrowing a wide listing names. The state its
    # row guessed was a git history; the reading wanted only an outline (RK1577).
    Site("history.py:Addresses.stated", "run"),
    # RK1498, over RK1140. The note a free top-level owes, run by `test_composing` — which
    # found the sentence false: it said `add --ref <it>.1` refuses until a section exists, and
    # the line lands (RK1598). It now names the command that acts and says what the gate says
    # meanwhile, which is `ref.unresolved` and not a refusal at the door.
    Site("history.py:opens", "run"),
    # RK1668. The close every line git already names is still open under: `unclosed` finds the
    # commits and the door is the departure they were leading up to. Run by `test_history`,
    # which substitutes the id off the row above it — the one token no table fills, being the
    # caller's own line — and reads the ledger entry the ship then writes.
    Site("history.py:Unclosed.stated", "run"),
    # RK1230. Run by `test_installing`, which asserts the line it composes *is* the copy the
    # registry names — the one composed command here whose whole point is being pasted.
    Site("installing.py:Engines.invoke", "run"),
    # RK1561. The sentence the line above does not carry: `--invoke` falls through a
    # declaration this command cannot read and prints the copy that is answering, which is
    # correct and silent about the harness starting something else. Run by `test_installing`,
    # which reads it off stderr beside the one-line answer on stdout.
    Site("installing.py:Engines.unread", "run"),
    # RK1487. The copy a refusal does not mention, and the read it names is what says which
    # surfaces are still to write — run by `test_installing`, which lands a vendor into a tree
    # whose `.claude` is a file and reads the sentence the exception above it is not about.
    Site("installing.py:Vendored.stranded", "run"),
    # RK1438. The five lines a write ends with, which name the verbs a day uses with the id
    # and the sentence left as placeholders — the same shape as `Retrofitted.stated` above,
    # and unreached for the same reason: the fixture here is an adopter with no line filed, so
    # a `brief`, a `show <id>` or a `ship <id> --why …` has nothing to run against yet.
    # RK1498, the orientation (RK1534). Run against a checkout beside a bare project, which
    # is what found the defect: the five lines named five commands that all refused there,
    # and the sentence saying what has to happen first was not among them. What is asserted
    # is the **order** — `init` first on a tree that governs nothing — because the rest are
    # verbs named in prose rather than a path (RK1198's distinction, the other way round).
    Site("installing.py:Plan.orientation", "run"),
    # RK1498. Both verdicts, run by `test_installing` against the state each is about: a
    # project whose surfaces are not what this engine writes, and a wired one being taken
    # apart. Each door is run and the check that offered it is then clean, which is the only
    # proof it was the right command — a verdict whose remedy leaves the verdict standing is
    # the loop RK393 named.
    Site("installing.py:Plan.verdict", "run"),
    Site("installing.py:Removal.verdict", "run"),
    # RK1549. The `kept` row that spent RK1514 handing its last step back in English — *delete
    # the directory* — now names the verb, and `test_composing` runs it: the copy is measured,
    # the door reclaims it, and the row is gone from the next report. Which is the only proof
    # a `kept` row naming a command is better than one naming none.
    Site("installing.py:removal", "run"),
    # RK1498. A driver is wired per governed file, so a tree declaring none has nothing to
    # register — run by `test_composing` through `install --register-merge`, which is the verb
    # that reaches it and not the one this row named. The sentence said the four surfaces did
    # not depend on it, and this refusal sits above the first write, so none of them was
    # there to not depend on it (RK1598).
    Site("installing.py:_governed", "run"),
    # RK1498, the fifth surface's row. Three states and three doors, run by `test_composing`
    # against a governed project in a repository: unwired, where both commands run in the order
    # printed and the second was spelled with no invocation at all; already wired, where one is
    # a write with nothing to write and the other a read whose 1 is its answer; and blocked,
    # where the sentence predicts a refusal and is held to it. The remedy is run and the row
    # re-read, which is the only proof it was the right command (RK393).
    Site("installing.py:plan", "run"),
    # RK1498. The derived block, both branches — run by `test_composing` against a README the
    # governed files no longer render. The stale one composes the rewrite and closes itself;
    # the half-marked one composes nothing, its message being `NoMarkers`', and what that
    # found is RK1591: the remedy under it is a `run` whose command refuses on the state that
    # emits the finding, so `repair` dispatches a door it cannot open. Named, not asserted
    # away — the row's flag now follows the finding, which is the half that was decidable.
    Site("linting.py:_projections", "run"),
    # RK1551. The read a suppressed note names, run by `test_scoping` against a design that
    # quotes its constraint's lead: `non-goal list` is the one register reporting the
    # suppression, and naming it is the whole of what the row owes a reader.
    Site("linting.py:_reaching", "run"),
    # The gate's own report, which is where every door below is rendered for a terminal.
    Site("linting.py:_report_rows", "run"),
    # RK1498. A ceiling under every tool, so the finding fires and the ranking it names is the
    # only route to the number — there being no file a reader could open to see the cost.
    Site("linting.py:_served", "run"),
    # RK1498. Both codes, one door: a surface behind the engine answering and one the project
    # never had. Installed from the checkout this process is, because that is what `staleness`
    # compares against — vendoring from a copy would report the fixture's own drift as the
    # state under test. The write runs and the notes go, which is RK393's half.
    Site("linting.py:_wired", "run"),
    # The absent half of that pair, its own function since RK1565 because the sentence is read
    # twice — as the row's message and as what its siblings share — and two spellings of one
    # sentence is a fold that stops folding. Same door, run by the same tests.
    Site("linting.py:_missing", "run"),
    # RK1498, over RK348/RK1152. A ship ticks its dependents and a ✅ is two characters wider,
    # so the line that overflows is somebody else's — run by `test_composing` against a
    # dependent with one character of room, where the door is the edit on **that** line and
    # taking it makes the refused ship land.
    Site("markers.py:_naming_the_lines", "run"),
    Site("merging.py:Wiring.repairs", "deliberate", FOREIGN),
    Site("merging.py:_spent", "deliberate", FOREIGN),
    # RK1512. The store no tier offers, and the read that opens it — run by `test_picking`,
    # which puts a line in the store and executes the listing the row names. `resume` rides in
    # the same sentence and is not run: ending a pause is a decision, and a sweep that made one
    # would be this suite taking the judgement the row deliberately leaves to the reader.
    # RK1668, the queue's two refusals and its three doors. A project with no priority heading
    # is offered the write that opens one; one whose order is still the config key is offered
    # the migration, which was bare in the same function and invisible to `unprefixed` the
    # moment the branch beside it became a site; and the migration with nothing to move names
    # the same write. All run by `test_queueing`, against the two states it already builds.
    Site("queueing.py:NoQueue.__init__", "run"),
    Site("queueing.py:NothingToMigrate.__init__", "run"),
    Site("rendering.py:_set_aside_rows", "run"),
    # RK1490. The two doors under a line the ranking set aside for a requirement — take the
    # whole thing, or take the half that does not need it — run by `test_picking`, which
    # executes the `status <id> 🛠` this composes and reads the marker it moved.
    Site("rendering.py:_withheld_rows", "run"),
    # The two that render a remedy, and so every door the gate offers.
    Site("remedying.py:Door.command", "run"),
    Site("remedying.py:Door.quoted", "run"),
    # The other half of a decision, named by every `ship --decides` (RK1361).
    Site("rendering.py:_decided_body_rows", "run"),
    # RK1498. The offer a departure's event line makes when the block it left is empty, run by
    # `test_composing`: the closure path takes the last line out and `block drop A` runs.
    Site("rendering.py:_event_rows", "run"),
    # The stairs RK1198, RK1205 and RK1207 each walked by hand.
    # The address a decision's body needs where the file numbers its own headings (RK1363).
    Site("shipping.py:DecidesUnaddressed.__init__", "run"),
    # RK1378: the read it names is the branch where `anchors` could not be read, and the one
    # `test_the_refusal_names_the_free_address_and_not_only_the_family` exercises is the other
    # — where the address is stated and no command is composed at all.
    # RK1668. The scheme where the anchor *is* the id, so the move belongs to the verb that
    # takes both ends: `test_sections` runs the `renumber` and reads the line, the heading and
    # the deps at their new address. The `section drop` beside it is the doubled-anchor answer
    # and was bare in the same sentence — prefixed with the anchor now, and parsed rather than
    # taken, `--role` being which of the two files holds the copy (L4).
    Site("sections.py:AnchorIsId.__init__", "run"),
    # RK1668. The read a `section find` that carries nothing names, which is the whole of what
    # an empty answer owes: run by `test_sections` with an anchor the same project declares.
    Site("sections.py:Found.stated", "run"),
    Site("sections.py:NotASibling.__init__", "deliberate", UNASKABLE),
    Site("sections.py:UnknownParent.__init__", "run"),
    Site("sections.py:_the_path_into", "run"),
    # RK1498, RK363's read. Both listings, run by `test_composing` against one outline: a
    # leading segment naming a live family narrows to it, and one naming none gets the whole
    # outline — two reads from one refusal, and a narrowing on a family the file does not
    # declare would exit 2 in the reader's hands.
    Site("sections.py:_where_a_top_level_is", "run"),
    Site("sections.py:_where_the_anchor_is", "run"),
    Site("serving.py:_rerouted", "deliberate", A_REWRITE),
    # RK1272, run by `test_composing` (RK1498). Both name a read rather than a repair, and
    # the fixture each wanted was one line: a scaffolded project for the address that is a
    # name, and a bare directory for the tree with no table. The second row's state was
    # wrong as well as unbuilt — it named a corpus reading, and the command is composed on
    # the branch before any reading happens.
    Site("governing.py:NoSuchKey.__init__", "run"),
    Site("governing.py:govern", "run"),
    # RK1498. Three departures that cannot happen, each run by `test_composing` against the
    # state that produces it: an id the ledger holds whole beside a ⏳ line, whose door is the
    # closure (the one state RK1045 made it true of); a line the deferred store still names,
    # whose door removes that copy; and two tasks sharing an address, whose door gives the open
    # one its own. Two lines of fixture each, which is what "unreached" was hiding.
    # RK1511. The one refusal a fold has, and the door it names is the *other* answer about
    # where the work went: run by `test_retiring`, which folds into a line that has shipped and
    # then executes the supersession the message offers.
    # RK1668. Two entries under one id that do not say the same thing, and the two doors are
    # alternatives — one entry goes, or the other gets its own address — so `test_recording`
    # runs each on its own tree, which is the only reading that says both are real.
    Site("shipping.py:NotRedundant.__init__", "run"),
    Site("shipping.py:NotAbsorbable.__init__", "run"),
    Site("shipping.py:AlreadyRecorded.__init__", "run"),
    Site("shipping.py:AlsoPaused.__init__", "run"),
    # RK1498, over RK441. The `near` row's two reads, run by `test_composing` against a block
    # that has recorded something — the state the count is about, a listing whose `is all 0`
    # never opened a file answering the same on a ledger of two hundred.
    Site("shipping.py:Delivered.__str__", "run"),
    # RK1624. The refusal a `--open` with no sentence to rank against gets, which names the two
    # halves as they stand — the listings this widening exists to be a ranking *instead* of.
    Site("verbs/shipping.py:_delivered", "run"),
    Site("shipping.py:Divergent.__init__", "run"),
    # RK1281, run by `test_composing` (RK1498). Two doors and they are alternatives, so each
    # is taken on its own tree and each has to make the refused ship land. The `govern` is the
    # one that is not a complete argv — which number a wider limit should be is the reading
    # that verb takes — and the `restate` beside it was spelled with no invocation at all,
    # which is why the sweep saw one door where there are two (RK1596).
    Site("shipping.py:InheritedClaim.__init__", "run"),
    # RK1269. Run by `test_composing`, which executes the `declare decisions` this refusal
    # names and then makes the `ship --decides` land — the whole reading of this file, on the
    # one door where the remedy is a role a project has not opened yet.
    Site("shipping.py:NoDecisions.__init__", "run"),
    Site("shipping.py:_elsewhere", "run"),
    # RK129 through the same two lines of ledger: retiring an id whose half is recorded would
    # replace the entry holding it, and the exit is the completion — which `test_composing`
    # now runs, RK1138 being the task that found this door naming something that was not one.
    Site("shipping.py:PartRecorded.__init__", "run"),
    # RK1498, one fixture family in (RK1532). The one door here that rides a **successful**
    # write: `test_composing` takes the partial, then the completion it printed — which is
    # what found the two defects in it, a bare `finish` no backtick scan could see and a
    # `ship <id>` that refused as printed for want of the `--why` a completion may not inherit.
    Site("shipping.py:Partial.stated", "run"),
    # The refusal beside it, same fixture: one id carries one partial and then the completion,
    # so a second is two answers about one piece of work. Parsed and not run — the door is an
    # `add` whose symptom, why and block are the author's own readings (L4).
    Site("shipping.py:SecondPartial.__init__", "run"),
    # RK1498. Run by `test_showing`: a caller who addressed a section is sent to the verb that
    # prints one, and what makes naming a verb one word away worth anything is that the word
    # is right — so the door runs and the section it prints is the one that was asked for.
    Site("showing.py:_instead", "run"),
    Site("showing.py:_paused", "run"),
    # RK1498, over RK1048. An entry is keyed by the id it leads with, so the second one it
    # delivered is invisible to the parse and visible to history — run by `test_composing`
    # against a committed ledger, a refusal claiming a commit wrote an id being a message
    # about nothing on a tree with none.
    Site("showing.py:_where_it_went", "run"),
    # The refusal beside it, on the same fixture: `--block` and `--family` are two questions,
    # and both doors it names now run — which is what found the second half spelling its
    # placeholder `<one of them>`, a token any shell splits (RK1548).
    Site("verbs/querying.py:_anchors", "run"),
)

#: The three states a site can be in. `run` is coverage; the other two are both "not run" and
#: are kept apart because only one of them is work somebody should do.
STATES = ("run", "unreached", "deliberate")


#: What stands in for prose in a composed command, by the flag it follows (RK1209). One value
#: per flag and not per verb: the same `--title` is filled the same way wherever it appears,
#: and a table keyed by verb would be a second place to remember a flag exists.
#:
#: Every value is deliberately *minimal and legal* — enough to pass the field's own validation
#: and nothing more — because what is being tested is whether the command lands, not whether
#: this file can write prose.
FILLS: dict[str, str] = {
    "--title": "A title",
    "--body": "Prose enough to matter, and a sentence that ends.",
    "--why": "Because of a reason.",
    "--symptom": "A symptom plainly long enough to read",
    "--reason": "Because of a reason.",
    "--lead": "No second backlog.",
    "--part": "the first half",
    # RK1668. The one door whose blank is a **choice between two files** and not prose: an
    # anchor two prose roles declare is resolved by the caller naming which they mean, and
    # `improvements` is the role every fixture here declares.
    "--role": "improvements",
}

#: The tokens this tool prints where the author's own words go. Both spellings: `…` is what
#: `remedying.BLANK` renders and `<…>` is what a refusal's prose spells.
_BLANKS = re.compile(r"^(…|<[^>]*>|\"<[^>]*>\"|'<[^>]*>')$")

#: A backticked span, which is how every composed command in this tool is delimited.
_SPAN = re.compile(r"`([^`]+)`")


def census() -> tuple[str, ...]:
    """Every function in the package that calls `invocation()`, by address.

    Derived and never listed, for the reason `surface.py` exists: a second view of the
    population agrees with the first right up to the moment somebody adds a site, which is the
    single moment either of them matters.

    **And this is the whole of what `SITES` is total over** (RK1605). A door composed *without*
    the prefix is not a function calling `invocation()`, so it is not a site, is not a row, and
    is covered by nothing here — which RK1498's closing sentence, *every site is run or
    deliberate*, does not say on its own.

    Met rather than theorised. `sections._WAYS_OUT["amend"]` printed `section move {anchor}
    --to <free anchor>` at every over-long amend from RK1034 on, and appeared in no census. It
    was bare, so nothing found it; its placeholder held a space, so nothing could have run it;
    and it offered the one act `section move` refuses by name (RK377). Three defects in one
    clause, none reachable by the sweep built to find exactly this — and it surfaced only when
    RK1548 added the invocation, which made it a site, which made the census red.

    Widening this to every backticked verb is the wrong repair and RK1590 measured why: 421
    such spans lead with a verb and carry no prefix, and most are prose — `add --section` named
    as a flag family, `pick` as a verb being discussed. :func:`beyond` is that population, and
    :func:`inconsistent` and :func:`unprefixed` are the two parts of it a rule can decide —
    the author's own two spellings inside one message, and a span carrying a field an author
    fills, which is what a caller substitutes and a flag family never has (RK1640).
    """
    #: `surface.scoped` since RK1647, where this built its own name stack: three walkers in
    #: this suite each rebuilt *which function is this node in*, and the third spelled the
    #: address differently — only functions, and the last name rather than the dotted path — so
    #: a method inside `Created` was `stated`, a name several classes in one module share.
    found: list[str] = []
    for module in modules():
        for where, node in scoped(module.text):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id == "invocation":
                address = f"{module.where}:{where}"
                if address not in found:
                    found.append(address)
    return tuple(sorted(found))


def commands(said: str) -> tuple[list[str], ...]:
    """Every command a message composes, as argv, with this engine's own prefix removed.

    Backticks and not line prefixes (see the module docstring): `roadkeep: refused, nothing
    written:` begins with the invocation wherever the console script is installed, and a scan
    that took it for a step failed on a machine whose only difference was a `pip install`.

    A span that is not a command — a flag being named, a file being quoted — is skipped rather
    than refused: a message is prose and backticks are how it emphasises anything.

    **And the prefix has to end where a word ends** (RK1498). `startswith` alone read
    `` `roadkeep.toml` `` as `roadkeep` plus the verb `.toml`, which is RK1220's own failure one
    step in: the config file is named after the tool, so every message that quotes it composed
    a command. Found by pointing this at the `install` note that names it — a message that had
    never been run, which is the population RK1498 is about.
    """
    prefix = invocation()
    out: list[list[str]] = []
    for span in _SPAN.findall(" ".join(said.split())):
        if not span.startswith(prefix):
            continue
        rest = span[len(prefix):]
        # A verb is a separate word: `roadkeep.toml` is a filename and `roadkeep-launch.py` is
        # a script, and neither is this tool being called.
        if rest and not rest[:1].isspace():
            continue
        rest = rest.strip()
        if not rest:
            continue
        try:
            argv = shlex.split(rest)
        except ValueError:
            # An unbalanced quote is prose, not a command this could have run.
            continue
        if argv:
            out.append(argv)
    return tuple(out)


def filled(argv: list[str], *, continuation: bool = False) -> list[str]:
    """The same command with the author's placeholders replaced by legal values (RK1209).

    Filled and never stripped: `add --why …` with the flag removed is a *different* command,
    and one that would be refused for a reason this sweep is not about.

    A dangling flag — the trailing `…` in `add --block Z --ref XXI.1 …`, which stands for the
    rest of a call rather than for one field — is dropped, because there is no flag in front
    of it to fill from.
    """
    out: list[str] = []
    for index, token in enumerate(argv):
        if not _BLANKS.match(token):
            out.append(token)
            continue
        before = argv[index - 1] if index else ""
        if before in FILLS:
            out.append(FILLS[before])
        elif before.startswith("--"):
            # A flag this table does not know: better to fail loudly in the sweep than to
            # quietly drop the argument and run something else.
            out.append(f"<unfilled {before}>")
        elif not continuation:
            # A blank in a *positional*, which the loud branch above never saw (RK1339). The
            # drop below is right only where the ellipsis stands for the rest of the caller's
            # own call, and that is a property of where the command was read: `runs` takes
            # them out of refusal prose and asks `abridged` which kind it has, while a remedy
            # door has no such ellipsis and no such question. Dropping one there turns
            # `block add … --title …` into `block add --title A title` — a different command,
            # which is exactly what the branch above refuses to let happen to a flag.
            out.append("<unfilled positional>")
        # else: a bare ellipsis standing for "and the rest", which has nothing to fill.
    return out


def abridged(argv: list[str]) -> bool:
    """Whether this printed command ends in a bare `…` meaning *and the rest of your call*.

    The one place a composed command is deliberately **incomplete**, and telling it apart is
    what keeps this sweep honest. A stair's retry reads `add --block Z --ref XXI.1 …`: the
    ellipsis stands for the caller's own `--symptom` and `--why`, which they already typed and
    the refusal is not going to repeat. Filling those in is right there and is *hiding a
    defect* anywhere else — a composed command that simply forgot a required flag is precisely
    what this file exists to catch, so the two cases may not share a rule.
    """
    return bool(argv) and bool(_BLANKS.match(argv[-1])) and not argv[-2:-1][0].startswith("--")


def supplied(argv: list[str], *, template: bool = False) -> list[str]:
    """The same command with a body added where omitting one sends it to the pipe (RK1209).

    Read off the parser's own :class:`~roadkeep.serving.Prose` declaration and never from a
    list here (RK171): which verbs take a paragraph off stdin is a claim the subparser makes,
    and a second copy of it would drift the moment a fourth one did.

    Not a change to the composed command, which is the distinction that matters. A refusal
    printing `section add I.1 --title "<its title>"` is *correct*: the body arrives on stdin,
    and a human running it types one. What this suite has is no stdin — under pytest the
    stream is the runner's and cannot be made strict UTF-8 (RK455) — so the harness supplies
    what a person would, rather than the sweep reporting a refusal about its own environment.
    """
    from roadkeep.cli import build_parser  # noqa: PLC0415 - the suite's own edge

    verbs = next(
        one for one in build_parser()._actions  # noqa: SLF001 - argparse exposes no reader
        if getattr(one, "choices", None) and one.dest == "command"
    ).choices
    parser = verbs.get(argv[0]) if argv else None
    for token in argv[1:]:
        # Subparsers and never *any* action carrying `choices`: an option declaring a value
        # set — `--role`, `--marker` — carries a list, and `.get` on it raises. Found by the
        # first composed command whose verb has one (RK1236), which is the same descent
        # `serving._parsers` makes and the reason it names the type.
        nested = next(
            (
                one.choices.get(token)
                for one in getattr(parser, "_actions", ())  # noqa: SLF001
                if isinstance(one, argparse._SubParsersAction)  # noqa: SLF001
            ),
            None,
        )
        if nested is None:
            break
        parser = nested
    declared = getattr(parser, "get_default", lambda _: None)("reads_stdin") or ()
    for prose in declared:
        flag = f"--{prose.dest.replace('_', '-')}"
        if not prose.omitted or flag in argv or f"{flag}-file" in argv:
            continue
        gate = getattr(prose, "gated_by", "")
        if gate and f"--{gate.replace('_', '-')}" not in argv:
            # `add` reads only where a section was named: an `add` with no rationale must
            # never block on a pipe, so there is nothing to supply.
            continue
        argv = [*argv, flag, FILLS.get(flag, "Prose enough to matter, and it ends.")]
    if not template:
        return argv
    # The caller's own fields, which a template stands in for and never states. Read off the
    # parser's `required`, so what is supplied is exactly what the printed line assumed the
    # caller still had — and never more, a flag this table cannot fill being a red rather than
    # a silent omission.
    for action in getattr(parser, "_actions", ()):  # noqa: SLF001 - argparse exposes no reader
        flags = getattr(action, "option_strings", ())
        if not action.required or not flags or any(one in argv for one in flags):
            continue
        argv = [*argv, flags[0], FILLS.get(flags[0], f"<unfilled {flags[0]}>")]
    return argv


def runs(root: Path, said: str, *, expect: int = 0) -> tuple[list[str], ...]:
    """Execute every command a message composed, in order, against ``root``.

    In the order printed, which is half the claim: RK1198's finding was a *path*, and a
    sequence whose second step refuses is a sequence, not a set.

    Returns what it ran, so a caller can assert the shape as well as the outcome.
    """
    from roadkeep.cli import main  # noqa: PLC0415 - the suite's own edge

    ran: list[list[str]] = []
    for printed in commands(said):
        # The one caller whose trailing ellipsis may be a continuation, so the one that says
        # so: `abridged` answers it for this text, and `filled` no longer assumes it (RK1339).
        continuation = abridged(printed)
        argv = supplied(filled(printed, continuation=continuation), template=continuation)
        if argv[:1] == ["report"]:
            # The capture offer, which every refusal ends with and which is not a step of
            # anything: running it would file a defect report about the run being tested.
            continue
        try:
            code = main(["-C", str(root), *argv])
        except SystemExit as ended:
            # `--help` is a door like any other and argparse opens it by ending the process
            # (RK1595). Read as the code it exits with, because that is what a caller pasting
            # the line sees — refusing to run it would leave every `see  <verb> --help` row
            # in this tool as a command nothing has executed.
            code = 0 if ended.code is None else int(ended.code)
        assert code == expect, (argv, code)
        ran.append(argv)
    return tuple(ran)


#: The shells a maintainer pastes a door into, on the platforms this project is developed and
#: gated on (RK1635). Every one absent from a machine is skipped by :func:`argv_after`, which is
#: what `tests/corpora` does with its pins: an instrument that refuses to run where a shell is
#: missing is one that runs nowhere.
SHELLS = ("cmd", "powershell", "sh")

#: What each shell is pointed at instead of this tool: a program that says which argv arrived.
#: Not `cli.main`, because the reader under test is the **shell** — routing the line back
#: through `shlex.split` is the assumption RK1580 was invisible behind.
_ECHOER = "import json, sys\nsys.stdout.write(json.dumps(sys.argv[1:]))\n"


def argv_after(shell: str, door: str, *, at: Path) -> list[str] | None:
    """The argv `shell` delivers when `door` is pasted at its prompt, or None if it is absent.

    RK1635. Every other reader in this file is `shlex.split`, which is a Python reading of a
    line a **shell** is going to read: a door quoted wrongly for a shell round-trips through it
    perfectly, so the sweep was green for the year RK1580's defect stood, and the only thing
    that found it was a person typing the printed line into three terminals.

    The tool's own name is swapped for :data:`_ECHOER` and **every other byte of the door is
    left as printed** — the quoting is the whole subject, so a harness that re-quoted anything
    after the prefix would be testing itself again.

    Each shell needs its own way to be handed a *line*, and none of that is the door's:

    * `cmd /s /c "<line>"` is the documented deterministic form — strip the outer pair, take
      the rest as typed — and it is passed as one string so Windows hands `CreateProcess` the
      line rather than an argv `subprocess` re-quoted.
    * PowerShell gets the script base64 UTF-16, because its own `-Command` splitter strips the
      quotes off its command line before the parser ever sees them, and its stdin is decoded
      in the console codepage. Both are transport and neither is the parser this is about.
      The `&` is the call operator a quoted executable path needs there.
    * `sh -c <line>` takes it as one argument, which is already a line.
    """
    exe = shutil.which(shell)
    if exe is None:
        return None
    script = at / "echoargv.py"
    script.write_text(_ECHOER, encoding="utf-8")
    prefix = invocation()
    assert door.startswith(prefix), door
    # Quoted, because a POSIX shell reads every backslash of a Windows path as an escape —
    # `provenance.quoted`'s own first reason, applied to the one token this harness supplies.
    line = f"{quoted(sys.executable)} {quoted(str(script))}{door[len(prefix) :]}"
    read = {"capture_output": True, "text": True, "encoding": "utf-8", "errors": "replace"}
    if shell == "cmd":
        got = subprocess.run(f'{exe} /s /c "{line}"', **read)  # type: ignore[call-overload]
    elif shell == "powershell":
        script_text = base64.b64encode(f"& {line}".encode("utf-16-le")).decode("ascii")
        got = subprocess.run(  # type: ignore[call-overload]
            [exe, "-NoProfile", "-EncodedCommand", script_text], **read
        )
    else:
        got = subprocess.run([exe, "-c", line], **read)  # type: ignore[call-overload]
    assert got.returncode == 0, (shell, line, got.stdout, got.stderr)
    return list(json.loads(got.stdout.strip()))


#: A placeholder — `<…>` with no quote inside it. The **space** is tested separately rather
#: than written into the pattern (RK1548): `<[^>"']*\s[^>]*>` says the same thing and
#: backtracks, which took this sweep from milliseconds to minutes over the package's longest
#: strings. One character class and one `in` is the same reading, linear.
_HOLDER = re.compile(r"<[^>\"']*>")


def spoken(module: Module) -> list[tuple[int, str]]:
    """Every string one module **composes**, docstrings left out (RK1548).

    Read off the AST and never off the file's text, which is what makes this a reading of what
    the tool prints. Raw text puts a backtick in a comment and a backtick in an f-string on the
    same footing, and the span between them is a sentence nobody wrote: pointed at
    `sections.py` that way, the first attempt at this check reported a span running from a
    comment about free anchors into the code three functions later.

    A `JoinedStr` is flattened with `{}` where its expressions are, so a door composed from
    fields is read as the shape it prints — `amend {id} --why …` is the command, and the id it
    interpolates is not the question.

    Docstrings are prose about the code and excluded on purpose: a flag named in a sentence is
    correct there, which is the line RK1548 draws and the reason this is not a text search.
    """
    tree = ast.parse(module.text)
    prose = {
        id(first.value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        for first in (next(iter(getattr(node, "body", ())), None),)
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
    }
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) not in prose:
                found.append((node.lineno, node.value))
        elif isinstance(node, ast.JoinedStr):
            found.append((
                node.lineno,
                "".join(
                    part.value if isinstance(part, ast.Constant) else "{}"
                    for part in node.values
                ),
            ))
    return found


@lru_cache(maxsize=1)
def _verbs() -> frozenset[str]:
    """Every subcommand this CLI declares, built once.

    Cached for `_reading`'s reason one file over: :func:`commanded` is asked of every string
    the package composes, and building the parser per span took this sweep from a second to
    two minutes — the same shape as the regex above it, and the same fix.
    """
    from roadkeep.cli import build_parser  # noqa: PLC0415 - the suite's own edge

    return frozenset(
        [one for one in build_parser()._actions if getattr(one, "choices", None)][0].choices  # noqa: SLF001
    )


def commanded(said: str) -> list[str]:
    """Every backticked span in one string that **is a command**, flattened to one line.

    Wider than :func:`commands`' boundary, and RK1548 is why: that one takes spans opening
    with the invocation, because it goes on to run them. This one asks whether a printed door
    is *runnable as printed*, and a door spelled without the prefix is still a door — the one
    live site this found was `section move {anchor} --to <free anchor>`, bare and unquoted at
    once, which the narrower reading walked straight past.
    """
    verbs = _verbs()
    prefix = invocation()
    out: list[str] = []
    for span in _SPAN.findall(said):
        flat = " ".join(span.split())
        words = flat.split()
        if words and words[0] == prefix:
            words = words[1:]
        if words and words[0] in verbs:
            out.append(flat)
    return out


def loose(said: str) -> list[str]:
    """Every command in this string whose placeholder holds an unquoted space (RK1548).

    `shlex.split` takes `<what` as the value and hands the verb the rest as stray arguments, so
    the printed line is a *different* command — and nothing here caught it: `_BLANKS` accepts
    both spellings and only the quoted one survives a split, so the unquoted placeholder never
    matches and `filled`'s loud `<unfilled --flag>` branch never sees it either.

    Checked from the **string alone**, which is what makes it worth having beside `SITES`: a
    span holding one is wrong whether or not any test reaches the site that prints it, so one
    pass covers the sites nothing runs as well as the ones it does.
    """
    found: list[str] = []
    for flat in commanded(said):
        for hit in _HOLDER.finditer(flat):
            if " " not in hit.group(0):
                continue
            quoted = flat[: hit.start()][-1:] in ('"', "'") and flat[hit.end():][:1] in (
                '"',
                "'",
            )
            if not quoted:
                found.append(flat)
                break
    return found


def inconsistent(said: str) -> list[str]:
    """The verb-leading spans of one message that a **sibling door** says should be doors.

    RK1590's answer, and the one the design's two options each ruled out. A gate rule that
    every backticked verb carries the invocation refuses prose that legitimately names a flag —
    421 spans in this package do; a rule over "spans that reach a printed message" needs a
    static reading of which strings those are, and 126 of them are inside a composer already.
    Neither decides which spans were *meant* to be doors, which is what a scan cannot know.

    This does not try. It reads the one tell RK1589 actually had: `install --register-merge`
    was bare **in a sentence whose sibling door carried the invocation**. Within one message,
    a span that runs and a span that names a verb are told apart by the author already — so
    what is checkable is that they agree, and a message naming verbs throughout is left alone.

    A door is the invocation **plus a verb**, which is `commands`' own boundary: a bare
    `` `roadkeep` `` is the tool's name being discussed, and three messages in `installing`
    pair one with the word `install` in prose. Counting those would make the rule fire on the
    sentences it exists to permit.
    """
    verbs = _verbs()
    prefix = invocation()
    spans = [" ".join(one.split()) for one in _SPAN.findall(said)]
    doors = [
        one
        for one in spans
        if one.split()[:1] == [prefix] and one.split()[1:2] and one.split()[1] in verbs
    ]
    if not doors:
        return []
    return [one for one in spans if one.split()[:1] and one.split()[0] in verbs]


def _owners(module: Module) -> dict[int, str]:
    """Line number to the address of the function holding it, for one module.

    `surface.owners` since RK1647, where this was the second of three walkers rebuilding the
    same scope stack. What is left here is the one thing that is this file's: a line in **no**
    function is left out rather than answered `<module>`, so every caller's `owner.get(lineno,
    module.where)` falls back to the file — which is how a message composed at module level is
    addressed in `beyond` and `unprefixed`.
    """
    return {
        line: where
        for line, where in owners(module.text, prefix=f"{module.where}:").items()
        if not where.endswith(f":{MODULE}")
    }


def dispatchable() -> tuple[str, ...]:
    """Every finding code whose remedy is a command this tool can be asked to run (RK1641).

    The population a door sweep is a property *over*, derived from the table rather than
    counted in prose. `fix`, `run` and `compose` are the kinds that dispatch; `read`, `decide`
    and `restore` name something to look at, choose between, or do with another tool.
    """
    from roadkeep.remedying import _TABLE  # noqa: PLC0415 - the table is the population

    return tuple(
        sorted(code for code, rule in _TABLE.items() if rule.kind in ("fix", "run", "compose"))
    )


def converged(root: Path, *, rounds: int = 6) -> tuple[str, ...]:
    """Run the doors of one defective project until the gate is clean, and answer which closed.

    RK1338's loop, lifted for its second fixture (RK1641). Converging rather than iterating a
    snapshot, which is the stronger claim: each door is run against the state that produced its
    finding, and a door that parses, is accepted and leaves the finding standing hangs this
    instead of passing an acceptance check.

    Not `fix`: `lint --fix` exits 1 while any unfixed finding still stands, so a mechanical row
    run mid-loop would be asserted against the wrong code. The fixer closes the derived and has
    its own suite; these doors close the rest, and one `--fix` at the end is where the two
    halves meet.

    Answers the codes it closed, in order, so a caller asserts the **reach** and not only that
    the gate went clean — which is the number RK1641 is about: this reaches five codes of
    eighty-five, and the sweep named for the table reaches one.
    """
    from roadkeep.cli import EXIT_OK, main  # noqa: PLC0415 - the suite's own edge
    from roadkeep.config import Config  # noqa: PLC0415 - the suite's own edge
    from roadkeep.linting import lint  # noqa: PLC0415 - the suite's own edge
    from roadkeep.remedying import remedy  # noqa: PLC0415 - the suite's own edge

    closed: list[str] = []
    for _ in range(rounds * 12):
        config = Config.discover(root)
        runnable = [
            (found, rule)
            for found in lint(config).findings
            if (rule := remedy(found, config)) is not None and rule.kind in ("run", "compose")
        ]
        if not runnable:
            break
        found, rule = runnable[0]
        for door in rule.doors:
            argv = supplied(filled(list(door.argv)))
            assert all(not one.startswith("<unfilled ") for one in argv), (found.code, argv)
            assert main(["-C", str(root), *argv]) == EXIT_OK, (found.code, argv)
        closed.append(found.code)
    main(["-C", str(root), "lint", "--fix"])
    return tuple(closed)


#: A field the author fills in: `<label>`, `<its title>`, `…`. What a caller **substitutes**,
#: which is the tell RK1640 measured — a flag family being named in prose never carries one,
#: and a command somebody is meant to paste almost always does.
_HOLDER_IN_SPAN = re.compile(r"<[^>]*>|…")


def unprefixed() -> list[str]:
    """Every verb-leading span that looks like a **door** and carries no invocation (RK1640).

    Three narrowings, and each is what keeps this from being the rule RK1590 measured and
    rejected — *every backticked verb carries the prefix*, which refuses the sentences this
    tool needs to write.

    * **No sibling door in the message.** Where there is one, :func:`inconsistent` already
      decides it off the author's own two spellings, and that is the sharper reading.
    * **Outside the census.** A function that calls `invocation()` is a site `SITES` accounts
      for and this suite runs, so a bare span beside a composed one there is not silent.
    * **Carrying a placeholder**, which is the measurement. 406 spans in this package have no
      sibling door; 27 of them carry a field an author fills, and reading those 27 is what the
      design asked for. The result contradicted its own sampling: they were not all prose.
      Thirteen were commands a caller is being offered, printed without the prefix — RK1589's
      defect exactly, standing thirteen times.

    **Those thirteen are closed** (RK1668), and what closing them cost is not the token: each
    prefixed door makes its function a :func:`census` site owing a `SITES` row, the pair rule
    forces every verb-leading span in the same message to be decided with it, and running two
    of the thirteen found the command did not exist — `govern {table}.lead` names a table
    `governing.GOVERNED` has never held, and `block add` refuses by name on the one state the
    catalogue's empty answer is about. Which is the argument for executing a printed line
    rather than reading it, met twice in thirteen.

    Returned as `<owner>: <span>`, deduplicated, so the population is a set a table can be
    total against. `tests/test_composing.BARE` is the verdict per row, because which of the
    fourteen left is *meant* as a door is a reading and not something this can decide (RK1590).
    """
    prefix = invocation()
    verbs = _verbs()
    # Built once, for `_verbs`' own reason one function up: the census is an AST walk of every
    # module, and taking it per message put this read past two minutes.
    sites = set(census())
    found: list[str] = []
    for module in modules():
        owner = _owners(module)
        for lineno, said in spoken(module):
            where = owner.get(lineno, module.where)
            if where in sites:
                continue
            spans = [" ".join(one.split()) for one in _SPAN.findall(said)]
            if any(
                one.split()[:1] == [prefix] and one.split()[1:2] and one.split()[1] in verbs
                for one in spans
            ):
                continue
            for one in spans:
                if not (one.split()[:1] and one.split()[0] in verbs):
                    continue
                if not _HOLDER_IN_SPAN.search(one):
                    continue
                row = f"{where}: {one}"
                if row not in found:
                    found.append(row)
    return found


def beyond() -> list[str]:
    """Every verb-leading span in a message **outside** the census, addressed (RK1605).

    The boundary of RK1498's guarantee, as a value rather than as something a reader has to
    infer from how :func:`census` is built. `SITES` is total over the functions that call
    `invocation()`; this is what that leaves — a message composed somewhere that never calls it,
    carrying a span that opens with one of this CLI's verbs.

    Non-empty on purpose and not a work-list. RK1590 measured the population: most of it is
    prose naming a flag family or a verb under discussion, and a rule refusing all of it would
    refuse the sentences this tool needs to write. What is checkable inside it is
    :func:`inconsistent`'s narrower claim and :func:`unprefixed`'s narrower one — the second
    being RK1640's measurement, which found the twenty-seven spans carrying a field an author
    fills and read each: thirteen were doors, RK1668 closed them, and the fourteen left are
    prose for four stated reasons.
    """
    sites = set(census())
    verbs = _verbs()
    found: list[str] = []
    for module in modules():
        owner = _owners(module)
        for lineno, said in spoken(module):
            where = owner.get(lineno, module.where)
            if where in sites:
                continue
            for one in (" ".join(span.split()) for span in _SPAN.findall(said)):
                if one.split()[:1] and one.split()[0] in verbs:
                    found.append(f"{where}: {one}")
    return found
