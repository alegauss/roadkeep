"""A number that is a judgement, declared where the reading that decides it is taken (RK1272).

`declare` retrofits a role into `[files]` and `priority migrate` moves the queue out of the
config. Every other table is edited by hand — and in an agent session that is not a hand edit,
it is no edit at all: the write path is the served surface, and nothing on it wrote this file.

The tables worth a verb are the ones whose value is a **judgement about a number**: `[limits]`,
`[budgets]`, `[tools]` and `[claims]`. Each already has the read that decides it — `budget
--file` prices an every-turn file, `cost --tools` ranks the served descriptions, and the P90
of the lines that already read well is what put `symptom` at 120. What they do not have is a
place where the reading and the number meet, so the reading happens once and the number is
defended in a comment afterwards: this project's own `[tools]` entry is four paragraphs of
exactly that, re-argued three times in one session.

So this prints the reading and takes the number in the same call, and **refuses one the corpus
already violates** rather than writing a limit whose first act is a finding. Which is L1 at the
one address it had never reached: the schema is enforced where the text is created everywhere
except the file the schema is written in.

Three things it deliberately is not:

* **Not a serialiser.** The key is inserted and every other byte stays, which is `declare`'s
  rule and `bump_version`'s before it: a `tomllib` round-trip drops the comments a scaffolded
  config is mostly made of.
* **Not the argument.** Why 120 and not 130 is prose, and the tool does not write prose (L4).
  What it writes is the declaration; the reading is printed for the author to argue from.
* **Not a second statement of the shape.** Which addresses exist, what type each takes and
  what this build defaults to are :mod:`roadkeep.describing`'s, read and never repeated.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep.config import Config
from roadkeep.kernel.schema import width
from roadkeep.provenance import invocation

__all__ = ["Declared", "Measured", "NoSuchKey", "Violated", "govern", "reading"]

#: The four tables this verb writes, and the whole of what it claims. Every other table in
#: `describing.TABLES` holds a name, a path or a flag — a decision with no reading behind it,
#: which is a `declare` or a hand edit and never a measurement.
GOVERNED = ("limits", "budgets.<path>", "tools", "claims", "reads")


class NoSuchKey(KeyError):
    """An address this build has no key for, or one no reading decides (RK1272).

    Two absences and one message, because the caller is choosing an address either way: a
    typo, and a key that exists and is not a number. The second is the interesting one — a
    `[files]` role or a `[markers]` glyph is a decision with nothing to measure it against, so
    a verb that took one would be printing an empty reading beside a write `declare` makes.
    """

    def __init__(self, address: str, known: Sequence[str]) -> None:
        self.address = address
        spelled = ", ".join(known)
        super().__init__(
            f"no governed number at {address!r}: this verb writes the tables a reading "
            f"decides — {spelled} — and `{invocation()} config` lists every key there is, "
            f"including the ones that are a name rather than a measurement"
        )


class Violated(ValueError):
    """A number the corpus already breaks, refused before it is written (RK1272).

    The whole of what makes this a verb rather than an editor. A limit whose first act is a
    finding is one somebody lowers, reads the report, and raises again — three commits and a
    red gate for a decision that was measurable before the first of them.

    The **widest** site is named and not all of them: what an author needs to choose a number
    is the one that would refuse, and a listing of every line over it is the gate's answer to
    a question this call exists to stop them asking.
    """

    def __init__(self, address: str, at: int, worst: int, where: str, over: int) -> None:
        self.address = address
        self.at = at
        self.worst = worst
        super().__init__(
            f"{address} = {at} is a limit this project already breaks: {where} measures "
            f"{worst}, and {over} of them would be over — declare it at {worst} or above, or "
            f"bring the corpus under it first and then declare it, which is the order that "
            f"leaves no commit with a red gate in it"
        )


@dataclass(frozen=True, slots=True)
class Measured:
    """What the corpus says about one governed number, now.

    Printed before the write and answerable on its own, which is the half a comment in the
    config was standing in for: the number is a judgement, and a judgement wants the figure it
    was made against written down where it can be taken again.
    """

    address: str
    #: What the key is measured in, as the read that owns it names it.
    unit: str
    #: The widest thing this limit governs today, and where it is.
    worst: int = 0
    where: str = ""
    #: How many sites the reading looked at, so a `0` is told from an empty corpus.
    sites: int = 0
    #: What this project declares now, or `None` where it declares nothing.
    declared: int | None = None
    #: What holds the key when the project declares nothing — the number this build falls back
    #: to, or `None` where there is no fallback at all (RK1343). Three governable keys are in
    #: the second state by design: `reads.brief`, `tools.session` and `tools.characters` are
    #: unpriced until somebody looks, and `budget.session` refuses a surface only where the
    #: ceiling *is* declared, so an undeclared one is not a lenient gate but no gate. Reported
    #: because the reader running this verb is asking exactly whether anything holds them, and
    #: :meth:`Schema.source_of` already refuses to guess for the same reason one surface over:
    #: a citation invented for an undeclared limit answers that question in the reassuring
    #: direction.
    default: int | None = None
    #: Absent where nothing measures this key — `[claims] held` is a judgement about how long
    #: work takes, which no file here holds evidence about (said, never invented).
    unmeasured: str = ""
    #: The argument standing above the key, one string per comment line and the `#` stripped
    #: (RK1296). Kept in the file by `--because` and handed back here, because a reason the
    #: read does not return is one the caller opens the config for — the read L5 exists to
    #: replace, on the one file every other rule is read out of. Verbatim: what the comment
    #: *means* is not this tool's to say (L4).
    because: tuple[str, ...] = ()
    #: Whether a corpus above this number is a **violation** (RK1476). True for every limit
    #: some gate refuses, which is what makes :class:`Violated` the right answer: a ceiling
    #: whose first act is a finding is one somebody lowers, reads and raises again.
    #:
    #: False for `reads.list`, and it is not an exception to that rule but its other side. That
    #: number bounds an *answer this verb declines to compose*, and the ledger it is declared
    #: against will be over it permanently and by design — being over is the state the ceiling
    #: exists to produce, not a red to bring the corpus under. Refusing the write would leave
    #: the key undeclarable on exactly the projects that need it.
    refuses: bool = True

    def over(self, at: int) -> bool:
        return self.refuses and bool(self.sites) and self.worst > at

    def stated(self, standing: bool = True) -> str:
        """The reading, and what the project declares — the second omitted by a write.

        `standing` is False at a `govern` that just wrote one: the header there already says
        the new number and the old, so a `declared` row beside it would state the value this
        call has replaced as if it were current.
        """
        rows = [f"{self.address}  {self.unit}"]
        if self.unmeasured:
            rows.append(f"  reading  none — {self.unmeasured}")
        else:
            rows.append(
                f"  reading  {self.sites} site(s), widest {self.worst}"
                + (f" at {self.where}" if self.where else "")
            )
        if standing:
            if self.declared is not None:
                rows.append(f"  declared {self.declared}")
            elif self.default is not None:
                # The number, not the fact that one exists (RK1343): *a default applies* is
                # the half a reader cannot act on, and the whole question they came with is
                # which figure they are held to.
                rows.append(f"  declared none — this tool's default of {self.default} holds")
            else:
                # And the honest other half. Three keys reach here — `reads.brief`,
                # `tools.session`, `tools.characters` — and their gates read `if … is not
                # None`, so undeclared is not lenient but absent. Saying *a default applies*
                # answered the reader's real question in the reassuring direction, which is
                # what `Schema.source_of` refuses to do about a limit for the same reason.
                # The gate clause only where there is a gate: `prose` and `claims.held` say
                # in the row above that nothing measures or refuses them, and a sentence
                # announcing a gate switched off would argue with the line it follows.
                gate = (
                    ""
                    if self.unmeasured
                    else ", so the gate reading it is off until a number is written here"
                )
                rows.append(
                    f"  declared none — and nothing holds it: this key has no default{gate}"
                )
            # Under the number and not beside it, because it is prose and wraps: the first
            # line is labelled and the rest are indented to it, which is how every wrapped
            # answer here is read (RK1296).
            rows.extend(
                f"  {'because' if index == 0 else '       '}  {line}"
                for index, line in enumerate(self.because)
            )
        return "\n".join(rows)


@dataclass(frozen=True, slots=True)
class Declared:
    """One key written into `roadkeep.toml`, with the reading it was written against."""

    address: str
    at: int
    measured: Measured
    #: The line the key landed on, 1-based — what a reviewer reads the diff against.
    lineno: int
    #: What it said before, or `None` where the key is new.
    before: int | None = None
    #: Whether an argument stands above the key after this call (RK1293). A field because the
    #: answer says which of the two happened: the reason is theirs either way, and where none
    #: arrived the line saying so is the one thing that keeps the number from being a figure
    #: nobody can date. Read off the **lines** and never off the flag (RK1295) — a `--because`
    #: that wrapped to nothing placed nothing, and the caller cannot see the file to tell.
    argued: bool = False
    #: Whether that argument was **already** the one above the key, so this call wrote none
    #: (RK1294). The number is idempotent and the reason beside it is too: a retried call, a
    #: replayed capture or an agent unsure its command took would otherwise leave the same
    #: sentence twice, which reads as two decisions and is one.
    standing: bool = False
    #: The comment lines `--instead` took out, verbatim and `#` included (RK1367). Empty on
    #: every `--because`, which stacks. Handed back rather than counted, because withdrawing an
    #: argument in silence is history removed — the caller reads what was displaced in the
    #: answer, puts back anything the run swept up that it should not have, and the commit
    #: carries the rest. What those lines *meant* is not this tool's to weigh (L4): the whole
    #: contiguous run above the key is what argues the number, so the whole run is what a
    #: replacement replaces, and saying which lines those were is the check on that reach.
    displaced: tuple[str, ...] = ()

    def stated(self, config: Config) -> str:
        where = config.relative(config.source) if config.source else "roadkeep.toml"
        was = "" if self.before is None else f" (was {self.before})"
        # The reading indented under this write's header (RK1372, RK1376): that record prints
        # its own column-0 header, which is right when `govern <key>` is the whole answer and
        # is a second subject line in the middle of one when it is not — the address is already
        # in the line above, so what the row adds is the unit and the sites.
        reading = "\n".join(f"  {row}" for row in self.measured.stated(standing=False).splitlines())
        return "\n".join(
            [
                f"{where}:{self.lineno}  {self.address} = {self.at}{was}",
                reading,
                # The prose is the author's and the placing is this verb's (RK1293). Said
                # either way, because a number with no argument beside it is one nobody can
                # date — and the rule that sent it to the commit was unkeepable here, the
                # commit body being composed by a tool this project does not own.
                self._reason(),
                # And the file, which is the half a reviewer would otherwise miss (RK298,
                # RK1130): a number moved in `roadkeep.toml` changes what every write is held
                # to, and it is the one file a commit about a limit is really about.
                f"  stage    git add -- {where}",
            ]
        )

    def _reason(self) -> str:
        """Which of the three happened to the argument, said in the answer (RK1293, RK1294).

        Three and not two, because "already there" is neither a write nor an absence: a caller
        told nothing was written would write it again, and a caller told it was would believe
        a second decision had been recorded.
        """
        if self.standing:
            return (
                "  reason   already above the key — the same sentence, so it was not "
                "written a second time"
            )
        if self.displaced:
            # A fourth, and the only one that reports a **deletion** (RK1367): the count and
            # the lines, because an argument withdrawn without saying so is the accreting
            # rationale read backwards, and the reach of the run is what a caller checks.
            return "\n".join(
                [
                    f"  reason   written above the key, in your words, instead of the "
                    f"{len(self.displaced)} line(s) that argued it before",
                    *(
                        f"  {'withdrew' if index == 0 else '        '}  {line.rstrip()}"
                        for index, line in enumerate(self.displaced)
                    ),
                ]
            )
        if self.argued:
            return "  reason   written above the key, in your words"
        return (
            '  reason   none — `--because "…"` writes yours above the key, and a number '
            "with none is one nobody can date"
        )

    def payload(self, config: Config) -> dict[str, object]:
        return {
            "address": self.address,
            "at": self.at,
            "was": self.before,
            "file": config.relative(config.source) if config.source else None,
            "line": self.lineno,
            "argued": self.argued,
            "standing": self.standing,
            # What `--instead` took out (RK1367). Always published and never omitted when
            # empty, for the reason `over` is: a key that appears only when it is set is one a
            # reader learns to stop looking for, and this one is a deletion.
            "displaced": [line.rstrip("\n") for line in self.displaced],
            "reading": {
                "unit": self.measured.unit,
                "sites": self.measured.sites,
                "worst": self.measured.worst,
                "where": self.measured.where,
                "unmeasured": self.measured.unmeasured or None,
            },
        }


def _addressed(config: Config, address: str) -> tuple[str, str]:
    """The `(table, key)` an address names, refused where no reading decides it."""
    from roadkeep.describing import TABLES  # noqa: PLC0415 - RK260

    table, _, key = address.rpartition(".")
    for name in GOVERNED:
        stem = name.split(".")[0]
        if table in (name, stem) and key in TABLES[name]:
            return name, key
    raise NoSuchKey(address, GOVERNED)


def reading(config: Config, address: str, *, file: str = "", role: str = "") -> Measured:
    """What this project's own files say about one governed number, now (RK1272).

    Every branch here calls a read that already exists and owns the question — the whole
    argument for the verb is that those readings live somewhere other than the declaration,
    not that they are missing.
    """
    from roadkeep.describing import shape  # noqa: PLC0415 - RK260

    table, key = _addressed(config, address)
    # Whether the project declared it is the shape's answer and the *value* is the live
    # config's: one read says which of the two facts this is, and the other says the number.
    written = any(one.name == key and one.declared for one in shape(config, table).keys)
    declared = _current(config, table, key, file=file, role=role) if written else None
    if table == "limits":
        found = _limits(config, address, key, declared, role=role)
    elif table == "budgets.<path>":
        found = _budgets(config, address, key, declared, file=file)
    elif table == "tools":
        found = _tools(config, address, key, declared)
    elif table == "reads":
        found = _reads(config, address, declared, key)
    else:
        found = Measured(
            address=address,
            unit="minutes",
            declared=declared,
            unmeasured=(
                "how long a claim reads as held is a judgement about how long work takes, "
                "and no file here holds evidence about that"
            ),
        )
    # And the argument, joined here rather than inside six branches: what argues a number is
    # the same question wherever the number is measured, and the answer is in one file (RK1296).
    # The fallback joins it for the same reason and from the same place (RK1343): which number
    # holds an undeclared key is one question, and only `limits` has an answer — a bare
    # `Schema` *is* this build's defaults, so reading them off one is reading them off the
    # thing that enforces them rather than off a second list that would drift.
    return replace(
        found,
        because=_because(config, table, key, file=file, role=role),
        default=_fallback(table, key),
    )


def _fallback(table: str, key: str) -> int | None:
    """The number this build holds an undeclared key to, where it holds one at all (RK1343).

    Only `limits`, and that is the finding rather than an omission here: `[tools]`, `[reads]`
    and `[budgets]` are `None` on `Config` until a project writes them, and the gates that
    read them are written `if … is not None` — so an undeclared ceiling there is no ceiling.
    Measured: with no `[limits]`, a 192-character symptom is refused at `120 (this tool's
    default)`; with no `[tools]`, `lint` reports nothing at all about the served surface.

    `prose` is absent from the schema and stays `None`, which is right and is the same fact
    its own row already states: it is a width this tool fills to and no gate refuses.
    """
    if table != "limits":
        return None
    from roadkeep.kernel.schema import Schema  # noqa: PLC0415 - RK1065's edge, deferred

    return getattr(Schema(), f"{key}_max", None)


def _current(config: Config, table: str, key: str, *, file: str, role: str) -> int | None:
    """What this project declares for a key today, read off the live config and not the file."""
    from roadkeep.config import _LIMIT_KEYS  # noqa: PLC0415 - RK260

    if table == "limits":
        return getattr(config.schema_for(role or "roadmap"), _LIMIT_KEYS[key])
    if table == "tools":
        return config.tool_characters if key == "characters" else config.tool_session
    if table == "reads":
        return config.list_read if key == "list" else config.brief_read
    if table == "claims":
        return config.held
    for budget in config.budgets:
        if config.relative(budget.path) == file or budget.path.as_posix().endswith(file):
            return getattr(budget, key)
    return None


def _limits(
    config: Config, address: str, key: str, declared: int | None, *, role: str
) -> Measured:
    """The widest field this limit governs, over the files the project declares.

    Measured in the unit the limit is in — code units for a field, words for a section, and
    the rendered line for `line` — because a number compared against the wrong unit is the one
    kind of reading that looks right.
    """
    from roadkeep.config import LINE_ROLES  # noqa: PLC0415 - RK260

    if key == "prose":
        # A width and not a ceiling, which is the one key in this table nothing refuses: it
        # says how wide a section this tool *writes* is filled, so the widest line on disk is
        # a fact about imported prose and never a violation. Measured by nobody, said here.
        return Measured(
            address=address,
            unit="utf-16 code units",
            declared=declared,
            unmeasured=(
                "the width a written section is filled to, which no gate refuses — an "
                "adopted file's own lines are wider and are not wrong"
            ),
        )
    if key == "section":
        return _sections(config, address, key, declared, role=role)
    # Declared and read from one place (RK1279, RK1361). It was derived here — a line file is
    # a declared role that is not a prose one — which held until `decisions` became both, and
    # then failed the way the derivation was written to fail loudly and did not: a widest
    # measured over three files where four hold lines, and a limit the fourth already breaks
    # accepted. So the set is stated in `config` beside the one it stopped being the
    # complement of, and the seventh role is added there once rather than reasoned about here.
    roles = (role,) if role else LINE_ROLES
    worst, where, sites = 0, "", 0
    for one in roles:
        if not config.has(one):
            continue
        document = config.document(one)
        for entry in document.entries:
            measured = _field(document, entry, key)
            if measured is None:
                continue
            sites += 1
            if measured > worst:
                worst = measured
                where = f"{config.relative(config.path(one))}:{entry.lineno}"
    # And what a write would **carry into** this file (RK1284), which for one role is not the
    # same population as what it holds. `ship --decides` composes the decision from the open
    # line's own claim, so a decisions file with nothing in it measured zero sites and
    # accepted any number — after which every ship carrying a claim wider than it was refused
    # over a field no flag on that call writes. RK1279's hole at a different set: there the
    # reading missed a file, and here it reads the right one and misses what is coming.
    for entry, carried in _carried(config, key, role):
        sites += 1
        if carried > worst:
            worst = carried
            where = f"{config.relative(config.path('roadmap'))}:{entry.lineno} (inherited)"
    return Measured(
        address=address,
        unit="utf-16 code units",
        worst=worst,
        where=where,
        sites=sites,
        declared=declared,
    )


def _carried(config: Config, key: str, role: str) -> tuple[tuple[object, int], ...]:
    """Every open claim a `ship --decides` would carry into the decisions file (RK1284).

    One role and one field, and both are declared in code rather than guessed:
    :func:`~roadkeep.shipping._decided` composes the record with `as_recorded`, which keeps
    the task's **symptom** and replaces the `why`. So the symptom is inherited whole and
    nothing else is, which is what makes this derivable — a reading of what *might* be
    written anywhere would be a guess, and this is the one inheritance the code states.

    Empty for every other role and every other key, and — the case that matters — for a call
    with **no** role at all: the shared `[limits]` already walks every line file including the
    roadmap, so adding the carried claims there would be one population reported twice.
    """
    if role != "decisions" or key != "symptom" or not config.has("roadmap"):
        return ()
    return tuple(
        (entry, width(entry.task.symptom))
        for entry in config.document("roadmap").entries
        if entry.task.symptom
    )


def _field(document: object, entry: object, key: str) -> int | None:
    """One line's measurement for one limit, or `None` where the line has no such field."""
    task = entry.task  # type: ignore[attr-defined]
    if key == "line":
        return width(entry.raw.rstrip("\r\n"))  # type: ignore[attr-defined]
    if key == "part":
        return width(task.part) if task.part else None
    value = getattr(task, key, None)
    return None if not value else width(value)


