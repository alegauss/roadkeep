"""One call to start a task, and the bound that makes it worth calling (RK29).

Two claims. The first is composition: the line, its rationale, its resolved deps, the
blocker chain, the leverage and the non-goals arrive together, because each of those was
already an answer and the cost being removed is the *joining*, not the computing.

The second is the one that can regress silently: **the output is bounded.** An answer that
fits in a tool result costs nothing to consult twice; one that does not gets replaced by
re-reading the file, which is exactly the 5k tokens this task exists to stop spending.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import corpora
from roadkeep.backlog import Readiness
from roadkeep.briefing import CHAINS, NON_GOALS, NothingToBrief, brief, non_goals
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config, Scope
from roadkeep.document import Document
from roadkeep.schema import DESIGNED, IDEA, SHIPPED, Schema

HERE = Path(__file__).resolve().parents[1]
#: How many non-goals Turing's roadmap declares at its pin. Exact, because the read cannot
#: move (RK105): a floor here was a bound under somebody else's list.
TURING_NON_GOALS = 7


def leads(text: str, config: Config | None = None) -> tuple[str, ...]:
    """The leads of a roadmap's non-goals, which is the only thing a brief carries of them."""
    document = Document.parse(text, Schema())
    return non_goals(config or Config(root=HERE), document).leads


ROADMAP = f"""# Roadmap

## Block A — The model

- {DESIGNED} **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- {DESIGNED} **RK4** (deps: RK1) **A fourth symptom** — Because of another. → §RK4

## Non-goals

- **No web UI and no server.** Files and a CLI.
- **No dates.** A marker is maturity, not a schedule.
"""

LEDGER = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK2** **A shipped symptom** — it was done.
"""

RATIONALE = """# Improvements

## Block A — The model

### §RK1 A first design

