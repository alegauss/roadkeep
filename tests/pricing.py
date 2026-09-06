"""A state that makes this build say one note, for every note it can say (RK1559).

The population became knowable at RK1521 and the figure beside it covers one of it. `cost
--notes` reads what *this* project's gate emits — `read.priced`, and `engine.disagreement`
composed because no checkout here can produce it — and says how many codes it never meets.
What it could not say is how big those are.

A note is prose the gate prints on every run, and prose accretes: `engine.disagreement` grew a
clause in each of three tasks, each time for a good reason and each time against no number.
RK1491 gave that one a figure. The other sixteen have never been read for length by anything,
which is RK1489's finding one subject over — a reading over part of a population, taken for
the population.

**A fixture per code and never a ceiling per code.** RK1491 declined a ceiling for the whole
cadence, and seventeen numbers with no argument behind them would be seventeen limits that move.
What is held here is that every code has a state that produces it and that the state still
produces it — so the width is a *measurement*, recomputed every run, and a note that doubles
shows up as a number in a diff rather than as nothing at all.

**Composed and never pasted.** Each row builds a project and runs the gate, so what is
measured is the sentence a reader is handed. `budgeting.note_cost` refuses a fixture for this
reason and refuses it still: a project's cost is what its own files trip, and pricing the
tool's test data as if it were somebody's repository is the same mistake in the other
direction. So the reading lives here, beside the states that produce it.

The reading at RK1559: **17 codes, 2741 characters** if one reader met every one of them —
against the 282 this repository's gate emits, which is `read.priced` alone. The widest is
`install.absent` at 281 and the narrowest `block.reopened` at 79, so the spread is three and a
half to one and a single figure over the cadence would have described neither end.

No single project produces them all, which is why there are seventeen states: five need a
commit and a diff against it, two an installed tree, one a plugin registry naming a version
this engine has not reached, and one — `engine.disagreement` — is composed off the function
the gate composes it with, because the engine is the tree it judges and no checkout here can
disagree with itself.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from unittest import mock

from conftest import git, git_commit, git_init

from roadkeep.config import Config
from roadkeep.linting import Note, lint

#: This checkout, which the install rows copy their surfaces out of.
HERE = Path(__file__).resolve().parents[1]


def write(root: Path, name: str, body: str) -> None:
    """One file, with its terminators left exactly as the caller spelled them (RK1132)."""
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(body)


def line(task: str, *, marker: str = "\U0001f4cb", deps: str = "—") -> str:
    return (
        f"- {marker} **{task}** (deps: {deps}) **A symptom for {task} of a kind** "
        f"— Because {task} needs doing. → §{task}"
    )


def roadmap(*blocks: tuple[str, tuple[str, ...]]) -> str:
    out = ["# Roadmap", ""]
    for label, lines in blocks:
        out += [f"## Block {label} — A heading", "", *lines, ""]
    return "\n".join(out)


def prose(*anchors: str) -> str:
    out = ["# Improvements", "", "## Block A — A heading", ""]
    for anchor in anchors:
        out += [
            f"### §{anchor} The design for {anchor}",
            "",
            f"The reasoning {anchor}'s line has no room for, at enough length that a "
            f"deletion here would leave prose behind.",
            "",
        ]
    return "\n".join(out)


def declare(*, top: str = "", **tables: str) -> str:
    """A `roadkeep.toml` with the three roles every row here uses, plus what a row adds.

    ``top`` is for a **top-level** key and the keywords for a table, which is the one
    distinction a caller here can get wrong invisibly: a `priority = [...]` appended after
    `[files]` is read as `files.priority` and refused as an unknown role, which reads as a
    fixture that stopped working rather than as one that was never right.
    """
    return (
        'prefix = "RK"\n'
        + top
        + '[files]\nroadmap = "ROADMAP.md"\n'
        'improvements = "IMPROVEMENTS.md"\nchangelog = "CHANGELOG.md"\n'
        + "".join(tables.values())
    )


LEDGER = "# Shipped\n\n## Block A — A heading\n\n## Block B — A heading\n"


def project(
    root: Path,
    *,
    config: str = "",
    lines: str = "",
    designs: str = "",
    committed: bool = False,
) -> Config:
    """A throwaway project with the three files, optionally under git."""
    if committed:
        git_init(root)
    else:
        root.mkdir(parents=True, exist_ok=True)
    write(root, "roadkeep.toml", config or declare())
    write(root, "ROADMAP.md", lines or roadmap(("A", (line("RK1"),))))
    write(root, "IMPROVEMENTS.md", designs or prose("RK1"))
    write(root, "CHANGELOG.md", LEDGER)
    if committed:
        git_commit(root, "chore: bootstrap")
    return Config.discover(root)


def said(config: Config, *, since: str | None = None) -> tuple[Note, ...]:
    """Every note one run of the gate emits, with the findings asserted away.

    A finding beside a note means the fixture is wrong in some second way, and the width of a
    note measured on a broken project is a width nobody meets — so the assertion is the row's
    own guard rather than a separate test.
    """
    report = lint(config, since=since) if since else lint(config)
    assert not report.findings, [str(one) for one in report.findings]
    return report.notes


# -- one state per code -------------------------------------------------------


def _read_priced(root: Path) -> tuple[Note, ...]:
    """More lines left out of the ranking than priced, which is the note's own threshold."""
    many = tuple(line(f"RK{n}") for n in range(1, 12))
    config = project(
        root,
        config=declare(reads="\n[reads]\nbrief = 4000\n"),
        lines=roadmap(("A", many)),
        designs=prose(*(f"RK{n}" for n in range(1, 12))),
    )
    return said(config)