def _sections(
    config: Config, address: str, key: str, declared: int | None, *, role: str = ""
) -> Measured:
    """The longest rationale section, charged as the budget charges one (RK136).

    ``role`` narrows it to one prose file, and it had to the moment a third one arrived with a
    budget of its own (RK1361): `[limits.decisions] section` governs that file alone, and a
    reading over every prose file would refuse a decisions limit the improvements file breaks
    — a number rejected on evidence from a file it does not govern.
    """
    from roadkeep.config import PROSE_ROLES  # noqa: PLC0415 - RK260
    from roadkeep.sections import anchored  # noqa: PLC0415 - RK260

    worst, where, sites = 0, "", 0
    for role in (role,) if role else PROSE_ROLES:
        if not config.has(role):
            continue
        document = config.document(role)
        for found in anchored(document):
            sites += 1
            # The section's own charge and the prose width, each read the way the limit that
            # governs it is: `words` is what the budget charges (RK136) and a `prose` width is
            # about the longest line somebody filled, not about the paragraph.
            measured = found.words
            if measured > worst:
                worst = measured
                where = f"{config.relative(config.path(role))}:{found.first}"
    return Measured(
        address=address,
        unit="words",
        worst=worst,
        where=where,
        sites=sites,
        declared=declared,
    )


