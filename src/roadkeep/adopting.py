"""Getting a project to where the rest of the tool applies (RK18).

Two commands against one problem: **every repository that needs this already has a
backlog**, so a tool that only works on an empty one is a tool nobody can adopt. The two
halves are deliberately asymmetric — one writes a scaffold and nothing else, the other
reads a file it does not own and writes nothing at all.

* :func:`init` creates `roadkeep.toml` and the files it declares. The config is *rendered
  from* :class:`~roadkeep.schema.Schema`'s own defaults rather than copied from a template
  kept beside them, because a template is a second statement of the format and the two
  drift in the direction nobody tests — the same reason `Schema.render` is the only writer
  of a task line.
* :func:`adopt` runs the schema over an existing backlog and reports what would have to
  change for `lint` to pass it. A migration estimate is only worth taking *before* the
  migration commitment, which is why it is a separate command from `lint` and not a flag
  on it: `lint` is a gate over files this project declared, and the file `adopt` reads is
  by definition not one of them yet. It counts what it could not read as well as what it
  could — a backlog kept as table rows, or as the plain `- [ ] …` list almost every
  unadopted roadmap actually is (RK279), parses as nothing, and a zero the reader cannot
  tell from an empty file is the one answer an estimate may not give (RK98). Counting the
  rows is not parsing them: reading the shape is an estimate's job, and a tool that read
  the cells would be a tool with two line formats. It reads **both** kinds of bullet a
  roadmap holds (RK139): the non-goals are measured against the two limits they would be
  held to, declared or not, because a third of one adoption's work was in that list and
  arrived after the commitment. `--sections` is the one read that goes past the path it was
  handed, and for one finding: an address is doubled only *across* two files, so a per-file
  estimate calls both of them conforming and the gate then files a `section.ambiguous` per
  collision (RK347). Which files those are is the project's `[files]` where the target is one
  of this project's own, for the reason :func:`_unread` does not name them otherwise (RK292),
  and otherwise `--with`, repeated (RK359) — the case the command exists for being a file no
  declaration reaches at all. Named and never found by looking in the directory.

Three decisions that are the point rather than details of it:

* **Neither command invents backlog content** (L4). `init` writes a title, the block
  headings the author named and an empty `## Non-goals`; the block *titles* are the
  author's own words, passed through. There is no starter task and no explanatory
  paragraph — prose the tool wrote would be prose the project then has to maintain.
* **Nothing is written unless everything can be.** The config is parsed back in memory and
  compared against the schema it was rendered from, and every target path is checked for
  existence, before the first byte reaches disk. A half-scaffolded project is worse than
  an unscaffolded one because it looks configured.
* **`adopt` measures and never proposes.** It reports the longest `symptom` it found and
  how many lines exceed the limit; it does not suggest raising the limit to fit them. The
  measurement is what decides whether the schema is wrong or the lines are (§RK20), and a
  tool that answered that question would be answering it in the direction that requires
  no work.

Neither prints the RK38 event line: that payload is an id and its block, and a scaffold
writes no task while an estimate writes nothing whatsoever.
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep import scoping
from roadkeep.config import (
    CLAIM_HELD,
    CONFIG_NAME,
    DEFAULT_PATHS,
    PROSE_ROLES,
    PYPROJECT,
    Config,
    Scope,
)
from roadkeep.document import LEDGER_SHAPES, Document, checkbox
from roadkeep.schema import DEFAULT_HEADING_WORD, OUTLINE_ANCHOR_RE, Schema
from roadkeep.sections import anchored, structural, unanchored, words as sections_words

#: The roles `init` scaffolds. `strategy` is absent and not empty: Turing has one and this
#: project does not, and a declared file nobody writes is `file.missing` on the first lint.
SCAFFOLD_ROLES = ("roadmap", "changelog", "improvements")

#: The heading each scaffolded file opens with. Structural, not prose — the block headings
#: below it are what `add`, `ship` and `section add` file text under.
_TITLES = {
    "roadmap": "Roadmap (active backlog)",
    "changelog": "Shipped Ledger",
    "improvements": "Improvements",
}

#: The fields `adopt` measures against their limits, and where each one is read from.
_MEASURED = (("symptom", "symptom_max"), ("why", "why_max"), ("line", "line_max"))

#: An id taken apart for the `[ids]` delta (RK110): the digits, and the one lowercase letter
#: a split keeps. Deliberately looser than any project's own shape — it has to read the ids a
#: declaration would refuse, those being the ones worth counting.
_ID_PARTS_RE = re.compile(r"^[A-Za-z]+(?P<number>[0-9]+)(?P<sub>[a-z]?)$")


class AlreadyConfigured(ValueError):
    """`init` scaffolds; a project that already declares the format wants `adopt`."""

    def __init__(self, source: Path) -> None:
        self.source = source
        super().__init__(
            f"{source} already configures roadkeep: `init` writes a scaffold and would "
            f"overwrite the declaration this project is already governed by — `adopt "
            f"<file>` reports what an existing backlog must change instead"
        )


class WouldOverwrite(ValueError):
    """One existing path is enough to refuse all of them (all-or-nothing).

    A scaffold that skipped what was there and wrote the rest leaves a project half
    configured, which reads as configured and behaves as neither.

    It names `adopt` for what it found (RK282). :class:`AlreadyConfigured` always did, and this
    is the branch that needed it more: a repository holding a backlog and no declaration has
    never met this tool, which is exactly who `adopt` was built for and exactly who is standing
    here — while the refusal that named the door is the one reached by a project that already
    adopted. Per file and never per directory, because the estimate is per file and a
    suggestion naming the directory would be a command that does not exist.
    """

    def __init__(self, paths: Sequence[Path], base: Path | None = None) -> None:
        self.paths = tuple(paths)
        #: Those of :attr:`paths` an estimate can actually be taken over. The configuration is
        #: not one: `adopt` reads a backlog, and pointing it at `roadkeep.toml` is
        #: :class:`NotACorpus` one command later — which this said before there was such a
        #: refusal, the command having answered `0 lines, 0 would change` instead (RK374).
        self.adoptable = tuple(path for path in self.paths if path.name != CONFIG_NAME)
        listed = ", ".join(str(path) for path in self.paths)
        message = f"{len(self.paths)} path(s) already exist and nothing was written: {listed}"
        if self.adoptable:
            # One door and not one per file, though the estimate is per file: every path is
            # already named above, and repeating them here doubled a message that is mostly
            # pathname. Spelled relative to the project where that is possible, for the reason
            # `provenance.invocation` gives — an absolute path is a message about one machine.
            first = _relative(self.adoptable[0], base)
            more = f" (and {len(self.adoptable) - 1} more)" if len(self.adoptable) > 1 else ""
            message += (
                f" — `adopt {first}`{more} reports what an existing backlog must change instead"
            )
        super().__init__(message)


class BlockedParent(ValueError):
    """A declared file whose directory cannot be created, because a file is standing in it.

    :class:`WouldOverwrite` asks whether a target already exists, which is whether writing
    would clobber. This is the other question nobody asked (RK392): whether writing can happen
    at all. A `docs` that is a file rather than a directory left `roadkeep.toml` on disk and
    every file it declares unwritten — the half-scaffolded project `init` says out loud it
    exists to prevent, reachable because the directory was created below the line where
    nothing is supposed to refuse.

    Named per file **and** per blocker, because they are different paths and the second is the
    one to act on: the reader is told `docs/ROADMAP.md` cannot be written and that `docs` is
    why, and deleting the roadmap they were never given would be the wrong move.
    """

    def __init__(self, blocked: Sequence[tuple[Path, Path]], base: Path | None = None) -> None:
        self.blocked = tuple(blocked)
        listed = ", ".join(
            f"{_relative(path, base)} (blocked by {_relative(parent, base)})"
            for path, parent in self.blocked
        )
        super().__init__(
            f"{len(self.blocked)} declared file(s) have a directory that cannot be created "
            f"and nothing was written: {listed}"
        )


def blocking(path: Path) -> Path | None:
    """The nearest ancestor of ``path`` that exists and is not a directory (RK392).

    Public because `install` asks it too (RK393): it writes four surfaces under directories it
    creates as it goes, and a `.claude` that is a file stopped it with the server declaration
    already on disk — `init`'s defect one command over, and the same question answers both.

    The whole chain and not the immediate parent: `docs/backlog/ROADMAP.md` is stopped just
    as dead by a `docs` that is a file, and `mkdir(parents=True)` is what would have walked
    it. Returns the blocker itself rather than a bool, because the file to act on is that one
    and not the one that was asked for.
    """
    for ancestor in path.parents:
        if ancestor.exists():
            return None if ancestor.is_dir() else ancestor
    return None


def _relative(path: Path, base: Path | None) -> str:
    """A path as a reader would type it from the project root, or absolute where it is not one."""
    try:
        return path.relative_to(base).as_posix() if base else path.as_posix()
    except ValueError:  # not under the base, so the whole path is the only true answer
        return path.as_posix()


class Unreadable(ValueError):
    """One path that is not a readable file is enough to refuse the whole estimate (RK370).

    `adopt` was handed one path until RK359 gave it a set, and a set opened a file at a time
    stops partway: the report an adopter reads then measured two of three files and looks
    complete, which is the state :class:`WouldOverwrite` refuses one command over for the same
    reason. So every path is checked before the first one is opened.

    Named by the **argument** that carried it and spelled from the project root, neither of
    which `pathlib`'s own sentence has. With a target and two `--with` files the reader is
    otherwise left with three candidates and one filename, on the one failure — a typo — where
    the filename is the part that is wrong; and the absolute path it prints is the message
    `provenance.invocation` refuses, one about a machine rather than about a project.

    A pre-check and not a replacement for the reader's own raise: a file that exists and
    cannot be read still comes out of :meth:`Document.load` as an `OSError`, which the command
    already reports. What is removed is the case the estimate can see coming.
    """

    def __init__(self, missing: Sequence[tuple[str, Path]], base: Path | None = None) -> None:
        self.missing = tuple(missing)
        listed = ", ".join(
            f"{_relative(path.resolve(), base)} ({named})" for named, path in self.missing
        )
        super().__init__(
            f"{len(self.missing)} path(s) are not a file this can read and nothing was "
            f"measured: {listed}"
        )


class NotACorpus(ValueError):
    """`adopt` was pointed at this format's own declaration, not at anything it measures (RK374).

    The file opens, so :class:`Unreadable` lets it through, and every reader below then finds
    no line and no heading in it: `0 line(s), 0 conform, 0 would change`, which is what an
    empty roadmap reports and is the one answer an estimate may not give (RK98). Counting the
    rows of a table and the plain bullets of a checklist exists so that a file the format has
    no reader for stops answering nothing; a configuration is that case with the reader's own
    declaration in it.

    A refusal and not a count, which is the choice §RK374 left open. `adopt` exits 0 over a
    corpus however far from the format it is (RK18) — the estimate is the thing being bought
    — and refuses the *arguments* that name no corpus to measure: `--ledger` with `--sections`,
    a path that does not open, and this. Measuring it would need a counter and a sentence for
    a file nobody wants measured, while the refusal is the one already written down as true in
    :class:`WouldOverwrite`, which leaves the configuration out of the door it offers on
    exactly this ground.

    Which files those are is :func:`_declares`, the reader `init` refuses against (RK375).
    This was written to catch `roadkeep.toml` by name, on the ground that refusing every
    `pyproject.toml` by name would refuse the ones configuring nothing here — sound against a
    *name* check, and no answer to the question under it, since the name is not how this tool
    recognises the file anywhere else. A pyproject declaring `[tool.roadkeep]` was left
    measuring as an empty backlog by the refusal written to stop exactly that.
    """

    def __init__(self, named: str, path: Path, config: Config | None = None) -> None:
        self.named = named
        self.path = path
        base = config.root if config else None
        # What that configuration declares, where it is the one this run loaded — the door,
        # said precisely. Another project's `roadkeep.toml` names files this run has not read,
        # and offering this project's paths for it would send the caller at the wrong tree.
        declared = (
            [config.relative(config.path(role)) for role in config.paths]
            if config is not None and config.source is not None
            and config.source.resolve() == path.resolve()
            else []
        )
        door = f" — measure {' or '.join(declared)}" if declared else ""
        super().__init__(
            f"{_relative(path.resolve(), base)} ({named}) configures roadkeep and is not a "
            f"corpus: `adopt` measures a backlog, a ledger or a rationale file{door}"
        )


class UnreadableBlock(ValueError):
    """A `--block` value that is not one heading declaring a label.

    Refused at input rather than written: `## Block <whatever>` that yields no label is a
    heading `add` cannot file a task under, and the author would discover that later.

    Two ways to be that, and the message says which (RK390). A value yielding no label is the
    original; a value yielding a label **and more** is the one that got through, because the
    check read the first heading and returned — so `A\\nB` was a block by that reading and the
    scaffold wrote the `B` out as prose beneath it. Naming the cause is the rule RK370 settled
    one refusal over: a caller holding a sentence about the wrong problem debugs the wrong
    thing, and here the two problems are "this is not a block" and "this is a block plus a
    line I did not ask you to write".
    """

    def __init__(self, given: str, *, beyond: bool = False) -> None:
        self.given = given
        #: Whether a label *was* read and the value carried more past it.
        self.beyond = beyond
        said = (
            "names a block and then more, which would be written out under it"
            if beyond
            else "does not name a block"
        )
        super().__init__(
            f"--block {given!r} {said}: give the label first, "
            f"optionally with a title — 'A' or 'A {chr(0x2014)} The model'"
        )


class RepeatedBlock(ValueError):
    """Two `--block` values that declare the same label (RK390).

    One heading twice is a file no verb can address: `add --block A` files under the **last**
    of them — what scanning to the end leaves, rather than anything decided — and `ship` looks
    for that label in the changelog. It is refused rather than
    folded to one, which is the choice §RK390 left open — folding makes `--block A --block A`
    and `--block A` produce identical output, so the author never learns the command was
    wrong, and `init` inventing what somebody meant is the one thing it does not do.

    Read off the **labels** and never the values handed over, because `A` and `A — The model`
    are one block written two ways, and it is the heading the label lands in that a verb has
    to find exactly once.
    """

    def __init__(self, label: str) -> None:
        self.label = label
        super().__init__(
            f"--block {label!r} was given twice: one label is one heading, and two of them "
            f"is a file `add` files into by position and `ship` cannot resolve at all"
        )


@dataclass(frozen=True, slots=True)
class Created:
    """What `init` wrote, in the order it wrote it."""

    config: Path
    files: tuple[Path, ...]
    blocks: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Measure:
    """One length limit, and what the corpus does against it.

    ``longest`` is reported beside ``over`` because the two answer different questions: how
    many lines have to change, and whether the limit is off by a word or by a paragraph.
    """

    field: str
    limit: int
    longest: int
    over: int


@dataclass(frozen=True, slots=True)
class Scoped:
    """The roadmap's *other* bullet, measured (RK139).

    `adopt` read one of the roadmap's two kinds of line. Measured on Claude Code Tray: 18
    lines over on `why` and `line` decided the adoption, and `lint` then produced nine
    findings nobody had been shown — two bullets with no parseable lead, one lead at 72
    against 60, six reasons over 200 with the worst at 1,100. A third of the work, after the
    commitment.

    Reported whether or not `[non_goals]` is declared, which is what ``governed`` says.
    Opt-in makes the measurement *more* useful rather than less: the number an adopter needs
    is what the limit would cost, and until this the only way to get it was to declare the
    table and run the gate.
    """

    parsed: int
    #: Bullets under the heading the grammar did not accept — `scoping.rejects`, which is the
    #: same split :class:`~roadkeep.document.Reject` is: a count that omitted them would read
    #: as complete.
    unparsed: int
    #: Bullets with at least one field over its limit. Per bullet and not per field, because
    #: what an adopter is counting is edits.
    over: int
    measures: tuple[Measure, ...] = ()
    governed: bool = False

    @property
    def changing(self) -> int:
        """Bullets that would have to change. Counted apart from the task lines' total where
        the project has not opted in, the gate reporting nothing there (see `Estimate`)."""
        return self.unparsed + self.over


@dataclass(frozen=True, slots=True)
class Shape:
    """One thing this file's ids spell that `[ids]` can declare, and how many spell it (RK110).

    The same shape the prefix delta and `undeclared` already have — a count, and the key that
    would close it — for the third declaration the estimate never named. It states what the
    ids spell and never that the project should therefore declare it: whether a corpus that
    pads *sometimes* wants a width is a judgement, and this tool has no model (L4).
    """

    #: The `[ids]` key: `pad` or `suffix`.
    key: str
    #: The value that key would take, written as TOML spells it — `2`, `true`.
    value: str
    count: int

    @property
    def declaration(self) -> str:
        """The line an adopting project would write, ready to be read out of a report."""
        return f"{self.key} = {self.value}"


@dataclass(frozen=True, slots=True)
class Doubling:
    """What the across-files read found, and what it opened to find it (RK373).

    Three answers off one walk, because each of them is only knowable there and each was
    being restated somewhere else instead: RK372's contradiction and RK373's were both a fact
    about *this* run written down as a rule about the configuration. The one that reads worst
    is :attr:`opened` — the sentence it feeds exists to say which cross-file checks went
    unmade, and derived from a constant it said a collision had been looked for in a file
    nobody opened.
    """

    #: Every address more than one of the files read declares now, with their names.
    addresses: tuple[tuple[str, tuple[str, ...]], ...] = ()
    #: Those names that are paths rather than roles — see :attr:`Estimate.by_path`.
    by_path: tuple[str, ...] = ()
    #: The declared roles whose files this read opened, prose or not. What makes a file read
    #: is that it was opened, and a changelog handed to `--with` was.
    opened: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Estimate:
    """What an existing backlog would cost to bring under the schema. Written by nothing."""

    path: Path
    prefix: str
    #: True when the prefix was read off the file's own ids because nothing declared one.
    #: Reported, never silent: a count taken under a guessed prefix is a different count.
    inferred: bool
    parsed: int
    conforming: int
    #: What ``parsed`` counts. A backlog is measured in lines and a rationale file in
    #: sections (RK99) — one command and not two, because the corpus an adopting project
    #: has to measure is both files, and a second command would be a second set of numbers
    #: to keep in step with these.
    unit: str = "line"
    #: The scheme the pointers and anchors were read under (RK44). Reported because it
    #: decides what was read at all: under the wrong one a file of 151 sections yields 0.
    ref_scheme: str = "id"
    #: Marker-bearing bullets the grammar refused, grouped by reason, worst first.
    rejects: tuple[tuple[str, int], ...] = ()
    #: Schema violations per code, worst first — the same codes `lint` prints.
    codes: tuple[tuple[str, int], ...] = ()
    measures: tuple[Measure, ...] = ()
    #: Tokens sitting where a marker sits that this project does not declare, with counts:
    #: the `[markers]` table the adopting project has to write.
    undeclared: tuple[tuple[str, int], ...] = ()
    #: What the ids spell that `[ids]` does not declare (RK110) — the third config delta,
    #: beside the prefix and the markers. Without it Dumont's nine `id.format` findings
    #: arrived as nine defects rather than as one unwritten key, and confirming that
    #: `pad = 2` cleared them and nothing else meant diffing two lint runs by hand.
    id_shape: tuple[Shape, ...] = ()
    #: Every prefix the ids actually spell, worst first. More than one is a backlog
    #: numbered by track, or one that absorbed another — `prefix` takes the list (RK74),
    #: and which of the two this is, is the reader's call and never the tool's.
    prefixes: tuple[tuple[str, int], ...] = ()
    #: Every scheme the **pointers** actually spell, worst first (RK285) — the same fact as
    #: :attr:`prefixes` one field over, and reported the same way. Shio's roadmap read
    #: `0 conform, 65 would change` under the default and `63 conform, 2 would change` under
    #: `--ref-scheme outline`, with `ref.mismatch` on every line as the only signal and no
    #: sentence naming the flag — while the prefix half of the same misreading had one.
    schemes: tuple[tuple[str, int], ...] = ()
    #: The `[ledger]` declaration this file's refused lines would parse under, with how many
    #: (RK286). The count is the half the reason cannot give: naming the slots tells an adopter
    #: what to write, and this tells them what writing it recovers — the number RK18 says is
    #: only worth having *before* the commitment, and which otherwise cost a scratch config.
    ledger_shape: tuple[tuple[str, int], ...] = ()
    #: The governed files this estimate did **not** read (RK291). RK290 made the estimate and
    #: the gate agree on everything one file decides, so what is left is the checks that
    #: resolve across files — a dep satisfied by the changelog, a pointer resolved in the
    #: rationale file. Running them from one file is what must not happen: pointed at Shio's
    #: roadmap without its changelog, a deps pass reports 82 unresolved deps on a backlog
    #: whose deps all resolve. Naming what was out of reach is the other act, and the one
    #: an adopter can take — handing `adopt` these files is what the sentence implies.
    unopened: tuple[str, ...] = ()
    #: Whether the target is one of the files this project declares (RK292). It usually is not
    #: — `adopt` reads a file that is "by definition not one of them yet" — and that decides
    #: what :attr:`unopened` can mean: siblings worth handing over where the target is declared,
    #: and nothing nameable where the config belongs to another project entirely.
    declared: bool = False
    #: Every family the measurement was taken under. One unless the caller passed a list:
    #: inference stays at the dominant spelling, because promoting the rest would be the
    #: tool deciding a foreign id is a second track (L4).
    families: tuple[str, ...] = ("RK",)
    blocks: tuple[str, ...] = ()
    #: Lines whose schema rendering differs from how they are written. Not a defect to fix
    #: here — it is the reason the tool would refuse to write the file at all (L3).
    non_canonical: int = 0
    #: The non-goals list, measured beside the task lines (RK139) — None on a run over a
    #: ledger or a rationale file, neither of which holds one. Its own count and not part of
    #: ``changing`` where the project has not opted in: the gate reports nothing there, and a
    #: headline that added the cost of a rule nobody has adopted would be measuring a
    #: different commitment from the one being taken.
    non_goals: Scoped | None = None
    #: Rows of a Markdown table filed under a block heading (RK98). A backlog kept as rows
    #: parses as nothing at all — no entry and no reject — so without this the headline is
    #: the one an empty file gets, and the estimate that decides whether to adopt reports
    #: nothing to change about a file it has not read.
    tabular: int = 0
    #: Every address more than one prose file declares **now**, with the roles (RK347) — the
    #: one finding a per-file estimate cannot reach by construction, because a doubling only
    #: exists across two files. Measured on a project whose `IMPROVEMENTS.md` and `STRATEGY.md`
    #: both open at `I` and both declare a `III`: four `section.ambiguous` on the first run of
    #: the gate, against two files this estimate had called conforming. Empty where the target
    #: is not declared here (RK292) — there the siblings belong to another project — and empty
    #: on a backlog, which holds lines and not headings.
    ambiguous: tuple[tuple[str, tuple[str, ...]], ...] = ()
    #: The files in this run's set that were read **by path** rather than through a prose
    #: role, by the name :attr:`ambiguous` calls them (RK371). Since RK369 a file is named the
    #: truest way this project can name it, and a run given `--with` gets one of each: the
    #: printed line shows which is which by sitting in a sentence, and `--json` — read by the
    #: caller who took it *not* to open a file (L5) — had a `roles` key holding filenames
    #: `[files]` does not answer, with no field saying the lookup would never work. Over the
    #: set that was read and not over the collisions, because how a run named a file is a fact
    #: about the run: it is the same answer when nothing collided at all.
    #:
    #: What it does **not** say is that the project has no claim on the file (RK372). A
    #: changelog handed to `--with` is declared here and still read by path, having no outline
    #: to collide in — and calling that ungoverned put the contradiction in the report, beside
    #: an `unopened` that had already counted the same file as this project's. Recorded and
    #: never resolved away either way: inventing a role for a file this project does not govern
    #: is the answer RK292 keeps out of the report.
    by_path: tuple[str, ...] = ()
    #: The lines this file holds, and how many of them were read in **any** shape at all —
    #: as an entry, a reject, a table row, a plain bullet or a heading (RK376). RK98's rule at
    #: the far end of itself: :attr:`tabular` and :attr:`listed` stop a backlog written in a
    #: shape nothing reads from answering the number an empty file answers, and a file that is
    #: not a backlog in any shape walked past both — a fourteen-line `README.md` and a roadmap
    #: with one heading and no tasks reporting the same `0 conform, 0 would change`, on the run
    #: where a typo puts the caller least able to check it.
    #:
    #: Two numbers because one of them alone is the ambiguity: zero read against a file with
    #: bulk is a different answer from zero against a file with none, and only the second means
    #: what the headline says. Reported and deliberately **not** added to :attr:`changing` — how
    #: many lines would have to change is an answer about a backlog becoming conforming, and
    #: this file may be no backlog at all. Counting what was read against what is there is a
    #: measurement; concluding somebody named the wrong file is an opinion (L4).
    lines: int = 0
    recognised: int = 0
    #: What this file holds in a shape the format has no reader for, in whatever :attr:`unit`
    #: is being counted: plain list items under a block heading in a backlog (RK279), and
    #: headings with prose and no anchor in a rationale file (RK281). One field because it is
    #: one idea and it lands in :attr:`changing` the same way — a backlog kept as `- [ ] …`
    #: priced 2 as a table and 0 as a list, and a `DESIGN.md` answered 0 sections, both being
    #: the zero RK98 forbids. The *sentence* differs by unit; the number does not.
    listed: int = 0

    @property
    def changing(self) -> int:
        """Lines that would have to change: everything that does not conform *or* read.

        Table rows and plain list items count here for the same reason rejects do — none is
        an entry, and a number that only added up what parsed would be smallest on the file
        furthest from the format.

        Non-goals join it only where the project **declared** them governed (RK139), because
        there they are lines the gate will fail on. Where it has not, they are measured and
        reported and left out of this number: the estimate would otherwise price a rule
        nobody has adopted into the decision about adopting a different one.
        """
        scoped = self.non_goals.changing if self.non_goals and self.non_goals.governed else 0
        return (
            self.parsed
            - self.conforming
            + sum(count for _, count in self.rejects)
            + self.tabular
            + self.listed
            + scoped
        )


# -- init ------------------------------------------------------------------


def init(
    root: str | Path = ".",
    *,
    prefix: str | Sequence[str] = "RK",
    blocks: Sequence[str] = ("A",),
    roles: Sequence[str] = SCAFFOLD_ROLES,
) -> Created:
    """Write `roadkeep.toml` and the files it declares, or write nothing.

    ``blocks`` are heading suffixes: ``"A"`` becomes ``## Block A`` and ``"A — The model"``
    becomes ``## Block A — The model``. They are mirrored into all three files, because the
    ledger and the rationale file are filed under the same headings the roadmap is and a
    write never invents one (RK37).
    """
    base = Path(root).resolve()
    existing = _configured(base)
    if existing is not None:
        raise AlreadyConfigured(existing)

    # Raises on a prefix this format cannot carry, and on a set of families that would
    # read one id two ways (RK74).
    schema = Schema(prefixes=_families(prefix))
    labels = tuple(_label(block, schema) for block in blocks)
    if not labels:
        raise UnreadableBlock("")
    # The check of the *set*, which per-value validation cannot make (RK390): `_label` is right
    # about each one and two of them being the same label is a fact about neither.
    seen: set[str] = set()
    for label in labels:
        if label in seen:
            raise RepeatedBlock(label)
        seen.add(label)

    paths = {role: base / DEFAULT_PATHS[role] for role in roles}
    text = render_config(schema, {role: DEFAULT_PATHS[role] for role in roles})
    _verify(text, schema, base, paths)

    target = base / CONFIG_NAME
    bodies = {role: _scaffold(role, blocks, schema) for role in roles}
    clashes = [path for path in (target, *paths.values()) if path.exists()]
    if clashes:
        raise WouldOverwrite(clashes, base)
    # `exists` answers whether a write would clobber, and not whether it can happen at all
    # (RK392): a `docs` that is a file is a `docs/ROADMAP.md` no write reaches, and the
    # question was never asked. Knowable in advance, so it is decided up here with the rest.
    blocked = [(path, parent) for path in paths.values() if (parent := blocking(path))]
    if blocked:
        raise BlockedParent(blocked, base)

    # Everything that can be decided in advance is decided above this line, which is what
    # makes the all-or-nothing claim a property of the order rather than a hope. What cannot
    # be is a write the filesystem refuses — a permission, a full disk — and the directories
    # go first so that failure lands before the configuration rather than after it: an empty
    # `docs/` is a tree nobody has to recognise, and a `roadkeep.toml` declaring three files
    # that do not exist is the half-scaffolded project this order exists to prevent.
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="")
    written: list[Path] = []
    for role in roles:
        path = paths[role]
        path.write_text(bodies[role], encoding="utf-8", newline="")
        written.append(path)
    return Created(config=target, files=tuple(written), blocks=labels)


def render_config(schema: Schema, paths: Mapping[str, str]) -> str:
    """The configuration as TOML, taken from a live :class:`Schema` and not a template.

    Every value here is read off the object the tool validates with, so a default that
    changes changes the scaffold in the same commit. The comments name each limit's *unit*,
    which is the one thing the key name does not say — a `section` in words and a `line` in
    characters are not the same kind of number.
    """
    # One family is written as the string every other project has; several as the list a
    # backlog numbered by track needs (RK74), in the order they were declared.
    prefix = (
        _quote(schema.prefix)
        if len(schema.prefixes) == 1
        else "[" + ", ".join(_quote(p) for p in schema.prefixes) + "]"
    )
    lines = [
        f"prefix = {prefix}",
        "",
        "# how a rationale section is addressed: \"id\" derives the pointer from the",
        "# task's own id, \"outline\" keeps a hand-numbered anchor",
        f"ref_scheme = {_quote(schema.ref_scheme)}",
        "",
        "# what jumps the queue, in order: an id or a \"Block X\", and nothing else",
        "priority = []",
        "",
        "[files]",
    ]
    lines += [f"{role} = {_quote(paths[role])}" for role in SCAFFOLD_ROLES if role in paths]
    lines += [
        "",
        "[limits]",
        "# characters",
        f"symptom = {schema.symptom_max}",
        f"why = {schema.why_max}",
        f"line = {schema.line_max}",
        "",
        "# a section is prose, so its budget is words; prose is the width one is filled to",
        f"section = {schema.section_max}",
        f"prose = {schema.prose_width}",
        "",
        "[markers]",
        f"open = [{', '.join(_quote(marker) for marker in schema.markers)}]",
        f"shipped = {_quote(schema.shipped_marker)}",
        f"retired = {_quote(schema.retired_marker)}",
        "",
        "[claims]",
        # Written even at its default, and with the unit in the comment, for the reason every
        # limit above carries one: minutes is the one thing `held` does not say, and a project
        # that meant seconds is refused rather than given a claim nobody would wait out (RK151).
        "# minutes a claim on a line reads as held, before a later caller steps over it",
        f"held = {CLAIM_HELD}",
    ]
    shape = [
        # Same rule as the heading word and the `[ledger]` absences: only what differs from
        # the shape every project starts with, because `pad = 1` reads as a width somebody
        # chose rather than as the unpadded id nobody had to (RK106).
        line
        for declared, line in (
            (schema.id_pad != 1, f"# the width the number is zero-filled to\npad = {schema.id_pad}"),
            (schema.id_suffix, "# a split task keeps its number and takes a letter\nsuffix = true"),
        )
        if declared
    ]
    if shape:
        lines += ["", "[ids]", *shape]
    if schema.heading_word != DEFAULT_HEADING_WORD:
        # Only when it differs, for the same reason the `[ledger]` absences below are only
        # written when they are absences: `word = "Block"` reads as a decision about a word
        # nobody chose.
        lines += [
            "",
            "[headings]",
            "# the word this project files work under",
            f"word = {_quote(schema.heading_word)}",
        ]
    absent = [
        # Only what is false: a default written out reads as a decision somebody made about
        # a slot the file carries anyway (RK43, RK48).
        line
        for present, line in (
            (
                schema.ledger_marker,
                # What the declaration costs, said where the choice is made (RK214) — and
                # since RK125 that cost is one line's worth: a departure is the one status
                # such a file does not state, so it is the one line that carries a marker.
                "# every entry in it shipped, so no line repeats it\n"
                f"# (a retirement still carries {schema.retired_marker}: a departure is "
                f"not a shipment)\n"
                "marker = false",
            ),
            (schema.ledger_symptom, "# its lines are `- **id** — <prose>`, with no symptom slot\nsymptom = false"),
        )
        if not present
    ]
    if absent:
        lines += ["", "[ledger]", *absent]
    lines.append("")
    return "\n".join(lines)


def _declares(path: Path) -> bool:
    """Whether this **file** is a declaration of this format (RK375).

    The reader both doors into it share. `init` refuses against a declaration and `adopt`
    refuses a path that is one, and they disagreed: this asked whether a `pyproject.toml`
    carries `[tool.roadkeep]`, while :class:`NotACorpus` asked only for the filename — so the
    newer refusal reached one of the two files and a pyproject that configures this tool was
    still measured as an empty backlog, which is the reading RK374 exists to stop.

    Two files and two rules, because they are not the same claim. A `roadkeep.toml` **is** the
    declaration by existing, whatever is in it; a `pyproject.toml` is a file most repositories
    have and this format only sometimes lives in, so the table is what decides. Unparseable is
    not a declaration — a caller who pointed here at a broken TOML has a different problem, and
    guessing it configures this tool would refuse a file on a hunch.
    """
    if path.name == CONFIG_NAME:
        return True
    if path.name != PYPROJECT:
        return False
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return False
    return "roadkeep" in data.get("tool", {})


def _configured(base: Path) -> Path | None:
    """A declaration *at this root*. An ancestor's is shadowed, not clobbered."""
    return next(
        (
            candidate
            for name in (CONFIG_NAME, PYPROJECT)
            if (candidate := base / name).is_file() and _declares(candidate)
        ),
        None,
    )


