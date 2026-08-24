"""The remedy table, and the one property that makes it worth having (RK420, RK421).

A remedy per finding is a convenience; a remedy per *code the package can emit* is a
guarantee, and only the second one saves a turn reliably. The difference is what this file
holds:

* **Totality** (RK421). Every code string reachable from `linting` or `schema` has a row.
  The domain is scraped from the source rather than listed here, so a check added to the
  gate without stating its repair is a red in this file rather than a discovery six months
  later on somebody else's backlog. A second list of codes would be exactly the drift this
  package exists to stop, one layer down.
* **Runnable means runnable.** A `run` or `fix` remedy carries no placeholder, and the
  first word of its argv is a subcommand this CLI actually parses. An argv that looks
  complete and is not is worse than no remedy at all, because a caller spends the turn
  before finding out.
* **L4 is honoured and stated.** Every remedy that would have to write prose is `compose`
  or `decide` and carries the blank, rather than inventing a title, a reason or a shorter
  sentence.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from roadkeep import remedying
from surface import address, modules
from roadkeep.backlog import Backlog
from roadkeep.cli import build_parser
from roadkeep.config import ROLES, Config
from roadkeep.linting import Finding, Note, lint
from roadkeep.provenance import invocation
from roadkeep.remedying import BLANK, KINDS, VARIES, Remedy, codes, explain, remedy

SOURCE = Path(remedying.__file__).resolve().parent

#: Strings that match the code shape and are not codes. Named individually, because a
#: pattern loose enough to exclude them by shape would exclude real codes too.
_NOT_CODES = frozenset({"roadkeep.toml"})


def emitted() -> set[str]:
    """Every code the package can report, read out of the modules that report them.

    The scrape is the point: a hand-written list here would go stale in exactly the
    direction that matters, since the code nobody remembered to add is the code whose
    remedy nobody wrote either.

    **Two ways of writing a code, so two reads** (RK428). A literal is found by pattern; a
    code the schema *composes* is not, and half of them are — `_check_text` validates both
    prose fields through one function and names its violations `f"{field}.newline"`, so
    twelve codes existed at runtime with no remedy and a green suite, because the test could
    not ask about a string nothing writes down. :func:`composed` is the second read, and it
    is an AST read rather than a wider regex for the reason the narrow one works at all: a
    pattern loose enough to catch `f"{field}.x"` catches every `f"{name}.{ext}"` in the
    package too, and an assertion over that domain is noise.
    """
    # `referring.py` joined the two when RK1082 moved the pairwise codes into the
    # declaration that drives them — and the list being hand-written is why this had to be
    # edited at all, which is RK1074's argument arriving in one more file.
    found: set[str] = set()
    # `criteria.py` joined them for `referring.py`'s reason (RK1265) and `scoping.py` for the
    # same one (RK1266): both name their codes as **module constants**, so `linting` emits
    # them through a variable and a scrape over that file alone saw not one of the six. The
    # module that *declares* a code is the honest place to read it from — which is what the
    # two additions above already say, and what nobody had said about the older of the two
    # bullet grammars: three codes reported by the gate, no row for any of them, and a green
    # suite for as long as they had existed.
    #
    # This is a list and never a glob. The files here are where codes are **composed** or
    # **declared**, and widening it to the package would drag in every dotted literal there
    # is — the noise `composed`'s own docstring refuses one read over.
    for name in (
        address("linting"),
        address("schema"),
        address("referring"),
        address("criteria"),
        address("scoping"),
    ):
        text = (SOURCE / name).read_text(encoding="utf-8")
        # **The hyphen on both halves** (RK1266). The tail already allowed one and the head
        # did not, so a whole grammar's codes fell out of the domain: `non-goal.duplicate` is
        # a literal in `linting.py` — a file this has read since the beginning — and was never
        # once matched. Measured before it was widened: over the five files here the change
        # admits exactly the four `non-goal.*` codes and nothing else, so the looser pattern
        # is not the noise `composed`'s own docstring refuses one read over.
        found |= set(re.findall(r'"([a-z][a-z-]*\.[a-z][a-z-]*)"', text))
    return (found | composed()) - _NOT_CODES


def composed() -> set[str]:
    """The codes `schema.py` builds from a field name, crossed with the fields it validates.

    Both halves are read from the source. The suffixes come from the `f"{field}.<suffix>"`
    literals, and the fields from what :meth:`Schema._check_text` is actually *called* with
    — so a third prose field added tomorrow widens this domain without anybody remembering
    to, which is the whole reason the fields are not a list sitting here.
    """
    import ast

    text = (SOURCE / "kernel/schema.py").read_text(encoding="utf-8")
    suffixes = set(re.findall(r'f"\{field\}\.([a-z][a-z-]*)"', text))
    fields = {
        node.args[0].value
        for node in ast.walk(ast.parse(text))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_check_text"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    }
    assert suffixes and fields, "the composed-code read stopped finding anything"
    return {f"{field}.{suffix}" for field in fields for suffix in suffixes}


#: Rows that are not codes: a `varies` answer swapped in for one that is (RK427). Named,
#: because the alternative is loosening the assertion that every row is reachable — and the
#: row nothing reaches is exactly what the other direction of this test exists to catch.
_SWAPPED_IN = frozenset({"priority.unmigrated"})


# -- totality (RK421) --------------------------------------------------------


def test_every_code_the_package_can_emit_has_a_door():
    missing = sorted(emitted() - set(codes()))
    assert not missing, (
        f"{len(missing)} code(s) report a defect and name no remedy: {missing}. "
        f"A check added to the gate states its repair in roadkeep.remedying, or the "
        f"only route left is the hand-edit the guard denies."
    )


def test_the_scrape_sees_a_code_whose_head_carries_a_hyphen():
    """RK1266, and the half a totality test cannot assert about itself.

    The domain was `[a-z]+\\.[a-z][a-z-]*`: a hyphen allowed after the dot and refused before
    it. Every `non-goal.*` code fell outside it — including `non-goal.duplicate`, a literal in
    a file this has scraped since the beginning — so four codes were reported by the gate,
    answered by nothing, and green for as long as they existed. A totality test is only as
    total as its domain, and the domain is the thing nothing else was watching.

    Asserted over the codes rather than over the pattern: a regex compared to a regex is the
    same claim twice, and what has to hold is that these four are *in* what the scrape reads.
    """
    from roadkeep import scoping

    hyphenated = {scoping.LEAD, scoping.WHY, scoping.SHAPE, "non-goal.duplicate"}
    assert all("-" in code.split(".")[0] for code in hyphenated), hyphenated
    assert hyphenated <= emitted(), sorted(hyphenated - emitted())
    # And they are answered, which is the finding this task actually closed.
    assert hyphenated <= set(codes()), sorted(hyphenated - set(codes()))


def test_the_module_that_declares_a_code_is_one_the_scrape_reads():
    """The other half (RK1265, RK1266): a code named as a module constant reaches `linting`
    through a variable, so scraping the reporter alone sees none of them. Both bullet
    grammars declare theirs that way, and both are read here now — a third grammar added
    tomorrow is a red in `test_every_code_the_package_can_emit_has_a_door` only if somebody
    adds its module too, which is the limit this states rather than papers over."""
    from roadkeep import criteria, scoping

    for module in (scoping, criteria):
        declared = {module.LEAD, module.WHY, module.SHAPE}
        assert declared <= emitted(), sorted(declared - emitted())
        assert declared <= set(codes()), sorted(declared - set(codes()))


def test_every_site_supplies_the_subject_its_own_remedy_substitutes():
    """The half of totality a lookup cannot check, and the one that failed first.

    `codes()` proves a row exists; it says nothing about whether the *emission site* passes
    the value that row interpolates. Three did not — `block.repeated`, `block.unrecorded`
    and `block.unorganised` all name a heading and none of them put the label anywhere the
    remedy could read — so `block merge …` came back with a blank where the label goes,
    which is the guess RK420 exists to remove, reintroduced one layer down.

    Every unit test missed it for the same reason: a fixture constructs `Finding(code, …,
    "RK1")` and hands over an id the real call never passes. So this reads the **source**,
    the way `test_provenance` reads it for a literal invocation: a call whose code has `{id}`
    in its template must pass an id or a subject, positionally or by name.
    """
    import ast

    needs = {
        code
        for code, rule in remedying._TABLE.items()  # noqa: SLF001 - the table is the subject
        for argv, _ in rule.doors
        if any("{id}" in word for word in argv)
    }
    tree = ast.parse((SOURCE / "linting.py").read_text(encoding="utf-8"))
    blank = [
        f"linting.py:{node.lineno} emits {node.args[0].value} with no id and no subject"
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in ("Finding", "Note")
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value in needs
        # `id` is the fifth positional; `subject` only ever arrives by name.
        and not (len(node.args) >= 5 or any(k.arg in ("id", "subject") for k in node.keywords))
    ]
    assert not blank, blank


def test_the_table_answers_no_code_that_cannot_be_reported():
    # The other direction, which is the one that rots quietly: a row for a code deleted
    # from the gate is a row nothing ever reaches, and `explain` would list it as
    # vocabulary this tool does not have.
    stale = sorted(set(codes()) - emitted() - _SWAPPED_IN)
    assert not stale, f"remedy rows for codes nothing emits: {stale}"


def test_every_kind_is_one_of_the_five():
    for code in codes():
        found = remedy(Finding(code, "ROADMAP.md", "", 1, "RK1"))
        assert found is not None and found.kind in KINDS, code


def test_a_read_is_never_something_repair_would_execute():
    # RK422's finding: a read costs a step, writes nothing and leaves the finding standing,
    # so it is a kind of its own rather than a `run` that happens not to help.
    for code in codes():
        found = remedy(Finding(code, "ROADMAP.md", "", 1, "RK1"))
        assert found is not None
        if found.kind == "read":
            assert not found.runnable, code
            # One door, or an ordered several that says it is one (RK1336). The claim here
            # was never about the count — it is that a read is not a repair — and the count
            # rode along until a read needed a second step.
            assert len(found.doors) == 1 or found.sequence, code


def test_a_decision_is_stated_exactly_where_there_is_one():
    for code in codes():
        found = remedy(Finding(code, "ROADMAP.md", "", 1, "RK1"))
        assert found is not None
        if found.kind == "decide":
            # Two doors and a sentence separating them, or the caller picks by running one
            # and reading its refusal — which is the loop this whole task removes.
            assert len(found.doors) > 1, code
            assert found.decision, code
            assert not found.sequence, code
        elif found.sequence:
            # RK1336's shape and the reason this branch is not `len(doors) == 1` relaxed: a
            # row may carry several doors that are *ordered*, and until it could say so the
            # only meaning several had was a choice. Named on the row rather than read off
            # the count, so the two cases stay tellable apart.
            assert len(found.doors) > 1, code
            assert not found.decision, code
        else:
            assert len(found.doors) == 1, code
            assert not found.decision, code
    # Exhaustive and not a widened disjunction: several doors are a choice or a sequence, and
    # a row that claimed both or neither would be the state this invariant exists to refuse.
    several = [
        remedy(Finding(code, "ROADMAP.md", "", 1, "RK1")) for code in codes()
    ]
    assert [
        one.code for one in several if one and len(one.doors) > 1
    ] == [
        one.code
        for one in several
        if one and (bool(one.decision) ^ one.sequence) and len(one.doors) > 1
    ]


# -- the shape of a remedy -------------------------------------------------


def test_a_runnable_remedy_carries_no_blank():
    for code in codes():
        found = remedy(Finding(code, "ROADMAP.md", "", 12, "RK1"))
        assert found is not None
        if found.kind in ("fix", "run"):
            assert found.runnable, f"{code}: {found.doors}"
            for door in found.doors:
                assert BLANK not in " ".join(door.argv), code


def test_every_door_names_a_subcommand_this_cli_parses():
    parser = build_parser()
    known = set()
    for action in parser._subparsers._group_actions:  # noqa: SLF001 - argparse has no public read
        known |= set(action.choices)
    for code in codes():
        found = remedy(Finding(code, "ROADMAP.md", "", 1, "RK1"))
        assert found is not None
        for door in found.doors:
            if door.foreign:
                # The one kind whose door is not this tool's (RK451): a governed file whose
                # content a crash took cannot be repaired, so what closes it is the store's
                # own verb — and nothing here prefixes it with this engine or offers it to
                # `repair`. Asserted the other way round, which is the claim that matters.
                assert door.argv[0] not in known, f"{code}: {door.argv[0]} is a subcommand"
                assert not door.command.startswith(invocation())
                assert door.call() is None
                continue
            assert door.argv[0] in known, f"{code}: {door.argv[0]} is not a subcommand"


def test_a_template_field_with_no_value_keeps_its_blank():
    # `--line None` looks runnable and is not; `--line …` says which word is missing.
    found = remedy(Finding("id.duplicate", "CHANGELOG.md", "", None, "RK1"))
    assert found is not None
    rendered = [" ".join(d.argv) for d in found.doors]
    assert all("None" not in line for line in rendered), rendered
    assert any(BLANK in line for line in rendered), rendered


def test_the_id_and_the_line_are_substituted():
    found = remedy(Finding("id.duplicate", "CHANGELOG.md", "", 275, "RK403"))
    assert found is not None
    assert ("record", "drop", "RK403", "--line", "275") in {d.argv for d in found.doors}
    assert ("record", "renumber", "RK403", "--line", "275") in {d.argv for d in found.doors}


def test_a_queue_finding_substitutes_its_token_and_not_its_id():
    # The queue codes carry no id — the message opens `queues RK12, …` and a prefix would
    # print `RK12: queues RK12` — so the subject is the field the remedy reads (RK420).
    found = remedy(Finding("priority.duplicate", "ROADMAP.md", "", 9, subject="Block D"))
    assert found is not None
    assert found.doors[0].argv == ("priority", "drop", "Block D")


def test_a_paused_block_is_read_by_id_and_dropped_by_token():
    # The only value this table can substitute is the queue token, and neither door a task
    # would take accepts one: `resume` takes an id, `list --block` takes a bare label. A
    # door that refuses when run is the defect RK420 exists to remove, one row down (RK434).
    found = remedy(Finding("priority.block-paused", "ROADMAP.md", "", 9, subject="Block A"))
    assert found is not None and found.kind == "decide"
    assert [door.argv for door in found.doors] == [
        ("list", "--role", "deferred"),
        ("priority", "drop", "Block A"),
    ]


def test_the_door_for_a_heading_before_its_lines_names_a_block_the_file_declares(tmp_path):
    """The remedy read *the block was never declared* under the one code that fires only
    where a heading does (RK435). Asserted structurally rather than as a substring: the
    label the door names is one `declared_blocks` carries, which is the same oracle the
    finding was raised from.
    """
    config = _project(tmp_path, roadmap=_UNSTARTED)
    (note,) = [
        n for n in lint(config).notes if n.code == "priority.block-unstarted"
    ]
    found = remedy(note, config)
    assert found is not None and found.kind == "decide"
    assert found.doors[0].argv[:3] == ("add", "--block", "B")
    assert "B" in Backlog.load(config).declared_blocks()
    # The two spellings, one line apart: `priority drop` takes the token and `--block` takes
    # the label inside it, and a door mixing them exits 2 on the remedy RK420 added.
    assert found.doors[1].argv == ("priority", "drop", "Block B")


def test_an_early_heading_is_never_closed_by_dropping_it_unasked():
    # `priority drop` is the one move that guarantees the tier never fires, and the queue
    # keeps no place to put a token back into — the fact `priority.deferred` is a `decide`
    # for. So it is offered second and never alone, and no automated pass can take it.
    found = remedy(Finding("priority.block-unstarted", "ROADMAP.md", "", 5, subject="Block B"))
    assert found is not None and not found.runnable
    assert [door.argv[0] for door in found.doors] == ["add", "priority"]


def test_the_explanation_of_an_early_heading_states_its_own_condition():
    # `explain` prints the cause, so the contradicted sentence was the code's published
    # definition and not only a line in a report.
    found = explain("priority.block-unstarted")
    assert found is not None and found.kind == "decide"
    assert "never declared" not in str(found)


def test_every_template_field_a_door_names_is_one_the_substitution_fills():
    """`{first}` and `{role}` were documented beside the table and substituted nowhere.

    A fifth unfilled field would arrive exactly that way, and a door rendering its own
    braces is a command line no shell repairs (RK435). Read off the source rather than the
    table, because two rules are minted inside `_varied` and never appear in `_TABLE`.

    `file` is the fourth and arrived with RK451, the one remedy that is about a file rather
    than about a line in one; `role` is the fifth and arrived with RK490, which is also where
    the set stopped being written out here — `FIELDS` is the declaration and this reads it.
    """
    import ast

    source = (SOURCE / "remedying.py").read_text(encoding="utf-8")
    named = {
        field
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        for field in re.findall(r"\{(\w+)\}", node.value)
    }
    assert named <= set(remedying.FIELDS), sorted(named - set(remedying.FIELDS))


def test_a_note_gets_a_remedy_on_the_same_lookup():
    found = remedy(Note("block.emptied", "ROADMAP.md", "", 3, "D"))
    assert found is not None and found.kind == "read"


def test_an_unknown_code_gets_none_rather_than_a_guess():
    assert remedy(Finding("nothing.here", "ROADMAP.md", "", 1)) is None


# -- L4: what the tool may not write -----------------------------------------


def test_a_prose_field_is_never_composed_for_the_author():
    # The five fields the tool refuses to write. Each one's remedy names the door and
    # leaves the field: a generator here reintroduces exactly the drift this exists to stop.
    for code in (
        "why.too-long",
        "why.sentences",
        "symptom.too-long",
        "block.unrecorded",
        "section.too-long",
    ):
        found = remedy(Finding(code, "ROADMAP.md", "", 1, "RK1"))
        assert found is not None
        assert found.kind in ("compose", "decide"), code
        assert not found.runnable, code
        # Two shapes of the same blank: a marked placeholder, or the dash every door that
        # takes a paragraph reads standard input from. Both say the field is the author's.
        assert any(
            BLANK in d.argv or "-" in d.argv for d in found.doors
        ), code


#: The two rows that ask for two fields, and why neither is the defect this test hunts: a
#: label the heading word cannot render has no line to read the replacement off, so both the
#: new label and its title are the author's; and a heading declared before its lines is
#: closed by filing one, which `add` cannot take with a single blank — `--symptom` and
#: `--why` are both required and both are L4's (RK435). Every other door leaves exactly one.
_TWO_BLANKS = frozenset({"block.format", "priority.block-unstarted"})


def test_every_door_leaves_exactly_one_field_to_the_author():
    # A door with several blanks is a door the caller composes from scratch, which is the
    # state this task replaced — so the bound is one, and the exceptions are named. Every
    # kind that can carry a blank, not `compose` alone: a `decide` door carries one wherever
    # the choice is between an editorial write and one only the author can compose, so a
    # bound checked on `compose` only is a bound a row escapes by changing kind.
    for code in codes():
        found = remedy(Finding(code, "ROADMAP.md", "", 1, "RK1"))
        assert found is not None
        if found.kind not in ("compose", "decide") or code in _TWO_BLANKS:
            continue
        for door in found.doors:
            blanks = sum(1 for word in door.argv if BLANK in word or word == "-")
            assert blanks <= 1, f"{code}: {door.argv} asks for {blanks} fields at once"


def test_the_mechanical_class_is_lint_fix_and_says_so():
    for code in ("char.bom", "char.invisible", "deps.stale", "line.non-canonical"):
        found = remedy(Finding(code, "ROADMAP.md", "", 1, "RK1"))
        assert found is not None and found.kind == "fix"
        assert found.doors[0].argv == ("lint", "--fix"), code


# -- what the project decides, not the table (L6) -----------------------------


def test_the_varying_rows_are_derived_from_the_table():
    # Each is an answer the table cannot give from a code alone: three are per-project (L6) —
    # which scheme derives the pointer, which file a finding is about, which declaration
    # holds the queue (RK427) — and the fourth is per *finding*, because `block.repeated`'s
    # own sentence branches on whether the later region is empty and the remedy has to say
    # the same verb (RK468).
    assert VARIES == {
        "ref.mismatch": "ref_scheme",
        # RK1337, and the second row the scheme decides: under an outline a duplicate moves
        # to a free anchor, and under an id scheme there is no free anchor to derive and
        # `section move` refuses an id-addressed section outright — so what closes it is not
        # the same command with a different argument but a different pair of verbs.
        "section.duplicate": "ref_scheme",
        "id.duplicate": "role",
        "priority.shipped": "queue",
        "priority.retired": "queue",
        "block.repeated": "region",
        # And the fifth, also per finding (RK472): the drop this names refuses while an open
        # line claims a section nested under the one being dropped, so `runnable` — which is
        # a question about the argv's shape — dispatched it and was refused, run after run.
        "section.stale": "nested",
        # The sixth, per finding again (RK1110): which of the three projections went stale.
        # A literal `--readme` was right while there were two targets in one file each, and
        # with a third it became a door contradicting the message printed above it.
        "export.stale": "target",
    }


def test_a_duplicate_id_in_the_roadmap_is_renumber_and_not_record_renumber(tmp_path):
    config = _project(tmp_path)
    roadmap = config.relative(config.path("roadmap"))
    found = remedy(Finding("id.duplicate", roadmap, "", 7, "RK1"), config)
    assert found is not None
    assert found.doors[0].argv == ("renumber", "RK1")
    ledger = config.relative(config.path("changelog"))
    other = remedy(Finding("id.duplicate", ledger, "", 7, "RK1"), config)
    assert other is not None
    assert other.doors[0].argv[:2] == ("record", "drop")


def test_an_outline_anchor_is_the_authors_and_not_the_fixers(tmp_path):
    config = _project(tmp_path, ref_scheme="outline")
    found = remedy(Finding("ref.mismatch", "ROADMAP.md", "", 5, "RK1"), config)
    assert found is not None and found.kind == "compose"
    derived = _project(tmp_path / "other", ref_scheme="id")
    assert remedy(Finding("ref.mismatch", "ROADMAP.md", "", 5, "RK1"), derived).kind == "fix"


# -- the report carries it (RK420) -------------------------------------------


def test_the_json_report_carries_a_runnable_remedy(tmp_path, capsys):
    from roadkeep.cli import EXIT_GATE, main

    config = _project(tmp_path, roadmap=_DUPLICATE)
    assert main(["-C", str(tmp_path), "lint", "--json"]) == EXIT_GATE
    import json

    payload = json.loads(capsys.readouterr().out)
    duplicates = [f for f in payload["findings"] if f["code"] == "id.duplicate"]
    assert duplicates, payload["codes"]
    found = duplicates[0]["remedy"]
    assert found["kind"] == "decide"
    assert found["doors"][0]["argv"][0] == "renumber"
    assert all(door["complete"] for door in found["doors"])


def test_the_text_report_prints_the_command_under_the_finding(tmp_path, capsys):
    from roadkeep.cli import EXIT_GATE, main

    _project(tmp_path, roadmap=_DUPLICATE)
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_GATE
    out = capsys.readouterr().out
    # The invocation is derived per machine (RK254), so the assertion is about the argv and
    # not about the word in front of it — which is the whole reason that word is derived.
    assert f"{invocation()} renumber RK1" in out


def test_the_mechanical_class_is_counted_once_and_not_printed_per_line(tmp_path, capsys):
    from roadkeep.cli import EXIT_GATE, main

    _project(tmp_path, roadmap=_INVISIBLE)
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_GATE
    out = capsys.readouterr().out
    # Said once in the summary, never under each finding: the mechanical remedy is
    # identical on every finding it answers, so repeating it spends the report's length
    # on the findings that cost the reader nothing.
    assert out.count(f"{invocation()} lint --fix") == 1
    assert "need no decision" in out


# -- fixtures ----------------------------------------------------------------

_CLEAN = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
"""