def _incidental_absent(root: Path) -> tuple[Note, ...]:
    """A `[history] incidental` path this tree does not hold, so the filter filters nothing."""
    config = project(root, config=declare(history='\n[history]\nincidental = ["scripts/gone.py"]\n'))
    return said(config)


def _deps_collective(root: Path) -> tuple[Note, ...]:
    """One `Block A` token naming every open line under that block, waited on by two."""
    config = project(
        root,
        lines=roadmap(
            ("A", (line("RK1"), line("RK2"))),
            ("B", (line("RK3", deps="Block A"), line("RK4", deps="Block A"))),
        ),
        designs=prose("RK1", "RK2", "RK3", "RK4"),
    )
    return said(config)


def _budget_translated(root: Path) -> tuple[Note, ...]:
    """A budget in bytes against a working tree whose lines end CRLF."""
    config = project(root, config=declare(budgets='\n[budgets]\n"agents.md" = { bytes = 4000 }\n'))
    write(root, "agents.md", "# Agents\r\n\r\nTwo lines, and both of them end CRLF.\r\n")
    return said(config)


def _priority_config(root: Path) -> tuple[Note, ...]:
    """A queue in the roadmap and an order in the config: the section wins, silently."""
    config = project(
        root,
        config=declare(top='priority = ["RK1"]\n'),
        lines=roadmap(("A", (line("RK1"), line("RK2")))) + "\n## Priority\n\n- RK2\n",
        designs=prose("RK1", "RK2"),
    )
    return said(config)


def _priority_block_unstarted(root: Path) -> tuple[Note, ...]:
    """A tier queuing a block no line is filed under yet."""
    config = project(
        root,
        lines=roadmap(("A", (line("RK1"),)), ("B", ())) + "\n## Priority\n\n- Block B\n",
    )
    return said(config)


def _non_goal(root: Path, *, answered: bool) -> Config:
    """A line whose symptom shares a rare word with a non-goal's lead."""
    lead = "**No calendar dates** Because a date is a promise the backlog cannot keep.\n"
    task = (
        "- \U0001f4cb **RK1** (deps: —) **The calendar an estimate is written against** "
        "— Because a reader needs one. → §RK1"
    )
    design = (
        "# Improvements\n\n## Block A — A heading\n\n### §RK1 The design for RK1\n\n"
        "The reasoning the line has no room for, at enough length to be a paragraph.\n"
    )
    if answered:
        design += (
            '\nThis is bounded by "No calendar dates" and does not breach it: what is written '
            "here is a column and never a promise.\n"
        )
    return project(
        root,
        # `[non_goals]` opted into, which is what makes the list a governed one: undeclared,
        # the whole reader returns nothing and the row measures a note nobody asked for.
        config=declare(non_goals="\n[non_goals]\n"),
        lines=f"# Roadmap\n\n## Block A — A heading\n\n{task}\n\n## Non-goals\n\n- {lead}",
        designs=design,
    )