def _verify(text: str, schema: Schema, base: Path, paths: Mapping[str, Path]) -> None:
    """Parse the rendered config back and refuse unless it means what it was built from.

    The same test the files get (L3), applied to the one file that decides how they are
    read: a scaffold whose config does not round-trip through `Config.parse` would
    configure the project as something other than what `init` was asked for, and the
    author would find out on the first `add`.
    """
    parsed = Config.parse(tomllib.loads(text), root=base)
    if parsed.schema != schema:
        raise ValueError(
            f"the rendered configuration does not read back as the schema it was built "
            f"from and nothing was written: {parsed.schema!r}"
        )
    if parsed.paths != {role: path.resolve() for role, path in paths.items()}:
        raise ValueError(
            "the rendered configuration declares different paths than were scaffolded "
            "and nothing was written"
        )


def _label(block: str, schema: Schema) -> str:
    """The label a `--block` value declares, or a refusal — under this project's word.

    **One heading and the whole value** (RK390). This used to read the label off the first
    heading it found and return, which is true of `A` and true of `A\\nB` — where the parse
    also produced a second line, and the scaffold then wrote it out as prose under a heading
    that had, correctly, parsed. What refuses it is the line count and not a hunt for
    newlines: the claim being made is that this value is one heading, and a value that came
    back as two lines is not, whatever split it.
    """
    document = Document.parse(f"## {schema.block_named(block.strip())}\n", schema)
    label = document.headings[0].label if document.headings else None
    if not label:
        raise UnreadableBlock(block)
    if len(document.lines) != 1:
        raise UnreadableBlock(block, beyond=True)
    return label