def _budgets(
    config: Config, address: str, key: str, declared: int | None, *, file: str
) -> Measured:
    """What an every-turn file costs now — `budget --file`'s own reading, taken here.

    That read **refuses** a project with no `[budgets]` at all, correctly: a budget for a file
    nobody declared is a limit invented there. Here it is the ordinary case — the caller is
    declaring the first one — so the refusal is caught and reported as the absence it is.
    """
    from roadkeep.budgeting import file_budget  # noqa: PLC0415 - RK260

    try:
        loads = file_budget(config)
    except (KeyError, OSError):
        loads = ()
    for one in loads:
        if file and one.path != file:
            continue
        cost = next((each for each in one.costs if each.unit == key), None)
        if cost is None:
            continue
        return Measured(
            address=address,
            unit=key,
            worst=cost.taken,
            where=one.path,
            sites=1,
            declared=declared,
        )
    # The file itself, for a budget nothing declares yet: what it costs is what decides the
    # number, and `spent` is the one counter both this and the gate go through.
    if file:
        from roadkeep.config import spent  # noqa: PLC0415 - RK260

        target = config.root / file
        if target.is_file():
            counted = spent(target.read_bytes())
            return Measured(
                address=address,
                unit=key,
                worst=counted[key],
                where=file,
                sites=1,
                declared=declared,
            )
    return Measured(
        address=address,
        unit=key,
        declared=declared,
        unmeasured=(
            f"{file or 'no file'} is not on disk, so there is nothing to measure — a budget "
            f"is about what a loader pays, and a file that is not there pays nothing"
        ),
    )