The reasoning, which names `roadkeep.toml`.
"""


def project(
    tmp_path: Path, roadmap: str = ROADMAP, improvements: str | None = RATIONALE
) -> Config:
    files = 'roadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    if improvements is not None:
        files += 'improvements = "IMPROVEMENTS.md"\n'
        (tmp_path / "IMPROVEMENTS.md").write_text(improvements, encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\n{files}', encoding="utf-8"
    )
    (tmp_path / "ROADMAP.md").write_text(roadmap, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(LEDGER, encoding="utf-8")
    return Config.discover(tmp_path)


# -- the composition ---------------------------------------------------------


def test_one_call_carries_every_answer(tmp_path):
    gathered = brief(project(tmp_path), "RK4")
    assert gathered.task.id == "RK4"
    assert str(gathered.readiness) == "blocked"
    assert [r.dep.id for r in gathered.deps] == ["RK1"]
    assert gathered.chains[0].root == "RK1"
    assert gathered.non_goals.leads == ("No web UI and no server.", "No dates.")
    assert gathered.leverage.of == 1


def test_the_rationale_arrives_with_the_line(tmp_path):
    gathered = brief(project(tmp_path), "RK1")
    assert gathered.view.section is not None
    assert "The reasoning" in gathered.view.section.body
    # RK12's path list rides along: what the task touches is part of starting it.
    assert [p.path for p in gathered.view.paths] == ["roadkeep.toml"]


def test_with_no_id_it_briefs_what_pick_would_choose(tmp_path):
    gathered = brief(project(tmp_path))
    assert gathered.task.id == "RK1"
    # The reason travels: a pick nobody can check is a pick nobody trusts (RK11).
    assert gathered.picked == "lowest ready id"


def test_an_explicit_id_is_not_a_pick(tmp_path):
    assert brief(project(tmp_path), "RK4").picked == ""


def test_the_pick_can_be_scoped_to_one_block(tmp_path):
    # "Start the next thing in Block B" is one call, and its absence of an answer is
    # about Block B rather than about a lower id somewhere else (RK40).
    roadmap = ROADMAP.replace(
        "## Non-goals",
        "## Block B — Authoring\n\n"
        f"- {DESIGNED} **RK8** (deps: —) **A later symptom** — Because of a reason. → §RK8\n\n"
        "## Non-goals",
    )
    gathered = brief(project(tmp_path, roadmap=roadmap), block="B")
    assert gathered.task.id == "RK8"
    assert gathered.picked == "lowest ready id in Block B"


def test_an_id_and_a_block_together_are_refused(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief", "RK1", "--block", "A"]) == EXIT_USAGE
    assert "not both" in capsys.readouterr().err


def test_the_pick_can_be_narrowed_to_written_designs(tmp_path):
    # "Execute Block A" and "plan Block A" are two questions, and only the markers tell
    # them apart (RK83): with `designed`, RK4's idea is not the answer to the first.
    roadmap = ROADMAP.replace(
        f"- {DESIGNED} **RK4**", f"- {IDEA} **RK4**"
    ).replace("(deps: RK1)", "(deps: —)")
    config = project(tmp_path, roadmap=roadmap)
    assert brief(config).task.id == "RK1"
    assert brief(config, designed=True).task.id == "RK1"
    # And with the design written on neither, the absence is about designing, not blocking.
    only_ideas = roadmap.replace(f"- {DESIGNED} **RK1**", f"- {IDEA} **RK1**")
    with pytest.raises(NothingToBrief) as caught:
        brief(project(tmp_path, roadmap=only_ideas), designed=True)
    assert "still needs designing" in caught.value.args[0]


def test_an_id_and_designed_together_are_refused(tmp_path, capsys):
    # For the reason `--block` is: an id is already the answer the search would look for.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief", "RK1", "--designed"]) == EXIT_USAGE
    assert "give an id or --designed, not both" in capsys.readouterr().err


def test_a_finished_block_is_reported_as_finished(tmp_path):
    roadmap = ROADMAP.replace("## Non-goals", "## Block B — Authoring\n\n## Non-goals")
    with pytest.raises(NothingToBrief) as caught:
        brief(project(tmp_path, roadmap=roadmap), block="B")
    assert "nothing is open in Block B" in caught.value.args[0]


def test_nothing_ready_is_refused_with_the_reason(tmp_path):
    roadmap = ROADMAP.replace("(deps: —)", "(deps: RK9)")
    with pytest.raises(NothingToBrief) as caught:
        brief(project(tmp_path, roadmap=roadmap))
    assert "every open task is blocked" in caught.value.args[0]


def test_a_shipped_task_briefs_from_the_ledger(tmp_path):
    # No deps left to state: the ledger carries none.
    gathered = brief(project(tmp_path), "RK2")
    assert gathered.view.shipped and gathered.deps == () and gathered.chains == ()
    assert "deleted on ship" in gathered.view.section_absence


def test_a_shipped_task_is_never_described_as_ready(tmp_path):
    # RK324: this is the command a session starts work with, so the word it leads with is
    # the one a caller acts on — and `show` on the same id has always answered shipped.
    gathered = brief(project(tmp_path), "RK2")
    assert gathered.readiness is Readiness.SHIPPED
    # Which is not a blocked state either: nothing shipping unblocks it, and nothing is left.
    assert gathered.readiness not in {Readiness.READY, Readiness.BLOCKED}


def test_the_chains_are_bounded_tighter_than_the_graphs_own_limit(tmp_path):
    deps = ", ".join(f"RK{n}" for n in range(20, 26))
    roadmap = (
        "# Roadmap\n\n## Block A — The model\n\n"
        + f"- {DESIGNED} **RK1** (deps: {deps}) **A symptom** — a reason. → §RK1\n"
        + "".join(
            f"- {DESIGNED} **RK{n}** (deps: —) **A symptom** — a reason. → §RK{n}\n"
            for n in range(20, 26)
        )
    )
    assert len(brief(project(tmp_path, roadmap=roadmap), "RK1").chains) == CHAINS


# -- the non-goals -----------------------------------------------------------


def test_the_heading_is_matched_by_prefix_because_no_two_projects_spell_it_alike():
    # This repository writes "## Non-goals"; Shio writes "## Non-goals (do NOT add as
    # tasks)". Neither is wrong, so neither is hardcoded.
    text = (
        "# Roadmap\n\n## Non-goals (do NOT add as tasks)\n\n"
        "- **No web UI.** Files and a CLI.\n"
    )
    assert leads(text) == ("No web UI.",)


def test_a_bullet_with_no_bold_lead_keeps_its_first_sentence():
    text = "# Roadmap\n\n## Non-goals\n\n- No server. It would be a second store.\n"
    assert leads(text) == ("No server",)


def test_the_section_ends_at_the_next_heading():
    text = (
        "# Roadmap\n\n## Non-goals\n\n- **No server.** Prose.\n\n"
        "## Block A — The model\n\n- **Not a non-goal.** Prose.\n"
    )
    assert leads(text) == ("No server.",)


def test_a_project_with_no_non_goals_section_reports_none():
    assert leads("# Roadmap\n\n## Block A\n") == ()


# -- the lead, where the file was not written to the convention (RK68) --------


def test_a_wrapped_bullet_is_read_whole_and_not_to_its_first_line():
    # Turing's first non-goal spans four lines and forbids ten things. Read to the first
    # physical line it appeared to forbid three, dropping the SSE bus and the rest.
    text = (
        "# Roadmap\n\n## Non-goals\n\n"
        "- Don't refactor the auto-trigger router, continuation logic,\n"
        "  A/B assignment, the SSE bus, or `summarizeVariables` cap — these\n"
        "  are product, not patches.\n"
    )
    assert leads(text, Config(root=HERE, non_goals=Scope(lead=200))) == (
        "Don't refactor the auto-trigger router, continuation logic, A/B assignment, "
        "the SSE bus, or `summarizeVariables` cap — these are product, not patches.",
    )


def test_a_bold_run_mid_sentence_is_emphasis_and_not_a_lead():
    # Turing writes `is **not** a path`, and the scraped lead was the word `not`.
    text = (
        "# Roadmap\n\n## Non-goals\n\n"
        "- Structured output (LLM → JSON) is **not** a path — use tool-calling schemas.\n"
    )
    assert leads(text, Config(root=HERE, non_goals=Scope(lead=200))) == (
        "Structured output (LLM → JSON) is **not** a path — use tool-calling schemas.",
    )


def test_a_lead_over_the_projects_limit_is_cut_where_the_cut_shows():
    text = "# Roadmap\n\n## Non-goals\n\n- Don't refactor the router, the bus or the cap.\n"
    assert leads(text, Config(root=HERE, non_goals=Scope(lead=30))) == (
        "Don't refactor the router, …",
    )


def test_a_governed_lead_is_never_cut_because_add_already_refused_a_long_one():
    lead = "No " + "x" * (Scope().lead - 3)
    text = f"# Roadmap\n\n## Non-goals\n\n- **{lead}** Because of a reason.\n"
    assert leads(text) == (lead,)


def test_a_section_longer_than_the_bound_says_how_many_it_left(tmp_path, capsys):
    bullets = "".join(
        f"- **No number {n}.** Because of a reason.\n" for n in range(NON_GOALS + 3)
    )
    project(tmp_path, roadmap=ROADMAP[: ROADMAP.index("- **No web")] + bullets)
    gathered = brief(Config.discover(tmp_path), "RK1")
    assert len(gathered.non_goals.leads) == NON_GOALS and gathered.non_goals.elided == 3
    assert main(["-C", str(tmp_path), "brief", "RK1"]) == EXIT_OK
    assert "not      … and 3 more under Non-goals" in capsys.readouterr().out


def test_turings_leads_are_each_a_scope_and_none_is_a_stray_word():
    # The second live corpus is where RK68's two failures actually are, and the property
    # is not a wording: it is that no lead is a fragment of the constraint it addresses.
    # At the pin (RK105), so the count is what that revision spells rather than a floor
    # under whatever Turing's list happens to say this afternoon.
    corpora.require(corpora.TURING)
    gathered = non_goals(
        corpora.config(corpora.TURING), corpora.document(corpora.TURING, "roadmap")
    )
    assert len(gathered.leads) == TURING_NON_GOALS
    for lead in gathered.leads:
        assert len(lead.split()) > 3, lead


# -- this repository ---------------------------------------------------------


def test_the_brief_here_is_bounded(governed, capsys):
    # The claim that pays for the command: it fits in a tool result. 4 KB is the ceiling
    # a section budget (250 words) plus a bounded dep list can reach.
    assert main(["-C", str(governed), "brief", "RK32"]) == EXIT_OK
    out = capsys.readouterr().out
    assert len(out) < 4000, f"a brief grew to {len(out)} characters"
    assert "not      No model and no prompts" in out


def test_every_open_task_here_briefs(governed):
    config = Config.discover(governed)
    for entry in config.document("roadmap").entries:
        gathered = brief(config, entry.task.id)
        assert gathered.non_goals.leads and gathered.view.section is not None


# -- the command -------------------------------------------------------------


def test_the_command_prints_the_pick_reason_when_it_picked(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("RK1  Block A  📋  ready  ROADMAP.md:5")
    assert "picked   lowest ready id" in out


def test_the_command_prints_the_chain_of_a_blocked_task(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief", "RK4"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "dep      RK1  open" in out
    assert "chain    RK4 → RK1" in out


def test_json_carries_the_whole_pack(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief", "RK4", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "RK4" and payload["readiness"] == "blocked"
    assert payload["deps_resolved"][0]["status"] == "open"
    assert payload["chains"][0]["path"] == ["RK4", "RK1"]
    assert payload["non_goals"] == ["No web UI and no server.", "No dates."]
    assert payload["unblocks"] == {"count": 0, "of": 1, "transitive": []}
    assert payload["picked"] is None


def test_the_command_leads_with_shipped_and_quotes_no_cost_for_it(tmp_path, capsys):
    # The measured defect (RK324): `✅  ready`, an unblocks count and a thin brief, which is
    # the shape of an answer about work that has not happened.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief", "RK2"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("RK2  Block A  ✅  shipped  CHANGELOG.md:5")
    assert "unblocks" not in out and "budget" not in out
    # And `show` still answers the same word about the same id, which is the whole point.
    assert main(["-C", str(tmp_path), "show", "RK2"]) == EXIT_OK
    assert "shipped" in capsys.readouterr().out


def test_the_json_says_shipped_where_a_client_reads_the_readiness(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief", "RK2", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["readiness"] == "shipped" and payload["shipped"] is True
    assert payload["budget"] is None


def test_nothing_to_brief_exits_two(tmp_path, capsys):
    project(tmp_path, roadmap=ROADMAP.replace("(deps: —)", "(deps: RK9)"))
    assert main(["-C", str(tmp_path), "brief"]) == EXIT_USAGE
    assert "nothing to brief" in capsys.readouterr().err


def test_an_unknown_id_exits_two(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief", "RK99"]) == EXIT_USAGE
    assert "no task RK99" in capsys.readouterr().err


# -- the finished block, in the shape it was asked for (RK409) ---------------

#: Block A declared and holding nothing: the state a loop drives a block *to*, and the one
#: whose answer is the only thing that means finished.
EMPTIED = """# Roadmap

