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

from conftest import git_commit, git_init

import corpora
from roadkeep.backlog import Readiness, Stage
from roadkeep.briefing import CHAINS, NON_GOALS, NothingToBrief, brief, non_goals
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config, Scope
from roadkeep.kernel.document import Document
from roadkeep.kernel.schema import DESIGNED, IDEA, SHIPPED, Schema

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


def test_a_block_declared_and_never_filed_is_reported_as_empty(tmp_path):
    # Named `finished` until RK429, which is the defect rather than the fixture: the
    # ledger files nothing under Block B here, so this is a heading opened before its
    # lines — and the sentence it used to answer with was the one a shipped block gave.
    roadmap = ROADMAP.replace("## Non-goals", "## Block B — Authoring\n\n## Non-goals")
    with pytest.raises(NothingToBrief) as caught:
        brief(project(tmp_path, roadmap=roadmap), block="B")
    assert "Block B is empty" in caught.value.args[0]
    assert caught.value.standing.stage is Stage.EMPTY


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
    assert payload["reason"].startswith("Block A is finished")
    # The boolean could not carry the third state and still cannot (RK429) — `empty` is
    # true here, for a finished block, for a heading before its lines and for a backlog
    # whose every line is blocked. The word beside it is what a loop branches on.
    assert payload["standing"] == {
        "block": "A",
        "state": "finished",
        "open": 0,
        "recorded": 1,
        "paused": 0,
        "sentence": payload["reason"],
    }


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
    assert "Block A is finished" in out.err


def test_the_reason_is_carried_and_never_reconstructed_from_the_message():
    # Two spellings of one sentence is one that goes wrong the first time either is
    # reworded — and `KeyError` quotes its own `str`, which is the half that would.
    nothing = NothingToBrief("nothing is open in Block A")
    assert nothing.reason == "nothing is open in Block A"
    assert nothing.reason not in ("", str(nothing))


# -- a dep that shipped after the design was written (RK1163) -----------------


def committed(tmp_path: Path) -> Config:
    """This file's project, in a repository — RK4 depends on RK1, and §RK4 is its design."""
    config = project(tmp_path, improvements=RATIONALE + "\n### §RK4 A design with a trade-off\n\nBoth sides argued here.\n")
    git_init(tmp_path)
    git_commit(tmp_path, "docs: file the backlog and its designs")
    return config


