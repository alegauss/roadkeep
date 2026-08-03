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

    def __post_init__(self) -> None:
        if self.ref_scheme not in REF_SCHEMES:
            raise ValueError(
                f"ref_scheme must be one of {', '.join(sorted(REF_SCHEMES))}, "
                f"got {self.ref_scheme!r}"
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
            f"{dash} {task.status} **{named}**" if self.marker_field else f"{dash} **{named}**"
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
                    f"expected {self._id_shape()}, got {task.id!r}",
                )
            )
        out.extend(self._check_part(task))
        if not self.marker_field and task.status != self.shipped_marker:
            # The one thing a markerless ledger cannot record is a departure that is not
            # a shipment (RK32): with no slot to carry 🗑, a retired line would read as
            # shipped. Refused here, so `retire` refuses the whole transaction (RK6).
            out.append(
                Violation(
                    "status.unrepresentable",
                    "status",
                    f"this project declares a ledger with no marker "
                    f"([ledger] marker = false), so {task.status!r} cannot be told from "
                    f"{self.shipped_marker}: declare the marker before recording one",
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
                    f"the qualifier is {len(task.part)} characters, limit is "
                    f"{self.part_max}: it names which half, it is not the why",
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
        out = self._check_text("why", task.why, self.why_max)
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
        if not OUTLINE_ANCHOR_RE.match(task.ref):
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
