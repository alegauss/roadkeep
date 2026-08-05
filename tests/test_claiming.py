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
from roadkeep.authoring import add, set_status
from roadkeep.backlog import Backlog
from roadkeep.claiming import AlreadyHeld, Followed, Held, window
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import CLAIM_HELD, CLAIM_HELD_MAX, Config, ConfigError
from roadkeep.deferring import defer, resume
from roadkeep.picking import Tier, hold, pick, take
from roadkeep.renumbering import renumber
from roadkeep.schema import DESIGNED, IDEA, IN_PROGRESS


def line(task_id: str, deps: str = "—", block: str = "A", status: str = DESIGNED) -> str:
    return (
        f"- {status} **{task_id}** (deps: {deps}) **A symptom for {task_id}** "
        f"— a reason. → §{task_id}\n"
    )


#: The default window, in seconds. `[claims] held` is minutes and nothing here declares one,
#: so this is what a project gets until it does (RK151) — read rather than written, because a
#: test that hardcoded the number would pass while the default said something else.
HELD = window(Config.default())

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
    """Backdate one claim, which is how expiry is staged rather than waited for.

    The scope rides along untouched (RK280): a backdated claim is the same claim, and a
    helper that dropped the paths would stage a state no door writes.
    """
    dated = claiming._read(claiming.path(root))  # noqa: SLF001 - the file under test
    held = dated.get(task_id)
    dated[task_id] = claiming.Dating(
        time.time() - seconds, held.paths if held is not None else ()
    )
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


def test_a_project_declares_its_own_window_in_minutes(tmp_path):
    # RK151: how long a task takes is the one thing about a claim that differs between
    # backlogs, so the number is the project's (L6) — declared in minutes and used in seconds.
    config = project(tmp_path, BLOCKS + line("RK2"), extra="[claims]\nheld = 5\n")
    assert config.held == 5 and window(config) == 300.0
    take(config)
    age(tmp_path, "RK2", 301)
    # Past its own window, not past the default's: the same claim is still inside that one.
    assert pick(config).entry.task.id == "RK2" and pick(config).held == ()


def test_a_window_nobody_would_wait_out_is_refused_and_names_the_unit(tmp_path):
    # The one way to be badly wrong here is to write seconds in a key that reads minutes, so
    # the bound turns that into a refusal rather than a claim that outlives the project.
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[claims]\nheld = 3600\n', encoding="utf-8"
    )
    with pytest.raises(ConfigError) as caught:
        Config.discover(tmp_path)
    assert "must be minutes" in str(caught.value)
    assert str(CLAIM_HELD_MAX) in str(caught.value)


def test_a_window_shorter_than_reading_the_brief_is_refused_too(tmp_path):
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[claims]\nheld = 0\n', encoding="utf-8"
    )
    with pytest.raises(ConfigError):
        Config.discover(tmp_path)