def _tools(config: Config, address: str, key: str, declared: int | None) -> Measured:
    """What the served surface costs now — `cost --tools`' own reading, taken here."""
    from roadkeep.serving import surface  # noqa: PLC0415 - RK260

    sent = surface(config)
    if key == "characters":
        largest = max(sent.tools, key=lambda one: one[1], default=("", 0))
        return Measured(
            address=address,
            unit="utf-16 code units, per tool",
            worst=largest[1],
            where=largest[0],
            sites=len(sent.tools),
            declared=declared,
        )
    return Measured(
        address=address,
        unit="utf-16 code units, the whole surface",
        worst=sent.characters,
        where=f"{len(sent.tools)} tool(s) and the handshake",
        sites=1,
        declared=declared,
    )


def _listings(config: Config, address: str, declared: int | None) -> Measured:
    """What the widest unscoped listing costs now, over the files that hold lines (RK1476).

    `list --role <r>` with no `--block` prints the whole of one file, and which file is widest
    is the only reading that can price a ceiling held against all of them. The bare form and
    not `--ids` or `--json`: the widest of the three is the one a ceiling has to clear, and it
    is the one every other caller's is measured under.

    The ledger is normally the answer and that is the point — a listing over a file that only
    grows is the answer `[reads] list` exists to bound, and a number chosen without seeing it
    is a number chosen against the roadmap.
    """
    from roadkeep.config import LINE_ROLES  # noqa: PLC0415 - RK260
    from roadkeep.counting import Census  # noqa: PLC0415 - RK260
    from roadkeep.kernel.schema import width  # noqa: PLC0415 - RK260

    widest, where, sites = 0, "", 0
    for role in LINE_ROLES:
        if not config.has(role):
            continue
        try:
            listed = width(Census.read(config, role).listed(ids=False))
        except (KeyError, OSError):
            # A role declared and unreadable is not this reading's to refuse: `lint` opens
            # every one of them and says so with a path, and a `govern` that raised here
            # would answer a question about a number with a question about a file.
            continue
        sites += 1
        if listed > widest:
            widest, where = listed, role
    if not sites:
        return Measured(
            address=address,
            unit="utf-16 code units, per unscoped listing",
            declared=declared,
            refuses=False,
            unmeasured=(
                "no file of lines to list, so there is nothing to price — a ceiling declared "
                "now is one the first file written measures itself against"
            ),
        )
    return Measured(
        address=address,
        unit="utf-16 code units, per unscoped listing",
        worst=widest,
        where=where,
        sites=sites,
        declared=declared,
        # Over it is where the ledger permanently is, and the whole point of the number.
        refuses=False,
    )