_DUPLICATE = _CLEAN + (
    "- 📋 **RK1** (deps: —) **A second symptom under one id** — Because of another"
    " reason. → §RK1\n"
)

#: A zero-width space inside the symptom: invisible in an editor, and the character pass's.
_INVISIBLE = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first​symptom** — Because of a reason. → §RK1
- 📋 **RK2** (deps: —) **A second​symptom** — Because of a reason. → §RK2
"""

#: A heading `block add` wrote and no line filed under it yet, queued: the one state
#: `priority.block-unstarted` is about (RK435). It pairs with `_LEDGER`, which files entries
#: under Block A alone — that is what keeps this `unstarted` rather than `block-empty`.
_UNSTARTED = """# Roadmap

## Priority

- Block B

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1

## Block B — Declared and not yet filled
"""

_LEDGER = """# Shipped

## Block A — The model

- ✅ **RK5** **An earlier symptom** — Because it was done.
"""

_PROSE = """# Design rationale

## Block A — The model

### §RK1 The first design

The reasoning the first line has no room for.

### §RK2 The second design

The reasoning the second line has no room for.
"""


def _project(tmp_path: Path, roadmap: str = _CLEAN, ref_scheme: str = "id") -> Config:
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\nref_scheme = "{ref_scheme}"\n[files]\n'
        'roadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'improvements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    for name, body in (
        ("ROADMAP.md", roadmap),
        ("CHANGELOG.md", _LEDGER),
        ("IMPROVEMENTS.md", _PROSE),
    ):
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


# -- the vocabulary, as a command (RK423) ------------------------------------


def test_every_code_explains_itself():
    for code in codes():
        found = explain(code)
        assert found is not None, code
        assert found.cause, code
        assert found.kind in KINDS, code


def test_a_fix_row_states_its_cause_and_no_other_row_repeats_one():
    """The rule that keeps one sentence in one place, asserted in both directions.

    A `fix` door describes the *repair* — "the mark is deleted" says nothing about what put
    it there — so those rows carry a `cause` of their own. Every other kind already had to
    state the defect in order to say what choosing a door means, so a second sentence beside
    it would be the drift this package exists to stop, one layer down.
    """
    for code in codes():
        rule = remedying._TABLE[code]  # noqa: SLF001 - the table is the subject
        if rule.kind == "fix":
            assert rule.cause, f"{code}: a fix row's door describes the repair, not the cause"
        else:
            assert not rule.cause, f"{code}: the doors already say this"


def test_the_cause_of_a_single_door_row_is_that_door_and_never_a_second_sentence():
    found = explain("section.stale")
    assert found is not None
    assert found.cause == found.remedy.doors[0].what
    # And it is printed once, not twice.
    assert str(found).count(found.cause) == 1


def test_a_decision_keeps_what_separates_its_doors():
    # The one place the `what` is not a restatement of the cause: it is what distinguishes
    # this door from the other, which is the entire content of a decision.
    found = explain("id.duplicate")
    assert found is not None
    rendered = str(found)
    for door in found.remedy.doors:
        assert door.what in rendered, door.argv


def test_a_code_this_gate_cannot_report_is_refused_with_the_near_ones(capsys):
    from roadkeep.cli import EXIT_USAGE, main

    assert main(["explain", "why.enormous"]) == EXIT_USAGE
    err = capsys.readouterr().err
    assert "not a code this gate reports" in err
    assert "why.too-long" in err


def test_the_listing_is_one_line_per_code(capsys):
    from roadkeep.cli import EXIT_OK, main

    assert main(["explain"]) == EXIT_OK
    out = capsys.readouterr().out.splitlines()
    # One per code, plus the count.
    assert len(out) == len(codes()) + 1
    assert out[-1] == f"{len(codes())} code(s) this gate can report"


def test_the_composed_read_finds_what_the_literal_one_cannot():
    """RK428: half the schema's codes are built from the field name, and a pattern over
    literals is blind to every one of them — silently, since the suite cannot ask about a
    string nothing writes down."""
    found = composed()
    # Both halves are read from the source, so this is what the schema actually validates.
    assert {"why.newline", "symptom.newline", "why.empty", "symptom.empty"} <= found
    literal: set[str] = set()
    for name in ("linting.py", "kernel/schema.py"):
        literal |= set(
            re.findall(r'"([a-z]+\.[a-z][a-z-]*)"', (SOURCE / name).read_text(encoding="utf-8"))
        )
    # The measurement: these existed at runtime and no literal read could reach them.
    assert found - literal, "the composed read found nothing the literal one missed"


def test_the_fields_come_from_the_calls_and_not_from_a_list_here():
    # A third prose field added tomorrow widens the domain without anybody remembering to,
    # which is why the fields are scraped from `_check_text`'s call sites rather than typed.
    assert {code.split(".")[0] for code in composed()} == {"symptom", "why"}


def test_the_composed_read_fails_loudly_if_the_source_stops_matching():
    # The one way a scrape stops asserting anything is by finding nothing and passing. Both
    # halves are asserted non-empty inside `composed`, so a rename is a red here.
    assert composed()


# -- the same door, on the surface the caller is already on (RK449) ------------


def test_a_door_is_published_as_a_call_where_the_session_serves_it():
    """RK420 gave every finding the command that closes it. `lint` and `explain` are both
    served as tools, and what they handed a caller there was the argv — a list of shell
    words, to the one surface RK57 left with no console script and no PATH entry."""
    door = remedying.Door(argv=("amend", "RK1", "--dep", BLANK), what="…")
    assert door.call() == ("amend", {"id": "RK1", "deps": [BLANK]})
    payload = Remedy(code="deps.unknown", kind="run", doors=(door,)).payload("mcp__roadkeep__")
    row = payload["doors"][0]
    # Both spellings, and the argv is still the fact `repair` dispatches.
    assert row["argv"] == ["amend", "RK1", "--dep", BLANK]
    assert row["call"] == {
        "tool": "mcp__roadkeep__amend",
        "arguments": {"id": "RK1", "deps": [BLANK]},
    }


def test_the_call_is_derived_from_the_argv_and_never_tabled_beside_it():
    """The subcommand's own parser, which is what `serving` reads to publish the schema — so
    a renamed flag moves both directions at once and there is no third declaration."""
    assert remedying.Door(argv=("record", "drop", "RK1"), what="…").call() == (
        "record_drop",
        {"id": "RK1"},
    )
    assert remedying.Door(argv=("section", "add", "RK1", "--title", BLANK), what="…").call() == (
        "section_add",
        {"anchor": "RK1", "title": BLANK},
    )


def test_the_one_remedy_that_must_stay_a_shell_command_does_so_by_derivation():
    """`--fix` writes, and RK16 keeps that where a human is standing, so `lint` is served
    without it. A door setting a field the tool surface withholds has no call — which is the
    rule, not an exception written for this row."""
    assert remedying.Door(argv=("lint", "--fix"), what="…").call() is None
    payload = Remedy(
        code="dep.order", kind="fix", doors=(remedying.Door(argv=("lint", "--fix"), what="x"),)
    ).payload("mcp__roadkeep__")
    assert "call" not in payload["doors"][0]


def test_a_verb_this_surface_does_not_serve_has_no_call():
    """`init` runs once, before the project is governed, so nothing serves it — where `gaps`
    stood here until RK463 put the eight reads the skill names on the surface, which is the
    same change read from this end: that door now publishes a call."""
    assert remedying.Door(argv=("init",), what="…").call() is None
    assert remedying.Door(argv=("gaps",), what="…").call() == ("gaps", {})


def test_a_session_with_no_tools_is_published_the_argv_alone():
    """What every consumer written before this already reads: absent, not null, for the
    reason `_remedy_json` gives about the key itself."""
    door = remedying.Door(argv=("amend", "RK1", "--dep", BLANK), what="…")
    payload = Remedy(code="deps.unknown", kind="run", doors=(door,)).payload()
    assert "call" not in payload["doors"][0]
    assert payload["doors"][0]["argv"] == ["amend", "RK1", "--dep", BLANK]


def test_every_complete_door_this_surface_serves_has_a_call():
    """The totality claim RK421 makes about the table, asked of the second spelling.

    Scoped to the doors that are **complete**, because an incomplete one has no call for the
    same reason it has no runnable command: `record drop … --line …` cannot put the marker in
    a field the parser types as a number, and `section move …` is missing the destination it
    requires. Both already say so through `complete`, and a call rendered around the marker
    would look makeable and not be.

    What is left over is `lint --fix` and nothing else — the one field the tool surface
    withholds, and it falls out of the derivation rather than being listed here.
    """
    from roadkeep.serving import TOOLS

    served = {tuple(tool.argv_head) for tool in TOOLS if not tool.always}
    uncalled = set()
    for code in codes():
        found = explain(code, Config.default())
        assert found is not None, code
        for door in found.remedy.doors:
            words = tuple(door.argv)
            if not door.complete or not (words[:2] in served or words[:1] in served):
                continue
            if door.call() is None:
                uncalled.add(words)
    assert uncalled == {("lint", "--fix")}


# -- the sentence and the remedy answer one question (RK468) ------------------


def repeated(tmp_path, later: str = "") -> Config:
    """A ledger declaring one label twice, with the later region empty or holding an entry.

    Found on Turing's live ledger and reduced to this: the state RK425 branches its sentence
    on, and the one the remedy table could not ask about.
    """
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text("# Roadmap\n\n## Block A\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "# Shipped\n\n## Block A — First\n\n- ✅ **RK1** **A symptom** — It works.\n\n"
        "## Block A — Again\n" + later,
        encoding="utf-8",
    )
    return Config.discover(tmp_path)


def test_the_remedy_is_the_verb_the_finding_s_own_sentence_names(tmp_path):
    """RK420 made every finding carry the command that closes it. On a `block.repeated`
    whose later region is empty the message said `block drop` and the remedy said `block
    merge` — two commands on one finding, and `repair` dispatched the one the sentence above
    it did not name. Both leave a legal file, which is why nothing caught it."""
    config = repeated(tmp_path)
    found = next(f for f in lint(config).findings if f.code == "block.repeated")
    assert "`block drop A` takes the empty one out" in found.message
    door = remedy(found, config).doors[0]
    assert door.argv == ("block", "drop", "A")


def test_a_region_that_holds_work_is_folded_and_says_so(tmp_path):
    config = repeated(tmp_path, later="\n- ✅ **RK2** **Another** — It works.\n")
    found = next(f for f in lint(config).findings if f.code == "block.repeated")
    assert "block merge A" in found.message
    assert remedy(found, config).doors[0].argv == ("block", "merge", "A")


def test_the_verb_offered_is_the_one_that_closes_the_finding(tmp_path):
    """The deeper half, and the reason `_droppable` alone was the wrong reader: it asks
    whether the verb would *refuse*, not which heading comes out. A repeat in the ledger
    beside an empty `## Block A` in the roadmap answered droppable, and `block drop` then
    withdrew the roadmap's heading and left this finding standing."""
    from roadkeep.blocking import drop_block, merge_block

    for later, verb in ((None, drop_block), ("\n- ✅ **RK2** **Another** — It works.\n", merge_block)):
        root = tmp_path / ("empty" if later is None else "held")
        root.mkdir()
        config = repeated(root, later=later or "")
        verb(config, "A").save()
        assert not [f for f in lint(Config.discover(root)).findings if f.code == "block.repeated"]


