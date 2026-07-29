"""A task line as data, before it is a line (RK1).

Everything else in roadkeep is downstream of this module: `add` validates here
before it renders, `lint` validates here instead of re-implementing the format as
regexes over prose, and the round-trip invariant (L3) compares against
:meth:`Schema.render`. A rule that lives in two places is a rule two places can
disagree about, so the schema lives in exactly one.

Seven fields carry a task: ``id``, ``status``, ``block``, ``deps``, ``symptom``,
``why``, ``ref``. What the schema enforces:

* **Lengths** — ``symptom`` 120, ``why`` 200, rendered line 320. These are the P90
  of the lines that already read well, not a round number.
* **One sentence for ``why``** — a second sentence is the signal that the content
  belongs in the improvements file, which is what ``ref`` points at.
* **Shape** — id against the configured prefix, status in the configured marker
  set, ``deps`` well-formed and non-self-referential, ``ref`` present and anchored.
* **Nothing that would break a round-trip** — no newlines, no stray ``**``, no
  leading or trailing whitespace in a field. These are refused rather than
  trimmed: silently normalizing text the tool misunderstood is what L3 forbids.

What it deliberately does **not** enforce: that ``symptom`` states what does not
work rather than naming a fix. That rule matters as much as the lengths — a line
named after its solution cannot be falsified, so it never gets closed, only
abandoned — but it is not decidable by a schema, and a tool that guesses at prose
quality has started writing prose (L4). It stays a documented rule, enforced by
the skill and by review.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from enum import StrEnum

# Status markers, as bare codepoints — no variation selectors, because the
# governed files carry none and a round-trip compares bytes.
DESIGNED = "\N{CLIPBOARD}"  # 📋
IDEA = "\N{THOUGHT BALLOON}"  # 💭
PARTIAL = "\N{HOURGLASS WITH FLOWING SAND}"  # ⏳
IN_PROGRESS = "\N{HAMMER AND WRENCH}"  # 🛠
SHIPPED = "\N{WHITE HEAVY CHECK MARK}"  # ✅

#: The markers a roadmap line may carry. ✅ is not among them: shipped work lives
#: in the changelog, and a roadmap that can say "done" is a second source of truth.
OPEN_MARKERS = (DESIGNED, IDEA, PARTIAL, IN_PROGRESS)

EM_DASH = "\N{EM DASH}"
ARROW = "\N{RIGHTWARDS ARROW}"
NO_DEPS = EM_DASH

_PREFIX_RE = re.compile(r"^[A-Z][A-Z0-9]{0,7}$")
_BLOCK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-]{0,15}$")
# A section, with any depth of subsection: "I.1", "XIV.8.7", and bare "XLV" —
# Turing points at nine whole sections, and a pointer that resolves is the rule
# (RK15), not the presence of a dot. [0-9] and not \d: an id is ASCII.
_REF_RE = re.compile(r"^[0-9IVXLCDM]+(?:\.[0-9]+)*$")

# A terminator followed by whitespace, i.e. a sentence that has a successor. A
# trailing period never matches because the field is measured stripped.
_SENTENCE_BREAK_RE = re.compile(r"[.!?][\"')\]]*\s")

# Abbreviations whose period is not a sentence boundary. Decimals ("3.11") and
# anchors ("§0.1") are already safe: no whitespace follows their period.
_ABBREVIATIONS = frozenset({"e.g.", "i.e.", "etc.", "vs.", "cf.", "al.", "no."})

_TERMINATORS = (".", "!", "?")

#: The pointer's two addressing schemes (RK27). "id" is the default because it is the
#: one an author cannot get wrong; "outline" exists for backlogs already numbered.
REF_SCHEMES = frozenset({"id", "outline"})

# What a dep token names (RK28). Derived from the text the corpora already write —
# `Block P` in Shio, `real design partners` in Turing — because inventing a sigil
# would make two live backlogs wrong rather than describing them.
_BLOCK_DEP_RE = re.compile(r"^Block ([A-Za-z0-9][A-Za-z0-9.\-]{0,15})$")
# Anything shaped like an id: letters then a digit. `RK007`, `RK9x` and `SH341` are
# mistakes to report, not external work to accept.
_ID_SHAPE_RE = re.compile(r"^[A-Za-z]{1,8}[0-9][A-Za-z0-9]*$")
# The shape of a range, without judging its direction, so that `RK9–RK5` can be
# reported instead of quietly becoming "outside the backlog".
_RANGE_SHAPE_RE = re.compile(r"^[A-Za-z]{1,8}[0-9]+\s*[-–—]\s*[A-Za-z]{0,8}[0-9]+$")


class DepKind(StrEnum):
    """The four things a dep can name, as the live backlogs already write them.

    The distinction exists because they resolve differently and one of them does not
    resolve at all: an :attr:`EXTERNAL` dep is unresolvable *by construction*, and
    reporting it as pending makes a permanently blocked task read like the next one
    to start. :attr:`RANGE` is here for the opposite reason — Turing's
    `(deps: T451–T457)` *is* resolvable, so calling it external would be a false
    statement rather than a missing one.
    """

    TASK = "task"
    BLOCK = "block"
    RANGE = "range"
    EXTERNAL = "external"


class SchemaError(ValueError):
    """Raised by :meth:`Schema.check`, carrying every violation, not the first.

    A refusal that reports one problem per run turns a single fix into a
    conversation, so the exception is a batch.
    """

    def __init__(self, violations: tuple[Violation, ...]) -> None:
        self.violations = tuple(violations)
        super().__init__("; ".join(str(v) for v in self.violations))


@dataclass(frozen=True, slots=True)
class Violation:
    """One rule, broken once. ``code`` is stable; ``message`` is for a human."""

    code: str
    field: str
    message: str

    def __str__(self) -> str:
        return f"{self.field}: {self.message} [{self.code}]"


@dataclass(frozen=True, slots=True)
class Dep:
    """A dependency, and the status its target carried when the line was written.

    ``marker`` is a cache of another line's status, derived on write (RK8); the
    model carries it because the rendered line does. It is any marker and not only
    ✅ — Shio's backlog annotates ⏳ and 📋 deps too, and since the marker is
    derived from the target's status there is no reason one status would be
    unrepresentable.
    """

    id: str
    marker: str | None = None

    @property
    def shipped(self) -> bool:
        return self.marker == SHIPPED

    def render(self) -> str:
        return f"{self.id} {self.marker}" if self.marker else self.id


@dataclass(frozen=True, slots=True)
class Task:
    """The six-field task line as data. Construction never validates.

    Validation is a separate call so that a caller can collect every violation
    (``lint``) or refuse before rendering (``add``) — a constructor that raises
    can only ever report the first problem, and cannot hold a line long enough
    to explain what is wrong with it.
    """

    id: str
    status: str
    block: str
    symptom: str
    why: str
    deps: tuple[Dep, ...] = ()
    ref: str | None = None

    def __post_init__(self) -> None:
        # Accept plain ids for convenience; keep the field a tuple of Dep so
        # rendering and validation have one shape to handle.
        coerced = tuple(Dep(d) if isinstance(d, str) else d for d in self.deps)
        object.__setattr__(self, "deps", coerced)

    @property
    def dep_ids(self) -> tuple[str, ...]:
        return tuple(d.id for d in self.deps)


@dataclass(frozen=True, slots=True)
class Schema:
    """The format, as configuration (L6).

    The defaults are this repository's, which is also the conformance fixture:
    if a limit here cannot express `docs/ROADMAP.md`, the limit is wrong and not
    the lines. `roadkeep.toml` (RK3) builds one of these instead of the tool
    hardcoding any project's vocabulary.
    """

    prefix: str = "RK"
    markers: tuple[str, ...] = OPEN_MARKERS
    shipped_marker: str = SHIPPED
    symptom_max: int = 120
    why_max: int = 200
    line_max: int = 320
    ref_required: bool = True
    #: The ledger's own status *is* ✅, so it is the one file where the shipped
    #: marker is legal. Set by :meth:`as_ledger`, never by hand.
    shipped_allowed: bool = False
    #: The ledger carries no `(deps: …)` group: a dependency is a planning fact
    #: about unshipped work, and a shipped line has none left to state.
    deps_field: bool = True
    #: How the rationale section is addressed (RK27). ``"id"`` derives the pointer
    #: from the line's own id — nothing to choose when writing, nothing to renumber
    #: when shipping. ``"outline"`` is the hand-numbered `§x.y` that Shio and Turing
    #: already use, kept because migrating a live outline is a separate decision
    #: from adopting the tool.
    ref_scheme: str = "id"

    def __post_init__(self) -> None:
        if self.ref_scheme not in REF_SCHEMES:
            raise ValueError(
                f"ref_scheme must be one of {', '.join(sorted(REF_SCHEMES))}, "
                f"got {self.ref_scheme!r}"
            )
        if not _PREFIX_RE.match(self.prefix):
            raise ValueError(f"prefix must be uppercase alphanumeric: {self.prefix!r}")
        if not self.markers:
            raise ValueError("markers must not be empty")
        if self.shipped_marker in self.markers and not self.shipped_allowed:
            raise ValueError(
                f"{self.shipped_marker} is the shipped marker and may not also be an "
                "open marker: a roadmap that can say 'done' disagrees with the changelog"
            )
        for name in ("symptom_max", "why_max", "line_max"):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be positive")

    def as_ledger(self) -> Schema:
        """The same format as the changelog reads it (L6, applied to a sibling file).

        Marker ✅, no deps, no pointer — the rationale section is deleted when the
        task ships, so a pointer to it could not resolve. One schema with two
        configurations beats two grammars that drift apart.
        """
        return replace(
            self,
            markers=(self.shipped_marker,),
            shipped_allowed=True,
            deps_field=False,
            ref_required=False,
        )

    # -- rendering ---------------------------------------------------------

    def render(self, task: Task) -> str:
        """The canonical line. The only writer of this format.

        `lint`'s comparison, `add`'s output and the round-trip test all read the
        line from here, so "canonical" is a fact about one function rather than a
        claim in a document.
        """
        head = f"- {task.status} **{task.id}**"
        if self.deps_field:
            deps = ", ".join(d.render() for d in task.deps) or NO_DEPS
            head += f" (deps: {deps})"
        line = f"{head} **{task.symptom}** {EM_DASH} {task.why}"
        if task.ref:
            # In the id scheme the pointer is *derived*, not echoed: a line carrying
            # the wrong anchor stops round-tripping instead of being preserved, which
            # is what makes the anchor impossible to get wrong rather than merely
            # discouraged.
            anchor = task.id if self.ref_scheme == "id" else task.ref
            line += f" {ARROW} §{anchor}"
        return line

    # -- validation --------------------------------------------------------

    def id_pattern(self) -> re.Pattern[str]:
        """Ids are ``<prefix><n>``, non-contiguous, and never zero-padded.

        Padding would make ``RK01`` and ``RK1`` two spellings of one id, and the
        next-id maximum (RK4) is taken over these strings.
        """
        return re.compile(rf"^{re.escape(self.prefix)}[1-9][0-9]*$")

    def validate(self, task: Task) -> tuple[Violation, ...]:
        """Every violation, in field order. Empty means the task conforms."""
        out: list[Violation] = []
        out.extend(self._check_identity(task))
        out.extend(self._check_deps(task))
        out.extend(self._check_symptom(task))
        out.extend(self._check_why(task))
        out.extend(self._check_ref(task))

        rendered = self.render(task)
        if len(rendered) > self.line_max:
            out.append(
                Violation(
                    "line.too-long",
                    "line",
                    f"rendered line is {len(rendered)} characters, "
                    f"limit is {self.line_max}: move the remainder to "
                    f"the improvements section",
                )
            )
        return tuple(out)

    def _check_identity(self, task: Task) -> list[Violation]:
        out: list[Violation] = []
        if not self.id_pattern().match(task.id):
            out.append(
                Violation(
                    "id.format",
                    "id",
                    f"expected {self.prefix}<n> with no leading zero, got {task.id!r}",
                )
            )
        if task.status == self.shipped_marker and not self.shipped_allowed:
            out.append(
                Violation(
                    "status.shipped",
                    "status",
                    f"{self.shipped_marker} belongs in the changelog, not the roadmap",
                )
            )
        elif task.status not in self.markers:
            out.append(
                Violation(
                    "status.unknown",
                    "status",
                    f"{task.status!r} is not one of {' '.join(self.markers)}",
                )
            )
        if not task.block:
            # Shio keeps a "## Priority queue" section above its blocks; a task
            # parked there has no block, and inferring one would file it under
            # whatever heading happened to precede it.
            out.append(
                Violation(
                    "block.missing", "block", "a task line lives under a block heading"
                )
            )
        elif not _BLOCK_RE.match(task.block):
            out.append(
                Violation("block.format", "block", f"not a block label: {task.block!r}")
            )
        return out

    def classify_dep(self, dep: Dep) -> DepKind:
        """What this dep names — a task, a block, a range, or work outside the backlog.

        Ordered so that neither a mistake nor a resolvable dep can hide as external:
        `Block P` first, then a range, then anything id-shaped (valid or not), and
        only what none of those match is external.
        """
        if _BLOCK_DEP_RE.match(dep.id):
            return DepKind.BLOCK
        if self.range_of_dep(dep) is not None:
            return DepKind.RANGE
        if _ID_SHAPE_RE.match(dep.id):
            return DepKind.TASK
        return DepKind.EXTERNAL

    def block_of_dep(self, dep: Dep) -> str | None:
        """The block label a block dep names, or None if it names something else."""
        match = _BLOCK_DEP_RE.match(dep.id)
        return match.group(1) if match else None

    def range_of_dep(self, dep: Dep) -> tuple[int, int] | None:
        """The inclusive `(first, last)` a range dep names, or None.

        Both `T451–T457` and `T451–457` occur in the wild, and the dash may be a
        hyphen or an en dash. A descending range is not a range: it is returned as
        None so the token falls through and gets reported instead of resolved.
        """
        pattern = re.compile(
            rf"^{re.escape(self.prefix)}([1-9][0-9]*)"
            rf"\s*[-–—]\s*(?:{re.escape(self.prefix)})?([1-9][0-9]*)$"
        )
        match = pattern.match(dep.id)
        if not match:
            return None
        first, last = int(match.group(1)), int(match.group(2))
        return (first, last) if first <= last else None

    def _check_deps(self, task: Task) -> list[Violation]:
        if task.deps and not self.deps_field:
            return [
                Violation(
                    "deps.unexpected",
                    "deps",
                    "this file carries no deps field: a shipped line has no "
                    "dependency left to state",
                )
            ]
        out: list[Violation] = []
        ids = self.id_pattern()
        seen: set[str] = set()
        allowed = (*self.markers, self.shipped_marker)
        for dep in task.deps:
            kind = self.classify_dep(dep)
            # An id-shaped token that is not an id of this project is a typo or a
            # paste from another backlog. Prose is not: real work waits on a whole
            # block, and on things that are not work at all (RK28).
            if kind is DepKind.TASK and not ids.match(dep.id):
                out.append(
                    Violation(
                        "deps.format", "deps", f"not an id of this project: {dep.id!r}"
                    )
                )
            elif kind is not DepKind.RANGE and _RANGE_SHAPE_RE.match(dep.id):
                # It looks like a range and did not parse as one, so it would resolve
                # as "outside the backlog" — a false statement, not a missing one.
                out.append(
                    Violation(
                        "deps.range",
                        "deps",
                        f"{dep.id!r} reads as a range but does not ascend from a "
                        f"{self.prefix} id",
                    )
                )
            if dep.marker is not None and dep.marker not in allowed:
                out.append(
                    Violation(
                        "deps.marker",
                        "deps",
                        f"{dep.marker!r} is not a status marker: a dep annotation "
                        f"caches the target's status and nothing else",
                    )
                )
            if dep.id == task.id:
                out.append(
                    Violation("deps.self", "deps", f"{task.id} depends on itself")
                )
            if dep.id in seen:
                out.append(Violation("deps.duplicate", "deps", f"{dep.id} listed twice"))
            seen.add(dep.id)
        return out

    def _check_symptom(self, task: Task) -> list[Violation]:
        out = self._check_text("symptom", task.symptom, self.symptom_max)
        if "**" in task.symptom:
            # Only the symptom reserves '**': it is what closes the field. Bold
            # inside a `why` round-trips (25 of Shio's lines use it), and grading
            # emphasis in someone's sentence is prose-grading, which is not the
            # tool's job (L4).
            out.append(
                Violation(
                    "symptom.markup",
                    "symptom",
                    "'**' closes the symptom and cannot appear inside it",
                )
            )
        if task.symptom.strip().endswith(_TERMINATORS):
            out.append(
                Violation(
                    "symptom.sentence",
                    "symptom",
                    "symptom is a phrase naming what does not work, not a sentence: "
                    "drop the terminating punctuation",
                )
            )
        return out

    def _check_why(self, task: Task) -> list[Violation]:
        out = self._check_text("why", task.why, self.why_max)
        why = task.why.strip()
        if why and not why.endswith(_TERMINATORS):
            out.append(
                Violation("why.no-terminator", "why", "why is a sentence: end it")
            )
        if _sentence_count(why) > 1:
            out.append(
                Violation(
                    "why.sentences",
                    "why",
                    "why is one sentence; a second sentence is the signal that it "
                    "belongs in the improvements section this line points at",
                )
            )
        return out

    def _check_ref(self, task: Task) -> list[Violation]:
        if not task.ref:
            if self.ref_required:
                return [
                    Violation(
                        "ref.missing", "ref", "every task points at its rationale section"
                    )
                ]
            return []
        if task.ref.startswith("§"):
            return [
                Violation(
                    "ref.sigil", "ref", f"store the anchor without §: {task.ref.lstrip('§')!r}"
                )
            ]
        if self.ref_scheme == "id":
            if task.ref != task.id:
                return [
                    Violation(
                        "ref.mismatch",
                        "ref",
                        f"the pointer is the task's own id ({task.id}), derived on "
                        f"render; {task.ref!r} names a section chosen by hand",
                    )
                ]
            return []
        if not _REF_RE.match(task.ref):
            return [Violation("ref.format", "ref", f"not an <x.y> anchor: {task.ref!r}")]
        return []

    def check(self, task: Task) -> Task:
        """Return the task, or raise :class:`SchemaError` with every violation."""
        violations = self.validate(task)
        if violations:
            raise SchemaError(violations)
        return task

    def _check_text(self, field: str, value: str, limit: int) -> list[Violation]:
        """The checks that apply to both prose fields, including round-trip safety."""
        out: list[Violation] = []
        if not value.strip():
            out.append(Violation(f"{field}.empty", field, "must not be empty"))
            return out
        if "\n" in value or "\r" in value:
            out.append(
                Violation(f"{field}.newline", field, "a task is one line: no newlines")
            )
        if value != value.strip():
            out.append(
                Violation(
                    f"{field}.whitespace",
                    field,
                    "leading or trailing whitespace (refused, not trimmed: the tool "
                    "does not silently rewrite text it did not author)",
                )
            )
        if len(value) > limit:
            out.append(
                Violation(
                    f"{field}.too-long",
                    field,
                    f"{len(value)} characters, limit is {limit}: move the remainder "
                    f"to the improvements section rather than compressing it away",
                )
            )
        return out


def _sentence_count(text: str) -> int:
    """Sentences in a stripped one-line field, ignoring known abbreviations."""
    count = 1 if text else 0
    for match in _SENTENCE_BREAK_RE.finditer(text):
        token = text[: match.start() + 1].split()[-1].lower()
        if token in _ABBREVIATIONS or len(token) == 2 and token[0].isalpha():
            continue  # "e.g. ", "A. Oliveira" — a period, not a boundary
        count += 1
    return count