def _reads(config: Config, address: str, declared: int | None, key: str = "brief") -> Measured:
    """What the widest brief costs now — `cost --brief`'s own reading, taken here (RK1286).

    The read this project recommends over reading the file, priced the way every other number
    in this table is: by the reader that owns the question. The **widest** and not the median
    is the reading, for that verb's reason — a brief that fits on the average task and not on
    the hardest one is a brief a session replaces exactly when the file is longest.
    """
    if key == "list":
        return _listings(config, address, declared)
    from roadkeep.budgeting import brief_budget  # noqa: PLC0415 - RK260

    found = brief_budget(config)
    if found.widest is None:
        return Measured(
            address=address,
            unit="utf-16 code units, per brief",
            declared=declared,
            unmeasured=(
                "no open line to brief, so there is nothing to price — a ceiling declared "
                "now is one the first task filed measures itself against"
            ),
        )
    return Measured(
        address=address,
        unit="utf-16 code units, per brief",
        worst=found.widest.characters,
        where=found.widest.id,
        sites=len(found.briefs),
        declared=declared,
    )


def govern(
    config: Config,
    address: str,
    at: int,
    *,
    file: str = "",
    role: str = "",
    because: str = "",
    instead: str = "",
) -> Declared:
    """Declare one governed number, against the reading that decides it (RK1272).

    Validated whole before anything is written, which is every other write here: a number the
    corpus breaks, an address this build has no key for, or a config with no table to put it in
    each cost a refusal and an untouched file.

    ``instead`` is the same sentence placed the other way (RK1367): `because` **stacks** on
    whatever argued the number before it, which is right while each paragraph argues about the
    same question, and this one **replaces** the run — the case where the question was settled
    differently and the argument above the key is now for a reading nothing takes. Naming both
    is refused, the two being two acts, and what came out is on :attr:`Declared.displaced`.

    Neither writes prose (L4). The verb wraps a sentence and places it, and — here — says
    which lines it took to do so.
    """
    if because and instead:
        raise ValueError(
            "`--because` stacks an argument onto the one above the key and `--instead` "
            "replaces it, so naming both is asking for two placements of one sentence: pass "
            "`--because` where this number is a decision about the last one, and `--instead` "
            "where the reading that decided it has moved"
        )
    if config.source is None:
        raise ValueError(
            "this project declares no roadkeep.toml, so there is no table to write a number "
            f"into: `{invocation()} init` scaffolds one, and every limit is declared there"
        )
    measured = reading(config, address, file=file, role=role)
    if measured.over(at):
        raise Violated(address, at, measured.worst, measured.where, 1)
    if address.startswith("budgets.") and not measured.sites:
        # The same argument as `Violated` for the other absence: a budget for a file that is
        # not there is `budget.absent` to the gate, so writing one is declaring a finding.
        raise ValueError(
            f"{file or 'no file'} is not in this repository, so a budget on it would be a "
            f"limit nothing pays: `budget --file` lists what this project holds, and a file "
            f"that exists is the one thing a budget is about"
        )
    table, key = _addressed(config, address)
    written = _spelled(table, key, file=file, role=role)
    # The lines, not the flag: an argument that wrapped to nothing placed nothing, and an
    # answer reporting a write that did not happen is the one thing no read here may do
    # (RK1295) — the caller this transport is reached from cannot see the file to tell.
    argument = _argued(config, because or instead)
    text, lineno, before, stands, displaced = _inserted(
        config.source, written, at, argument, withdrawing=bool(instead)
    )
    config.source.write_text(text, encoding="utf-8", newline="")
    return Declared(
        address=address,
        at=at,
        measured=measured,
        lineno=lineno,
        before=before,
        argued=bool(argument),
        standing=stands,
        displaced=displaced,
    )