def test_the_row_declares_what_it_varies_with(tmp_path):
    """The third thing a row is decided by, beside the config's two (L6): a reader asking
    `explain` what this code means is told the answer moves."""
    assert VARIES["block.repeated"] == "region"
    described = explain("block.repeated", Config.default())
    assert described is not None and described.varies == "region"
    assert "later region holds anything" in str(described)


# -- which prose file the remedy is about (RK470) -----------------------------


def _two_prose(tmp_path: Path) -> Config:
    """A project declaring both prose files, which is what makes `--role` load-bearing."""
    config = _project(tmp_path)
    (tmp_path / "roadkeep.toml").write_text(
        (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")
        + 'strategy = "STRATEGY.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "STRATEGY.md").write_text(
        "# Strategy\n\n## Block A — The model\n\n### §RK1 A design\n\nProse.\n",
        encoding="utf-8",
    )
    return Config.discover(tmp_path)


def test_a_section_remedy_names_the_file_the_finding_is_about(tmp_path):
    """RK420 promises a complete argv, and on a project with one prose file it was: every
    `section` verb defaults to that file. Measured on Turing, which declares two: a
    `section.stale` at `docs/STRATEGY.md` produced `section drop XIV.2`, which opened
    `docs/IMPROVEMENTS.md` and answered `no §XIV.2 section` — a remedy that cannot close its
    own finding."""
    config = _two_prose(tmp_path)
    on_strategy = Finding("section.stale", "STRATEGY.md", "", 5, "RK1")
    assert remedy(on_strategy, config).doors[0].argv == (
        "section", "drop", "RK1", "--role", "strategy",
    )
    on_improvements = Finding("section.stale", "IMPROVEMENTS.md", "", 5, "RK1")
    assert remedy(on_improvements, config).doors[0].argv == (
        "section", "drop", "RK1", "--role", "improvements",
    )


def test_a_project_with_one_prose_file_is_given_no_such_word(tmp_path):
    """The question §RK470 left open: on a single-file project the flag names the default and
    changes nothing, and these argvs are read by people as well as run by `repair`."""
    config = _project(tmp_path)
    found = remedy(Finding("section.stale", "IMPROVEMENTS.md", "", 5, "RK1"), config)
    assert found.doors[0].argv == ("section", "drop", "RK1")


def test_every_section_verb_is_scoped_and_nothing_else_is(tmp_path):
    """Derived here rather than written into five rows: `section add`, `amend`, `drop` and
    `move` all take `--role`, and a remedy that names a *task* is about an id rather than a
    file — `show RK1` finds its own section."""
    config = _two_prose(tmp_path)
    for code in codes():
        found = remedy(Finding(code, "STRATEGY.md", "", 5, "RK1"), config)
        assert found is not None, code
        for door in found.doors:
            if door.argv[:1] == ("section",):
                assert door.argv[-2:] == ("--role", "strategy"), f"{code}: {door.argv}"
    # And it touches nothing else. `priority.block-paused` answers `list --role deferred`,
    # whose role the *table* wrote and which names the store rather than a prose file — so
    # the claim is that this appends to `section` argvs, not that nothing else carries one.
    for argv in (
        ("list", "--role", "deferred"),
        ("show", "RK1"),
        ("anchors",),
        ("lint", "--fix"),
    ):
        values = remedying._values(Finding("x", "STRATEGY.md", "", 5, "RK1"), config)
        assert remedying._scoped(argv, values, config) == argv


def test_the_scoped_argv_is_one_the_cli_accepts(tmp_path):
    """The same rule every door is held to: a flag appended here that the verb does not take
    would be a remedy that exits 2."""
    config = _two_prose(tmp_path)
    found = remedy(Finding("section.stale", "STRATEGY.md", "", 5, "RK1"), config)
    build_parser().parse_args(list(found.doors[0].argv))


# -- every door, not only the ones repair runs (RK474) ------------------------


def _every_door(config: Config):
    """Each code's doors under one project, with the finding each row varies on.

    `varies` decides four rows off the config and the finding, so a sweep that asked with one
    shape would check the branch this project happens to take and none of the others. The
    file is what `_role_of` reads and the line is what `block.repeated` needs, so both are
    passed rather than defaulted.
    """
    for code in codes():
        for role in ("roadmap", "improvements"):
            if not config.has(role):
                continue
            where = config.relative(config.path(role))
            found = remedy(Finding(code, where, "", 5, "RK1"), config)
            assert found is not None, code
            for door in found.doors:
                yield code, where, door


def test_every_complete_door_is_an_argv_the_cli_accepts(tmp_path):
    """RK473 holds the remedies `repair` dispatches, which is the third of the table it runs.
    `read`, `compose` and `decide` are printed instead — most of the seventy codes, and the
    half a person acts on — and nothing checked them past their first word.

    The whole argv and not the subcommand: a flag the verb does not take, or a positional it
    requires and the row omits, is a door that exits 2 in the reader's hands. Decidable here
    and needing no corpus, which is the question §RK474 left open.

    **Complete doors only.** An incomplete one carries `…` where the author's word goes, and
    a blank in a typed field cannot parse by construction — `record drop … --line …` is the
    row that proves it, and `complete` is what already says so.
    """
    for role in ("id", "outline"):
        config = _project(tmp_path / role, ref_scheme=role)
        for code, where, door in _every_door(config):
            if door.foreign or not door.complete:
                continue
            try:
                build_parser().parse_args(list(door.argv))
            except SystemExit:
                raise AssertionError(
                    f"{code} on {where} under ref_scheme={role}: "
                    f"`{' '.join(door.argv)}` is not an argv this CLI accepts"
                ) from None


def test_an_incomplete_door_is_incomplete_for_a_reason(tmp_path):
    """The exemption above, held so it cannot widen: a door this sweep skips has to be one
    whose blank L4 left to the author, not one that failed to substitute."""
    config = _project(tmp_path)
    for code, _, door in _every_door(config):
        if not door.complete:
            assert BLANK in " ".join(door.argv), f"{code}: {door.argv} is incomplete without a blank"


# -- the one renderer, held total the way the table is (RK488) -----------------

#: The two modules allowed to spell a served command: the renderer, and the one that decides
#: which prefix this session has. Every other module states the **door** and lets `Door.named`
#: choose the spelling — which is the property below, and the reason a seventh surface costs
#: one change instead of forty.
#: Addressed under the package and not by filename since RK494, `verbs/` holding a module
#: per verb family named after the domain module it calls.
_MAY_SPELL = frozenset({"remedying.py", "provenance.py"})


def _spelling(source: str) -> list[str]:
    """Every place this module composes a served command, by line. Docstrings excluded.

    Read from the **AST** and not from the text, so a comment recording what the defect was
    is not itself a violation of it — this file's own prose names `mcp__roadkeep__lint` while
    asserting nothing composes one, and a grep could not tell those apart.
    """
    import ast

    tree = ast.parse(source)
    documented = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) not in documented and "mcp__" in node.value:
                found.append(f"line {node.lineno}: a prefix written out as {node.value!r}")
        if not isinstance(node, ast.JoinedStr):
            continue
        for part in node.values:
            if not isinstance(part, ast.FormattedValue):
                continue
            spelled = part.value
            name = (
                spelled.attr
                if isinstance(spelled, ast.Attribute)
                else spelled.id
                if isinstance(spelled, ast.Name)
                else ""
            )
            # `served` and not `prefix`: this package spells an *id* prefix that way in
            # `schema` and `adopting`, and an indent that way in `capturing`, so the wider
            # name would be three false reds about a word rather than about a fact.
            if name == "served":
                found.append(f"line {node.lineno}: the prefix interpolated as {name}")
    return found


