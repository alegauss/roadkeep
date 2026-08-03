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

import os
import re
from dataclasses import dataclass
from pathlib import Path

from roadkeep.config import PROSE_ROLES, Config
from roadkeep.document import Document, Entry
from roadkeep.history import tracked_now
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
#: A token made of nothing but separators and dots names no artefact — a lone `\` quoted
#: as a character, `./`, `..`. Two of Turing's ledger entries quote one, and on Windows a
#: bare backslash *resolves*, to the drive root, so it read as a path the repository has
#: until RK218 stopped asking the disk about a revision. Refused rather than resolved,
#: because what it resolves to depends on the platform running the gate.
_SEPARATORS_ONLY = re.compile(r"^[\\/.]+$")


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
    #: Every source line this entry owns, verbatim and with its endings (RK194). One on any
    #: line a governed roadmap holds — the format has no multi-line task line — and more only
    #: on a ledger written before this tool, where a bullet wraps. The span has been a fact
    #: since RK157 and every *writer* uses it; this is the reader that prints it, so what
    #: `record amend --lines` replaces is a command's answer rather than a file to open.
    lines: tuple[str, ...] = ()

    @property
    def task(self) -> Task:
        return self.entry.task

    @property
    def wrapped(self) -> bool:
        """Whether the sentence runs past the line the parse read it from."""
        return self.entry.wrapped


def show(config: Config, task_id: str) -> View:
    """Join the line, its section and the paths it names. Reads; never writes."""
    entry, role, document = _locate(config, task_id)
    section, section_file, absence = _rationale(config, entry, shipped=role == "changelog")
    owned = document.lines[entry.index : entry.stop]
    # The whole entry, and not `entry.raw`: on a wrapped bullet the tail is the rest of the
    # sentence, so a path quoted there is one this task names (RK194).
    text = "".join(owned) + ("\n" + section.body if section is not None else "")
    return View(
        entry=entry,
        role=role,
        lines=owned,
        file=config.relative(config.path(role)),
        shipped=role == "changelog",
        section=section,
        section_file=section_file,
        section_absence=absence,
        # Both bases, for the reason RK51 gives: the line and its section are read from a
        # file, and a link relative to that file names an artefact the repository has.
        paths=paths_in(
            text, config.root, near=config.path(role).parent, known=known_directories(config)
        ),
    )


def _locate(config: Config, task_id: str) -> tuple[Entry, str, Document]:
    asked: list[str] = []
    for role in ("roadmap", "changelog"):
        if not config.has(role) or not config.path(role).is_file():
            continue
        asked.append(config.relative(config.path(role)))
        document = config.document(role)
        found = document.by_id().get(task_id)
        if found is not None:
            # The document too, and not the entry alone: the lines an entry owns are the
            # file's, and loading it a second time to reach them is a second parse (RK194).
            return found, role, document
    raise NoSuchTask(task_id, tuple(asked))


def _rationale(
    config: Config, entry: Entry, shipped: bool
) -> tuple[Section | None, str | None, str]:
    """The section the pointer addresses, from **whichever** prose role declares it (RK186).

    RK172 taught resolution that a pointer addresses every governed prose file, because
    `[files]` declares strategy as a role and a line pointing at it is already in the model.
    It taught the gate and not this reader — and this is the worse half to leave: `lint` is
    the backstop and is read once, while `show` and `brief` are what *start* a task. An agent
    told the pointer resolves to nothing writes the design a second time, under an anchor the
    line does not name, which is the `section.unreachable` RK135 exists to report.

    Two roles declaring one anchor is the ambiguity, not a first match: reading the first is
    what billed T354's `§X.1` 365 words of somebody else's subtree without saying so, and
    `ref.ambiguous` is the gate's own word for it.
    """
    anchor = entry.task.ref or entry.task.id
    roles = tuple(role for role in PROSE_ROLES if config.has(role))
    if not roles:
        return None, None, f"this project declares no {' or '.join(PROSE_ROLES)} file"
    named = " or ".join(config.relative(config.path(role)) for role in roles)
    # Where the design would go, for every answer that has no section: the first declared
    # role, which is `improvements` wherever a project declares one.
    where = config.relative(config.path(roles[0]))
    on_disk = tuple(role for role in roles if config.path(role).is_file())
    if not on_disk:
        return None, where, f"{named} is not on disk yet"
    found = [
        (config.relative(config.path(role)), section)
        for role in on_disk
        if (section := find(config.document(role), anchor)) is not None
    ]
    if len(found) == 1:
        return found[0][1], found[0][0], ""
    if found:
        both = " and ".join(file for file, _ in found)
        return (
            None,
            None,
            f"§{anchor} is declared by {both}: one anchor names one section, and a "
            f"pointer resolving to two resolves to neither",
        )
    if shipped:
        # Not a defect: `ship` deletes the section, which is what keeps the prose file a
        # design file rather than a second changelog (RK6).
        return None, where, "deleted on ship, which is where the rationale ends"
    return None, where, f"§{anchor} is not in {named}: the pointer resolves to nothing"


