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
    anchors,
    commits_touching,
    gaps,
    git_available,
    next_child,
    origin_of,
    searchable,
)
from roadkeep.sections import AnchorRetired
from roadkeep.sections import add as add_section
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
    return commit(config.root, message)


def unwrite(config: Config, heading: str, message: str) -> str:
    path = config.path("improvements")
    kept = [
        line
        for line in path.read_text(encoding="utf-8").splitlines(keepends=True)
        if line.rstrip("\n") != heading
    ]
    path.write_text("".join(kept), encoding="utf-8")
    return commit(config.root, message)


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
    commit(config.root, "docs: import the outline")
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


def test_an_address_nothing_ever_declared_is_written(tmp_path):
    # The refusal is about reuse and never about the scheme: a fresh address still writes.
    config = outlined(tmp_path)
    design(config, "## XXXVII The family", "docs: open the family")
    design(config, "### XXXVII.1 A first design", "docs: file it")
    unwrite(config, "### XXXVII.1 A first design", "feat: it works (RK1)")
    config = Config.discover(tmp_path)

    document, section = add_section(config, "improvements", "XXXVII.2", "A design", "Prose.")
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

    document, section = add_section(config, "improvements", "RK2", "A design", "Prose.")
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
