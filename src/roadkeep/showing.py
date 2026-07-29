"""One task, from wherever its parts live (RK12).

A task is a line in one file, a rationale section in another, and sometimes a path on
disk. Nothing joins them, so reading one task means loading two whole files to reach
forty lines — the cost §RK29 measured at some 5k tokens to learn one line. `show` does
the join, and the join is the whole feature: no new field, no new file, nothing stored.

Three things it derives rather than trusts:

* **Where the id is.** The roadmap and the ledger are asked in that order, because
  "RK6 shipped" is an answer and "no such task" is a different one (RK28's `NotOpen`
  makes the same distinction one file up).
* **Whether the pointer resolves.** A `→ §RK12` whose section does not exist reads as a
  design that does. Here it is reported as an absence *with the reason* — deleted on
  ship, never written, or no prose file declared at all — because those are three
  different states and only one of them is a defect (`lint` gates it: RK15).
* **The paths its text names.** Kept only when the file is really there, or when the
  token is slash-shaped and therefore an explicit claim about the repository. That rule
  is what separates `docs/specs/show.md` (missing, worth saying) from `Config.load`
  (a dotted name in prose, and not this tool's business to report as a broken file).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from roadkeep.config import Config
from roadkeep.document import Entry
from roadkeep.schema import Task
from roadkeep.sections import Section, find

#: A path as prose spells one: inside backticks, or as a Markdown link target. Both are
#: deliberate acts of quoting, unlike a bare word that happens to contain a dot.
_QUOTED = re.compile(r"`([^`\s]+)`|\]\(([^)\s]+)\)")
_SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:")


class NoSuchTask(KeyError):
    """An id that is in neither governed file. Not a lint error — a wrong question."""

    def __init__(self, task_id: str, where: tuple[str, ...]) -> None:
        self.task_id = task_id
        super().__init__(
            f"no task {task_id} in {' or '.join(where)}: an id in neither file was "
            f"never written or was retired (RK32)"
        )


@dataclass(frozen=True, slots=True)
class Referenced:
    """A path the task's text names, and whether the repository has it."""

    path: str
    exists: bool


@dataclass(frozen=True, slots=True)
class View:
    """Everything one task is, gathered from the files that hold a piece of it."""

    entry: Entry
    role: str
    file: str
    shipped: bool
    section: Section | None
    section_file: str | None
    #: Why there is no section, when there is none. Empty when there is one.
    section_absence: str
    paths: tuple[Referenced, ...]

    @property
    def task(self) -> Task:
        return self.entry.task


def show(config: Config, task_id: str) -> View:
    """Join the line, its section and the paths it names. Reads; never writes."""
    entry, role = _locate(config, task_id)
    section, section_file, absence = _rationale(config, entry, shipped=role == "changelog")
    text = entry.raw + ("\n" + section.body if section is not None else "")
    return View(
        entry=entry,
        role=role,
        file=config.relative(config.path(role)),
        shipped=role == "changelog",
        section=section,
        section_file=section_file,
        section_absence=absence,
        paths=paths_in(text, config.root),
    )


def _locate(config: Config, task_id: str) -> tuple[Entry, str]:
    asked: list[str] = []
    for role in ("roadmap", "changelog"):
        if not config.has(role) or not config.path(role).is_file():
            continue
        asked.append(config.relative(config.path(role)))
        found = config.document(role).by_id().get(task_id)
        if found is not None:
            return found, role
    raise NoSuchTask(task_id, tuple(asked))


def _rationale(
    config: Config, entry: Entry, shipped: bool
) -> tuple[Section | None, str | None, str]:
    if not config.has("improvements"):
        return None, None, "this project declares no improvements file"
    path = config.path("improvements")
    where = config.relative(path)
    if not path.is_file():
        return None, where, f"{where} is not on disk yet"
    section = find(config.document("improvements"), entry.task.ref or entry.task.id)
    if section is not None:
        return section, where, ""
    if shipped:
        # Not a defect: `ship` deletes the section, which is what keeps the prose file a
        # design file rather than a second changelog (RK6).
        return None, where, "deleted on ship, which is where the rationale ends"
    anchor = entry.task.ref or entry.task.id
    return None, where, f"§{anchor} is not in {where}: the pointer resolves to nothing"


def paths_in(text: str, root: Path) -> tuple[Referenced, ...]:
    """Quoted paths, deduplicated, in order of appearance.

    Public because RK29 joins the same list onto a wider answer, and a second
    implementation would disagree about what counts as a path.
    """
    out: dict[str, Referenced] = {}
    for match in _QUOTED.finditer(text):
        token = (match.group(1) or match.group(2)).rstrip(".,;:")
        if not token or _SCHEME.match(token) or token.startswith("#"):
            continue
        exists = (root / token).exists() if not Path(token).is_absolute() else False
        # Either the repository really has it, or the token is slash-shaped and so an
        # explicit claim about the repository — a missing one of those is worth saying.
        if exists or "/" in token:
            out.setdefault(token, Referenced(path=token, exists=exists))
    return tuple(out.values())