def test_a_dep_that_shipped_after_the_design_was_written_is_said_beside_it(tmp_path, capsys):
    """Measured on a real run: a task asked whether a check should widen and its rationale argued
    both sides; the dep then shipped a unique index, deleting one side of the trade-off. The
    section still read as an open question and `brief` handed it over verbatim beside
    `deps_resolved: shipped` — both facts on screen, nothing joining them.

    An **ordering** and never a claim about the prose (L4): what changed is in the dep's commit,
    so that commit is what this names and the reader decides.
    """
    committed(tmp_path)
    # RK1 ships *after* the design above was written, which is the whole fact this reports.
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "It works now."]) == EXIT_OK
    capsys.readouterr()
    git_commit(tmp_path, "feat: ship RK1, which settles half of RK4's question")

    assert main(["-C", str(tmp_path), "brief", "RK4"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "after this design was last written" in printed

    assert main(["-C", str(tmp_path), "brief", "RK4", "--json"]) == EXIT_OK
    (dep,) = json.loads(capsys.readouterr().out)["deps_resolved"]
    assert dep["dep"] == "RK1"
    assert dep["settled_since"]["shipped"]["subject"].startswith("feat: ship RK1")
    assert dep["settled_since"]["revised"]["subject"].startswith("docs: file the backlog")
    # Four fields and not five (RK1163, wired for real in RK1170): a commit rides here as an
    # *address*, and a `brief` is a bounded answer — one whole commit message inside it would be
    # the paragraph nobody asked for. The full record is what `origin` answers with, that read
    # being about the commit rather than about the line this dep blocks.
    assert set(dep["settled_since"]["shipped"]) == {"sha", "short", "date", "subject"}


def test_a_design_written_after_its_dep_shipped_says_nothing(tmp_path, capsys):
    """The control, and the reason this is a note rather than a nag: a design revised *after* the
    ship has already read what changed, and a line there would be noise on every brief."""
    committed(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "It works now."]) == EXIT_OK
    capsys.readouterr()
    git_commit(tmp_path, "feat: ship RK1 first")

    # The design is rewritten afterwards, so it has already read what the ship changed.
    assert main(
        ["-C", str(tmp_path), "section", "amend", "RK4", "--body", "Rewritten after the ship."]
    ) == EXIT_OK
    capsys.readouterr()
    git_commit(tmp_path, "docs: rewrite RK4's design afterwards")

    assert main(["-C", str(tmp_path), "brief", "RK4"]) == EXIT_OK
    assert "after this design was last written" not in capsys.readouterr().out


# -- the allowance for the write about to be made (RK1174) --------------------


def test_the_brief_states_the_ledgers_allowance_beside_the_lines_own(tmp_path, capsys):
    """Measured across four ships in one session: three were refused for `why.too-long` on the
    first attempt, each costing the round trip the budget line exists to prevent. The number
    shown was the roadmap line's; the write about to be made is a **ledger** line, whose limit is
    `[limits.changelog]` and whose structure carries no deps and no pointer."""
    # A line whose own remainder bites: the deps group and the pointer are what the ledger's
    # line does not carry, so the same field has more room there — and where the roadmap line is
    # short enough for `why_max` to be the binding number, the two agree and nothing is printed.
    long = (
        "- 📋 **RK7** (deps: RK1, RK2, RK4) **A symptom long enough that the line's own "
        "remainder is what binds the why rather than its declared maximum** — Because. → §RK7\n"
    )
    project(tmp_path, roadmap=ROADMAP + long)
    assert main(["-C", str(tmp_path), "brief", "RK7"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "budget   why" in printed
    assert "shipping why" in printed and "which is the limit that refuses it" in printed

    assert main(["-C", str(tmp_path), "brief", "RK7", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    line = next(s for s in payload["budget"]["fields"] if s["field"] == "why")
    ship = next(s for s in payload["shipping"]["fields"] if s["field"] == "why")
    # The ledger's line is shorter by what a dep group and a pointer cost, so the same field has
    # more room there — which is the whole finding: two numbers, and only one was ever shown.
    assert ship["allowed"] > line["allowed"]


def test_the_second_line_is_silent_where_the_two_agree(tmp_path, capsys):
    """A line repeating the number above it teaches nobody anything, so it prints only where the
    difference is the thing worth seeing — while the payload publishes both either way, a key
    costing a client nothing to skip."""
    # A project with no changelog has no ledger line to compose for at all.
    project(tmp_path)
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nimprovements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    assert main(["-C", str(tmp_path), "brief", "RK4"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "budget   why" in printed and "shipping why" not in printed

    assert main(["-C", str(tmp_path), "brief", "RK4", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["shipping"] is None


# -- and the ten that figure did not have (RK1199) -----------------------------


def test_the_figure_is_the_line_the_ship_actually_writes(tmp_path, capsys):
    """The defect, held as the only thing that can hold it: the prediction and the refusal,
    asked of one line with nothing between them changing it.

    `brief` priced the roadmap's task under the ledger's schema, and `Schema.render` appends
    `→ §<anchor>` whenever the task carries one — the pointer being split off before the
    grammar's slot loop runs, so no `drop` reaches it. Ten characters of structure the ledger
    line does not have, in the direction that never refuses a legal sentence and is wrong
    anyway: the figure exists to be composed against, so ten it cannot spend is a clause cut
    for nothing.
    """
    from roadkeep.verbs.refusing import EXIT_USAGE

    # Under the block, because this one ships: a line appended after `## Non-goals` is filed
    # under nothing and refused for that instead of for the length being measured.
    long = (
        "- 📋 **RK7** (deps: RK1, RK2, RK4) **A symptom long enough that the line's own "
        "remainder is what binds the why rather than its declared maximum** — Because. → §RK7\n"
    )
    config = project(
        tmp_path, roadmap=ROADMAP.replace("\n## Non-goals", f"{long}\n## Non-goals")
    )
    root = str(tmp_path)

    assert main(["-C", root, "brief", "RK7", "--json"]) == EXIT_OK
    allowed = next(
        s for s in json.loads(capsys.readouterr().out)["shipping"]["fields"]
        if s["field"] == "why"
    )["allowed"]

    # One character past what the brief promised, and the refusal names the same number.
    assert main(["-C", root, "ship", "RK7", "--why", "x" * (allowed + 1) + "."]) == EXIT_USAGE
    assert f"limit is {allowed}" in capsys.readouterr().err
    # And exactly what it promised lands, which is the half an under-report hides.
    assert main(["-C", root, "ship", "RK7", "--why", "x" * (allowed - 1) + "."]) == EXIT_OK
    capsys.readouterr()
    assert "RK7" in config.path("changelog").read_text(encoding="utf-8")


def test_the_qualifier_a_brief_cannot_know_about_is_named_and_not_folded_in(tmp_path, capsys):
    """A `--part` is structure the caller opts into after this read, and it is not free — 18
    characters on the measured pair. Predicting it would be a guess and staying silent is how
    RK1199 happened, so the row says which line it priced."""
    long = (
        "- 📋 **RK7** (deps: RK1, RK2, RK4) **A symptom long enough that the line's own "
        "remainder is what binds the why rather than its declared maximum** — Because. → §RK7\n"
    )
    project(tmp_path, roadmap=ROADMAP + long)
    assert main(["-C", str(tmp_path), "brief", "RK7"]) == EXIT_OK
    assert "--part" in capsys.readouterr().out


# -- the half a partial already landed (RK1226) --------------------------------


def parted(tmp_path: Path, *parts: str) -> Config:
    """A task shipped in halves, which is the shape `ship --part` leaves behind."""
    config = project(tmp_path)
    for part in parts:
        assert main([
            "-C", str(tmp_path), "ship", "RK1", "--part", part,
            "--why", f"{part} works now.",
        ]) == EXIT_OK
    return Config.discover(tmp_path)


def test_the_brief_names_what_already_landed(tmp_path, capsys):
    """`ship --part` records the half that landed and leaves the line open, which is right.
    What nothing held was the **other** half: reading the ⏳ line said the problem was not
    solved and reading the ledger said what was done, so the remainder was reconstructed by
    subtracting one from the other — across two files, from prose written for different
    purposes, by whoever picked the line up.

    That reconstruction happened here several sessions after the partial and needed the whole
    design read to recover a remainder the person shipping had known precisely.
    """
    config = parted(tmp_path, "the parser half")
    capsys.readouterr()
    assert brief(config, "RK1").landed == ("the parser half",)

    assert main(["-C", str(tmp_path), "brief", "RK1"]) == EXIT_OK
    assert "landed   the parser half" in capsys.readouterr().out


def test_the_door_records_one_half_and_an_adopted_ledger_may_hold_more(tmp_path):
    """Two facts that decide the reader, and the first is the opposite of what it looks like:
    `SecondPartial` **refuses** a second `ship --part` on one id, so this tool writes at most
    one qualifier per task.

    An adopted ledger is the other half. Turing's holds 755 entries written before the tool
    existed, and a history that spelled two deliveries of one id is exactly what `adopt` takes
    in — so reading `by_id`, which answers the first entry per id by design, would name one and
    hide the other. Every entry, in file order.
    """
    config = parted(tmp_path, "the parser half")
    # The door: one id carries one partial and then the completion, so a second is refused.
    assert main([
        "-C", str(tmp_path), "ship", "RK1", "--part", "the writer half",
        "--why", "the writer half works now.",
    ]) == EXIT_USAGE

    # And a ledger that already spells two, which no door of this tool wrote.
    ledger = config.path("changelog")
    ledger.write_text(
        ledger.read_text(encoding="utf-8")
        + f"- {SHIPPED} **RK1 (the writer half)** **A first symptom** — it writes now.\n",
        encoding="utf-8",
    )
    assert brief(Config.discover(tmp_path), "RK1").landed == (
        "the parser half",
        "the writer half",
    )


def test_a_line_that_shipped_nothing_says_nothing(tmp_path, capsys):
    """Silence on the ordinary line: a row saying *nothing has shipped* on every brief is a nag
    this tool has no standing to make."""
    config = project(tmp_path)
    assert brief(config, "RK1").landed == ()
    assert main(["-C", str(tmp_path), "brief", "RK1"]) == EXIT_OK
    assert "landed" not in capsys.readouterr().out


def test_the_payload_carries_it_for_a_caller_that_is_not_a_terminal(tmp_path, capsys):
    config = parted(tmp_path, "the parser half")
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "brief", "RK1", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["landed"] == ["the parser half"]
