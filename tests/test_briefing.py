"""One call to start a task, and the bound that makes it worth calling (RK29).

Two claims. The first is composition: the line, its rationale, its resolved deps, the
blocker chain, the leverage and the non-goals arrive together, because each of those was
already an answer and the cost being removed is the *joining*, not the computing.

The second is the one that can regress silently: **the output is bounded.** An answer that
fits in a tool result costs nothing to consult twice; one that does not gets replaced by
re-reading the file, which is exactly the 5k tokens this task exists to stop spending.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.briefing import CHAINS, NothingToBrief, brief, non_goals
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.document import Document
from roadkeep.schema import DESIGNED, SHIPPED, Schema

HERE = Path(__file__).resolve().parents[1]

ROADMAP = f"""# Roadmap

## Block A — The model

- {DESIGNED} **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- {DESIGNED} **RK4** (deps: RK1) **A fourth symptom** — Because of another. → §RK4

## Non-goals

- **No web UI and no server.** Files and a CLI.
- **No dates.** A marker is maturity, not a schedule.
"""

LEDGER = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK2** **A shipped symptom** — it was done.
"""

RATIONALE = """# Improvements

## Block A — The model

### §RK1 A first design

The reasoning, which names `roadkeep.toml`.
"""


def project(
    tmp_path: Path, roadmap: str = ROADMAP, improvements: str | None = RATIONALE
) -> Config:
    files = 'roadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    if improvements is not None:
        files += 'improvements = "IMPROVEMENTS.md"\n'
        (tmp_path / "IMPROVEMENTS.md").write_text(improvements, encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\n{files}', encoding="utf-8"
    )
    (tmp_path / "ROADMAP.md").write_text(roadmap, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(LEDGER, encoding="utf-8")
    return Config.discover(tmp_path)


# -- the composition ---------------------------------------------------------


def test_one_call_carries_every_answer(tmp_path):
    gathered = brief(project(tmp_path), "RK4")
    assert gathered.task.id == "RK4"
    assert str(gathered.readiness) == "blocked"
    assert [r.dep.id for r in gathered.deps] == ["RK1"]
    assert gathered.chains[0].root == "RK1"
    assert gathered.non_goals == ("No web UI and no server", "No dates")
    assert gathered.leverage.of == 1


def test_the_rationale_arrives_with_the_line(tmp_path):
    gathered = brief(project(tmp_path), "RK1")
    assert gathered.view.section is not None
    assert "The reasoning" in gathered.view.section.body
    # RK12's path list rides along: what the task touches is part of starting it.
    assert [p.path for p in gathered.view.paths] == ["roadkeep.toml"]


def test_with_no_id_it_briefs_what_pick_would_choose(tmp_path):
    gathered = brief(project(tmp_path))
    assert gathered.task.id == "RK1"
    # The reason travels: a pick nobody can check is a pick nobody trusts (RK11).
    assert gathered.picked == "lowest ready id"


def test_an_explicit_id_is_not_a_pick(tmp_path):
    assert brief(project(tmp_path), "RK4").picked == ""


def test_nothing_ready_is_refused_with_the_reason(tmp_path):
    roadmap = ROADMAP.replace("(deps: —)", "(deps: RK9)")
    with pytest.raises(NothingToBrief) as caught:
        brief(project(tmp_path, roadmap=roadmap))
    assert "every open task is blocked" in caught.value.args[0]


def test_a_shipped_task_briefs_from_the_ledger(tmp_path):
    # No readiness to compute and no deps left to state: the ledger carries neither.
    gathered = brief(project(tmp_path), "RK2")
    assert gathered.view.shipped and gathered.deps == () and gathered.chains == ()
    assert "deleted on ship" in gathered.view.section_absence


def test_the_chains_are_bounded_tighter_than_the_graphs_own_limit(tmp_path):
    deps = ", ".join(f"RK{n}" for n in range(20, 26))
    roadmap = (
        "# Roadmap\n\n## Block A — The model\n\n"
        + f"- {DESIGNED} **RK1** (deps: {deps}) **A symptom** — a reason. → §RK1\n"
        + "".join(
            f"- {DESIGNED} **RK{n}** (deps: —) **A symptom** — a reason. → §RK{n}\n"
            for n in range(20, 26)
        )
    )
    assert len(brief(project(tmp_path, roadmap=roadmap), "RK1").chains) == CHAINS


# -- the non-goals -----------------------------------------------------------


def test_the_heading_is_matched_by_prefix_because_no_two_projects_spell_it_alike():
    # This repository writes "## Non-goals"; Shio writes "## Non-goals (do NOT add as
    # tasks)". Neither is wrong, so neither is hardcoded.
    text = (
        "# Roadmap\n\n## Non-goals (do NOT add as tasks)\n\n"
        "- **No web UI.** Files and a CLI.\n"
    )
    assert non_goals(Document.parse(text, Schema())) == ("No web UI",)


def test_a_bullet_with_no_bold_lead_keeps_its_first_sentence():
    text = "# Roadmap\n\n## Non-goals\n\n- No server. It would be a second store.\n"
    assert non_goals(Document.parse(text, Schema())) == ("No server",)


def test_the_section_ends_at_the_next_heading():
    text = (
        "# Roadmap\n\n## Non-goals\n\n- **No server.** Prose.\n\n"
        "## Block A — The model\n\n- **Not a non-goal.** Prose.\n"
    )
    assert non_goals(Document.parse(text, Schema())) == ("No server",)


def test_a_project_with_no_non_goals_section_reports_none():
    assert non_goals(Document.parse("# Roadmap\n\n## Block A\n", Schema())) == ()


# -- this repository ---------------------------------------------------------


def test_the_brief_here_is_bounded(capsys):
    # The claim that pays for the command: it fits in a tool result. 4 KB is the ceiling
    # a section budget (250 words) plus a bounded dep list can reach.
    assert main(["-C", str(HERE), "brief", "RK32"]) == EXIT_OK
    out = capsys.readouterr().out
    assert len(out) < 4000, f"a brief grew to {len(out)} characters"
    assert "not      No model and no prompts" in out


def test_every_open_task_here_briefs():
    config = Config.discover(HERE)
    for entry in config.document("roadmap").entries:
        gathered = brief(config, entry.task.id)
        assert gathered.non_goals and gathered.view.section is not None


# -- the command -------------------------------------------------------------


def test_the_command_prints_the_pick_reason_when_it_picked(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("RK1  Block A  📋  ready  ROADMAP.md:5")
    assert "picked   lowest ready id" in out


def test_the_command_prints_the_chain_of_a_blocked_task(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief", "RK4"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "dep      RK1  open" in out
    assert "chain    RK4 → RK1" in out


def test_json_carries_the_whole_pack(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief", "RK4", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "RK4" and payload["readiness"] == "blocked"
    assert payload["deps_resolved"][0]["status"] == "open"
    assert payload["chains"][0]["path"] == ["RK4", "RK1"]
    assert payload["non_goals"] == ["No web UI and no server", "No dates"]
    assert payload["unblocks"] == {"count": 0, "of": 1, "transitive": []}
    assert payload["picked"] is None


def test_nothing_to_brief_exits_two(tmp_path, capsys):
    project(tmp_path, roadmap=ROADMAP.replace("(deps: —)", "(deps: RK9)"))
    assert main(["-C", str(tmp_path), "brief"]) == EXIT_USAGE
    assert "nothing to brief" in capsys.readouterr().err


def test_an_unknown_id_exits_two(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief", "RK99"]) == EXIT_USAGE
    assert "no task RK99" in capsys.readouterr().err
