"""Which refusals a door makes that the gate can also report about a file (RK1004).

RK498 read the register one way — every code the gate emits, and whether a write refuses it
— and it paid: an estimate of two open codes turned out to be five. Nothing read it back.
The first hole in the other direction was **opened by a fix**: RK1002 put a rule at the door
where the prose is composed and left no backstop, and RK1003 closed it within the hour.

L1 says the write is where a rule is enforced and `lint` is only the backstop — *only*, not
*never*. The backstop covers text this tool did not write, which is exactly an adopted
backlog, a hand edit and a textual merge. So a rule held at the door alone is a rule that
does not survive any of those three, and this is the enumeration that says which ones are.

**The rows are three answers, not two.**

`gate` naming the **same code** is the common one and needs no probe: RK421 holds the remedy
table total over what the gate emits, so a code in that table is a code the gate can report,
and the two surfaces sharing a string is what :class:`~roadkeep.linting.Finding` promises.

`gate` naming a **different code** is a mapping, measured: the gate reports a section past
its budget as `section.too-long` and a design nothing points at as `section.orphan`, which
are the same defects the door calls `body.too-long` and `anchor.unknown`.

`gate` **empty** is one of two things and :attr:`Backstopped.because` says which. Some are
not a state a governed file can be in at all — a heading is one line, so `title.newline` is
about an argument and never about text; an address the scheme cannot read is not parsed as a
section, so the heading is prose and prose is allowed. The rest are the finding: measured,
**two** of the forty-three are states a file can hold with a pointer resolving to them and
nothing saying so — and RK1012 closed both, so the set is empty and the next row to join it
is one somebody has to notice.
"""

from __future__ import annotations

import ast
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from surface import modules

from roadkeep.config import Config
from roadkeep.linting import lint
from roadkeep.remedying import codes

#: The prose fields :meth:`Schema._check_text` judges, which is what a `{field}.…` code
#: expands over. Two and not three: `part` carries its own explicit codes, because a
#: qualifier is a ledger field and its rules are not the line's.
FIELDS = ("symptom", "why")

#: What :func:`~roadkeep.kernel.schema._codepoints` resolves its code from (RK499). Read here as the
#: three it can be, because the constructor's first argument is a name and not a literal —
#: the one place this enumeration cannot read the code off the call.
COMPUTED = ("char.tab", "char.space", "char.invisible")

#: The names a `Violation`'s code may arrive under that no pass here can resolve, with
#: :data:`COMPUTED` as what each can be (RK1665). One: `_codepoints` picks the code from the
#: kind of character it found, so the value is a local and the enumeration above is the
#: answer. Declared rather than fallen through to — that fall-through is what let six codes
#: named as module constants read as *the three character codes* and leave the register
#: agreeing with itself about a set that was short.
COMPUTED_FROM = ("code",)

#: Not a state a governed file can be in: the refusal is about an argument, and the file has
#: no way to carry the mistake. Stated once, because five rows give the same reason.
ARGUMENT = "not a state a file can be in: the refusal is about an argument, not about text"
#: An address this project's scheme cannot read is not parsed as a section at all, so the
#: heading is prose — and prose in a prose file is allowed. Nothing is wrong with the file.
PROSE = "an address the scheme cannot read is not a section, so the heading is prose"
#: A heading whose title repeats its own anchor is uninformative and **legal** (RK1329): it
#: round-trips, it names a section every reader resolves, and an adopted file may carry one.
#: So the rule is the door's alone — a gate finding here would report on prose somebody wrote
#: before this tool owned the file, which is the adoption gate RK66 keeps out.
UNINFORMATIVE = "a title repeating its anchor is legal prose: refusing it would gate adoption"


@dataclass(frozen=True)
class Backstopped:
    """One code a write refuses, and what the gate says about a file already in that state."""

    code: str
    #: The gate code that reports the same defect. Equal to :attr:`code` for the common case,
    #: a different string where the gate's vocabulary names it otherwise, and `""` where
    #: nothing reports it.
    gate: str = ""
    #: Why nothing does. Required when :attr:`gate` is empty and absent otherwise.
    because: str = ""
    #: The prose that puts a file in the state, where the row was measured rather than
    #: stated. Present on every row whose `gate` is not simply its own code.
    section: str = ""


def _same(*names: str) -> tuple[Backstopped, ...]:
    return tuple(Backstopped(name, gate=name) for name in names)


PROSE_HEAD = "# Improvements\n\n## Block A — The model\n\n"

