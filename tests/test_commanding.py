"""The command surface as data, held against the parser that is it (RK1401).

One property carries this file and it is the one that lasts: the **census is total against
the parser**, so a verb added tomorrow appears here without anybody editing anything, and a
verb that stopped appearing is a red rather than a page that quietly lists one command fewer.
That is `test_describing`'s rule for the other half of the contract, and it is the only thing
that makes a generated reference worth generating.

The second is that nothing is restated. Every sentence this read prints is the `help=` its
author wrote at the `add_argument` call, and a copy in `commanding.py` would be the one that
goes stale — which is the failure the whole task is an instance of, one file out.

The third is the join to the served surface. `writes`, exposure and withholding are read off
the parser and off :data:`~roadkeep.serving.TOOLS`, so a listing that disagreed with what an
agent is actually sent would be a reference describing a tool nobody has.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep import commanding
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.serving import TOOLS, _parsers

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"

BACKLOG = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason.
"""

LEDGER = """# Shipped

## Block A — The model
"""


def project(tmp_path: Path, *, extra: str = "") -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n' + extra,
        encoding="utf-8",
    )
    for name, body in ((ROADMAP, BACKLOG), (CHANGELOG, LEDGER)):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


# -- the census, which is the deliverable -------------------------------------


def test_every_command_the_parser_declares_is_one_this_read_names(tmp_path):
    """The closure, and the reason a generated page can be trusted at all.

    The population is the subparser tree, so a verb added tomorrow is in this answer the day
    it is declared — and a filter that started dropping one would be a reference page silently
    missing a command while still looking total.
    """
    found = commanding.commands(project(tmp_path))
    assert {one.path for one in found.commands} == set(_parsers())


def test_the_population_is_never_empty(tmp_path):
    """The one way a derived census fails silently: a walk that stops finding anything passes
    exactly like one that finds everything."""
    assert commanding.commands(project(tmp_path)).commands


def test_help_is_never_one_of_the_arguments(tmp_path):
    """`--help` is argparse's and not this tool's, so a row for it on each of eighty-eight
    verbs would spend the reference on the fact that this is a command-line program."""
    found = commanding.commands(project(tmp_path))
    assert not [
        one.path
        for one in found.commands
        for argument in one.arguments
        if argument.dest == "help"
    ]


# -- the sentence, harvested and never restated -------------------------------


def test_every_sentence_is_the_one_the_parser_already_carries(tmp_path):
    """Not *a* sentence about the argument — **the** one, off the action itself. A reference
    that paraphrased would be a second declaration, which is the accretion this read exists to
    make unnecessary."""
    parsers = _parsers()
    for one in commanding.commands(project(tmp_path)).commands:
        declared = {
            action.dest: action.help or ""
            for action in parsers[one.path]._actions  # noqa: SLF001
        }
        for argument in one.arguments:
            assert argument.help == declared[argument.dest], (one.path, argument.dest)


def test_a_verbs_own_sentence_comes_off_its_parent(tmp_path):
    """argparse keeps `help=` on the action that created the child, never on the child — so a
    verb asked for its own answers with nothing, and the one place it exists is the parent's
    choices. Held because it is the reading that is easy to get silently empty."""
    found = commanding.commands(project(tmp_path))
    by_path = {one.path: one for one in found.commands}
    assert by_path["lint"].help
    assert by_path["section add"].help
    # And nothing is left blank across the whole surface, which is what makes the listing
    # readable and what a wrong parent lookup would quietly undo.
    assert [one.path for one in found.commands if not one.help] == []


# -- the join to what actually runs, and to what an agent is sent -------------


def test_writing_is_the_parsers_claim_and_never_a_table(tmp_path):
    """`reads_only` is what keeps a command out of the write lock (RK117), so it is the one
    authority on this. `lint` is the case the pair exists for: a read that writes when `--fix`
    is given, which a single boolean gets backwards either way."""
    by_path = {one.path: one for one in commanding.commands(project(tmp_path)).commands}
    assert by_path["lint"].writes is False
    assert by_path["lint"].turns_on == ("fix",)
    assert by_path["add"].writes is True
    # And the whole surface, so a verb declared read-only tomorrow is reported as one without
    # anybody adding a row.
    parsers = _parsers()
    for one in commanding.commands(project(tmp_path)).commands:
        declared = parsers[one.path].get_default("reads_only")
        assert one.writes == (one.runs and not declared), one.path