def test_no_module_outside_the_renderer_spells_a_served_command():
    """RK488. `provenance.serving` says which prefix this session's tools arrive under, and it
    used to reach a message by being threaded by hand — a `served` field on `guarding.Refusal`,
    another on `attesting.Unattested`, an argument to `Remedy.payload`, a `cli._served` helper
    beside four print sites, and `serving._as_call` composing its own. Four mechanisms and a
    third copy for one fact, so a module that never learned to ask printed the shell form
    regardless; RK444, RK447, RK448, RK475, RK477 and RK479 each taught one more site, and
    nothing could say how many were left.

    This is what says how many are left. The prefix still travels as a field — which engine
    answers is a fact about the project, decided where the project is read — but nothing
    outside these two modules turns it into text. A module states its `Door` and the renderer
    spells it, so the seventh surface is one change here rather than forty out there.
    """
    composed = {}
    for module in modules():
        if module.where in _MAY_SPELL:
            continue
        found = _spelling(module.text)
        if found:
            composed[module.where] = found
    assert not composed, composed


def test_the_renderer_answers_one_spelling_to_a_table_and_to_a_sentence():
    """The property that makes the one above worth holding: a door cannot say *tool* in the
    table and *shell* in the sentence under it, which is what six separate compositions could
    and did. `lint --fix` is the case that has to answer the shell in both, because RK16 keeps
    the writing flag where a human is standing and the served `lint` withholds it."""
    for argv in (("lint",), ("lint", "--fix"), ("repair", "--dry-run"), ("init",)):
        door = remedying.Door(argv, "what it does")
        served = door.named("mcp__roadkeep__")
        assert door.mention("mcp__roadkeep__").startswith(served), argv
        assert door.spoken("mcp__roadkeep__").startswith(served), argv
        assert remedying.offered((door,), "mcp__roadkeep__")[0].strip().startswith(served), argv
        assert remedying.alongside((door,), "mcp__roadkeep__")[0] == served, argv
    # And the two that must not be served, each for its own reason: `--fix` is withheld, and
    # `init` runs once per project and is not on this surface at all.
    for argv in (("lint", "--fix"), ("init",)):
        door = remedying.Door(argv, "what it does")
        assert door.named("mcp__roadkeep__") == door.command, argv
        assert door.passing("mcp__roadkeep__") == "", argv