def _spelled(table: str, key: str, *, file: str, role: str) -> tuple[str, str, str]:
    """The `(heading, key, unit)` this write addresses, as the file spells them.

    A `<role>` or a `<path>` in the published name is a table declared once per something the
    project names, so the heading is composed from what the caller passed rather than from the
    placeholder — and a path is quoted, that being how TOML spells a key with a stop in it.

    ``unit`` is non-empty only for `[budgets]`, whose value is an **inline table**: the address
    there is the file and the two numbers live inside it, so the key and the thing being set
    are two names rather than one. Every other table's value is a scalar and says so with `""`.
    """
    if table == "budgets.<path>":
        return "[budgets]", f'"{file}"', key
    if table == "limits" and role:
        return f"[limits.{role}]", key, ""
    return f"[{table}]", key, ""


def _because(
    config: Config, table: str, key: str, *, file: str, role: str
) -> tuple[str, ...]:
    """The argument standing above one key in `roadkeep.toml`, verbatim (RK1296).

    The contiguous comment run directly above the row, with the `#` and one space taken off
    and nothing else touched. Whether those lines were placed by `--because` or written by
    hand years ago is not a question this can answer and not one worth asking: what argues
    the number is what is above it.

    A project with no config, a table nobody declared or a key nobody wrote each answer with
    nothing, which is the same answer a key with no comment above it gives — and correct in
    all four, an argument being absent either way.
    """
    if config.source is None or not config.source.exists():
        return ()
    heading, spelled, _ = _spelled(table, key, file=file, role=role)
    lines = config.source.read_text(encoding="utf-8").splitlines()
    inside = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("["):
            if inside:
                return ()
            inside = stripped == heading
        elif inside and "=" in stripped and _named(stripped) == spelled.strip('"'):
            start = _run(lines, index)
            return tuple(line.lstrip()[1:].strip() for line in lines[start:index])
    return ()


