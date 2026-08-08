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
from roadkeep.cli import build_parser
from roadkeep.config import Config
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
    found: set[str] = set()
    for name in ("linting.py", "schema.py"):
        text = (SOURCE / name).read_text(encoding="utf-8")
        found |= set(re.findall(r'"([a-z]+\.[a-z][a-z-]*)"', text))
    return (found | composed()) - _NOT_CODES


def composed() -> set[str]:
    """The codes `schema.py` builds from a field name, crossed with the fields it validates.

    Both halves are read from the source. The suffixes come from the `f"{field}.<suffix>"`
    literals, and the fields from what :meth:`Schema._check_text` is actually *called* with
    — so a third prose field added tomorrow widens this domain without anybody remembering
    to, which is the whole reason the fields are not a list sitting here.
    """
    import ast

    text = (SOURCE / "schema.py").read_text(encoding="utf-8")
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
            assert len(found.doors) == 1, code


def test_a_decision_is_stated_exactly_where_there_is_one():
    for code in codes():
        found = remedy(Finding(code, "ROADMAP.md", "", 1, "RK1"))
        assert found is not None
        if found.kind == "decide":
            # Two doors and a sentence separating them, or the caller picks by running one
            # and reading its refusal — which is the loop this whole task removes.
            assert len(found.doors) > 1, code
            assert found.decision, code
        else:
            assert len(found.doors) == 1, code
            assert not found.decision, code


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


#: The one row that asks for two fields, and why that is not the defect this test hunts:
#: a label the heading word cannot render has no line to read the replacement off, so both
#: the new label and its title are the author's. Every other `compose` leaves exactly one.
_TWO_BLANKS = frozenset({"block.format"})


def test_every_compose_door_leaves_exactly_one_field_to_the_author():
    # A door with several blanks is a door the caller composes from scratch, which is the
    # state this task replaced — so the bound is one, and the exception is named.
    for code in codes():
        found = remedy(Finding(code, "ROADMAP.md", "", 1, "RK1"))
        assert found is not None
        if found.kind != "compose" or code in _TWO_BLANKS:
            continue
        door = found.doors[0]
        blanks = sum(1 for word in door.argv if BLANK in word or word == "-")
        assert blanks <= 1, f"{code}: {door.argv} asks for {blanks} fields at once"


def test_the_mechanical_class_is_lint_fix_and_says_so():
    for code in ("char.bom", "char.invisible", "deps.stale", "line.non-canonical"):
        found = remedy(Finding(code, "ROADMAP.md", "", 1, "RK1"))
        assert found is not None and found.kind == "fix"
        assert found.doors[0].argv == ("lint", "--fix"), code


# -- what the project decides, not the table (L6) -----------------------------


def test_the_varying_rows_are_derived_from_the_table():
    # Each is a per-project answer L6 makes and the table cannot: which scheme derives the
    # pointer, which file a finding is about, and which declaration holds the queue (RK427).
    assert VARIES == {
        "ref.mismatch": "ref_scheme",
        "id.duplicate": "role",
        "priority.shipped": "queue",
        "priority.retired": "queue",
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
    for name in ("linting.py", "schema.py"):
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