def _scaffold(role: str, blocks: Sequence[str], schema: Schema) -> str:
    """One file: a title, the block headings, and — for the roadmap — where non-goals go."""
    lines = [f"# {_TITLES[role]}", ""]
    for block in blocks:
        lines += [f"## {schema.block_named(block.strip())}", ""]
    if role == "roadmap":
        # `brief` prints these with every task (RK29), so the heading exists from the
        # start: an author who has to create it first is an author who writes none.
        lines += ["## Non-goals", ""]
    return "\n".join(lines)


def _families(prefix: str | Sequence[str]) -> tuple[str, ...]:
    """One family or a list of them, as :class:`Schema` takes it (RK74).

    A bare string stays one family rather than becoming a list of its letters, which is
    the one thing a `str`-is-a-`Sequence` reading of this argument would silently do.
    """
    return (prefix,) if isinstance(prefix, str) else tuple(prefix)


def _quote(value: str) -> str:
    """A TOML basic string, or a refusal — this never guesses at an escape."""
    if '"' in value or "\\" in value or "\n" in value:
        raise ValueError(f"cannot be written to TOML without escaping: {value!r}")
    return f'"{value}"'


# -- adopt -----------------------------------------------------------------


def adopt(
    config: Config,
    path: str | Path,
    *,
    prefix: str | Sequence[str] | None = None,
    ref_scheme: str | None = None,
    ledger: bool = False,
    sections: bool = False,
    alongside: Sequence[str | Path] = (),
) -> Estimate:
    """Read a backlog this tool does not own and report what it would cost to adopt it.

    The prefix comes from ``prefix`` if given, from `roadkeep.toml` if the project has one,
    and otherwise from the file's own ids — flagged as ``inferred`` in the result, because
    a count of `id.format` violations taken under the wrong prefix is a count of one
    mistake repeated, which is exactly the noise that makes a migration estimate useless.

    ``ref_scheme`` is an override and never an inference, which is the asymmetry worth
    stating: a prefix is a fact about the ids already written, while the scheme is a
    *decision* about whether a live outline gets migrated (§RK27) — measuring Shio under
    `outline` says what adopting the tool costs, and under `id` what adopting the tool
    *and* renumbering the outline costs. Both are real questions and only the caller
    knows which one is being asked.

    ``ledger`` names the **role** the file is read in, not a schema to apply (RK76): the
    numbers come from :meth:`Config.schema_for`, the same seam every other command loads a
    document through, so `[limits.changelog]` and `[rules.changelog]` reach the estimate.
    They did not before, and an estimate taken under limits the gate does not apply is a
    measurement of a commitment nobody is being asked to make. A role and not a path
    because the caller names a file the project may not have declared at all.

    ``sections`` names the *other half of the corpus* (RK99): a rationale file, whose unit
    is a section and whose limits are `[limits] section` and `prose`. Those are two of the
    numbers an adopting project has to declare, and until this they were the only ones the
    estimate never reported — so setting them meant copying this repository's, which is
    the template argument L6 refuses, or writing a throwaway script, which is what
    adopting commitclerk actually did. A flag and not a second command, because a corpus
    measured by two commands is two sets of numbers to keep in step.

    ``alongside`` names the *rest of the set* the doubled-address finding is about (RK359).
    That finding is the one measure here that is not a property of one file, and until this
    it was reachable only where the target was already one of this project's own — so the
    adopter it exists for, running `--sections` from outside against a file no
    `roadkeep.toml` declares, met the collision on the first `lint` after the commitment
    instead. Named and never inferred from the directory: a `DESIGN.md` beside an
    `IMPROVEMENTS.md` is a guess about somebody's layout, and the report would then be
    measuring a set the caller never chose. Every other number stays about ``path`` alone.
    """
    target = Path(path)
    if ledger and sections:
        raise ValueError(
            "--ledger and --sections measure different units — a ledger in lines and a "
            "rationale file in sections — so each is its own run over its own file"
        )
    if alongside and not sections:
        raise ValueError(
            "--with names the other prose files an address could be doubled across, which "
            "is a --sections measurement: a backlog holds lines and not headings"
        )
    if prefix is not None and sections:
        raise ValueError(
            "--prefix selects the ids to read, and --sections measures a rationale file "
            "whose sections are addressed by § and not by a family: there is nothing here "
            "for a prefix to choose between"
        )
    # Every path before the first one is opened (RK370), so a run over a set refuses whole
    # rather than reporting the files it reached before the one it could not.
    handed = (
        ("the file to measure", target),
        *(("--with", Path(one)) for one in alongside),
    )
    unreadable = [(named, one) for named, one in handed if not one.is_file()]
    if unreadable:
        raise Unreadable(unreadable, config.root)
    # And before that, the file that is readable and is still not a corpus (RK374) — which is
    # either of the two this format is declared in, asked the way `init` asks (RK375).
    declaration = [(named, one) for named, one in handed if _declares(one)]
    if declaration:
        raise NotACorpus(declaration[0][0], declaration[0][1], config)
    if sections:
        return _prose(config, target, ref_scheme, alongside)
    schema = config.schema_for("changelog" if ledger else "roadmap")
    if ref_scheme is not None and ref_scheme != schema.ref_scheme:
        schema = replace(schema, ref_scheme=ref_scheme)  # raises on an unknown scheme
    document = Document.load(target, schema)

    spelled = _prefixes(document)
    declared = _families(prefix) if prefix else None
    if declared is None and config.source is not None:
        declared = config.schema.prefixes
    inferred = declared is None
    # Inference stays at *one* family even now that the schema carries several (RK74).
    # Which of two spellings is a second track and which is a paste from another backlog
    # is a judgement about meaning, and this tool has no model (L4) — so a project that
    # numbers by track declares it, and `--prefix` takes the list.
    chosen = declared or ((spelled[0][0],) if spelled else schema.prefixes)
    if chosen != schema.prefixes:
        # Swapped rather than re-read: the prefix is a validation rule and not a grammar,
        # so no line parses differently under it and a second read would be the same read.
        schema = replace(schema, prefixes=chosen)
        document = replace(document, schema=schema)

    # The findings the gate would raise over **this file alone** (RK290), and not a second
    # walk of the per-line rules. `adopt` used to call `Schema.validate` per entry, which is
    # the per-line half only, so a duplicated id — decidable from one file, and refused by
    # `lint` over that same file — read as `2 conform, 0 would change`. `within` is the half
    # of the gate one file can run, already named and already relied on by the merge driver,
    # so the estimate and the gate now disagree only where they read different files.
    #
    # `role` names the *schema* this file is being read in, which is what the finding's path
    # is cosmetic against here: `adopt` reads a file the project may not declare at all, and
    # only the codes are counted.
    # Imported here and not at module level (RK260): `linting` reaches `backlog` and
    # `exporting`, and an estimate is the only caller in this module.
    from roadkeep.linting import within  # noqa: PLC0415

    findings = within(config, "changelog" if ledger else "roadmap", document)
    counts: dict[str, int] = {}
    for finding in findings:
        # `line.unparsed` is the reject, already reported as its own row with the reason that
        # names a remedy (RK286) — counting it again here would price one line twice.
        if finding.code != "line.unparsed":
            counts[finding.code] = counts.get(finding.code, 0) + 1
    faulted = {f.lineno for f in findings if f.code != "line.unparsed"}
    conforming = sum(1 for entry in document.entries if entry.lineno not in faulted)

    return Estimate(
        path=target,
        prefix=chosen[0],
        families=chosen,
        inferred=inferred,
        parsed=len(document.entries),
        conforming=conforming,
        ref_scheme=schema.ref_scheme,
        rejects=_grouped(reject.reason for reject in document.rejects),
        codes=_ranked(counts),
        measures=_measures(document, schema),
        undeclared=_undeclared(document),
        id_shape=_id_shape(document, schema),
        prefixes=spelled,
        schemes=_schemes(document),
        ledger_shape=_ledger_shape(document, schema),
        unopened=_unread(config, target),
        declared=_declared(config, target),
        blocks=tuple(h.label for h in document.headings if h.label),
        non_canonical=len(document.non_canonical),
        # Only where the file is being read as a backlog: a ledger has no such list, and a
        # heading matching there would be an answer about the wrong file (RK139).
        non_goals=None if ledger else _scoped(config, document),
        tabular=len(document.tabular),
        listed=len(document.listed),
        lines=len(document.lines),
        recognised=_recognised(
            (entry.lineno for entry in document.entries),
            (reject.lineno for reject in document.rejects),
            (row.lineno for row in document.tabular),
            (item.lineno for item in document.listed),
            (heading.lineno for heading in document.headings if heading.label),
        ),
    )


