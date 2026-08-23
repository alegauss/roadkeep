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

from roadkeep.backlog import Stage
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config, ConfigError
from roadkeep.picking import Tier, pick
from roadkeep.kernel.schema import DESIGNED, IDEA, IN_PROGRESS, SHIPPED

HERE = Path(__file__).resolve().parents[1]


def line(
    task_id: str,
    deps: str = "—",
    block: str = "A",
    status: str = DESIGNED,
    requires: str = "",
) -> str:
    group = f" (requires: {requires})" if requires else ""
    return (
        f"- {status} **{task_id}** (deps: {deps}){group} **A symptom for {task_id}** "
        f"— a reason. → §{task_id}\n"
    )


#: A project that declares the vocabulary the requirement tests quote from (RK1297). Written
#: out rather than defaulted, because the axis being opt-in is half of what is under test.
DECLARED = '[requirements]\ndeclared = ["dualsense", "ps5"]\n\n'


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


# -- and what it is waiting on, where it names nothing ready (RK1304) ---------


def test_the_fall_through_names_the_task_that_would_release_the_priority(tmp_path):
    """Observed over four consecutive sessions on a port whose roadmap declares Priority as
    two blocks, every line in both blocked. The fall-through is true and stops one step short:
    the block held one line, blocked on a single task elsewhere, and nothing in the answer said
    which. The caller who wanted the priority opened the roadmap, read the queue, found the
    block's lines, read their deps and looked each one up — the reading this verb replaces,
    done by hand, at the moment it was least obvious.
    """
    config = project(
        tmp_path,
        BLOCKS + line("RK2") + MORE + line("RK8", "RK2", block="B"),
        extra='priority = ["Block B"]\n',
    )
    choice = pick(config)
    # The pick is unchanged: this is beside it, because it may still be the right call.
    assert (choice.entry.task.id, choice.tier) == ("RK2", Tier.LOWEST)
    assert "names nothing ready" in choice.reason
    (waiting,) = choice.waiting
    assert (waiting.token, waiting.lines) == ("Block B", 1)
    assert (waiting.releases, waiting.of) == (("RK2",), 1)


def test_the_queue_that_was_answered_is_not_also_reported_as_waiting(tmp_path):
    # The queue named something ready and the pick came from it, so a row about what some
    # other token is blocked on is a cost quoted against a question nobody asked.
    config = project(
        tmp_path,
        BLOCKS + line("RK2") + MORE + line("RK8", block="B"),
        extra='priority = ["Block B"]\n',
    )
    choice = pick(config)
    assert choice.tier is Tier.PRIORITY and choice.waiting == ()


def test_a_priority_blocked_outside_the_backlog_names_no_id_it_cannot(tmp_path):
    # Nothing this tool could offer would release it, and an id it cannot name is worse than
    # the count alone — the same rule that keeps `block drop` off a paused heading (RK16).
    config = project(
        tmp_path,
        BLOCKS + line("RK2") + MORE + line("RK8", "real design partners", block="B"),
        extra='priority = ["Block B"]\n',
    )
    (waiting,) = pick(config).waiting
    assert waiting.releases == () and waiting.of == 0


