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
  Two of those slots are *per-file* rather than per-format: the ledger carries no
  ``deps``, and a ledger where every entry shipped carries no marker either (RK43) —
  which is a marker derived from the file instead of repeated on all 920 of its lines.
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

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from enum import StrEnum

# Status markers, as bare codepoints — no variation selectors, because the
# governed files carry none and a round-trip compares bytes.
DESIGNED = "\N{CLIPBOARD}"  # 📋
IDEA = "\N{THOUGHT BALLOON}"  # 💭
PARTIAL = "\N{HOURGLASS WITH FLOWING SAND}"  # ⏳
IN_PROGRESS = "\N{HAMMER AND WRENCH}"  # 🛠
SHIPPED = "\N{WHITE HEAVY CHECK MARK}"  # ✅
#: A line that left the roadmap without shipping (RK32). Lives in the ledger beside ✅,
#: under the block it belonged to: a departure is a departure, and the block is the one
#: piece of provenance worth keeping when the design itself is deleted.
RETIRED = "\N{WASTEBASKET}"  # 🗑
#: A line set aside and still alive (RK96) — the one state that is neither open nor
#: terminal. It lives in the deferred store and nowhere else: a roadmap that can say
#: "paused" is a backlog counting work nobody is doing, and a ledger that can is a ledger
#: of departures one of which comes back.
DEFERRED = "\N{DOUBLE VERTICAL BAR}"  # ⏸

#: The markers a roadmap line may carry. ✅ is not among them: shipped work lives
#: in the changelog, and a roadmap that can say "done" is a second source of truth.
OPEN_MARKERS = (DESIGNED, IDEA, PARTIAL, IN_PROGRESS)

#: Which of those mean the design is not written yet (RK83). Ready and implementable are
#: two different states, and only the markers know the difference: a 💭 line offered to a
#: caller who asked to execute a block hands it a design session. Not a readiness gate —
#: `pick` still offers these — but a fact the answer states, and one `--designed` can skip.
UNDESIGNED = (IDEA,)

EM_DASH = "\N{EM DASH}"
ARROW = "\N{RIGHTWARDS ARROW}"
NO_DEPS = EM_DASH

_PREFIX_RE = re.compile(r"^[A-Z][A-Z0-9]{0,7}$")
_BLOCK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-]{0,15}$")
#: A section, with any depth of subsection: "I.1", "XIV.8.7", and bare "XLV" —
#: Turing points at nine whole sections, and a pointer that resolves is the rule
#: (RK15), not the presence of a dot. [0-9] and not \d: an id is ASCII.
#: Public because it reads the *heading* too (RK44): under the outline scheme a heading
#: numbers itself and the number is what announces it, so one pattern has to answer both
#: ends of the pointer or the two disagree about which sections exist.
#: The final segment may be **one lowercase letter** (RK47), which is measured and not
#: guessed: it admits exactly Turing's 20 `VII.2.a` headings across both prose files, and
#: a general alphanumeric segment admits not one thing more while also admitting
#: `VII.2.beta`, where `§VII.2` stops telling an anchor from a title's first word.
#: The *first* segment may be **one uppercase letter followed by a dot** (RK101), the same
#: measured admission one level up: commitclerk numbers its rationale by the roadmap's own
#: block letters, `§B.2` to `§J.9`, of which only C and D were read before — because those
#: letters happen to be roman numerals. The dot is what keeps a title's capitalised first
#: word prose, and a bare `§B` names a block rather than a section, so it stays refused.
OUTLINE_ANCHOR_RE = re.compile(r"^(?:[0-9IVXLCDM]+|[A-Z](?=\.))(?:\.[0-9]+)*(?:\.[a-z])?$")

#: The namespace an outline address may name in front of itself (RK340). `ref_scheme` is
#: read once per project and every outline starts at `I`, so two prose files each numbering
#: their own headings land in one flat set: measured in an adopting project, `IMPROVEMENTS.md`
#: and `STRATEGY.md` both open at `§I` and both declare a `§III`, `lint` reports four
#: `section.ambiguous`, and ten pointers resolve to nothing. A prefix is what makes `§S:I`
#: and `§I` two addresses, and the **separator is a colon** for a reason the alternative
#: makes plain: a dot is what an outline already segments by, so `§S.I` would be a child of
#: something called `S` to every reader that splits one.
REF_PREFIX_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
REF_SEPARATOR = ":"


def split_ref(ref: str) -> tuple[str, str]:
    """`S:I.2` → `("S", "I.2")`, and a bare `I.2` → `("", "I.2")` (RK340).

    One reader of the spelling, for the reason :func:`~roadkeep.sections.anchor_text` is one
    writer of it: an address parsed one way by the gate and another by the write is the
    disagreement that made the ambiguity unreportable in the first place. Partitioning and
    not a match, so an anchor carrying two colons keeps the tail verbatim and fails the
    *anchor* check with the text the author typed rather than being silently re-cut.
    """
    prefix, found, bare = ref.partition(REF_SEPARATOR)
    return (prefix, bare) if found else ("", ref)

# A terminator followed by whitespace, i.e. a sentence that has a successor. A
# trailing period never matches because the field is measured stripped.
_SENTENCE_BREAK_RE = re.compile(r"[.!?][\"')\]]*\s")

# Abbreviations whose period is not a sentence boundary. Decimals ("3.11") and
# anchors ("§0.1") are already safe: no whitespace follows their period.
_ABBREVIATIONS = frozenset({"e.g.", "i.e.", "etc.", "vs.", "cf.", "al.", "no."})

_TERMINATORS = (".", "!", "?")

#: The violations that already carry the line's own limit into a field the author writes
#: (RK183), and therefore the ones `line.too-long` stands down for.
_LENGTH_CODES = frozenset({"symptom.too-long", "why.too-long", "part.too-long"})


#: The pointer's two addressing schemes (RK27). "id" is the default because it is the
#: one an author cannot get wrong; "outline" exists for backlogs already numbered.
REF_SCHEMES = frozenset({"id", "outline"})

