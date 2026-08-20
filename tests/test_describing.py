"""The config's own shape, answered by the parser that enforces it (RK1270).

Two properties carry this file and the first is the one that lasts. The **census** is total:
every `_reject_unknown` call site in `config.py` is a table, so a table added tomorrow is a red
here until `describing.TABLES` names it — and `WHERE` is held total against those sets the same
way, because a key nobody accounted for reads exactly like a key with no default.

The second is that nothing is restated. The sentence printed beside a table is the one already
above its frozenset, harvested from the source; a copy in `describing.py` would be the one that
goes stale the first time somebody edits the real one, which is the failure this task is an
instance of one file out.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from roadkeep import config as module, describing
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config

HERE = Path(__file__).resolve().parent.parent
SOURCE = Path(module.__file__ or "")

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"

BACKLOG = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason.
"""

LEDGER = """# Shipped

## Block A — The model
"""


def project(tmp_path: Path, *, extra: str = "") -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n' + extra,
        encoding="utf-8",
    )
    for name, body in ((ROADMAP, BACKLOG), (CHANGELOG, LEDGER)):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


# -- the census, which is the deliverable -------------------------------------


def _guarded() -> tuple[frozenset[str], ...]:
    """Every key set `_reject_unknown` is called with, read out of `config.py`.

    The **call sites** and not a list somebody keeps: that function is the one gate on what
    this file may say, so its arguments are the population, and reading them here is what
    makes `TABLES` a projection rather than a second opinion. Two shapes reach it — a
    frozenset by name, and `frozenset(<a dict>)` where the set is a mapping's keys — because
    a table whose keys map to schema attributes is declared as that mapping.
    """
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    out: list[frozenset[str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "_reject_unknown":
            continue
        named = ast.unparse(node.args[1])
        inner = named.removeprefix("frozenset(").removesuffix(")")
        assert inner.isidentifier(), named
        out.append(frozenset(getattr(module, inner)))
    return tuple(out)


def test_every_table_the_parser_guards_is_one_this_read_names():
    """The closure. `_reject_unknown` is the one gate on what `roadkeep.toml` may say, so its
    arguments are the whole population — and a table added to the parser without a row here
    would be a key the file accepts and the read denies."""
    published = {frozenset(keys) for keys in describing.TABLES.values()}
    guarded = set(_guarded())
    assert guarded, "the scan stopped finding call sites, so it asserts nothing"
    assert guarded <= published, {
        "the parser guards it, nothing publishes it": [sorted(one) for one in guarded - published]
    }


def test_every_key_says_where_its_default_lives():
    """`WHERE` is the one thing this module writes down, so it is held total both ways: a key
    with no row reads exactly like a key with no default, and a row for a key no table carries
    is a default nothing can ever print."""
    declared = {
        (table, key) for table, keys in describing.TABLES.items() for key in keys
    }
    assert declared == set(describing.WHERE), {
        "a key with no row": sorted(declared - set(describing.WHERE)),
        "a row with no key": sorted(set(describing.WHERE) - declared),
    }


# -- the sentence, harvested and never restated -------------------------------


def test_the_note_is_the_one_the_source_already_carries():
    found = describing.notes()
    assert "`[ids]` — the shape of an id" in found["_IDS_KEYS"]
    # And it is not written twice: a copy here is the one that goes stale when the real one
    # is edited, which is this task's own finding pointed at itself.
    written = Path(describing.__file__ or "").read_text(encoding="utf-8")
    assert "the shape of an id" not in written


def test_a_build_with_no_source_answers_the_shape_and_not_the_prose(tmp_path):
    # An absence and never an invention: a zipapp or a stripped install still says which keys
    # exist, which is the half a reader cannot reconstruct.
    assert describing.notes(tmp_path / "nothing.py") == {}


# -- what this project declared -----------------------------------------------


def test_a_key_declared_at_the_default_is_still_declared(tmp_path):
    """The whole reason this is read back off the *file*: a config carries the effective value,
    where a limit left out and a limit declared at the default are the same number and a
    different fact about the project."""
    config = project(tmp_path, extra="[limits]\nwhy = 200\n")
    found = describing.shape(config, "limits")
    declared = {one.name: one.declared for one in found.keys}
    assert declared["why"] is True
    assert declared["symptom"] is False
    # And the default printed is this build's, not the project's declaration.
    assert next(one for one in found.keys if one.name == "why").default == "200"


def test_a_tree_with_no_config_is_answered_and_not_refused(tmp_path):
    # The caller who most needs the list is the one who has not written the file yet.
    found = describing.shape(Config.discover(tmp_path))
    assert found.source is None
    assert found.keys and not any(one.declared for one in found.keys)


def test_the_answer_names_the_build_that_gave_it(tmp_path):
    """`ConfigError`'s skew clause, reachable: a key nothing declares is a typo and a key this
    build predates is an upgrade, and the file cannot tell them apart — so the version is what
    lets a reader conclude the second."""
    from roadkeep import __version__

    assert describing.shape(project(tmp_path)).version == __version__


# -- the verb ------------------------------------------------------------------


def test_the_verb_prints_every_table_and_narrows_to_one(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "config"]) == EXIT_OK
    every = capsys.readouterr().out
    assert "[limits]" in every and "[markers]" in every and "[top level]" in every

    assert main(["-C", str(tmp_path), "config", "--table", "limits"]) == EXIT_OK
    one = capsys.readouterr().out
    assert "[limits]" in one and "[markers]" not in one


def test_the_top_level_is_askable_by_the_name_it_has(tmp_path, capsys):
    # Its name *is* the empty string, so a `--table` defaulting to `""` would make the one
    # table a reader starts from the one they cannot ask for.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "config", "--table", ""]) == EXIT_OK
    said = capsys.readouterr().out
    assert "[top level]" in said and "[limits]" not in said


def test_a_table_this_build_does_not_have_is_refused(tmp_path, capsys):
    # Refused rather than answered empty, that answer being read as evidence — and the refusal
    # names every table, because the caller is choosing one.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "config", "--table", "limit"]) != EXIT_OK
    said = capsys.readouterr().err
    assert "no table 'limit'" in said and "'limits'" in said


def test_the_payload_is_what_a_completion_list_reads(tmp_path, capsys):
    """RK1271 is what this shape is for: one row per key, each carrying the address it would be
    typed at, so an editor offers them without compiling a second copy."""
    project(tmp_path, extra="[limits]\nwhy = 90\n")
    assert main(["-C", str(tmp_path), "config", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    rows = {one["address"]: one for one in payload["keys"]}
    assert rows["limits.why"]["declared"] is True
    assert rows["limits.why"]["type"] == "integer"
    assert rows["prefix"]["address"] == "prefix"
    assert payload["version"] and payload["source"] == "roadkeep.toml"


def test_the_read_writes_nothing(tmp_path):
    config = project(tmp_path, extra="[limits]\nwhy = 90\n")
    before = {
        name: (config.root / name).read_text(encoding="utf-8")
        for name in ("roadkeep.toml", ROADMAP, CHANGELOG)
    }
    assert main(["-C", str(tmp_path), "config"]) == EXIT_OK
    assert {
        name: (config.root / name).read_text(encoding="utf-8") for name in before
    } == before


# -- and it answers about this repository, which is the fixture ----------------


def test_this_project_reads_its_own_configuration_back(tmp_path):
    found = describing.shape(Config.discover(HERE))
    rows = {one.address: one for one in found.keys}
    assert rows["files.decisions"].declared is True
    assert rows["files.strategy"].declared is False
    assert rows["limits.symptom"].declared is True
    # `part` is one this repository leaves at the default, which is the row a listing exists
    # to show: accepted, unused, and named.
    assert rows["limits.part"].declared is False
    assert rows["limits.part"].default


# -- the value beside the default (RK1278) ------------------------------------


def test_a_key_the_project_set_says_what_it_says_now(tmp_path):
    """The defect. `default 120, declared here` is two true statements arranged to read as one
    false one, and the reader most likely to meet it is the one hovering the key they are
    about to change — the moment the value matters and the default does not."""
    config = project(tmp_path, extra="[limits]\nsymptom = 90\n")
    rows = {one.address: one for one in describing.shape(config, "limits").keys}

    assert rows["limits.symptom"].default == "120", "this build's, unchanged"
    assert rows["limits.symptom"].set == "90"
    # An absence and not an emptiness: a key nobody declared has no declared value, which is
    # a different fact from one declared as zero.
    assert rows["limits.why"].set is None and rows["limits.why"].declared is False


def test_the_declared_value_is_rendered_by_the_same_writer_as_the_default(tmp_path):
    # Never resolved into what the schema makes of it, which would be this module re-deciding
    # what the parser decided: what TOML hands back is a scalar, a string or a list.
    config = project(
        tmp_path,
        extra='[headings]\nword = "Fase"\npermanent = true\n[markers]\nopen = ["A", "B"]\n',
    )
    rows = {one.address: one for one in describing.shape(config).keys}

    assert rows["headings.word"].set == '"Fase"'
    assert rows["headings.permanent"].set == "true"
    assert rows["markers.open"].set == '["A", "B"]'


def test_a_table_carries_no_value_of_its_own(tmp_path):
    # What a table *is* is the keys under it, so a rendered subtree there would be the whole
    # of `[limits]` printed as though somebody had declared it as a value.
    config = project(tmp_path, extra="[limits]\nsymptom = 90\n")
    rows = {one.address: one for one in describing.shape(config, "").keys}

    assert rows["limits"].declared is True
    assert rows["limits"].set is None


def test_a_table_declared_per_role_reports_what_that_role_set(tmp_path):
    # `[limits.changelog]` is the `limits` this build published, so the row keyed by the
    # placeholder is where the value it carries lands.
    config = project(tmp_path, extra="[limits.changelog]\nwhy = 150\n")
    rows = {one.address: one for one in describing.shape(config, "limits").keys}

    assert rows["limits.why"].set == "150"


def test_the_listing_prints_the_value_where_there_is_one(tmp_path, capsys):
    project(tmp_path, extra="[limits]\nsymptom = 90\n")
    assert main(["-C", str(tmp_path), "config", "--table", "limits"]) == EXIT_OK
    said = capsys.readouterr().out

    assert "default 120  (declared 90)" in said
    # And the row for a key nobody declared says so with nothing after it.
    assert "(—)" in said


def test_a_table_written_at_several_addresses_reports_how_many(tmp_path):
    """RK1282. A placeholder table is declared once per something the project names, and the
    shape publishes one address — so the value it reported was one of however many the file
    carried, chosen by whichever came last, with nothing saying there were others. Precise and
    wrong is worse than thin and true: a number a reader can act on and should not."""
    config = project(
        tmp_path,
        extra='[budgets]\n"one.md" = { lines = 10 }\n"two.md" = { lines = 20 }\n',
    )
    rows = {one.address: one for one in describing.shape(config, "budgets.<path>").keys}

    assert rows["budgets.<path>.lines"].declared is True
    assert rows["budgets.<path>.lines"].at == 2
    # Neither of the two, which is the whole repair: which applies is `budget --file`'s.
    assert rows["budgets.<path>.lines"].set is None


def test_one_address_still_says_what_it_says(tmp_path):
    # The count is the answer only where there is more than one, so the ordinary case keeps
    # the value RK1278 added.
    config = project(tmp_path, extra='[budgets]\n"one.md" = { lines = 10 }\n')
    rows = {one.address: one for one in describing.shape(config, "budgets.<path>").keys}

    assert rows["budgets.<path>.lines"].at == 1
    assert rows["budgets.<path>.lines"].set == "10"


def test_the_listing_says_the_count_where_it_cannot_say_the_value(tmp_path, capsys):
    project(
        tmp_path,
        extra='[budgets]\n"one.md" = { lines = 10 }\n"two.md" = { lines = 20 }\n',
    )
    assert main(["-C", str(tmp_path), "config", "--table", "budgets.<path>"]) == EXIT_OK
    said = capsys.readouterr().out

    assert "declared at 2 addresses" in said
    assert "declared 20" not in said, "the last one is not the answer"


def test_this_project_budgets_two_files_and_the_row_says_so(tmp_path):
    # The measurement the task was filed from, held against the live tree: two budgets, and a
    # row that used to print the second one's numbers as though they were the project's.
    rows = {one.address: one for one in describing.shape(Config.discover(HERE)).keys}
    assert rows["budgets.<path>.lines"].at == 2
    assert rows["budgets.<path>.lines"].set is None
