"""The editor host, declared in JSON and JavaScript and reasoned about here (RK1011).

`editor/package.json` is the sixth surface that runs this tool somewhere other than a
developer's shell, and like the plugin manifest it cannot explain itself: JSON has no
comments. So the decisions it encodes live here, beside the assertions that hold them.

* **It activates on a governed workspace.** `workspaceContains:roadkeep.toml`, never `*` and
  never a language: a surface that costs something on every session touching none of these
  files is paying for the sessions it does nothing in, which is RK23's argument for a
  trigger-loaded skill applied to the one place it is even easier to get wrong.
* **It carries no rule.** No limit, no marker set, no id shape, no parser — every fact it
  shows was read from a payload some verb printed. Held below by the same scan RK1000 runs
  over the package, because a rule compiled into a *reader* is L6 broken from the outside.
* **No dependencies and no build step.** Plain CommonJS against the editor's own API, which
  is the argument the package makes about `argparse` over `click` (zero runtime deps),
  applied to a tree where five surfaces already ship with no toolchain. A `dependencies`
  table here is a toolchain in every adopting CI, which is RK1010's line and not this one's.
* **It reads only what RK1005 promised.** The keys this host walks are the keys that test
  holds, so a rename goes red in Python before it reaches a reader in another language.
* **The version is the module's**, for `plugin.json`'s reason: two numbers that can disagree
  is the state a reader cannot diagnose, and the pre-commit hook writes both.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import roadkeep
from roadkeep.cli import build_parser
from roadkeep.schema import DEFERRED, DESIGNED, IDEA, IN_PROGRESS, PARTIAL, RETIRED, SHIPPED

HERE = Path(__file__).resolve().parents[1]
EDITOR = HERE / "editor"
MANIFEST = EDITOR / "package.json"
EXTENSION = EDITOR / "extension.js"


def _code() -> str:
    """The file with its comments taken out, which is RK1000's own distinction one language
    over: a header citing `RK1011` is a reference to this project's history, and a literal
    that *is* an id is a value. There is no AST here, so the line comment is the seam."""
    return "\n".join(
        line
        for line in EXTENSION.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith(("//", "*", "/*"))
    )


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_the_host_activates_on_a_governed_workspace_and_nothing_else(manifest):
    """The one property that decides what it costs a session it does nothing in."""
    assert manifest["activationEvents"] == ["workspaceContains:roadkeep.toml"]
    assert "*" not in manifest["activationEvents"]
    assert "onLanguage:markdown" not in manifest["activationEvents"]


def test_the_host_takes_no_dependencies_and_needs_no_build(manifest):
    # `main` names a file that is in the tree, not one a build would produce.
    assert manifest["main"] == "./extension.js"
    assert (EDITOR / manifest["main"]).is_file()
    assert "dependencies" not in manifest and "devDependencies" not in manifest
    assert "scripts" not in manifest, "a build step here is a toolchain in every adopting CI"


def test_the_version_is_the_module_s(manifest):
    """`plugin.json`'s rule, for `plugin.json`'s reason: a reader that reports a version this
    package never released is a reader nobody can diagnose."""
    assert manifest["version"] == roadkeep.__version__


def test_every_view_it_contributes_is_in_the_container_it_declares(manifest):
    containers = {one["id"] for one in manifest["contributes"]["viewsContainers"]["activitybar"]}
    assert set(manifest["contributes"]["views"]) <= containers
    icons = {one["icon"] for one in manifest["contributes"]["viewsContainers"]["activitybar"]}
    for icon in icons:
        assert (EDITOR / icon).is_file(), icon


def test_every_command_it_contributes_is_one_it_registers(manifest):
    """The `plugin.json` rule about two lists that can disagree, one surface over: a menu
    entry for a command nothing registers is a button that does nothing when pressed."""
    declared = {one["command"] for one in manifest["contributes"]["commands"]}
    registered = set(re.findall(r'registerCommand\(\s*"([^"]+)"', EXTENSION.read_text(encoding="utf-8")))
    assert declared == registered
    for entry in manifest["contributes"]["menus"]["view/title"]:
        assert entry["command"] in declared


def test_the_host_carries_no_rule_this_project_configures():
    """RK1000's scan, pointed at the reader. A limit, a marker or an id spelled here is a fact
    about somebody's project compiled into a client that ships on its own clock — the one
    place L6 can break where no Python test would ever see it."""
    source = _code()
    markers = (DESIGNED, IDEA, PARTIAL, IN_PROGRESS, SHIPPED, RETIRED, DEFERRED)
    assert not [one for one in markers if one in source], "a marker set is `[markers]`'"
    assert not re.search(r"\b[A-Z]{1,4}\d+\b", source), "an id is `[ids]`'"
    assert not re.search(r"\b(ROADMAP|CHANGELOG|IMPROVEMENTS|STRATEGY)\.md\b", source), (
        "where a backlog lives is `[files]`'"
    )


def test_every_verb_the_host_runs_is_one_this_cli_parses():
    """RK167's rule for the fourth surface: a reader that spells a command this tool does not
    have answers `unrecognized arguments` where a user expects a panel."""
    parsed = next(
        set(action.choices)
        for action in build_parser()._actions
        if getattr(action, "choices", None) and action.dest == "command"
    )
    read = re.findall(r'payload\([^,]+,\s*\["([a-z-]+)"', _code())
    assert read, "the host stopped running a command at all"
    for call in read:
        assert call in parsed, f"the host runs `{call}`, which this CLI does not parse"


def test_the_host_reads_only_keys_a_payload_promises():
    """The join RK1005 exists for. Every key this reader walks is one that test holds, so a
    rename is red in Python before it is a broken view in another language."""
    from test_payloads import INSIDE, PROMISED

    source = _code()
    # The host's **own** two rows, which no payload ever carried: `notice` is the message it
    # shows instead of an empty tree when the read failed, and `group` is a block heading it
    # made by grouping what `list` returned. Named here so the set below is payload keys.
    promised = (
        set(PROMISED["list"])
        | set(INSIDE["list"][1])
        | set(PROMISED["deps"])
        | {"notice", "group"}
    )
    read = set(re.findall(r"\.value\.(\w+)|\brow\.(\w+)", source))
    walked = {name for pair in read for name in pair if name}
    assert walked, "the host stopped reading a payload at all"
    assert walked <= promised, f"reads {sorted(walked - promised)}, which nothing promises"


def test_the_extension_exports_the_two_hooks_and_names_what_else_it_exports():
    """The two an editor loads, and the one it does not: `Backlog` is exported for the
    harness, because the properties worth proving about this surface are not renderable and
    a tree that groups wrong still draws. Anything a fourth name appears for is a decision."""
    source = EXTENSION.read_text(encoding="utf-8")
    exported = re.search(r"module\.exports\s*=\s*\{([^}]*)\}", source)
    assert exported, "the file stopped exporting anything an editor could load"
    assert [one.strip() for one in exported.group(1).split(",") if one.strip()] == [
        "activate",
        "deactivate",
        "Backlog",
    ]
    assert "function activate(" in source and "function deactivate(" in source


NODE = shutil.which("node")


@pytest.mark.skipif(not NODE, reason="node is not on PATH")
def test_the_tree_groups_by_block_and_separates_what_is_blocked():
    """The two properties RK1006 is about, neither of which a source read can see: rows are
    grouped by the block **the payload gave**, and a line that cannot be started is last and
    carries its blocker. Run against this repository's own `docs/` and the real verbs — the
    editor is stubbed and the tool is not, because what is under test is the client's reading
    of two payloads and nothing else.

    Skipped rather than required: node is a reader's toolchain and not this tree's, which is
    the whole of RK1010's open question — so this is the corpora rule (RK105) applied to a
    language, testing what is here and staying quiet where it is not.
    """
    said = subprocess.run(
        [NODE, str(EDITOR / "harness.js"), str(HERE)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "ROADKEEP_COMMAND": "python -m roadkeep.cli", "PYTHONPATH": "src"},
        cwd=str(HERE),
    )
    tree = json.loads(said.stdout)
    assert "notice" not in tree, tree.get("notice")
    assert tree["blocks"], "the harness read no block at all"
    for block in tree["blocks"]:
        assert block["label"] == block["group"]
        ids = [row["id"] for row in block["rows"]]
        assert len(set(ids)) == len(ids), f"block {block['group']} repeats a line"
        blocked = [index for index, row in enumerate(block["rows"]) if row["blockers"]]
        ready = [index for index, row in enumerate(block["rows"]) if not row["blockers"]]
        assert not (blocked and ready) or min(blocked) > max(ready), block["group"]
    # And the separation is not vacuous: some line in this backlog is blocked, and it names
    # what it waits on rather than saying only that it cannot start.
    waiting = [row for block in tree["blocks"] for row in block["rows"] if row["blockers"]]
    if waiting:
        assert all(row["blockers"] for row in waiting)


def test_the_manifest_is_the_only_json_in_this_surface():
    """A second manifest is a second declaration of the same thing, which is the state
    `hooks.json` taught this project to check rather than to remember."""
    assert sorted(one.name for one in EDITOR.glob("*.json")) == ["package.json"]