def _above(lines: list[str], index: int, because: tuple[str, ...]) -> bool:
    """Whether `because` is already the last thing standing above `index` (RK1294).

    The **tail** of the comment run and not the whole of it: a key under a table's own
    scaffolded explanation has that text above it for good, and the argument stacked onto it
    last session is above it too. What a re-run would duplicate is the bottom of that stack.
    """
    return bool(because) and tuple(lines[max(index - len(because), 0) : index]) == because


def _inserted(
    source: Path,
    written: tuple[str, str, str],
    at: int,
    because: tuple[str, ...] = (),
    *,
    withdrawing: bool = False,
) -> tuple[str, int, int | None, bool, tuple[str, ...]]:
    """The config with one key set, byte for byte otherwise (`adopting._with_role`'s rule).

    A targeted edit and never a serialiser: a `tomllib` round-trip drops the comments a
    config is mostly made of, and this file's comments are the arguments for its numbers —
    which is the one thing this verb exists to keep beside them.

    A key already there is **rewritten in place**, not appended: a second declaration of one
    number is a file `tomllib` reads one way and a reader reads the other. Where the value is
    an inline table the *other* unit inside it is carried across, for the same reason — a
    `bytes` declared last year is not something a `lines` call decided to drop.

    The author's argument lands **above** the row wherever the row lands, and **stacks** on
    whatever argued the number before it (RK1293): a raise is a decision about the previous
    decision, and this project's own `[tools]` entry is five of them written that way by hand.

    **Except where it is that same argument**, byte for byte, in which case nothing is written
    and the fourth return says so (RK1294). The number is idempotent already; the sentence
    beside it is a second decision only when it is a second sentence, and a retried call, a
    replayed capture or an unsure re-run is not one. Byte-for-byte and no wider: whether two
    sentences mean the same thing is a judgement, and this tool has no model (L4).

    ``withdrawing`` is `--instead` (RK1367), and it is the one path that **deletes**: the
    contiguous comment run above the row — the same span :func:`_because` reads back and
    `govern <key>` prints, so the caller replacing it has been shown it — comes out, and the
    argument lands in its place. Only where the key is already there, an argument being
    withdrawn from somewhere; a key this file does not carry has nothing above it, and the
    write is the stacking one with an empty stack. What came out is the fifth return, because
    a deletion nobody is told about is history removed.
    """
    heading, key, unit = written
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    table, last = None, None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("["):
            if stripped == heading:
                table = index
            elif table is not None and index > table:
                break
        elif table is not None and index > table and "=" in stripped:
            last = index
            if _named(stripped) == key.strip('"'):
                before = _number(stripped, unit)
                lines[index] = _row(key, at, unit, standing=stripped)
                stands = _above(lines, index, because)
                # The run comes out first, so `index` is re-taken against the shortened file
                # rather than adjusted by a count computed before the splice.
                # And only where there is a sentence to put in its place (RK1295): an argument
                # that wrapped to nothing placed nothing, so it withdraws nothing either —
                # otherwise `--instead "   "` is the silent deletion this flag is built not
                # to be, and the answer would report a reason where the file has none.
                displaced: tuple[str, ...] = ()
                if withdrawing and because and not stands:
                    start = _run(lines, index)
                    displaced = tuple(lines[start:index])
                    del lines[start:index]
                    index = start
                placed = () if stands else because
                lines[index:index] = placed
                return "".join(lines), index + len(placed) + 1, before, stands, displaced
    row = _row(key, at, unit)
    if table is None:
        # The table is opened where the key is written, which is `criterion add`'s rule about a
        # heading: a project that never declared one has no place for the first number, and a
        # verb that refused would send the author to the hand edit this exists to end.
        opened = _opened(lines, heading, row, because)
        return "".join(opened), len(opened), None, False, ()
    into = (last if last is not None else table) + 1
    return (
        "".join([*lines[:into], *because, row, *lines[into:]]),
        into + len(because) + 1,
        None,
        False,
        (),
    )


