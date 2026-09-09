"""The figures in prose a caller is handed, held against nothing taking them again (RK1639).

RK1541's read found its own subject stale: the withholding reason for `budget --decides`
quoted *2947 characters against 2850* and the tool measured 2758 the same session. A served
surface moves whenever a `help=` is edited; a number frozen in prose beside it does not. RK1588
swept that one closed set and found two more — `cost --deny` said *19 of room* where `cost
--tools` reports hundreds, `anchors --retired` said *943 of 983* against a repository now
holding over a thousand. Two of nine reasons, a third of those carrying a number at all.

None of the three broke anything, which is the whole finding: a decision defended by a stale
figure reads exactly like one that is right.

**What made it cheap was the distinction, not the regex.** `RK1506` is an address, `L5` is a
law, `UTF-8` is an encoding — each glued to a letter or a hyphen — and `943` is a measurement,
standing as its own word. One line of pattern separates them (`surface.measured`), and it
holds wherever the prose is reached through a table this suite already keeps total. Which is
exactly the three sets RK1588 left: `remedying`'s remedies, `serving`'s notes, `guarding`'s
refusals.

**Whose prose it is decides whether a figure is a defect or a date.** A withholding reason is
read by whoever edits the surface; a refusal by whoever met it. The three new sets all reach a
**caller**, which makes a stale figure worse there than in the one already swept — so the
census carries the reader per table, and that field is the rule rather than a label.

What this is **not** is a rule about digits in this package. `test_corpora` quotes pinned
counts on purpose, `budgeting` quotes what a surface measured the day a limit was chosen, and
RK1530's docstring names the two figures it is about. Outside prose a caller is handed, a
number is a record and not a claim — which is why the population is declared here and not
derived from a search for digits.
"""

from __future__ import annotations

from dataclasses import dataclass

from surface import measured

from roadkeep import guarding, remedying, serving


@dataclass(frozen=True, slots=True)
class Handed:
    """One closed set of prose, and who reads it (RK1639)."""

    #: `module.TABLE`, as the package spells it.
    where: str
    #: `a caller` or `an author`. The field the census exists for: it is what decides whether
    #: a figure in this prose is a defect or a date, and a table without it would be a list of
    #: four sweeps with one assertion silently standing for two different rules.
    read_by: str
    #: Why this set is closed — what holds it total, so the sweep is over a population and not
    #: over whatever a grep happened to reach.
    closed: str


#: The four sets, with the reader each reaches. Declared and never derived: the boundary of
#: this rule is *prose a caller is handed*, and a fifth set is a row somebody writes with an
#: answer to the reader question in it.
HANDED: tuple[Handed, ...] = (
    Handed(
        "serving.withheld",
        "an author",
        "every argument this server does not publish, total against the parsers in "
        "test_serving::test_every_argument_the_surface_withholds_says_why",
    ),
    Handed(
        "remedying._TABLE",
        "a caller",
        "one row per finding code, total against what the package can emit in "
        "test_remedying::test_every_code_the_package_can_emit_has_a_door",
    ),
    Handed(
        "serving.NOTES",
        "a caller",
        "every note this server appends beside an answer, total against the composing "
        "sites in test_serving::test_every_kind_is_a_site_that_appends_one",
    ),
    Handed(
        "guarding._INSTEAD",
        "a caller",
        "what to call instead per governed role, every named tool held against what the "
        "server serves in test_guarding::test_every_named_tool_is_one_the_server_serves",
    ),
)


def _withheld() -> dict[str, str]:
    """Every withholding reason, addressed as the surface a caller would name."""
    return {
        f"{verb} --{arg.replace('_', '-')}": why
        for verb, args in serving.withheld().items()
        for arg, why in args.items()
    }


