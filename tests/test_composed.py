"""The fields a caller composes, held total against the parsers that take them (RK1627).

RK1570 found the block title because a design named it. What it could not have found is the
next one: nothing enumerated the fields a caller composes, so *which of them has a validator*
was answered by remembering — and the same gap in any other composed field would have been as
invisible as that one was.

`composed.FIELDS` is the register and this is its closure, in the shape the two beside it
already have: the population comes off the source, every member resolves to a row, and a row
claiming a validator is joined to the two registers that already hold codes — the gate's
`remedying.codes()` and the write's `test_backstop.BACKSTOP` — rather than being believed
here. Both, because neither is total over what a write refuses, which is a thing this file
found out by trying each and is asserted below rather than remembered.
"""

from __future__ import annotations

import pytest

from composed import ELSEWHERE, FIELDS, KINDS, classify, fields, rows


def test_every_field_a_write_takes_is_accounted_for():
    """The deliverable. An argument added tomorrow is in the population by being declared, so
    the register cannot silently stop covering it — which is the property RK1570's gap had
    none of, `block add --title` having been written and nobody ever asked what checked it."""
    unaccounted = sorted(
        f"{command} --{dest}" for command, dest in fields() if classify(command, dest) is None
    )
    assert not unaccounted, {
        "takes a value and no row says what it is": unaccounted,
        "add a row to composed.FIELDS keyed by the dest, or to ELSEWHERE where a second "
        "verb means something else by it": True,
    }


def test_no_row_describes_an_argument_nothing_declares():
    """The other direction, and the one a register loses without: a row for a dest no parser
    takes is a claim about a field that is gone, and it reads exactly like a rule being kept."""
    taken = {dest for _, dest in fields()}
    assert set(FIELDS) <= taken, sorted(set(FIELDS) - taken)
    pairs = set(fields())
    assert set(ELSEWHERE) <= pairs, sorted(set(ELSEWHERE) - pairs)


def test_every_row_states_one_of_the_four_kinds_and_argues_it():
    # A kind outside the four is a fifth answer nobody decided, and a clause too short to be
    # a reason is the row somebody added to make this file green.
    for name, row in rows().items():
        assert row.kind in KINDS, (name, row.kind)
        assert len(row.why.split()) >= 8, (name, row.why)


def test_a_field_that_claims_a_validator_names_a_code_a_register_holds():
    """The join, and what makes *has a validator* an answer rather than a claim.

    **Both registers, because neither covers a write's codes alone** — which this file found by
    trying each. `remedying.codes()` is what the *gate* declares and has no row for a code only
    an argument can be wrong in: `title.newline` is refused at the door and is not a state a
    file can be in, so `block add --title` names two codes that table has never heard of.
    `test_backstop.BACKSTOP` is what a *write* refuses and reads the first argument of every
    `Violation(…)` in the source, so it sees only a literal — and `scoping` and `criteria` name
    their codes as constants, deliberately, a code spelled twice being a code that drifts.

    So a `schema` row names a code one of the two holds, and a row inventing a family is red
    here. The pair each miss is the reason this register is worth having: neither could have
    answered *which composed field has a validator*, because neither is about the fields."""
    from test_backstop import BACKSTOP

    from roadkeep.remedying import codes

    known = set(codes()) | {one.code for one in BACKSTOP}
    for name, row in rows().items():
        if row.kind != "schema":
            continue
        assert row.codes, f"{name}: a schema row names the codes it is refused under"
        missing = sorted(set(row.codes) - known)
        assert not missing, {name: missing}


def test_the_two_registers_this_joins_to_each_miss_something():
    """Stated rather than left implicit, because the union above reads as belt and braces until
    somebody checks. Each set is genuinely short of the other, and the day one becomes total
    this test says so — which is the moment the join could be narrowed."""
    from test_backstop import BACKSTOP

    from roadkeep.remedying import codes

    gate, written = set(codes()), {one.code for one in BACKSTOP}
    assert written - gate, "the backstop now names nothing the gate does not"
    assert gate - written, "the gate now names nothing the backstop does not"


def test_only_a_schema_row_names_codes():
    # The split is the register's whole content: a `round-trip` row naming a code would be
    # claiming the field validator this file exists to say it has not got.
    for name, row in rows().items():
        if row.kind == "schema":
            continue
        assert not row.codes, (name, row.kind, row.codes)


def test_the_paths_are_the_ones_the_config_already_classifies():
    """`config.PATH_ARGUMENTS` says, per argument, which directory a path is read from — so a
    row here calling something a path and that table not knowing it is two answers about one
    field, which is the drift this whole file is one instance of."""
    from roadkeep.config import PATH_ARGUMENTS

    declared = {dest for row in PATH_ARGUMENTS.values() for dest in row}
    ours = {dest for dest, row in FIELDS.items() if row.kind == "path"}
    # Not equality: that table covers reads too, and this population is the writes.
    unknown = sorted(ours - declared)
    assert not unknown, {
        "called a path here and unclassified in config.PATH_ARGUMENTS": unknown
    }


def test_no_field_is_left_to_the_round_trip_alone():
    """RK1627's own first finding, and RK1666 closing it — which is what this test was written
    to make visible. `govern --because` wraps a sentence into comment lines above a key and the
    whole file is re-parsed before the bytes land (RK1533/RK1576); that refuses a value TOML
    cannot carry and saw nothing about the prose, so a mangled run landed in a file `lint`
    reads for budgets and not for characters.

    **Empty now**, which is a state and not an achievement: the two rows take the pair of
    character rules `characters()` names, and the next field composed with nothing but the
    round-trip behind it is a row here somebody has to write down. Asserted so that closing
    one moves this test rather than passing quietly."""
    weak = sorted(dest for dest, row in FIELDS.items() if row.kind == "round-trip")
    assert weak == [], weak


@pytest.mark.parametrize(
    "kind, floor",
    # The shape of the population, as a floor per kind: what may not happen is a register that
    # has quietly become one kind — every field an address would mean nothing is composed at
    # all, which is the reading RK1570's gap was invisible inside.
    [("schema", 10), ("address", 20), ("path", 6)],
)
def test_the_register_covers_every_kind_it_declares(kind, floor):
    found = [dest for dest, row in FIELDS.items() if row.kind == kind]
    assert len(found) >= floor, {kind: sorted(found)}


def test_the_population_is_the_size_this_was_measured_over():
    """A census nobody can size is one that can go empty without saying so — `composing`'s own
    rule. Stated as a floor, because arguments are added and the number moves with them."""
    taken = fields()
    assert len(taken) >= 130, len(taken)
    # And over more than one verb, which a walk that stopped descending would not be.
    assert len({command for command, _ in taken}) >= 20
