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
from roadkeep.cli import EXIT_OK, build_parser, main
from roadkeep.kernel.schema import DEFERRED, DESIGNED, IDEA, IN_PROGRESS, PARTIAL, RETIRED, SHIPPED

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


def _builder(*names: str) -> tuple:
    """`scripts/` is not a package and never has been — it holds the two entry points a
    developer runs, not modules anything imports (RK18). Loaded by path here for that reason,
    which is also how `conftest` reaches nothing else: there is nothing else to reach."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("build_vsix", HERE / "scripts" / "build_vsix.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return tuple(getattr(module, name) for name in names)


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
        | set(PROMISED["lint"])
        | set(INSIDE["lint"][1])
        | set(PROMISED["budget"])
        | set(PROMISED["stats"])
        | set(INSIDE["budget"][1])
        | set(INSIDE["stats"][1])
        | set(PROMISED["engines"])
        | {"notice", "group", "engine", "detail", "count"}
    )
    # The receivers a payload is bound to, named rather than matched by `.value.` alone: an
    # input box also has a `value`, and `box.value.length` is a string's length, not a key.
    holders = ("answer", "budget", "blocks", "engines", "counted")
    for holder in holders:
        assert f"{holder}.value" in source, f"{holder} stopped holding a payload"
    read = set(re.findall(rf"(?:{'|'.join(holders)})\.value\.(\w+)|\brow\.(\w+)", source))
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
        "Gate",
        "compose",
    ]
    assert "function activate(" in source and "function deactivate(" in source


NODE = shutil.which("node")


def _harness(
    root, typed: list[str] | None = None, declared: str | None = None, cycles: bool = False
) -> dict:
    """Run the stubbed host against **this checkout's** roadkeep and read its report back.

    ``typed`` is what somebody writes into the two prompts, in order — passed as JSON because
    an environment variable is a string and a separator inside prose is a bug waiting.

    **Which copy answered is asserted here and not left to the machine** (RK1019). RK1009 made
    the view refuse to guess that, because a panel answering from a copy the commits do not
    use fails quietly; the suite proving the view had the same shape and none of the care. The
    child resolves `python -m roadkeep.cli`, and this package imports from anywhere on a
    machine that installed it — so on a machine that installed a *different* one, every
    assertion below would have been about a package this tree does not contain, and passed.

    So the engine row is read back and compared to this directory, exactly. `engines` derives
    that home from the module the child actually imported, which makes it the one fact in the
    report that is about the process rather than about the files it read.

    Held on every call that produces an engine row, including the ones that declare a command
    of their own: a wrapper that delegates to this tree still answers from it, and one that
    did not is exactly what this is for. The undeclared case names no engine at all, which is
    the point of that case.
    """
    env = {
        **os.environ,
        "ROADKEEP_COMMAND": "python -m roadkeep.cli" if declared is None else declared,
        # Absolute: the child runs with the *workspace* as its cwd, so a relative entry here
        # would resolve against a directory that has no package in it.
        "PYTHONPATH": str(HERE / "src"),
    }
    if typed is not None:
        env["ROADKEEP_TYPED"] = json.dumps(typed)
    if cycles:
        env["ROADKEEP_CYCLES"] = "1"
    said = subprocess.run(
        [NODE, str(EDITOR / "harness.js"), str(root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        cwd=str(HERE),
    )
    assert said.stdout, said.stderr
    report = json.loads(said.stdout)
    if "engine" in report:
        # The home `engines` derived, against this checkout — as a path and not a suffix: two
        # trees ending in the same two segments is exactly the state RK79 exists to separate.
        assert report["engine"]["detail"] == (HERE / "src" / "roadkeep").as_posix(), (
            f"the harness answered from {report['engine']['detail']}, which is not this tree"
        )
    return report


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
    tree = _harness(HERE)
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


# -- the archive an editor installs (RK1013) ----------------------------------


def test_the_archive_carries_the_files_this_tree_holds_and_nothing_generated(tmp_path):
    """A `.vsix` is an OPC package, and `zipfile` is the standard library — so the format is
    this repository's to own, for the reason it owns `argparse` over `click`: the alternative
    is node, a lockfile and a step in every adopting CI."""
    import zipfile

    SHIPPED, build = _builder("SHIPPED", "build")

    archive = build(tmp_path)
    assert archive.parent == tmp_path and archive.suffix == ".vsix"
    with zipfile.ZipFile(archive) as opened:
        held = set(opened.namelist())
    assert {"[Content_Types].xml", "extension.vsixmanifest"} <= held
    assert {f"extension/{name}" for name in SHIPPED} <= held
    # `harness.js` is a test's fixture, so it belongs in the repository and not in what
    # somebody installs — which is why the list is a list and never a glob.
    assert "extension/harness.js" not in held


def test_the_archive_is_named_and_stamped_by_the_manifest_it_carries(manifest, tmp_path):
    """One source for the version, which the pre-commit hook already writes: an archive whose
    filename, whose manifest and whose module disagree is one nobody can diagnose."""
    import zipfile

    (build,) = _builder("build")

    archive = build(tmp_path)
    assert archive.name == f"{manifest['publisher']}.{manifest['name']}-{manifest['version']}.vsix"
    with zipfile.ZipFile(archive) as opened:
        declared = opened.read("extension.vsixmanifest").decode("utf-8")
        carried = json.loads(opened.read("extension/package.json"))
    assert f'Version="{manifest["version"]}"' in declared
    assert f'Id="{manifest["name"]}"' in declared and f'Publisher="{manifest["publisher"]}"' in declared
    assert carried == manifest, "the archive carries a manifest other than this tree's"


def test_every_part_the_archive_carries_has_a_declared_content_type(tmp_path):
    """The half an installer reads before anything else: a part whose extension the types
    document omits is a part it skips, which is an extension that installs and does nothing."""
    import zipfile

    CONTENT_TYPES, build = _builder("CONTENT_TYPES", "build")

    with zipfile.ZipFile(build(tmp_path)) as opened:
        parts = [name for name in opened.namelist() if "." in name.rsplit("/", 1)[-1]]
    declared = set(re.findall(r'Extension="([^"]+)"', CONTENT_TYPES))
    for part in parts:
        suffix = part.rsplit(".", 1)[-1]
        if part == "[Content_Types].xml":
            continue
        assert suffix in declared, f"{part} has no content type"


@pytest.mark.skipif(not NODE, reason="node is not on PATH")
def test_a_finding_becomes_a_diagnostic_where_the_report_already_points(tmp_path):
    """RK1007's whole claim: the mapping is a translation and not a feature. A finding
    carries `file:line:column` and a code, and what the panel shows is those — anchored at
    the column where there is one, and at the line where there is not."""
    root = tmp_path / "project"
    root.mkdir()
    (root / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nimprovements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    (root / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Block A — The model\n\n"
        "- 📋 **RK1** (deps: RK9) **A symptom** — Because of a reason. → §RK1\n"
        "- 📋 **RK2** (deps: —) **A symptom\twith a tab** — Because of it. → §RK2\n",
        encoding="utf-8",
        newline="",
    )
    (root / "IMPROVEMENTS.md").write_text(
        "# Improvements\n\n## Block A — The model\n", encoding="utf-8", newline=""
    )
    tree = _harness(root)
    gate = tree["gate"]
    assert not gate["notice"], gate["notice"]
    (file,) = gate["files"]
    assert file["file"] == "ROADMAP.md"
    found = {one["code"]: one for one in file["found"]}
    assert "char.tab" in found and "deps.unknown" in found
    # Zero-based, because that is what an editor counts in — and the column is the finding's
    # where it has one, never a guess where it does not.
    assert found["char.tab"]["column"] == 33 and found["char.tab"]["line"] == 5
    assert found["deps.unknown"]["column"] == 0
    assert all(one["source"] == "roadkeep" for one in file["found"])


@pytest.mark.skipif(not NODE, reason="node is not on PATH")
def test_only_a_door_the_tool_called_complete_becomes_an_action(tmp_path):
    """The half that is a refusal rather than a feature. `char.tab` closes with `lint --fix`
    and is offered; `deps.unknown`'s doors carry a marked blank, which is prose the tool does
    not compose (L4) — so the panel offers the explanation and nothing that would write it."""
    root = tmp_path / "project"
    root.mkdir()
    (root / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nimprovements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    (root / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Block A — The model\n\n"
        "- 📋 **RK1** (deps: RK9) **A symptom** — Because of a reason. → §RK1\n"
        "- 📋 **RK2** (deps: —) **A symptom\twith a tab** — Because of it. → §RK2\n",
        encoding="utf-8",
        newline="",
    )
    (root / "IMPROVEMENTS.md").write_text(
        "# Improvements\n\n## Block A — The model\n", encoding="utf-8", newline=""
    )
    actions = _harness(root)["gate"]["actions"]
    assert actions and all(one["argv"] for one in actions)
    titles = {code: [one["title"] for one in actions if one["code"] == code] for code in
              {one["code"] for one in actions}}
    # `char.tab` closes with a complete command, so it is offered.
    assert any("lint --fix" in title for title in titles["char.tab"])
    # `deps.unknown` has two doors: `amend {id} --dep …` carries a marked blank and is offered
    # to nobody, and `gaps` is a **read**, which the kind says to show rather than to apply.
    assert titles["deps.unknown"] == [
        "roadkeep gaps — read where the id went before deciding it is gone",
        "roadkeep explain deps.unknown",
    ]
    # And every code gets the explanation, which is the door for a code nobody has met.
    for code, found in titles.items():
        assert f"roadkeep explain {code}" in found


def test_nothing_in_the_host_writes_a_file():
    """The property the round-trip law rests on (L3): one writer. The extension composes an
    argv and the command writes — a `fs.write` here would be a second writer of a governed
    file, which is the state every refusal in this project exists to prevent."""
    source = _code()
    assert "writeFile" not in source and "writeFileSync" not in source
    assert "require(\"fs\")" not in source and "require('fs')" not in source


@pytest.mark.skipif(not NODE, reason="node is not on PATH")
def test_the_prompt_carries_the_budget_and_the_command_is_what_writes(tmp_path):
    """RK1008. `budget` answers, before the first word, what each field has left on the line
    `add` is about to derive — so the number is on screen instead of being discovered by a
    refusal. Every figure in the prompt came from that payload, and the line that lands is
    written by `add` and read back off the file."""
    root = tmp_path / "project"
    root.mkdir()
    assert main(["-C", str(root), "init"]) == EXIT_OK
    typed = ["A thing does not work at all here", "Because nothing holds it."]
    said = _harness(root, typed=typed)
    assert said["wrote"] is True, said.get("said")
    # 120 is `[limits] symptom` and 33 is what was typed: the countdown is the payload's
    # number minus the words on screen, and neither figure is written into the client.
    assert "87 of 120 left" in said["prompts"][0] and "aim 18 words" in said["prompts"][0]
    assert "175 of 200 left" in said["prompts"][1]
    written = (root / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
    assert typed[0] in written and typed[1] in written


@pytest.mark.skipif(not NODE, reason="node is not on PATH")
def test_a_refusal_reaches_the_editor_in_the_tool_s_own_words(tmp_path):
    """The half that makes it a door and not a validator: the prompt shows the budget and
    `add` decides, so what the editor reports is the refusal verbatim — which already names
    every field it looked at, in one message (RK426)."""
    root = tmp_path / "project"
    root.mkdir()
    assert main(["-C", str(root), "init"]) == EXIT_OK
    said = _harness(root, typed=["A thing does not work at all here", ""])
    assert said["wrote"] is False
    (reported,) = said["said"]
    assert "refused, nothing written" in reported and "why.empty" in reported
    assert not (root / "docs" / "ROADMAP.md").read_text(encoding="utf-8").count("A thing does not")


@pytest.mark.skipif(not NODE, reason="node is not on PATH")
def test_the_view_refuses_to_guess_which_roadkeep_it_calls(tmp_path):
    """RK1009's whole decision. Three copies can already differ and `engines` exists because
    of it; an editor adds a fourth resolved from a PATH, a virtualenv or a `uvx` cache, and
    the failure is quiet — a panel showing findings a commit will not produce is discovered
    when a hook denies a write the panel said was fine. So the setting is required, and what
    a reader gets instead of a guess is the name of the setting."""
    root = tmp_path / "project"
    root.mkdir()
    assert main(["-C", str(root), "init"]) == EXIT_OK
    said = _harness(root, declared="")
    assert "roadkeep.command is not set" in said["notice"]
    assert said["blocks"] == [] and "engine" not in said


@pytest.mark.skipif(not NODE, reason="node is not on PATH")
def test_the_view_says_which_copy_answered_and_what_it_agrees_with():
    """The fourth row, above the rows it produced: whatever the setting resolves is a copy
    with a version and a verdict, and `engines` already answers both — so nothing here judges
    anything, it shows the answer of the process that produced the list underneath."""
    said = _harness(HERE)
    assert said["engine"]["label"].endswith(("agreed", "behind", "unpinnable")), said["engine"]
    assert roadkeep.__version__ in said["engine"]["label"]
    # And the home, because two copies at one version is exactly the state RK79 was about.
    assert said["engine"]["detail"].endswith("src/roadkeep")


@pytest.mark.skipif(not NODE, reason="node is not on PATH")
def test_a_save_re_reads_the_backlog_and_not_the_installation(tmp_path):
    """RK1017. `engines` asks git which commit the package's files are at — a fact about the
    installation, which moves when somebody upgrades and not when a line is edited. The
    package says as much about the same question: it is asked at most once per process and
    never on a path that writes. A CLI invocation *is* a process, so a view that shelled out
    per save asked it per save, on a keystroke nobody thinks about.

    Counted end to end rather than asserted: the declared command is a wrapper that logs its
    own argv, so what this reads is the child processes that actually ran.
    """
    root = tmp_path / "project"
    root.mkdir()
    assert main(["-C", str(root), "init"]) == EXIT_OK
    log = tmp_path / "ran.log"
    spy = tmp_path / "spy.py"
    spy.write_text(
        "\n".join(
            [
                "import pathlib, runpy, sys",
                f"with pathlib.Path({str(log)!r}).open('a', encoding='utf-8') as handle:",
                "    handle.write(' '.join(sys.argv[1:]) + chr(10))",
                "sys.argv[0] = 'roadkeep'",
                "runpy.run_module('roadkeep.cli', run_name='__main__')",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _harness(root, declared=f"python {spy}", cycles=True)
    ran = [line.split()[0] for line in log.read_text(encoding="utf-8").splitlines() if line]
    # Three tree builds: the harness's first, one after a save, one after an explicit
    # refresh. Activation adds a `lint` and no `list` — nothing is subscribed to the tree in
    # a stubbed window, so firing the change event asks nothing — and it is counted at all
    # only because `activate` returns its promise and the harness awaits it. Un-awaited, that
    # `lint` sometimes landed after the log was read, which is what made this count flaky.
    assert ran.count("list") == 3, ran
    assert ran.count("lint") == 2, ran
    # And two `engines` across all four: the window's first answer, and the one the button
    # asked for — which is the whole of RK1017, counted rather than asserted.
    assert ran.count("engines") == 2, ran


@pytest.mark.skipif(not NODE, reason="node is not on PATH")
def test_the_tree_says_how_much_work_there_is_without_computing_it(tmp_path):
    """RK1018. The number is `stats`'s — the total, and each marker in the order the payload
    lists them, which is the order `roadkeep.toml` declares. A project with a marker set of
    its own gets its own numbers and nothing here changes (L6), which is what makes this a
    rendering rather than a count."""
    root = tmp_path / "project"
    root.mkdir()
    assert main(["-C", str(root), "init"]) == EXIT_OK
    for number in range(3):
        assert main([
            "-C", str(root), "add", "--block", "A",
            "--symptom", f"A thing numbered {number} does not work here",
            "--why", "Because nothing holds it.",
        ]) == EXIT_OK
    assert main(["-C", str(root), "status", "RK2", "🛠"]) == EXIT_OK
    said = _harness(root)["count"]
    assert said["label"].startswith("3 open")
    # The markers the file carries, and only those — the numbers came from the payload.
    assert "📋 2" in said["label"] and "🛠 1" in said["label"]
    assert "uncounted" not in said["label"], "a zero is not news"
    assert said["detail"] == "docs/ROADMAP.md"
