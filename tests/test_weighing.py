"""What a comparable task cost, derived rather than stored (RK71).

Two claims are worth a test and the rest is arithmetic. The first is the derivation: the
number comes from the commit that wrote the ledger entry, so it is right after a squash, an
amend or a rebase — the same property that made RK31's pointer derived. The second is the
boundary: nothing here ranks work and nothing lands on a line, because the non-goal against a
size field is binding and a cheapness tier would defer the architectural tasks.

The last test is the conformance one: this repository's own ledger is the corpus §RK71 was
measured on, so the numbers it states have to come back out of the command.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from conftest import git, git_init, git_commit

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.history import added_ids, costs_of, git_available
from roadkeep.kernel.schema import SHIPPED
from roadkeep.serving import TOOLS
from roadkeep.weighing import COMPARABLES, Spread, weigh

HERE = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(not git_available(), reason="git is not on PATH")




def repo(tmp_path: Path) -> Config:
    git_init(tmp_path)
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text("## Block A — The model\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "## Block A — The model\n\n## Block B — Authoring\n", encoding="utf-8"
    )
    git_commit(tmp_path, "chore: bootstrap")
    return Config.discover(tmp_path)




def ship(config: Config, task_id: str, block: str = "A", weight: int = 3) -> str:
    """Write a ledger entry under ``block`` in a commit that also changes ``weight`` lines."""
    ledger = config.path("changelog")
    lines = ledger.read_text(encoding="utf-8").splitlines(keepends=True)
    entry = f"- {SHIPPED} **{task_id}** **A symptom** — a reason.\n"
    at = next(
        (n for n, line in enumerate(lines) if line.startswith(f"## Block {block}")), 0
    )
    lines.insert(at + 1, entry)
    ledger.write_text("".join(lines), encoding="utf-8")
    (config.root / f"{task_id}.py").write_text(
        "".join(f"line {n}\n" for n in range(weight)), encoding="utf-8"
    )
    return git_commit(config.root, f"feat: {task_id}")


# -- the derivation -----------------------------------------------------------


def test_the_weight_is_the_commit_that_wrote_the_entry(tmp_path):
    config = repo(tmp_path)
    ship(config, "RK1", weight=10)
    weights = weigh(config)
    assert [w.task_id for w in weights.weighed] == ["RK1"]
    # One entry line plus the ten in the file beside it: what the commit changed, both
    # sides, across every file — which is the number §RK71 measured the corpus with.
    assert weights.weighed[0].lines == 11
    assert weights.weighed[0].files == 2


def test_the_answer_survives_a_history_rewrite(tmp_path):
    # The property that makes it derived rather than stored (RK31): a hash written into the
    # ledger would be dead after this, and a dead hash reads exactly like a live one.
    config = repo(tmp_path)
    ship(config, "RK1", weight=10)
    before = weigh(config).weighed[0]
    git(config.root, "commit", "--quiet", "--amend", "-m", "feat: RK1 reworded")
    after = weigh(config).weighed[0]
    assert after.lines == before.lines and after.commit != before.commit


def test_one_git_call_per_question_and_not_one_per_id(tmp_path):
    # 69 ids is 69 processes on the pickaxe route, which is a query nobody runs twice.
    config = repo(tmp_path)
    for number in range(1, 6):
        ship(config, f"RK{number}", weight=number * 10)
    shipped = added_ids(config, "changelog")
    assert set(shipped) == {"RK1", "RK2", "RK3", "RK4", "RK5"}
    assert len(costs_of(config, tuple(dict.fromkeys(shipped.values())))) == 5


def test_an_entry_no_commit_accounts_for_is_counted_and_never_guessed_at(tmp_path):
    # A squash, a shallow clone, an entry that never reached a commit: an absent answer is
    # not a cheap task (RK28), so it is named rather than folded into the distribution.
    config = repo(tmp_path)
    ship(config, "RK1", weight=10)
    ledger = config.path("changelog")
    ledger.write_text(
        ledger.read_text(encoding="utf-8")
        + f"- {SHIPPED} **RK2** **Never committed** — a reason.\n",
        encoding="utf-8",
    )
    weights = weigh(Config.discover(config.root))
    assert weights.unresolved == ("RK2",)
    assert [w.task_id for w in weights.weighed] == ["RK1"]


def ship_together(config: Config, ids: tuple[str, ...], block: str = "A", weight: int = 3):
    """Write several ledger entries in **one** commit — the adoption import's shape."""
    ledger = config.path("changelog")
    lines = ledger.read_text(encoding="utf-8").splitlines(keepends=True)
    at = next(
        (n for n, line in enumerate(lines) if line.startswith(f"## Block {block}")), 0
    )
    for task_id in reversed(ids):
        lines.insert(at + 1, f"- {SHIPPED} **{task_id}** **A symptom** — a reason.\n")
    ledger.write_text("".join(lines), encoding="utf-8")
    (config.root / f"{'_'.join(ids)}.py").write_text(
        "".join(f"line {n}\n" for n in range(weight)), encoding="utf-8"
    )
    return git_commit(config.root, f"feat: {', '.join(ids)}")