# What a dep token names (RK28). Derived from the text the corpora already write —
# `Block P` in Shio, `real design partners` in Turing — because inventing a sigil
# would make two live backlogs wrong rather than describing them. The word is the
# project's (RK75); only the shape after it is the format's.
BLOCK_LABEL = r"[A-Za-z0-9][A-Za-z0-9.\-]{0,15}"
#: The word a project files work under. `Block` for the two corpora the format was read
#: off, and not for the others: Dumont writes `Track`, cursarei writes `Fase`.
DEFAULT_HEADING_WORD = "Block"
#: Anything shaped like an id: letters then a digit. `RK007`, `RK9x` and `SH341` are
#: mistakes to report, not external work to accept. Public as a fragment because the
#: parser asks the same question: a bullet leading with a bold one is a ledger line whose
#: marker slot is empty (RK43), and a second spelling of "id-shaped" would disagree with
#: this one on the first `**Delete**`.
ID_SHAPE = r"[A-Za-z]{1,8}[0-9][A-Za-z0-9]*"
_ID_SHAPE_RE = re.compile(rf"^{ID_SHAPE}$")
#: The sub-letter a split id may carry where a project declares one (RK106). Lowercase, so
#: it can never be read as a family — those are uppercase by :data:`_PREFIX_RE` — and one,
#: because `T24b` is what Turing writes and `T24beta` would put the letter back in prose.
SUB_LETTER = r"[a-z]"
# The shape of a range, without judging its direction, so that `RK9–RK5` can be
# reported instead of quietly becoming "outside the backlog".
_RANGE_SHAPE_RE = re.compile(r"^[A-Za-z]{1,8}[0-9]+\s*[-–—]\s*[A-Za-z]{0,8}[0-9]+$")


#: Characters per word, for turning a budget that refuses into one that can be aimed at
#: (RK185). Measured over this repository's 392 written `symptom` and `why` fields: the
#: median is 5.5 and the 95th percentile 6.36, so this is the first round number above it
#: — an author who lands on the word aim clears the character gate about nineteen times in
#: twenty, and the twentieth is the refusal that already names the surplus (RK184).
#:
#: Not configuration (L6). A project declares how long its lines may be; this is a property
#: of the prose those lines are written in, and a `roadkeep.toml` field for it would be a
#: project declaring a fact about English. The corpus that fixes it is the one the format is
#: proven by, and `tests/test_budgeting.py` re-measures it rather than trusting this comment.
#:
#: Here rather than in `budgeting`, which is where it was written and is still read from
#: (RK201): the refusal needs the same conversion the aim is published with, and a second
#: constant one layer down would be the second opinion an author stops trusting.
CHARS_PER_WORD = 6.5


#: How far a body composed *to* its word limit overshot the count `words` takes (RK301).
#: Measured filing five tasks in one session: four `section add` bodies aimed at a declared
#: 250 arrived at 250, 251, 253 and 266, thirteen refusals between them, each costing the
#: whole paragraph re-sent. An author counts sentences and this counts tokens the markup
#: between them puts in or leaves out, so a limit published as its own aim is a limit hit
#: from above. The first round figure above the worst of the four, 266 against 250.
#:
#: Not configuration, for `CHARS_PER_WORD`'s reason: a project declares how long a section
#: may be, and this is a property of counting prose by hand.
BODY_HEADROOM = 0.07


