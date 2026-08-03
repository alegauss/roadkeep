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


def test_a_split_id_counts_at_its_own_number_and_not_at_zero(tmp_path):
    # RK106: a `T24b` the ordering cannot read counts as zero, and zero is *first* — so
    # the split task a project deliberately numbered after T24 would be offered ahead of
    # every line below it. The letter is a tie-break, never a rank.
    config = project(
        tmp_path,
        BLOCKS + line("RK24b") + line("RK24") + line("RK9"),
        extra="[ids]\nsuffix = true\n",
    )
    choice = pick(config)
    assert choice.entry.task.id == "RK9"
    assert choice.alternatives == ("RK24", "RK24b")


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


# -- scoped to one block (RK40) ----------------------------------------------


def test_a_scoped_pick_answers_about_that_block_only(tmp_path):
    # The failure this closes: unscoped, RK2 is the answer, and reading it as "Block B is
    # finished" is a mistake non-sequential ids make easy.
    config = project(
        tmp_path, BLOCKS + line("RK2") + MORE + line("RK8", block="B") + line("RK9", block="B")
    )
    assert pick(config).entry.task.id == "RK2"
    scoped = pick(config, "B")
    assert scoped.entry.task.id == "RK8" and scoped.block == "B"
    assert "in Block B" in scoped.reason
    # Every count is about the scope too, or the answer is scoped and its numbers are not.
    assert scoped.ready == 2


def test_a_finished_block_and_a_stuck_one_read_differently(tmp_path):
    # The distinction the scope exists for: nothing open means done, and everything
    # blocked means not done — one word for both would be the bug again.
    config = project(
        tmp_path, BLOCKS + line("RK2", "RK5") + MORE
    )
    empty = pick(config, "B")
    assert not empty.found and empty.reason == "nothing is open in Block B"
    stuck = pick(config, "A")
    assert not stuck.found and "every open task in Block A is blocked" in stuck.reason
    assert (stuck.blocked, stuck.ready) == (1, 0)


