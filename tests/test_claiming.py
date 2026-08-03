"""One backlog, two workers, one answer — and the claim that makes it two (RK119).

The defect is not that `pick` chose wrongly. Every tier is a pure function of two files, so
two callers reading an unchanged roadmap get the *same* correct answer, and tier 1 — which
prefers a 🛠 line so one worker finishes what they started — is the most confident about
handing over the line somebody else is holding. So the tests stage two callers rather than
hope for them: one claims, and the second is asked what to do.

The three properties that keep this from becoming a lock nobody can break:

* a claim **expires**, and a later caller steps over it rather than waiting;
* a claim is **named** in the answer it was kept out of, because it carries no owner and an
  id is the only thing a caller can recognise its own by;
* every marker door is a **release** — the registry is read against the 🛠 line, so nothing
  has to be told when the line ships, pauses or is put back.

What is asserted about the registry itself is that deleting it loses nothing (L2): the
durable half of a claim is the marker git carries, and the transient half only dates it.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from roadkeep import claiming
from roadkeep.briefing import NothingToBrief, brief
from roadkeep.claiming import HELD, AlreadyHeld, Held
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.picking import Tier, hold, pick, take
from roadkeep.schema import DESIGNED, IDEA, IN_PROGRESS


def line(task_id: str, deps: str = "—", block: str = "A", status: str = DESIGNED) -> str:
    return (
        f"- {status} **{task_id}** (deps: {deps}) **A symptom for {task_id}** "
        f"— a reason. → §{task_id}\n"
    )


BLOCKS = "## Block A — The model\n"
MORE = "\n## Block B — Authoring\n"


def project(tmp_path: Path, roadmap: str, extra: str = "") -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n{extra}[files]\nroadmap = "ROADMAP.md"\n'
        'changelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(roadmap, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "# Shipped\n\n## Block A — The model\n", encoding="utf-8"
    )
    return Config.discover(tmp_path)


@pytest.fixture(autouse=True)
def _no_leftovers(tmp_path):
    """The registry lives outside the checkout, so a test that wrote one cleans it up."""
    yield
    claiming.path(tmp_path).unlink(missing_ok=True)


def age(root: Path, task_id: str, seconds: float) -> None:
    """Backdate one claim, which is how expiry is staged rather than waited for."""
    dated = claiming._read(claiming.path(root))  # noqa: SLF001 - the file under test
    dated[task_id] = time.time() - seconds
    claiming._write(claiming.path(root), dated)  # noqa: SLF001


# -- the second caller gets a different line ---------------------------------


def test_a_claimed_line_is_not_handed_to_the_next_caller(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    first = take(config)
    assert first.choice.entry.task.id == "RK2" and first.taken
    # The whole defect, in one assertion: unclaimed, this is RK2 again.
    assert pick(config).entry.task.id == "RK9"


def test_the_claim_is_the_marker_and_the_marker_is_in_the_file(tmp_path):
    # Durable and git's, which is why no owner field is needed: what a commit shows is that
    # this line is under way, and who took it is the commit's own subject.
    config = project(tmp_path, BLOCKS + line("RK2"))
    claim = take(config)
    assert (claim.change.before, claim.change.after) == (DESIGNED, IN_PROGRESS)
    assert IN_PROGRESS in (tmp_path / "ROADMAP.md").read_text(encoding="utf-8")


def test_tier_one_would_otherwise_hand_over_the_line_it_just_claimed(tmp_path):
    # Tier 1 is the tier that gets this most wrong: a 🛠 line is *evidence* somebody
    # started, so without the claim the second caller is sent at it with the reason saying
    # so. RK9 is the answer, and the tier is the lowest-id one.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    second = pick(config)
    assert (second.entry.task.id, second.tier) == ("RK9", Tier.LOWEST)


def test_nothing_left_to_claim_is_an_answer_and_not_a_write(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK2"))
    take(config)
    empty = take(config)
    assert not empty.taken and empty.change is None
    assert empty.choice.reason == (
        "every ready task is claimed by a worker who has not finished it"
    )


def test_a_claim_is_scoped_by_nothing_but_the_id(tmp_path):
    # A claim in Block A does not make Block B unanswerable: the registry is keyed by id and
    # the scope is applied by `pick` exactly as it was before (RK40).
    config = project(tmp_path, BLOCKS + line("RK2") + MORE + line("RK8", block="B"))
    take(config, "A")
    scoped = pick(config, "B")
    assert scoped.entry.task.id == "RK8" and scoped.held == ()


# -- an expiry, not a lock ---------------------------------------------------


def test_a_claim_nobody_released_is_stepped_over_once_it_is_old(tmp_path):
    # The failure this avoids: an agent that was killed takes a task out of the backlog for
    # ever. Past HELD the line is ordinary half-done work, which is tier 1's own subject.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    age(tmp_path, "RK2", HELD + 1)
    revived = pick(config)
    assert (revived.entry.task.id, revived.tier) == ("RK2", Tier.STARTED)
    assert revived.held == ()


def test_re_taking_an_expired_claim_dates_it_again_without_a_second_write(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK2"))
    take(config)
    age(tmp_path, "RK2", HELD + 1)
    again = take(config)
    # The marker was already 🛠, so nothing was written to the file — and the claim is new.
    assert again.taken and not again.change.changed
    assert [h.id for h in pick(config).held] == ["RK2"]


def test_a_claim_younger_than_the_window_is_still_held(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    age(tmp_path, "RK2", HELD - 60)
    assert pick(config).entry.task.id == "RK9"


# -- named, never counted ----------------------------------------------------


def test_the_answer_names_the_line_it_stepped_around(tmp_path):
    # A claim carries no owner, so a *count* is a line the caller cannot recognise as its
    # own and will ask about again on the next turn.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    held = pick(config).held
    assert [h.id for h in held] == ["RK2"] and held[0].age < HELD


def test_ready_still_counts_the_line_a_claim_holds(tmp_path):
    # `ready` is a fact about the file, and a claim is a fact about the checkout: the same
    # split `--designed` respects, so neither number moves because of the other.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    assert pick(config).ready == 2


def test_how_long_it_has_been_held_reads_as_a_duration(tmp_path):
    assert Held("RK1", 840.0).since == "14m"
    assert Held("RK1", 7_500.0).since == "2h05m"


# -- every marker door is a release ------------------------------------------


def test_moving_the_marker_back_releases_the_claim(tmp_path):
    # `status <id> 📋` is the release, and it is a door that already existed: the registry is
    # read against the 🛠 line, so a claim on a line that is no longer in progress is not one.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    assert main(["-C", str(tmp_path), "status", "RK2", DESIGNED]) == EXIT_OK
    assert pick(config).entry.task.id == "RK2"


def test_a_claim_on_a_line_that_left_the_roadmap_is_forgotten(tmp_path):
    # Nothing tells the registry about a ship; the next write prunes it, because the ids
    # still at 🛠 are in front of it anyway.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    assert main(["-C", str(tmp_path), "ship", "RK2", "--why", "It works now."]) == EXIT_OK
    take(config)
    assert "RK2" not in claiming._read(claiming.path(tmp_path))  # noqa: SLF001


# -- not a second store (L2) -------------------------------------------------


def test_deleting_the_registry_loses_the_date_and_never_the_task(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    claiming.path(tmp_path).unlink()
    # Exactly the behaviour before claims existed: a 🛠 line nobody holds is work to
    # continue, and tier 1 offers it.
    revived = pick(config)
    assert (revived.entry.task.id, revived.tier) == ("RK2", Tier.STARTED)


def test_the_registry_lives_outside_the_checkout(tmp_path):
    # A file the tool wrote into a project's root is one every adopting project has to
    # gitignore before its first `git status` reads as dirty.
    config = project(tmp_path, BLOCKS + line("RK2"))
    take(config)
    assert tmp_path not in claiming.path(tmp_path).parents
    assert claiming.path(tmp_path).is_file()


def test_an_unreadable_registry_is_empty_rather_than_an_error(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK2", status=IN_PROGRESS))
    claiming.path(tmp_path).write_text("not a claim\nRK2 not-a-number\n", encoding="utf-8")
    assert pick(config).entry.task.id == "RK2"


def test_two_checkouts_of_one_project_claim_independently(tmp_path):
    # The scope the defect has is two agents in one working tree, so the key is the resolved
    # root — the same rule the write lock is keyed by (RK117).
    first, second = tmp_path / "one", tmp_path / "two"
    for root in (first, second):
        root.mkdir()
        project(root, BLOCKS + line("RK2"))
    assert claiming.path(first) != claiming.path(second)
    take(Config.discover(first))
    assert pick(Config.discover(second)).entry.task.id == "RK2"
    for root in (first, second):
        claiming.path(root).unlink(missing_ok=True)


# -- the command -------------------------------------------------------------


def test_the_command_claims_and_says_what_it_moved(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2"))
    assert main(["-C", str(tmp_path), "pick", "--claim"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.splitlines()[0].startswith(f"RK2  Block A  {IN_PROGRESS}")
    assert f"claimed  {DESIGNED} → {IN_PROGRESS}" in out
    # Every write prints the event line (RK38), and this one writes.
    assert "event    RK2  Block A  open" in out


def test_the_command_names_the_claim_it_was_not_offered(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    assert main(["-C", str(tmp_path), "pick", "--claim"]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "pick"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.splitlines()[0].startswith("RK9")
    assert "held     RK2 was claimed 0m ago and is not offered" in out


def test_the_json_carries_the_claim_and_the_holds(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    assert main(["-C", str(tmp_path), "pick", "--claim", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["pick"]["id"] == "RK2" and payload["pick"]["status"] == IN_PROGRESS
    assert payload["claimed"] == {"taken": True, "from": DESIGNED, "to": IN_PROGRESS}
    assert payload["event"]["id"] == "RK2" and payload["held"] == []
    assert main(["-C", str(tmp_path), "pick", "--json"]) == EXIT_OK
    second = json.loads(capsys.readouterr().out)
    assert second["claimed"] is None and second["event"] is None
    assert second["held"] == [{"id": "RK2", "age": 0, "since": "0m"}]


def test_nothing_to_claim_exits_zero_because_it_is_an_answer(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2"))
    assert main(["-C", str(tmp_path), "pick", "--claim"]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "pick", "--claim"]) == EXIT_OK
    assert "claimed by a worker" in capsys.readouterr().out


def test_claiming_composes_with_the_flags_that_narrow_the_pick(tmp_path, capsys):
    # `--designed` and `--block` decide *what* is claimed, which is the point of both.
    project(tmp_path, BLOCKS + line("RK2", status=IDEA) + MORE + line("RK8", block="B"))
    argv = ["-C", str(tmp_path), "pick", "--claim", "--designed", "--json"]
    assert main(argv) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["pick"]["id"] == "RK8" and payload["undesigned"] == 1


# -- the door a session actually starts a task with (RK149) -------------------


def test_briefing_the_next_task_takes_it(tmp_path):
    # The gap RK149 records: the skill says `brief` starts a task in one call, so a claim
    # only `pick` could take was a claim the agent following the instructions never took.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    gathered = brief(config, claim=True)
    assert gathered.task.id == "RK2" and gathered.claim.taken
    # The brief describes the line as it was taken, not as it was chosen.
    assert gathered.task.status == IN_PROGRESS
    assert pick(config).entry.task.id == "RK9"


def test_briefing_without_the_flag_still_writes_nothing(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK2"))
    gathered = brief(config)
    assert gathered.claim is None
    assert (tmp_path / "ROADMAP.md").read_text(encoding="utf-8") == BLOCKS + line("RK2")


def test_a_named_line_is_claimed_by_the_caller_and_not_by_a_tier(tmp_path):
    # There is no choice to report, so there is no tier and no runner-up: an empty `Choice`
    # would read as a pick that found nothing rather than one that never happened.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    gathered = brief(config, "RK9", claim=True)
    assert gathered.task.id == "RK9" and gathered.picked == ""
    assert gathered.claim.taken and gathered.claim.choice is None
    assert pick(config).entry.task.id == "RK2"


def test_claiming_a_line_another_worker_holds_is_refused(tmp_path):
    # The one difference between the two doors: `take` was choosing anyway and steps around
    # a live claim, and a caller that named an id has nowhere to step.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    with pytest.raises(AlreadyHeld) as caught:
        brief(config, "RK2", claim=True)
    assert "RK2 was claimed 0m ago" in str(caught.value)
    # It says what to do, because a claim names nobody and this one may be the caller's own.
    assert "without --claim" in str(caught.value)


def test_a_named_claim_whose_window_passed_is_taken_rather_than_refused(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK2"))
    take(config)
    age(tmp_path, "RK2", HELD + 1)
    assert hold(config, "RK2").taken


def test_a_named_claim_never_judges_the_line_it_takes(tmp_path):
    # `pick` never offers blocked work, and a caller that named an id may be about to
    # unblock it: the marker door has always allowed that, and a policy here would be this
    # command re-deciding what `status` decides.
    config = project(tmp_path, BLOCKS + line("RK2", "RK5"))
    assert hold(config, "RK2").taken


def test_nothing_ready_to_brief_writes_nothing(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK2", "RK5"))
    with pytest.raises(NothingToBrief):
        brief(config, claim=True)
    assert not claiming.path(tmp_path).exists()


def test_the_brief_command_claims_and_says_what_it_moved(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2"))
    assert main(["-C", str(tmp_path), "brief", "--claim"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.splitlines()[0].startswith(f"RK2  Block A  {IN_PROGRESS}")
    assert f"claimed  {DESIGNED} → {IN_PROGRESS}" in out
    assert "event    RK2  Block A  open" in out


def test_the_brief_json_carries_the_claim(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    assert main(["-C", str(tmp_path), "brief", "--claim", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["claimed"] == {"taken": True, "from": DESIGNED, "to": IN_PROGRESS}
    assert payload["event"]["id"] == "RK2"
    assert main(["-C", str(tmp_path), "brief", "RK9", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["claimed"] is None


def test_the_brief_command_reports_a_held_line_and_writes_nothing(tmp_path, capsys):
    config = project(tmp_path, BLOCKS + line("RK2"))
    assert main(["-C", str(tmp_path), "brief", "--claim"]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "brief", "RK2", "--claim"]) == EXIT_USAGE
    assert "may be yours" in capsys.readouterr().err
    # The refusal wrote nothing, so the claim is still the first one's.
    assert [h.id for h in claiming.live(tmp_path, config.document("roadmap").entries)] == [
        "RK2"
    ]


def test_claiming_a_brief_composes_with_the_flags_that_narrow_the_pick(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2", status=IDEA) + MORE + line("RK8", block="B"))
    argv = ["-C", str(tmp_path), "brief", "--block", "B", "--claim", "--json"]
    assert main(argv) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "RK8" and payload["status"] == IN_PROGRESS


def test_a_refusal_the_marker_write_raises_is_reported_and_not_a_traceback(tmp_path, capsys):
    # `--claim` makes this command a write, so it inherits every refusal that guards one:
    # here a sibling file already states this id's status, which has one home (RK7).
    config = project(tmp_path, BLOCKS + line("RK2"))
    (tmp_path / "IMPROVEMENTS.md").write_text(
        f"# Improvements\n\n## Block A — The model\n\n{line('RK2')}", encoding="utf-8"
    )
    (tmp_path / "roadkeep.toml").write_text(
        (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")
        + 'improvements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    assert main(["-C", str(tmp_path), "pick", "--claim"]) == EXIT_USAGE
    assert "IMPROVEMENTS.md" in capsys.readouterr().err
    assert config.document("roadmap").by_id()["RK2"].task.status == DESIGNED