def words(chars: int) -> int:
    """A character budget as the word count it is safe to aim at.

    Floored, never rounded: an aim that rounds up is an aim that lands over the gate half
    the time it is hit exactly, which is the retry this exists to remove.
    """
    return max(0, int(chars // CHARS_PER_WORD))


def body_aim(limit: int) -> int:
    """A word limit as the word count it is safe to compose to (RK301).

    :func:`words` for a budget already declared in words. There is no unit to convert, so
    what the aim buys is the headroom instead: composing to exactly the limit is what the
    thirteen measured refusals did, and a figure published as both the ceiling and the target
    is a target that lands over half the time it is hit. Floored, for :func:`words`' reason.
    """
    return max(0, int(limit / (1 + BODY_HEADROOM)))


def words_over(chars: int) -> int:
    """A character *surplus* as the words it takes to clear it (RK201).

    Ceiled, where :func:`words` floors, and for the same reason read backwards: an aim
    that rounds up overshoots the gate, and a cut that rounds down stops short of it.
    Naming four words to delete against a 29-character overrun sends the author back to
    the same refusal, which is the retry the figure exists to remove.
    """
    return max(1, math.ceil(chars / CHARS_PER_WORD))


def over_by(
    actual: int,
    limit: int,
    unit: str = "character",
    because: str = "",
    *,
    prose: bool = True,
) -> str:
    """The arithmetic every length refusal opens with, spelled in one place (RK184).

    An author handed a total and a limit derives the surplus and then does not act on it:
    the sequence measured against 320 was 327, then 303, then 300 — three rewrites where
    one subtraction would have done, because "move the remainder" is editorial advice and
    an author who takes it recomposes the sentence. A rewrite re-rolls the length.

    So the number to remove is stated, and the verb is **delete**: subtracting a count
    from a sentence is an operation that succeeds on the first attempt, where writing to a
    target length is one that converges by feedback. Where the text goes is still true and
    still said — after the arithmetic, because it answers a different question.

    One function, because a refusal spelled five ways is five things that drift apart, and
    the unit is a parameter for the two refusals counted in words rather than characters.

    **And the surplus is restated in words** (RK201). A character count is exact and it is
    not a unit the author composing the retry can count, which is the whole argument RK185
    made for publishing every aim in words — and it left this surface, the one an author
    reaches *after* the overrun, in characters alone. The exact figure stays first, because
    the approximation is derived from it; the word one follows, hedged, because it is. A
    refusal already counted in words gets no second copy of itself.

    ``prose`` is the caller's answer to whether a shorter *sentence* is the remedy (RK243).
    It is the caller's because only they know: `line.too-long` fires when no field is over
    the budget the line left it, so what does not fit is the structure around the prose —
    and its own message says exactly that, in the sentence the word figure would be
    appended to. Naming an edit that cannot work, beside the clause explaining why, is
    worse than naming no edit at all (RK16). One spelling either way, which is what this
    function exists for, so the switch is a parameter and not a second composer.
    """
    surplus = actual - limit
    deletion = f"delete {surplus} {_plural(surplus, unit)}"
    if prose and unit == "character":
        aim = words_over(surplus)
        deletion += f" {EM_DASH} about {aim} {_plural(aim, 'word')}"
    return f"{actual} {_plural(actual, unit)}, limit is {limit}{because}: {deletion}"


def _plural(count: int, unit: str) -> str:
    return unit if count == 1 else f"{unit}s"


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
    #: Which part of the work this entry records, where only part of it landed (RK121).
    #: A **ledger** field and the third state the model did not have: open in the roadmap
    #: and recorded in the changelog were the only two, so work delivered in halves was
    #: neither, and every project using this invented the same escape — `SH96 (local
    #: half)`, `SH275 (partial)` — in a spelling the grammar could not read. None is the
    #: ordinary entry: a shipment that needs no qualifier is not a partial one.
    part: str | None = None
    #: The whitespace the line starts with, kept verbatim (RK49). Part of the line and so
    #: part of the model: Shio nests four live tasks under the line that shipped their
    #: parent, and a render that dropped two spaces would stop 4 files from round-tripping.
    #: Never invented — no write sets it, so a nested line stays nested and nothing else is.
    indent: str = ""

    def __post_init__(self) -> None:
        # Accept plain ids for convenience; keep the field a tuple of Dep so
        # rendering and validation have one shape to handle.
        coerced = tuple(Dep(d) if isinstance(d, str) else d for d in self.deps)
        object.__setattr__(self, "deps", coerced)

    @property
    def dep_ids(self) -> tuple[str, ...]:
        return tuple(d.id for d in self.deps)


@dataclass(frozen=True, slots=True)
class Id:
    """One id, taken apart by the declaration that spells it (RK109).

    The three parts are exactly the three `[ids]` declares — the family (RK74), the
    number the next-id maximum is taken over (RK4), and the sub-letter a split task
    carries (RK106) — so a caller reads the same shape whatever the project wrote, and
    ``sub`` is `""` at a project that declares none rather than a case to remember.

    Produced only by :meth:`Schema.parse_id`, which is the *same* fragment
    :meth:`Schema.id_pattern` refuses a line with: a string this exists for is a string
    the gate admits, and the two used to be able to disagree.
    """

    family: str
    number: int
    sub: str = ""


def number_fragment(pad: int = 1) -> str:
    """The numeric part of an id, as a regex fragment, for a project that pads to ``pad``.

    **One spelling per number** is the whole rule (RK106). A number shorter than the
    declared width is zero-filled to it, a longer one is written out, and nothing else
    matches — so ``pad = 2`` admits `01`…`09`, `10`…`99` and `100` upward while refusing
    both `1` and `001`. That is what makes a declared width safe where padding in general
    is not: the hazard is a backlog that pads *sometimes*, and a project stating a width
    has said which of `D1` and `D01` is the id.

    ``pad = 1`` is the unpadded default, spelled as the bare ``[1-9][0-9]*`` a reader
    recognises rather than a one-branch alternation that means the same thing.
    """
    if pad < 2:
        return "[1-9][0-9]*"
    # One branch per significant-digit count below the width, each with the zeros that
    # fill it out, then one for everything at or above it. Written as repeated literals
    # rather than `{n}` counts because a declared width is 2 or 3 in practice, and
    # `0[1-9]` is read at a glance where `0{1}[1-9][0-9]{0}` is decoded.
    branches = ["0" * (pad - k) + "[1-9]" + "[0-9]" * (k - 1) for k in range(1, pad)]
    branches.append("[1-9]" + "[0-9]" * (pad - 1) + "[0-9]*")
    return "(?:" + "|".join(branches) + ")"


def _check_prefixes(prefixes: tuple[str, ...]) -> None:
    """Every family this backlog numbers has to be readable, and readable as one thing."""
    if not prefixes:
        raise ValueError("prefix must name at least one family")
    for prefix in prefixes:
        if not _PREFIX_RE.match(prefix):
            raise ValueError(f"prefix must be uppercase alphanumeric: {prefix!r}")
    if len(set(prefixes)) != len(prefixes):
        raise ValueError(f"prefix names a family twice: {list(prefixes)}")
    for prefix in prefixes:
        # `C` beside `C1` makes `C12` two ids — `C`+12 and `C1`+2 — and which one it is
        # would depend on the order the alternation happens to be written in.
        other = next((p for p in prefixes if p != prefix and p.startswith(prefix)), None)
        if other is not None:
            raise ValueError(
                f"prefix {prefix!r} and {other!r} cannot both be families: an id "
                f"starting {other!r} would read as either, and no rule breaks the tie"
            )


@dataclass(frozen=True, slots=True)
class Schema:
    """The format, as configuration (L6).

    The defaults are this repository's, which is also the conformance fixture:
    if a limit here cannot express `docs/ROADMAP.md`, the limit is wrong and not
    the lines. `roadkeep.toml` (RK3) builds one of these instead of the tool
    hardcoding any project's vocabulary.
    """

    #: Every family this backlog numbers, the first being the one new ids are minted
    #: under. One is the common case and three of the four live corpora; cursarei numbers
    #: six tracks and the letter *is* which track the work belongs to (RK74), so a single
    #: string would have made 521 of its lines unreadable rather than non-conforming.
    #: Nothing maps a family to anything — a track is not a block and not an owner.
    prefixes: tuple[str, ...] = ("RK",)
    #: The width the number is zero-filled to, `[ids] pad` (RK106). 1 is unpadded, which is
    #: what three of the four live corpora write; Dumont writes `D01` through `D09` on every
    #: line and was getting a finding for each. Declared rather than tolerated: the tool
    #: refuses padding in general because `D1` and `D01` would be two names for one task,
    #: and a *width* is the project answering that — every number has exactly one spelling
    #: again, and both the unpadded `D1` and the over-padded `D001` stay refused.
    id_pad: int = 1
    #: Whether an id may end in one lowercase letter, `[ids] suffix` (RK106) — Turing's
    #: `T24b`, a task split after its number was already cited in commits and issues, which
    #: is the thing an id is for. Off by default, because a letter is a second address for
    #: one number and only a backlog that already spells it should be able to. Never
    #: minted: :meth:`spell_id` counts, and a split is a `renumber --to`.
    id_suffix: bool = False
    markers: tuple[str, ...] = OPEN_MARKERS
    shipped_marker: str = SHIPPED
    #: The ledger's other legal marker (RK32). Not an open marker: a retired line is a
    #: record of a departure, and a roadmap that can say "retired" is a roadmap holding
    #: work nobody will do.
    retired_marker: str = RETIRED
    #: The deferred store's only legal marker (RK96) — the state between open and terminal.
    #: Held to the same rule as the two above and for the same reason: the file a line
    #: sits in is what says whether it is being worked, so a marker legal in two files is
    #: two files that can both claim one task.
    deferred_marker: str = DEFERRED
    #: The open markers whose design is still to be written (RK83), `[markers] undesigned`.
    #: A subset of :attr:`markers` — checked where it is typed, like the shipped/deferred
    #: clash, because this list only ever meets the open set inside `pick`. Nothing here
    #: refuses a line for carrying one: what it changes is what an answer *says*, and what
    #: `--designed` sets aside, since the bias belongs to the caller and not to the ranking.
    undesigned: tuple[str, ...] = UNDESIGNED
    symptom_max: int = 120
    why_max: int = 200
    #: How long a partial entry's qualifier may be (RK121). Short by design — it names
    #: *which half*, and the sentence about what landed is the `why` two characters away.
    #: The default clears the longest the corpus wrote (`the SH22 half`, 13) many times over
    #: and still refuses a qualifier that has become a second summary.
    part_max: int = 40
    #: Whether `why` is held to one sentence, and to ending in a stop. True everywhere by
    #: default, because the rule is what keeps a `why` from becoming the rationale — and
    #: switchable per role (`[rules.<role>]`, RK52) because a ledger written before the
    #: tool is 233 paragraphs of history, and a rule cannot be obeyed retroactively.
    one_sentence: bool = True
    terminator: bool = True
    line_max: int = 320
    #: A rationale section's budget, in **words** — the unit a paragraph has (RK9). The
    #: default clears the longest section in this repository (181 words) and no more:
    #: the file that motivated the tool reached 539 KB one honest paragraph at a time.
    section_max: int = 250
    #: The width prose is filled to when a section is written. A table or a list is left
    #: exactly as the author wrote it; only plain paragraphs are re-flowed.
    prose_width: int = 88
    #: Whether a line must point at a rationale section. True by default and switchable per
    #: role (`[rules.<role>]`, RK66), because it is a project's convention and not a fact
    #: about the format: one that derives its anchors from ids can demand the pointer, the
    #: section being one command away and the anchor unable to be wrong, while one that
    #: numbers by hand may have a task whose design is a single line — and inventing a
    #: section to satisfy a linter is the accretion this tool exists to refuse. What is never
    #: negotiable is the other direction: a pointer that *is* written must resolve.
    ref_required: bool = True
    #: The ledger's own status *is* ✅, so it is the one file where the shipped
    #: marker is legal. Set by :meth:`as_ledger`, never by hand.
    shipped_allowed: bool = False
    #: The same claim for the deferred store, whose own status is ⏸ (RK96). Set by
    #: :meth:`as_deferred`, never by hand.
    deferred_allowed: bool = False
    #: The ledger carries no `(deps: …)` group: a dependency is a planning fact
    #: about unshipped work, and a shipped line has none left to state.
    deps_field: bool = True
    #: Whether the line carries a status slot at all. False is a **ledger** stating once
    #: what every entry in it would otherwise repeat (RK43): both live ledgers write
    #: `- **T1** — …`, 755 lines in Turing and 234 in Shio, and the marker of a file
    #: where everything shipped is derivable from the file. Set by :meth:`as_ledger`.
    marker_field: bool = True
    #: Whether the line carries a bold symptom before the em dash. False is the other
    #: shape both live ledgers write — `- **T1** — <prose>`, 761 lines in Turing and 234
    #: in Shio — where the whole tail is the `why` and the split has no consumer, because
    #: nothing picks, blocks on or budgets a line that already shipped (RK48). Set by
    #: :meth:`as_ledger`.
    symptom_field: bool = True
    #: The project's declaration of the two above — `[ledger] marker` and `[ledger]
    #: symptom` in `roadkeep.toml` (L6). Read only by :meth:`as_ledger`: in the roadmap
    #: the marker *is* the status, so a roadmap without one could not tell 📋 from 🛠, and
    #: a roadmap without a symptom would be a backlog of reasons with no faults.
    ledger_marker: bool = True
    ledger_symptom: bool = True
    #: The word a heading files work under (RK75). `Block` by default, so nothing changes
    #: for a project that never declares it; `Track`, `Fase` or anything else for the three
    #: of four adopting corpora that chose their own. Only the word is configuration — a
    #: heading still declares exactly one label, and a dep still resolves against that same
    #: list, because that is what `pick`, `stats` and every block dep are over.
    heading_word: str = DEFAULT_HEADING_WORD
    #: How the rationale section is addressed (RK27). ``"id"`` derives the pointer
    #: from the line's own id — nothing to choose when writing, nothing to renumber
    #: when shipping. ``"outline"`` is the hand-numbered `§x.y` that Shio and Turing
    #: already use, kept because migrating a live outline is a separate decision
    #: from adopting the tool.
    ref_scheme: str = "id"
    #: The namespace this role's outline addresses live in (`[refs]`, RK340). Empty is every
    #: project that has not declared one, and every role under `ref_scheme = "id"`, where the
    #: anchor is the id and the ids are already one namespace the format keeps unique. Where
    #: it is set, this role answers **only** prefixed addresses and no bare one — which is
    #: what makes `§S:I` and `§I` two addresses rather than one read twice.
    ref_prefix: str = ""

    def __post_init__(self) -> None:
        if self.ref_scheme not in REF_SCHEMES:
            raise ValueError(
                f"ref_scheme must be one of {', '.join(sorted(REF_SCHEMES))}, "
                f"got {self.ref_scheme!r}"
            )
        if self.ref_prefix and not REF_PREFIX_RE.match(self.ref_prefix):
            raise ValueError(
                f"ref prefix must be one word of letters and digits starting with a "
                f"letter, got {self.ref_prefix!r}: it is written in front of an address "
                f"as {self.ref_prefix}{REF_SEPARATOR}<x.y>, so a dot in it would read as "
                f"an outline segment"
            )
        _check_prefixes(self.prefixes)
        if self.id_pad < 1:
            raise ValueError(
                f"id_pad must be at least 1, got {self.id_pad}: 1 is an unpadded id, and "
                f"there is no width below it to declare"
            )
        if not self.heading_word.strip() or self.heading_word != self.heading_word.strip():
            raise ValueError(
                f"heading word must be one bare word: {self.heading_word!r} — it is "
                f"joined to the label by exactly one space, on both the heading and the dep"
            )
        if not self.markers:
            raise ValueError("markers must not be empty")
        if self.shipped_marker in self.markers and not self.shipped_allowed:
            raise ValueError(
                f"{self.shipped_marker} is the shipped marker and may not also be an "
                "open marker: a roadmap that can say 'done' disagrees with the changelog"
            )
        if self.deferred_marker in self.markers and not self.deferred_allowed:
            raise ValueError(
                f"{self.deferred_marker} is the deferred marker and may not also be an "
                "open marker: a roadmap that can say 'paused' is a backlog `pick` reads "
                "as work waiting to be started"
            )
        for name in (
            "symptom_max",
            "why_max",
            "part_max",
            "line_max",
            "section_max",
            "prose_width",
        ):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be positive")

    @property
    def prefix(self) -> str:
        """The family a new id is minted under when the caller names none (RK74).

        The first declared, and not a default the tool chose: a project that numbers one
        family reads this as "the prefix", and one that numbers six has already said which
        track is its main line by writing it first.
        """
        return self.prefixes[0]

    @property
    def prefix_alternation(self) -> str:
        """The families as one regex fragment, ready to embed. `RK`, or `(?:C|G|L)`.

        One family stays bare, so a single-track project's `id_pattern` is still the
        `^RK[1-9][0-9]*$` a reader recognises — an MCP client shows this string, and a
        group nothing alternates over is punctuation that has to be read past.

        Longest first, so `CX` would win over `C`. A tie is impossible —
        :func:`_check_prefixes` refuses a family that starts another — but the alternation
        is still ordered, because a regex that only works because no input reaches its
        ambiguity is one that reads as though the order did not matter.
        """
        if len(self.prefixes) == 1:
            return re.escape(self.prefixes[0])
        ordered = sorted(self.prefixes, key=lambda p: (-len(p), p))
        return "(?:" + "|".join(re.escape(prefix) for prefix in ordered) + ")"

    @property
    def number_fragment(self) -> str:
        """The number an id of this project carries, as a regex fragment (RK106)."""
        return number_fragment(self.id_pad)

    def _fragment(self, named: bool, *, sub_required: bool = False) -> str:
        """The join itself, spelled once, with or without the three parts named (RK109).

        Two spellings of one fragment and not two fragments: a caller that embeds an id in
        a larger pattern cannot use named groups twice, and a caller that takes an id apart
        cannot count anonymous ones — so the *joining* is here, and each caller asks for the
        form it can read rather than reassembling the three declarations for itself.

        ``sub_required`` makes the sub-letter mandatory instead of optional, which is the
        one caller that wants the ids :meth:`spell_id` cannot reach rather than the ids a
        line may carry (:meth:`split_id_pattern`, RK111). A third form and not a third
        fragment, for the same reason there are two: the three declarations still join here.
        """
        family = self.prefix_alternation
        number = self.number_fragment
        tail = ""
        if self.id_suffix:
            tail = SUB_LETTER if sub_required else f"{SUB_LETTER}?"
        if not named:
            return f"{family}{number}{tail}"
        # An empty group where the project declares no sub-letter, so `parse_id` reads
        # `sub` unconditionally and a project without one is not a second code path.
        return f"(?P<family>{family})(?P<number>{number})(?P<sub>{tail})"

    @property
    def id_fragment(self) -> str:
        """A whole id as a regex fragment: the family, the number, and the sub-letter.

        The one place the three declarations are joined, because an id is matched in five —
        :meth:`id_pattern`, the scan the next id is a maximum over, both ends of a range
        dep, and the bold id `lint` and `origin` read out of prose — and a spelling only
        four of them knew would make an id legal on the line and invisible to the counter,
        which is how a number gets minted twice.
        """
        return self._fragment(named=False)

    @property
    def id_groups(self) -> str:
        """The same fragment with its three parts named `family`, `number` and `sub`.

        For the two callers that take an id *apart* rather than test one: :meth:`parse_id`,
        and the scan the next id is a maximum over (RK4), which used to build its own
        three-group copy — a third reader of a shape declared once. Embeddable exactly once
        in a pattern, named groups being unique; :attr:`id_fragment` is the other form.
        """
        return self._fragment(named=True)

    def parse_id(self, text: str) -> Id | None:
        """An id of this project taken apart, or None if this is not one (RK109).

        The single parse both the pattern and the ordering are derived from. Anything
        :meth:`id_pattern` refuses returns None here — under `pad = 2` that includes the
        `D1` the ordering used to read as 1 — so a caller cannot hold half the declaration:
        it either has all three parts or it has no id, and there is no third answer where a
        number was read out of a string the gate would reject.
        """
        match = re.fullmatch(self.id_groups, text)
        if match is None:
            return None
        return Id(match.group("family"), int(match.group("number")), match.group("sub"))

    def spell_id(self, family: str, number: int) -> str:
        """How this project writes an id — the one place a number becomes a name (RK106).

        Zero-filled to `[ids] pad`, so a project that pads gets `D10` from the counter and
        never a `D1` its own gate would then refuse. No sub-letter: the letter addresses a
        split of an id that already exists, and nothing derives that.
        """
        return f"{family}{number:0{self.id_pad}d}"

    def block_dep_pattern(self) -> re.Pattern[str]:
        """`<word> <label>` as a dep names it (RK28, RK75)."""
        return re.compile(rf"^{re.escape(self.heading_word)} ({BLOCK_LABEL})$")

    def heading_pattern(self) -> re.Pattern[str]:
        """`<word> <label>` as a heading declares it — the same label shape as the dep.

        The same, and not merely similar: a heading that declared `D` where the dep spells
        `D.1` would make `pick --block D.1` an answer about a block nothing declares, and
        the disagreement would be invisible because both halves parse.
        """
        return re.compile(
            rf"^{re.escape(self.heading_word)} (?P<label>{BLOCK_LABEL})(?:\s|$)"
        )

    def block_named(self, label: str) -> str:
        """How a report names a block — the project's word, so a refusal it prints is
        the text its own files carry rather than a vocabulary it never adopted."""
        return f"{self.heading_word} {label}"

    def _families(self) -> str:
        """The families as a refusal names them: `RK`, or `C/L/S/P/G/V` in declared order.

        Declared order and not the alternation's, because a message is read by the author
        who wrote the config and a reordering they did not make reads as a second list.
        """
        return "/".join(self.prefixes)

    def _id_shape(self) -> str:
        """How a refusal spells this project's id, including what `[ids]` declared (RK106).

        Derived, because the alternative is a message naming the built-in shape at a
        project whose own config legalised another — which is a refusal that reads as a
        bug in the tool and gets the config edited back.
        """
        shape = (
            f"{self._families()}<n> with no leading zero"
            if self.id_pad == 1
            else f"{self._families()}<n> zero-filled to {self.id_pad} digits"
        )
        return shape + (", plus at most one lowercase letter" if self.id_suffix else "")

    @property
    def is_ledger(self) -> bool:
        """This is the ledger's configuration — the one file whose own status is ✅.

        Named because two things read it and "shipped_allowed" only implies it: the marker
        that may be absent is the ledger's (RK43), and so is the advice a reject gives.
        """
        return self.shipped_allowed

    def as_ledger(self) -> Schema:
        """The same format as the changelog reads it (L6, applied to a sibling file).

        Marker ✅ or 🗑, no deps, no pointer — the rationale section is deleted when the
        task leaves, so a pointer to it could not resolve. One schema with two
        configurations beats two grammars that drift apart, and a retired line (RK32) is
        the same grammar again rather than a third: a departure with a different door.

        Two slots are the part a project can drop, both declared in `[ledger]`: the marker
        (RK43), because a ledger where every entry shipped says so once in the file rather
        than on every line, and the symptom (RK48), because `- **T1** — <prose>` is what a
        ledger written before this tool already spells — and on a shipped line the split
        between the fault and its outcome has no reader left.
        """
        return replace(
            self,
            markers=(self.shipped_marker, self.retired_marker),
            shipped_allowed=True,
            deps_field=False,
            ref_required=False,
            marker_field=self.ledger_marker,
            symptom_field=self.ledger_symptom,
        )

    @property
    def is_deferred(self) -> bool:
        """This is the deferred store's configuration — the one file whose status is ⏸."""
        return self.deferred_allowed

    def as_deferred(self) -> Schema:
        """The same format as the deferred store reads it (RK96, L6 again).

        The roadmap's shape with one marker swapped, and nothing else dropped. One marker,
        because the file *is* the state: a store that could also hold 📋 would be a second
        roadmap, and two files that both say a task is open eventually disagree about which
        one it is. Everything else stays, and that is what separates a pause from the
        ledger's two departures — the id every dependent names, the deps that are still
        deps, the symptom, and the `→ §id` pointer whose section is carried rather than
        deleted. :meth:`as_ledger` drops all three because a shipped line has no design and
        no blocker left; a deferred one has both, and a return that had to reinvent them
        would be a re-add under a new id.
        """
        return replace(self, markers=(self.deferred_marker,), deferred_allowed=True)

    def needs_design(self, status: str) -> bool:
        """Whether a line carrying this marker still has its design to write (RK83).

        A method rather than a comparison at the call site for the reason every other
        marker question is one: which codepoint means "idea" is `[markers] undesigned` and
        never a constant a query hardcoded. A ledger or deferred schema answers False for
        its own markers by the same rule, which is right — neither file is picked from.
        """
        return status in self.undesigned

    def marks(self, status: str) -> bool:
        """Whether a line carrying this status writes the marker slot at all (RK43, RK125).

        True everywhere except the ledger a project declared markerless — and there too for
        the one status that file cannot state about itself. `[ledger] marker = false` says
        *every entry in this file shipped*, which is exactly why the one that did not has to
        say so on its own line: there is no other slot for a departure, and a file whose
        lines carry no marker has nothing for this one to be inconsistent with.

        That is what keeps `retire` a door on an adopting project (RK125). The alternative
        reachable before this was `ship` with an outcome saying the work was decided against
        — a ✅ over work nobody did, which is the lie `marker = false` was declared to
        prevent — and the two are not interchangeable to this tool either: `Backlog.retired`
        and the projected status block both read the marker, so a retirement recorded without
        one is *counted as a shipment*.
        """
        return self.marker_field or (self.is_ledger and status == self.retired_marker)

    @property
    def dep_markers(self) -> tuple[str, ...]:
        """The statuses a dep annotation may cache (RK8) — the open set, ✅ and ⏸.

        Derived from the target's status, so what a file may *hold* and what an annotation
        may *say* are the same list or the re-derivation writes a line the gate then
        refuses (RK96). 🗑 is not among them for the one reason that is not symmetry: a
        retired target leaves no line to derive from, and the dep on it is unresolvable
        rather than annotated (RK28).
        """
        return tuple(
            dict.fromkeys((*self.markers, self.shipped_marker, self.deferred_marker))
        )

    # -- rendering ---------------------------------------------------------

    def render(self, task: Task) -> str:
        """The canonical line. The only writer of this format.

        `lint`'s comparison, `add`'s output and the round-trip test all read the
        line from here, so "canonical" is a fact about one function rather than a
        claim in a document.
        """
        # The marker is omitted, never emptied: `- **T1** …` is the shape both live
        # ledgers already write, and `-  **T1** …` would be a third one nobody has.
        # The indentation is the line's, not the format's (RK49): read off the file and
        # written back unchanged, so a nested follow-up is a task instead of prose.
        dash = f"{task.indent}-"
        # The qualifier of a partial entry goes *inside* the bold, after the id (RK121):
        # that is where the corpus writes it, and a second spelling would be a line the
        # tool renders differently from the one it read.
        named = f"{task.id} ({task.part})" if task.part else task.id
        head = (
            f"{dash} {task.status} **{named}**"
            if self.marks(task.status)
            else f"{dash} **{named}**"
        )
        if self.deps_field:
            deps = ", ".join(d.render() for d in task.deps) or NO_DEPS
            head += f" (deps: {deps})"
        # The symptom is omitted the same way and for the same reason (RK48): a ledger that
        # never had the slot must render back the line it read, not one with an empty bold.
        body = f" **{task.symptom}**" if self.symptom_field else ""
        line = f"{head}{body} {EM_DASH} {task.why}"
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
        """Ids are ``<prefix><n>``, non-contiguous, and spelled as this project spells them.

        Unpadded by default, because ``RK01`` and ``RK1`` would otherwise be two spellings
        of one id and the next-id maximum (RK4) is taken over these strings. A project that
        pads *every* line has already answered that, and says so as `[ids] pad` (RK106) —
        as it says `[ids] suffix` for the sub-letter a split task carries. Every declared
        family matches (RK74): a backlog that numbers by track is one backlog, so `C14` and
        `V05` are both ids of it and a dep from one to the other is an ordinary dep.
        """
        return re.compile(rf"^{self.id_fragment}$")

    def ids_named(self, text: str) -> tuple[str, ...]:
        """Every id of this project written **inside** a string, in order (RK389).

        :meth:`id_pattern` answers *is this an id*, which is the question every other reader
        has. This one answers *does this mention one*, and it exists for the dep arm that
        matches nothing: `RK5 + RK7` is not an id, not a block and not a range, so it is
        accepted as work outside the backlog — a statement about two ids that are in it.

        Bounded on both sides by an alphanumeric lookaround rather than `\\b`, because an id
        ends in a digit and `\\b` would find `RK5` inside `RK55`. The same reason
        :attr:`id_fragment` exists at all: a spelling only some readers know is how a number
        gets counted twice.
        """
        pattern = rf"(?<![A-Za-z0-9]){self.id_fragment}(?![A-Za-z0-9])"
        return tuple(match.group() for match in re.finditer(pattern, text))

    @staticmethod
    def _spell_ids(ids: Sequence[str]) -> str:
        """`RK5`, or `RK5 and RK7`, or `2 ids (RK5, RK7, …)` — a refusal names what it read."""
        if len(ids) == 1:
            return ids[0]
        if len(ids) == 2:
            return f"{ids[0]} and {ids[1]}"
        return f"{len(ids)} ids ({', '.join(ids)})"

    def split_id_pattern(self) -> re.Pattern[str]:
        """The ids :meth:`spell_id` cannot reach: the same shape with the letter **required**.

        :meth:`id_pattern` admits the sub-letter where `[ids] suffix` declares one, because a
        line may carry it. This one demands it, which makes the two patterns exactly the ids
        the counter derives and the ids it never will — and the second set is the whole reason
        a caller is ever allowed to *choose* an id instead (RK111).

        Matches nothing where no suffix is declared, which is the honest answer rather than a
        second code path: there, every legal id is one the counter produces. Spelled as an
        empty character class rather than an empty lookahead, because this string is handed to
        a client to validate against and the class is the form every regex engine reads.
        """
        if not self.id_suffix:
            return re.compile(r"[^\s\S]")
        return re.compile(rf"^{self._fragment(named=False, sub_required=True)}$")

    def prose_budget(self, task: Task) -> int:
        """How many characters this line's prose fields have between them (RK183).

        The line limit minus what the line costs before a word is written: the dash, the
        marker, the bold id, the `(deps: …)` group, the em dash and the `→ §<id>` pointer.
        Measured by rendering the line with both fields emptied rather than by adding up a
        second copy of the format — :meth:`render` is the only writer of it (L3), and a
        constant here would be a second one that drifts the first time a slot moves.

        Everything it needs is known before the prose exists: `add` derives the id, the
        marker, the deps and the pointer, so the budget is a fact about the line the author
        is *about* to write rather than a verdict on one they already wrote.
        """
        return self.line_max - len(self.render(replace(task, symptom="", why="")))

    def why_budget(self, task: Task) -> int:
        """The smaller of the `why`'s own limit and what this line has left for it (RK183).

        `symptom_max` plus `why_max` is at or over `line_max` on every default this ships
        and on both live corpora, so an author writing to the two published numbers is
        refused by the third — one that is measured on a string they never write and whose
        overhead moves with the dep count. The `why` is where the remainder is taken from
        because it is the field whose overflow has somewhere to go: the rationale section
        the line already points at. The symptom is the claim the line *is*, and compressing
        it is how a falsifiable line becomes a slogan.

        A symptom over its own limit is reported as itself and takes no room from the
        `why`: deriving a remainder from an illegal field would refuse one sentence for
        another field's overrun, and the author would fix twice what was wrong once.
        """
        taken = len(task.symptom) if self.symptom_field else 0
        if taken > self.symptom_max:
            return self.why_max
        return min(self.why_max, max(0, self.prose_budget(task) - taken))

    def validate(self, task: Task) -> tuple[Violation, ...]:
        """Every violation, in field order. Empty means the task conforms."""
        out: list[Violation] = []
        out.extend(self._check_identity(task))
        out.extend(self._check_deps(task))
        out.extend(self._check_symptom(task))
        out.extend(self._check_why(task))
        out.extend(self._check_ref(task))

        rendered = self.render(task)
        # The backstop, and only that (RK183): where a field's own budget already carries
        # the line's limit, the same overrun reported twice is one defect with two numbers
        # and the author cutting both. What is left for this to catch is an overrun no
        # field explains — a line whose *structure* does not fit, which no prose edit fixes.
        # Which is why this one asks for no word figure (RK243): the hint is aimed at a
        # sentence, and the clause after it says a sentence is not what is over.
        if len(rendered) > self.line_max and not any(
            violation.code in _LENGTH_CODES for violation in out
        ):
            out.append(
                Violation(
                    "line.too-long",
                    "line",
                    f"the rendered line is "
                    f"{over_by(len(rendered), self.line_max, prose=False)}; "
                    f"no field is over the budget this line left it, so what does "
                    f"not fit is the structure around them",
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
                    f"expected {self._id_shape()}, got {task.id!r}",
                )
            )
        out.extend(self._check_part(task))
        if not self.marks(task.status) and task.status != self.shipped_marker:
            # A markerless ledger states one status for the whole file, so every marker but
            # the departure it cannot state is unwritable there: an open line filed as
            # shipped work would read as shipped and no slot would say otherwise. 🗑 is the
            # exception `marks` carries (RK125) — it writes the marker on that line alone.
            out.append(
                Violation(
                    "status.unrepresentable",
                    "status",
                    f"this project declares a ledger with no marker "
                    f"([ledger] marker = false), so {task.status!r} cannot be told from "
                    f"{self.shipped_marker}: only {self.retired_marker} carries a marker "
                    f"there, a departure being the one status the file does not state",
                )
            )
        elif task.status == self.shipped_marker and not self.shipped_allowed:
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

    def _check_part(self, task: Task) -> list[Violation]:
        """A partial entry's qualifier: legal in the ledger, and nowhere else (RK121).

        Refused on a roadmap line because the roadmap already has a word for work in
        halves — ⏳, an open marker — and a line that said it twice would be two places to
        read the same claim. The ledger is where the statement is new: *this much of it is
        done*, which an entry could not previously make without leaving the grammar.
        """
        if task.part is None:
            return []
        if not self.is_ledger:
            return [
                Violation(
                    "part.unexpected",
                    "id",
                    f"({task.part}) qualifies a partial entry and this is not the ledger: "
                    f"an open line says the same thing with a marker",
                )
            ]
        if not task.part.strip() or task.part != task.part.strip():
            return [
                Violation(
                    "part.blank", "id", f"the qualifier is not a phrase: {task.part!r}"
                )
            ]
        if len(task.part) > self.part_max:
            return [
                Violation(
                    "part.too-long",
                    "id",
                    f"the qualifier is {over_by(len(task.part), self.part_max)}; "
                    f"it names which half, it is not the why",
                )
            ]
        return []

    def classify_dep(self, dep: Dep) -> DepKind:
        """What this dep names — a task, a block, a range, or work outside the backlog.

        Ordered so that neither a mistake nor a resolvable dep can hide as external:
        `Block P` first, then a range, then anything id-shaped (valid or not), and
        only what none of those match is external.
        """
        if self.block_dep_pattern().match(dep.id):
            return DepKind.BLOCK
        if self.range_of_dep(dep) is not None:
            return DepKind.RANGE
        if _ID_SHAPE_RE.match(dep.id):
            return DepKind.TASK
        return DepKind.EXTERNAL

    def block_of_dep(self, dep: Dep) -> str | None:
        """The block label a block dep names, or None if it names something else."""
        match = self.block_dep_pattern().match(dep.id)
        return match.group(1) if match else None

    def range_of_dep(self, dep: Dep) -> tuple[int, int] | None:
        """The inclusive `(first, last)` a range dep names, or None.

        Both `T451–T457` and `T451–457` occur in the wild, and the dash may be a
        hyphen or an en dash. A descending range is not a range: it is returned as
        None so the token falls through and gets reported instead of resolved.

        Both ends are the *same* family: `C14–V05` spans two tracks that number
        independently, so the pair it names is not a range of anything (RK74).
        """
        match = self._range_match(dep)
        if not match:
            return None
        first, last = int(match.group(2)), int(match.group(3))
        return (first, last) if first <= last else None

    def family_of_dep(self, dep: Dep) -> str | None:
        """Which family a range dep counts in (RK74), or None if it names no range.

        A range is bounded twice — by its numbers and by its track — and only the numbers
        used to be read, which was correct while `C14–C20` was the only kind of range a
        project could write. On a backlog that numbers six tracks it would also swallow
        `V15`, and a dep reported satisfied by work in another track is worse than one
        reported unresolvable.
        """
        match = self._range_match(dep)
        return match.group("family") if match else None

    def _range_match(self, dep: Dep) -> re.Match[str] | None:
        # Both ends are spelled the way this project spells a number (RK106), so a padded
        # backlog's `D01–D09` is the range it reads as rather than a `deps.range` finding.
        # The sub-letter is not admitted here and nowhere else is it withheld: a range is
        # bounded by numbers, and `T24b` is a name for a task and not for a bound.
        families = self.prefix_alternation
        number = self.number_fragment
        pattern = re.compile(
            rf"^(?P<family>{families})({number})"
            rf"\s*[-–—]\s*(?P=family)?({number})$"
        )
        return pattern.match(dep.id)

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
        allowed = self.dep_markers
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
                        f"{self._families()} id",
                    )
                )
            elif kind is DepKind.EXTERNAL and (named := self.ids_named(dep.id)):
                # The same argument as the range above, one arm over (RK389): free text is
                # the arm nothing matches, so `RK5 + RK7` lands whole and resolves as
                # "outside the backlog: shipping cannot satisfy it" — about two ids that are
                # in the backlog, one of which may already have shipped.
                one = len(named) == 1
                out.append(
                    Violation(
                        "deps.compound",
                        "deps",
                        f"{dep.id!r} names {self._spell_ids(named)} of this project inside "
                        f"work outside it: pass "
                        f"{'it as its own dep' if one else 'a dep each'}, or spell the "
                        f"external work without {'it' if one else 'them'}",
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
        if not self.symptom_field:
            # The slot does not exist in this file (RK48), so there is no field to judge
            # and an empty one is not a violation: `- **T1** — <prose>` is the whole line.
            return []
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
        budget = self.why_budget(task)
        because = ""
        if budget < self.why_max:
            # Said only where the two differ, and then it is the whole explanation: the
            # number the author was given is not the number that refused them, and which
            # line they are writing is why (RK183).
            taken = len(task.symptom) if self.symptom_field else 0
            because = (
                f" (the line's own limit of {self.line_max} leaves "
                f"{self.prose_budget(task)} for prose, and the symptom takes {taken})"
            )
        out = self._check_text("why", task.why, budget, because)
        why = task.why.strip()
        if why and self.terminator and not why.endswith(_TERMINATORS):
            out.append(
                Violation("why.no-terminator", "why", "why is a sentence: end it")
            )
        if self.one_sentence and _sentence_count(why) > 1:
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
        # The namespace a project may put in front of an address (RK340). Checked for shape
        # and never for membership: which prefixes exist is `[refs]`, and a line naming one
        # this project does not declare is a pointer at nothing — `ref.unresolved`, reported
        # by the gate against the files, rather than a format violation about a legal
        # spelling. The roadmap's own schema carries no prefix and could not answer anyway.
        prefix, bare = split_ref(task.ref)
        if prefix and not REF_PREFIX_RE.match(prefix):
            return [
                Violation(
                    "ref.format",
                    "ref",
                    f"not a <prefix>:<x.y> anchor: {task.ref!r} — a namespace is one word "
                    f"of letters and digits, starting with a letter",
                )
            ]
        if not OUTLINE_ANCHOR_RE.match(bare):
            return [Violation("ref.format", "ref", f"not an <x.y> anchor: {task.ref!r}")]
        return []

    def check(self, task: Task) -> Task:
        """Return the task, or raise :class:`SchemaError` with every violation."""
        violations = self.validate(task)
        if violations:
            raise SchemaError(violations)
        return task

    def _check_text(
        self, field: str, value: str, limit: int, because: str = ""
    ) -> list[Violation]:
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
                    f"{over_by(len(value), limit, because=because)}; the remainder "
                    f"belongs in the improvements section rather than compressed away",
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