# -- one commit, many entries, one number (RK94) ------------------------------


def test_a_batch_is_left_out_of_the_distributions_rather_than_divided(tmp_path):
    # Dividing invents a per-task cost: 20963 over 47 entries is 446 apiece, a number no
    # commit contains and `git show` cannot refute — which is the one property this has.
    config = repo(tmp_path)
    ship(config, "RK1", weight=10)
    ship_together(config, ("RK2", "RK3", "RK4"), weight=300)
    weights = weigh(Config.discover(config.root))
    assert weights.co_shipped == ("RK2", "RK3", "RK4")
    # The percentiles describe the one entry whose commit is its own, and nothing else.
    assert weights.lines.count == 1 and weights.lines.median == 11
    # And the batch keeps its real numbers in the list, which is what a reader checks.
    batched = {w.task_id: w for w in weights.weighed}
    assert batched["RK2"].lines == 303 and batched["RK2"].shared == 3
    assert not batched["RK2"].alone and batched["RK1"].alone


def test_the_batch_is_the_same_batch_inside_a_scope(tmp_path):
    # How many entries a commit wrote is a fact about the commit (RK94): a `--block` question
    # seeing only its own two of the three would call a batch a task.
    config = repo(tmp_path)
    ship_together(config, ("RK1", "RK2"), block="A", weight=300)
    ship_together(config, ("RK3",), block="B", weight=10)
    weights = weigh(Config.discover(config.root), "A")
    assert weights.co_shipped == ("RK1", "RK2") and weights.lines.count == 0
    assert str(weights.lines) == "nothing shipped"


def test_a_block_of_only_batched_entries_keeps_its_row(tmp_path):
    # An empty spread reads as "nothing comparable here"; a missing row reads as no block.
    config = repo(tmp_path)
    ship(config, "RK1", block="A", weight=10)
    ship_together(config, ("RK2", "RK3"), block="B", weight=50)
    by_block = weigh(Config.discover(config.root)).by_block()
    assert set(by_block) == {"A", "B"}
    assert by_block["A"].count == 1 and by_block["B"].count == 0


def test_a_batch_is_not_offered_as_a_recent_comparable(tmp_path):
    # "The last three comparables" is a question about what a task costs, and a batch is
    # not comparable to the line being written.
    config = repo(tmp_path)
    ship(config, "RK1", weight=10)
    ship_together(config, ("RK2", "RK3"), weight=500)
    assert [w.task_id for w in weigh(Config.discover(config.root)).recent] == ["RK1"]