def test_a_group_reaches_no_handler_and_carries_no_arguments(tmp_path):
    """`section` is a real door — `section --help` lists what is under it — and it runs
    nothing. Published rather than filtered, so the nesting is stated instead of inferred from
    the spaces in its children's paths."""
    by_path = {one.path: one for one in commanding.commands(project(tmp_path)).commands}
    assert by_path["section"].runs is False
    assert by_path["section"].writes is False
    assert by_path["section"].arguments == ()
    assert by_path["section add"].runs is True


def test_exposure_is_read_off_the_served_surface(tmp_path):
    """The tool table is the authority on which arguments an agent may set (RK1360), so this
    is a projection of it and never a second opinion — a listing that disagreed would describe
    a tool nobody has."""
    config = project(tmp_path)
    found = commanding.commands(config)
    by_path = {one.path: one for one in found.commands}
    for tool in TOOLS:
        one = by_path[tool.command]
        assert tool.name in one.tools, tool.command
        exposed = {argument.dest for argument in one.arguments if argument.exposed}
        assert set(tool.exposed(config)) <= exposed, tool.command


def test_a_withheld_tool_names_the_declaration_that_opens_it(tmp_path):
    """A project that never declared `[files] deferred` is not sent `defer` (RK1360), and an
    absence a reader cannot explain is what sends them to the source."""
    config = project(tmp_path)
    by_path = {one.path: one for one in commanding.commands(config).commands}
    assert by_path["defer"].tools == ("defer",)
    assert by_path["defer"].published is False
    assert by_path["defer"].needs == "deferred"
    assert "declare deferred" in commanding.stated(commanding.commands(config))


def test_a_command_the_cli_keeps_to_itself_is_served_as_nothing(tmp_path):
    """`init` and `adopt` run before the project is governed and `mcp` is the harness's own
    entry point, so none of the three is a tool — which the listing says rather than leaving a
    reader to notice the missing line."""
    by_path = {one.path: one for one in commanding.commands(project(tmp_path)).commands}
    for path in ("init", "adopt", "mcp", "guard"):
        assert by_path[path].tools == (), path
        assert by_path[path].published is False, path


# -- the two renderings, and the refusal --------------------------------------


def test_the_listing_answers_on_a_tree_with_no_configuration(tmp_path):
    """The reader deciding whether to adopt has no config, which is exactly why this read must
    not need one — the whole symptom is an answer that requires the adoption it would decide."""
    found = commanding.commands(Config.discover(tmp_path))
    assert found.source is None
    assert found.commands
    assert commanding.stated(found)


def test_the_payload_carries_the_build_that_answered(tmp_path, capsys):
    """What is listed is what *this* copy takes, so a flag a reader's build does not have is an
    upgrade rather than a typo — which they can only conclude if the version is on the answer."""
    from roadkeep import __version__

    assert main(["-C", str(tmp_path), "commands", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["version"] == __version__
    assert payload["commands"]
    one = next(one for one in payload["commands"] if one["command"] == "lint")
    assert one["writes"] is False
    assert one["writes_when"] == ["fix"]


def test_one_verb_narrows_to_one_block(tmp_path, capsys):
    assert main(["-C", str(tmp_path), "commands", "--command", "section add"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "section add" in out
    assert "\nlint " not in out


def test_a_verb_this_build_does_not_have_is_refused_and_not_answered_empty(tmp_path, capsys):
    """An empty answer reads as evidence that the verb was removed, which is the one
    conclusion a reader on an older copy must not draw."""
    assert main(["-C", str(tmp_path), "commands", "--command", "nope"]) == EXIT_USAGE
    error = capsys.readouterr().err
    assert "no command 'nope'" in error
    # And it names what this build does have, so the correction is a read and not a guess.
    assert "'lint'" in error


@pytest.mark.parametrize("path", ["", "section add"])
def test_the_two_renderings_answer_about_the_same_surface(tmp_path, path):
    """A payload and a report that could disagree is two surfaces, which is what one record
    read twice (RK1170) exists to stop."""
    config = project(tmp_path)
    found = commanding.commands(config, path or None)
    assert len(commanding.payload(found)["commands"]) == len(found.commands)