def _run(lines: list[str], index: int) -> int:
    """Where the contiguous comment run above `index` starts (RK1367).

    :func:`_because`'s own scan, over lines in hand rather than over the file, so the span a
    read hands back and the span a `--instead` replaces cannot come apart.
    """
    start = index
    while start > 0 and lines[start - 1].lstrip().startswith("#"):
        start -= 1
    return start


def _row(key: str, at: int, unit: str = "", standing: str = "") -> str:
    """One declaration line: a scalar, or an inline table with the other unit carried over."""
    if not unit:
        return f"{key} = {at}\n"
    inside = dict(_pairs(standing))
    inside[unit] = at
    spelled = ", ".join(f"{name} = {value}" for name, value in inside.items())
    return f"{key} = {{ {spelled} }}\n"


def _pairs(line: str) -> tuple[tuple[str, int], ...]:
    """The `name = <number>` pairs inside an inline table, in the order the file wrote them."""
    if "{" not in line:
        return ()
    body = line[line.index("{") + 1 : line.rindex("}")] if "}" in line else ""
    return tuple(
        (found.group(1), int(found.group(2)))
        for found in re.finditer(r"(\w+)\s*=\s*(-?\d+)", body)
    )


def _named(line: str) -> str:
    return line.split("=", 1)[0].strip().strip('"')


def _number(line: str, unit: str = "") -> int | None:
    """What the line declares now — the scalar, or the one unit inside an inline table."""
    if unit:
        return dict(_pairs(line)).get(unit)
    found = re.search(r"-?\d+", line.split("=", 1)[1])
    return int(found.group()) if found else None


def _opened(
    lines: list[str], heading: str, row: str, because: tuple[str, ...] = ()
) -> list[str]:
    """The file with a new table appended, separated by one blank line and no more."""
    end = len(lines)
    while end > 0 and not lines[end - 1].strip():
        end -= 1
    return [*lines[:end], "\n", f"{heading}\n", *because, row]


def _argued(config: Config, because: str) -> tuple[str, ...]:
    """The author's argument as comment lines, filled to this project's own width (RK1293).

    Filled and never one long line, because the file it lands in is read by a person and every
    comment already in it wraps. The width is the project's `[limits] prose` — the one number
    here about how wide written prose is — so a config whose author chose 72 gets 72 rather
    than a column this module picked.

    The prose is the author's verbatim (L4). What this composes is the `#` and the wrapping,
    which is the same split every field of every write here already takes.
    """
    if not because:
        return ()
    import textwrap  # noqa: PLC0415 - RK260

    return tuple(
        f"{line}\n"
        for line in textwrap.wrap(
            " ".join(because.split()),
            width=config.schema.prose_width,
            initial_indent="# ",
            subsequent_indent="# ",
            break_long_words=False,
            break_on_hyphens=False,
        )
    )
