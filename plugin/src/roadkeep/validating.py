"""What a person saw when they tried a shipped entry — the verdict, and the one door to it (RK1690).

`ship --checked <lead>` (RK1460) is the shipping session saying it verified a criterion it
declared. That is not a person using the thing, and nothing else in the ledger is either: an
entry records what landed and is silent about whether anybody ever looked.

**One continuation line, in the grammar that is already there.** `shipping.carried` writes
`checked **<lead>** <why>` under an entry; this writes one derived word beside it, indented by
two exactly as that one is — `validated **worked** Reopened the task and the answer was there.`
The address is the verdict, out of :data:`VERDICTS` and refused at input (L1); the sentence is
the caller's own, flattened and never composed (L4). The third verdict keeps the set honest: a
refactor has nothing a person can open, and saying so is somebody's act rather than a heuristic
this tool would guess.

**No date and no author.** `attesting` argues it for claims — the identity behind a write lives
outside the repository, and the commit is where it belongs — so `origin <id>` resolves it.

**The last verdict wins and the line is rewritten in place** (RK7). Nothing a failure found is
lost by that: the defect it found is an open line of its own.

The writer and its recogniser sit together, for RK1507's reason: two readers of one shape
drift silently, in the direction that costs.

**And the read that makes the state actionable** (RK1691): a verdict nobody can enumerate is a
verdict nobody writes. :func:`unvalidated` is `unclosed`'s mirror in shape and in temperament —
a report and never a gate, since whether work needs a person is a judgement this tool has no
model for, and an entry that shipped an hour ago is unvalidated as its ordinary state. A gate
that fired on every ship is one somebody switches off, and it would take the honest findings
with it. :func:`looked` is the same walk as two counts, which is what `stats` carries for a
caller drawing twenty backlogs who wants the figure without the list.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from roadkeep.config import Config
from roadkeep.kernel.document import Continuation, Document, Entry

if TYPE_CHECKING:  # a name for the annotation only: `authoring` is imported where it is called
    from roadkeep.authoring import Insertion
from roadkeep.kernel.schema import SchemaError, Violation, mangled, over_by, width

#: The closed set a verdict is drawn from. A tuple and not a config key: the set is what the
#: gate and every reader agree a verdict *is*, and a project that spelled its own would be a
#: ledger no other copy of this tool could read.
VERDICTS: tuple[str, ...] = ("worked", "failed", "nothing to see")

#: The one word this write derives, in front of the caller's verdict — `shipping._CHECKED`'s
#: sibling, and the same argument: prose the tool writes before the caller's, so a reader can
#: tell a verdict from a criterion that was checked.
_VALIDATED = "validated"

#: Two spaces, the word and the opening bold — what identifies the line, the verdict and the
#: sentence being the caller's.
_PREFIX = f"  {_VALIDATED} **"

_LINE = re.compile(rf"^{re.escape(_PREFIX)}(?P<verdict>[^*]+)\*\*(?: (?P<saw>.*))?$")

#: The codes a verdict can be wrong under, declared once for the door and the gate (RK1693). The
#: first two are refused where `validate` composes the line and reported where a hand wrote
#: one; the last two are states only a hand or a merge reaches — the write collapses a second
#: verdict and refuses an open line — so the gate is where they are read at all.
VERDICT = "validation.verdict"
SAW = "validation.saw"
REPEATED = "validation.repeated"
OPEN = "validation.open"


def verdict_line(verdict: str, saw: str) -> str:
    """The continuation line this tool writes under a ledger entry (RK1690).

    Indented by two, which is what a continuation of a bullet is: the parse reads the entry as
    wrapped, and `show` prints every line the entry owns.
    """
    return f"{_PREFIX}{verdict}** {' '.join(saw.split())}"


def is_verdict_line(line: str) -> bool:
    """Whether this line is one :func:`verdict_line` wrote — a prefix, as `carries` is."""
    return line.strip("\r\n").startswith(_PREFIX)


@dataclass(frozen=True, slots=True)
class Verdict:
    """One verdict read back off the line that holds it."""

    verdict: str
    saw: str


def read_verdict(line: str) -> Verdict | None:
    """The verdict and the sentence a verdict line holds, or None for any other line."""
    match = _LINE.match(line.strip("\r\n"))
    if match is None:
        return None
    return Verdict(verdict=match.group("verdict"), saw=(match.group("saw") or "").strip())


def check(config: Config, verdict: str, saw: str) -> None:
    """Refuse a verdict outside the set, or a sentence the ledger could not hold, all at once."""
    out = violations(config, verdict, saw)
    if out:
        raise SchemaError(tuple(out))


def violations(config: Config, verdict: str, saw: str) -> list[Violation]:
    """Every rule a verdict line is held to, for the door and the gate alike (RK1693).

    The sentence is held to the ledger's own `why` limit, being a sentence under one of its
    entries, and to the codec check every field is (RK1497). Length and shape only: that the
    sentence says what somebody actually saw is the caller's claim, as a symptom's is (L4).
    """
    out: list[Violation] = []
    if verdict not in VERDICTS:
        out.append(
            Violation(
                VERDICT,
                "verdict",
                f"{verdict!r} is not a verdict: one of "
                f"{', '.join(repr(one) for one in VERDICTS)}",
            )
        )
    said = " ".join(saw.split())
    schema = config.schema_for("changelog")
    if not said:
        out.append(Violation(SAW, "saw", "a verdict nobody described is a checkbox"))
    elif width(said) > schema.why_max:
        out.append(
            Violation(
                SAW,
                "saw",
                over_by(
                    width(said),
                    schema.why_max,
                    measured=said,
                    source=schema.source_of("why_max"),
                ),
            )
        )
    out += mangled("saw", said)
    return out


def verdicts_under(ledger: Document, entry: Entry) -> tuple[int, ...]:
    """The 0-based indices of the verdict lines an entry owns, in file order."""
    return tuple(
        index
        for index in range(entry.index + 1, entry.stop)
        if is_verdict_line(ledger.lines[index])
    )


class Unshipped(ValueError):
    """A verdict on work nothing has shipped (RK1690).

    Refused where the ledger has no entry, and where the roadmap still holds the line open —
    a half that shipped is an entry, and a verdict under it would read as a verdict on the
    whole — and where the entry is a retirement, which left without anything to try.
    """

    def __init__(self, task_id: str, *, why: str) -> None:
        self.task_id = task_id
        super().__init__(f"{task_id} {why}: a verdict is about work that shipped")


class Twice(ValueError):
    """A verdict on an id the ledger states twice (RK1690).

    `shipping.Ambiguous`' refusal and for its reason — which entry the verdict is about is not a
    fact any file holds — spelled here because `shipping` reads this module for `carries`.
    """

    def __init__(self, task_id: str, where: str, linenos: Sequence[int]) -> None:
        self.task_id = task_id
        lines = ", ".join(str(one) for one in linenos)
        super().__init__(
            f"{where} states {task_id} at {len(linenos)} lines ({lines}): which of them this "
            f"verdict is about is not a fact any file holds — de-duplicate it first"
        )


@dataclass(frozen=True, slots=True)
class Validated:
    """One verdict written under a ledger entry, or rewritten where it stood (RK1690)."""

    task_id: str
    ledger: Document
    #: The verdict line's own number, which is where a reader looks.
    lineno: int
    verdict: str
    rendered: str
    #: The verdict this one replaced, or `""` where the entry carried none.
    replaced: str = ""
    #: False where the entry already carried exactly this verdict and nothing was written.
    changed: bool = True
    #: The open line a failure filed in the same transaction (RK1694), or None.
    filed: Insertion | None = None

    def save(self) -> tuple[Path, ...]:
        """Write the ledger — and the roadmap a failure filed into — as one (RK1130, RK1694).

        Both or neither, which is the whole of `--files`: a verdict and the line it owes left as
        two writes is how the second one gets forgotten, `ship`'s argument for its three.
        """
        from roadkeep.kernel.document import save_all  # noqa: PLC0415 - RK260

        if self.filed is not None:
            return save_all(
                self.ledger if self.changed else None, self.filed.document, self.filed.prose
            )
        return self.ledger.save() if self.changed else ()

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        from roadkeep.authoring import follow_ups, owed_rows  # noqa: PLC0415 - RK260
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        where = config.relative(config.path("changelog"))
        if not self.changed and self.filed is None:
            return f"{self.task_id} unchanged: the entry already carries that verdict"
        rows = [f"{self.task_id} validated  {where}:{self.lineno}  {self.verdict}", self.rendered]
        if self.replaced:
            # Said at the one door that could be read as having kept both: the last verdict
            # wins, and a reader who did not see the old one go would count two.
            rows.append(f"  replaced {self.replaced}, rewritten in place: the last verdict wins")
        if self.filed is not None:
            filed = self.filed
            rows.append(f"  filed    {filed.entry.raw.rstrip()}")
            if filed.needs is not None:
                # The design the new line points at is still the caller's to write (L4), so the
                # pointer owes one and the answer says so, as `add`'s does.
                calls = follow_ups(filed.needs, filed.needs_role, filed.opens)
                rows += owed_rows(filed.needs, calls)
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "id": self.task_id,
            "file": config.relative(config.path("changelog")),
            "line": self.lineno,
            "verdict": self.verdict,
            "rendered": self.rendered,
            # Null where the entry carried none, so a consumer tells a first verdict from one
            # that overwrote another without diffing the file.
            "replaced": self.replaced or None,
            "changed": self.changed,
            # The line a failure filed (RK1694), with the design it still owes where it owes one
            # — `absent`-shaped as `reopen` publishes it — or null where nothing was filed.
            "filed": None if self.filed is None else self._filed(),
            **_wrote_json(config, wrote),
        }

    def _filed(self) -> dict[str, object]:
        from roadkeep.authoring import follow_ups  # noqa: PLC0415 - RK260

        filed = self.filed
        assert filed is not None
        return {
            "id": filed.entry.task.id,
            "block": filed.entry.task.block,
            "line": filed.entry.lineno,
            "rendered": filed.entry.raw.rstrip(),
            **(
                {}
                if filed.needs is None
                else {
                    "needs": filed.needs,
                    "doors": [
                        {"argv": one.split(), "what": "the design this pointer resolves to"}
                        for one in follow_ups(filed.needs, filed.needs_role, filed.opens)
                    ],
                }
            ),
        }


class NotAFailure(ValueError):
    """`--files` on a verdict that found nothing to file (RK1694).

    A `worked` that filed a line would be filing work nobody found, and `nothing to see` has
    nothing to report — so the flag is refused naming the one verdict that takes it.
    """

    def __init__(self, verdict: str) -> None:
        super().__init__(
            f"--files files the defect a failed validation found, and {verdict!r} found none: "
            f"pass it with `failed`, or leave it off"
        )


def validate(
    config: Config, task_id: str, verdict: str, *, saw: str, files: str | None = None
) -> Validated:
    """Write what a person saw under the ledger entry for `task_id` (RK1690).

    Appended as the entry's last line where it carries none, and rewritten where it stands
    where it carries one — so a second verdict replaces the first and never sits beside it.
    Everything else under the entry stays verbatim: a `checked` line, and a hand-wrapped
    paragraph, are both text this write was not asked about.

    **An entry already carrying two is collapsed to this one** (RK1693), at the first's place.
    Which of the two was the last is not a fact the file holds, and it does not need to be:
    the call being made now is the latest verdict by construction, so writing it over both is
    the rule the file broke, applied — and the door `validation.repeated` names.

    **`files` writes the line a failure found** (RK1694), in the transaction that writes the
    verdict, as `ship --decides` writes a decision: the open line lands under the entry's own
    block with `files` as its symptom and the `saw` sentence as its why — both the caller's, so
    nothing here composes prose — and it is refused through every rule `add` holds a line to,
    before anything is written. Only with `failed`: `worked` found nothing to file and
    `nothing to see` has nothing to report.
    """
    check(config, verdict, saw)
    if files is not None and verdict != "failed":
        raise NotAFailure(verdict)
    ledger = config.document("changelog")
    where = config.relative(config.path("changelog"))
    if task_id in config.document("roadmap").by_id():
        roadmap = config.relative(config.path("roadmap"))
        raise Unshipped(task_id, why=f"is still open in {roadmap}")
    twins = tuple(entry for entry in ledger.entries if entry.task.id == task_id)
    if not twins:
        raise Unshipped(task_id, why=f"is not in {where}")
    if len(twins) > 1:
        raise Twice(task_id, where, tuple(entry.lineno for entry in twins))
    entry = twins[0]
    if entry.task.status == ledger.schema.retired_marker:
        raise Unshipped(task_id, why="was retired and never shipped")

    line = verdict_line(verdict, saw)
    written = _written(ledger, entry, line)
    filed = None
    if files is not None:
        from roadkeep.authoring import prepared  # noqa: PLC0415 - RK260

        filed = prepared(
            config, block=entry.task.block, symptom=files, why=" ".join(saw.split())
        )
    return Validated(
        task_id,
        written.document,
        written.index + 1,
        verdict,
        line,
        replaced=written.replaced,
        changed=written.changed,
        filed=filed,
    )


@dataclass(frozen=True, slots=True)
class _Written:
    document: Document
    index: int
    replaced: str = ""
    changed: bool = True


def _written(ledger: Document, entry: Entry, line: str) -> _Written:
    """The ledger with `line` as the entry's one verdict, appended or written over the rest."""
    held = verdicts_under(ledger, entry)
    if held:
        index = held[0]
        standing = ledger.lines[index].rstrip("\r\n")
        before = read_verdict(standing)
        replaced = "" if before is None else before.verdict
        if standing == line and len(held) == 1:
            return _Written(ledger, index, changed=False)
        # The extra ones first and from the bottom, so the indices above them still hold.
        document = ledger
        for extra in reversed(held[1:]):
            document = document.remove_line(extra)
        document = document.replace_line(index, line)
    else:
        index, replaced = entry.stop, ""
        document = ledger.insert_line(index, line)
    # The one check, made against the re-parse for `rewrite_entry`'s reason: a tail is whatever
    # the parser reads as one, so whether the line came back as this entry's is its question.
    task_id = entry.task.id
    owned = document.by_id()[task_id]
    expected = entry.stop - (len(held) - 1 if held else -1)
    if owned.stop != expected:
        raise Continuation(task_id, 1, owned.stop - entry.stop, line)
    return _Written(document, index, replaced)