def test_the_command_names_what_it_left_out(tmp_path, capsys):
    config = repo(tmp_path)
    ship(config, "RK1", weight=10)
    ship_together(config, ("RK2", "RK3"), weight=500)
    assert main(["-C", str(config.root), "weight", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["co_shipped"] == ["RK2", "RK3"]
    # The exclusions are ids and not records, so they are never behind `--records` (RK264):
    # they are what says the distribution is over fewer entries than the ledger holds.
    assert payload["weighed"] == [] and payload["weighed_elided"] == 3
    assert main(["-C", str(config.root), "weight", "--records", "--json"]) == EXIT_OK
    assert [w["shared"] for w in json.loads(capsys.readouterr().out)["weighed"]] == [1, 2, 2]
    assert main(["-C", str(config.root), "weight"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "batched  2 entr(ies) left out" in out and "RK2, RK3" in out


def test_a_block_is_weighed_against_the_whole_ledger(tmp_path):
    config = repo(tmp_path)
    ship(config, "RK1", block="A", weight=100)
    ship(config, "RK2", block="B", weight=10)
    weights = weigh(config, "B")
    assert weights.block == "B" and weights.lines.count == 1
    assert weights.lines.median == 11
    # The number the block is being compared against travels with it: a block median means
    # nothing without the ledger's.
    assert weights.everywhere.count == 2 and weights.everywhere.high == 101


def test_the_recent_comparables_are_the_last_ones_newest_first(tmp_path):
    config = repo(tmp_path)
    for number in range(1, COMPARABLES + 3):
        ship(config, f"RK{number}", weight=number)
    recent = weigh(config).recent
    assert len(recent) == COMPARABLES
    assert [w.task_id for w in recent] == ["RK5", "RK4", "RK3"]


def test_nothing_shipped_is_an_answer_and_not_a_zero(tmp_path):
    weights = weigh(repo(tmp_path))
    assert weights.weighed == () and str(weights.lines) == "nothing shipped"


def test_the_percentiles_are_values_somebody_can_open(tmp_path):
    # Nearest rank, no interpolation: every number printed is a commit that exists, and an
    # interpolated 811.4 is nobody's commit.
    spread = Spread.of((100, 200, 300, 400))
    assert spread.median == 250  # the one exception, and it is the median's definition
    assert (spread.low, spread.p25, spread.p75, spread.p90, spread.high) == (
        100,
        200,
        300,
        400,
        400,
    )


# -- the boundary -------------------------------------------------------------


def test_it_ranks_nothing_and_writes_nothing(tmp_path):
    """Stated as a test so nothing later promises it: no `pick` tier reads a weight, and no
    write door takes one. A cheapness tier would defer the architectural tasks, which are
    where the leverage is, and a field on the line is the non-goal §RK72 argued."""
    config = repo(tmp_path)
    ship(config, "RK1", weight=10)
    before = config.path("roadmap").read_text(encoding="utf-8")
    assert main(["-C", str(config.root), "weight"]) == EXIT_OK
    assert config.path("roadmap").read_text(encoding="utf-8") == before
    served = next(tool for tool in TOOLS if tool.name == "weight")
    assert not served.writes and served.unconditional == ("block", "records")


# -- the command --------------------------------------------------------------


def test_the_command_prints_both_axes_and_the_blocks(tmp_path, capsys):
    config = repo(tmp_path)
    ship(config, "RK1", block="A", weight=10)
    ship(config, "RK2", block="B", weight=20)
    assert main(["-C", str(config.root), "weight"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("CHANGELOG.md  2 weighed")
    assert "  lines    11–21" in out
    assert "  files    2–2" in out
    assert "  block A  " in out and "  block B  " in out


def test_the_scoped_command_names_the_comparables_with_their_commit(tmp_path, capsys):
    config = repo(tmp_path)
    ship(config, "RK1", block="A", weight=10)
    assert main(["-C", str(config.root), "weight", "--block", "A"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "Block A  1 weighed" in out
    assert "  ledger   " in out
    assert "RK1       11 lines    2 files" in out


def test_the_json_carries_every_weight_and_both_distributions(tmp_path, capsys):
    config = repo(tmp_path)
    ship(config, "RK1", weight=10)
    assert main(["-C", str(config.root), "weight", "--records", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["block"] is None and payload["file"] == "CHANGELOG.md"
    assert payload["weighed"][0]["id"] == "RK1"
    assert payload["weighed"][0]["lines"] == 11 and payload["weighed"][0]["files"] == 2
    assert payload["lines"]["median"] == 11 and payload["files"]["median"] == 2
    assert payload["blocks"]["A"]["count"] == 1
    assert payload["unresolved"] == [] and payload["weighed_elided"] == 0


# -- the sample the percentiles summarise (RK264) -----------------------------


def test_the_distribution_arrives_without_the_sample_it_summarises(tmp_path, capsys):
    # Measured before it was written: 22.7k of 23.7k characters were this array, and
    # `--block F` only moved that to 89% — the read priced to save context spending it.
    config = repo(tmp_path)
    for number in range(1, 6):
        ship(config, f"RK{number}", weight=10 * number)
    assert main(["-C", str(config.root), "weight", "--json"]) == EXIT_OK
    bare = capsys.readouterr().out
    assert main(["-C", str(config.root), "weight", "--records", "--json"]) == EXIT_OK
    full = capsys.readouterr().out
    assert len(bare) < len(full)
    # The figure is the one thing this command may not get wrong, so it is the same figure.
    assert json.loads(bare)["lines"] == json.loads(full)["lines"]
    assert json.loads(bare)["weighed_elided"] == len(json.loads(full)["weighed"]) == 5


def test_what_was_left_out_is_named_and_never_capped(tmp_path, capsys):
    # A count and not a top-N: a sample nobody chose would make the p90 a statement about
    # that sample, which is the one number this may not misreport (RK10's rule, one over).
    config = repo(tmp_path)
    for number in range(1, 4):
        ship(config, f"RK{number}", weight=10 * number)
    assert main(["-C", str(config.root), "weight"]) == EXIT_OK
    assert "records  3 not shown — `--records` prints them" in capsys.readouterr().out
    assert main(["-C", str(config.root), "weight", "--records"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.count("  record   ") == 3 and "not shown" not in out


def test_no_history_is_reported_as_absent_and_not_as_zero(tmp_path):
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nchangelog = "CHANGELOG.md"\n', encoding="utf-8"
    )
    (tmp_path / "CHANGELOG.md").write_text("## Block A\n", encoding="utf-8")
    # No repository at all, which is the shape a `uvx` run in a tarball has.
    assert main(["-C", str(tmp_path), "weight"]) == EXIT_USAGE


# -- this repository, which is the corpus §RK71 measured ----------------------


def test_this_ledgers_own_spread_is_the_one_the_design_states():
    # 63 tasks then, more now, so the claims that hold are the shape ones: the spread is
    # an order of magnitude, the median a few hundred lines, the architectural tasks the tail.
    weights = weigh(Config.discover(HERE))
    assert weights.lines.count > 60
    # At most one: the entry `ship` wrote this turn has no commit until the commit that
    # carries the code, which is the one-task-one-commit rule stated as a number.
    assert len(weights.unresolved) <= 1, weights.unresolved
    assert weights.lines.high > 20 * weights.lines.low
    # The third collision came, and it was the claim (RK364). Measured in ledger order, in
    # quarters of ~90 entries: median 349, 218, 160, 154 — the first 63, which is the corpus
    # §RK71 read, sit at 402 and everything after them at 174. So the median is not being moved
    # by a run of small tasks on a long ledger; the tasks got smaller, monotonically, and the
    # rule that did it is one task one commit. A floor tracking that down is a record of where
    # the median has been, which is why this one stops tracking it.
    #
    # 100 is the floor the claim was always about: *tens* would mean granularity stopped being
    # true — a backlog of trivia the one-commit rule is manufacturing rather than measuring —
    # and hundreds mean it holds. It is far from the reading (154 at 359 entries) on purpose,
    # because a bound landed on twice is a bound chosen for the wrong reason. What ages here is
    # the number and not the shape, so the shape is what the assertions below are.
    assert 100 <= weights.lines.median < 500
    assert weights.files.median < weights.lines.median  # the axis that does not vary
    # The comparison the "no size field" non-goal argues from, held here rather than in the
    # five prose copies that stated it as two ranges and drifted (RK367). Scale-free on
    # purpose: p90 over median holds where 26-to-1384 has not, and the claim was never the
    # range — it is that the axis an agent pays is the flatter one. 1.5 and not the reading
    # (2.7 against 1.4, so 1.9) for the reason the median's floor is far from its: a bound
    # landed on is a bound chosen for the wrong reason. Cross-multiplied to stay in ints.
    assert weights.lines.p90 * weights.files.median * 2 > 3 * weights.files.p90 * weights.lines.median
    heavy = {w.task_id for w in weights.weighed if w.lines > 800}
    assert {"RK2", "RK6", "RK9", "RK10", "RK18", "RK22", "RK32", "RK48"} <= heavy


def test_a_partial_entry_is_accounted_for_by_the_commit_that_carries_it(tmp_path):
    """RK1175. `ship --part` writes the qualifier inside the bold span — which is where the corpus
    writes it and what the grammar reads (RK121) — and this search read the bare id, so a partial
    entry matched nothing and was reported as accounted for by no commit. Permanently: the
    qualifier stays until the completing ship.

    Measured here as the state that found it: two partial ships in flight, both in commits, both
    listed as missing — and the distribution silently over fewer entries than it stated (RK94).
    """
    config = repo(tmp_path)
    ledger = config.path("changelog")
    lines = ledger.read_text(encoding="utf-8").splitlines(keepends=True)
    lines.insert(1, f"- {SHIPPED} **RK7 (the local half)** **A symptom** — it half shipped.\n")
    ledger.write_text("".join(lines), encoding="utf-8")
    (config.root / "RK7.py").write_text("one\ntwo\n", encoding="utf-8")
    git_commit(config.root, "feat: ship half of RK7")
    weights = weigh(config)
    assert weights.unresolved == ()
    assert [one.task_id for one in weights.weighed] == ["RK7"]


# -- the list that outgrew the argv (RK1315) ----------------------------------


def test_the_commit_list_is_fed_and_not_spelled_into_the_argv():
    """Measured here at the commit that crossed it: 802 ledger entries, 798 distinct
    commits, 32,718 characters of shas alone against Windows' CreateProcess limit of
    32,767. `weigh` raised `HistoryUnavailable`, which its caller reports as an absent
    answer — so the verb that says what a comparable task cost stopped answering at exactly
    the ledger size that makes the question worth asking.

    Held on the call and not on a number: a test asserting 798 would pass the day the
    ledger shrank and fail the day it grew, and neither is about the defect. What is true
    whatever the size is that the revisions leave on stdin and the argv stays short.
    """
    import roadkeep.history as history

    seen: dict[str, object] = {}

    def watched(root, *args, fed=()):
        seen["args"] = args
        seen["fed"] = fed
        return b""

    original = history._bytes
    history._bytes = watched
    try:
        history.costs_of(_config(), tuple(f"{n:040x}" for n in range(2000)))
    finally:
        history._bytes = original

    assert "--stdin" in seen["args"]
    # Two git calls whatever the size of the ledger is the property this read was written
    # for, so the fix is the transport and never a batch loop that grows with the file.
    assert len(seen["fed"]) == 2000
    assert not [one for one in seen["args"] if len(one) == 40]


def _config():
    from roadkeep.config import Config

    return Config.discover(Path(__file__).resolve().parents[1])