def _prose(
    config: Config,
    target: Path,
    ref_scheme: str | None,
    alongside: Sequence[str | Path] = (),
) -> Estimate:
    """A rationale file, measured in sections against the two limits nobody reported (RK99).

    Read under the `improvements` role, so `[limits.improvements]` reaches it the same way
    `[limits.changelog]` reaches a ledger — and under the caller's ``ref_scheme``, which
    here decides not a count but *whether there is one*: an anchor is spelled `§RK9` under
    `id` and `XVI.12` under an outline, and reading one as the other turned Shio's 151
    headings into 0 sections. The scheme is on the result for that reason.

    No prefix is reported and none is inferred, because a section is not addressed by one:
    :func:`~roadkeep.sections.anchored` reads the § and not the family behind it, so a
    prefix printed here would be a claim this run never made. Which is why one *named* is
    refused rather than dropped (RK384): the report has no prefix line by design, so nothing
    on screen would have contradicted a caller who believed the run was taken under theirs —
    and `--prefix "not a prefix at all"` was a refusal one flag over and a no-op here.

    ``prose`` is a measurement and never a violation — the width is what a written section
    is *filled to*, and nothing gates a hand-wrapped file at it. It is here because it is
    the second number an adopting project has to declare, and the file it is declaring it
    for is the one being read. Taken over the paragraphs the tool would actually fill
    (:func:`~roadkeep.sections.structural` is the same predicate that decides), because the
    widest line in a rationale file is a table row nobody would wrap to.
    """
    schema = config.schema_for("improvements")
    if ref_scheme is not None and ref_scheme != schema.ref_scheme:
        schema = replace(schema, ref_scheme=ref_scheme)  # raises on an unknown scheme
    document = Document.load(target, schema)
    found = anchored(document)
    words = [section.words for section in found]
    # Headings where a section would be, carrying no anchor (RK281). Measured the same way —
    # a span of prose has a word count whether or not this tool has an address for it.
    loose = unanchored(document)
    loose_words = [
        sections_words("".join(document.lines[h.lineno : document.prose_end(h)]))
        for h in loose
    ]
    # Every prose paragraph, not only a section's: the width an author wraps to is a fact
    # about the file, and a preamble above the first anchor is written to the same margin.
    widths = [len(line) for line in _filled(document)]
    # RK347: the finding one path cannot hold, with the kind of name each file got (RK371).
    # Taken before `unopened`, which is derived from it — a file this opened is not one the
    # same report may name as out of reach, and a file it did not is not one it may cover for.
    across = _ambiguous(config, target, alongside, schema)
    return Estimate(
        path=target,
        prefix="",
        families=(),
        inferred=False,
        unit="section",
        ref_scheme=schema.ref_scheme,
        # RK288: the second source. Without it `--sections` had no way to say "read this the
        # other way", which is the one sentence Shio's file needed.
        schemes=_heading_schemes(document),
        ambiguous=across.addresses,
        by_path=across.by_path,
        # What that read opened, and never a rule about what a read of this kind opens (RK373).
        unopened=_unread(config, target, opened=across.opened),
        declared=_declared(config, target),
        parsed=len(found),
        conforming=sum(1 for count in words if count <= schema.section_max),
        # RK281: the same contract `listed` has one file over. A rationale file that never
        # adopted the sigil has sections in every sense but this tool's, and the zero it used
        # to get is the one RK98 forbids.
        listed=len(loose),
        # The same pair the backlog run carries (RK387). Its shapes are entries and bullets and
        # this one's are headings, so what is read differs — what may not is whether the run
        # says so, a rationale file of prose and no heading having answered a blank file's
        # `0 conform, 0 would change` for as long as the other one stopped doing that.
        lines=len(document.lines),
        recognised=_recognised(
            (section.first for section in found),
            (heading.lineno for heading in loose),
        ),
        measures=(
            Measure(
                field="section",
                limit=schema.section_max,
                # Over both, because the width an unanchored section is written to is the
                # number an adopter is being asked to declare — the same reason `prose` below
                # measures every paragraph and not only an anchored one's.
                longest=max([*words, *loose_words], default=0),
                over=sum(1 for count in (*words, *loose_words) if count > schema.section_max),
            ),
            Measure(
                field="prose",
                limit=schema.prose_width,
                longest=max(widths, default=0),
                over=sum(1 for width in widths if width > schema.prose_width),
            ),
        ),
        blocks=tuple(h.label for h in document.headings if h.label),
    )