def test_the_command_names_the_projects_own_window_and_not_the_default(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2"), extra="[claims]\nheld = 25\n")
    assert main(["-C", str(tmp_path), "brief", "--claim"]) == EXIT_OK
    assert "held for 25m" in capsys.readouterr().out


def test_the_scaffold_writes_the_window_with_its_unit(tmp_path):
    # The scaffold's own job (RK18): every limit it writes carries the unit the key name does
    # not say, and this is the key where getting the unit wrong is the whole hazard.
    assert main(["-C", str(tmp_path), "init"]) == EXIT_OK
    written = (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")
    assert "[claims]" in written and f"held = {CLAIM_HELD}" in written
    assert "minutes a claim" in written
    assert Config.discover(tmp_path).held == CLAIM_HELD


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


# -- the line that is both stalled and held (RK152) ---------------------------


def test_a_stalled_line_says_whether_somebody_is_on_it(tmp_path):
    # Two states one sentence used to serve: "started and hit a wall", which invites
    # unblocking the line, and "somebody is on this and the dep is what they are waiting
    # for", which invites leaving it alone.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK7", "RK5", status=IN_PROGRESS))
    unheld = pick(config)
    assert unheld.stalled[0].id == "RK7" and unheld.stalled[0].claimed is None
    hold(config, "RK7")
    stalled = pick(config).stalled[0]
    assert stalled.claimed is not None and stalled.blockers == ("RK5",)


def test_a_claim_on_a_blocked_line_is_not_a_candidate_stepped_around(tmp_path):
    # Two facts, two names: `held` is the ready lines the ranking stepped around, and a
    # blocked line was never in the ranking to be stepped around.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK7", "RK5", status=IN_PROGRESS))
    hold(config, "RK7")
    choice = pick(config)
    assert choice.held == () and choice.stalled[0].claimed is not None
    # And the answer is unchanged: a claim on something unpickable cannot move the pick.
    assert choice.entry.task.id == "RK2"


def test_the_command_says_a_stalled_line_is_claimed(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2") + line("RK7", "RK5", status=IN_PROGRESS))
    config = Config.discover(tmp_path)
    hold(config, "RK7")
    assert main(["-C", str(tmp_path), "pick"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "stalled  RK7 is in progress and claimed 0m ago, waiting on RK5" in out


def test_the_json_names_the_two_kinds_of_claim_apart(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2") + line("RK7", "RK5", status=IN_PROGRESS))
    config = Config.discover(tmp_path)
    hold(config, "RK7")
    take(config)  # RK2, the ready one
    assert main(["-C", str(tmp_path), "pick", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["stalled"][0] == {
        "id": "RK7",
        "blockers": ["RK5"],
        "claimed": {"age": 0, "since": "0m"},
    }
    assert payload["held"] == [{"id": "RK2", "age": 0, "since": "0m"}]


def test_an_expired_claim_on_a_stalled_line_says_nothing(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK7", "RK5", status=IN_PROGRESS))
    hold(config, "RK7")
    age(tmp_path, "RK7", HELD + 1)
    assert pick(config).stalled[0].claimed is None


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


# -- the two doors the marker cannot express (RK156) ---------------------------


def test_a_renumber_carries_the_claim_to_the_new_address(tmp_path):
    # `renumber` does not move the marker, it moves the *address* — so without this the new
    # id reads as started work nobody holds, which is RK119's defect reopened by the one
    # command that exists because a merge spent an id twice.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    hold(config, "RK2")
    moved = renumber(config, "RK2", "RK20")
    assert moved.claim is not None
    moved.save()
    held = pick(config).held
    assert [h.id for h in held] == ["RK20"]
    assert "RK2" not in claiming._read(claiming.path(tmp_path))  # noqa: SLF001


def test_the_carried_claim_keeps_its_age_rather_than_restarting(tmp_path):
    # The work is the same age, and a claim that renewed itself on a rename would be an
    # expiry a rename could postpone for ever.
    config = project(tmp_path, BLOCKS + line("RK2"))
    hold(config, "RK2")
    age(tmp_path, "RK2", HELD - 30)
    renumber(config, "RK2", "RK20").save()
    dated = claiming._read(claiming.path(tmp_path))  # noqa: SLF001
    assert time.time() - dated["RK20"].when > HELD - 60


def test_a_renumber_of_an_unheld_line_carries_nothing(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK2", status=IN_PROGRESS))
    moved = renumber(config, "RK2", "RK20")
    moved.save()
    assert moved.claim is None and not claiming.path(tmp_path).exists()


def test_the_renumber_command_says_the_claim_moved(tmp_path, capsys):
    config = project(tmp_path, BLOCKS + line("RK2"))
    hold(config, "RK2")
    assert main(["-C", str(tmp_path), "renumber", "RK2", "--to", "RK20"]) == EXIT_OK
    assert "claimed  the claim taken 0m ago moved with it" in capsys.readouterr().out


def test_shipping_a_claimed_line_leaves_no_entry_behind(tmp_path):
    # RK162, found by the first `claims` run after RK161 shipped: the entry is inert, an id
    # never being reused — and a row that can never mean anything is noise in the one listing
    # that exists to surface the row somebody is hunting.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    assert main(["-C", str(tmp_path), "ship", "RK2", "--why", "It works now."]) == EXIT_OK
    assert claiming.survey(Backlog.load(config)) == ()


def test_retiring_a_claimed_line_leaves_no_entry_either(tmp_path):
    # The same door with the other marker: 🗑 is not the in-progress one, so the rule every
    # marker write obeys already said release.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    argv = ["-C", str(tmp_path), "retire", "RK2", "--reason", "Not happening."]
    assert main(argv) == EXIT_OK
    assert claiming._read(claiming.path(tmp_path)) == {}  # noqa: SLF001


def test_a_release_reconciles_every_row_and_not_only_its_own(tmp_path):
    # RK163: dropping a single key left every row *no door reported* standing, which is what
    # the `claims` run straight after RK162 shipped was still printing.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    hold(config, "RK2")
    # As a `git checkout` would leave it: RK2 reads 📋 again and no door was told.
    (tmp_path / "ROADMAP.md").write_text(BLOCKS + line("RK2") + line("RK9"), encoding="utf-8")
    # A marker write that is not about RK2 at all, and not a claim either.
    set_status(Config.discover(tmp_path), "RK9", IDEA)
    assert claiming._read(claiming.path(tmp_path)) == {}  # noqa: SLF001


def test_a_marker_write_on_a_backlog_with_no_registry_writes_no_file(tmp_path):
    # Every direction now reads the registry, so the one thing to hold is that reading it is
    # not creating it: a project that never claims gets no temp file from a `status`.
    config = project(tmp_path, BLOCKS + line("RK2"))
    set_status(config, "RK2", IDEA)
    assert not claiming.path(tmp_path).exists()


def test_the_prune_still_reconciles_what_no_door_reported(tmp_path):
    # Why the prune stays and is not a second writer of the release rule (RK159's argument):
    # git moves markers under the tool, and a checkout fires no door at all.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    hold(config, "RK2")
    # As a `git checkout` would leave it: RK2 reads 📋 again and no door was told.
    (tmp_path / "ROADMAP.md").write_text(BLOCKS + line("RK2") + line("RK9"), encoding="utf-8")
    assert "RK2" in claiming._read(claiming.path(tmp_path))  # noqa: SLF001
    hold(Config.discover(tmp_path), "RK9")
    assert set(claiming._read(claiming.path(tmp_path))) == {"RK9"}  # noqa: SLF001


def test_deferring_a_claimed_line_drops_the_claim(tmp_path):
    # The other door the marker cannot express: the line leaves the file the marker is read
    # in, so nothing would clear the entry — and a `resume` inside the window would read as
    # held by the worker who gave it up.
    project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'deferred = "DEFERRED.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "DEFERRED.md").write_text(
        "# Set aside\n\n## Block A — The model\n", encoding="utf-8"
    )
    config = Config.discover(tmp_path)
    hold(config, "RK2")
    defer(config, "RK2", reason="waiting on a decision").save()
    assert "RK2" not in claiming._read(claiming.path(tmp_path))  # noqa: SLF001
    resume(config, "RK2", marker=DESIGNED).save()
    # Back, and unheld: the claim the pause dropped is not one the return brings with it.
    revived = pick(Config.discover(tmp_path))
    assert revived.entry.task.id == "RK2" and revived.held == ()


def test_resuming_a_line_in_progress_is_an_assertion_like_any_other(tmp_path):
    # The wrinkle RK158's design named: `--marker 🛠` says somebody is on it, so it claims —
    # a *fresh* claim, the pause having dropped the one that was there (RK156).
    project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'deferred = "DEFERRED.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "DEFERRED.md").write_text(
        "# Set aside\n\n## Block A — The model\n", encoding="utf-8"
    )
    config = Config.discover(tmp_path)
    defer(config, "RK2", reason="waiting on a decision").save()
    resume(config, "RK2", marker=IN_PROGRESS).save()
    assert [h.id for h in pick(Config.discover(tmp_path)).held] == ["RK2"]


# -- the claim follows the marker (RK158) --------------------------------------


def test_marking_a_line_in_progress_claims_it(tmp_path):
    # The third way to start work, and the one that asserted nothing: the next `pick` read the
    # line as work somebody abandoned and offered it with tier 1's own reason.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    change = set_status(config, "RK2", IN_PROGRESS)
    assert change.claim is Followed.CLAIMED
    assert pick(config).entry.task.id == "RK9"


def test_marking_it_anything_else_releases_the_claim(tmp_path):
    # The half that was implicit — inferred by the read — made explicit at the write.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    change = set_status(config, "RK2", DESIGNED)
    assert change.claim is Followed.RELEASED
    assert "RK2" not in claiming._read(claiming.path(tmp_path))  # noqa: SLF001
    assert pick(config).entry.task.id == "RK2"


def test_a_marker_that_released_nothing_says_nothing(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK2"))
    assert set_status(config, "RK2", IDEA).claim is Followed.NEITHER


def test_re_asserting_the_marker_a_line_carries_is_a_new_claim(tmp_path):
    # The no-op path: nothing is written to the file, because an unchanged file with a moved
    # mtime reads as an edit — and the claim is dated again, a re-assertion being an assertion.
    config = project(tmp_path, BLOCKS + line("RK2", status=IN_PROGRESS))
    before = (tmp_path / "ROADMAP.md").read_bytes()
    change = set_status(config, "RK2", IN_PROGRESS)
    assert not change.changed and change.claim is Followed.CLAIMED
    assert (tmp_path / "ROADMAP.md").read_bytes() == before
    assert [h.id for h in pick(config).held] == ["RK2"]


def test_the_marker_door_refuses_a_line_a_live_claim_holds(tmp_path):
    # RK160: the refusal guarded the named door and not the marker write beneath it, so
    # `status <id> 🛠` re-dated somebody's claim in their name and said nothing.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    with pytest.raises(AlreadyHeld) as caught:
        set_status(config, "RK2", IN_PROGRESS)
    assert "RK2 was claimed 0m ago" in str(caught.value)
    assert main(["-C", str(tmp_path), "status", "RK2", IN_PROGRESS]) == EXIT_USAGE


def test_nothing_re_dates_a_live_claim(tmp_path):
    # The invariant that falls out of it, and the one worth having: the window is the expiry,
    # not something a second call can postpone.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    age(tmp_path, "RK2", 600)
    for door in (lambda: hold(config, "RK2"), lambda: set_status(config, "RK2", IN_PROGRESS)):
        with pytest.raises(AlreadyHeld):
            door()
    assert claiming.live(config, config.document("roadmap").entries)[0].age > 600


def test_a_release_is_never_refused(tmp_path):
    # The constraint that holds whichever way this went: writing any other marker is how a
    # claim is given back, and a release that could be refused is a line nobody can hand over.
    config = project(tmp_path, BLOCKS + line("RK2"))
    take(config)
    assert set_status(config, "RK2", DESIGNED).claim is Followed.RELEASED
    # And the line is claimable again, by the door that was just refused.
    assert set_status(config, "RK2", IN_PROGRESS).claim is Followed.CLAIMED


def test_the_refusal_writes_nothing_at_all(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK2", status=IN_PROGRESS))
    set_status(config, "RK2", IN_PROGRESS)  # the first claim, on a line already 🛠
    dated = claiming._read(claiming.path(tmp_path))  # noqa: SLF001
    before = (tmp_path / "ROADMAP.md").read_bytes()
    with pytest.raises(AlreadyHeld):
        set_status(config, "RK2", IN_PROGRESS)
    assert (tmp_path / "ROADMAP.md").read_bytes() == before
    assert claiming._read(claiming.path(tmp_path)) == dated  # noqa: SLF001


def test_every_door_that_claims_leaves_the_same_registry(tmp_path):
    """The property RK159 asked for, which no door's own tests stated: `take`, `hold` and
    `status` write a claim through one rule, so what they leave behind is one thing. This is
    what would have caught a *disagreement* between them — the duplication it removed was
    only visible in the code."""
    left: list[dict[str, float]] = []
    for door in ("take", "hold", "status"):
        config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
        claiming.path(tmp_path).unlink(missing_ok=True)
        if door == "take":
            take(config)
        elif door == "hold":
            hold(config, "RK2")
        else:
            set_status(config, "RK2", IN_PROGRESS)
        dated = claiming._read(claiming.path(tmp_path))  # noqa: SLF001
        left.append({name: round(row.when) for name, row in dated.items()})
    assert [set(one) for one in left] == [{"RK2"}, {"RK2"}, {"RK2"}]
    # And each of them leaves a line the next caller is not sent at.
    assert pick(Config.discover(tmp_path)).entry.task.id == "RK9"


def test_adding_a_line_in_progress_is_not_one_of_the_three_doors(tmp_path):
    # A stated boundary rather than a silent gap: the three ways to *start* work are the two
    # `--claim` flags and `status`, and a line being created is not one the backlog handed out.
    config = project(tmp_path, BLOCKS)
    add(config, block="A", symptom="A symptom", why="A reason.", status=IN_PROGRESS)
    assert not claiming.path(tmp_path).exists()


# -- the listing L5 was missing (RK161) ----------------------------------------


def test_the_registry_reads_as_three_different_things(tmp_path):
    # One date means three states, and the two that are not `held` are what somebody hunting a
    # claim is looking for: the entry nothing reads, and the one already stepped over.
    config = project(
        tmp_path,
        BLOCKS + line("RK2", status=IN_PROGRESS) + line("RK9", status=IN_PROGRESS) + line("RK5"),
    )
    for task_id in ("RK2", "RK9", "RK5"):
        claiming.follow(
            tmp_path, task_id, IN_PROGRESS, config.document("roadmap").entries
        )
    age(tmp_path, "RK9", HELD + 60)
    age(tmp_path, "RK5", 120)
    rows = {row.id: row for row in claiming.survey(Backlog.load(config))}
    assert rows["RK2"].state is claiming.State.HELD
    assert rows["RK9"].state is claiming.State.EXPIRED
    # 📋: the marker moved, so the entry is not a claim at all.
    assert rows["RK5"].state is claiming.State.STALE and rows["RK5"].marker == DESIGNED


def test_an_entry_for_an_id_no_line_carries_is_stale_and_not_an_error(tmp_path):
    # What a `ship` leaves behind until the next marker write reconciles it, and what a
    # hand-edited file can leave for ever: reported, because it is the entry a reader wants.
    config = project(tmp_path, BLOCKS + line("RK2"))
    claiming._write(  # noqa: SLF001
        claiming.path(tmp_path), {"RK99": claiming.Dating(time.time())}
    )
    row = claiming.survey(Backlog.load(config))[0]
    assert (row.id, row.state, row.marker) == ("RK99", claiming.State.STALE, "")
    # And the one of the four absences that is worth acting on (RK164).
    assert row.where is claiming.Where.NOWHERE


def test_the_three_ids_that_left_by_a_door_say_which_one(tmp_path):
    # RK164: "no line carries this id" was true of four situations and useful in one, so the
    # listing named a consequence where every other answer in this tool names a cause.
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'deferred = "DEFERRED.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(BLOCKS + line("RK2"), encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "# Shipped\n\n## Block A — The model\n\n"
        "- ✅ **RK7** **A shipped symptom** — it works now.\n"
        "- 🗑 **RK8** **An abandoned symptom** — superseded by RK7.\n",
        encoding="utf-8",
    )
    (tmp_path / "DEFERRED.md").write_text(
        "# Set aside\n\n## Block A — The model\n\n"
        "- ⏸ **RK9** (deps: —) **A paused symptom** — set aside (waiting): a reason. → §RK9\n",
        encoding="utf-8",
    )
    config = Config.discover(tmp_path)
    now = time.time()
    claiming._write(  # noqa: SLF001
        claiming.path(tmp_path),
        {name: claiming.Dating(now) for name in ("RK7", "RK8", "RK9", "RK99")},
    )
    where = {row.id: row.where for row in claiming.survey(Backlog.load(config))}
    assert where == {
        "RK7": claiming.Where.SHIPPED,
        "RK8": claiming.Where.RETIRED,
        "RK9": claiming.Where.PAUSED,
        "RK99": claiming.Where.NOWHERE,
    }
    # Every one of them is still `stale`: what it *is* and where it went are two facts.
    assert {row.state for row in claiming.survey(Backlog.load(config))} == {
        claiming.State.STALE
    }


def test_the_listing_is_oldest_first_because_age_is_the_axis(tmp_path):
    config = project(
        tmp_path, BLOCKS + line("RK2", status=IN_PROGRESS) + line("RK9", status=IN_PROGRESS)
    )
    for task_id in ("RK2", "RK9"):
        claiming.follow(
            tmp_path, task_id, IN_PROGRESS, config.document("roadmap").entries
        )
    age(tmp_path, "RK9", 600)
    assert [row.id for row in claiming.survey(Backlog.load(config))] == [
        "RK9",
        "RK2",
    ]


def test_the_command_names_the_window_and_the_registry(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2"), extra="[claims]\nheld = 25\n")
    take(Config.discover(tmp_path))
    assert main(["-C", str(tmp_path), "claims"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.splitlines()[0] == "1 dated, 1 held  (window 25m)"
    assert "held     RK2  claimed 0m ago" in out
    # The file, because the release is a marker and the *file* is what is deleted when a
    # whole checkout's claims outlived their workers.
    assert str(claiming.path(tmp_path)) in out


def test_a_prune_drops_what_is_not_a_claim_and_keeps_what_is(tmp_path, capsys):
    # RK165: the other remedy is the whole file, so clearing one row nobody can act on meant
    # deleting the claims of every worker beside it.
    config = project(
        tmp_path, BLOCKS + line("RK2", status=IN_PROGRESS) + line("RK5") + line("RK9")
    )
    for task_id in ("RK2", "RK5", "RK99"):
        claiming._write(  # noqa: SLF001
            claiming.path(tmp_path),
            {
                **claiming._read(claiming.path(tmp_path)),  # noqa: SLF001
                task_id: claiming.Dating(time.time()),
            },
        )
    pruning = claiming.prune(config)
    assert [row.id for row in pruning.kept] == ["RK2"]
    assert {row.id for row in pruning.dropped} == {"RK5", "RK99"}
    assert set(claiming._read(claiming.path(tmp_path))) == {"RK2"}  # noqa: SLF001


def test_a_prune_keeps_an_expired_claim_because_it_is_still_one(tmp_path, capsys):
    # What `follow` keeps is every id the roadmap carries at 🛠, live or expired: an expired row
    # is still a statement about a started line, and moving the marker is how it goes.
    config = project(tmp_path, BLOCKS + line("RK2"))
    take(config)
    age(tmp_path, "RK2", HELD + 60)
    pruning = claiming.prune(config)
    assert [row.state for row in pruning.kept] == [claiming.State.EXPIRED]
    assert pruning.dropped == ()


def test_a_prune_never_takes_a_live_claim(tmp_path):
    # Taking a line from a worker is a marker, and the door that refuses it is RK160's.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    claiming.prune(config)
    assert [h.id for h in pick(config).held] == ["RK2"]


def test_the_prune_names_what_it_dropped_and_says_when_it_dropped_nothing(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2"))
    claiming._write(  # noqa: SLF001
        claiming.path(tmp_path), {"RK99": claiming.Dating(time.time())}
    )
    assert main(["-C", str(tmp_path), "claims", "--prune"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "pruned   RK99  claimed 0m ago  in no file at all" in out
    # And a second run has nothing to do, which it says rather than printing an empty listing.
    assert main(["-C", str(tmp_path), "claims", "--prune"]) == EXIT_OK
    assert "pruned   nothing: every row is a claim" in capsys.readouterr().out


def test_the_prune_carries_what_it_dropped_in_the_json(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2"))
    claiming._write(  # noqa: SLF001
        claiming.path(tmp_path), {"RK99": claiming.Dating(time.time())}
    )
    assert main(["-C", str(tmp_path), "claims", "--prune", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["claims"] == [] and len(payload["pruned"]) == 1
    assert payload["pruned"][0]["where"] == "in no file at all"


def test_an_empty_registry_is_an_answer_and_not_a_failure(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2"))
    assert main(["-C", str(tmp_path), "claims"]) == EXIT_OK
    assert capsys.readouterr().out.startswith("0 dated, 0 held")


def test_the_listing_offers_nothing_and_ranks_nothing(tmp_path, capsys):
    # It must not become a second answer to "what should I work on": `pick` decides that, and
    # a listing that offered anything would be a fourth tier nobody declared.
    project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(Config.discover(tmp_path))
    assert main(["-C", str(tmp_path), "claims", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == {"window", "registry", "held", "claims", "pruned"}
    # `null` and not an empty list, because the flag was not passed: nothing was dropped and
    # nothing was asked to be (RK165).
    assert payload["pruned"] is None
    assert set(payload["claims"][0]) == {
        "id",
        "state",
        # Where the id is, which is a fact and not an offer (RK164).
        "where",
        "age",
        "since",
        "marker",
        "block",
        # What this claim says its commit owns (RK280), counted in the listing and named
        # by `claim <id>` — present as an empty list where the holder has not said.
        "paths",
    }


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
    assert [h.id for h in claiming.live(config, config.document("roadmap").entries)] == [
        "RK2"
    ]


def test_the_brief_names_the_lines_its_pick_stepped_around(tmp_path):
    # RK154: the call a session starts a task with was the one reporting the least, and the
    # claiming caller is precisely the one that will ask about the missing id again.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    gathered = brief(config)
    assert gathered.task.id == "RK9" and [h.id for h in gathered.held] == ["RK2"]
    # Carried as the pick's own answer, so the next thing `pick` knows is a field and not a
    # change — and `picked` is still that answer's reason.
    assert gathered.choice is not None and gathered.picked == gathered.choice.reason


def test_a_brief_the_caller_addressed_reports_no_pick_at_all(tmp_path):
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    named = brief(config, "RK9")
    assert named.choice is None and named.picked == "" and named.held == ()


def test_the_absence_of_an_answer_names_the_claims_that_emptied_it(tmp_path):
    # The one absence in this design a caller cannot act on without the ids: with no owner
    # field, "somebody holds it" and "you hold it" read identically.
    config = project(tmp_path, BLOCKS + line("RK2"))
    take(config)
    with pytest.raises(NothingToBrief) as caught:
        brief(config)
    assert [h.id for h in caught.value.held] == ["RK2"]
    assert "held: RK2 (0m ago)" in str(caught.value)
    # And on the claiming path too, where nothing was written either.
    with pytest.raises(NothingToBrief):
        brief(config, claim=True)


def test_the_brief_command_and_the_pick_report_a_hold_the_same_way(tmp_path, capsys):
    project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    config = Config.discover(tmp_path)
    take(config)
    assert main(["-C", str(tmp_path), "brief", "--json"]) == EXIT_OK
    briefed = json.loads(capsys.readouterr().out)
    assert main(["-C", str(tmp_path), "pick", "--json"]) == EXIT_OK
    picked = json.loads(capsys.readouterr().out)
    # One fact spelled two ways is two facts.
    assert briefed["held"] == picked["held"] == [{"id": "RK2", "age": 0, "since": "0m"}]
    assert main(["-C", str(tmp_path), "brief"]) == EXIT_OK
    assert "held     RK2 was claimed 0m ago and is not offered" in capsys.readouterr().out


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


# -- what a claim says its commit owns (RK280) -------------------------------


def test_a_scope_is_recorded_against_the_claim_and_read_back(tmp_path):
    # The write that was missing: `claim` locks a scan-to-save span and knows who holds a
    # line, and nothing said which of a dirty tree's files that line's commit was.
    config = project(tmp_path, BLOCKS + line("RK2"))
    take(config)
    assert claiming.scope(config, "RK2", ["src/a.py", "tests/test_a.py"]) == (
        "src/a.py",
        "tests/test_a.py",
    )
    held = claiming.live(config, config.document("roadmap").entries)
    assert held[0].paths == ("src/a.py", "tests/test_a.py")


def test_a_scope_on_a_line_nobody_holds_is_refused(tmp_path):
    # Taking is a marker, and a command that dated a claim as a side effect of naming files
    # would be a second way to start work — the shape RK158 spent a task removing.
    config = project(tmp_path, BLOCKS + line("RK2"))
    with pytest.raises(claiming.NotHeld) as raised:
        claiming.scope(config, "RK2", ["src/a.py"])
    assert "take the line first" in str(raised.value)
    assert not claiming.path(tmp_path).exists()  # refused before it wrote anything


def test_a_scope_replaces_rather_than_grows(tmp_path):
    # A scope answers *what is this commit*, and a call that only ever added would put the
    # corrected answer back behind the file (RK165, one row along).
    config = project(tmp_path, BLOCKS + line("RK2"))
    take(config)
    claiming.scope(config, "RK2", ["src/a.py", "src/b.py"])
    assert claiming.scope(config, "RK2", ["src/b.py"]) == ("src/b.py",)


def test_a_scope_collapses_a_path_named_twice(tmp_path):
    # The answer is fed to `git add --`, where a path staged twice is noise in a contract
    # meant to be read.
    config = project(tmp_path, BLOCKS + line("RK2"))
    take(config)
    assert claiming.scope(config, "RK2", ["src/a.py", "src/a.py"]) == ("src/a.py",)


def test_re_asserting_a_claim_keeps_the_scope_it_was_holding(tmp_path):
    # A re-assertion is a new date about the same work, and a clock that revoked the scope
    # would make the declaration something to remember to repeat.
    config = project(tmp_path, BLOCKS + line("RK2"))
    take(config)
    claiming.scope(config, "RK2", ["src/a.py"])
    age(tmp_path, "RK2", HELD + 1)
    take(config)
    assert claiming.live(config, config.document("roadmap").entries)[0].paths == ("src/a.py",)


def test_releasing_the_line_drops_the_scope_with_the_claim(tmp_path):
    # The rule that keeps this from being a second thing to remember: every marker door is a
    # release, and a scope outliving its claim would be a statement about nobody's work.
    config = project(tmp_path, BLOCKS + line("RK2"))
    take(config)
    claiming.scope(config, "RK2", ["src/a.py"])
    set_status(config, "RK2", DESIGNED)
    assert claiming._read(claiming.path(tmp_path)) == {}  # noqa: SLF001


def test_a_scope_travels_with_a_renumbered_line(tmp_path):
    # `renumber` moves the address and not the marker (RK156), so what it carries is the
    # whole row: a scope left behind on the old id is one no command can reach.
    config = project(tmp_path, BLOCKS + line("RK2", status=IN_PROGRESS))
    hold(config, "RK2")
    claiming.scope(config, "RK2", ["src/a.py"])
    renumber(config, "RK2", "RK20").save()
    assert claiming._read(claiming.path(tmp_path))["RK20"].paths == ("src/a.py",)  # noqa: SLF001


def test_a_path_holding_a_space_survives_the_registry(tmp_path):
    # The date is separated by a space and the paths by a tab, which is the reason: a
    # second space-separated field would end the first path at its first blank.
    config = project(tmp_path, BLOCKS + line("RK2"))
    take(config)
    claiming.scope(config, "RK2", ["src/a file.py"])
    assert claiming.live(config, config.document("roadmap").entries)[0].paths == (
        "src/a file.py",
    )


def test_a_row_written_before_scopes_existed_still_parses(tmp_path):
    # A session upgrading under a claim it is holding keeps it: the paths are a tail, so a
    # row without one is a claim with no scope and never a row that is skipped.
    config = project(tmp_path, BLOCKS + line("RK2", status=IN_PROGRESS))
    claiming.path(tmp_path).write_text(f"RK2 {time.time():.6f}\n", encoding="utf-8")
    held = claiming.live(config, config.document("roadmap").entries)
    assert [(one.id, one.paths) for one in held] == [("RK2", ())]


def test_the_other_claims_a_commit_has_to_leave_alone_are_the_scoped_ones(tmp_path):
    # A claim names nobody (RK119), so no write can be refused as somebody else's — what is
    # decidable is the reverse, asked from the id being committed.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    hold(config, "RK9")
    claiming.scope(config, "RK2", ["src/a.py"])
    claiming.scope(config, "RK9", ["src/b.py"])
    entries = config.document("roadmap").entries
    assert [(o.id, o.paths) for o in claiming.elsewhere(config, "RK2", entries)] == [
        ("RK9", ("src/b.py",))
    ]


def test_a_claim_that_declared_nothing_is_left_out_of_that_answer(tmp_path):
    # Silence is a holder who has not said, not a holder claiming nothing — treating it as
    # the second would answer with a confidence the registry does not carry.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    hold(config, "RK9")
    claiming.scope(config, "RK2", ["src/a.py"])
    entries = config.document("roadmap").entries
    assert claiming.elsewhere(config, "RK2", entries) == ()


def test_the_command_answers_the_paths_alone_when_a_script_is_reading(tmp_path, capsys):
    # `--porcelain` is consumed by `git add --`, so a heading on it would be a filename.
    project(tmp_path, BLOCKS + line("RK2"))
    config = Config.discover(tmp_path)
    take(config)
    at = ["-C", str(tmp_path), "claim", "RK2"]
    assert main([*at, "--path", "src/a.py", "--path", "tests/test_a.py"]) == EXIT_OK
    capsys.readouterr()
    assert main([*at, "--porcelain"]) == EXIT_OK
    assert capsys.readouterr().out == "src/a.py\ntests/test_a.py\n"


def test_the_command_refuses_a_line_no_claim_holds_rather_than_answering_empty(
    tmp_path, capsys
):
    # An empty answer would read as "this commit owns nothing", which is the sentence that
    # makes `git add -A` look right.
    project(tmp_path, BLOCKS + line("RK2"))
    assert main(["-C", str(tmp_path), "claim", "RK2"]) == EXIT_USAGE
    assert "no live claim on RK2" in capsys.readouterr().err


# -- the caller that reads it back, at the commit (RK294) ---------------------


def test_the_split_names_what_no_claim_speaks_for(tmp_path):
    # The list the incident was made of: a path in neither scope is one `git add -A` takes
    # silently, so it is named rather than counted.
    config = project(tmp_path, BLOCKS + line("RK2") + line("RK9"))
    take(config)
    hold(config, "RK9")
    claiming.scope(config, "RK2", ["src/a.py"])
    claiming.scope(config, "RK9", ["src/b.py"])
    entries = config.document("roadmap").entries
    split = claiming.split(config, "RK2", entries, ["src/a.py", "src/b.py", "src/c.py"])
    assert split.mine == ("src/a.py",)
    assert split.theirs == (("src/b.py", "RK9"),)
    assert split.loose == ("src/c.py",)
    # A path some other claim declared but nothing changed is not in any of the three: the
    # question is what *this commit* would take.
    assert claiming.split(config, "RK2", entries, ["src/a.py"]).theirs == ()


def test_a_departure_reads_the_scope_while_the_claim_is_still_live(tmp_path):
    # The caller RK280 did not have. `ship` releases the claim, so a read made after it is a
    # read of nothing — this one is taken from the roadmap as it was, at 🛠.
    config = project(tmp_path, BLOCKS + line("RK2", status=IN_PROGRESS))
    hold(config, "RK2")
    claiming.scope(config, "RK2", ["src/a.py"])
    entries = config.document("roadmap").entries
    assert claiming.departing(config, "RK2", entries).mine == ("src/a.py",)


def test_a_departure_says_nothing_where_no_claim_declared_a_path(tmp_path):
    # Every project that has not adopted this. There is nothing to subtract the tree from, so
    # the honest report is no report — and git is not asked either.
    config = project(tmp_path, BLOCKS + line("RK2", status=IN_PROGRESS))
    hold(config, "RK2")
    assert claiming.departing(config, "RK2", config.document("roadmap").entries) is None


def test_the_listing_counts_a_scope_and_the_json_carries_it(tmp_path, capsys):
    # Counted in `claims` and named by `claim <id>`: that listing ranks nothing and offers
    # nothing, and four paths a row would make it the other command.
    project(tmp_path, BLOCKS + line("RK2"))
    config = Config.discover(tmp_path)
    take(config)
    claiming.scope(config, "RK2", ["src/a.py", "src/b.py"])
    assert main(["-C", str(tmp_path), "claims"]) == EXIT_OK
    assert "2 path(s)" in capsys.readouterr().out
    assert main(["-C", str(tmp_path), "claims", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["claims"][0]["paths"] == ["src/a.py", "src/b.py"]
