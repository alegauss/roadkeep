"""Reaching a shipped decision's reasoning (RK31).

The load-bearing test is `test_the_pointer_survives_a_history_rewrite`: a stored hash
would be wrong after a squash, an amend or a rebase, and would look exactly as valid as
a live one. Deriving the pointer is what makes that failure mode impossible rather than
unlikely, so the test rewrites history on purpose and asserts the answer still resolves.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.history import (
    HistoryUnavailable,
    commits_touching,
    gaps,
    git_available,
    origin_of,
    searchable,
)
from roadkeep.schema import DESIGNED, SHIPPED

HERE = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(not git_available(), reason="git is not on PATH")


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return result.stdout


def repo(tmp_path: Path) -> Config:
    """A real git repository with a roadmap, a ledger and a config."""
    git(tmp_path, "init", "--quiet")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text("## Block A — The model\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("## Block A — The model\n", encoding="utf-8")
    commit(tmp_path, "chore: bootstrap")
    return Config.discover(tmp_path)


def commit(root: Path, message: str) -> str:
    git(root, "add", "-A")
    git(root, "commit", "--quiet", "-m", message)
    return git(root, "rev-parse", "HEAD").strip()


def append(path: Path, text: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


def propose(config: Config, task_id: str, message: str) -> str:
    append(
        config.path("roadmap"),
        f"- {DESIGNED} **{task_id}** (deps: —) **A symptom** — a reason. → §{task_id}\n",
    )
    return commit(config.root, message)


def ship(config: Config, task_id: str, message: str) -> str:
    roadmap = config.path("roadmap")
    kept = [
        line
        for line in roadmap.read_text(encoding="utf-8").splitlines(keepends=True)
        if f"**{task_id}**" not in line
    ]
    roadmap.write_text("".join(kept), encoding="utf-8")
    append(
        config.path("changelog"),
        f"- {SHIPPED} **{task_id}** **A symptom** — a reason.\n",
    )
    return commit(config.root, message)


# -- resolving ---------------------------------------------------------------


def test_a_task_resolves_to_the_commits_that_proposed_and_shipped_it(tmp_path):
    config = repo(tmp_path)
    proposed = propose(config, "RK1", "docs: add RK1")
    shipped = ship(config, "RK1", "feat: the thing (RK1)")

    origin = origin_of(config, "RK1")
    assert origin.proposed_in.sha == proposed
    assert origin.shipped_in.sha == shipped
    assert origin.shipped_in.subject == "feat: the thing (RK1)"


def test_the_reasoning_comes_from_the_commit_body_not_the_ledger(tmp_path):
    config = repo(tmp_path)
    propose(config, "RK1", "docs: add RK1")
    ship(config, "RK1", "feat: the thing (RK1)\n\nBecause the alternative rots.\n")

    origin = origin_of(config, "RK1")
    # The one question an unfamiliar repository answers worst, in one lookup.
    assert "Because the alternative rots." in origin.shipped_in.reasoning


def test_an_unshipped_task_has_a_proposal_and_no_shipping_commit(tmp_path):
    config = repo(tmp_path)
    propose(config, "RK1", "docs: add RK1")
    origin = origin_of(config, "RK1")
    assert origin.proposed_in is not None
    assert origin.shipped_in is None


def test_an_unknown_id_resolves_to_nothing_rather_than_guessing(tmp_path):
    config = repo(tmp_path)
    propose(config, "RK1", "docs: add RK1")
    origin = origin_of(config, "RK77")
    assert (origin.proposed_in, origin.shipped_in) == (None, None)


def test_the_bold_id_is_the_needle_so_RK1_does_not_match_RK10(tmp_path):
    config = repo(tmp_path)
    propose(config, "RK10", "docs: add RK10")
    ship(config, "RK10", "feat: ten (RK10)")
    assert origin_of(config, "RK1").proposed_in is None
    assert origin_of(config, "RK10").shipped_in.subject == "feat: ten (RK10)"


def test_the_first_commit_wins_when_a_line_is_edited_later(tmp_path):
    config = repo(tmp_path)
    proposed = propose(config, "RK1", "docs: add RK1")
    roadmap = config.path("roadmap")
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8").replace("a reason.", "a better reason."),
        encoding="utf-8",
    )
    commit(config.root, "docs: reword RK1")
    # Where the task entered, not where it was last touched.
    assert origin_of(config, "RK1").proposed_in.sha == proposed


# -- the objection this design answers (RK33) --------------------------------


def test_the_pointer_survives_a_history_rewrite(tmp_path):
    config = repo(tmp_path)
    propose(config, "RK1", "docs: add RK1")
    original = ship(config, "RK1", "feat: the thing (RK1)")

    git(config.root, "commit", "--quiet", "--amend", "-m", "feat: the thing, reworded (RK1)")
    rewritten = git(config.root, "rev-parse", "HEAD").strip()
    assert rewritten != original  # the hash a stored pointer would have recorded

    origin = origin_of(config, "RK1")
    assert origin.shipped_in.sha == rewritten
    assert origin.shipped_in.subject == "feat: the thing, reworded (RK1)"


def test_a_squash_keeps_the_reasoning_reachable_and_loses_only_the_proposal(tmp_path):
    config = repo(tmp_path)
    propose(config, "RK1", "docs: add RK1")
    ship(config, "RK1", "feat: the thing (RK1)")
    base = git(config.root, "rev-list", "--max-parents=0", "HEAD").strip()

    git(config.root, "reset", "--soft", base)
    squashed = commit(config.root, "feat: everything at once (RK1)")

    origin = origin_of(config, "RK1")
    # The squash left the roadmap exactly as it found it, so there is no diff in which
    # the proposal could be found — the history lost that fact, not the lookup. What
    # matters survives: the commit carrying the reasoning still resolves.
    assert origin.proposed_in is None
    assert origin.shipped_in.sha == squashed


# -- when there is no history ------------------------------------------------


def test_a_directory_that_is_not_a_repository_says_so(tmp_path):
    config = Config.default(tmp_path)
    with pytest.raises(HistoryUnavailable):
        commits_touching(tmp_path, "**RK1**")
    assert config.source is None


# -- this repository ---------------------------------------------------------


def test_this_repository_can_reach_its_own_first_decision():
    config = Config.discover(HERE)
    origin = origin_of(config, "RK1")
    # RK1 shipped before this module existed: deriving the pointer works
    # retroactively, which storing one never could.
    assert origin.shipped_in is not None
    assert "RK1" in origin.shipped_in.subject
    assert origin.proposed_in is not None


# -- the command -------------------------------------------------------------


def test_the_command_prints_both_commits(tmp_path, capsys):
    config = repo(tmp_path)
    propose(config, "RK1", "docs: add RK1")
    ship(config, "RK1", "feat: the thing (RK1)")
    assert main(["-C", str(tmp_path), "origin", "RK1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "proposed" in out and "shipped" in out and "feat: the thing (RK1)" in out


def test_why_prints_the_message_the_ledger_dropped(tmp_path, capsys):
    config = repo(tmp_path)
    propose(config, "RK1", "docs: add RK1")
    ship(config, "RK1", "feat: the thing (RK1)\n\nThe reasoning lives here.\n")
    assert main(["-C", str(tmp_path), "origin", "RK1", "--why"]) == EXIT_OK
    assert "The reasoning lives here." in capsys.readouterr().out


def test_json_carries_both_shas_and_the_reasoning(tmp_path, capsys):
    config = repo(tmp_path)
    propose(config, "RK1", "docs: add RK1")
    ship(config, "RK1", "feat: the thing (RK1)\n\nWhy.\n")
    assert main(["-C", str(tmp_path), "origin", "RK1", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "RK1"
    assert len(payload["shipped_in"]["sha"]) == 40
    assert "Why." in payload["shipped_in"]["reasoning"]
    assert payload["proposed_in"]["subject"] == "docs: add RK1"


def test_a_task_nothing_mentions_is_reported_as_such(tmp_path, capsys):
    repo(tmp_path)
    assert main(["-C", str(tmp_path), "origin", "RK77"]) == EXIT_OK
    assert "nothing in history" in capsys.readouterr().out


def test_no_repository_exits_two_with_the_reason(tmp_path, capsys):
    (tmp_path / "roadkeep.toml").write_text('prefix = "RK"\n', encoding="utf-8")
    assert main(["-C", str(tmp_path), "origin", "RK1"]) == EXIT_USAGE
    assert "no history" in capsys.readouterr().err


# -- the two ways a gap holds no commit (RK95) -------------------------------


def drop(config: Config, task_id: str, message: str) -> str:
    """Take a line out of the roadmap and record it nowhere — the hand-edit RK32 is about."""
    roadmap = config.path("roadmap")
    roadmap.write_text(
        "".join(
            line
            for line in roadmap.read_text(encoding="utf-8").splitlines(keepends=True)
            if f"**{task_id}**" not in line
        ),
        encoding="utf-8",
    )
    return commit(config.root, message)


def test_a_number_nothing_ever_carried_is_never_carried_and_not_unresolvable(tmp_path):
    """RK80 in this repository's own backlog: six findings were filed under seven numbers.
    No commit will ever mention it, and reporting that as 'history cannot answer' sends a
    reader to look for a decision that was never taken."""
    config = repo(tmp_path)
    propose(config, "RK1", "docs: add RK1")
    propose(config, "RK3", "docs: add RK3")  # RK2 was skipped when these were allocated
    found = gaps(Config.discover(tmp_path))
    assert [gap.id for gap in found] == ["RK2"]
    assert found[0].never_carried and not found[0].resolved


def test_a_line_that_left_resolves_and_is_not_called_never_carried(tmp_path):
    config = repo(tmp_path)
    propose(config, "RK1", "docs: add RK1")
    propose(config, "RK2", "docs: add RK2")
    propose(config, "RK3", "docs: add RK3")  # a gap is only a gap below the highest id
    drop(config, "RK2", "docs: RK2 was a duplicate of RK1")
    found = gaps(Config.discover(tmp_path))
    assert [gap.id for gap in found] == ["RK2"]
    assert found[0].resolved and not found[0].never_carried
    assert found[0].removed_in.subject == "docs: RK2 was a duplicate of RK1"


def test_a_shallow_clone_says_unresolvable_because_it_cannot_know(tmp_path):
    """The distinction is a property of the checkout, not of the id: the same backlog in a
    clone that cannot reach its root commit must answer nothing rather than 'never'."""
    config = repo(tmp_path)
    propose(config, "RK1", "docs: add RK1")
    propose(config, "RK3", "docs: add RK3")
    shallow = tmp_path.parent / f"{tmp_path.name}-shallow"
    git(tmp_path, "clone", "--quiet", "--depth", "1", tmp_path.as_uri(), str(shallow))
    assert not searchable(Config.discover(shallow))
    found = gaps(Config.discover(shallow))
    assert [gap.id for gap in found] == ["RK2"]
    assert not found[0].never_carried and not found[0].resolved


def test_a_directory_that_is_not_a_repository_is_not_searchable(tmp_path):
    (tmp_path / "roadkeep.toml").write_text('prefix = "RK"\n', encoding="utf-8")
    assert not searchable(Config.discover(tmp_path))


def test_the_command_names_the_two_answers_apart(tmp_path, capsys):
    config = repo(tmp_path)
    propose(config, "RK1", "docs: add RK1")
    propose(config, "RK3", "docs: add RK3")
    assert main(["-C", str(tmp_path), "gaps"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "RK2    never carried" in out and "unresolvable" not in out
    assert "1 gap(s), 0 resolved against history, 1 never carried" in out
