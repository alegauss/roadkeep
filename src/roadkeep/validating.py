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
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from roadkeep.config import Config
from roadkeep.kernel.document import Continuation, Document
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

#: The codes a refused verdict carries. `validation.verdict` is the code the gate reports for a
#: hand-written token outside the set, so the door and the backstop name one rule.
VERDICT = "validation.verdict"
SAW = "validation.saw"


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
    """Refuse a verdict outside the set, or a sentence the ledger could not hold, all at once.

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
    if out:
        raise SchemaError(tuple(out))


class Unshipped(ValueError):
    """A verdict on work nothing has shipped (RK1690).

    Refused where the ledger has no entry, and where the roadmap still holds the line open —
    a half that shipped is an entry, and a verdict under it would read as a verdict on the
    whole — and where the entry is a retirement, which left without anything to try.
    """

    def __init__(self, task_id: str, *, why: str) -> None:
        self.task_id = task_id
        super().__init__(f"{task_id} {why}: a verdict is about work that shipped")


class Repeated(ValueError):
    """An entry already carrying two verdicts, which is a rewrite that failed (RK1690).

    Refused rather than resolved to either: which of the two is the last is not a fact the
    file holds, and `record amend --lines` is the door that rewrites a span somebody read.
    """

    def __init__(self, task_id: str, where: str, linenos: Sequence[int]) -> None:
        self.task_id = task_id
        spelled = ", ".join(str(one) for one in linenos)
        super().__init__(
            f"{where}: {task_id} carries {len(linenos)} verdicts (lines {spelled}), and a "
            f"verdict is rewritten in place — so which is the last is not a fact the file "
            f"holds: correct the entry with `record amend {task_id} --lines`, then validate"
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

    def save(self) -> tuple[Path, ...]:
        """Write the ledger and answer it (RK1130), or nothing where nothing moved."""
        return self.ledger.save() if self.changed else ()

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        where = config.relative(config.path("changelog"))
        if not self.changed:
            return f"{self.task_id} unchanged: the entry already carries that verdict"
        rows = [f"{self.task_id} validated  {where}:{self.lineno}  {self.verdict}", self.rendered]
        if self.replaced:
            # Said at the one door that could be read as having kept both: the last verdict
            # wins, and a reader who did not see the old one go would count two.
            rows.append(f"  replaced {self.replaced}, rewritten in place: the last verdict wins")
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
            **_wrote_json(config, wrote),
        }


def validate(config: Config, task_id: str, verdict: str, *, saw: str) -> Validated:
    """Write what a person saw under the ledger entry for `task_id` (RK1690).

    Appended as the entry's last line where it carries none, and rewritten where it stands
    where it carries one — so a second verdict replaces the first and never sits beside it.
    Everything else under the entry stays verbatim: a `checked` line, and a hand-wrapped
    paragraph, are both text this write was not asked about.
    """
    from roadkeep.shipping import Ambiguous  # noqa: PLC0415 - shipping reads this module

    check(config, verdict, saw)
    ledger = config.document("changelog")
    where = config.relative(config.path("changelog"))
    if task_id in config.document("roadmap").by_id():
        roadmap = config.relative(config.path("roadmap"))
        raise Unshipped(task_id, why=f"is still open in {roadmap}")
    twins = tuple(entry for entry in ledger.entries if entry.task.id == task_id)
    if not twins:
        raise Unshipped(task_id, why=f"is not in {where}")
    if len(twins) > 1:
        raise Ambiguous(task_id, where, tuple(entry.lineno for entry in twins))
    entry = twins[0]
    if entry.task.status == ledger.schema.retired_marker:
        raise Unshipped(task_id, why="was retired and never shipped")

    under = ledger.lines[entry.index + 1 : entry.stop]
    held = [entry.index + 1 + at for at, line in enumerate(under) if is_verdict_line(line)]
    if len(held) > 1:
        raise Repeated(task_id, where, [one + 1 for one in held])
    line = verdict_line(verdict, saw)
    if held:
        index = held[0]
        standing = ledger.lines[index].rstrip("\r\n")
        before = read_verdict(standing)
        replaced = "" if before is None else before.verdict
        if standing == line:
            return Validated(task_id, ledger, index + 1, verdict, line, changed=False)
        document = ledger.replace_line(index, line)
    else:
        index, replaced = entry.stop, ""
        document = ledger.insert_line(index, line)
    # The one check, made against the re-parse for `rewrite_entry`'s reason: a tail is whatever
    # the parser reads as one, so whether the line came back as this entry's is its question.
    owned = document.by_id()[task_id]
    if owned.stop != entry.stop + (0 if held else 1):
        raise Continuation(task_id, 1, owned.stop - entry.stop, line)
    return Validated(task_id, document, index + 1, verdict, line, replaced=replaced)