def test_a_sentence_names_the_engine_once_and_a_table_names_it_per_row():
    """`alongside` against `offered` (RK488). The notice is 260 characters and names three
    reads: spelling the invocation before each of them is 46 characters of repetition, which
    is a fifth of the budget spent saying `python -m roadkeep.cli` twice more."""
    doors = (
        remedying.Door(("brief",), "starts a task"),
        remedying.Door(("show", "<id>"), "joins the line to its rationale"),
    )
    said = remedying.alongside(doors)
    assert said[0] == f"{invocation()} brief"
    assert said[1] == "show <id>"
    # A table is columns, so every row carries it and they line up under each other.
    rows = remedying.offered(doors)
    assert all(invocation() in row for row in rows)
    assert len({len(row.split("  ")[0]) for row in rows}) == 1
    # Served, both forms are self-contained: there is no engine to repeat.
    assert remedying.alongside(doors, "mcp__roadkeep__") == (
        "mcp__roadkeep__brief",
        "mcp__roadkeep__show",
    )


#: The modules that may write a command out as a literal, and why each one may. Both write
#: into a file that leaves this machine, which is what makes the invocation wrong there: a
#: README carries the note to everyone who reads the repository, and the workflow runs on a
#: runner where the action this project ships is what puts `roadkeep` on PATH. Named with the
#: reason rather than skipped, because that is the difference between an exception and a
#: literal nobody has looked at since it was typed.
_MAY_WRITE_LITERALLY = {
    "exporting.py": "the note is committed into a README; an absolute path there is a "
    "message about one machine, written into the file everyone reads",
    "installing.py": "the generated workflow runs on a runner where the action this "
    "project ships is what puts the console script on PATH",
}