def _filled(document: Document) -> list[str]:
    """Every line of every paragraph the tool would re-wrap, stripped of its ending.

    Blank-separated, because a paragraph is the unit the structure test judges — one table
    row would otherwise read as prose the moment it was looked at on its own.
    """
    out: list[str] = []
    paragraph: list[str] = []
    for raw in (*document.lines, "\n"):
        line = raw.rstrip("\r\n")
        if line.strip():
            paragraph.append(line)
            continue
        if paragraph and not structural(paragraph):
            out += paragraph
        paragraph = []
    return out


def _scoped(config: Config, document: Document) -> Scoped:
    """The non-goals under this roadmap's heading, against the two limits they will be held to.

    The parser is `scoping`'s own — the reader every other caller shares — so the count is the
    one `lint` will take and not a second reading of the same bullets. The limits are the
    project's `[non_goals]` where it declared them and :class:`Scope`'s defaults where it has
    not, which is the whole point of measuring an opt-in rule: an adopter is asking what the
    table would cost before writing it.
    """
    scope = config.non_goals or Scope()
    # The bullets whose shape held, which is what `parsed` has always counted (RK233): the
    # reader now returns the others too, so the filter is here and named rather than inside a
    # reader two other callers share. An unshaped bullet is one edit, counted by `unparsed`,
    # and charging its sentence-lead against `lead` as well would count that edit twice.
    found = tuple(goal for goal in scoping.read(document) if goal.shaped)
    over = sum(
        1
        for goal in found
        if len(goal.lead) > scope.lead or len(goal.why) > scope.why
    )
    leads = [len(goal.lead) for goal in found]
    whys = [len(goal.why) for goal in found]
    return Scoped(
        parsed=len(found),
        unparsed=len(scoping.rejects(document)),
        over=over,
        measures=(
            Measure(
                field="lead",
                limit=scope.lead,
                longest=max(leads, default=0),
                over=sum(1 for length in leads if length > scope.lead),
            ),
            Measure(
                field="why",
                limit=scope.why,
                longest=max(whys, default=0),
                over=sum(1 for length in whys if length > scope.why),
            ),
        ),
        governed=config.non_goals is not None,
    )