def _remedies() -> dict[str, str]:
    """Every sentence a remedy row hands a caller, addressed by code and field.

    Each field and not a join: a stale figure has to be reported where it is written, and a
    row's prose is five separately-authored sentences plus one per door.
    """
    found: dict[str, str] = {}
    for code, rule in remedying._TABLE.items():  # noqa: SLF001 - the table is the population
        for field in ("decision", "varies", "cause", "cleared"):
            if said := getattr(rule, field, ""):
                found[f"{code}.{field}"] = said
        for index, (_, what) in enumerate(rule.doors):
            found[f"{code}.doors[{index}]"] = what
    return found


def _notes() -> dict[str, str]:
    """The rule behind every note this server appends, per kind."""
    return {f"{one.name}.why": one.why for one in serving.NOTES}


def _refusals() -> dict[str, str]:
    """Every command a denial offers and what it says the command is for, per role."""
    found: dict[str, str] = {}
    for role, rows in guarding._INSTEAD.items():  # noqa: SLF001 - the table is the population
        for command, what in rows:
            found[f"{role}: {command}"] = what
    return found


#: The reader per table, so a sweep names which set a finding is in — and the one function
#: this file has for reaching each. Keyed by `Handed.where`, asserted total below.
READERS = {
    "serving.withheld": _withheld,
    "remedying._TABLE": _remedies,
    "serving.NOTES": _notes,
    "guarding._INSTEAD": _refusals,
}


def test_no_prose_a_caller_is_handed_rests_on_a_figure_nothing_re_takes():
    """RK1639, which is RK1588 over the three sets it left. Every one of these is reached
    through a table this suite holds total, so the population is a population — and each of
    the three new ones reaches a caller rather than a maintainer, which is what makes a stale
    figure worse there than in the set already swept.

    The fix, every time, is the one RK1530, RK1540 and RK1541 made: name the read that takes
    the figure instead of the figure."""
    frozen = {
        f"{one.where} — {where}": found
        for one in HANDED
        for where, said in READERS[one.where]().items()
        if (found := measured(said))
    }
    assert frozen == {}, (
        "prose a caller is handed quotes a measured figure, which goes stale where nothing "
        f"re-takes it — name the read instead: {frozen}"
    )


def test_each_set_is_read_and_not_an_empty_one():
    """The half that makes the assertion above worth having: a reader that reached no prose at
    all would pass while covering nothing, which is `test_composing`'s finding one file over.
    Per table, because four readers is four ways to stop reading."""
    for one in HANDED:
        said = READERS[one.where]()
        assert len(said) >= 4, (one.where, said)
        assert all(value.strip() for value in said.values()), one.where


def test_the_pattern_tells_a_measurement_from_an_address():
    """The one line the whole sweep rests on, exhibited rather than trusted: every shape in
    these tables that carries a digit and is *not* a figure, beside the two that are.

    Held here because the sweep passing is otherwise indistinguishable from a pattern that
    matches nothing — which is how a green census stops covering its population."""
    for address in ("RK1506", "L5", "UTF-8", "utf-16-code-units", "base64", "CP1252"):
        assert measured(f"a reason naming {address} and nothing else") == (), address
    assert measured("943 of 983 retired") == ("943", "983")
    assert measured("2,947 characters against 2850") == ("2,947", "2850")


def test_every_row_names_a_reachable_table_and_says_who_reads_it():
    """`test_invariants`' own shape — a rule and what holds it — applied to this one. A fifth
    set of prose is a row somebody writes, and the reader field is what they have to answer:
    without it the sweep would be one assertion standing for two different rules."""
    assert {one.where for one in HANDED} == set(READERS)
    assert len(HANDED) >= 4, HANDED
    for one in HANDED:
        assert one.read_by in {"a caller", "an author"}, one
        # A holder and a reason in it, which is what keeps a row from being a name and a shrug.
        assert "::" in one.closed or "test_" in one.closed, one.where
        assert len(one.closed.split()) >= 8, one.where
    # And the claim the design turns on: three of the four reach a caller, so the rule is
    # about prose somebody meets rather than about prose somebody maintains.
    assert sum(one.read_by == "a caller" for one in HANDED) == 3, HANDED