# -- the read: what nobody has looked at (RK1691) -----------------------------


def _carries_verdict(ledger: Document, entry: Entry) -> bool:
    return bool(verdicts_under(ledger, entry))


class NoStart(KeyError):
    """`validation.from` naming an id the ledger does not carry (RK1692).

    Refused as every other declared address is: a start nothing answers is a question the
    project believes it is asking and is not, and silence would read as *nothing to look at*.
    """

    def __init__(self, source: str, start: str, where: str) -> None:
        self.start = start
        super().__init__(
            f"{source}: validation.from names {start}, which {where} does not carry — it "
            f"names the first ledger entry a verdict is asked of, so it has to be one"
        )


def _walked(config: Config) -> Mapping[str, str] | None:
    """Which commit first wrote each id into the ledger, or None where there is no history."""
    from roadkeep.history import HistoryUnavailable, added_ids  # noqa: PLC0415 - RK260

    try:
        return added_ids(config, "changelog")
    except (HistoryUnavailable, OSError):
        return None


def _started(
    config: Config, ledger: Document, walked: Mapping[str, str] | None
) -> frozenset[str] | None:
    """The ids shipped at or after where looking starts, or None where history cannot say.

    **Placed on the history and never on the file**, because the file is grouped by block and
    the ships are not: an entry shipped this morning into Block A sits above one shipped last
    year into Block J. So the start is a commit — the one that first wrote `from` into the
    ledger, or, with no `from`, the one that declared the table — and what is in the question
    is every entry the ledger carries now that it did not carry just before that commit. A
    start nobody has committed yet is the working tree's, which is where the next ship lands.
    """
    from roadkeep.history import (  # noqa: PLC0415 - RK260
        HistoryUnavailable,
        commits_touching,
        content_at,
        resolves,
    )

    declared = config.validation
    assert declared is not None
    now = frozenset(ledger.by_id())
    if walked is None:
        return None
    try:
        if declared.start is not None:
            if declared.start not in now:
                raise NoStart(
                    config.relative(config.source or config.root),
                    declared.start,
                    config.relative(config.path("changelog")),
                )
            sha = walked.get(declared.start)
        else:
            source = (config.source or config.root / "roadkeep.toml").resolve()
            try:
                relative = source.relative_to(config.root)
            except ValueError:
                relative = source
            opened = commits_touching(config.root, "[validation]", relative)
            sha = opened[0].sha if opened else None
        base = f"{sha}^" if sha else "HEAD"
        if resolves(config, base):
            earlier = Document.parse(content_at(config, base, "changelog"), schema=ledger.schema)
            after = now - frozenset(earlier.by_id())
        else:
            # The start is the first commit there is, or there is none yet: nothing came before.
            after = now
    except (HistoryUnavailable, OSError, ValueError):
        return None
    if declared.start is None or sha is None:
        return after
    # One commit carries no order among the entries it wrote — an adopted ledger arrives in
    # one — so inside the commit that wrote `from` the file's own order is the only one there
    # is, and what sits above `from` there is history the declaration named as such.
    position = {entry.task.id: at for at, entry in enumerate(ledger.entries)}
    first = position[declared.start]
    return frozenset(
        one for one in after if walked.get(one) != sha or position.get(one, first) >= first
    )


