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