def _non_goal_reaches(root: Path) -> tuple[Note, ...]:
    return said(_non_goal(root, answered=False))


def _non_goal_settled(root: Path) -> tuple[Note, ...]:
    return said(_non_goal(root, answered=True))


def _section_unpaired(root: Path) -> tuple[Note, ...]:
    """A design edited since the last commit whose line was not."""
    config = project(root, committed=True)
    write(root, "IMPROVEMENTS.md", prose("RK1").replace("has no room for", "has no room for at all"))
    return said(config, since="HEAD")


def _worked(root: Path, *, block: bool) -> Config:
    """Source a design names, moved since the last commit, with the line still open."""
    lines = (line("RK1"), line("RK2")) if block else (line("RK1"),)
    designs = "# Improvements\n\n## Block A — A heading\n\n" + "".join(
        f"### §{task} The design for {task}\n\nThe reasoning, which lives in "
        f"`src/{task.lower()}.py` and is worth a paragraph.\n\n"
        for task in (one.split("**")[1] for one in lines)
    )
    config = project(root, lines=roadmap(("A", lines)), designs=designs, committed=True)
    for task in ("rk1", "rk2") if block else ("rk1",):
        write(root, f"src/{task}.py", f"# {task}\nvalue = 1\n")
    git(root, "add", "-A")
    return config


def _task_worked(root: Path) -> tuple[Note, ...]:
    return said(_worked(root, block=False), since="HEAD")


def _block_worked(root: Path) -> tuple[Note, ...]:
    return said(_worked(root, block=True), since="HEAD")


def _turned(root: Path, *, emptied: bool) -> Config:
    """A block that held open lines at HEAD and holds none now, or the other way round.

    The design moves with the line: a section left behind by a removed line is
    `section.orphan`, which is a *finding* — so the fixture would be measuring a note beside
    a broken project, and :func:`said` refuses that.
    """
    full = (roadmap(("A", (line("RK1"),)), ("B", (line("RK2"),))), prose("RK1", "RK2"))
    bare = (roadmap(("A", (line("RK1"),)), ("B", ())), prose("RK1"))
    before, after = (full, bare) if emptied else (bare, full)
    config = project(root, lines=before[0], designs=before[1], committed=True)
    write(root, "ROADMAP.md", after[0])
    write(root, "IMPROVEMENTS.md", after[1])
    return config


def _block_emptied(root: Path) -> tuple[Note, ...]:
    return said(_turned(root, emptied=True), since="HEAD")


def _block_reopened(root: Path) -> tuple[Note, ...]:
    return said(_turned(root, emptied=False), since="HEAD")


def _source(root: Path) -> Path:
    """A checkout of this tool beside the project, which is what `install` copies from."""
    from roadkeep.installing import CARRIED

    into = root / "roadkeep"
    for part in CARRIED:
        target = into / part
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HERE / part, target)
    return into


def _install_absent(root: Path) -> tuple[Note, ...]:
    """A project with one surface and not the rest, so the others are pages it has not got."""
    from roadkeep.installing import PROJECT_SKILL, install

    where = root / "adopter"
    (where / ".github" / "workflows").mkdir(parents=True)
    config = project(where, committed=False)
    install(where, source=_source(root))
    for page in (where / PROJECT_SKILL).parent.glob("*.md"):
        if page.name != Path(PROJECT_SKILL).name:
            page.unlink()
    return said(Config.discover(where))


def _install_stale(root: Path) -> tuple[Note, ...]:
    """A surface behind the engine answering here, which is what a rewritten copy is."""
    from roadkeep.installing import PROJECT_SKILL, install

    where = root / "adopter"
    (where / ".github" / "workflows").mkdir(parents=True)
    config = project(where, committed=False)
    install(where, source=_source(root))
    (where / PROJECT_SKILL).write_text("stale\n", encoding="utf-8")
    return said(Config.discover(where))


