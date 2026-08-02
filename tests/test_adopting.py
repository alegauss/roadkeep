"""The two doors into a project the tool does not own yet (RK18).

`init` and `adopt` are tested against opposite failure modes, because they have opposite
risks. A scaffold's risk is that it writes: the assertions here are that it writes nothing
when anything is in the way, and that what it does write is a project the *rest* of the
tool then works on — `add`, `section add`, `ship` and `lint` are run over the output,
because a scaffold proven only by its own file listing is a scaffold proven by nothing.

An estimate's risk is the opposite: that it reports a number nobody can act on. So the
claims are that it never fails (exit 0 on a file with eighty defects — an estimate with a
gate's exit code is a gate), that a prefix it guessed is *labelled* as guessed, and that
the counts move for the reason the reader would assume they moved.

And the corpus that decides §RK20: Shio's roadmap, read where it lives and never written
to, skipped on any machine but the author's.
"""

from __future__ import annotations

import json
import tomllib
from dataclasses import replace
from pathlib import Path

import pytest

from roadkeep.adopting import (
    AlreadyConfigured,
    UnreadableBlock,
    WouldOverwrite,
    adopt,
    init,
    render_config,
)
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.schema import Schema

SHIO = Path("D:/Git/viglet/shio/latest/docs/ROADMAP.md")

CONFORMING = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- 💭 **RK2** (deps: RK1) **A second symptom** — Because of another reason. → §RK2
"""

FOREIGN = """# Roadmap

## Block A — The model