def paths_in(
    text: str,
    root: Path,
    *,
    near: Path | None = None,
    known: frozenset[str] | None = None,
) -> tuple[Referenced, ...]:
    """Quoted paths, deduplicated, in order of appearance.

    Public because RK29 joins the same list onto a wider answer, and a second
    implementation would disagree about what counts as a path.

    `near` is the directory the text was read from, and a token resolves against it as
    well as against `root` (RK51). Both conventions are live: this repository writes
    root-relative tokens in its own lines, Shio writes the file-relative ones Markdown
    itself reads — 886 of them — and the question being asked is whether the repository
    has the artefact, not whether the link would render from where it is written.

    `known` is every directory the repository knows about, which is what decides whether a
    token is a *claim* at all (RK217, and see :func:`_claims_a_file`). Passed in rather than
    computed here, because it costs two git calls and this function is called per entry —
    and omitted by a caller with no repository, which keeps the filesystem answer.
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
        if _UNRESOLVABLE.search(token) or _SEPARATORS_ONLY.match(token):
            # Nothing on disk can settle it either way, so there is no question to ask.
            continue
        exists = _resolves(token, root, near)
        # Either the repository really has it, or the token is a decidable claim that it
        # should: a filename whose directory is there (RK55). A slash alone is not — 60 of
        # Shio's 61 findings were a MIME type, an i18n key or two method names sharing one.
        if exists or _claims_a_file(token, root, near, known):
            out.setdefault(token, Referenced(path=token, exists=exists))
    return tuple(out.values())


def _claims_a_file(
    token: str, root: Path, near: Path | None, known: frozenset[str] | None
) -> bool:
    """Whether a token that does not resolve is nonetheless a claim about a file (RK55).

    Both halves are needed. The extension is what tells `lib/shio.ts` from
    `ShPostUnifiedWriteService.update/publish`; the directory is what tells a file this
    repository lost from one that was never in it — the `app/api/…` of a template it
    generates elsewhere. Together they took Shio's 61 findings to the one true row: a Java
    class the ledger still names under the directory it was renamed inside.

    ``known`` is the second half asked of the **repository** rather than of this disk
    (RK217). The filesystem was a proxy, and it failed in the direction that costs most: a
    ledger naming `lib/gone.py` reported when that one file went and reported *nothing*
    when `lib/` went with it, which is the larger deletion. Given the directories the
    repository tracks or has declared it never will, the answer stops depending on what
    somebody last built or cleaned.

    Measured before the change, over both pins: 7246 distinct tokens, and the two rules
    disagree on **none** of them — so what RK55 closed stays closed and nothing new is
    admitted. The difference only appears once the disk stops matching the repository,
    which is exactly the state the gate has to survive. ``None`` keeps the filesystem
    answer, for a caller with no repository to ask.
    """
    head, _, name = token.rpartition("/")
    if not head or "." not in name:
        return False
    bases = (root,) if near is None else (near, root)
    if known is None:
        return any((base / head).is_dir() for base in bases)
    return any(_within(base / head, root) in known for base in bases)


def known_directories(
    config: Config, names: frozenset[str] | None = None
) -> frozenset[str] | None:
    """Every directory this repository knows about, tracked or declared untracked (RK217).

    The set `_claims_a_file` asks instead of the disk: every prefix of every tracked path,
    built once per command from one listing rather than a stat per token.

    **Tracked only, and no ignored directory in it.** A `bin/Release/app.exe` under an
    ignored `bin/` would be admitted here and then withheld by `declared_untracked` (RK213)
    one step later, so adding it would be a `check-ignore` per head for an answer that does
    not change. The two rules compose in that order on purpose: this one asks whether the
    token is a claim about *this* repository, and that one asks whether the repository said
    it would never hold the file.

    ``names`` is the tracked listing a caller already holds, so a `lint` run at a revision
    passes that revision's and this does not ask twice. Absent, the working tree's is read.

    **None where git cannot answer**, and the caller falls back to the disk. An absent
    answer is not a negative one (RK95, and RK28 one file up): a checkout with no history
    tracks nothing and declares nothing, so reading its silence as "no directory here is
    the repository's" would drop every path claim in the file rather than decide it.

    The root is in the set, because a token written from a governed file's own directory
    can name it — `../outside.txt` from `docs/` is a path at the top of the repository, and
    the repository certainly knows that directory.
    """
    if names is None:
        names = tracked_now(config)
    if not names:
        return None
    return frozenset(
        {"."}
        | {
            "/".join(segments[:cut])
            for name in names
            for segments in (name.split("/"),)
            for cut in range(1, len(segments))
        }
    )


def _within(path: Path, root: Path) -> str | None:
    """A path as the repository spells it, or None where it climbs out of the tree."""
    try:
        spelled = os.path.relpath(path.resolve(), root.resolve()).replace(os.sep, "/")
    except ValueError:  # a different mount, so not this repository's at all
        return None
    return None if spelled.startswith("..") else spelled


def _resolves(token: str, root: Path, near: Path | None) -> bool:
    """Whether the repository has this artefact, under either convention (RK51)."""
    if Path(token).is_absolute():
        # Refused in a config and meaningless in a line: it is a claim about one machine.
        return False
    bases = (root,) if near is None else (near, root)
    return any((base / token).exists() for base in bases)