def _gate_behind(root: Path) -> tuple[Note, ...]:
    """An enforced project whose registered plugin is a version this gate has not reached.

    Through the registry the harness actually writes, and not by standing a fake in front of
    `behind`: what the note is about is two copies at two versions, and a row read for real is
    the only reading that proves this build can still see one. `CLAUDE_CONFIG_DIR` is where
    :func:`~roadkeep.provenance.installed` looks, so the environment is the whole of the
    setup — patched as a context rather than through `monkeypatch`, so a row stays one call.
    """
    from test_provenance import wired

    where = root / "adopter"
    config = project(where, config=declare(install="\n[install]\nenforced = true\n"))
    wired(root / "claude", where, version="99.0.0")
    with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(root / "claude")}):
        return said(config)


def _engine_disagreement(root: Path) -> tuple[Note, ...]:
    """The one code no checkout produces, composed off the function the gate composes it with.

    :func:`~roadkeep.linting.disagreements` is what RK1491 lifted out for exactly this, and
    `budgeting.note_cost` already reads it. Read here too rather than fixtured, so the row is
    the same sentence a reader on a skewed machine meets.
    """
    from roadkeep.linting import disagreements
    from roadkeep.provenance import engine

    running = engine()
    return tuple(
        Note("engine.disagreement", "roadkeep.toml", message)
        for _, message in disagreements(
            running.version,
            running.home.as_posix(),
            running.version,
            running.version,
            running.on_disk,
            working=True,
            skewed=True,
            split=True,
            swapped=True,
        )
    )


@dataclass(frozen=True, slots=True)
class Priced:
    """One note code, and the state that makes this build say it."""

    code: str
    #: Builds a project under ``root`` and hands back the notes its gate emitted. Every row
    #: has one: a code with no state that produces it is a sentence nothing has read, which
    #: is what this census exists to end.
    build: Callable[[Path], tuple[Note, ...]]
    #: What the state is, in one clause — the row's own reason, so a reader meeting a red
    #: knows what stopped being true rather than only which code went silent.
    because: str

    def measure(self, root: Path) -> Note:
        """Run the state and hand back this row's note, refusing a row that produced none."""
        found = [one for one in self.build(root) if one.code == self.code]
        assert found, f"{self.code}: {self.because} — and the gate said nothing"
        return max(found, key=lambda one: len(one.message))


PRICED: tuple[Priced, ...] = (
    Priced("read.priced", _read_priced, "more open lines left out of the ranking than priced"),
    Priced("incidental.absent", _incidental_absent, "an incidental path this tree does not hold"),
    Priced("deps.collective", _deps_collective, "one block token naming two open lines"),
    Priced("budget.translated", _budget_translated, "a byte budget against a CRLF working tree"),
    Priced("priority.config", _priority_config, "a queue in the file and an order in the config"),
    Priced(
        "priority.block-unstarted",
        _priority_block_unstarted,
        "a tier queuing a block nothing is filed under",
    ),
    Priced("non-goal.reaches", _non_goal_reaches, "a symptom sharing a rare word with a lead"),
    Priced("non-goal.settled", _non_goal_settled, "the same pair, answered in the design"),
    Priced("section.unpaired", _section_unpaired, "a design edited since HEAD and its line not"),
    Priced("task.worked", _task_worked, "source a design names, moved, with the line open"),
    Priced("block.worked", _block_worked, "the same, true of every line under one heading"),
    Priced("block.emptied", _block_emptied, "a block that held open lines at HEAD and holds none"),
    Priced("block.reopened", _block_reopened, "the same block, in the other direction"),
    Priced("install.absent", _install_absent, "a wired project missing one of the pages"),
    Priced("install.stale", _install_stale, "a wired surface behind the engine answering here"),
    Priced("gate.behind", _gate_behind, "an enforced project pinned to a version this gate is past"),
    Priced(
        "engine.disagreement",
        _engine_disagreement,
        "all four clauses at once, which no checkout of this repository can produce",
    ),
)
