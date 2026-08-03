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
  Slash-shaped is not sufficient on its own: a glob, an elision, a placeholder or an npm
  scope names a *class* of file rather than one, so it is dropped before disk is asked
  (RK46) — asking would only ever answer "missing", and eight such answers on Shio were
  eight false ones.
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
#: A quoted token that stands for a *class* of file, not a file: a glob, an elision, a
#: placeholder, an npm scope. Each is slash-shaped, so each would otherwise read as a
#: claim the repository fails — `blueprints/*/files/package.json`, `monaco-editor/esm/vs/…`,
#: `template/widget/<name>.html`, `@graphiql/react`, four of the eight RK46 measured.
_UNRESOLVABLE = re.compile(r"[*…<]|^@")
#: A line anchor, which addresses a place *inside* a file and is not part of its name
#: (RK173): `scripts/prerender.mjs#L35`, `#L12-L20`. Two of Turing's eight `path.missing`
#: findings were this and nothing else — a token quoted the way GitHub spells a citation.
_LINE_ANCHOR = re.compile(r"#L\d+(?:-L?\d+)?$")


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
        # Both bases, for the reason RK51 gives: the line and its section are read from a
        # file, and a link relative to that file names an artefact the repository has.
        paths=paths_in(text, config.root, near=config.path(role).parent),
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


def paths_in(text: str, root: Path, *, near: Path | None = None) -> tuple[Referenced, ...]:
    """Quoted paths, deduplicated, in order of appearance.

    Public because RK29 joins the same list onto a wider answer, and a second
    implementation would disagree about what counts as a path.

    `near` is the directory the text was read from, and a token resolves against it as
    well as against `root` (RK51). Both conventions are live: this repository writes
    root-relative tokens in its own lines, Shio writes the file-relative ones Markdown
    itself reads — 886 of them — and the question being asked is whether the repository
    has the artefact, not whether the link would render from where it is written.
    """
    out: dict[str, Referenced] = {}
    for match in _QUOTED.finditer(text):
        token = (match.group(1) or match.group(2)).rstrip(".,;:")
        if not token or _SCHEME.match(token) or token.startswith("#"):
            continue
        token = _LINE_ANCHOR.sub("", token)
        if token.startswith("/"):
            # Not this repository: `/roadkeep:add` is a slash command, and an absolute
            # path is wrong on every other machine (which `roadkeep.toml` also refuses).
            # Both are slash-shaped, so without this they read as claims about a file
            # that is missing — four of them on one line, in RK25's own text.
            continue
        if _UNRESOLVABLE.search(token):
            # Nothing on disk can settle it either way, so there is no question to ask.
            continue
        exists = _resolves(token, root, near)
        # Either the repository really has it, or the token is a decidable claim that it
        # should: a filename whose directory is there (RK55). A slash alone is not — 60 of
        # Shio's 61 findings were a MIME type, an i18n key or two method names sharing one.
        if exists or _claims_a_file(token, root, near):
            out.setdefault(token, Referenced(path=token, exists=exists))
    return tuple(out.values())


def _claims_a_file(token: str, root: Path, near: Path | None) -> bool:
    """Whether a token that does not resolve is nonetheless a claim about a file (RK55).

    Both halves are needed. The extension is what tells `lib/shio.ts` from
    `ShPostUnifiedWriteService.update/publish`; the existing directory is what tells a file
    this repository lost from one that was never in it — the `app/api/…` of a template it
    generates elsewhere. Together they took Shio's 61 findings to the one true row: a Java
    class the ledger still names under the directory it was renamed inside.
    """
    head, _, name = token.rpartition("/")
    if not head or "." not in name:
        return False
    bases = (root,) if near is None else (near, root)
    return any((base / head).is_dir() for base in bases)


def _resolves(token: str, root: Path, near: Path | None) -> bool:
    """Whether the repository has this artefact, under either convention (RK51)."""
    if Path(token).is_absolute():
        # Refused in a config and meaningless in a line: it is a claim about one machine.
        return False
    bases = (root,) if near is None else (near, root)
    return any((base / token).exists() for base in bases)