def _verbs() -> frozenset[str]:
    """Every subcommand this CLI parses, off the parser rather than listed here."""
    import argparse

    parser = build_parser()
    subs = next(
        one for one in parser._actions if isinstance(one, argparse._SubParsersAction)  # noqa: SLF001
    )
    return frozenset(subs.choices)


def test_a_command_written_out_as_a_literal_is_one_of_four_and_each_says_why():
    """RK488's other count. Five spellings never reached `invocation` at all — and gated on
    the verbs this CLI actually parses, four of them are commands (`roadkeep export` in the
    README note, `roadkeep lint` three times in the generated workflow) and the fifth is the
    capture's own title, which names no verb.

    Held as a register rather than repaired: both survivors write into a file that leaves this
    machine, where the literal is the right answer and the invocation is the wrong one. What
    was missing was anywhere saying so, which is how the other thirty-six got written."""
    verbs = _verbs()
    spelled = re.compile(r"\broadkeep ([a-z][a-z-]*)\b")
    found: dict[str, set[str]] = {}
    for module in modules():
        for lineno, text in _literals(module.text):
            for verb in spelled.findall(text):
                if verb in verbs:
                    found.setdefault(module.where, set()).add(f"{lineno}: roadkeep {verb}")
    assert set(found) == set(_MAY_WRITE_LITERALLY), found
    assert sum(len(where) for where in found.values()) == 4, found