def test_a_block_no_heading_declares_is_refused(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK2"))
    with pytest.raises(KeyError) as caught:
        pick(config, "Z")
    assert "no heading declares Block Z" in caught.value.args[0]
    assert "declares: A" in caught.value.args[0]
    # Nothing extra where nothing shades into it (RK216): `Z` against A and B is already
    # actionable, and a hint on every refusal is output nobody reads.
    assert "prefix" not in caught.value.args[0]


def test_a_block_that_shades_into_a_declared_one_says_so(tmp_path):
    # The read side of RK216: scoping a pick to `A` where the heading says `AJ` would
    # otherwise read as "that block is absent" for a block that is right there.
    # Both files, because a block is declared by a heading in either of them (RK37).
    config = project(
        tmp_path,
        "## Block AJ — The late block\n" + line("RK2", block="AJ"),
        changelog="# Shipped\n\n## Block AJ — The late block\n",
    )
    with pytest.raises(KeyError) as caught:
        pick(config, "A")
    assert "AJ shares a prefix with A" in caught.value.args[0]
    assert "check that the label reached this command whole" in caught.value.args[0]


def test_a_block_whose_last_task_shipped_still_resolves(tmp_path):
    # The heading may only be in the ledger by then (RK37): the answer is "finished",
    # not "no such block".
    config = project(
        tmp_path,
        BLOCKS + line("RK2"),
        changelog=f"# Shipped\n\n## Block B — Authoring\n\n- {SHIPPED} **RK8** "
        f"**A symptom** — done.\n",
    )
    choice = pick(config, "B")
    assert not choice.found and choice.reason == "nothing is open in Block B"


def test_the_scope_does_not_change_the_tiers(tmp_path):
    # In-progress still outranks a lower id — inside the block it is scoped to.
    config = project(
        tmp_path,
        BLOCKS + line("RK2") + MORE + line("RK8", block="B")
        + line("RK9", block="B", status=IN_PROGRESS),
    )
    scoped = pick(config, "B")
    assert (scoped.entry.task.id, scoped.tier) == ("RK9", Tier.STARTED)


# -- the absence of an answer is an answer -----------------------------------


def test_nothing_ready_is_reported_with_its_counts(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK1", "RK5") + line("RK2", "RK6"))
    choice = pick(config)
    assert not choice.found and choice.tier is None
    assert choice.counts == (
        "0 ready, 2 blocked, 0 blocked outside the backlog, 0 blocked on paused work"
    )


def test_an_empty_backlog_is_not_an_error(tmp_path):
    config = project(tmp_path, BLOCKS)
    assert not pick(config).found


# -- this repository ---------------------------------------------------------


def test_the_pick_here_is_the_lowest_ready_id_in_the_file():
    config = Config.discover(HERE)
    choice = pick(config)
    if not choice.found:
        # This repository's backlog is empty since RK21, and "nothing to pick" is an answer
        # rather than a failure: every tier was applied and none of them had a candidate, so
        # the counts are zero and the caller is told which. The branch below is what holds
        # the moment a line is added back, which is why it is kept rather than deleted.
        assert choice.reason == "nothing is open"
        assert (choice.ready, choice.blocked, choice.outside, choice.paused) == (0, 0, 0, 0)
        return
    assert choice.tier is Tier.LOWEST
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
    # `claimed` is null because nothing took RK7: a stalled line says whether somebody is on
    # it, and "started and stuck" is the answer when nobody is (RK152).
    assert payload["stalled"] == [{"id": "RK7", "blockers": ["RK5"], "claimed": None}]
    assert payload["ready"] == 1 and payload["blocked"] == 1


def test_nothing_to_pick_exits_zero_because_it_is_an_answer(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK1", "RK5"))
    assert main(["-C", str(tmp_path), "pick"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("nothing to pick: every open task is blocked")
    assert "0 ready, 1 blocked" in out


def test_the_command_scopes_and_says_so(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2") + MORE + line("RK8", block="B"))
    assert main(["-C", str(tmp_path), "pick", "--block", "B", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["pick"]["id"] == "RK8" and payload["scope"] == "B"
    assert payload["reason"].endswith("in Block B")


def test_an_undeclared_block_exits_two(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2"))
    assert main(["-C", str(tmp_path), "pick", "--block", "Z"]) == EXIT_USAGE
    assert "no heading declares Block Z" in capsys.readouterr().err


def test_the_command_names_what_designed_set_aside(tmp_path, capsys):
    # Printed and not folded into `backlog`: a filter that hides its own effect is how
    # "this block is finished" gets read off an answer that never looked at half of it.
    project(tmp_path, BLOCKS + line("RK4", status=IDEA) + line("RK9"))
    assert main(["-C", str(tmp_path), "pick", "--designed"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.splitlines()[0].startswith("RK9")
    assert "skipped  1 ready and still needing designing" in out


def test_the_command_says_the_pick_still_needs_designing(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK4", status=IDEA))
    assert main(["-C", str(tmp_path), "pick", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["needs_design"] and payload["undesigned"] == 0
    assert "still needs designing" in payload["reason"]


def test_a_missing_roadmap_is_a_usage_error_not_a_traceback(tmp_path, capsys):
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n', encoding="utf-8"
    )
    assert main(["-C", str(tmp_path), "pick"]) == EXIT_USAGE
    assert "ROADMAP.md" in capsys.readouterr().err


def test_an_idea_is_pickable_because_maturity_is_not_readiness(tmp_path):
    # 💭 is a maturity marker, not a gate: the deps decide, and a block whose ideas are
    # never offered is a block whose ideas are never designed (RK83).
    config = project(tmp_path, BLOCKS + line("RK4", status=IDEA))
    assert pick(config).entry.task.id == "RK4"


# -- ready and implementable are two different states (RK83) ------------------


def test_the_answer_says_when_its_choice_still_needs_designing(tmp_path):
    # The complaint RK83 records is not that `pick` chose wrongly — an idea *is* the
    # lowest ready id — but that it chose silently, and the caller found out by reading
    # the marker it had just been handed.
    config = project(tmp_path, BLOCKS + line("RK4", status=IDEA) + line("RK9"))
    choice = pick(config)
    assert choice.entry.task.id == "RK4" and choice.needs_design
    # The tier still fired and still says so: the caveat is added, never substituted.
    assert choice.reason.startswith("lowest ready id")
    assert "still needs designing" in choice.reason


def test_a_designed_pick_carries_no_caveat(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK4"))
    choice = pick(config)
    assert not choice.needs_design and "designing" not in choice.reason


def test_designed_sets_the_ideas_aside_and_takes_the_higher_id(tmp_path):
    # What "execute Block A" means: the caller wants the implementable line, and the id
    # order is not the axis that distinguishes it.
    config = project(tmp_path, BLOCKS + line("RK4", status=IDEA) + line("RK9"))
    choice = pick(config, designed=True)
    assert choice.entry.task.id == "RK9" and not choice.needs_design
    assert choice.undesigned == 1
    # `ready` is a fact about the file, so the caller's intent does not change it.
    assert choice.ready == 2 and choice.alternatives == ()


def test_a_block_of_ideas_reads_differently_from_a_blocked_one(tmp_path):
    # The third absence: not finished, not stuck — waiting on a design session, which is
    # the one of the three a caller answers by writing prose rather than by shipping.
    config = project(tmp_path, BLOCKS + line("RK4", status=IDEA))
    choice = pick(config, designed=True)
    assert not choice.found and choice.tier is None
    assert choice.reason == (
        "every ready task still needs designing, so there is nothing to implement"
    )
    assert choice.ready == 1 and choice.undesigned == 1


def test_designed_and_a_scope_compose(tmp_path):
    config = project(
        tmp_path,
        BLOCKS + line("RK2") + MORE + line("RK8", block="B", status=IDEA),
    )
    choice = pick(config, "B", designed=True)
    assert not choice.found
    assert choice.reason.startswith("every ready task in Block B still needs designing")


def test_without_the_flag_nothing_is_set_aside(tmp_path):
    # A count that moved without the caller asking would be the ranking taking the bias
    # back, which is the one thing RK83's design rules out.
    config = project(tmp_path, BLOCKS + line("RK4", status=IDEA))
    assert pick(config).undesigned == 0


def test_a_project_that_names_no_undesigned_marker_never_skips(tmp_path):
    config = project(
        tmp_path,
        BLOCKS + line("RK4", status=IDEA),
        extra='[markers]\nopen = ["📋", "💭", "⏳", "🛠"]\nundesigned = []\n\n',
    )
    choice = pick(config, designed=True)
    assert choice.entry.task.id == "RK4" and not choice.needs_design
