"""Refusing at input, and writing without disturbing the file (RK5).

Two claims carry the task and neither is about convenience:

* **A refusal costs nothing and teaches the fix.** The over-length field is named with
  its length and its limit, every violation is reported at once, and the file is
  byte-identical afterwards — a partial write to a governed file is the failure this
  tool exists to remove.
* **An accepted line changes exactly one line.** Placement is asserted against the
  whole file text rather than against the inserted line, because "inserted correctly"
  and "did not touch anything else" are the same property (L3).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.authoring import DerivedPointer, IdInUse, UnknownBlock, add, amend
from roadkeep.cli import EXIT_GATE, EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.backlog import NotOpen
from roadkeep.document import RoundTripError
from roadkeep.schema import SchemaError

ROADMAP = "docs/ROADMAP.md"

FIRST = "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1"
BODY = f"""# Roadmap

## Block A — The model

{FIRST}

## Block B — Authoring

## Non-goals

- not a task line, and never reported as one
"""


def project(
    tmp_path: Path,
    body: str = BODY,
    *,
    declares: tuple[str, ...] = (),
    files: dict[str, str] | None = None,
) -> Config:
    """A throwaway project: a config, its roadmap, and whatever else it declares."""
    lines = ['prefix = "RK"', *declares, "[files]", f'roadmap = "{ROADMAP}"']
    (tmp_path / "roadkeep.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for name, text in {ROADMAP: body, **(files or {})}.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        # newline="" so a CRLF fixture stays CRLF on disk, which is the point of one
        # of these tests and would otherwise be silently translated by the write.
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)
    return Config.discover(tmp_path)


def source(config: Config) -> str:
    with config.path("roadmap").open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def task(config: Config, **overrides: object) -> object:
    fields: dict[str, object] = {
        "block": "B",
        "symptom": "A second symptom",
        "why": "Because of another reason.",
    }
    fields.update(overrides)
    return add(config, **fields)  # type: ignore[arg-type]


# -- where the line lands ----------------------------------------------------


def test_the_line_lands_after_the_last_task_in_its_block(tmp_path):
    config = project(tmp_path)
    added = task(config, block="A")
    assert added.rendered == (
        "- 📋 **RK2** (deps: —) **A second symptom** — Because of another reason. → §RK2"
    )
    assert source(config) == BODY.replace(FIRST, f"{FIRST}\n{added.rendered}")
    assert added.lineno == 6


def test_an_empty_block_keeps_the_blank_line_before_the_next_heading(tmp_path):
    # A task glued to a heading reads as belonging to the wrong block, and the diff
    # that introduces it looks identical to the correct one.
    config = project(tmp_path)
    added = task(config)
    assert source(config) == BODY.replace(
        "## Block B — Authoring\n\n", f"## Block B — Authoring\n\n{added.rendered}\n\n"
    )


def test_a_block_heading_on_the_last_line_gains_no_trailing_blank(tmp_path):
    config = project(tmp_path, "# Roadmap\n\n## Block B — Authoring\n")
    added = task(config)
    assert source(config) == f"# Roadmap\n\n## Block B — Authoring\n\n{added.rendered}\n"


def test_a_heading_followed_immediately_by_another_is_separated(tmp_path):
    config = project(tmp_path, "## Block B — Authoring\n## Block C — Query\n")
    added = task(config)
    assert source(config) == f"## Block B — Authoring\n\n{added.rendered}\n\n## Block C — Query\n"


def test_the_file_keeps_its_line_endings(tmp_path):
    config = project(tmp_path, BODY.replace("\n", "\r\n"))
    added = task(config)
    written = source(config)
    assert f"{added.rendered}\r\n" in written
    assert "\n" not in written.replace("\r\n", "")


def test_a_block_no_heading_declares_is_refused_and_the_file_is_untouched(tmp_path):
    config = project(tmp_path)
    with pytest.raises(UnknownBlock) as raised:
        task(config, block="Z")
    # The declared blocks are named: the fix is a heading or a different label, and
    # inventing the heading would file the task where nothing looks for it.
    assert "Block Z" in str(raised.value) and "A, B" in str(raised.value)
    assert source(config) == BODY


# -- refusing before the prose exists ----------------------------------------


def test_an_over_length_why_is_refused_with_its_length_and_its_limit(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SchemaError) as raised:
        task(config, why="Because " + "of a reason " * 20 + "indeed.")
    codes = [v.code for v in raised.value.violations]
    assert "why.too-long" in codes
    assert "255 characters, limit is 200" in str(raised.value)
    assert "improvements" in str(raised.value)
    assert source(config) == BODY


def test_every_violation_is_reported_not_the_first(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SchemaError) as raised:
        task(config, symptom="Ends in a stop.", why="One sentence. And a second.")
    assert {v.code for v in raised.value.violations} == {
        "symptom.sentence",
        "why.sentences",
    }
    assert source(config) == BODY


def test_a_status_outside_the_declared_set_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SchemaError) as raised:
        task(config, status="✅")
    assert [v.code for v in raised.value.violations] == ["status.shipped"]
    assert source(config) == BODY


def test_a_file_that_already_drifted_is_not_rewritten(tmp_path):
    # The pointer is derived here, so a hand-numbered anchor is a line the schema would
    # render differently: the write is refused rather than normalizing what it may have
    # misread.
    drifted = BODY.replace("→ §RK1", "→ §2.1")
    config = project(tmp_path, drifted)
    with pytest.raises(RoundTripError) as raised:
        task(config)
    assert "RK1" in str(raised.value)
    assert source(config) == drifted


# -- the id and the pointer --------------------------------------------------


def test_the_id_is_derived_one_past_the_highest(tmp_path):
    config = project(tmp_path, BODY.replace("RK1", "RK41"))
    assert task(config).entry.task.id == "RK42"


def test_an_id_already_used_is_refused_even_where_it_is_only_prose(tmp_path):
    config = project(
        tmp_path, declares=['id_sources = ["agents.md"]'], files={"agents.md": "RK9 is retired.\n"}
    )
    with pytest.raises(IdInUse) as raised:
        task(config, task_id="RK9")
    assert "agents.md:1" in str(raised.value)
    assert source(config) == BODY


def test_the_pointer_is_derived_and_cannot_be_chosen(tmp_path):
    config = project(tmp_path)
    with pytest.raises(DerivedPointer):
        task(config, ref="4.2")
    assert task(config, ref="RK2").entry.task.ref == "RK2"


def test_an_outline_project_supplies_its_own_anchor(tmp_path):
    config = project(tmp_path, declares=['ref_scheme = "outline"'])
    assert task(config, ref="4.2").rendered.endswith("→ §4.2")
    with pytest.raises(SchemaError) as raised:
        task(config)
    assert [v.code for v in raised.value.violations] == ["ref.missing"]


def test_the_default_status_is_the_first_marker_the_project_declares(tmp_path):
    config = project(tmp_path, declares=['[markers]', 'open = ["💭", "📋"]'])
    assert task(config).entry.task.status == "💭"


# -- deps --------------------------------------------------------------------


def test_a_dep_is_read_by_the_same_code_that_reads_the_file(tmp_path):
    config = project(tmp_path)
    added = task(config, deps=["RK1", "Block A", "real design partners"])
    assert added.rendered.startswith(
        "- 📋 **RK2** (deps: RK1, Block A, real design partners)"
    )
    assert [dep.id for dep in added.entry.task.deps] == [
        "RK1",
        "Block A",
        "real design partners",
    ]


def test_a_typed_marker_is_corrected_rather_than_trusted(tmp_path):
    # The annotation is a cache of another line's status (RK8), so what the author typed
    # about RK1 loses to what RK1's own line says.
    config = project(tmp_path)
    assert task(config, deps=["RK1 ✅"]).rendered.startswith("- 📋 **RK2** (deps: RK1 📋)")


def test_a_task_cannot_depend_on_itself(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SchemaError) as raised:
        task(config, task_id="RK7", deps=["RK7"])
    assert [v.code for v in raised.value.violations] == ["deps.self"]


# -- the command -------------------------------------------------------------


def test_the_command_prints_the_line_it_wrote(tmp_path, capsys):
    config = project(tmp_path)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "B",
                "--symptom",
                "A second symptom",
                "--why",
                "Because of another reason.",
                "--dep",
                "RK1",
            ]
        )
        == EXIT_OK
    )
    printed, event = capsys.readouterr().out.splitlines()
    assert printed == "- 📋 **RK2** (deps: RK1) **A second symptom** — Because of another reason. → §RK2"
    assert printed in source(config)
    # A block that just gained a line is never empty, and the event says so anyway: one
    # shape from every mutator is what makes it parseable at all (RK38).
    assert event == "event    RK2  Block B  open"


def test_json_says_where_the_line_landed(tmp_path, capsys):
    project(tmp_path)
    assert main(
        [
            "-C",
            str(tmp_path),
            "add",
            "--block",
            "A",
            "--symptom",
            "A second symptom",
            "--why",
            "Because of another reason.",
            "--json",
        ]
    ) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "RK2"
    assert payload["file"] == ROADMAP
    assert payload["line"] == 6
    assert payload["length"] == len(payload["rendered"]) <= 320


def test_a_refusal_exits_two_and_names_every_violation(tmp_path, capsys):
    config = project(tmp_path)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "B",
                "--symptom",
                "A symptom that ends in a stop.",
                "--why",
                "No terminator",
            ]
        )
        == EXIT_USAGE
    )
    err = capsys.readouterr().err
    assert "nothing written" in err
    assert "symptom.sentence" in err and "why.no-terminator" in err
    assert source(config) == BODY


def test_a_drifted_file_exits_one_because_the_gate_says_no(tmp_path, capsys):
    project(tmp_path, BODY.replace("→ §RK1", "→ §2.1"))
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "B",
                "--symptom",
                "A second symptom",
                "--why",
                "Because of another reason.",
            ]
        )
        == EXIT_GATE
    )
    assert "will not be rewritten" in capsys.readouterr().err


# -- correcting a line that already exists (RK65) ------------------------------


def test_amend_rewrites_the_why_and_re_validates_it(tmp_path):
    # The work Shio's adoption is: 70 lines whose `why` is a paragraph, and §0.4 measured that
    # 67 of them point at a section that already makes the argument. Compression against a text
    # already written had no command until this one.
    config = project(tmp_path)
    amended = amend(config, "RK1", why="A shorter sentence.")
    assert amended.changed == ("why",)
    assert amended.rendered.endswith("— A shorter sentence. → §RK1")
    assert "A shorter sentence." in source(config)


def test_amend_refuses_a_why_over_the_limit_and_writes_nothing(tmp_path):
    config = project(tmp_path)
    before = source(config)
    with pytest.raises(SchemaError, match="why"):
        amend(config, "RK1", why="Because of " + "a long reason " * 30)
    assert source(config) == before


def test_amend_replaces_the_whole_dep_group(tmp_path):
    # Given at all, `--dep` replaces: a flag that appended could not remove the dep naming an
    # id in neither file, which is 4 of Shio's findings.
    second = "- 💭 **RK2** (deps: RK1) **A second symptom** — Because of another. → §RK2"
    config = project(tmp_path, BODY.replace(FIRST, FIRST + "\n" + second))
    amended = amend(config, "RK2", deps=["RK1"])
    assert amended.changed == ()  # already exactly that
    amended = amend(config, "RK2", deps=[])
    assert amended.changed == ("deps",) and "(deps: —)" in amended.rendered


def test_amend_writes_nothing_when_every_field_already_reads_that_way(tmp_path):
    config = project(tmp_path)
    before = source(config)
    amended = amend(config, "RK1", why=config.document("roadmap").by_id()["RK1"].task.why)
    assert amended.changed == ()
    assert source(config) == before


def test_amend_refuses_an_id_that_is_not_open(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotOpen):
        amend(config, "RK404", why="A sentence.")


def test_the_symptom_is_not_amendable():
    """It is the falsifiable claim the line *is*, so a different one is a different task — and
    the corpus agrees it is not the problem: 0 of Shio's 78 over the limit, against 70 whys."""
    import inspect

    assert "symptom" not in inspect.signature(amend).parameters
