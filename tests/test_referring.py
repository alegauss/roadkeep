"""The reference index is total, or it is a second source of truth (RK1066).

`referring.py` claims to name every reference relation this backlog has, which machine each
resolves through, and which gate codes each is the source of. A claim like that is worth
exactly what holds it: an index missing a code is one a reader trusts and then finds a rule
outside, which is the arrangement this whole tool exists to remove — and this one would carry
the tool's own authority while doing it.

So the closure is the deliverable, the way `test_prevention` holds the remedy table and
`test_caches` holds the cache inventory. Every code in the four reference families is either
answered by a relation or named in `ELSEWHERE` with a reason, exactly once.
"""

from __future__ import annotations

from roadkeep.referring import ELSEWHERE, RELATIONS
from roadkeep.remedying import codes

#: The families a reference question can be asked in. Named rather than derived from the
#: index, so a relation added over a fifth family is a failure here and not a silent gap.
FAMILIES = ("deps", "ref", "section", "priority")


def familied() -> set[str]:
    return {code for code in codes() if code.split(".")[0] in FAMILIES}


def test_every_code_in_a_reference_family_is_accounted_for_exactly_once():
    answered = [code for relation in RELATIONS for code in relation.answers]
    assert len(answered) == len(set(answered)), "two relations claim one code"
    covered = set(answered) | set(ELSEWHERE)
    assert set(answered).isdisjoint(ELSEWHERE), "a code is both resolved and set aside"
    assert covered == familied(), {
        "emitted, not indexed": familied() - covered,
        "indexed, not emitted": covered - familied(),
    }


def test_the_count_the_task_argued_from_is_re_readable_and_was_one_short():
    # §RK1066 argued from sixteen, and a number nobody can re-read is the sentence this
    # project keeps replacing with a command. It is seventeen: the pointer relation answers
    # `section.ambiguous` too, which the closure above found on its first run — the argument
    # for a total index, made by the index. The rest are shapes, traversals and procedures.
    assert sum(len(relation.answers) for relation in RELATIONS) == 17
    assert len(familied()) == 17 + len(ELSEWHERE)


def test_the_queue_and_the_deps_share_one_resolver():
    # The half RK1066 assumed was missing and measuring found already done (RK326): there is
    # no third place — `_queued` reads one `Resolution` and spells it in its own codes. Held
    # here because the reduction the task asks for is one family, not three, and a later
    # reader deserves to find that as a check rather than as a paragraph.
    by_name = {relation.name: relation for relation in RELATIONS}
    assert by_name["queued"].resolver == by_name["dep"].resolver
    assert by_name["pointer"].resolver != by_name["dep"].resolver


def test_every_relation_says_what_an_absent_reference_looks_like():
    # The distinction a resolver cannot work without: a line with no deps is complete, and
    # one whose dep is missing is not. A relation that could not tell them apart would
    # report every unreferencing line in the file.
    for relation in RELATIONS:
        assert relation.targets in ("id", "heading", "id-or-block"), relation.name
        assert isinstance(relation.empty, str), relation.name
        assert relation.resolver.startswith("roadkeep."), relation.name


def test_every_rule_left_out_says_why():
    # A reason and not a bare list: "not a reference" is the claim, and an entry that does
    # not argue it is one somebody added to make this file green.
    for code, because in ELSEWHERE.items():
        assert len(because.split()) >= 4, code


# -- the pairs of files that can hold one id (RK1082) -------------------------


def test_the_pairs_are_the_cross_product_of_the_files_that_carry_a_line():
    """Three governed files can hold a line, so there are three pairs, and the gate read two
    of them by two hand-written loops — RK1081 wrote the second by copying the first.

    Derived from `CARRIERS` rather than listed, which is the whole point: a fourth role that
    can hold a line is covered by arithmetic instead of by somebody remembering.
    """
    from itertools import combinations

    from roadkeep.ids import CARRIERS
    from roadkeep.referring import PAIRS

    assert {frozenset((one.first, one.second)) for one in PAIRS} == {
        frozenset(pair) for pair in combinations(CARRIERS, 2)
    }