@dataclass(frozen=True, slots=True)
class _Asked:
    """The entries the question is asked of, and why there may be none."""

    ledger: Document
    entries: tuple[Entry, ...] = ()
    #: False where this project declares no `[validation]`.
    governed: bool = True
    #: False where the history could not place the start.
    placed: bool = True
    walked: Mapping[str, str] | None = None


def _about(config: Config, block: str | None) -> _Asked:
    """Every ledger entry a verdict is asked of, in file order.

    Exactly the entries :func:`validate` accepts, so the list never offers one the write then
    refuses: a retirement left with nothing to try, and an id the roadmap still holds open is
    a half whose verdict would read as a verdict on the whole. And only those at or after where
    looking starts (RK1692) — none at all where the project has not declared the question. A
    label the ledger declares no heading for is refused by the census's own words, a filter
    matching nothing being the answer a finished backlog also gives.
    """
    from roadkeep.counting import Census  # noqa: PLC0415 - counting reads this module

    ledger = config.document("changelog")
    if block is not None:
        Census.of(config, "changelog", ledger).select(block=block)
    if config.validation is None:
        return _Asked(ledger, governed=False)
    walked = _walked(config)
    started = _started(config, ledger, walked)
    if started is None:
        return _Asked(ledger, placed=False)
    still_open = set(config.document("roadmap").by_id()) if config.on_disk("roadmap") else set()
    return _Asked(
        ledger,
        tuple(
            entry
            for entry in ledger.entries
            if (block is None or entry.task.block == block)
            and entry.task.status != ledger.schema.retired_marker
            and entry.task.id not in still_open
            and entry.task.id in started
        ),
        walked=walked,
    )