## Block A — The model

## Non-goals

- **No web UI and no server.** Files and a CLI.
"""


def test_a_finished_block_answers_in_json_when_json_was_asked_for(tmp_path, capsys):
    """The one branch a loop reads, and the one `--json` did not cover.

    `brief --block <x>` is how a worker asks what to do next, and "nothing is open in Block
    <x>" is the only answer that means the block is finished — so a loop driving one to
    completion polls exactly this. Asked for JSON it got an empty stdout and the sentence on
    stderr, where a real failure also lands, which is the coupling `--json` exists to remove.
    """
    project(tmp_path, roadmap=EMPTIED)
    assert main(["-C", str(tmp_path), "brief", "--block", "A", "--json"]) == EXIT_USAGE
    payload = json.loads(capsys.readouterr().out)
    assert payload["brief"] is None
    assert payload["empty"] is True
    assert payload["block"] == "A"
    assert payload["reason"] == "nothing is open in Block A"


def test_the_empty_answer_is_never_a_success(tmp_path, capsys):
    # Nothing to brief is still nothing to brief: at exit 0 a typo'd block name would look
    # exactly like a finished one, and the payload is what tells those apart instead.
    project(tmp_path, roadmap=EMPTIED)
    assert main(["-C", str(tmp_path), "brief", "--block", "A", "--json"]) == EXIT_USAGE
    capsys.readouterr()
    # A block nothing declares never reaches that branch at all — it is a different refusal,
    # and it stays prose on stderr with no payload to mistake for an empty one.
    assert main(["-C", str(tmp_path), "brief", "--block", "Z", "--json"]) == EXIT_USAGE
    out = capsys.readouterr()
    assert out.out == ""
    assert "no heading declares Block Z" in out.err


def test_without_json_the_finished_block_still_answers_in_prose(tmp_path, capsys):
    project(tmp_path, roadmap=EMPTIED)
    assert main(["-C", str(tmp_path), "brief", "--block", "A"]) == EXIT_USAGE
    out = capsys.readouterr()
    assert out.out == ""
    assert "nothing is open in Block A" in out.err


def test_the_reason_is_carried_and_never_reconstructed_from_the_message():
    # Two spellings of one sentence is one that goes wrong the first time either is
    # reworded — and `KeyError` quotes its own `str`, which is the half that would.
    nothing = NothingToBrief("nothing is open in Block A")
    assert nothing.reason == "nothing is open in Block A"
    assert nothing.reason not in ("", str(nothing))
