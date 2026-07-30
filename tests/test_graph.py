"""The dep graph, walked both ways (RK13).

Four claims, one per answer the traversal exists to give: the chain names the task to
start, the closure says what has to happen first, leverage is derivable where value is
not, and a cycle is a defect rather than a shape.

The fifth claim is quieter and is what makes the other four correct: a **block or range
dep is expanded to its open members** before the walk. A traversal that treats `Block B`
as opaque does not answer "what has to happen first" — it answers a smaller question and
looks like it answered the big one.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.backlog import Backlog, DepStatus
from roadkeep.cli import EXIT_OK, main
from roadkeep.config import Config
from roadkeep.graph import SHOWN, Graph
from roadkeep.schema import DESIGNED, SHIPPED

HERE = Path(__file__).resolve().parents[1]


def line(task_id: str, deps: str = "—", block: str = "A") -> str:
    return (
        f"- {DESIGNED} **{task_id}** (deps: {deps}) **A symptom for {task_id}** "
        f"— a reason. → §{task_id}\n"
    )


def project(tmp_path: Path, roadmap: str, changelog: str = "") -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(roadmap, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        changelog or "# Shipped\n\n## Block A — The model\n", encoding="utf-8"
    )
    return Config.discover(tmp_path)


A = "## Block A — The model\n"
B = "\n## Block B — Authoring\n"


def graph(tmp_path: Path, roadmap: str, changelog: str = "") -> Graph:
    return Graph.load(project(tmp_path, roadmap, changelog))


# -- forward: what has to happen first ---------------------------------------


def test_the_blocker_set_is_transitive(tmp_path):
    g = graph(tmp_path, A + line("RK1", "RK2") + line("RK2", "RK3") + line("RK3"))
    assert g.blockers("RK1") == {"RK2", "RK3"}
    assert g.blockers("RK3") == frozenset()


def test_a_satisfied_dep_is_not_an_edge(tmp_path):
    g = graph(
        tmp_path,
        A + line("RK9", f"RK1 {SHIPPED}"),
        changelog=f"# Shipped\n\n{A}\n- {SHIPPED} **RK1** **Done** — done.\n",
    )
    assert g.blockers("RK9") == frozenset() and g.chains("RK9") == ()


def test_the_chain_names_the_task_to_start(tmp_path):
    # "RK1 is blocked" is not actionable; the chain ending in a ready task is.
    g = graph(tmp_path, A + line("RK1", "RK2") + line("RK2", "RK3") + line("RK3"))
    (chain,) = g.chains("RK1")
    assert chain.render("RK1") == "RK1 → RK2 → RK3"
    assert chain.root == "RK3" and "ready to start" in chain.detail


def test_a_chain_can_end_outside_the_backlog(tmp_path):
    g = graph(tmp_path, A + line("RK1", "RK2") + line("RK2", "real design partners"))
    (chain,) = g.chains("RK1")
    assert chain.end is DepStatus.UNRESOLVABLE
    assert "shipping cannot satisfy it" in chain.detail


def test_a_chain_can_end_on_an_id_in_neither_file(tmp_path):
    g = graph(tmp_path, A + line("RK1", "RK77"))
    (chain,) = g.chains("RK1")
    assert chain.end is DepStatus.UNKNOWN and chain.root == "RK77"


def test_a_block_dep_is_expanded_to_its_open_members(tmp_path):
    # The claim that makes transitive readiness true rather than smaller: RK9 waits on
    # Block B, whose only open task waits on RK4, so RK4 is what has to happen first.
    g = graph(
        tmp_path,
        A + line("RK9", "Block B") + line("RK4") + B + line("RK5", "RK4", block="B"),
    )
    assert g.blockers("RK9") == {"RK5", "RK4"}
    (chain,) = g.chains("RK9")
    assert chain.render("RK9") == "RK9 → RK5 (via Block B) → RK4"


def test_a_block_no_heading_declares_is_a_terminal_hop(tmp_path):
    # RK37 one level up: there is nothing to expand, and waiting on it is not waiting
    # on tasks — so the walk must stop rather than report an empty chain as ready.
    g = graph(tmp_path, A + line("RK9", "Block Z"))
    (chain,) = g.chains("RK9")
    assert chain.end is DepStatus.UNRESOLVABLE and chain.root == "Block Z"


def test_a_range_dep_is_expanded_too(tmp_path):
    g = graph(tmp_path, A + line("RK9", "RK20–RK30") + line("RK25", "RK4") + line("RK4"))
    assert g.blockers("RK9") == {"RK25", "RK4"}


def test_the_chain_report_is_bounded(tmp_path):
    # A wide graph has combinatorially many paths, and a report nobody reads is the
    # failure this command exists to fix.
    deps = ", ".join(f"RK{n}" for n in range(20, 20 + SHOWN + 3))
    roadmap = A + line("RK1", deps) + "".join(
        line(f"RK{n}") for n in range(20, 20 + SHOWN + 3)
    )
    assert len(graph(tmp_path, roadmap).chains("RK1")) == SHOWN


# -- reverse: leverage -------------------------------------------------------


def test_leverage_counts_what_shipping_would_unblock(tmp_path):
    g = graph(
        tmp_path,
        A + line("RK1") + line("RK2", "RK1") + line("RK3", "RK2") + line("RK4"),
    )
    leverage = g.leverage("RK1")
    assert leverage.direct == ("RK2",)
    assert leverage.transitive == ("RK2", "RK3") and leverage.count == 2
    # The denominator is the other open tasks: a count with no total means nothing.
    assert leverage.of == 3
    assert g.leverage("RK4").count == 0


def test_leverage_sees_a_dependent_that_named_a_block(tmp_path):
    g = graph(tmp_path, A + line("RK9", "Block B") + B + line("RK5", "—", block="B"))
    assert g.leverage("RK5").transitive == ("RK9",)


# -- the defect --------------------------------------------------------------


def test_a_cycle_is_reported_as_a_group_not_a_path(tmp_path):
    g = graph(tmp_path, A + line("RK1", "RK2") + line("RK2", "RK1"))
    assert g.cycles() == (("RK1", "RK2"),)
    # Entering from either node reports the same group: rotated twice would read as two.
    assert g.cycle_of("RK1") == g.cycle_of("RK2") == ("RK1", "RK2")


def test_a_longer_cycle_and_a_separate_one_are_two_groups(tmp_path):
    g = graph(
        tmp_path,
        A
        + line("RK1", "RK2")
        + line("RK2", "RK3")
        + line("RK3", "RK1")
        + line("RK8", "RK9")
        + line("RK9", "RK8"),
    )
    assert g.cycles() == (("RK1", "RK2", "RK3"), ("RK8", "RK9"))


def test_a_task_outside_a_cycle_reports_none(tmp_path):
    g = graph(tmp_path, A + line("RK1", "RK2") + line("RK2", "RK1") + line("RK7"))
    assert g.cycle_of("RK7") == ()


def test_a_chain_into_a_cycle_says_so_instead_of_looping(tmp_path):
    g = graph(tmp_path, A + line("RK1", "RK2") + line("RK2", "RK3") + line("RK3", "RK2"))
    chains = g.chains("RK1")
    assert any("a cycle" in chain.detail for chain in chains)


def test_a_clean_backlog_has_no_cycles(tmp_path):
    g = graph(tmp_path, A + line("RK1", "RK2") + line("RK2"))
    assert g.cycles() == ()


# -- this repository ---------------------------------------------------------


def test_this_backlog_has_no_cycle_and_a_measurable_gap():
    g = Graph.load(Config.discover(HERE))
    assert g.cycles() == ()
    ranked = sorted(
        ((g.leverage(task).count, task) for task in g.edges), reverse=True
    )
    top, least = ranked[0], ranked[-1]
    if top[0] == 0:
        # The measurement is exhausted, not broken: RK23 was the last open task any other
        # open task waited on, so nothing left blocks anything. A flat graph is still a
        # statement worth failing on — every open line is ready, which is what `pick` reads,
        # and a cycle or an unsatisfied dep would break it.
        assert all(not g.blockers(task) for task in g.edges)
        return
    # §RK13's measurement, now derived: one task sits in several blocker sets and the tail
    # sits in none — the gap no reading of the file makes visible. Asserted as a gap and
    # not a threshold: shipping the most-blocking task collapses the top count (RK14 went
    # from 15 dependents to zero the moment it landed), and a bound that has to be edited
    # by the commit that shipped it gets edited without being read.
    assert top[0] > least[0] and least[0] == 0


@pytest.mark.parametrize(
    ("path", "prefix"),
    [
        ("D:/Git/viglet/shio/latest/docs/ROADMAP.md", "SH"),
        ("D:/Git/viglet/turing/latest/docs/ROADMAP.md", "T"),
    ],
)
def test_a_live_backlog_is_walked_without_looping(path, prefix):
    # The traversal has to terminate on files it did not write, cycles or not.
    source = Path(path)
    if not source.exists():
        pytest.skip(f"{source} is not on this machine")
    config = Config.parse(
        {
            "prefix": prefix,
            "ref_scheme": "outline",
            "files": {"roadmap": source.name},
        },
        root=source.parent,
    )
    g = Graph.of(Backlog.load(config))
    assert g.edges
    for task in g.edges:
        g.chains(task)
        g.leverage(task)
    g.cycles()


# -- the command -------------------------------------------------------------


def test_the_command_prints_the_chain_and_the_leverage(tmp_path, capsys):
    project(tmp_path, A + line("RK1", "RK2") + line("RK2", "RK3") + line("RK3"))
    assert main(["-C", str(tmp_path), "deps", "RK1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "chain    RK1 → RK2 → RK3" in out
    assert "unblocks 0 of 2 open" in out


def test_the_command_prints_the_leverage_of_a_task_with_no_deps(tmp_path, capsys):
    project(tmp_path, A + line("RK1") + line("RK2", "RK1"))
    assert main(["-C", str(tmp_path), "deps", "RK1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "RK1: ready (no deps)" in out
    assert "unblocks 1 of 1 open: RK2" in out


def test_the_command_names_a_cycle(tmp_path, capsys):
    project(tmp_path, A + line("RK1", "RK2") + line("RK2", "RK1"))
    assert main(["-C", str(tmp_path), "deps", "RK1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "cycle    RK1 ↔ RK2" in out
    assert "nothing in this group can be started" in out


def test_json_carries_both_directions(tmp_path, capsys):
    project(tmp_path, A + line("RK1", "Block B") + B + line("RK5", "RK4", block="B") + line("RK4", block="B"))
    assert main(["-C", str(tmp_path), "deps", "RK1", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["blockers"] == ["RK4", "RK5"]
    assert payload["chains"][0]["path"] == ["RK1", "RK5", "RK4"]
    assert payload["chains"][0]["via"] == ["Block B", "RK4"]
    assert payload["cycle"] == []
    assert payload["unblocks"] == {
        "direct": [],
        "transitive": [],
        "count": 0,
        "of": 2,
    }