- 📋 **SH1** (deps: —) **A symptom from another backlog** — Because of a reason. → §SH1
- 📋 **SH2** (deps: SH1) **A second one** — Because of another reason. → §SH2
- ✨ **SH3** (deps: —) **A marker nobody declared** — Because of a third reason. → §SH3
"""


def scaffolded(tmp_path: Path, **kwargs) -> Config:
    init(tmp_path, **kwargs)
    return Config.discover(tmp_path)


def written(tmp_path: Path) -> set[str]:
    return {
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }


# -- init writes a project the rest of the tool works on ---------------------


def test_scaffold_is_a_project_lint_passes(tmp_path: Path, capsys) -> None:
    assert main(["-C", str(tmp_path), "init"]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_OK
    assert "clean" in capsys.readouterr().out


def test_scaffold_takes_the_whole_lifecycle(tmp_path: Path, capsys, monkeypatch) -> None:
    """The claim the file listing cannot make: `add`, `section`, `ship` and `lint` all run.

    A scaffold is only correct if the block headings it wrote are the ones every write
    files under — the failure this catches is a heading that reads as prose to the parser
    and refuses every task with `UnknownBlock` on the project's first day.
    """
    where = ["-C", str(tmp_path)]
    assert main([*where, "init", "--block", "A — The model"]) == EXIT_OK
    assert (
        main(
            [
                *where,
                "add",
                "--block",
                "A",
                "--symptom",
                "The scaffold is never written to",
                "--why",
                "A file nothing writes to is a file whose shape was never tested.",
            ]
        )
        == EXIT_OK
    )
    monkeypatch.setattr("sys.stdin", _Stdin("The reasoning the line has no room for."))
    assert main([*where, "section", "add", "RK1", "--title", "The first"]) == EXIT_OK
    assert main([*where, "ship", "RK1"]) == EXIT_OK
    capsys.readouterr()
    assert main([*where, "lint"]) == EXIT_OK
    assert "clean" in capsys.readouterr().out


def test_config_reads_back_as_the_schema_it_was_rendered_from(tmp_path: Path) -> None:
    """The scaffold cannot declare a format the tool does not implement."""
    init(tmp_path)
    assert Config.load(tmp_path / "roadkeep.toml").schema == Schema()


def test_config_follows_the_schema_and_not_a_template() -> None:
    """A default that moves moves the scaffold, because the value is read off the object."""
    rendered = render_config(
        Schema(prefixes=("SH",), symptom_max=99), {"roadmap": "docs/ROADMAP.md"}
    )
    assert 'prefix = "SH"' in rendered
    assert "symptom = 99" in rendered
    assert 'roadmap = "docs/ROADMAP.md"' in rendered
    assert "changelog" not in rendered


def test_only_the_ledger_slots_a_file_lacks_are_written_out() -> None:
    # A key is emitted only when it is false (RK43, RK48): a default written out reads as a
    # decision somebody made about a slot the file carries anyway.
    paths = {"roadmap": "docs/ROADMAP.md"}
    assert "ledger" not in render_config(Schema(), paths)
    for field, key in (("ledger_marker", "marker"), ("ledger_symptom", "symptom")):
        rendered = render_config(replace(Schema(), **{field: False}), paths)
        assert "[ledger]" in rendered and f"{key} = false" in rendered
        parsed = Config.parse(tomllib.loads(rendered), root=".").schema
        assert getattr(parsed, field) is False
        # And only that one: the other slot is still the default the file has.
        other = "ledger_symptom" if field == "ledger_marker" else "ledger_marker"
        assert getattr(parsed, other) is True


def test_prefix_is_carried_into_the_first_id(tmp_path: Path, capsys) -> None:
    assert main(["-C", str(tmp_path), "init", "--prefix", "SH"]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "next-id"]) == EXIT_OK
    assert capsys.readouterr().out.strip() == "SH1"


def test_every_named_block_is_declared_in_all_three_files(tmp_path: Path) -> None:
    """The ledger and the rationale file are filed under the same headings (RK37)."""
    config = scaffolded(tmp_path, blocks=("A", "B — Authoring"))
    for role in ("roadmap", "changelog", "improvements"):
        document = config.document(role)
        assert [h.label for h in document.headings if h.label] == ["A", "B"]


def test_non_goals_heading_exists_from_the_start(tmp_path: Path) -> None:
    config = scaffolded(tmp_path)
    texts = [h.text for h in config.document("roadmap").headings]
    assert "Non-goals" in texts


# -- init refuses, and refusing means nothing was written --------------------


def test_a_configured_project_is_adopt_s_problem(tmp_path: Path) -> None:
    (tmp_path / "roadkeep.toml").write_text('prefix = "RK"\n', encoding="utf-8")
    with pytest.raises(AlreadyConfigured):
        init(tmp_path)
    assert written(tmp_path) == {"roadkeep.toml"}


def test_pyproject_that_declares_roadkeep_counts_as_configured(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.roadkeep]\nprefix = "RK"\n', encoding="utf-8"
    )
    with pytest.raises(AlreadyConfigured):
        init(tmp_path)


def test_an_ancestor_s_config_is_shadowed_not_clobbered(tmp_path: Path) -> None:
    """A subproject may declare its own format; the walk finds the nearest (RK3)."""
    (tmp_path / "roadkeep.toml").write_text('prefix = "RK"\n', encoding="utf-8")
    inner = tmp_path / "packages" / "inner"
    inner.mkdir(parents=True)
    init(inner, prefix="IN")
    assert Config.discover(inner).schema.prefix == "IN"


def test_one_existing_file_refuses_all_of_them(tmp_path: Path) -> None:
    """All-or-nothing: a half-scaffolded project reads as configured and is neither."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "CHANGELOG.md").write_text("# Mine\n", encoding="utf-8")
    with pytest.raises(WouldOverwrite):
        init(tmp_path)
    assert written(tmp_path) == {"docs/CHANGELOG.md"}


def test_a_block_no_heading_could_declare_is_refused(tmp_path: Path) -> None:
    with pytest.raises(UnreadableBlock):
        init(tmp_path, blocks=("— The model",))
    assert written(tmp_path) == set()


def test_a_prefix_the_format_cannot_carry_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        init(tmp_path, prefix="rk-1")
    assert written(tmp_path) == set()


# -- adopt measures and writes nothing ---------------------------------------


def test_a_conforming_file_costs_nothing(tmp_path: Path) -> None:
    config = scaffolded(tmp_path)
    (tmp_path / "docs" / "ROADMAP.md").write_text(CONFORMING, encoding="utf-8")
    estimate = adopt(config, tmp_path / "docs" / "ROADMAP.md")
    assert (estimate.parsed, estimate.conforming, estimate.changing) == (2, 2, 0)
    assert estimate.inferred is False
    assert estimate.non_canonical == 0