def test_every_pair_either_has_a_code_or_says_why_it_has_none():
    # The closure, and the difference from the arrangement RK1077 was filed about: a pair
    # nobody has walked into says so here rather than being absent, so the gap is a line to
    # read instead of a discovery somebody's adoption makes.
    from roadkeep.referring import PAIRS
    from roadkeep.remedying import codes

    for pair in PAIRS:
        assert bool(pair.code) != bool(pair.because), (pair.first, pair.second)
        if pair.code:
            # A code with no remedy is a finding that names no door, which is the property
            # `test_remedying` holds over the whole table and this holds over this relation.
            assert pair.code in set(codes()), pair.code
            assert pair.says, pair.code
        else:
            assert len(pair.because.split()) >= 12, (pair.first, pair.second)




def test_the_gate_still_reports_both_pairs_it_read_before(tmp_path):
    # The loop replaced two hand-written ones, so both answers are asked for again: a
    # refactor that quietly dropped one would be the silence RK1076 spent a task removing.
    from roadkeep.config import Config
    from roadkeep.linting import lint

    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "R.md"\nchangelog = "C.md"\n'
        'deferred = "D.md"\n[rules.roadmap]\nref = false\n[rules.deferred]\nref = false\n',
        encoding="utf-8",
    )
    line = "- {m} **RK{n}** (deps: —) **A symptom** — Because of a reason.\n"
    (tmp_path / "R.md").write_text(
        "# R\n\n## Block A — x\n\n" + line.format(m="📋", n=1) + line.format(m="📋", n=2),
        encoding="utf-8",
    )
    (tmp_path / "C.md").write_text(
        "# C\n\n## Block A — x\n\n- ✅ **RK1** **A symptom** — It landed.\n",
        encoding="utf-8",
    )
    (tmp_path / "D.md").write_text(
        "# Deferred\n\n## Block A — x\n\n" + line.format(m="⏸", n=2), encoding="utf-8"
    )
    found = {f.code: f.id for f in lint(Config.discover(tmp_path)).findings}
    assert found.get("id.two-files") == "RK1"
    assert found.get("id.paused-and-open") == "RK2"


def test_the_third_pair_is_read_and_filed_against_its_own_first_file(tmp_path):
    """RK1084, after measuring: **neither adopting corpus declares a store at all**, so the
    pair nobody had walked into is one nobody can walk into yet. The rule is written anyway —
    a contradiction the format can express should not be silent, and the third row costs one
    entry — and the door is two reads, because which file is the leftover is a fact about
    what happened rather than one this tool may decide (L4).
    """
    from roadkeep.config import Config
    from roadkeep.linting import lint

    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "R.md"\nchangelog = "C.md"\n'
        'deferred = "D.md"\n[rules.roadmap]\nref = false\n[rules.deferred]\nref = false\n',
        encoding="utf-8",
    )
    (tmp_path / "R.md").write_text("# R\n\n## Block A — x\n", encoding="utf-8")
    (tmp_path / "C.md").write_text(
        "# C\n\n## Block A — x\n\n- ✅ **RK1** **A symptom** — It landed.\n", encoding="utf-8"
    )
    (tmp_path / "D.md").write_text(
        "# Deferred\n\n## Block A — x\n\n"
        "- ⏸ **RK1** (deps: —) **A symptom** — Because of a reason.\n",
        encoding="utf-8",
    )
    (found,) = lint(Config.discover(tmp_path)).findings
    assert found.code == "id.paused-and-gone" and found.id == "RK1"
    # Filed against the changelog, which is where its line is: the first two pairs are the
    # roadmap's and this one is not, which is why the loop reads the pair's own first file.
    assert found.file == "C.md"


def test_no_pair_is_left_without_a_rule():
    # The closure RK1082 wrote and RK1084 emptied: every pair of files that can hold one id
    # is read now, so `because` has no occupant and the field stays for the next carrier.
    from roadkeep.referring import PAIRS

    assert [pair.code for pair in PAIRS] == [pair.code for pair in PAIRS if pair.code]