def _literals(source: str) -> list[tuple[int, str]]:
    """Every string constant that is not a docstring, with its line."""
    import ast

    tree = ast.parse(source)
    documented = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    return [
        (node.lineno, node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in documented
    ]


# -- a row derives what its finding already knows (RK490) ---------------------


def test_the_declared_fields_are_exactly_the_ones_a_finding_answers(tmp_path):
    """Both directions of `FIELDS`, which is what makes it a declaration rather than a note.

    A name in the table that `_values` does not answer renders its own braces — the state
    `{first}` and `{role}` were in for years. A name `_values` answers that the declaration
    omits is the inverse and just as silent: the test above bounds the source by this set, so
    a field left out of it would make a legal row read as a defect."""
    config = _project(tmp_path)
    finding = Finding("id.duplicate", config.relative(config.path("roadmap")), "", 5, "RK1")
    assert set(remedying.FIELDS) == set(remedying._values(finding, config))
    # And with no project at all, which is what `explain` composes a class from: every name
    # still answers, because a door that cannot be told a value renders the blank rather
    # than the brace.
    assert set(remedying.FIELDS) == set(remedying._values(finding, None))


def test_no_door_the_gate_can_report_renders_a_brace(tmp_path):
    """The property the three per-row defects were instances of (RK490). RK468 named one verb
    and dispatched another, RK470 omitted the file the finding was in, RK472 dispatched a door
    the verb refuses — each found by example, each a row stating what the finding already
    knew. What a sweep can hold is that nothing is left unsaid: a brace surviving into an argv
    is a field the row named and the finding was never asked for."""
    for role in ("id", "outline"):
        config = _project(tmp_path / f"braces-{role}", ref_scheme=role)
        for code, where, door in _every_door(config):
            rendered = " ".join(door.argv)
            assert "{" not in rendered and "}" not in rendered, f"{code} on {where}: {rendered}"


def test_a_door_carries_the_finding_s_own_subject_and_never_another(tmp_path):
    """`{id}` is the finding's :attr:`Finding.token` — the explicit subject, or the id it
    usually is — read off the finding rather than recomposed here (RK490), which is the
    smallest instance of this task's rule and the one that was written twice.

    Asked with the subject set and unset, because the fallback is where the two spellings of
    it could differ: a queue finding carries `Block D` in `subject` and an id in `id`, and a
    row that read the wrong one would name a line the caller never asked about."""
    config = _project(tmp_path)
    where = config.relative(config.path("roadmap"))
    for code in codes():
        if not _names_the_subject(code):
            continue
        for subject in ("", "Block D"):
            finding = Finding(code, where, "", 5, "RK7", subject=subject)
            found = remedy(finding, config)
            assert found is not None
            assert any(
                finding.token in word for door in found.doors for word in door.argv
            ), f"{code} with subject={subject!r}: no door names {finding.token!r}"


def _names_the_subject(code: str) -> bool:
    """Whether this row writes `{id}` at all — read off the table, never listed here."""
    rule = remedying._TABLE[code]
    return any("{id}" in word for argv, _ in rule.doors for word in argv)


def test_a_section_door_names_the_role_the_finding_was_reported_about(tmp_path):
    """RK470 as a property over the table rather than as one row's repair (RK490). Every
    `section` verb takes `--role`, and on a project declaring two prose files a door that
    omits it opens the other file — so what this holds is that wherever the flag is there at
    all, its value is the finding's own file and never a default that happens to match."""
    config = _two_prose(tmp_path)
    for where, role in (("STRATEGY.md", "strategy"), ("IMPROVEMENTS.md", "improvements")):
        for code in codes():
            found = remedy(Finding(code, where, "", 5, "RK1"), config)
            assert found is not None
            for door in found.doors:
                if "--role" not in door.argv or door.argv[:1] != ("section",):
                    continue
                assert door.argv[door.argv.index("--role") + 1] == role, (code, door.argv)


def test_no_row_writes_a_word_only_the_author_could_have(tmp_path):
    """L4 over the whole table, which is what §RK491 found this law was missing (RK491).

    `test_a_prose_field_is_never_composed_for_the_author` holds it over five codes somebody
    listed — which is the state RK421 replaced for the table's *domain* and nobody had
    replaced for its *content*. A generator reintroduces exactly the drift this package
    exists to stop, and a row quietly filling in a title would look like a helpful default.

    Every word a row writes is one of four things, and none of them is prose: a subcommand
    this CLI parses, a flag, the blank (or the dash that reads standard input), or a value
    the finding itself supplied. The fifth is a **name for a governed file** — `--organise
    changelog`, `--role deferred` — which is a role this project declares (L6) rather than a
    word anybody composed, and is read off `ROLES` instead of being listed here; the sixth is
    a choice the parser itself enumerates. Both are derived, so a row inventing a value fails
    the same way a row inventing a sentence does.
    """
    from roadkeep.serving import _parsers

    config = _project(tmp_path)
    where = config.relative(config.path("roadmap"))
    # Every word any subcommand path is spelled with, nested ones included: `priority drop`
    # is two verbs and neither is a word this table composed.
    index = _parsers()
    subcommands = {word for path in index for word in path.split()}
    for code in codes():
        finding = Finding(code, where, "", 5, "RK1")
        given = set(remedying._values(finding, config).values()) | {BLANK, "-", ""}
        found = remedy(finding, config)
        assert found is not None
        for door in found.doors:
            if door.foreign:
                continue  # somebody else's argv; this table names none of its words (RK451)
            words = list(door.argv)
            # Two words before one, for `serves`' reason: `block add` is a parser and
            # `block` is the group that holds it, so the flags live on the nested one.
            nested = " ".join(words[:2])
            parser = index[nested if nested in index else words[0]]
            for before, word in zip(["", *words], words, strict=False):
                if word.startswith("-") or word in given or word in subcommands:
                    continue
                declared = next(
                    (
                        one
                        for one in parser._actions  # noqa: SLF001
                        if before in one.option_strings
                    ),
                    None,
                )
                enumerated = declared is not None and word in (declared.choices or ())
                assert enumerated or word in ROLES, (
                    f"{code}: `{' '.join(words)}` writes {word!r}, which is neither a verb, "
                    f"a flag, a blank, a value the finding gave, nor a choice the parser "
                    f"declares — so it is a word this tool composed (L4)"
                )


# -- what a door does, per door (RK1015) --------------------------------------


def _finding(code: str) -> Finding:
    return Finding(code, "ROADMAP.md", "", 1, "RK1")


def test_one_decide_can_hold_a_read_and_a_write():
    """The measurement RK1015 was filed on. `deps.unknown` is a single `decide` whose doors
    are `gaps`, which answers a question and changes nothing, and `amend <id> --dep …`, which
    writes — so a caller reading the remedy's `kind` learns `decide` about both."""
    found = remedy(_finding("deps.unknown"))
    doors = {door.argv[0]: door.writes for door in found.doors}
    assert doors == {"gaps": False, "amend": True}
    assert found.kind == "decide", "the kind is the remedy's, which is the whole point"


def test_a_read_only_verb_with_the_flag_that_makes_it_a_write_writes():
    """The case a set of verb names gets backwards, and the reason the mapping carries flags:
    `lint` is read-only — that is what keeps it out of the write lock — and `lint --fix` is
    not. Both facts are the parser's, which is where they were already declared."""
    fixes = remedy(_finding("char.tab"))
    (door,) = fixes.doors
    assert door.argv[:2] == ("lint", "--fix") and door.writes is True
    reads = remedy(_finding("engine.disagreement"))
    assert [door.writes for door in reads.doors] == [False]


def test_a_foreign_door_writes_and_this_tool_has_no_opinion_about_it():
    """`git checkout` is somebody else's command (RK451): it writes, it says so in its own
    name, and nothing here derives that from a parser that never heard of it."""
    (door,) = remedy(_finding("file.not-text")).doors
    assert door.foreign is True and door.writes is True


def test_the_payload_carries_it_because_the_caller_outside_this_process_asked():
    """The reader RK1015 was about. An editor building a quick fix has to know whether the
    thing it is about to run changes the files, and the remedy's kind cannot tell it."""
    payload = remedy(_finding("deps.unknown")).payload()
    assert [door["writes"] for door in payload["doors"]] == [True, False]


def test_the_promise_row_names_the_declaration_built_for_it():
    """RK1047. `body.promise` fires on an id no line carries, and RK1031 shipped the one
    mechanism for the reading it did not offer — an address the project spoke for and will
    never write as a line. Measured on Shio: declaring `reserved_ids` took its gate from
    twelve findings to one, and the rewording this row *did* offer is recorded there as the
    wrong fix, because a decision not to build something has to keep its address."""
    found = remedy(Finding("body.promise", "IMPROVEMENTS.md", "", 1, "RK1"))
    assert found is not None and found.kind == "decide"
    said = " ".join(door.what for door in found.doors)
    assert "reserved_ids" in said
    # The cause names the four readings it now asks the author to choose between.
    for reading in ("illustration", "should have had", "not filed yet", "reserved"):
        assert reading in found.decision, reading


def test_the_four_readings_are_four_doors():
    """One door per reading, because the decision is the author's and a row offering three
    answers to a four-way question is the tool making one of them for them."""
    found = remedy(Finding("body.promise", "IMPROVEMENTS.md", "", 1, "RK1"))
    assert len(found.doors) == 4


def test_the_ledger_finding_names_a_verb_that_reaches_the_ledger(tmp_path):
    """RK1203. `path.missing` fires on the **changelog alone** — `_paths` reads that document
    and no other, a roadmap naming an artefact its task exists to write being the opposite
    claim — so the `amend` this row used to name was not wrong for one role, it was wrong on
    every finding the code can produce.

    Found adopting Turing, whose ledger holds 755 entries written before the tool existed:
    T759 names a script that later moved to its own repository, and following the door gives
    `no open task T759 in docs/ROADMAP.md: it is already in the changelog`. `amend` loads the
    roadmap, looks the id up and raises `NotOpen` for anything the ledger holds — it was built
    to correct an open line and says so.

    Run rather than matched, which is the only way this stays fixed: an argv that looks
    complete and refuses is worse than none, because the caller spends the turn finding out.
    """
    from roadkeep.cli import EXIT_OK, main

    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    # A directory the repository does have, holding a file it does not: a token under one it
    # has never heard of is not read as a claim at all (RK217), which is the right rule and
    # would make this fixture prove nothing.
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "kept.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "ROADMAP.md").write_text("# Roadmap\n\n## Block A\n\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "# Shipped\n\n## Block A\n\n"
        "- ✅ **RK1** **A symptom** — it works, in `src/gone.py`.\n",
        encoding="utf-8",
    )
    config = Config.discover(tmp_path)
    (found,) = [one for one in lint(config).findings if one.code == "path.missing"]

    door = remedy(found, config).doors[0]
    assert tuple(door.argv[:2]) == ("record", "amend"), door.argv
    # The blank is the caller's prose (L4); everything else is a command that lands.
    filled = [one if one != BLANK else "it works, elsewhere now." for one in door.argv]
    assert main(["-C", str(tmp_path), *filled]) == EXIT_OK
    assert lint(Config.discover(tmp_path)).clean


