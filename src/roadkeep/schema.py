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
from dataclasses import dataclass

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
_REF_RE = re.compile(r"^[0-9IVXLCDM]+(?:\.[0-9]+)+$")

# A terminator followed by whitespace, i.e. a sentence that has a successor. A
# trailing period never matches because the field is measured stripped.
_SENTENCE_BREAK_RE = re.compile(r"[.!?][\"')\]]*\s")

# Abbreviations whose period is not a sentence boundary. Decimals ("3.11") and
# anchors ("§0.1") are already safe: no whitespace follows their period.
_ABBREVIATIONS = frozenset({"e.g.", "i.e.", "etc.", "vs.", "cf.", "al.", "no."})

_TERMINATORS = (".", "!", "?")


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
    """A dependency, and whether its target has shipped.

    ``shipped`` is a cache of another line's status and is derived on write
    (RK8); the model carries it because the rendered line does.
    """

    id: str
    shipped: bool = False

    def render(self, shipped_marker: str = SHIPPED) -> str:
        return f"{self.id} {shipped_marker}" if self.shipped else self.id


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

    def __post_init__(self) -> None:
        if not _PREFIX_RE.match(self.prefix):
            raise ValueError(f"prefix must be uppercase alphanumeric: {self.prefix!r}")
        if not self.markers:
            raise ValueError("markers must not be empty")
        if self.shipped_marker in self.markers:
            raise ValueError(
                f"{self.shipped_marker} is the shipped marker and may not also be an "
                "open marker: a roadmap that can say 'done' disagrees with the changelog"
            )
        for name in ("symptom_max", "why_max", "line_max"):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be positive")

    # -- rendering ---------------------------------------------------------

    def render(self, task: Task) -> str:
        """The canonical line. The only writer of this format.

        `lint`'s comparison, `add`'s output and the round-trip test all read the
        line from here, so "canonical" is a fact about one function rather than a
        claim in a document.
        """
        deps = ", ".join(d.render(self.shipped_marker) for d in task.deps) or NO_DEPS
        line = (
            f"- {task.status} **{task.id}** (deps: {deps}) "
            f"**{task.symptom}** {EM_DASH} {task.why}"
        )
        if task.ref:
            line += f" {ARROW} §{task.ref}"
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
        ids = self.id_pattern()

        if not ids.match(task.id):
            out.append(
                Violation(
                    "id.format",
                    "id",
                    f"expected {self.prefix}<n> with no leading zero, got {task.id!r}",
                )
            )

        if task.status == self.shipped_marker:
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

        if not _BLOCK_RE.match(task.block):
            out.append(
                Violation("block.format", "block", f"not a block label: {task.block!r}")
            )

        seen: set[str] = set()
        for dep in task.deps:
            if not ids.match(dep.id):
                out.append(
                    Violation(
                        "deps.format", "deps", f"not an id of this project: {dep.id!r}"
                    )
                )
            if dep.id == task.id:
                out.append(
                    Violation("deps.self", "deps", f"{task.id} depends on itself")
                )
            if dep.id in seen:
                out.append(Violation("deps.duplicate", "deps", f"{dep.id} listed twice"))
            seen.add(dep.id)

        out.extend(self._check_text("symptom", task.symptom, self.symptom_max))
        if task.symptom.strip().endswith(_TERMINATORS):
            out.append(
                Violation(
                    "symptom.sentence",
                    "symptom",
                    "symptom is a phrase naming what does not work, not a sentence: "
                    "drop the terminating punctuation",
                )
            )

        out.extend(self._check_text("why", task.why, self.why_max))
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

        if task.ref is None or task.ref == "":
            if self.ref_required:
                out.append(
                    Violation(
                        "ref.missing",
                        "ref",
                        "every task points at its rationale section",
                    )
                )
        elif task.ref.startswith("§"):
            out.append(
                Violation(
                    "ref.sigil",
                    "ref",
                    f"store the anchor without §: {task.ref.lstrip('§')!r}",
                )
            )
        elif not _REF_RE.match(task.ref):
            out.append(
                Violation("ref.format", "ref", f"not an <x.y> anchor: {task.ref!r}")
            )

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
        if "**" in value:
            out.append(
                Violation(
                    f"{field}.markup",
                    field,
                    "'**' is the field delimiter and cannot appear inside a field",
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
