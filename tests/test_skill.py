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
import contextlib
import re
from pathlib import Path

import conftest
from roadkeep.config import Config
from roadkeep.cli import build_parser, main

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


def flowed() -> str:
    """The same text with every wrap taken out (RK366).

    Every assertion here about *what the skill says* reads this instead of the raw file:
    where a paragraph's line breaks fall is not a fact about its content, and a phrase that
    straddles two lines turned a content assertion into a failure about formatting. The
    assertions about **shape** — the frontmatter, the width — still read the file.
    """
    return " ".join(text().split())


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
    body = flowed()
    assert "states what does not work" in body
    assert "one sentence" in body


def test_the_free_address_is_taught_as_the_command_computes_it(capsys):
    """Both accounts of `anchors`, held against the one thing the command answers (RK383).

    The failure this pins is help that *was* accurate: RK340 made the free top-level a
    per-namespace number and RK346 made `--json` answer one row each, and the two sentences a
    caller reads first went on promising one address for the project. Nothing prompts a
    re-read of prose that reads correct, so the caller picks a top-level out of the sibling's
    namespace — the collision `[refs]` exists to end.
    """
    with contextlib.suppress(SystemExit):
        main(["anchors", "--help"])
    surfaces = {"the skill": text(), "anchors --help": capsys.readouterr().out}
    for where, body in surfaces.items():
        assert "namespace" in body, where
        # The claim itself, not a paraphrase: it is true of a project declaring no `[refs]`
        # and false of one that does, so it may not be stated unconditionally.
        assert "one outline spans both" not in body, where


def test_the_body_is_wrapped_and_nothing_but_a_re_wrap_holds_it(): 
    """RK366, and the third of the three answers its own section lists.

    Measured as it shipped: 299 body lines, 24 past 110 characters, the widest 283, and six
    orphans under 30 mid-paragraph — all from one pattern, text appended to a line instead of
    the paragraph re-wrapped. Nothing renders differently and nothing costs more tokens, so
    the cost is **review**: a diff of a 283-character line is a whole-paragraph diff, in the
    file every adopting project loads.

    The other two answers were argued against in the section itself. A width in
    `roadkeep.toml` with a `lint` finding puts this tool a step from a Markdown formatter it
    has no reason to be; a `--fix` repair rewrites somebody's line, which is exactly what RK16
    confines to the derived. So nothing is held *there* — it is held here, where a test about
    this file already belongs, and where it costs no adopting project anything.

    The frontmatter is exempt and has to be: `description` is one YAML scalar a loader reads,
    and wrapping it changes what the harness matches on.
    """
    lines = text().split("\n")
    body, fence = [], False
    for at, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```"):
            fence = not fence
        elif not fence and at > _frontmatter_ends(lines) and line.strip():
            body.append((at, line))
    over = [(at, len(line)) for at, line in body if len(line) > 110]
    assert not over, f"{len(over)} body line(s) past 110 characters: {over}"


def test_no_copy_of_the_duplicate_claim_prices_it_at_a_rank_nobody_can_reproduce():
    """RK441. Three copies argue the same right decision — a duplicate cannot be refused —
    and all three argued it from a rank of 33rd that re-measuring this ledger does not
    produce: BM25 over the 426 shipped symptoms ranks the true partner of all four
    `superseded by` pairs at #1 to #3.

    What actually fails is the **score**. Two of those four sit below the 13th percentile of
    the top-1 score a proposal with no duplicate produces, so a threshold catching all four
    flags 419 of the 426 — relative order inside one query carries signal and the absolute
    score carries none, which makes a gate impossible rather than merely unreliable. That
    fact holds however good the ranking gets, which is why it is the one to publish.

    Held here because a number nobody can reproduce is worse than no number *where three
    copies publish it*, and one of them ships to every adopting project. The assertion is
    the rank's absence and not the new sentence's wording: what must not come back is a
    figure the ledger contradicts.
    """
    copies = {
        "skill": flowed(),
        "guard": (HERE / "src" / "roadkeep" / "guarding.py").read_text(encoding="utf-8"),
        "delivered": _subparser("delivered").description or "",
    }
    for name, body in copies.items():
        assert "delivered" in body or name == "guard", name
        assert "33rd" not in body, name
    # And the one that is not a rank at all is the one every copy may keep: the ranking is
    # fine, and the sentence has to say so or the reader repairs the wrong half.
    assert "top three" in copies["skill"] and "top three" in copies["delivered"]
    assert "419 of the 426" in copies["guard"]


def _subparser(command: str):
    """The parser for one subcommand, for the description the CLI publishes as its own."""
    actions = [
        action
        for action in build_parser()._actions  # noqa: SLF001
        if isinstance(action, argparse._SubParsersAction)  # noqa: SLF001
    ]
    return actions[0].choices[command]


def _frontmatter_ends(lines: list[str]) -> int:
    if not lines or lines[0] != "---":
        return 0
    return next(at for at, line in enumerate(lines[1:], start=2) if line == "---")