# -- the address a door substitutes is the one the finding read (RK1206) -------


OUTLINED_CONFIG = (
    'prefix = "TT"\nref_scheme = "outline"\n[files]\nroadmap = "ROADMAP.md"\n'
    'changelog = "CHANGELOG.md"\nimprovements = "IMPROVEMENTS.md"\n'
)


def outlined(tmp_path: Path) -> Config:
    """A project whose anchors are **not** its ids, which this repository can never be.

    The whole reason RK1206 was invisible here: under `ref_scheme = "id"` the anchor *is* the
    id, so a door composed from either field is right and the two cannot be told apart. The
    corpora at `tests/corpora.py` are the other way to see it, and they are not always there.
    """
    (tmp_path / "roadkeep.toml").write_text(OUTLINED_CONFIG, encoding="utf-8")
    (tmp_path / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Block A\n\n"
        "- 📋 **TT1** (deps: —) **A symptom** — Because of a reason. → §I.1\n",
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text("# Shipped\n\n## Block A\n", encoding="utf-8")
    # The family exists and the child does not, which is the state this task is about. Without
    # it `section add I.1` is refused for a different and correct reason — an anchor states its
    # own place, so a child whose parent is missing needs the family opened first — and the
    # fixture would be measuring that stair instead of the address.
    (tmp_path / "IMPROVEMENTS.md").write_text(
        "# Improvements\n\n## Block A\n\n### I A family\n\nProse enough to matter.\n",
        encoding="utf-8",
    )
    return Config.discover(tmp_path)


def test_the_pointer_door_names_the_anchor_and_not_the_task_id(tmp_path):
    """The defect, and it can only be seen on a project whose anchors are not its ids: `TT1`
    points at `§I.1`, the section is missing, and the command underneath read `section add TT1
    --title …`. Run as printed it writes a section the line does not point at, so the finding
    survives with a second orphan beside it.

    RK14 and RK326 settled that every finding carries the command that closes it, and the
    whole value of that is the command being *runnable*.
    """
    from roadkeep.cli import EXIT_OK, main

    config = outlined(tmp_path)
    (found,) = [one for one in lint(config).findings if one.code == "ref.unresolved"]
    # The report still addresses the line, which is what a reader clicks.
    assert found.id == "TT1" and "§I.1" in found.message

    (door,) = remedy(found, config).doors
    assert "I.1" in door.argv and "TT1" not in door.argv, door.argv
    filled = [one if one != BLANK else "A design" for one in door.argv]
    assert main(["-C", str(tmp_path), *filled, "--body", "Prose enough to matter."]) == EXIT_OK
    # And the finding is gone, which is the only proof the door was the right one.
    assert not [one for one in lint(Config.discover(tmp_path)).findings
                if one.code == "ref.unresolved"]


def test_no_door_addressing_a_section_substitutes_an_address_the_finding_never_named(tmp_path):
    """The sweep RK1206 asked for, because this class is invisible on an id-scheme repository
    by construction. A door that addresses a section must substitute an address the finding's
    own sentence contains — anything else is a value the row composed rather than read.

    Held over an outline fixture for that reason, and stated as *the message mentions it*
    rather than as a field comparison: what makes a door wrong here is precisely that it names
    something the reader was never shown.
    """
    config = outlined(tmp_path)
    # A second line whose pointer resolves nowhere either, so more than one code is in play.
    roadmap = config.path("roadmap")
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8")
        + "- 📋 **TT2** (deps: —) **Another symptom** — Because of another. → §II.3\n",
        encoding="utf-8",
    )
    config = Config.discover(tmp_path)

    wrong = []
    for found in lint(config).findings:
        rule = remedy(found, config)
        if rule is None:
            continue
        for door in rule.doors:
            if tuple(door.argv[:1]) != ("section",):
                continue
            # The address is the argument after the action word.
            named = door.argv[2] if len(door.argv) > 2 else ""
            if named and named != BLANK and named not in found.message:
                wrong.append((found.code, named, found.message))
    assert wrong == [], wrong


def test_a_read_may_be_a_sequence_and_the_order_is_the_claim():
    """RK1336. `budget.session` says the surface is over and no single tool is at fault, then
    sent the reader to `cost --session` — which reprints the figure the finding just gave and
    names no tool, when what they do next is pick one to cut. The read that ranks them is
    `cost --tools`, and it could not answer a session question until RK1335 taught it this
    ceiling, so the single door was right to avoid it then and wrong to afterwards.

    Measured on this corpus before the change: the ceiling has been re-argued six times and a
    served flag withdrawn once, and a whole verb never — so ranking is not the detour."""
    found = remedy(Finding("budget.session", "roadkeep.toml", "", None, ""))
    assert found is not None and found.kind == "read"
    assert found.sequence and not found.decision
    # The order is the claim: rank, then price the whole. A set would say the same about
    # either arrangement, which is what makes this an assertion about the list.
    assert [door.argv for door in found.doors] == [
        ("cost", "--tools"),
        ("cost", "--session"),
    ]
    # And every step reaches the reader, where the terminal register spoke only the first: a
    # row carrying a sequence that printed its head drops the step saying what to do with
    # what the head shows.
    spoken = found.spoken()
    assert "cost --tools" in spoken and "cost --session" in spoken
    # `door` stays the one-door accessor, so a caller wanting *the* command still gets None
    # here rather than silently the first of two.
    assert found.door is None


def test_the_duplicate_anchor_door_is_the_one_this_scheme_has(tmp_path):
    """RK1337. The row was written for an outline and offered under both schemes. Reproduced
    at `ref_scheme = "id"`, which is what `init` writes: `anchors --next` exits 2 there,
    having no numbering to take the next of, and `section move` refuses an id-addressed
    section by design — *the address is not this verb's to move*. So the door named a command
    the verb it names rejects, in the state that produces the finding.

    No test caught it because `test_every_door_the_gate_offers_on_this_project_lands` runs the
    doors this repository's gate produces, and `section.duplicate` never fires here."""
    finding = Finding("section.duplicate", "docs/IMPROVEMENTS.md", "", 9, "RK1")
    outlined = remedy(finding, _project(tmp_path / "outline", ref_scheme="outline"))
    assert outlined is not None and outlined.kind == "compose"
    assert outlined.doors[0].argv[:2] == ("section", "move")

    identified = remedy(finding, _project(tmp_path / "ids", ref_scheme="id"))
    assert identified is not None and identified.kind == "decide"
    assert identified.decision
    # Both doors the refusal of the old one already named, and neither is `section move`.
    assert [door.argv[0] for door in identified.doors] == ["renumber", "section"]
    assert "anchors --next" not in identified.spoken()


def test_a_door_names_the_id_its_finding_carries_rather_than_a_blank():
    """RK1340. `id.paused-and-gone` is emitted with the task id — the walk over `PAIRS` passes
    it — and its doors printed `show …` and `origin …`, asking the reader to type the one
    value the tool had just held, on a finding whose whole content is that this id is in two
    files at once. The substitution is the same one `budget.tool` already spells.

    The sentence moved with the argv, which is the half worth a test of its own: `show` joins
    a task out of the files holding a piece of it and reports the ledger's side, the store's
    pause appearing in neither of its registers — so *the entry and the pause side by side*
    was a promise the door could not keep, and filling the blank would have made it a promise
    that ran.
    """
    found = remedy(Finding("id.paused-and-gone", "docs/CHANGELOG.md", "", 5, "RK7"))
    assert found is not None
    assert [door.argv for door in found.doors] == [("show", "RK7"), ("origin", "RK7")]
    assert all(BLANK not in door.argv for door in found.doors)
    assert "side by side" not in found.spoken()