def _measures(document: Document, schema: Schema) -> tuple[Measure, ...]:
    """Every length limit against the corpus: the longest, and how many exceed it."""
    out: list[Measure] = []
    for field, attribute in _MEASURED:
        limit = getattr(schema, attribute)
        lengths = [
            len(schema.render(entry.task) if field == "line" else getattr(entry.task, field))
            for entry in document.entries
        ]
        out.append(
            Measure(
                field=field,
                limit=limit,
                longest=max(lengths, default=0),
                over=sum(1 for length in lengths if length > limit),
            )
        )
    return tuple(out)


def _undeclared(document: Document) -> tuple[tuple[str, int], ...]:
    """Tokens in the marker slot this project does not declare — the `[markers]` delta.

    Read off the rejected line's own text rather than matched against the reason string:
    a reason is a sentence for a human, and a report that parsed one would break the first
    time the sentence was reworded.

    A task-list checkbox is skipped by the same shape test that rejected it (RK103) and not
    by a token spelling here: `- [ ] **C40**` splits to `[`, which carries no alphanumeric
    and so would otherwise arrive as a marker to declare — and declaring `[` is the one
    answer that widens the slot to two tokens. The line is still counted, in `rejects`.
    """
    schema = document.schema
    known = {
        *schema.markers,
        schema.shipped_marker,
        schema.retired_marker,
        schema.deferred_marker,
    }
    counts: dict[str, int] = {}
    for reject in document.rejects:
        rest = reject.raw.lstrip("-*+ ")
        if checkbox(rest) is not None:
            continue
        token = rest.split(" ", 1)[0]
        if token and token not in known and not any(c.isalnum() for c in token):
            counts[token] = counts.get(token, 0) + 1
    return _ranked(counts)