BACKSTOP: tuple[Backstopped, ...] = (
    *_same(
        "block.format",
        "block.missing",
        "body.promise",
        "char.tab",
        "char.space",
        "char.invisible",
        # RK1497. The door refuses it and the gate names the same line: the rule reads a
        # *field*, so both surfaces ask one function and a file already carrying the bytes is
        # reported rather than being a state only a write could have prevented.
        "char.mangled",
        "deps.compound",
        "deps.duplicate",
        "deps.format",
        "deps.marker",
        "deps.range",
        "deps.self",
        "deps.unexpected",
        "id.format",
        "line.too-long",
        "part.blank",
        "part.too-long",
        "part.unexpected",
        # RK1618. One rule and one name on both surfaces: `dismiss` refuses an entry with no
        # premise through `Schema.validate`, and a file already carrying one is reported by
        # that same rule — which is what keeps the required field required for an entry that
        # arrived by a merge or a hand edit.
        "premise.missing",
        # The four the scan could not see (RK1665): `scoping` and `criteria` name their codes
        # as module constants, so `Violation(LEAD, …)` was a `Name` where the reader wanted a
        # literal. Nothing was wrong — the gate reads the same `validate` for a bullet already
        # in the file, which is why these are the ordinary shared-code rows — and what was
        # wrong is that a seventh added to either module would have had no row and no red.
        "non-goal.lead",
        "non-goal.why",
        "criterion.lead",
        "criterion.why",
        # RK1227. The one code here that is refused about a *body* and reported about a
        # citation inside one — the same defect and the same name, because `section amend`
        # now asks the question `lint` was left to answer three commits later.
        "ref.dangling",
        "ref.format",
        "ref.mismatch",
        "ref.missing",
        "ref.sigil",
        # RK1297. Four rows and one shape: a `(requires: …)` group is validated at the write
        # and read back by the gate off the same `Schema.validate`, so a line that reached a
        # file by any other route is reported under the name the write refused it by.
        "requires.duplicate",
        "requires.format",
        "requires.unknown",
        "requires.unrenderable",
        "status.shipped",
        "status.unknown",
        "status.unrepresentable",
        "symptom.markup",
        "symptom.sentence",
        "symptom.control",
        "symptom.empty",
        "symptom.newline",
        "symptom.too-long",
        "symptom.whitespace",
        "why.control",
        "why.empty",
        "why.newline",
        "why.no-terminator",
        "why.sentences",
        "why.too-long",
        "why.whitespace",
    ),
    # -- the same defect under the gate's own name, measured ------------------
    Backstopped(
        "body.too-long",
        gate="section.too-long",
        section="### §RK1 A first design\n\n" + "word " * 400 + "\n",
    ),
    Backstopped(
        "anchor.unknown",
        gate="section.orphan",
        section="### §RK9 A design for nothing\n\nA paragraph about it.\n",
    ),
    # -- nothing reports it, and the two kinds of nothing ---------------------
    # RK1229. Mapped, and the mapping is the whole argument for holding it at the door: a
    # line carrying an unrenderable dep does not parse at all, so the gate reports
    # `line.unparsed` — which names no field. The *reason* is unrecoverable the moment the
    # line is written, and no verb starting from a task reaches it to repair.
    #
    # Unprobed, and said rather than left blank: every measured row here puts a file in the
    # state by writing a **section**, and this state is a roadmap *line*. A probe would want a
    # second fixture shape for one row, so what stands instead is `test_prevention`'s, which
    # runs the write and asserts it refuses.
    Backstopped("deps.unrenderable", gate="line.unparsed"),
    Backstopped("title.newline", because=ARGUMENT),
    # RK1112: the argument covered the wrong extent, and once written a pasted child heading
    # *is* a heading — so the state this refuses has no spelling in the file to report.
    Backstopped("body.subtree", because=ARGUMENT),
    Backstopped("title.markup", because=ARGUMENT),
    Backstopped("title.is-anchor", because=UNINFORMATIVE),
    Backstopped("anchor.namespace", because=PROSE),
    Backstopped(
        "anchor.format",
        because=PROSE,
        section="### §RK1 A first design\n\nA paragraph.\n\n### §not-an-id Another\n\nMore.\n",
    ),
    Backstopped("anchor.sigil", because=PROSE),
    # Closed by RK1012, which is what a row leaving :data:`UNBACKSTOPPED` looks like: the same
    # probe, the other outcome, and a gate that stopped reporting turns it red.
    Backstopped("body.empty", gate="body.empty", section="### §RK1 A first design\n"),
    Backstopped("title.empty", gate="title.empty", section="### §RK1\n\nA paragraph.\n"),
)

#: The codes a file can carry that nothing reports — the register's finding, asserted in both
#: directions so closing one is a decision somebody writes down (RK491's rule for `UNHELD`).
#: **Empty since RK1012**, which is a state and not an achievement: the five rows beside them
#: report nothing because no file can be in the state, and the next row to join this set is
#: one somebody has to notice writing a refusal without a backstop.
UNBACKSTOPPED = frozenset()

ROADMAP = (
    "# Roadmap\n\n## Block A — The model\n\n"
    "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1\n"
)
LEDGER = "# Shipped\n\n## Block A — The model\n"


def _named(tree: ast.Module) -> dict[str, str]:
    """Module-level names bound to a string constant, by name (RK1665).

    The pass the reader below did not have. `scoping` and `criteria` declare their codes as
    constants — `LEAD = "non-goal.lead"` and five beside them — on the stated argument that a
    code spelled twice is a code that drifts once, which is right; so `Violation(LEAD, …)` had
    a `Name` where the scan wanted a literal, and six codes a write genuinely refuses sat
    outside a register whose whole claim is `covered == written`.

    Module level only, and that is the honest bound: a name bound inside a function is a
    value this pass cannot resolve without following the call, and what it does about one is
    fail loudly rather than widen the set (see :func:`_written`).
    """
    return {
        target.id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign) and len(node.targets) == 1
        for target in [node.targets[0]]
        if isinstance(target, ast.Name)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    }