def test_the_row_says_which_task_and_the_payload_carries_it(tmp_path, capsys):
    project(
        tmp_path,
        BLOCKS + line("RK2") + MORE + line("RK8", "RK2", block="B"),
        extra='priority = ["Block B"]\n',
    )
    assert main(["-C", str(tmp_path), "pick"]) == EXIT_OK
    assert "  waiting  Block B — 1 line, blocked; RK2 would release it" in (
        capsys.readouterr().out
    )
    assert main(["-C", str(tmp_path), "pick", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["waiting"] == [
        {"token": "Block B", "lines": 1, "releases": ["RK2"], "of": 1}
    ]


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
    # Declared here and filed under in neither file, so the state is `empty` and not
    # `finished` (RK429) — this fixture is a heading opened before its lines, which is
    # what "nothing is open in Block B" used to say about a shipped block as well.
    assert not empty.found and empty.stage is Stage.EMPTY
    # The wording itself is `Standing.sentence`'s, and asserted verbatim once, where it is
    # written: a sentence pinned in three test files is a reword that fails in three.
    assert empty.reason.startswith("Block B is empty")
    stuck = pick(config, "A")
    assert not stuck.found and "every open task in Block A is blocked" in stuck.reason
    assert (stuck.blocked, stuck.ready) == (1, 0)
    # A block with open lines is neither of the two absences, and the state says so even
    # though the sentence above is about the deps rather than about the block.
    assert stuck.stage is Stage.LIVE


def test_a_block_no_heading_declares_is_refused(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK2"))
    with pytest.raises(KeyError) as caught:
        pick(config, "Z")
    assert "no heading declares Block Z" in caught.value.args[0]
    # And not the labels that are declared (RK296): the caller typed a block rather than
    # choosing from a menu, and a read scoped to a block that is not there says only that.
    assert "declares: A" not in caught.value.args[0]
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
    assert not choice.found and choice.stage is Stage.FINISHED
    # The count is the evidence for the word: `finished` is a claim about the ledger, and
    # an answer that makes it without saying how many entries it read is one the caller
    # has to check with the grep this command replaces (RK429).
    assert choice.reason.startswith("Block B is finished") and "1 filed" in choice.reason
    assert (choice.standing.recorded, choice.standing.open) == (1, 0)


def test_the_three_ways_a_block_can_answer_nothing_are_three_sentences(tmp_path):
    """Finished, empty and unknown — the whole of RK429 in one comparison.

    They were one sentence, and two of the three readers of it were being sent to grep
    the ledger: a block that is done and a block letter nobody ever used are opposite
    facts, and "nothing is open in Block B" is what both of them said.
    """
    config = project(
        tmp_path,
        BLOCKS + line("RK2") + MORE + "\n## Block C — Query\n",
        changelog=f"# Shipped\n\n## Block B — Authoring\n\n- {SHIPPED} **RK8** "
        f"**A symptom** — done.\n",
    )
    finished, empty = pick(config, "B"), pick(config, "C")
    assert (finished.stage, empty.stage) == (Stage.FINISHED, Stage.EMPTY)
    assert finished.reason != empty.reason
    with pytest.raises(KeyError) as caught:
        pick(config, "Z")
    # The third stays a refusal and keeps its own wording: it is the only one of the
    # three that is a typo, and an exit code is the part of that answer a loop reads.
    assert "no heading declares Block Z" in caught.value.args[0]


def test_the_state_of_the_scope_is_carried_even_when_a_line_was_picked(tmp_path):
    # So that a caller driving a block to completion never needs a second command to ask
    # what the block it is working through currently is.
    config = project(tmp_path, BLOCKS + line("RK2") + MORE + line("RK8", block="B"))
    choice = pick(config, "B")
    assert choice.found and choice.stage is Stage.LIVE
    assert choice.standing.open == 1 and choice.standing.label == "B"


def test_an_unscoped_pick_has_no_block_to_have_a_state(tmp_path):
    # There is no label, so there is nothing for `finished` or `empty` to be about, and
    # the sentence that was always the whole truth here is left exactly as it was.
    config = project(tmp_path, BLOCKS)
    choice = pick(config)
    assert choice.standing is None and choice.stage is None
    assert choice.reason == "nothing is open"


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


def test_the_pick_here_is_the_lowest_ready_id_in_the_file(governed):
    config = Config.discover(governed)
    choice = pick(config)
    if not choice.found:
        # This repository's backlog is empty since RK21, and "nothing to pick" is an answer
        # rather than a failure: every tier was applied and none of them had a candidate, so
        # the counts are zero and the caller is told which. The branch below is what holds
        # the moment a line is added back, which is why it is kept rather than deleted.
        assert choice.reason == "nothing is open"
        assert (choice.ready, choice.blocked, choice.outside, choice.paused) == (0, 0, 0, 0)
        return
    # Tier.STARTED while a line is claimed, and that is the workflow rather than a defect:
    # one task per commit means the 🛠 window is the window work happens in, so asserting
    # LOWEST alone would redden every run made mid-task (RK358). What survives a claim is
    # that this backlog is pickable and that the chosen line points at its own section.
    assert choice.tier in (Tier.LOWEST, Tier.STARTED)
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


def test_the_scoped_payload_carries_the_state_and_the_wire_value_is_the_word(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2") + MORE)
    assert main(["-C", str(tmp_path), "pick", "--block", "B", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["pick"] is None and payload["scope"] == "B"
    # The word and not the enum's repr: it is what a loop matches on, so it is asserted.
    assert payload["standing"]["state"] == "empty"
    assert payload["standing"]["sentence"] == payload["reason"]


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


# -- ready and executable-here are two different states (RK1297) --------------


def test_the_same_line_comes_back_until_the_file_or_the_caller_changes(tmp_path):
    """The defect, as the shape it actually had: five calls, five identical answers.

    Every tier is a pure function of the file, so a caller that cannot finish the line it
    was handed has nothing to do about it — and the roadmap is right, which is why no
    `ship`, `defer` or `resume` was ever the answer.
    """
    config = project(tmp_path, BLOCKS + line("RK4"), extra=DECLARED)
    assert {pick(config).entry.task.id for _ in range(5)} == {"RK4"}


def test_a_requirement_this_caller_lacks_is_never_offered(tmp_path):
    config = project(
        tmp_path,
        BLOCKS + line("RK4", requires="dualsense") + line("RK9"),
        extra=DECLARED,
    )
    choice = pick(config)
    assert choice.entry.task.id == "RK9"
    # `ready` is a fact about the file, so the caller's world does not change it — the
    # same rule `--designed` obeys one axis over.
    assert choice.ready == 2
    assert [(one.id, one.missing) for one in choice.lacking] == [("RK4", ("dualsense",))]


def test_the_caller_that_has_it_gets_the_line_the_other_could_not(tmp_path):
    """The half that makes this an axis and not a second `defer`: the pause is symmetric
    and this is not, so the person at the desk is offered what the agent was not."""
    config = project(
        tmp_path,
        BLOCKS + line("RK4", requires="dualsense") + line("RK9"),
        extra=DECLARED,
    )
    choice = pick(config, available=["dualsense"])
    assert choice.entry.task.id == "RK4"
    assert choice.lacking == ()


def test_one_requirement_of_two_is_still_missing(tmp_path):
    config = project(
        tmp_path, BLOCKS + line("RK4", requires="dualsense, ps5"), extra=DECLARED
    )
    choice = pick(config, available=["ps5"])
    assert not choice.found
    # Only what is actually absent: telling the caller to find a PS5 it just declared is
    # the answer that gets ignored the second time it is printed.
    assert choice.lacking[0].missing == ("dualsense",)


def test_a_started_line_this_caller_cannot_continue_is_stepped_around(tmp_path):
    """Before the tiers and not after, for the claim's reason: tier 1 prefers a 🛠 line,
    which is exactly the line somebody started at the desk and this caller cannot finish."""
    config = project(
        tmp_path,
        BLOCKS + line("RK4", status=IN_PROGRESS, requires="ps5") + line("RK9"),
        extra=DECLARED,
    )
    choice = pick(config)
    assert choice.entry.task.id == "RK9"
    assert choice.tier is Tier.LOWEST


def test_a_backlog_of_hardware_work_says_so_and_names_what_is_missing(tmp_path):
    """The fifth absence, and the only one whose remedy is a person (RK1297)."""
    config = project(
        tmp_path,
        BLOCKS + line("RK4", requires="dualsense") + line("RK9", requires="ps5"),
        extra=DECLARED,
    )
    choice = pick(config)
    assert not choice.found and choice.tier is None
    assert choice.reason.startswith(
        "every ready task needs something this caller does not have: dualsense, ps5"
    )
    assert choice.ready == 2


def test_a_line_that_requires_nothing_is_unaffected(tmp_path):
    # The axis is opt-in at every level: a project declaring a vocabulary does not make
    # every line subject to it, and a caller declaring nothing is the ordinary case.
    config = project(tmp_path, BLOCKS + line("RK4"), extra=DECLARED)
    choice = pick(config)
    assert choice.entry.task.id == "RK4" and choice.lacking == ()


def test_the_command_names_the_lines_it_set_aside(tmp_path, capsys):
    project(
        tmp_path, BLOCKS + line("RK4", requires="ps5") + line("RK9"), extra=DECLARED
    )
    assert main(["-C", str(tmp_path), "pick"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.splitlines()[0].startswith("RK9")
    # Named, never counted: the id is what gets handed to whoever has the thing.
    assert "absent   RK4 is ready and requires ps5" in out


def test_the_payload_carries_the_ids_and_what_each_would_take(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK4", requires="ps5"), extra=DECLARED)
    assert main(["-C", str(tmp_path), "pick", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["pick"] is None
    assert payload["lacking"] == [{"id": "RK4", "missing": ["ps5"]}]


def test_the_flag_declares_what_the_caller_has(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK4", requires="ps5"), extra=DECLARED)
    assert main(["-C", str(tmp_path), "pick", "--have", "ps5", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["pick"]["id"] == "RK4" and payload["lacking"] == []


def test_a_claim_never_takes_a_line_this_caller_cannot_finish(tmp_path):
    """`take` answers and writes in one transaction, so the filter has to hold inside the
    lock: a marker moved onto hardware work nobody here can do is the stalled line the
    next five calls report."""
    config = project(tmp_path, BLOCKS + line("RK4", requires="ps5"), extra=DECLARED)
    from roadkeep.picking import take

    taken = take(config)
    assert not taken.taken
    assert (tmp_path / "ROADMAP.md").read_text(encoding="utf-8").count(IN_PROGRESS) == 0


# -- the line the picker offers is a line the claim can take (RK1114) ----------


def test_a_partially_shipped_line_can_be_claimed_from_the_picker(tmp_path, capsys):
    """The picker and the claim disagreed about one line and the picker was right: an id in the
    ledger is a finished task only when the roadmap no longer carries the line. Measured on
    dockerdesk one command after the other — `pick` named it, `brief` called it ready, and
    `--claim` answered that status lives in exactly one file."""
    project(
        tmp_path,
        BLOCKS + line("RK1", status="⏳"),
        changelog=(
            "# Shipped\n\n## Block A — The model\n\n"
            "- ✅ **RK1 (local half)** **A symptom for RK1** — a reason.\n"
        ),
    )
    assert main(["-C", str(tmp_path), "pick", "--claim"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "RK1" in printed
    # And the line is taken, which is what the flag promises the next caller.
    assert IN_PROGRESS in (tmp_path / "ROADMAP.md").read_text(encoding="utf-8")


def test_the_half_that_landed_is_still_what_the_ledger_says(tmp_path):
    # The marker moved and the record did not: the qualifier is where a partial lives (RK1075),
    # so `ship RK1` still completes it — the door the partial's own answer names.
    from roadkeep.backlog import Backlog

    config = project(
        tmp_path,
        BLOCKS + line("RK1", status="⏳"),
        changelog=(
            "# Shipped\n\n## Block A — The model\n\n"
            "- ✅ **RK1 (local half)** **A symptom for RK1** — a reason.\n"
        ),
    )
    assert main(["-C", str(tmp_path), "status", "RK1", IN_PROGRESS]) == EXIT_OK
    assert Backlog.load(Config.discover(tmp_path)).partial("RK1") == "local half"
    # And the completion closes it from the claimed marker, the line's own door either way.
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "The rest of it landed."]) == EXIT_OK
    assert "RK1" not in (tmp_path / "ROADMAP.md").read_text(encoding="utf-8")