def _id_shape(document: Document, schema: Schema) -> tuple[Shape, ...]:
    """What the ids spell about `[ids]` that this schema does not declare (RK110).

    Two counts over strings already parsed, and neither is a proposal. **A leading zero** is
    a width: `D01` under the default `pad = 1` is one of nine findings that are one unwritten
    key, and the widths are reported separately because a corpus that pads to two and to
    three is a corpus whose width nobody has chosen. **A trailing lowercase letter** is
    `suffix = true` — Turing's `T24b`, 4 of its 361 findings.

    Read with a pattern of its own rather than :meth:`Schema.parse_id`, which is precisely
    the *declared* shape: under `pad = 1` it reads `D01` as no id at all, and what the ids
    spell that the declaration does not is the whole measurement.

    Only what the schema does not already hold, exactly as the prefix delta prints only the
    families the chosen ones do not cover: a project that declared the width is not owed a
    report saying it could.
    """
    widths: dict[int, int] = {}
    suffixed = 0
    for entry in document.entries:
        parts = _ID_PARTS_RE.match(entry.task.id)
        if parts is None:
            continue
        number = parts.group("number")
        if number.startswith("0") and len(number) != schema.id_pad:
            widths[len(number)] = widths.get(len(number), 0) + 1
        if parts.group("sub") and not schema.id_suffix:
            suffixed += 1
    out = [
        Shape(key="pad", value=str(width), count=count)
        for width, count in sorted(widths.items(), key=lambda pair: (-pair[1], pair[0]))
    ]
    if suffixed:
        out.append(Shape(key="suffix", value="true", count=suffixed))
    return tuple(out)


def _prefixes(document: Document) -> tuple[tuple[str, int], ...]:
    """The alphabetic head of every id in the file, counted. A measurement, not a choice."""
    counts: dict[str, int] = {}
    for entry in document.entries:
        head = _alpha_head(entry.task.id)
        if head:
            counts[head] = counts.get(head, 0) + 1
    return _ranked(counts)


def _ledger_shape(document: Document, schema: Schema) -> tuple[tuple[str, int], ...]:
    """Which `[ledger]` declaration would read this file's refused lines, and how many (RK286).

    Only where the file is being read as a ledger, and only over lines that were *refused*: a
    line that already parses is not evidence about a slot, and a roadmap has no `[ledger]` to
    declare. Grouped by the declaration, so a file needing both slots is one row and not two
    with the same count.

    Measured rather than left to a flag. The reason names the slots and this names what
    declaring them recovers, which is the number RK18 says is only worth having before the
    commitment — and reaching it otherwise meant writing the configuration under decision.

    One count per **whole** declaration, and never a tally of what each line individually
    wants: the two slots are not independent. A `- ✅ **T3** — why` line is read by
    `symptom = false` and *stopped* by `marker = false`, because with no marker slot the ✅
    sits where the id goes. Summing per-line wants would promise a total no single
    configuration delivers, and a project declares one `[ledger]`, not one per line.

    Counted by **re-reading the file** under each declaration, not by matching the line
    grammar again: a ledger with no marker slot still carries one on a departure (RK125), and
    a regex that did not know it under-reported Turing by the 11 lines that are retirements.
    The reader is the only thing that knows what the reader does — this is the seam every
    other command loads a document through, so the promise cannot drift from the outcome.
    """
    if not schema.is_ledger:
        return ()
    text = "".join(document.lines)
    counts: dict[str, int] = {}
    for marker, symptom, slots in LEDGER_SHAPES:
        if (marker, symptom) == (schema.marker_field, schema.symptom_field):
            continue  # what the file already declares is not a hypothesis about it
        under = replace(schema, marker_field=marker, symptom_field=symptom)
        read = len(Document.parse(text, under).entries)
        if read > len(document.entries):
            counts[", ".join(slots)] = read
    return _ranked(counts)


def _heading_schemes(document: Document) -> tuple[tuple[str, int], ...]:
    """Which scheme the **headings** of a prose file are anchored in, counted (RK288).

    :func:`_schemes` reads the pointers on task lines, and a rationale file has none — so the
    one output that would say "read this the other way" was structurally absent on the command
    where the misreading is total. Shio's rationale file read `0 conform, 94 would change`
    under the default and `93 conform` under `--ref-scheme outline`, with no line naming the
    flag.

    Read off the heading's first token and never off the schema, which is the whole point: an
    anchor is `0.1` or it is an id, and which a file spells is a fact about the file. The
    sigil is optional here because `anchor_text` writes one only under the id scheme — a bare
    `0.1` is what an outline heading looks like on disk.

    This is a *report* about the file and never a per-heading guess: :func:`unanchored` keeps
    asking the declared schema, because a count that quietly repaired itself would leave the
    reader with the right number under a reading the report still claims is right.
    """
    counts: dict[str, int] = {}
    for heading in document.headings:
        token = heading.text.split(maxsplit=1)[0].lstrip("§") if heading.text.strip() else ""
        if not token:
            continue
        if _ID_PARTS_RE.match(token):
            counts["id"] = counts.get("id", 0) + 1
        elif OUTLINE_ANCHOR_RE.match(token):
            counts["outline"] = counts.get("outline", 0) + 1
    return _ranked(counts)