def test_the_prefix_is_inferred_only_when_nothing_declares_one(tmp_path: Path) -> None:
    """And it is labelled, because a count under a guessed prefix is a different count."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(FOREIGN, encoding="utf-8")
    guessed = adopt(Config.default(tmp_path), target)
    assert (guessed.prefix, guessed.inferred) == ("SH", True)
    assert ("SH", 2) in guessed.prefixes

    declared = adopt(Config.default(tmp_path), target, prefix="RK")
    assert (declared.prefix, declared.inferred) == ("RK", False)
    assert dict(declared.codes)["id.format"] == 2


def test_a_configured_project_never_guesses(tmp_path: Path) -> None:
    config = scaffolded(tmp_path)
    target = tmp_path / "OTHER.md"
    target.write_text(FOREIGN, encoding="utf-8")
    estimate = adopt(config, target)
    assert (estimate.prefix, estimate.inferred) == ("RK", False)


def test_an_undeclared_marker_is_named_as_the_markers_delta(tmp_path: Path) -> None:
    target = tmp_path / "ROADMAP.md"
    target.write_text(FOREIGN, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target)
    assert estimate.undeclared == (("✨", 1),)
    # The line is unread rather than invalid, so it counts as changing and not as parsed.
    assert estimate.parsed == 2
    assert estimate.changing == 1
    assert [count for _, count in estimate.rejects] == [1]


def test_a_length_is_reported_as_a_distance_and_not_a_verdict(tmp_path: Path) -> None:
    """`longest` beside `over`: how many lines change, and whether the limit is close."""
    target = tmp_path / "ROADMAP.md"
    why = "Because of a reason that runs on. " * 12
    target.write_text(
        f"# Roadmap\n\n## Block A\n\n- 📋 **RK1** (deps: —) **A symptom** — {why}\n",
        encoding="utf-8",
    )
    estimate = adopt(Config.default(tmp_path), target)
    measures = {m.field: m for m in estimate.measures}
    assert measures["symptom"].over == 0
    assert measures["why"].over == 1
    assert measures["why"].longest > measures["why"].limit
    assert measures["line"].limit == 320


def test_the_ledger_is_measured_as_the_ledger(tmp_path: Path) -> None:
    """✅ with no deps is a defect in a roadmap and the format of a changelog (L6)."""
    target = tmp_path / "CHANGELOG.md"
    target.write_text(
        "# Shipped\n\n## Block A\n\n- ✅ **RK1** **A symptom** — because it was done.\n",
        encoding="utf-8",
    )
    assert adopt(Config.default(tmp_path), target, ledger=True).conforming == 1
    assert adopt(Config.default(tmp_path), target).conforming == 0


def test_the_ref_scheme_is_an_override_and_never_a_guess(tmp_path: Path) -> None:
    """Two real questions: adopt the tool, or adopt it and renumber the outline (RK27)."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(
        "# Roadmap\n\n## Block A\n\n"
        "- 📋 **RK1** (deps: —) **A symptom** — Because of a reason. → §2.3\n",
        encoding="utf-8",
    )
    assert adopt(Config.default(tmp_path), target).conforming == 0
    assert adopt(Config.default(tmp_path), target, ref_scheme="outline").conforming == 1


def test_adopt_writes_nothing(tmp_path: Path) -> None:
    target = tmp_path / "ROADMAP.md"
    target.write_text(FOREIGN, encoding="utf-8")
    before = target.read_bytes()
    adopt(Config.default(tmp_path), target)
    assert target.read_bytes() == before
    assert written(tmp_path) == {"ROADMAP.md"}


# -- the command surface -----------------------------------------------------