def _written() -> set[str]:
    """Every code a `Violation` in this package is constructed with, expanded.

    Read from the source and not from a registry, for :func:`tests.surface.modules`' own
    reason: importing the package to find them finds only what happens to have run. A
    `{field}` is expanded over :data:`FIELDS` and the one computed code over
    :data:`COMPUTED`, both of which are declared above rather than guessed at here.

    **A `Name` is resolved and never widened** (RK1665). This fell through to `COMPUTED` on
    anything that was not a literal, which is the branch that hid the six: a code named as a
    module constant read as *the three character codes*, so the closure agreed with itself
    about a set that was missing rows. Now a name resolves through :func:`_named`, and one
    that does not resolve raises — a scan that cannot read a code has to say so, this
    register's whole value being that it is total.
    """
    found: set[str] = set()
    for module in modules():
        tree = ast.parse(module.text)
        bound = _named(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name != "Violation":
                continue
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                found.add(first.value)
            elif isinstance(first, ast.JoinedStr):
                spelled = "".join(
                    part.value if isinstance(part, ast.Constant) else "{field}"
                    for part in first.values
                )
                found |= {spelled.replace("{field}", field) for field in FIELDS}
            elif isinstance(first, ast.Name) and first.id in bound:
                found.add(bound[first.id])
            elif isinstance(first, ast.Name) and first.id in COMPUTED_FROM:
                # The one code this scan cannot read off the call: `_codepoints` resolves it
                # from the kind of character it found, so the three it can be are declared.
                found |= set(COMPUTED)
            else:
                raise AssertionError(
                    f"{module.where}:{node.lineno} constructs a Violation from "
                    f"{ast.unparse(first)}, which this scan cannot resolve to a code — "
                    f"bind it to a module-level string, or name it in COMPUTED_FROM with "
                    f"the codes it can be"
                )
    return found


def _project(root: Path, section: str) -> Config:
    (root / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n'
        'changelog = "CHANGELOG.md"\nimprovements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    for name, body in (
        ("ROADMAP.md", ROADMAP),
        ("CHANGELOG.md", LEDGER),
        ("IMPROVEMENTS.md", PROSE_HEAD + section),
    ):
        (root / name).write_text(body, encoding="utf-8", newline="")
    return Config.discover(root)


# -- the closure --------------------------------------------------------------


def test_every_code_a_write_refuses_has_a_row():
    """The deliverable. A `Violation` raised tomorrow with no row is red here until somebody
    says whether a file already in that state is reported by anything."""
    written = _written()
    assert written, "the source scan found no violations: the closure is reading nothing"
    covered = {one.code for one in BACKSTOP}
    assert covered == written, {"raised, no row": written - covered, "row, not raised": covered - written}


def test_every_row_is_addressed_once_and_answers_one_way():
    addressed = [one.code for one in BACKSTOP]
    assert len(addressed) == len(set(addressed)), addressed
    for one in BACKSTOP:
        assert bool(one.gate) != bool(one.because), f"{one.code}: name a gate code or say why not"


def test_every_named_gate_code_is_one_the_gate_can_emit():
    """A mapping that named a code nothing emits would be a backstop that is not there —
    `remedying.codes()` is held total over the gate by RK421, so it is the list to check."""
    emitted = set(codes())
    for one in BACKSTOP:
        if one.gate:
            assert one.gate in emitted, f"{one.code} maps to {one.gate}, which nothing emits"


def test_the_unbackstopped_rows_are_the_ones_named():
    # Keyed on the *reason* and not on the absence of a gate code: some rows have no
    # backstop because no file can be in the state, and one (RK1329) because a file in it is
    # not wrong — which is an answer and not a hole either way.
    harmless = (ARGUMENT, PROSE, UNINFORMATIVE)
    assert {
        one.code for one in BACKSTOP if not one.gate and one.because not in harmless
    } == UNBACKSTOPPED


# -- the measurements ---------------------------------------------------------


@pytest.mark.parametrize(
    "row", [one for one in BACKSTOP if one.section], ids=lambda one: one.code
)
def test_the_probe_measures_what_its_row_claims(row):
    """A row that maps to another code, or claims none, is a judgement — so the ones that can
    be measured are. `gate == code` rows carry no probe and need none: RK421 already proves
    the gate emits that string."""
    root = Path(tempfile.mkdtemp())
    try:
        reported = {one.code for one in lint(_project(root, row.section)).findings}
    finally:
        shutil.rmtree(root, ignore_errors=True)
    if row.gate:
        assert row.gate in reported, f"{row.code}: the gate no longer reports {row.gate}"
    else:
        assert not reported, f"{row.code}: the gate reports {sorted(reported)} after all"
