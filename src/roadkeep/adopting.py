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
  could — a backlog kept as table rows parses as nothing, and a zero the reader cannot
  tell from an empty file is the one answer an estimate may not give (RK98). Counting the
  rows is not parsing them: reading the shape is an estimate's job, and a tool that read
  the cells would be a tool with two line formats.

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

from roadkeep.config import CLAIM_HELD, CONFIG_NAME, DEFAULT_PATHS, PYPROJECT, Config
from roadkeep.document import Document, checkbox
from roadkeep.schema import DEFAULT_HEADING_WORD, Schema
from roadkeep.sections import anchored, structural

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
    """

    def __init__(self, paths: Sequence[Path]) -> None:
        self.paths = tuple(paths)
        listed = ", ".join(str(path) for path in self.paths)
        super().__init__(
            f"{len(self.paths)} path(s) already exist and nothing was written: {listed}"
        )


class UnreadableBlock(ValueError):
    """A `--block` value no heading parser would recognise as declaring a block.

    Refused at input rather than written: `## Block <whatever>` that yields no label is a
    heading `add` cannot file a task under, and the author would discover that later.
    """

    def __init__(self, given: str) -> None:
        self.given = given
        super().__init__(
            f"--block {given!r} does not name a block: give the label first, "
            f"optionally with a title — 'A' or 'A {chr(0x2014)} The model'"
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
    #: Every family the measurement was taken under. One unless the caller passed a list:
    #: inference stays at the dominant spelling, because promoting the rest would be the
    #: tool deciding a foreign id is a second track (L4).
    families: tuple[str, ...] = ("RK",)
    blocks: tuple[str, ...] = ()
    #: Lines whose schema rendering differs from how they are written. Not a defect to fix
    #: here — it is the reason the tool would refuse to write the file at all (L3).
    non_canonical: int = 0
    #: Rows of a Markdown table filed under a block heading (RK98). A backlog kept as rows
    #: parses as nothing at all — no entry and no reject — so without this the headline is
    #: the one an empty file gets, and the estimate that decides whether to adopt reports
    #: nothing to change about a file it has not read.
    tabular: int = 0

    @property
    def changing(self) -> int:
        """Lines that would have to change: everything that does not conform *or* read.

        Table rows count here for the same reason rejects do — neither is an entry, and a
        number that only added up what parsed would be smallest on the file furthest from
        the format.
        """
        return (
            self.parsed
            - self.conforming
            + sum(count for _, count in self.rejects)
            + self.tabular
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

    paths = {role: base / DEFAULT_PATHS[role] for role in roles}
    text = render_config(schema, {role: DEFAULT_PATHS[role] for role in roles})
    _verify(text, schema, base, paths)

    target = base / CONFIG_NAME
    bodies = {role: _scaffold(role, blocks, schema) for role in roles}
    clashes = [path for path in (target, *paths.values()) if path.exists()]
    if clashes:
        raise WouldOverwrite(clashes)

    # Everything above this line can refuse; nothing below it can, which is what makes
    # the all-or-nothing claim a property of the order rather than a hope.
    target.write_text(text, encoding="utf-8", newline="")
    written: list[Path] = []
    for role in roles:
        path = paths[role]
        path.parent.mkdir(parents=True, exist_ok=True)
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
                # Named where the choice is made, not where it is hit (RK214): this one
                # closes `retire`, there being no slot for a departure that is not a
                # shipment, and `lint` repeats it every run.
                "# every entry in it shipped, so no line repeats it\n"
                "# (this closes `retire`: a departure that is not a shipment has no slot)\n"
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


def _configured(base: Path) -> Path | None:
    """A declaration *at this root*. An ancestor's is shadowed, not clobbered."""
    candidate = base / CONFIG_NAME
    if candidate.is_file():
        return candidate
    pyproject = base / PYPROJECT
    if pyproject.is_file():
        try:
            with pyproject.open("rb") as handle:
                data = tomllib.load(handle)
        except (OSError, tomllib.TOMLDecodeError):
            return None
        if "roadkeep" in data.get("tool", {}):
            return pyproject
    return None


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
    """The label a `--block` value declares, or a refusal — under this project's word."""
    document = Document.parse(f"## {schema.block_named(block.strip())}\n", schema)
    label = document.headings[0].label if document.headings else None
    if not label:
        raise UnreadableBlock(block)
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
    """
    target = Path(path)
    if ledger and sections:
        raise ValueError(
            "--ledger and --sections measure different units — a ledger in lines and a "
            "rationale file in sections — so each is its own run over its own file"
        )
    if sections:
        return _prose(config, target, ref_scheme)
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

    counts: dict[str, int] = {}
    conforming = 0
    for entry in document.entries:
        violations = schema.validate(entry.task)
        if not violations:
            conforming += 1
        for violation in violations:
            counts[violation.code] = counts.get(violation.code, 0) + 1

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
        blocks=tuple(h.label for h in document.headings if h.label),
        non_canonical=len(document.non_canonical),
        tabular=len(document.tabular),
    )


def _prose(config: Config, target: Path, ref_scheme: str | None) -> Estimate:
    """A rationale file, measured in sections against the two limits nobody reported (RK99).

    Read under the `improvements` role, so `[limits.improvements]` reaches it the same way
    `[limits.changelog]` reaches a ledger — and under the caller's ``ref_scheme``, which
    here decides not a count but *whether there is one*: an anchor is spelled `§RK9` under
    `id` and `XVI.12` under an outline, and reading one as the other turned Shio's 151
    headings into 0 sections. The scheme is on the result for that reason.

    No prefix is reported and none is inferred, because a section is not addressed by one:
    :func:`~roadkeep.sections.anchored` reads the § and not the family behind it, so a
    prefix printed here would be a claim this run never made.

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
    # Every prose paragraph, not only a section's: the width an author wraps to is a fact
    # about the file, and a preamble above the first anchor is written to the same margin.
    widths = [len(line) for line in _filled(document)]
    return Estimate(
        path=target,
        prefix="",
        families=(),
        inferred=False,
        unit="section",
        ref_scheme=schema.ref_scheme,
        parsed=len(found),
        conforming=sum(1 for count in words if count <= schema.section_max),
        measures=(
            Measure(
                field="section",
                limit=schema.section_max,
                longest=max(words, default=0),
                over=sum(1 for count in words if count > schema.section_max),
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


def _alpha_head(text: str) -> str:
    """The leading letters of an id — `SH` of `SH41`."""
    for index, char in enumerate(text):
        if not char.isalpha():
            return text[:index]
    return text


def _grouped(reasons: Iterable[str]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for reason in reasons:
        counts[reason] = counts.get(reason, 0) + 1
    return _ranked(counts)


def _ranked(counts: Mapping[str, int]) -> tuple[tuple[str, int], ...]:
    """Worst first, ties by name — a report read top-down has to start with the work."""
    return tuple(sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])))
