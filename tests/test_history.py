"""Reaching a shipped decision's reasoning (RK31).

The load-bearing test is `test_the_pointer_survives_a_history_rewrite`: a stored hash
would be wrong after a squash, an amend or a rebase, and would look exactly as valid as
a live one. Deriving the pointer is what makes that failure mode impossible rather than
unlikely, so the test rewrites history on purpose and asserts the answer still resolves.
"""

from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path

import pytest

from conftest import git, git_init, git_commit

from roadkeep import claiming
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.history import (
    HistoryUnavailable,
    anchors,
    commits_touching,
    carrying,
    dirty,
    families_of_block,
    gaps,
    doubled,
    git_available,
    next_child,
    next_family,
    numeral,
    origin_of,
    searchable,
    spell,
)
from roadkeep.provenance import invocation
from roadkeep.sections import AnchorRetired
from roadkeep.sections import add as add_section
from roadkeep.sections import move as move_section
from roadkeep.kernel.schema import DESIGNED, IN_PROGRESS, SHIPPED

HERE = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(not git_available(), reason="git is not on PATH")




def repo(tmp_path: Path) -> Config:
    """A real git repository with a roadmap, a ledger and a config."""
    git_init(tmp_path)
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text("## Block A — The model\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("## Block A — The model\n", encoding="utf-8")
    git_commit(tmp_path, "chore: bootstrap")
    return Config.discover(tmp_path)




def append(path: Path, text: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


def propose(config: Config, task_id: str, message: str) -> str:
    append(
        config.path("roadmap"),
        f"- {DESIGNED} **{task_id}** (deps: —) **A symptom** — a reason. → §{task_id}\n",
    )
    return git_commit(config.root, message)


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
    return git_commit(config.root, message)


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
    git_commit(config.root, "docs: reword RK1")
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
    squashed = git_commit(config.root, "feat: everything at once (RK1)")

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
    return git_commit(config.root, message)


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
    # The row and not the padding (RK1165): the column is sized to the widest label now.
    assert any(line.split()[:3] == ["RK2", "never", "carried"] for line in out.splitlines()), out
    assert "unresolvable" not in out
    assert "1 gap(s), 0 resolved against history, 1 never carried" in out


# -- the anchor a shipped line stops carrying (RK212) -------------------------


def prose(config: Config, name: str = "IMPROVEMENTS.md") -> Path:
    """Give the project a rationale file, which `repo` does not declare."""
    path = config.root / name
    path.write_text("# Improvements\n\n## Block A — The model\n", encoding="utf-8")
    with (config.root / "roadkeep.toml").open("a", encoding="utf-8") as handle:
        handle.write(f'improvements = "{name}"\n')
    return path


def design(config: Config, heading: str, message: str) -> str:
    append(config.path("improvements"), f"\n{heading}\n\nThe reasoning.\n")
    return git_commit(config.root, message)


def unwrite(config: Config, heading: str, message: str) -> str:
    path = config.path("improvements")
    kept = [
        line
        for line in path.read_text(encoding="utf-8").splitlines(keepends=True)
        if line.rstrip("\n") != heading
    ]
    path.write_text("".join(kept), encoding="utf-8")
    return git_commit(config.root, message)


def test_a_citation_of_a_shipped_design_resolves_to_the_commit_that_took_it(tmp_path, capsys):
    """The half of RK206 a verb cannot reach.

    `ship` names the sections left citing what it deleted, at the moment it deletes it. A
    reader meeting `§RK1` a year later has no such moment and the files hold no answer:
    `as_ledger` keeps no pointer, so nothing records which anchor a shipped design had.
    """
    config = repo(tmp_path)
    prose(config)
    config = Config.discover(tmp_path)
    design(config, "### §RK1 A first design", "docs: file the design")
    unwrite(config, "### §RK1 A first design", "feat: the thing works now (RK1)")

    assert main(["-C", str(tmp_path), "origin", "§RK1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "docs: file the design" in out
    assert "feat: the thing works now (RK1)" in out


def test_an_anchor_nobody_ever_wrote_is_a_different_answer(tmp_path, capsys):
    """RK95's split, one unit along: a history that was searched and never saw the address
    says nobody wrote it, which is what a typo looks like — and is not the same answer as a
    history that could not be searched."""
    config = repo(tmp_path)
    prose(config)
    config = Config.discover(tmp_path)
    design(config, "### §RK1 A first design", "docs: file the design")

    assert main(["-C", str(tmp_path), "origin", "§RK9"]) == EXIT_OK
    assert "nothing ever wrote it" in capsys.readouterr().out


def test_a_section_that_is_still_there_is_not_reported_as_removed(tmp_path, capsys):
    """The commit that last touched a heading is only a removal if the heading is gone: a
    live section has one too, and calling that a deletion would invent one nobody made."""
    config = repo(tmp_path)
    prose(config)
    config = Config.discover(tmp_path)
    design(config, "### §RK1 A first design", "docs: file the design")

    assert main(["-C", str(tmp_path), "origin", "§RK1"]) == EXIT_OK
    assert "the section is still there" in capsys.readouterr().out


def test_the_heading_is_searched_and_not_the_citation(tmp_path, capsys):
    """The needle that made the first attempt wrong.

    `§RK1` alone matches every commit that touched somebody's *prose* about it, so the last
    one is whatever commit deleted a sentence mentioning it — which is how this first
    answered "§RK15 was removed by RK206", a ship that never went near the section.
    """
    config = repo(tmp_path)
    prose(config)
    config = Config.discover(tmp_path)
    design(config, "### §RK1 A first design", "docs: file the design")
    removed = unwrite(config, "### §RK1 A first design", "feat: the thing works (RK1)")
    # A later commit whose diff mentions the anchor in prose, and removes that mention.
    design(config, "### §RK2 A second design", "docs: cite it — §RK1 said why")
    unwrite(config, "### §RK2 A second design", "feat: the second thing (RK2)")

    assert main(["-C", str(tmp_path), "origin", "§RK1", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["removed"]["sha"] == removed


def test_an_outline_heading_without_the_sigil_is_found_too(tmp_path, capsys):
    """Two live outline projects disagree about the sigil in a heading — Shio and Turing
    write `### VIII.1`, claude-tray writes `### §I.1` and `### XVIII.12` in one file — so a
    needle that admitted one of them would answer "nobody ever wrote it" for the other."""
    config = repo(tmp_path)
    prose(config)
    with (config.root / "roadkeep.toml").open("a", encoding="utf-8") as handle:
        handle.write('\n')
    (config.root / "roadkeep.toml").write_text(
        (config.root / "roadkeep.toml").read_text(encoding="utf-8").replace(
            'prefix = "RK"', 'prefix = "RK"\nref_scheme = "outline"'
        ),
        encoding="utf-8",
    )
    config = Config.discover(tmp_path)
    design(config, "### XVIII.12 A design with no sigil", "docs: file it")
    unwrite(config, "### XVIII.12 A design with no sigil", "feat: it works (RK1)")

    assert main(["-C", str(tmp_path), "origin", "§XVIII.12"]) == EXIT_OK
    assert "feat: it works (RK1)" in capsys.readouterr().out


def test_a_prefix_of_an_anchor_does_not_answer_for_it(tmp_path, capsys):
    config = repo(tmp_path)
    prose(config)
    config = Config.discover(tmp_path)
    design(config, "### §RK12 A twelfth design", "docs: file the twelfth")

    assert main(["-C", str(tmp_path), "origin", "§RK1"]) == EXIT_OK
    assert "nothing ever wrote it" in capsys.readouterr().out


# -- the addresses history spent (RK247) -------------------------------------


def outlined(tmp_path: Path) -> Config:
    """A project addressing its prose by an outline, which is the only scheme this asks of."""
    config = repo(tmp_path)
    prose(config)
    (config.root / "roadkeep.toml").write_text(
        (config.root / "roadkeep.toml")
        .read_text(encoding="utf-8")
        .replace('prefix = "RK"', 'prefix = "RK"\nref_scheme = "outline"'),
        encoding="utf-8",
    )
    return Config.discover(tmp_path)


def test_a_retired_anchor_is_named_where_the_file_says_nothing(tmp_path):
    # The symptom: `section add` lists what exists, so after a fully-shipped family that is
    # none of them and the next number looks like .1 — while the entries citing .1 are there.
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 A first design", "docs: file it")
    design(config, "### XXXVII.2 A second design", "docs: file the second")
    unwrite(config, "### XXXVII.1 A first design", "feat: the first thing (RK1)")

    found = {one.anchor: one.live for one in anchors(config, "improvements", "XXXVII")}
    assert found == {"XXXVII.1": False, "XXXVII.2": True}


def test_the_next_child_is_one_past_the_highest_ever_used(tmp_path):
    # One past the highest **ever**, not one past the highest surviving, which is often none.
    config = outlined(tmp_path)
    for number in (1, 2, 3):
        design(config, f"### XXXVII.{number} A design", f"docs: file {number}")
    for number in (1, 2, 3):
        unwrite(config, f"### XXXVII.{number} A design", f"feat: it works ({number})")

    found = anchors(config, "improvements", "XXXVII")
    assert [one.live for one in found] == [False, False, False]
    assert next_child(found, "XXXVII") == "XXXVII.4"


def test_an_address_removed_before_it_was_ever_added_here_is_still_spent(tmp_path):
    # An anchor written before the clone's history appears only as a removed line, and that
    # is exactly the retired address this exists to name.
    config = outlined(tmp_path)
    path = config.path("improvements")
    path.write_text(
        path.read_text(encoding="utf-8") + "\n### XL.7 An older design\n\nProse.\n",
        encoding="utf-8",
    )
    git_commit(config.root, "docs: import the outline")
    unwrite(config, "### XL.7 An older design", "feat: it shipped")

    assert [one.anchor for one in anchors(config, "improvements", "XL")] == ["XL.7"]


def test_reusing_a_retired_address_is_refused_and_the_free_one_is_named(tmp_path):
    # The silent rewrite: the ledger entries citing §XXXVII.1 would point at this prose.
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 A first design", "docs: file it")
    unwrite(config, "### XXXVII.1 A first design", "feat: it works (RK1)")
    config = Config.discover(tmp_path)

    with pytest.raises(AnchorRetired) as raised:
        add_section(config, "improvements", "XXXVII.1", "A reopened design", "Prose.")
    assert raised.value.free == "XXXVII.2"
    assert "still there" in str(raised.value)


def test_a_move_onto_a_retired_address_is_refused_by_the_same_read(tmp_path):
    # RK377 takes every refusal `add` computes about a destination, and this is the one only
    # history can answer: the repair verb reaching for "the next free number" would otherwise
    # re-point every ledger entry citing §XXXVII.1 at prose about something else.
    config = outlined(tmp_path)
    design(config, "## XXXVII The family", "docs: open the family")
    design(config, "### XXXVII.1 A first design", "docs: file it")
    design(config, "### XXXVII.2 A second design", "docs: file the second")
    unwrite(config, "### XXXVII.1 A first design", "feat: it works (RK1)")
    config = Config.discover(tmp_path)

    with pytest.raises(AnchorRetired) as raised:
        move_section(config, "improvements", "XXXVII.2", "XXXVII.1")
    assert raised.value.anchor == "XXXVII.1"


def test_an_address_nothing_ever_declared_is_written(tmp_path):
    # The refusal is about reuse and never about the scheme: a fresh address still writes.
    config = outlined(tmp_path)
    design(config, "## XXXVII The family", "docs: open the family")
    design(config, "### XXXVII.1 A first design", "docs: file it")
    unwrite(config, "### XXXVII.1 A first design", "feat: it works (RK1)")
    config = Config.discover(tmp_path)

    out = add_section(config, "improvements", "XXXVII.2", "A design", "Prose.")
    document, section = out.document, out.section
    assert section.anchor == "XXXVII.2" and document is not None


def test_an_id_scheme_project_is_not_asked_twice(tmp_path):
    # Under the id scheme the address is the id, so reuse is `add`'s refusal (RK4) and the
    # retired ones are every shipped task — a second check on a closed question.
    config = repo(tmp_path)
    prose(config)
    config = Config.discover(tmp_path)
    propose(config, "RK1", "docs: propose it")
    design(config, "### §RK1 A design", "docs: file it")
    unwrite(config, "### §RK1 A design", "feat: it works (RK1)")
    propose(config, "RK2", "docs: propose the second")
    config = Config.discover(tmp_path)

    out = add_section(config, "improvements", "RK2", "A design", "Prose.")
    document, section = out.document, out.section
    assert section.anchor == "RK2" and document is not None


def test_the_command_summarises_by_family_and_lists_one_on_request(tmp_path, capsys):
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 A first design", "docs: file it")
    unwrite(config, "### XXXVII.1 A first design", "feat: it works (RK1)")

    assert main(["-C", str(tmp_path), "anchors"]) == EXIT_OK
    summary = capsys.readouterr().out
    assert "XXXVII" in summary and "1 retired" in summary
    assert "XXXVII.1" not in summary

    assert main(["-C", str(tmp_path), "anchors", "--family", "XXXVII", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["next"] == "XXXVII.2"
    assert [one["anchor"] for one in payload["anchors"]] == ["XXXVII.1"]


def test_a_project_with_no_prose_file_is_a_usage_error_and_not_a_crash(tmp_path):
    repo(tmp_path)
    assert main(["-C", str(tmp_path), "anchors"]) == EXIT_USAGE


# -- what a commit would carry (RK280) ---------------------------------------


def test_the_dirty_listing_holds_every_kind_of_change_a_commit_would_take(tmp_path):
    # `git add -A` is what the scope is subtracted from, so this has to be exactly that
    # list: an untracked file is somebody's new test, and omitting it would answer "clean"
    # about the tree that carried the defect this exists for.
    config = repo(tmp_path)
    (tmp_path / "ROADMAP.md").write_text("## Block A — Changed\n", encoding="utf-8")
    (tmp_path / "new.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "staged.py").write_text("y = 2\n", encoding="utf-8")
    git(tmp_path, "add", "staged.py")
    assert dirty(config) == {"ROADMAP.md", "new.py", "staged.py"}


def test_a_rename_arrives_as_both_of_its_ends(tmp_path):
    # `status --porcelain -z` spends two NUL-separated fields on a rename, so a naive split
    # reads the origin as a record and its first two characters as a status code.
    config = repo(tmp_path)
    git(tmp_path, "mv", "CHANGELOG.md", "LEDGER.md")
    assert dirty(config) == {"CHANGELOG.md", "LEDGER.md"}


def test_a_clean_tree_says_nothing(tmp_path):
    assert dirty(repo(tmp_path)) == frozenset()


def test_a_checkout_git_cannot_answer_for_reports_nothing_rather_than_refusing(tmp_path):
    # The rule every reader here keeps: no git is a question this answers nothing about.
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n', encoding="utf-8"
    )
    (tmp_path / "ROADMAP.md").write_text("## Block A — The model\n", encoding="utf-8")
    assert dirty(Config.discover(tmp_path)) == frozenset()


# -- the caller a scope did not have, at the commit (RK294) -------------------


def test_a_ship_names_what_the_tree_holds_that_its_claim_does_not(tmp_path, capsys):
    # RK280 gave the claim a scope and `claim <id>` the read, and left it with no caller: the
    # declaration was asked for in prose, at the one moment the author is already finishing.
    config = repo(tmp_path)
    append(
        config.path("roadmap"),
        f"- {IN_PROGRESS} **RK2** (deps: —) **A symptom** — a reason.\n",
    )
    git_commit(tmp_path, "chore: a line under way")
    try:
        claiming.follow(tmp_path, "RK2", IN_PROGRESS, config.document("roadmap").entries)
        claiming.scope(config, "RK2", ["mine.py"])
        (tmp_path / "mine.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "stray.py").write_text("y = 2\n", encoding="utf-8")
        assert main(["-C", str(tmp_path), "ship", "RK2", "--why", "it works now."]) == EXIT_OK
        out = capsys.readouterr().out
        assert "loose    stray.py  (no claim names it)" in out
        # And the scope itself, as the command that stages it (RK298): the ship released the
        # claim, so `claim RK2 --porcelain` now refuses and the `status RK2 🛠` it names is
        # refused too — this is the last moment the answer exists.
        assert "stage    git add -- mine.py" in out
    finally:
        claiming.path(tmp_path).unlink(missing_ok=True)


def test_the_command_marks_a_declared_path_that_would_stage_nothing(tmp_path, capsys):
    # The comparison the read already had the facts for and did not make (RK295): today the
    # mistyped name printed as an ordinary line and the real file printed two lines below
    # under `loose`, where the eye reads it as somebody else's.
    config = repo(tmp_path)
    append(
        config.path("roadmap"),
        f"- {IN_PROGRESS} **RK2** (deps: —) **A symptom** — a reason.\n",
    )
    git_commit(tmp_path, "chore: a line under way")
    try:
        claiming.follow(tmp_path, "RK2", IN_PROGRESS, config.document("roadmap").entries)
        (tmp_path / "mine.py").write_text("x = 1\n", encoding="utf-8")
        at = ["-C", str(tmp_path), "claim", "RK2"]
        assert main([*at, "--path", "mnie.py", "--path", "ROADMAP.md"]) == EXIT_OK
        capsys.readouterr()
        assert main(at) == EXIT_OK
        out = capsys.readouterr().out
        assert "mine     mnie.py  (stages nothing right now)" in out
        # The tracked file nothing has touched yet is not a typo, and the real file is still
        # reported for what it is: a change no claim names.
        assert "mine     ROADMAP.md\n" in out
        assert "loose    mine.py  (no claim names it)" in out
    finally:
        claiming.path(tmp_path).unlink(missing_ok=True)


def test_the_verb_that_answered_that_before_the_ship_no_longer_does(tmp_path, capsys):
    # The whole of RK298: the order the work happens in is claim, code, `ship`, commit, and
    # the ship releases the claim — so the answer has to arrive in the ship's own output.
    config = repo(tmp_path)
    append(
        config.path("roadmap"),
        f"- {IN_PROGRESS} **RK2** (deps: —) **A symptom** — a reason.\n",
    )
    git_commit(tmp_path, "chore: a line under way")
    try:
        claiming.follow(tmp_path, "RK2", IN_PROGRESS, config.document("roadmap").entries)
        claiming.scope(config, "RK2", ["mine.py"])
        assert main(["-C", str(tmp_path), "ship", "RK2", "--why", "it works now."]) == EXIT_OK
        capsys.readouterr()
        assert main(["-C", str(tmp_path), "claim", "RK2", "--porcelain"]) == EXIT_USAGE
        assert "no live claim on RK2" in capsys.readouterr().err
    finally:
        claiming.path(tmp_path).unlink(missing_ok=True)


def test_a_path_holding_a_space_survives_the_staging_line(tmp_path, capsys):
    # A scope is declared verbatim, so it may hold a blank — and a `git add --` line that
    # split one in two would stage two files that do not exist.
    config = repo(tmp_path)
    append(
        config.path("roadmap"),
        f"- {IN_PROGRESS} **RK2** (deps: —) **A symptom** — a reason.\n",
    )
    git_commit(tmp_path, "chore: a line under way")
    try:
        claiming.follow(tmp_path, "RK2", IN_PROGRESS, config.document("roadmap").entries)
        claiming.scope(config, "RK2", ["a file.py", "plain.py"])
        assert main(["-C", str(tmp_path), "ship", "RK2", "--why", "it works now."]) == EXIT_OK
        assert 'stage    git add -- "a file.py" plain.py' in capsys.readouterr().out
    finally:
        claiming.path(tmp_path).unlink(missing_ok=True)


def test_a_ship_in_a_project_no_claim_spoke_for_reports_nothing(tmp_path, capsys):
    # Every project that has not adopted a scope. There is nothing to subtract the tree from,
    # so the whole answer would be `git status` under a heading claiming to have read it.
    config = repo(tmp_path)
    append(
        config.path("roadmap"),
        "- \U0001f4cb **RK2** (deps: —) **A symptom** — a reason.\n",
    )
    git_commit(tmp_path, "chore: a line")
    (tmp_path / "stray.py").write_text("y = 2\n", encoding="utf-8")
    assert main(["-C", str(tmp_path), "ship", "RK2", "--why", "it works now."]) == EXIT_OK
    assert "loose" not in capsys.readouterr().out


# -- the half of the commit no author declares (RK309) ------------------------


def test_the_staging_line_holds_the_governed_files_the_ship_itself_wrote(tmp_path, capsys):
    # Every scope named the roadmap and the ledger by hand, and neither was a judgement: they
    # are what the departure just wrote, which the write already answers.
    config = repo(tmp_path)
    append(
        config.path("roadmap"),
        f"- {IN_PROGRESS} **RK2** (deps: —) **A symptom** — a reason.\n",
    )
    git_commit(tmp_path, "chore: a line under way")
    try:
        claiming.follow(tmp_path, "RK2", IN_PROGRESS, config.document("roadmap").entries)
        claiming.scope(config, "RK2", ["mine.py"])  # the code, and nothing the tool writes
        (tmp_path / "mine.py").write_text("x = 1\n", encoding="utf-8")
        assert main(["-C", str(tmp_path), "ship", "RK2", "--why", "it works now."]) == EXIT_OK
        out = capsys.readouterr().out
        staged = next(one for one in out.splitlines() if "stage    git add --" in one)
        # Declared first and verbatim, then what the write record holds — relative, because the
        # caller pastes the line at the repository root.
        assert staged.split("--", 1)[1].split() == ["mine.py", "CHANGELOG.md", "ROADMAP.md"]
        # And never twice: a path this command wrote is not a change no claim accounts for, so
        # answering both in one output would be the tool contradicting itself.
        assert "loose" not in out
    finally:
        claiming.path(tmp_path).unlink(missing_ok=True)


def test_the_declaration_and_the_record_stay_two_fields(tmp_path, capsys):
    # A client that merged them would read back a scope this tool never received: `mine` is
    # what the holder said (RK280) and `wrote` is what the departure did.
    config = repo(tmp_path)
    append(
        config.path("roadmap"),
        f"- {IN_PROGRESS} **RK2** (deps: —) **A symptom** — a reason.\n",
    )
    git_commit(tmp_path, "chore: a line under way")
    try:
        claiming.follow(tmp_path, "RK2", IN_PROGRESS, config.document("roadmap").entries)
        claiming.scope(config, "RK2", ["mine.py"])
        (tmp_path / "mine.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "stray.py").write_text("y = 2\n", encoding="utf-8")
        at = ["-C", str(tmp_path), "ship", "RK2", "--why", "it works now.", "--json"]
        assert main(at) == EXIT_OK
        scope = json.loads(capsys.readouterr().out)["scope"]
        assert scope["mine"] == ["mine.py"]
        assert scope["wrote"] == ["CHANGELOG.md", "ROADMAP.md"]
        # A change neither the holder declared nor this command wrote is still reported.
        assert scope["unclaimed"] == ["stray.py"]
    finally:
        claiming.path(tmp_path).unlink(missing_ok=True)


def test_a_retirement_answers_for_its_own_writes_as_a_ship_does(tmp_path, capsys):
    # A retirement is committed exactly as a ship is and releases the same claim, so the half
    # of the commit it wrote is the same fact there.
    config = repo(tmp_path)
    append(
        config.path("roadmap"),
        f"- {IN_PROGRESS} **RK2** (deps: —) **A symptom** — a reason.\n",
    )
    git_commit(tmp_path, "chore: a line under way")
    try:
        claiming.follow(tmp_path, "RK2", IN_PROGRESS, config.document("roadmap").entries)
        claiming.scope(config, "RK2", ["mine.py"])
        (tmp_path / "mine.py").write_text("x = 1\n", encoding="utf-8")
        at = ["-C", str(tmp_path), "retire", "RK2", "--reason", "the premise did not hold."]
        assert main(at) == EXIT_OK
        staged = next(
            one for one in capsys.readouterr().out.splitlines() if "stage    git add --" in one
        )
        assert staged.split("--", 1)[1].split() == ["mine.py", "CHANGELOG.md", "ROADMAP.md"]
    finally:
        claiming.path(tmp_path).unlink(missing_ok=True)


def test_a_ship_no_claim_spoke_for_still_says_what_it_wrote(tmp_path, capsys):
    """The other way round since RK1130, and deliberately. This asserted silence on the
    argument that *the record is not a scope* — true, and it is the three lists below the
    staging line that need a claim to mean anything. The line itself is a fact about what this
    transaction wrote, which is why RK1129 has `add` print it on a project with no claims at
    all; a `ship` that stayed quiet was the same tool answering one question two ways, on the
    write with the most files in it and the one whose commit is hardest to compose."""
    config = repo(tmp_path)
    append(
        config.path("roadmap"),
        f"- {DESIGNED} **RK2** (deps: —) **A symptom** — a reason.\n",
    )
    git_commit(tmp_path, "chore: a line")
    assert main(["-C", str(tmp_path), "ship", "RK2", "--why", "it works now."]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "stage    git add --" in printed
    # And still nothing that needs a claim to be true: no scope spoke, so no path is anybody's.
    assert "loose" not in printed and "theirs" not in printed


# -- the next family, and the order that lets a reader check it (RK293) --------


def test_a_numeral_is_read_as_the_number_it_spells_and_a_letter_is_not():
    # Arithmetic, not prose (L4): reading `IX` is what a listing has to do to be scannable.
    assert numeral("IX") == ("roman", 9) and numeral("XXXVII") == ("roman", 37)
    assert numeral("0") == ("decimal", 0) and numeral("12") == ("decimal", 12)
    # Strict: a permissive reader would order the file by a spelling nobody wrote.
    assert numeral("A") is None and numeral("IIII") is None and numeral("IL") is None
    assert numeral("") is None and numeral("RK12") is None


def test_a_numeral_reads_back_as_the_spelling_it_came_from():
    for value in (1, 4, 9, 14, 40, 90, 400, 900, 1987):
        assert numeral(spell(value, "roman")) == ("roman", value)
    assert spell(7, "decimal") == "7"


def test_the_families_come_out_in_numeral_order_and_not_in_spelling_order(tmp_path):
    # The defect: sorted as strings, `IX` follows `IV` and precedes `V`, so the last row is
    # not the maximum and the listing cannot be scanned for a gap.
    config = outlined(tmp_path)
    for family in ("IV", "V", "IX", "X"):
        design(config, f"### {family}.1 A design", f"docs: file {family}")

    order = [one.anchor for one in anchors(config, "improvements")]
    assert order == ["IV.1", "V.1", "IX.1", "X.1"]


def test_the_next_free_top_level_is_derived_and_not_read_off_the_tail(tmp_path):
    # The question one line up from `next_child`, and the normal case in a backlog organised
    # by theme: a block reused after its family shipped needs a new top-level.
    config = outlined(tmp_path)
    for family in ("IV", "IX", "V"):
        design(config, f"### {family}.1 A design", f"docs: file {family}")
    found = anchors(config, "improvements")
    assert next_family(found) == "X"
    # One past the highest **ever** used, exactly as `next_child` is: a shipped family does
    # not give its address back, and every entry that cited it still says so.
    unwrite(config, "### IX.1 A design", "feat: it works (RK1)")
    assert next_family(anchors(Config.discover(tmp_path), "improvements")) == "X"


def test_families_that_are_not_one_numbering_derive_no_next_at_all(tmp_path):
    # A guess printed beside a total reads exactly like a fact, so None is the answer.
    config = outlined(tmp_path)
    for family in ("A", "B"):
        design(config, f"### {family}.1 A design", f"docs: file {family}")
    assert next_family(anchors(config, "improvements")) is None


def test_a_letter_family_is_never_read_as_the_roman_number_it_could_spell(tmp_path):
    # `C` is 100 on a file numbered in Roman and a letter on one whose families are A to F,
    # and only the whole set says which — so the decision is made once, over the set.
    config = outlined(tmp_path)
    for family in ("A", "B", "C", "D"):
        design(config, f"### {family}.1 A design", f"docs: file {family}")
    assert [one.anchor for one in anchors(config, "improvements")] == [
        "A.1", "B.1", "C.1", "D.1"
    ]
    assert next_family(anchors(config, "improvements")) is None


def test_the_command_names_the_next_family_beside_the_totals(tmp_path, capsys):
    config = outlined(tmp_path)
    for family in ("IV", "IX"):
        design(config, f"### {family}.1 A design", f"docs: file {family}")

    assert main(["-C", str(tmp_path), "anchors"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "next     §X — no family ever used it" in printed
    # And the rows below it, in the order that lets a reader check the claim.
    assert printed.index("\n  IV ") < printed.index("\n  IX ")


def test_the_command_says_so_where_no_next_derives(tmp_path, capsys):
    config = outlined(tmp_path)
    design(config, "### A.1 A design", "docs: file it")
    assert main(["-C", str(tmp_path), "anchors"]) == EXIT_OK
    assert "not one numbering" in capsys.readouterr().out


def test_the_json_carries_the_next_family_beside_the_next_child(tmp_path, capsys):
    config = outlined(tmp_path)
    for family in ("IV", "IX"):
        design(config, f"### {family}.1 A design", f"docs: file {family}")

    assert main(["-C", str(tmp_path), "anchors", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    # One field and not two (RK346): the free top-level is asked per namespace, and a project
    # declaring no `[refs]` is the one row whose namespace is null.
    assert payload["next_families"] == [{"namespace": None, "next": "X"}]
    assert "next_family" not in payload and payload["next"] is None
    assert [one["family"] for one in payload["families"]] == ["IV", "IX"]
    # Narrowed to one family, the question is the child's again and the top-level is not asked.
    assert main(["-C", str(tmp_path), "anchors", "--family", "IX", "--json"]) == EXIT_OK
    narrowed = json.loads(capsys.readouterr().out)
    assert narrowed["next"] == "IX.2" and narrowed["next_families"] == []


def test_the_json_states_the_namespace_of_every_free_top_level_it_answers(tmp_path, capsys):
    # RK346: the older field answered for the unprefixed namespace alone, so on a project
    # whose roles each declare one it named a namespace that no longer exists — and on one
    # that declares a single `[refs]` it was right about the other by coincidence. A row
    # carries its own namespace, which is the one reading that cannot be two.
    config = outlined(tmp_path)
    design(config, "### A.1 A design", "docs: file it")
    assert main(["-C", str(tmp_path), "anchors", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    # `next` is null *inside* the row, which says which namespace derives nothing — where the
    # older field's null said only that something, somewhere, did not derive.
    assert payload["next_families"] == [{"namespace": None, "next": None}]


# -- the address book that read half the addresses (RK297) ---------------------


def two_files(tmp_path: Path) -> Config:
    """A project declaring both prose roles, which is where one outline spans two files."""
    config = outlined(tmp_path)
    (config.root / "STRATEGY.md").write_text(
        "# Strategy\n\n## Block A — The model\n", encoding="utf-8"
    )
    with (config.root / "roadkeep.toml").open("a", encoding="utf-8") as handle:
        handle.write('strategy = "STRATEGY.md"\n')
    git_commit(config.root, "docs: declare the plan")
    return Config.discover(tmp_path)


def plan(config: Config, heading: str, message: str) -> str:
    append(config.path("strategy"), f"\n{heading}\n\nThe reasoning.\n")
    return git_commit(config.root, message)


def test_the_addresses_are_the_projects_and_not_the_first_files(tmp_path):
    # The measured defect: nine families declared in both files, and for seven of them the
    # two answered differently about the next child — `IX.5` free where the other spent to
    # `IX.12`. The read made to avoid spending an address twice handed back a taken one.
    config = two_files(tmp_path)
    design(config, "### IX.1 A design", "docs: file the first")
    plan(config, "### IX.2 A plan", "docs: file the plan")
    plan(config, "### IX.3 A second plan", "docs: file the second")

    found = anchors(config, family="IX")
    assert [one.anchor for one in found] == ["IX.1", "IX.2", "IX.3"]
    assert next_child(found, "IX") == "IX.4"
    # And the narrower question still answers, for the caller that asked it.
    assert [one.anchor for one in anchors(config, "improvements", "IX")] == ["IX.1"]


def test_each_row_says_which_file_declared_it(tmp_path):
    config = two_files(tmp_path)
    design(config, "### IX.1 A design", "docs: file the first")
    plan(config, "### IX.2 A plan", "docs: file the plan")
    assert {one.anchor: one.role for one in anchors(config, family="IX")} == {
        "IX.1": "improvements",
        "IX.2": "strategy",
    }


def test_an_address_two_files_declare_is_named_rather_than_collapsed(tmp_path):
    # `lint` says this as `ref.ambiguous`, and a gate is not a question: by then both
    # headings exist and four verbs refuse to resolve between them.
    config = two_files(tmp_path)
    design(config, "### IX.1 A design", "docs: file it")
    plan(config, "### IX.1 A plan", "docs: file it there too")
    assert doubled(anchors(config)) == (("IX.1", ("improvements", "strategy")),)


def test_a_retired_address_in_both_files_is_two_histories_and_not_a_conflict(tmp_path):
    # Live only: two headings are the state a pointer cannot resolve against, and two
    # deletions are nothing to act on.
    config = two_files(tmp_path)
    design(config, "### IX.1 A design", "docs: file it")
    plan(config, "### IX.1 A plan", "docs: file it there too")
    unwrite(config, "### IX.1 A design", "feat: it shipped (RK1)")
    config = Config.discover(tmp_path)
    assert doubled(anchors(config)) == ()
    # Still spent, in both files, which is what keeps the next address free of it.
    assert next_child(anchors(config, family="IX"), "IX") == "IX.2"


def test_a_project_with_one_prose_file_answers_exactly_as_it_did(tmp_path):
    # The single-file project is every project until it declares a second, so nothing here
    # may cost it a row, a label or a different number.
    config = outlined(tmp_path)
    design(config, "### IX.1 A design", "docs: file it")
    assert anchors(config) == anchors(config, "improvements")


def test_the_command_reads_both_files_and_names_the_doubling(tmp_path, capsys):
    config = two_files(tmp_path)
    design(config, "### IX.1 A design", "docs: file it")
    plan(config, "### IX.1 A plan", "docs: file it there too")
    plan(config, "### IX.2 A second plan", "docs: file the second")

    assert main(["-C", str(tmp_path), "anchors"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "IMPROVEMENTS.md, STRATEGY.md" in printed
    assert "doubled  §IX.1 is declared by improvements and strategy" in printed
    # The family row names both files, because which one spent an address is what a reader
    # checks the number against.
    assert "(improvements, strategy)" in printed


def test_the_free_address_stays_the_projects_even_when_the_listing_is_narrowed(tmp_path, capsys):
    # `--role` is the narrower question and it narrows the *listing*: a `next` taken from one
    # file is the answer this read exists to stop somebody acting on.
    config = two_files(tmp_path)
    design(config, "### IX.1 A design", "docs: file it")
    for number in (2, 3):
        plan(config, f"### IX.{number} A plan", f"docs: file {number}")

    assert main(
        ["-C", str(tmp_path), "anchors", "--role", "improvements", "--family", "IX", "--json"]
    ) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert [one["anchor"] for one in payload["anchors"]] == ["IX.1"]
    assert payload["role"] == "improvements" and payload["next"] == "IX.4"


def test_a_write_is_refused_against_an_address_the_sibling_file_spent(tmp_path):
    # The consequence the read exists to prevent, at the door it reaches: taking the address
    # the other file retired is what writes the doubled anchor in the first place.
    config = two_files(tmp_path)
    plan(config, "### IX.1 A plan", "docs: file the plan")
    unwrite_in(config, "strategy", "### IX.1 A plan", "feat: it shipped (RK1)")
    config = Config.discover(tmp_path)
    with pytest.raises(AnchorRetired):
        add_section(config, "improvements", "IX.1", "A design", "Prose.")


def unwrite_in(config: Config, role: str, heading: str, message: str) -> str:
    path = config.path(role)
    kept = [
        line
        for line in path.read_text(encoding="utf-8").splitlines(keepends=True)
        if line.rstrip("\n") != heading
    ]
    path.write_text("".join(kept), encoding="utf-8")
    return git_commit(config.root, message)


# -- the family a block's prose lives under (RK312) ---------------------------


def outlined_blocks(tmp_path: Path) -> Config:
    """An outline project whose two blocks have prose under two different families."""
    config = outlined(tmp_path)
    append(config.path("roadmap"), "\n## Block Q — Serving\n\n")
    append(
        config.path("roadmap"),
        f"- {DESIGNED} **RK1** (deps: —) **A symptom** — a reason. → §XVII.1\n"
        f"- {DESIGNED} **RK2** (deps: —) **A symptom** — a reason. → §XVII.3\n",
    )
    append(config.path("roadmap"), "\n## Block R — Later\n\n")
    append(
        config.path("roadmap"),
        f"- {DESIGNED} **RK3** (deps: —) **A symptom** — a reason. → §XX.1\n",
    )
    for anchor in ("XVII.1", "XVII.3", "XX.1"):
        design(config, f"### {anchor} A design", f"docs: file {anchor}")
    return Config.discover(tmp_path)


def test_which_family_a_blocks_prose_lives_under_is_a_command(tmp_path):
    # Derivable from none before this: under an outline the prose file declares no block
    # heading, so the mapping came from globbing pointers per block by hand, four times.
    config = outlined_blocks(tmp_path)
    assert families_of_block(config, "Q") == ("XVII",)
    assert families_of_block(config, "R") == ("XX",)
    assert families_of_block(config, "A") == ()


def test_a_block_that_spans_two_families_answers_with_both(tmp_path):
    # A block reopened under a fresh top-level has two, and returning one would be the guess
    # this read exists to stop making.
    config = outlined_blocks(tmp_path)
    append(
        config.path("roadmap"),
        f"- {DESIGNED} **RK4** (deps: —) **A symptom** — a reason. → §XVII.5\n",
    )
    assert families_of_block(Config.discover(tmp_path), "R") == ("XX", "XVII")


def test_the_block_a_caller_knows_narrows_to_the_family_they_do_not(tmp_path, capsys):
    config = outlined_blocks(tmp_path)
    assert main(["-C", str(config.root), "anchors", "--block", "Q", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)

    assert payload["block"] == "Q" and payload["block_families"] == ["XVII"]
    # Narrowed exactly as `--family XVII` would have, which is the whole claim: the caller
    # names the address they have and the rest of the answer is unchanged.
    assert payload["family"] == "XVII"
    assert [one["anchor"] for one in payload["anchors"]] == ["XVII.1", "XVII.3"]
    assert payload["next"] == "XVII.4"


def test_two_families_are_reported_and_neither_is_picked(tmp_path, capsys):
    config = outlined_blocks(tmp_path)
    append(
        config.path("roadmap"),
        f"- {DESIGNED} **RK4** (deps: —) **A symptom** — a reason. → §XVII.5\n",
    )
    assert main(["-C", str(config.root), "anchors", "--block", "R"]) == EXIT_OK
    printed = capsys.readouterr().out

    assert "§XX, §XVII" in printed and "pick one" in printed


def test_a_block_and_a_family_together_ask_two_questions(tmp_path, capsys):
    config = outlined_blocks(tmp_path)
    assert (
        main(["-C", str(config.root), "anchors", "--block", "Q", "--family", "XX"])
        == EXIT_USAGE
    )
    assert "asks two questions" in capsys.readouterr().err


def test_a_block_whose_prose_has_not_started_says_so(tmp_path, capsys):
    config = outlined_blocks(tmp_path)
    assert main(["-C", str(config.root), "anchors", "--block", "A"]) == EXIT_USAGE
    err = capsys.readouterr().err
    assert "no open line in Block A carries a pointer" in err
    assert "next free one is where a new block starts" in err


def test_the_refusal_that_demands_a_ref_names_what_produces_one(tmp_path, capsys):
    # This project's own standard applied to itself: `--ref` is required, unguessable, and
    # wrong silently if the number picked is one some heading already spent.
    config = outlined_blocks(tmp_path)
    assert (
        main(
            [
                "-C",
                str(config.root),
                "add",
                "--block",
                "Q",
                "--symptom",
                "A symptom",
                "--why",
                "A reason.",
            ]
        )
        == EXIT_USAGE
    )
    err = capsys.readouterr().err
    # The rule survives, because a refusal that only says what to type teaches nobody why.
    assert "every task points at its rationale section" in err
    assert "Block Q's prose is under §XVII" in err and "§XVII.4 is free" in err
    assert "anchors --block Q" in err


def test_the_refusal_offers_the_call_and_the_call_is_the_one_that_works(tmp_path, capsys):
    """RK1149: the refusal had already done the work and handed it over as prose to retype.

    Measured on a project on the outline scheme: seven tasks filed, five refused first for
    exactly this, five retries carrying no new information. So the retry is **executed** here
    rather than matched — a printed command whose quoting is wrong is a command that runs as
    eight arguments, and this is the first door carrying the caller's own prose.
    """
    config = outlined_blocks(tmp_path)
    # The ledger has to declare the block before any `add` there can succeed, because the retry
    # is *run* below and a second refusal would prove nothing about the first one's quoting.
    assert main(["-C", str(config.root), "block", "add", "Q", "--title", "Serving"]) == EXIT_OK
    typed = [
        "-C", str(config.root), "add", "--block", "Q",
        "--symptom", "A symptom with spaces", "--why", "A reason, with a comma.",
    ]
    assert main(typed) == EXIT_USAGE
    (offered,) = [
        line for line in capsys.readouterr().err.splitlines() if line.startswith("  retry")
    ]
    retry = offered.split("retry", 1)[1].strip()
    assert retry.startswith(invocation())
    again = shlex.split(retry[len(invocation()) :])
    # The same call, one flag longer — and the address is the one the sentence named.
    assert again == [*typed, "--ref", "XVII.4"]
    assert main(again) == EXIT_OK


def test_the_retry_replaces_an_address_the_caller_typed_and_cannot_reuse(tmp_path, capsys):
    """The second refusal, which RK1149 measured as worse than the first: the anchor is spent,
    the author had no way to know, and what changes is one token of the same call. Replaced
    wherever it sits, so the positional of `section add` and a `--ref` are one rule."""
    config = outlined_blocks(tmp_path)
    root = str(config.root)
    # Spent the way RK1149 measured it: the entry shipped, which takes its section with it, and
    # the ledger keeps prose citing the address while nothing on any file says it was ever used.
    assert main(["-C", root, "block", "add", "Q", "--title", "Serving"]) == EXIT_OK
    assert main(["-C", root, "ship", "RK2", "--why", "It works now."]) == EXIT_OK
    assert main(["-C", root, "section", "drop", "XVII.3"]) == EXIT_OK
    git_commit(config.root, "chore: ship the line and drop the prose it pointed at")
    typed = [
        "-C", str(config.root), "section", "add", "XVII.3",
        "--title", "A design at a spent address", "--body", "Prose enough to matter.",
    ]
    assert main(typed) == EXIT_USAGE
    err = capsys.readouterr().err
    (offered,) = [line for line in err.splitlines() if line.startswith("  retry")]
    again = shlex.split(offered.split("retry", 1)[1].strip()[len(invocation()) :])
    # The substitution is the claim: the spent address is gone from the call and the offered one
    # is where it stood. Not executed here — this fixture writes its prose file directly, so
    # `section add` refuses the offered child for a missing parent, which is a fact about the
    # fixture and not about the retry. The test above runs its call, which is where quoting lives.
    assert "XVII.3" not in again and again[again.index("add") + 1] == "XVII.4"
    assert again[:3] == ["-C", root, "section"] and "--title" in again


def test_a_refusal_that_derived_no_address_offers_no_call(tmp_path, capsys):
    """The absence is the rule (RK360): where this declines to name an address — two families,
    or no history to read — there is nothing to substitute and no retry is printed."""
    config = outlined_blocks(tmp_path)
    append(
        config.path("roadmap"),
        f"- {DESIGNED} **RK4** (deps: —) **A symptom** — a reason. → §XVII.5\n",
    )
    argv = ["-C", str(config.root), "add", "--block", "R", "--symptom", "A", "--why", "B."]
    assert main(argv) == EXIT_USAGE
    assert "retry" not in capsys.readouterr().err


def test_a_block_spanning_two_families_is_told_to_ask_rather_than_given_one(tmp_path, capsys):
    config = outlined_blocks(tmp_path)
    append(
        config.path("roadmap"),
        f"- {DESIGNED} **RK4** (deps: —) **A symptom** — a reason. → §XVII.5\n",
    )
    assert (
        main(
            [
                "-C",
                str(config.root),
                "add",
                "--block",
                "R",
                "--symptom",
                "A symptom",
                "--why",
                "A reason.",
            ]
        )
        == EXIT_USAGE
    )
    err = capsys.readouterr().err
    assert "anchors --block R" in err and "free top-level" in err


def test_filing_into_a_block_whose_prose_has_not_started_gets_the_whole_path(tmp_path, capsys):
    """RK1198. The staircase, collapsed into the refusal the author is actually standing in.

    Measured filing three tasks into an outline project, into blocks whose every line had
    shipped: `add` refused for a missing `--ref`, `anchors --block` refused because no open
    line there carries a pointer, `add` refused for the block heading, `section add` refused
    for a family with nothing to extend — six calls before the first write, and the prose was
    ready at call one. Every fact those five calls established was available at this refusal.

    Reporting one step is right when a caller is one step from done and wrong when they are
    six, because a staircase discovered a stair at a time reads as a tool changing its mind.
    """
    config = outlined_blocks(tmp_path)
    # Block Z, which no governed file declares: the measured case is a block being *opened*,
    # so the heading is the first stair and Block A — declared in all three — is the next test.
    argv = ["-C", str(config.root), "add", "--block", "Z", "--symptom", "A", "--why", "B."]
    assert main(argv) == EXIT_USAGE
    err = capsys.readouterr().err
    # The rule survives, as it does at every other door this clause is appended at.
    assert "every task points at its rationale section" in err
    assert "Block Z's prose has not started and §XXI is its free top-level" in err
    # The ordered verbs with their arguments filled in, and not a description of them: what is
    # left in angle brackets is the title, which is editorial and L4's to leave alone.
    for step in (
        'block add Z --title "<its title>"',
        'section add XXI --title "<its title>"',
        "add --block Z --ref XXI.1 …",
        "section add XXI.1 --title …",
    ):
        assert f"`{invocation()} {step}`" in err, step


def test_the_path_names_no_block_add_where_a_heading_already_declares_it(tmp_path, capsys):
    # The first stair is conditional, being `add`'s own second door: a block every governed
    # file already declares is one the retry walks straight past, and a step naming a write
    # that is already done is the same noise as a step withheld.
    config = outlined_blocks(tmp_path)
    argv = ["-C", str(config.root), "add", "--block", "A", "--symptom", "A", "--why", "B."]
    assert main(argv) == EXIT_USAGE
    err = capsys.readouterr().err
    assert "block add A" not in err
    assert f'`{invocation()} section add XXI --title "<its title>"`' in err


def test_the_path_is_the_one_that_works(tmp_path, capsys):
    """Executed and not matched, for the reason RK1149's retry is: a printed sequence whose
    order is wrong is a sequence that refuses at step two, and this one exists precisely
    because each step in it was previously discovered by being refused."""
    config = outlined_blocks(tmp_path)
    root = str(config.root)
    typed = ["-C", root, "add", "--block", "Z", "--symptom", "A symptom", "--why", "A reason."]
    assert main(typed) == EXIT_USAGE
    steps = [
        shlex.split(one.strip()[len(invocation()) :])
        for one in capsys.readouterr().err.replace("`", "\n").splitlines()
        if one.strip().startswith(invocation())
    ]
    # Every refusal ends with the `report` line that files a defect against this tool, and it
    # is spelled as an invocation like the rest — it is not a stair, so it is not walked.
    steps = [one for one in steps if one[0] != "report"]
    # The ellipsis stands for the caller's own prose, which only they can write (L4). Filling
    # it in is this test's job and the order is not: each step runs as printed, in the order
    # printed, and every one of them has to be accepted where it stands.
    filled = {
        "block": ["--title", "The model"],
        "section": ["--title", "A title", "--body", "Prose enough to matter."],
        "add": ["--symptom", "A symptom", "--why", "A reason."],
    }
    for step in steps:
        again = step[: step.index("…")] if "…" in step else step
        # The ellipsis stands where a flag was already typed as often as where none was, so
        # the dangling `--title` goes with it rather than being answered twice.
        again = again[:-1] if again[-1].startswith("--") else again
        assert main(["-C", root, *again, *filled[again[0]]]) == EXIT_OK, step
    # And the line the path landed is one the gate has nothing to say about. Asked of this
    # block alone rather than of the file: `outlined_blocks` writes two blocks whose ledger
    # headings it never declares, which is a fixture the path being tested does not touch.
    capsys.readouterr()
    main(["-C", root, "lint"])
    reported = capsys.readouterr().out
    assert "Block Z" not in reported and "XXI" not in reported


def test_every_other_violation_still_arrives_with_it(tmp_path, capsys):
    # Enriched around `place` and not before it: the schema reports every violation at once,
    # and an early refusal would trade that for the one sentence it improves.
    config = outlined_blocks(tmp_path)
    assert (
        main(
            [
                "-C",
                str(config.root),
                "add",
                "--block",
                "Q",
                "--symptom",
                "A symptom",
                "--why",
                "no terminator here",
            ]
        )
        == EXIT_USAGE
    )
    err = capsys.readouterr().err
    assert "ref.missing" in err and "why.no-terminator" in err
    assert "§XVII.4 is free" in err


# -- the same clause, at every door that refuses one (RK349) ------------------


def excused_the_pointer(tmp_path: Path) -> Config:
    """An outline project whose roadmap is let off the pointer its store still demands.

    Which is the state `defer` refuses in, and the one RK349 was measured from: the line is
    legal where the author wrote it and illegal where the pause files it, so the field named
    in the refusal is one they never typed and the address it wants is one nothing named.
    """
    config = outlined_blocks(tmp_path)
    (config.root / "roadkeep.toml").write_text(
        'prefix = "RK"\nref_scheme = "outline"\n'
        '[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'improvements = "IMPROVEMENTS.md"\ndeferred = "DEFERRED.md"\n'
        "[rules.roadmap]\nref = false\n",
        encoding="utf-8",
    )
    (config.root / "DEFERRED.md").write_text("## Block Q — Serving\n", encoding="utf-8")
    append(
        config.path("roadmap"),
        f"\n## Block Q — Serving\n\n- {DESIGNED} **RK9** (deps: —) **A symptom** — a reason.\n",
    )
    git_commit(tmp_path, "chore: a line with no pointer")
    return Config.discover(tmp_path)


def test_the_pause_that_demands_a_ref_names_what_produces_one(tmp_path, capsys):
    # The measured case. `defer` reaches the same `check` through its own door and printed the
    # bare rule, which is the exact text RK312 was filed against, one verb over.
    config = excused_the_pointer(tmp_path)
    assert main(["-C", str(config.root), "defer", "RK9", "--reason", "waiting"]) == EXIT_USAGE

    err = capsys.readouterr().err
    assert "every task points at its rationale section" in err
    assert "Block Q's prose is under §XVII" in err and "§XVII.4 is free" in err


def test_the_return_from_the_store_answers_the_same_way(tmp_path, capsys):
    # `resume` writes the line back and validates it again, so it is the same gap read
    # backwards: the store excused the pointer and the roadmap it returns to does not.
    config = outlined_blocks(tmp_path)
    (config.root / "roadkeep.toml").write_text(
        'prefix = "RK"\nref_scheme = "outline"\n'
        '[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'improvements = "IMPROVEMENTS.md"\ndeferred = "DEFERRED.md"\n'
        "[rules.deferred]\nref = false\n",
        encoding="utf-8",
    )
    (config.root / "DEFERRED.md").write_text(
        "## Block Q — Serving\n\n- ⏸ **RK9** (deps: —) **A symptom** — a reason (paused: waiting).\n",
        encoding="utf-8",
    )
    git_commit(tmp_path, "chore: a paused line with no pointer")
    config = Config.discover(tmp_path)
    assert main(["-C", str(config.root), "resume", "RK9"]) == EXIT_USAGE

    err = capsys.readouterr().err
    assert "every task points at its rationale section" in err
    assert "§XVII.4 is free" in err


def test_a_section_written_at_an_id_under_an_outline_is_told_where_addresses_come_from(
    tmp_path, capsys
):
    # The third door: `section add RK2` under a scheme that numbers its own headings refused
    # `not an <x.y> outline anchor` and named nothing — the same author, holding no address.
    config = outlined_blocks(tmp_path)
    assert (
        main(["-C", str(config.root), "section", "add", "RK2", "--title", "A design",
              "--body", "Some prose."])
        == EXIT_USAGE
    )

    err = capsys.readouterr().err
    # The rule survives here too: what an outline anchor is, and then where to get one.
    assert "the heading numbers itself" in err
    assert "Block Q's prose is under §XVII" in err and "§XVII.4 is free" in err


# -- the caller who has no address at all (RK360) -----------------------------


def test_an_anchor_naming_no_task_is_told_where_a_top_level_comes_from(tmp_path, capsys):
    # RK349 read the block off the task the anchor names, which left this caller silent — and
    # they are the one who did not know what an address here looks like, not the rare case.
    config = outlined_blocks(tmp_path)
    assert (
        main(["-C", str(config.root), "section", "add", "II-1", "--title", "A design",
              "--body", "Some prose."])
        == EXIT_USAGE
    )

    err = capsys.readouterr().err
    # The rule survives, and what follows it is the top-level — never a child derived from
    # whichever family happened to be last, which is the guess there is no block to make.
    assert "the heading numbers itself" in err
    assert "belonging to no task takes a top-level" in err
    assert "§XXI is free" in err
    assert "anchors --block" not in err


def test_a_typo_inside_a_family_that_exists_is_answered_with_that_family(tmp_path, capsys):
    # RK360's top-level was the wrong address here, and wrong is worse than silent: `XVII-1`
    # is a hyphen where a dot belongs, and "start a new subtree" is what that author was not
    # doing. The family is not a guess from context — it is a string they wrote down.
    config = outlined_blocks(tmp_path)
    assert (
        main(["-C", str(config.root), "section", "add", "XVII-1", "--title", "A design",
              "--body", "Some prose."])
        == EXIT_USAGE
    )

    err = capsys.readouterr().err
    assert "§XVII is a family that exists" in err and "§XVII.4 is free" in err
    assert "anchors --family XVII" in err
    assert "takes a top-level" not in err


def test_the_separator_typed_wrong_is_one_mistake_however_it_is_typed(tmp_path, capsys):
    # What counts as the segment: the letters and digits before whichever separator went
    # wrong, so `XVII-1` and `XVII 1` are the same address written badly twice.
    config = outlined_blocks(tmp_path)
    assert (
        main(["-C", str(config.root), "section", "add", "XVII 1", "--title", "A design",
              "--body", "Some prose."])
        == EXIT_USAGE
    )
    assert "§XVII.4 is free" in capsys.readouterr().err


def test_the_free_top_level_is_read_per_namespace(tmp_path, capsys):
    # Two prose files each numbering themselves from I have two free top-levels, and the
    # taller file's number is not an answer about the shorter one (RK340's rule, one door on).
    config = outlined_blocks(tmp_path)
    prose(config, "STRATEGY.md")
    (config.root / "roadkeep.toml").write_text(
        (config.root / "roadkeep.toml")
        .read_text(encoding="utf-8")
        .replace('improvements = "STRATEGY.md"', 'strategy = "STRATEGY.md"')
        + '[refs]\nstrategy = "S"\n',
        encoding="utf-8",
    )
    config = Config.discover(tmp_path)
    # Unprefixed in the file: the namespace rides on the pointer, and the heading keeps the
    # number this file wrote — which is what makes `S:IV` and `XVII` two numberings and not one.
    append(config.path("strategy"), "\n### IV.1 A plan\n\nThe reasoning.\n")
    git_commit(tmp_path, "docs: a second outline of its own")

    # A leading segment naming no family, so this is the top-level branch and not RK363's.
    assert (
        main(["-C", str(config.root), "section", "add", "S:ZZ-1", "--role", "strategy",
              "--title", "A plan", "--body", "Some prose."])
        == EXIT_USAGE
    )
    err = capsys.readouterr().err
    assert "§S:V is free" in err


# -- the doors that rewrite a line already on the file (RK379) ----------------


def imported_without_a_pointer(tmp_path: Path) -> Config:
    """An outline project holding one line that arrived with no `→ §` at all.

    The population every door below is for: `add` refuses to write such a line, so the only
    way one exists is an import — and correcting it is exactly what `amend` and `restate` are
    the doors for. RK312 enriched the refusal on the way *in*, which none of these calls take.

    The line lands under Block R, which is where an append to this file puts it, and whose
    prose is the second family — so the address offered is read from the block the line is
    actually in and never from whichever family happened to be first.
    """
    config = outlined_blocks(tmp_path)
    append(
        config.path("roadmap"),
        f"- {DESIGNED} **RK9** (deps: —) **A symptom** — a reason.\n",
    )
    git_commit(tmp_path, "chore: an imported line with no pointer")
    return Config.discover(tmp_path)


def test_the_correction_that_demands_a_ref_names_what_produces_one(tmp_path, capsys):
    # The measured door, one file over from RK312's: an adopted line's `why` is the field
    # `amend` exists to compress, and the author is told a pointer is required by a sentence
    # that names no address — while `anchors` has computed one all along.
    config = imported_without_a_pointer(tmp_path)
    assert (
        main(["-C", str(config.root), "amend", "RK9", "--why", "a shorter reason."])
        == EXIT_USAGE
    )

    err = capsys.readouterr().err
    assert "every task points at its rationale section" in err
    assert "Block R's prose is under §XX" in err and "§XX.2 is free" in err


def test_the_restated_symptom_answers_the_same_way(tmp_path, capsys):
    # The door next to it, which composes its own task and validates it the same way.
    config = imported_without_a_pointer(tmp_path)
    assert (
        main(["-C", str(config.root), "restate", "RK9", "--symptom", "Another symptom"])
        == EXIT_USAGE
    )
    assert "§XX.2 is free" in capsys.readouterr().err


def test_the_marker_write_answers_the_same_way(tmp_path, capsys):
    # Taking a line is a marker write, so this is the refusal that meets an author who asked
    # to *start* the imported task — the first call of the work, and the worst one to be bare.
    config = imported_without_a_pointer(tmp_path)
    assert main(["-C", str(config.root), "status", "RK9", IN_PROGRESS]) == EXIT_USAGE
    assert "§XX.2 is free" in capsys.readouterr().err


def test_the_id_that_moves_answers_the_same_way(tmp_path, capsys):
    # `renumber` re-validates the line under its new id, so a merge repair hits it too.
    config = imported_without_a_pointer(tmp_path)
    assert main(["-C", str(config.root), "renumber", "RK9"]) == EXIT_USAGE
    assert "§XX.2 is free" in capsys.readouterr().err


def test_a_paused_line_that_moves_is_still_judged_by_the_stores_own_grammar(tmp_path):
    # The regression the clause could have bought: `renumber` reaches the deferred store too,
    # and this project excuses its pointer. Validating one against the roadmap's schema would
    # refuse a paused line for lacking a field its own file was configured not to want.
    config = outlined_blocks(tmp_path)
    (config.root / "roadkeep.toml").write_text(
        'prefix = "RK"\nref_scheme = "outline"\n'
        '[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'improvements = "IMPROVEMENTS.md"\ndeferred = "DEFERRED.md"\n'
        "[rules.deferred]\nref = false\n",
        encoding="utf-8",
    )
    (config.root / "DEFERRED.md").write_text(
        "## Block Q — Serving\n\n- ⏸ **RK9** (deps: —) **A symptom** — a reason (paused: waiting).\n",
        encoding="utf-8",
    )
    git_commit(tmp_path, "chore: a paused line with no pointer")
    assert main(["-C", str(tmp_path), "renumber", "RK9", "--to", "RK12"]) == EXIT_OK
    assert "RK12" in (config.root / "DEFERRED.md").read_text(encoding="utf-8")


# -- the read-back that called its own writes loose (RK342) -------------------


def claimed(tmp_path: Path) -> Config:
    """A committed repository with one line, taken, and the marker write left uncommitted."""
    config = repo(tmp_path)
    append(
        config.path("roadmap"),
        f"- {DESIGNED} **RK2** (deps: —) **A symptom** — a reason. → §RK2\n",
    )
    git_commit(tmp_path, "chore: a line to take")
    config = Config.discover(tmp_path)
    # The write a claim makes: the marker moves, which is the diff the read-back has to read.
    assert main(["-C", str(tmp_path), "status", "RK2", IN_PROGRESS]) == EXIT_OK
    return Config.discover(tmp_path)


def test_a_claims_own_marker_write_is_not_a_file_nobody_owns(tmp_path, capsys):
    # `loose` reads as *a file somebody else touched*, so the author declares the governed
    # paths by hand to silence it — and the scope then carries paths that were never the work.
    # That is the analysis `claim` exists to make, made wrong, on the first call of every task.
    config = claimed(tmp_path)
    try:
        assert main(["-C", str(tmp_path), "claim", "RK2"]) == EXIT_OK
        out = capsys.readouterr().out
        assert "wrote    ROADMAP.md" in out
        assert "loose" not in out
        assert "stage    git add -- ROADMAP.md" in out
    finally:
        claiming.path(tmp_path).unlink(missing_ok=True)


def test_a_governed_file_this_task_did_not_write_stays_loose(tmp_path, capsys):
    # The repair that was available and wrong: a roadmap the tree holds may hold another
    # session's `add`, and handing every dirty governed file to whoever asks would give the
    # two sessions RK294 separates each other's files with this tool's signature on it.
    config = claimed(tmp_path)
    capsys.readouterr()  # the marker write the fixture made, not this test's
    append(
        config.path("changelog"),
        f"- {SHIPPED} **RK7** **Another symptom** — somebody else's delivery.\n",
    )
    try:
        assert main(["-C", str(tmp_path), "claim", "RK2", "--json"]) == EXIT_OK
        payload = json.loads(capsys.readouterr().out)
        assert payload["wrote"] == ["ROADMAP.md"]
        assert payload["unclaimed"] == ["CHANGELOG.md"]
    finally:
        claiming.path(tmp_path).unlink(missing_ok=True)


def test_a_source_file_citing_the_id_is_the_authors_and_not_the_tools(tmp_path, capsys):
    # The other half of the same narrowness: the claim being made is that *this tool* wrote
    # it, so a file no verb can produce is never in the list however its diff reads.
    claimed(tmp_path)
    capsys.readouterr()  # the marker write the fixture made, not this test's
    (tmp_path / "mine.py").write_text("# RK2: the fix\nx = 1\n", encoding="utf-8")
    try:
        assert main(["-C", str(tmp_path), "claim", "RK2", "--json"]) == EXIT_OK
        payload = json.loads(capsys.readouterr().out)
        assert payload["wrote"] == ["ROADMAP.md"]
        assert payload["unclaimed"] == ["mine.py"]
    finally:
        claiming.path(tmp_path).unlink(missing_ok=True)


def test_the_declaration_stays_what_the_holder_said(tmp_path, capsys):
    # `mine` is the scope, verbatim; `wrote` is a record to be used. Both reach the staging
    # line, in that order, exactly as a departure prints them.
    config = claimed(tmp_path)
    capsys.readouterr()  # the marker write the fixture made, not this test's
    claiming.scope(config, "RK2", ["mine.py"])
    (tmp_path / "mine.py").write_text("x = 1\n", encoding="utf-8")
    try:
        assert main(["-C", str(tmp_path), "claim", "RK2", "--json"]) == EXIT_OK
        payload = json.loads(capsys.readouterr().out)
        assert payload["paths"] == ["mine.py"] and payload["wrote"] == ["ROADMAP.md"]

        assert main(["-C", str(tmp_path), "claim", "RK2", "--porcelain"]) == EXIT_OK
        assert capsys.readouterr().out.split() == ["mine.py", "ROADMAP.md"]
    finally:
        claiming.path(tmp_path).unlink(missing_ok=True)


def test_a_near_id_does_not_answer_for_this_one(tmp_path):
    # `RK2` must not be found in a line naming `RK25`, the care `cited_origin` takes with an
    # anchor and for the same reason.
    config = repo(tmp_path)
    append(
        config.path("roadmap"),
        f"- {DESIGNED} **RK25** (deps: —) **A symptom** — a reason.\n",
    )
    git_commit(tmp_path, "chore: a neighbour")
    append(config.path("roadmap"), f"- {DESIGNED} **RK251** (deps: —) **Another** — a reason.\n")

    assert carrying(config, "RK251", ["ROADMAP.md"]) == ("ROADMAP.md",)
    assert carrying(config, "RK25", ["ROADMAP.md"]) == ()


def test_a_removed_line_counts_because_that_is_what_a_departure_leaves(tmp_path):
    # Read off both sides of the diff: a ship takes the line out, and reading additions alone
    # would answer "no" about the departure that is most of the work.
    config = repo(tmp_path)
    append(
        config.path("roadmap"),
        f"- {DESIGNED} **RK2** (deps: —) **A symptom** — a reason.\n",
    )
    git_commit(tmp_path, "chore: a line to remove")
    kept = [
        one
        for one in config.path("roadmap").read_text(encoding="utf-8").splitlines(keepends=True)
        if "**RK2**" not in one
    ]
    config.path("roadmap").write_text("".join(kept), encoding="utf-8")

    assert carrying(config, "RK2", ["ROADMAP.md"]) == ("ROADMAP.md",)


# -- which lines claim an address, beside whether it is spent (RK453) ---------


def claimants(config: Config, *pointers: str) -> None:
    """Give the roadmap one open line per pointer, so an address has claimants to name."""
    path = config.path("roadmap")
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    for at, ref in enumerate(pointers, start=1):
        lines.append(
            f"- 📋 **RK{90 + at}** (deps: —) **A symptom number {at}** — Because. → §{ref}\n"
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("".join(lines))


def test_a_live_heading_says_which_task_it_binds(tmp_path):
    """Under an outline the id in the heading is the ownership (RK262), and until this read
    it was visible only as `ship`'s `kept` field scrolling past."""
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 A bound design (RK91)", "docs: file it")
    claimants(config, "XXXVII.1")
    found = anchors(config, "improvements", "XXXVII")
    assert [(one.anchor, one.binds, one.claimed) for one in found] == [
        ("XXXVII.1", "RK91", ("RK91",))
    ]
    assert not found[0].orphaned


def test_a_heading_written_before_its_line_binds_nobody_and_says_so(tmp_path):
    """RK452 stops this being created and does not reach a corpus already holding it. The
    fixture's §I.1 was found by reading a field as it scrolled past, and Shio's the same."""
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 An unbound design", "docs: file it")
    claimants(config, "XXXVII.1")
    found = anchors(config, "improvements", "XXXVII")
    assert found[0].binds == "" and found[0].claimed == ("RK91",)
    assert not found[0].orphaned  # a line claims it; what is missing is the binding


def test_a_heading_no_open_line_claims_is_named(tmp_path):
    """`live` answered a different question — RK247 built it about address reuse — so a
    section written for a task that has since shipped was counted among the working ones."""
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 A design whose task has gone (RK91)", "docs: file it")
    found = anchors(config, "improvements", "XXXVII")
    assert found[0].binds == "RK91" and found[0].claimed == ()
    assert found[0].orphaned


def test_a_retired_address_is_asked_nothing_about_ownership(tmp_path):
    """There is no heading left to read an id off, and a live line pointing at an address
    nothing declares is `ref.unresolved` — reading it here would be a second gate."""
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 A design", "docs: file it")
    unwrite(config, "### XXXVII.1 A design", "feat: it shipped (RK91)")
    found = anchors(config, "improvements", "XXXVII")
    assert found[0].live is False
    assert found[0].binds == "" and found[0].claimed == () and not found[0].orphaned


def test_the_listing_says_nothing_about_the_ordinary_row(tmp_path, capsys):
    """A heading bound to the one line that claims it is what every write produces, and
    repeating it on every address would bury the two that are not."""
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 A bound design (RK91)", "docs: file it")
    claimants(config, "XXXVII.1")
    assert main(["-C", str(tmp_path), "anchors", "--family", "XXXVII"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "binds" not in out and "claimed" not in out


def test_the_listing_names_each_way_they_come_apart(tmp_path, capsys):
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 An unbound design", "docs: file it")
    design(config, "### XXXVII.2 A design whose task has gone (RK92)", "docs: file it")
    claimants(config, "XXXVII.1")
    assert main(["-C", str(tmp_path), "anchors", "--family", "XXXVII"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "binds nobody, claimed by RK91" in out
    assert "binds RK92, which no open line claims" in out

    assert main(["-C", str(tmp_path), "anchors", "--family", "XXXVII", "--json"]) == EXIT_OK
    rows = {row["anchor"]: row for row in json.loads(capsys.readouterr().out)["anchors"]}
    assert rows["XXXVII.1"]["binds"] is None and rows["XXXVII.1"]["claimed"] == ["RK91"]
    assert rows["XXXVII.2"]["binds"] == "RK92" and rows["XXXVII.2"]["orphaned"] is True


def test_the_audit_needs_no_family_and_leaves_out_what_nobody_reads(tmp_path, capsys):
    """RK459. RK453 put `binds` and `claimed` on every row, and RK264 prints rows only under
    `--family` — rightly, since unnarrowed this repository lists 287 retired addresses. So
    the two facts it added were reachable one numeral at a time, and the corpus they were
    written for spans dozens of them: the audit cost a call per family, on the adopting
    project that most needs it.

    What is filtered out is exactly what `_ownership` already stays silent about, which is
    why the listing is small on any corpus and needs no family at all.
    """
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 An unbound design", "docs: file it")
    design(config, "### XXXVIII.1 A design whose task has gone (RK99)", "docs: file it")
    design(config, "### XXXIX.1 An ordinary design (RK92)", "docs: file it")
    # RK91 claims the first pointer and RK92 the second, so the third row is the ordinary
    # one: a heading bound to the single line that claims it.
    claimants(config, "XXXVII.1", "XXXIX.1")
    assert main(["-C", str(tmp_path), "anchors", "--claims"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "2 of 3 address(es) say something about ownership" in out
    assert "XXXVII.1  binds nobody, claimed by RK91" in out
    assert "XXXVIII.1  binds RK99, which no open line claims" in out
    # The ordinary row is what every write produces, and printing it would bury the two.
    assert "XXXIX.1" not in out


def test_the_audit_carries_the_rows_in_the_payload_too(tmp_path, capsys):
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 An unbound design", "docs: file it")
    design(config, "### XXXIX.1 An ordinary design (RK92)", "docs: file it")
    claimants(config, "XXXVII.1", "XXXIX.1")
    assert main(["-C", str(tmp_path), "anchors", "--claims", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert [row["anchor"] for row in payload["anchors"]] == ["XXXVII.1"]
    assert payload["anchors"][0]["binds"] is None


def test_a_retired_address_is_never_in_the_audit(tmp_path, capsys):
    """It has no heading to have an opinion about, which is the same reason `_ownership`
    says nothing about one."""
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 A design", "docs: file it")
    unwrite(config, "### XXXVII.1 A design", "feat: it shipped (RK91)")
    assert main(["-C", str(tmp_path), "anchors", "--claims"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "0 of 1 address(es)" in out and "XXXVII.1" not in out


def test_a_standing_memo_is_not_a_thing_to_act_on(tmp_path, capsys):
    """RK461. Run on this repository the audit reported five addresses and all five were
    `§0` to `§0.4`, the design preamble — prose belonging to no task and never will. RK236 is
    why that is right and not a defect; what was wrong is that the listing did not tell it
    apart from the two states it exists for, so its majority was noise."""
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 A standing memo", "docs: file it")
    found = anchors(config, "improvements", "XXXVII")[0]
    assert found.memo and not found.orphaned
    assert main(["-C", str(tmp_path), "anchors", "--claims"]) == EXIT_OK
    out = capsys.readouterr().out
    # Counted and not listed: "none needing anything" is a different answer from silence.
    assert "0 of 1 address(es) say something about ownership, 1 standing memo(s)" in out
    assert "XXXVII.1" not in out


def test_prose_whose_task_has_left_is_not_a_memo(tmp_path):
    """`orphaned` was `live and not claimed`, so it was true of a memo too — which was never
    anybody's and therefore cannot have been left."""
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 A design whose task has gone (RK99)", "docs: file it")
    found = anchors(config, "improvements", "XXXVII")[0]
    assert found.orphaned and not found.memo


def test_an_unbound_heading_a_line_claims_is_neither(tmp_path):
    """RK452's write left undone on an older corpus: one `section amend` closes it, which is
    what makes it a finding rather than a memo."""
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 An unbound design", "docs: file it")
    claimants(config, "XXXVII.1")
    found = anchors(config, "improvements", "XXXVII")[0]
    assert not found.memo and not found.orphaned and found.claimed == ("RK91",)


def test_the_payload_tells_the_third_state_apart(tmp_path, capsys):
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 A standing memo", "docs: file it")
    design(config, "### XXXVIII.1 A design whose task has gone (RK99)", "docs: file it")
    assert main(["-C", str(tmp_path), "anchors", "--claims", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert [row["anchor"] for row in payload["anchors"]] == ["XXXVIII.1"]
    assert payload["anchors"][0]["orphaned"] is True
    assert payload["anchors"][0]["memo"] is False


def test_the_free_address_and_the_audit_are_two_answers(tmp_path, capsys):
    """RK466. `--next` returned before the `--claims` branch was reached, so a caller asking
    for the audit and the free address read the address alone with nothing said about the
    other — two subjects, as `budget`'s five are, and one answer per call."""
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 An unbound design", "docs: file it")
    claimants(config, "XXXVII.1")
    assert main(["-C", str(tmp_path), "anchors", "--claims", "--next"]) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "the free address (--next)" in said
    assert "the ownership audit (--claims)" in said
    assert "one answer per call" in said
    # And each alone still answers, which is what makes the refusal about the pair.
    assert main(["-C", str(tmp_path), "anchors", "--next"]) == EXIT_OK
    assert capsys.readouterr().out.startswith("§")
    assert main(["-C", str(tmp_path), "anchors", "--claims"]) == EXIT_OK
    assert "ownership" in capsys.readouterr().out


# -- an address the writer will refuse is not offered silently (RK1024) -------


def crowded(tmp_path: Path, spent: int, limit: int = 30) -> Config:
    """An outline project whose §IX is a live design already spending most of its budget."""
    config = outlined(tmp_path)
    append(
        config.path("roadmap"),
        f"- {DESIGNED} **RK1** (deps: —) **A symptom** — a reason. → §IX\n",
    )
    append(config.root / "roadkeep.toml", f"\n[limits]\nsection = {limit}\n")
    append(
        config.path("improvements"),
        f"\n### IX A design already spending its budget\n\n{' '.join(['word'] * spent)}\n",
    )
    git_commit(config.root, "docs: file IX")
    return Config.discover(tmp_path)


def test_the_listing_says_where_a_child_has_no_room_before_it_is_written(tmp_path, capsys):
    """The address `anchors` offered and `add` then refused. §IX is 29 of its own 30 words,
    so every child of it — the empty one included — is over the limit before a word of it is
    composed, and only `lint` used to say so."""
    config = crowded(tmp_path, spent=29)
    assert main(["-C", str(tmp_path), "anchors", "--family", "IX"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "next     §IX.1" in out
    assert "already spends 29 of its 30 words" in out


def test_a_family_with_room_is_offered_with_nothing_added(tmp_path, capsys):
    """Said only where it is true: a parent with room is the normal case, and a sentence
    printed on every listing is one nobody reads on the listing that needed it."""
    config = crowded(tmp_path, spent=4)
    assert main(["-C", str(tmp_path), "anchors", "--family", "IX"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "next     §IX.1 — nothing ever used it\n" in out
    assert "already spends" not in out


# -- the free address that is not a section yet (RK1140) ------------------------


def test_a_free_top_level_says_it_is_not_a_section_yet(tmp_path, capsys):
    """RK1140, from a capture this repository kept. `anchors` reads which addresses the outline
    has **spent**, so a free top-level is a fact about numbering — and `add --ref XXII.1` then
    refuses, because a pointer resolves to a section and nothing declares `XXII`. The read
    answered `XXII` and the write answered "no section XXII.1 extends"."""
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 A design", "docs: file it")
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "anchors", "--next"]) == EXIT_OK
    said = capsys.readouterr()
    # stdout stays the address and nothing else: this command exists to be captured.
    assert said.out.startswith("§") and "roadkeep:" not in said.out
    assert "is free and not yet a section" in said.err
    assert "section add" in said.err and "--title" in said.err


def test_a_free_child_says_nothing_because_its_family_exists(tmp_path, capsys):
    # The distinction the note turns on: a child is placeable the moment it is answered,
    # because the heading it extends is already there.
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 A design", "docs: file it")
    assert main(["-C", str(tmp_path), "anchors", "--next", "--family", "XXXVII"]) == EXIT_OK
    said = capsys.readouterr()
    assert said.out.startswith("§XXXVII.")
    assert said.err == ""


def test_the_payload_names_the_command_the_reader_is_given(tmp_path, capsys):
    # One question, one answer: a client composing `add --ref <next>.1` walks into the refusal
    # a person now reads about, so the payload carries the command and not only the address.
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 A design", "docs: file it")
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "anchors", "--next", "--json"]) == EXIT_OK
    rows = json.loads(capsys.readouterr().out)["next_families"]
    assert rows and all(row["opens"] == f"section add {row['next']} --title …" for row in rows)


def test_the_command_it_names_is_the_one_that_makes_the_pointer_resolve(tmp_path, capsys):
    """RK1045's rule: a remedy is a promise, and a promise nothing runs is prose. So the
    sentence is not read here — the command it names is executed, and then the `add` it says
    will resolve is executed too."""
    config = outlined(tmp_path)
    design(config, "### XXXVII.1 A design", "docs: file it")
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "anchors", "--next"]) == EXIT_OK
    free = capsys.readouterr().out.splitlines()[0].lstrip("§").split()[0]
    argv = ["-C", str(tmp_path), "section", "add", free, "--title", "A new family",
            "--body", "The reasoning it carries."]
    assert main(argv) == EXIT_OK
    capsys.readouterr()
    filed = ["-C", str(tmp_path), "add", "--block", "A", "--symptom", "A symptom",
             "--why", "Because of a reason.", "--ref", f"{free}.1"]
    assert main(filed) == EXIT_OK


# -- a run of never-carried ids is one row (RK1165) ---------------------------


def numbered(config: Config, *ids: str) -> None:
    """File one line per id, so the numbers between them become gaps of the never-carried kind."""
    for one in ids:
        append(
            config.path("roadmap"),
            f"- {DESIGNED} **{one}** (deps: —) **A symptom** — a reason. → §{one}\n",
        )
    git_commit(config.root, "docs: file the lines these ids carry")


def test_a_contiguous_run_of_never_carried_ids_is_one_row(tmp_path, capsys):
    """Measured on this repository: `gaps` printed 503 lines, 499 of them a numbering jump saying
    the same sentence with a different number — and the two ids worth reading were behind them.

    **Every** run and not a long one: a threshold would be a number nobody can re-read, and two
    consecutive ids in one row is the same information rather than less."""
    config = repo(tmp_path)
    numbered(config, "RK1", "RK9")
    assert main(["-C", str(config.root), "gaps"]) == EXIT_OK
    printed = capsys.readouterr().out
    # RK2 through RK8 is one row, and the count rides on it.
    assert "RK2–RK8" in printed and "(7 ids)" in printed
    assert "RK3" not in printed and "RK7" not in printed
    assert "7 gap(s)" in printed and "7 never carried" in printed


def test_a_gap_history_answers_for_is_never_folded_into_a_run(tmp_path, capsys):
    """One kind runs together and the other does not: a gap resolved against history carries a
    commit of its own, and two of them are two answers however adjacent their numbers."""
    config = repo(tmp_path)
    numbered(config, "RK1", "RK5")
    ship(config, "RK1", "feat: ship RK1")
    assert main(["-C", str(config.root), "gaps"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "RK2–RK4" in printed
    # And RK1, which the ledger holds, is no gap at all — the run starts after it.
    assert "RK1–" not in printed


def test_an_anchor_nobody_wrote_answers_with_nulls_and_not_a_traceback(tmp_path, capsys):
    """Both halves of `cited_origin` are `None` by construction — an address nobody ever wrote has
    no writing commit, and one still in the file has no removing one — so the payload publishes
    nulls. It raised instead, from RK1163 until RK1170 found it: that task added a second
    `_commit_json` to `rendering.py`, which shadowed the nullable one and narrowed every caller of
    the name to a commit that must exist.

    On the command and not on the function, because what a duplicate definition breaks is the
    call: both spellings passed their own tests, and nothing asked what the module resolved.
    """
    config = repo(tmp_path)
    assert main(["-C", str(config.root), "origin", "§RK9999", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["written"] is None and payload["removed"] is None


# -- an address spent inside one commit (RK1178) ------------------------------


def outlined_project(tmp_path: Path, pointer: str = "XIV.30") -> Config:
    """An outline project with one open line pointing at an address no heading holds yet."""
    git_init(tmp_path)
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "SH"\nref_scheme = "outline"\n[files]\nroadmap = "ROADMAP.md"\n'
        'changelog = "CHANGELOG.md"\nimprovements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(
        f"## Block A — The model\n\n- {DESIGNED} **SH1** (deps: —) **A symptom worth a line** "
        f"— Because of a reason. → §{pointer}\n",
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text("## Block A — The model\n", encoding="utf-8")
    (tmp_path / "IMPROVEMENTS.md").write_text(
        "## Block A — The model\n\n### XIV.29 An older design\n\nProse here.\n",
        encoding="utf-8",
    )
    git_commit(tmp_path, f"docs: file SH1 pointing at {pointer}")
    return Config.discover(tmp_path)


def test_an_address_spent_inside_one_commit_is_read_off_the_pointer_that_left(tmp_path):
    """RK1178, observed in Shio. A task whose `section add` and whose `ship` land in the same
    commit leaves a **net-zero diff** in the prose file: the heading was in no committed tree, so
    no diff of that file mentions it, and `as_ledger` keeps no pointer either. The address then
    looked never-used and `anchors` offered it as next — an address a shipped task already spent,
    whose ledger entry's prose cites it.

    What survives is the roadmap: the line was filed carrying `→ §XIV.30` and the ship removed it.
    Worth fixing rather than tolerating because of which workflow produces it — a task that files
    its own rationale and ships in one commit is what a one-task-one-commit rule *requires*.
    """
    config = outlined_project(tmp_path)
    ship(config, "SH1", "feat: ship SH1, whose pointer left with the line")
    taken = anchors(config)
    spent = next((one for one in taken if one.anchor == "XIV.30"), None)
    assert spent is not None and not spent.live
    # And the recommendation moves past it, which is the answer a caller acts on.
    assert next_child(taken, "XIV") == "XIV.31"


def test_a_pointer_still_on_a_line_is_not_a_spent_address(tmp_path):
    """The two-command flow, which must keep working: `add --ref XIV.30` then `section add XIV.30`
    is one address being spent *now*, and counting the pointer while its line is still in the file
    would make the second command refuse what the first was told to take."""
    config = outlined_project(tmp_path)
    taken = anchors(config)
    assert not [one for one in taken if one.anchor == "XIV.30"]
    assert next_child(taken, "XIV") == "XIV.30"


def test_the_id_scheme_is_left_alone(tmp_path):
    """Under `ref_scheme = "id"` the pointer *is* the id, and retired-never-reused is the
    roadmap's own property (RK4) — so every shipped task would arrive here as an address to
    refuse. Silent there, as `_refuse_reuse` is, and for the same reason."""
    config = repo(tmp_path)
    append(
        config.path("roadmap"),
        f"- {DESIGNED} **RK7** (deps: —) **A symptom** — a reason. → §RK7\n",
    )
    git_commit(config.root, "docs: file RK7")
    ship(config, "RK7", "feat: ship RK7")
    assert not [one for one in anchors(config) if one.anchor == "RK7" and not one.live]