def _ambiguous(
    config: Config,
    target: Path,
    alongside: Sequence[str | Path] = (),
    schema: Schema | None = None,
) -> Doubling:
    """Every address two prose files declare now, with the roles that declare it (RK347).

    The one check `adopt` could not make from one path. Every other limit it reports is a
    property of the file in front of it; a doubled address is a property of the *set*, so a
    per-file read answers "conforming" about two files the gate then files four
    `section.ambiguous` against — and that is the finding an adopting project meets first,
    because two outlines written independently both start at `I`.

    :func:`~roadkeep.history.doubled` is the reader, so this is the same answer `anchors`
    prints rather than a second opinion about what a collision is. Handed live headings only
    and never :func:`~roadkeep.history.anchors`, which reaches for `git log` to date them: an
    estimate is taken on a tree that may not be a clone, and the address a *pointer* cannot
    resolve is one two headings declare today.

    Empty where the target is not one of this project's files (RK292), for the reason
    :func:`_unread` is: there `[files]` names somebody else's siblings, and reporting a
    collision between two of them would be measuring a project the caller did not ask about.

    Reads the anchors **qualified** (RK340), which is what makes the report actionable rather
    than merely true: declaring `[refs]` puts each file's outline in its own namespace, and
    the same run then answers zero.

    ``alongside`` replaces that set with the one the caller named (RK359) — the target plus
    those files. It replaces rather than extends for the same reason the whole finding is
    guarded: a set half chosen by the caller and half by a `[files]` table that may belong to
    another project is a doubling the reader cannot act on. Resolved before pairing, so a file
    named twice, or named as well as being the target, does not collide with itself.

    Each of them is read **through its role where it has one** (RK369), which is where the
    qualification comes from: the prefix rides on the document's schema, so a path loaded
    directly carries none and a project that already declared `[refs]` was told twice about a
    collision its configuration resolved — the one thing an estimate may not do, its number
    being the one bought before a commitment. So the label is a role where there is one and
    the path where there is not: each file named the truest way this project can name it, and
    a file it does not govern has no role to be called by.

    Which kind each name is, is returned beside them (RK371). It is known here and nowhere
    after — the printed line survives on the sentence around it, and `--json` was left with a
    `roles` key holding filenames and no way to tell.

    So is **which declared files this actually opened** (RK373). The sentence naming what went
    unread used to be handed every prose role, which was exactly true while this read all of
    them and became a claim about a set the caller had since narrowed: with `--with`, a
    `STRATEGY.md` nobody looked at was reported as covered by the one line whose job is to say
    what was not. What was read is known here and derived nowhere else.
    """
    from roadkeep.history import Anchor, doubled  # noqa: PLC0415 - RK260

    if alongside:
        read = schema or config.schema_for("improvements")
        roles = _by_role(config)
        seen: dict[Path, tuple[str, Document]] = {}
        for one in (target, *(Path(p) for p in alongside)):
            here = one.resolve()
            if here in seen:
                continue
            role = roles.get(here)
            seen[here] = (
                (role, config.document(role))
                if role in PROSE_ROLES
                # `read` and not the role's schema for a governed file that is not prose: a
                # ledger read as a ledger has no headings to anchor, and the caller handed it
                # over as the other half of an outline.
                else (_relative(here, config.root), Document.load(here, read))
            )
        named = [
            Anchor(anchor=section.anchor, role=label, live=True)
            for label, document in seen.values()
            for section in anchored(document)
        ]
        by_path = tuple(
            label for path, (label, _) in seen.items() if roles.get(path) not in PROSE_ROLES
        )
        # Every declared role behind one of those paths, prose or not: what makes a file
        # "read" here is that this opened it, and a changelog handed over was opened.
        opened = tuple(role for path in seen if (role := roles.get(path)) is not None)
        return Doubling(doubled(named), by_path, opened)
    if not _declared(config, target):
        return Doubling()

    kept = [role for role in PROSE_ROLES if config.has(role) and config.path(role).is_file()]
    taken = [
        Anchor(anchor=section.anchor, role=role, live=True)
        for role in kept
        for section in anchored(config.document(role))
    ]
    # Every name here is a role by construction, so nothing was read by path. A declared prose
    # file that is not on disk is *not* in `kept` and so is named as unread: `file.missing` is
    # the gate's word for it, and claiming a collision was checked for in it would be this
    # sentence covering for the other one.
    return Doubling(doubled(taken), (), tuple(kept))


def _by_role(config: Config) -> dict[Path, str]:
    """Every path this project declares, resolved, against the role that declares it (RK372).

    The one place a path becomes a role. Two callers asked it separately and narrowed it
    differently — one against every role, one against the prose roles alone — and each was
    right about its own question while the report carried both answers about one file, one of
    them saying it had been read and the other that this project had no role for it. Neither
    rule moved; what changed is that there is one answer to narrow.

    It is the **resolved** path that decides and never the filename: an `IMPROVEMENTS.md` in
    another checkout is a different file from this one's, and the whole case `adopt` exists
    for is a caller standing outside the project.
    """
    return {config.path(role).resolve(): role for role in config.paths}


def _unread(config: Config, target: Path, opened: Sequence[str] = ()) -> tuple[str, ...]:
    """The governed files this run did not open, in `[files]` order (RK291).

    Named by **file** and not by finding code, which is the decision the section settled:
    `deps.unknown` and `ref.unresolved` is precise and ages badly as the gate grows a check,
    while a filename is what an adopter can act on — handing `adopt` that file is the move the
    sentence implies.

    Empty where the target is **not** one of the declared files (RK292), which is the case
    `adopt` exists for. There this project's `[files]` belong to somebody else: naming them as
    unread said that Turing's `docs/IMPROVEMENTS.md` was measured while this repository's
    `docs/IMPROVEMENTS.md` went unread, which reads as the report not having read what it read
    — and offering siblings nobody can hand over. The limit is still real and simply narrower,
    and :attr:`Estimate.declared` is what lets the sentence say which one it is.

    ``opened`` is what this run *did* read past the target (RK347), which the caller takes off
    the read itself and never off a rule about what a read of this kind opens (RK373): naming
    an opened file here would say it was out of reach in the same report that measured it, and
    excluding one that was not opened would cover for a check nobody made. Both were the same
    mistake, and the second arrived the moment `--with` let a caller narrow the set of files
    the doubling is taken over. What stays unread is what stays unread — the
    checks that resolve through a task line — which is what the sentence was always about.
    """
    here = target.resolve()
    by_role = {role: config.path(role).resolve() for role in config.paths}
    if here not in by_role.values():
        return ()
    return tuple(
        config.relative(config.path(role))
        for role, path in by_role.items()
        if path != here and role not in opened
    )


def _declared(config: Config, target: Path) -> bool:
    """Whether this target is one of the files the loaded project governs (RK292)."""
    here = target.resolve()
    return any(config.path(role).resolve() == here for role in config.paths)


def _schemes(document: Document) -> tuple[tuple[str, int], ...]:
    """Which scheme each pointer in this file is *shaped* like, counted (RK285).

    :func:`_prefixes` one field over, and a measurement rather than a choice for the same
    reason: whether a file that points by `<x.y>` should be read under `outline` is a decision
    about a live outline, and only the caller knows which question is being asked (see `adopt`).

    Read off the pointers already parsed and never by re-reading the file under the other
    scheme: the scheme is a validation rule and not a grammar — no line parses differently
    under it — so a second read would be the same read.
    """
    counts: dict[str, int] = {}
    for entry in document.entries:
        ref = entry.task.ref
        if not ref:
            continue
        if ref == entry.task.id:
            counts["id"] = counts.get("id", 0) + 1
        elif OUTLINE_ANCHOR_RE.match(ref):
            counts["outline"] = counts.get("outline", 0) + 1
    return _ranked(counts)


def _alpha_head(text: str) -> str:
    """The leading letters of an id — `SH` of `SH41`."""
    for index, char in enumerate(text):
        if not char.isalpha():
            return text[:index]
    return text


def _recognised(*shapes: Iterable[int]) -> int:
    """How many of a file's lines were read in **any** shape at all (RK376, RK387).

    Distinct line numbers rather than a sum, because the shapes are not disjoint by
    construction and a total that double-counted one line would be a number nobody could
    check against the file. Zero is the whole point of it — beside :attr:`Estimate.lines` it
    is what tells an empty roadmap apart from a file this format read nothing in.

    The shapes are named by the **caller** and not gathered here, because the two runs do not
    read the same ones (RK387). A backlog is read as entries, the marker lines it refused,
    table rows and plain bullets (RK98's two counters), and headings that *declare a block* —
    that last qualifier being the measurement rather than a detail of it, since a `README.md`
    opening at `# My project` would otherwise answer two for headings this format cannot read
    as structure, which is exactly the prose that walked past. A rationale file has no entries
    at all and is read as its anchored sections and the headings carrying prose without one.
    Gathering both sets here would mean a function that knows which run it is in; naming them
    at the call site is what lets one counter serve two readings.
    """
    return len({lineno for shape in shapes for lineno in shape})


def _grouped(reasons: Iterable[str]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for reason in reasons:
        counts[reason] = counts.get(reason, 0) + 1
    return _ranked(counts)


def _ranked(counts: Mapping[str, int]) -> tuple[tuple[str, int], ...]:
    """Worst first, ties by name — a report read top-down has to start with the work."""
    return tuple(sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])))