@dataclass(frozen=True, slots=True)
class Looked:
    """The two counts a verdict splits the shipped entries into (RK1691)."""

    validated: int = 0
    unvalidated: int = 0


def looked(config: Config, block: str | None = None) -> Looked | None:
    """How many of the entries a verdict is asked of carry one, and how many do not.

    None where the question is not asked — no `[validation]`, or no history to place its start —
    so `stats` prints no row rather than a zero that reads as *every one looked at*.
    """
    asked = _about(config, block)
    if not (asked.governed and asked.placed):
        return None
    carrying = sum(1 for entry in asked.entries if _carries_verdict(asked.ledger, entry))
    return Looked(validated=carrying, unvalidated=len(asked.entries) - carrying)


@dataclass(frozen=True, slots=True)
class Unlooked:
    """One shipped entry no person has left a verdict on."""

    task_id: str
    block: str
    symptom: str
    lineno: int
    #: The commit that first wrote the entry into the ledger — what `origin` answers as where it
    #: shipped — or `""` where the history could not say.
    commit: str = ""


@dataclass(frozen=True, slots=True)
class Unvalidated:
    """Every shipped entry carrying no verdict, and how many do (RK1691)."""

    file: str
    rows: tuple[Unlooked, ...] = ()
    validated: int = 0
    block: str | None = None
    #: False where this project declares no `[validation]` (RK1692): the list is not empty,
    #: it is not asked, and the answer says which with the command that asks it.
    governed: bool = True
    #: False where the history could not place where looking starts, for `Unclosed.searched`'s
    #: reason: an empty list here and an empty list because every entry carries a verdict are
    #: two answers, and only this tells them apart.
    placed: bool = True
    #: `validation.from` as declared, or None where looking starts at the table's own ship.
    start: str | None = None

    def stated(self) -> str:
        from roadkeep.provenance import invocation  # noqa: PLC0415 - RK260

        if not self.governed:
            return (
                f"this project declares no [validation], so no shipped entry is asked about — "
                f"`{invocation()} declare validation` opens it, and looking starts at the next "
                f"ship"
            )
        if not self.placed:
            return (
                "no history to read, so where looking starts cannot be placed and no entry is "
                "listed"
            )
        shipped = self.validated + len(self.rows)
        scope = f" under Block {self.block}" if self.block else ""
        since = f"from {self.start}" if self.start else "since [validation] was declared"
        if not shipped:
            return f"nothing has shipped {since}{scope}, so no entry is asked about yet"
        if not self.rows:
            return f"every one of {shipped} entr(ies) shipped {since}{scope} carries a verdict"
        out = [f"{len(self.rows)} of {shipped} entr(ies) shipped {since}{scope} carry no verdict"]
        for one in self.rows:
            out.append(
                f"  {one.task_id:<8} Block {one.block:<3} {one.commit[:8] or '-':<8}  {one.symptom}"
            )
        # The door, as every report here carries one (RK420): what closes a row is a person
        # saying what they saw, and the verb writes it rather than this read guessing.
        out.append(
            f"  validate `{invocation()} validate <id> <verdict> --saw …` once somebody has "
            f"tried it"
        )
        return "\n".join(out)

    def payload(self) -> dict[str, object]:
        return {
            "file": self.file,
            # Null where no block was named, which is the question rather than a missing answer.
            "block": self.block,
            "governed": self.governed,
            "placed": self.placed,
            "from": self.start,
            "validated": self.validated,
            "unvalidated": [
                {
                    "id": one.task_id,
                    "block": one.block,
                    "symptom": one.symptom,
                    "line": one.lineno,
                    "commit": one.commit or None,
                }
                for one in self.rows
            ],
        }


def unvalidated(config: Config, block: str | None = None) -> Unvalidated:
    """Every entry a verdict is asked of that carries none, in the ledger's own order.

    One walk of the ledger's history for the start and every commit column
    (`history.added_ids`), never one `origin` per row: that is a pickaxe per id, and a list of
    a thousand entries is the read this exists to make cheap enough to ask.
    """
    asked = _about(config, block)
    file = config.relative(config.path("changelog"))
    start = None if config.validation is None else config.validation.start
    if not (asked.governed and asked.placed):
        return Unvalidated(
            file=file, block=block, governed=asked.governed, placed=asked.placed, start=start
        )
    missing = tuple(
        entry for entry in asked.entries if not _carries_verdict(asked.ledger, entry)
    )
    shipped_in = asked.walked or {}
    return Unvalidated(
        file=file,
        rows=tuple(
            Unlooked(
                task_id=entry.task.id,
                block=entry.task.block,
                symptom=entry.task.symptom,
                lineno=entry.lineno,
                commit=shipped_in.get(entry.task.id, ""),
            )
            for entry in missing
        ),
        validated=len(asked.entries) - len(missing),
        block=block,
        start=start,
    )


