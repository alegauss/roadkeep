"""The skill the plugin ships, and why the rules live there and nowhere else (RK23).

`agents.md` held the write path — which command to call, what it derives, how work is picked —
and an instruction file is loaded on **every** turn, including every turn that touches no
governed file. That is the failure this project was built from: the `agents.md` measured at
186 KB in `docs/IMPROVEMENTS.md §0.1` grew because resident prose has no natural ceiling.

A skill is the same text with a trigger. `skills/roadkeep/SKILL.md` is read when a roadmap,
changelog or rationale file is in play and costs nothing otherwise, which is L5 applied to the
instructions themselves rather than only to the backlog they describe.

The decisions that arrangement encodes, and the assertions that hold them:

* **One copy, in the plugin.** The skill ships with the plugin, so every adopting project runs
  the same text; `agents.md` points at it and states only what is true of *this* checkout. A
  rule written in two files is a rule two files can disagree about, so a test — not a
  reviewer — checks the write path is gone from the resident file.
* **Auto-discovered, not declared.** `skills/<name>/SKILL.md` beside `hooks/` is where the
  plugin loader looks, so the manifest needs no path for it and cannot state a stale one.
* **No configured value is written in it.** Prefix, paths, markers and limits are per-project
  (L6); a skill that spells `RK` or a word budget is a skill that is wrong in the second
  project it is installed in. It names `roadkeep.toml` instead.
* **Every command it names is one the CLI accepts.** The same argument `tests/test_surfaces.py`
  makes about the Action: instructions that drift from `cli.py` teach a flag that exits 2.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import conftest
from roadkeep.config import Config
from roadkeep.cli import build_parser

HERE = Path(__file__).resolve().parents[1]
SKILL = HERE / "skills" / "roadkeep" / "SKILL.md"
AGENTS = HERE / "agents.md"

#: The write path, as the skill spells it. Each is a command an agent would otherwise guess.
_MUST_NAME = (
    "add",
    "status",
    "ship",
    "retire",
    "record",
    "section",
    "brief",
    "list",
    "show",
    "deps",
    "export",
    "lint",
)


def text() -> str:
    return SKILL.read_text(encoding="utf-8")


def frontmatter() -> dict[str, str]:
    """The two flat keys a skill declares, read the way a loader reads them (RK331)."""
    return conftest.frontmatter(SKILL)


def subcommands() -> set[str]:
    """Every subcommand `cli.py` actually registers, read off the real parser."""
    return {
        name
        for action in build_parser()._actions
        if isinstance(action, argparse._SubParsersAction)
        for name in action.choices
    }


# -- where it lives ----------------------------------------------------------


def test_the_skill_sits_where_the_plugin_loader_looks():
    # Beside hooks/, one directory per skill, the file named SKILL.md: the convention is the
    # declaration, which is why the manifest carries no path that could go stale.
    assert SKILL.is_file()
    assert SKILL.parent.parent == HERE / "skills"
    assert (HERE / "hooks" / "hooks.json").is_file()


def test_the_skill_is_named_for_the_plugin_and_its_own_directory():
    assert frontmatter()["name"] == SKILL.parent.name == "roadkeep"


# -- what triggers it --------------------------------------------------------


def test_the_description_names_the_files_it_governs():
    """The description *is* the trigger: a governed file named in a prompt has to reach it."""
    description = frontmatter()["description"]
    for role, path in Config.discover(HERE).paths.items():
        assert path.name in description, role


def test_the_description_names_the_acts_that_should_load_it():
    description = frontmatter()["description"].lower()
    for act in ("adding", "shipping", "retiring", "roadmap", "changelog", "next task"):
        assert act in description, act


# -- one copy, and it is this one --------------------------------------------


def test_the_resident_file_points_at_the_skill_instead_of_repeating_it():
    resident = AGENTS.read_text(encoding="utf-8")
    assert "skills/roadkeep/SKILL.md" in resident
    # The two headings whose content moved. Their prose in `agents.md` would be a second
    # authority, and the one that is not trigger-loaded.
    assert "## Writing and shipping" not in resident
    assert "## Picking work" not in resident
    for flag in ("--symptom", "--superseded-by", "--block <x>"):
        assert flag not in resident, flag
        assert flag in text(), flag


def test_the_skill_states_no_value_this_project_configures():
    """Installed everywhere, so a number or a prefix written here is wrong somewhere (L6)."""
    schema = Config.discover(HERE).schema
    body = text()
    assert schema.prefix not in body
    for name in ("symptom_max", "why_max", "line_max", "section_max", "prose_width"):
        assert str(getattr(schema, name)) not in body, name
    assert "roadkeep.toml" in body


# -- what it teaches ---------------------------------------------------------


def test_every_command_the_skill_names_is_one_the_cli_accepts():
    named = {word for span in re.findall(r"`([^`]+)`", text()) for word in re.findall(r"[a-z-]+", span)}
    assert set(_MUST_NAME) <= named, sorted(set(_MUST_NAME) - named)
    assert set(_MUST_NAME) <= subcommands(), sorted(set(_MUST_NAME) - subcommands())


def test_the_skill_keeps_the_two_rules_a_schema_cannot_check():
    # They are the reason the skill is prose at all: a `maxLength` cannot see that a symptom
    # was named after its fix, so this is the only place either rule can be stated.
    body = text()
    assert "states what does not work" in body
    assert "one sentence" in body
