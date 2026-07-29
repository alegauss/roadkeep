"""Picking the next task, and being able to argue with the answer (RK11).

The claim under test is not "it returns a task" — it is that **each tier is a fact and
the answer says which one fired**. So the tests are one per tier, plus the two things a
pick must never do: offer work that shipping cannot unblock (RK28), and hide a started
task it could not choose.

The priority tier is declared in `roadkeep.toml` and nowhere else. Shio's own "## Priority
queue" is a prose section explaining why reachability comes first, which is exactly the
input a tool must not rank work by (L4) — so the declaration is a list of ids and blocks,
typed by the same code that types a dep.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config, ConfigError
from roadkeep.picking import Tier, pick
from roadkeep.schema import DESIGNED, IDEA, IN_PROGRESS, SHIPPED

HERE = Path(__file__).resolve().parents[1]


def line(task_id: str, deps: str = "—", block: str = "A", status: str = DESIGNED) -> str:
    return (
        f"- {status} **{task_id}** (deps: {deps}) **A symptom for {task_id}** "
        f"— a reason. → §{task_id}\n"
    )


def project(tmp_path: Path, roadmap: str, changelog: str = "", extra: str = "") -> Config:
    # `extra` before the table: a key written after `[files]` would belong to it.
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n{extra}[files]\nroadmap = "ROADMAP.md"\n'
        'changelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(roadmap, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        changelog or "# Shipped\n\n## Block A — The model\n", encoding="utf-8"
    )
    return Config.discover(tmp_path)


BLOCKS = "## Block A — The model\n"
MORE = "\n## Block B — Authoring\n"


# -- tier 3: the rule the roadmap already states -----------------------------


def test_the_lowest_ready_id_wins_and_says_so(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK9") + line("RK2") + line("RK10"))
    choice = pick(config)
    assert choice.entry.task.id == "RK2"
    assert choice.tier is Tier.LOWEST
    # Numerically: a string sort would put RK10 before RK2 in exactly one of the two.
    assert choice.alternatives == ("RK9", "RK10")


def test_a_blocked_task_is_never_offered(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK1", "RK5") + line("RK4"))
    choice = pick(config)
    assert choice.entry.task.id == "RK4"
    assert (choice.ready, choice.blocked) == (1, 1)


def test_a_task_blocked_outside_the_backlog_is_not_offered_either(tmp_path):
    # RK28's distinction, applied where it pays: waiting will never satisfy the dep, so
    # offering RK1 as "next" sends the caller at something that cannot be finished.
    config = project(
        tmp_path, BLOCKS + line("RK1", "real design partners") + line("RK4")
    )
    choice = pick(config)
    assert choice.entry.task.id == "RK4"
    assert (choice.blocked, choice.outside) == (0, 1)


def test_a_shipped_dep_makes_a_task_ready(tmp_path):
    config = project(
        tmp_path,
        BLOCKS + line("RK9", f"RK1 {SHIPPED}"),
        changelog=f"# Shipped\n\n## Block A — The model\n\n- {SHIPPED} **RK1** "
        f"**An earlier symptom** — done.\n",
    )
    assert pick(config).entry.task.id == "RK9"


# -- tier 1: work already started --------------------------------------------


def test_work_in_progress_outranks_a_lower_id(tmp_path):
    # The tier that makes `pick` more than a sort: leaving a 🛠 line half-done is the one
    # state the marker set can express and no count can repair.
    config = project(
        tmp_path, BLOCKS + line("RK2") + line("RK7", status=IN_PROGRESS)
    )
    choice = pick(config)
    assert (choice.entry.task.id, choice.tier) == ("RK7", Tier.STARTED)
    assert "already in progress" in choice.reason


def test_a_started_task_that_is_blocked_is_reported_beside_the_answer(tmp_path):
    # It cannot be picked and it must not be hidden: this is the state a reader most
    # needs to know about, and tier 1 is precisely the tier that could not choose it.
    config = project(
        tmp_path, BLOCKS + line("RK2") + line("RK7", "RK5", status=IN_PROGRESS)
    )
    choice = pick(config)
    assert choice.entry.task.id == "RK2"
    assert choice.stalled[0].id == "RK7" and choice.stalled[0].blockers == ("RK5",)


# -- tier 2: the declared priority -------------------------------------------


def test_a_declared_id_jumps_the_queue(tmp_path):
    config = project(
        tmp_path, BLOCKS + line("RK2") + line("RK8"), extra='priority = ["RK8"]\n'
    )
    choice = pick(config)
    assert (choice.entry.task.id, choice.tier) == ("RK8", Tier.PRIORITY)
    assert "RK8" in choice.reason


def test_a_declared_block_is_applied_in_declaration_order(tmp_path):
    config = project(
        tmp_path,
        BLOCKS + line("RK2") + MORE + line("RK8", block="B") + line("RK9", block="B"),
        extra='priority = ["Block B"]\n',
    )
    choice = pick(config)
    assert (choice.entry.task.id, choice.tier) == ("RK8", Tier.PRIORITY)
    assert "Block B" in choice.reason


def test_a_declaration_naming_nothing_ready_falls_through_and_says_so(tmp_path):
    config = project(
        tmp_path,
        BLOCKS + line("RK2") + line("RK8", "RK5"),
        extra='priority = ["RK8"]\n',
    )
    choice = pick(config)
    assert (choice.entry.task.id, choice.tier) == ("RK2", Tier.LOWEST)
    assert "names nothing ready" in choice.reason


def test_a_priority_entry_that_names_neither_a_task_nor_a_block_is_refused(tmp_path):
    # Refused, not ignored: a queue the author believes is in force and is not is the
    # same failure the whole tool exists to remove, one layer down.
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\npriority = ["whatever comes up"]\n', encoding="utf-8"
    )
    with pytest.raises(ConfigError) as caught:
        Config.discover(tmp_path)
    assert "neither an id nor 'Block X'" in str(caught.value)


def test_a_priority_entry_shaped_like_an_id_but_not_one_is_refused(tmp_path):
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\npriority = ["SH341"]\n', encoding="utf-8"
    )
    with pytest.raises(ConfigError) as caught:
        Config.discover(tmp_path)
    assert "not an id of this project" in str(caught.value)


# -- the absence of an answer is an answer -----------------------------------


def test_nothing_ready_is_reported_with_its_counts(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK1", "RK5") + line("RK2", "RK6"))
    choice = pick(config)
    assert not choice.found and choice.tier is None
    assert choice.counts == "0 ready, 2 blocked, 0 blocked outside the backlog"


def test_an_empty_backlog_is_not_an_error(tmp_path):
    config = project(tmp_path, BLOCKS)
    assert not pick(config).found


# -- this repository ---------------------------------------------------------


def test_the_pick_here_is_the_lowest_ready_id_in_the_file():
    config = Config.discover(HERE)
    choice = pick(config)
    assert choice.found and choice.tier is Tier.LOWEST
    assert choice.ready > 0 and choice.entry.task.ref == choice.entry.task.id


# -- the command -------------------------------------------------------------


def test_the_command_prints_the_reason_and_the_counts(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2") + line("RK9", "RK5"))
    assert main(["-C", str(tmp_path), "pick"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.splitlines()[0].startswith("RK2  Block A  📋  ROADMAP.md:2")
    assert "because  lowest ready id" in out
    assert "1 ready, 1 blocked" in out


def test_json_carries_the_tier_and_the_stalled_work(tmp_path, capsys):
    project(
        tmp_path,
        BLOCKS + line("RK2") + line("RK7", "RK5", status=IN_PROGRESS),
        extra='priority = ["Block A"]\n',
    )
    assert main(["-C", str(tmp_path), "pick", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["pick"]["id"] == "RK2" and payload["tier"] == "declared-priority"
    assert payload["stalled"] == [{"id": "RK7", "blockers": ["RK5"]}]
    assert payload["ready"] == 1 and payload["blocked"] == 1


def test_nothing_to_pick_exits_zero_because_it_is_an_answer(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK1", "RK5"))
    assert main(["-C", str(tmp_path), "pick"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("nothing to pick: every open task is blocked")
    assert "0 ready, 1 blocked" in out


def test_a_missing_roadmap_is_a_usage_error_not_a_traceback(tmp_path, capsys):
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n', encoding="utf-8"
    )
    assert main(["-C", str(tmp_path), "pick"]) == EXIT_USAGE
    assert "ROADMAP.md" in capsys.readouterr().err


def test_an_idea_is_pickable_because_maturity_is_not_readiness(tmp_path):
    # 💭 is a maturity marker, not a gate: the deps decide, and a project that wanted
    # ideas excluded would say so in its marker set (L6).
    config = project(tmp_path, BLOCKS + line("RK4", status=IDEA))
    assert pick(config).entry.task.id == "RK4"