def test_an_estimate_is_not_a_gate(tmp_path: Path, capsys) -> None:
    """Exit 0 on a file with nothing but defects: an estimate with a gate's exit code
    is a gate, and the point is to take it *before* the commitment."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(FOREIGN, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target)]) == EXIT_OK
    out = capsys.readouterr().out
    assert "inferred from the ids" in out
    assert "declared by nothing in [markers]" in out


def test_a_file_that_is_not_there_is_a_usage_error(tmp_path: Path, capsys) -> None:
    assert main(["-C", str(tmp_path), "adopt", str(tmp_path / "nope.md")]) == EXIT_USAGE
    assert capsys.readouterr().err


def test_json_carries_every_number_the_report_prints(tmp_path: Path, capsys) -> None:
    target = tmp_path / "ROADMAP.md"
    target.write_text(FOREIGN, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target), "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["prefix"] == "SH"
    assert payload["inferred"] is True
    assert payload["parsed"] == 2
    assert payload["undeclared"] == [{"marker": "✨", "count": 1}]
    assert {m["field"] for m in payload["measures"]} == {"symptom", "why", "line"}


def test_init_json_names_what_it_created(tmp_path: Path, capsys) -> None:
    assert main(["-C", str(tmp_path), "init", "--json", "--block", "A"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["blocks"] == ["A"]
    assert len(payload["created"]) == 4
    assert all(Path(name).is_file() for name in payload["created"])


def test_init_refusal_is_a_usage_error(tmp_path: Path, capsys) -> None:
    (tmp_path / "roadkeep.toml").write_text('prefix = "RK"\n', encoding="utf-8")
    assert main(["-C", str(tmp_path), "init"]) == EXIT_USAGE
    assert "adopt" in capsys.readouterr().err


# -- the corpus that decides §RK20 -------------------------------------------


@pytest.mark.skipif(not SHIO.is_file(), reason="Shio is not checked out here")
def test_shio_is_readable_before_it_is_conforming() -> None:
    """The measurement RK20 turns on: the lines parse, and it is the *prose* that does not.

    If a meaningful fraction could not be read at all, the grammar would be wrong. What
    this asserts is the opposite finding — under Shio's own outline scheme the lines round
    -trip, so adoption is an editing cost and not a reformatting one.
    """
    estimate = adopt(Config.default(SHIO.parent), SHIO, ref_scheme="outline")
    assert estimate.prefix == "SH"
    assert estimate.non_canonical == 0
    assert estimate.parsed > 0  # the weakest bound that still fails on an empty read
    codes = dict(estimate.codes)
    if not codes:
        pytest.skip(f"{SHIO} now conforms: there is no adoption cost left to estimate")
    # No count of the offences, slack or otherwise: this is another repository's live
    # backlog, it shrinks every time Shio ships, and a bound set at today's reading is a
    # count whatever the comment beside it claims (RK102) — which is how the one in
    # `test_document.py` was crossed. The finding is which *kind* of code appears: none
    # about the id, the deps, the marker or the block, so adoption is an editing cost.
    assert [c for c in codes if not c.startswith(("why.", "line.", "ref."))] == []


class _Stdin:
    """A stdin the section writer can read prose from, with nothing to reconfigure."""

    def __init__(self, text: str) -> None:
        self._text = text

    def read(self) -> str:
        return self._text


def test_the_estimate_is_taken_under_the_numbers_the_gate_applies(tmp_path: Path) -> None:
    """RK76: `adopt` was the one caller reaching past `Config.schema_for(role)`.

    So `[limits.changelog]` and `[rules.changelog]` — the two tables a project writes
    *because* its ledger is history — were invisible to the estimate, and the number it
    printed measured a commitment nobody was being asked to make. Measured on Dumont:
    34 `why.no-terminator` from `adopt` against none from `lint`, on one file.
    """
    (tmp_path / "roadkeep.toml").write_text(
        '[files]\nchangelog = "CHANGELOG.md"\n\n'
        "[limits.changelog]\nwhy = 4000\nline = 4200\n\n"
        "[rules.changelog]\none_sentence = false\nterminator = false\n",
        encoding="utf-8",
    )
    history = "Two sentences. And no terminating stop, at " + "x" * 400
    target = tmp_path / "CHANGELOG.md"
    target.write_text(
        f"# Shipped\n\n## Block A\n\n- ✅ **RK1** **A symptom** — {history}\n",
        encoding="utf-8",
    )
    assert adopt(Config.discover(tmp_path), target, ledger=True).conforming == 1

    # And it is those two tables doing it, not the ledger shape: the same file, the same
    # `--ledger`, with the role's own numbers withdrawn, is the estimate as it read before.
    (tmp_path / "roadkeep.toml").write_text(
        '[files]\nchangelog = "CHANGELOG.md"\n', encoding="utf-8"
    )
    bare = adopt(Config.discover(tmp_path), target, ledger=True)
    assert bare.conforming == 0
    assert {code for code, _ in bare.codes} >= {
        "why.too-long",
        "why.sentences",
        "why.no-terminator",
    }
