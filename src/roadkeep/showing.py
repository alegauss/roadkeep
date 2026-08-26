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
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from roadkeep.config import DESIGN_ROLES, PROSE_ROLES, Config
from roadkeep.kernel.document import Document, Entry
from roadkeep.history import indexed
from roadkeep.provenance import invocation
from roadkeep.kernel.schema import Task
from roadkeep.sections import Section, addressable, declaring, find, heading_of

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

    #: What an id in neither file means when it is nothing else. Replaced rather than
    #: appended to where the argument turns out to address a live section (RK1025): "never
    #: written or was retired" and "it is the section over there" are two different answers,
    #: and printing both makes the refusal argue with itself.
    ABSENT = "an id in neither file was never written or was retired (RK32)"

    def __init__(self, task_id: str, where: tuple[str, ...], instead: str = "") -> None:
        self.task_id = task_id
        #: The verb one word away, where the argument turned out to address a section
        #: (RK1025). Empty on the ordinary case, which is an id nothing carries.
        self.instead = instead
        super().__init__(
            f"no task {task_id} in {' or '.join(where)}: {instead or self.ABSENT}"
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
    #: Which prose role declared it, so a reader can reach that file's own `section = <n>`
    #: (RK287). The file alone cannot: `[limits.<role>]` is keyed by the role, and a printer
    #: that re-derived it from the path would be the second answer to a settled question.
    section_role: str | None
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

    def stated(self, config: Config, *, body: bool = True) -> str:
        """One task as a reader is told it, heading and prose included (RK9).

        Beside :meth:`payload` since RK1170: these two were a printer in the handler and a builder
        in `rendering.py`, so one answer was spelled in two files and neither held both. `config`
        is passed and not stored — the limit beside a section's count is the *role's*, and which
        file declared it is a fact about the project rather than about this view (RK287).
        """
        state = "shipped" if self.shipped else "open"
        task, section = self.task, self.section
        rows = [
            f"{task.id}  Block {task.block}  {task.status}  {state}  "
            f"{self.file}:{self.entry.lineno}",
            f"  symptom  {task.symptom}",
            f"  why      {task.why}",
        ]
        if self.wrapped:
            # The rest of the sentence, verbatim (RK194): the fields above hold only as much of it
            # as fits on the first line, and this is exactly what `record amend --lines` says it
            # replaces — so the caller confirms the count here instead of opening the file.
            rows.append(
                f"  wrapped  {len(self.lines)} lines, {self.entry.lineno}-{self.entry.stop}"
            )
            rows += [
                f"  {offset:<9}{raw.rstrip()}"
                for offset, raw in enumerate(self.lines, start=self.entry.lineno)
            ]
        if task.deps:
            rows.append(f"  deps     {', '.join(dep.render() for dep in task.deps)}")
        # And what the line is waiting **for**, which is not a dep (RK1311): a `(requires: …)`
        # group says what has to be present for the work to be finishable, and this read — the
        # one that joins a task out of every file holding a piece of it — printed the marker,
        # the deps, the section and the budget, and nothing about it. Below the deps because
        # that is the order the line spells them in, and silent where there are none, as the
        # deps row is: a group nobody wrote is not an absence to report.
        if task.requires:
            rows.append(f"  requires {', '.join(task.requires)}")
        if section is not None:
            # The role that declared it, so the limit printed beside the count is the one this
            # file is held to (RK287) — `[limits.<role>]` is per prose file, exactly as it is for
            # the changelog. A section exists only where a role declared it.
            limit = config.schema_for(str(self.section_role)).section_max
            rows.append(
                f"  section  {self.section_file}:{section.first}  "
                f"§{section.anchor}, {section.counted(limit)}"
            )
        else:
            # The absence carries its reason: deleted on ship, never written, or no prose file at
            # all are three states, and only one of them is a defect (RK15).
            rows.append(f"  section  none — {self.section_absence}")
        rows += [
            f"  path     {one.path}{'' if one.exists else '  (missing)'}" for one in self.paths
        ]
        if section is not None and body:
            rows += ["", heading_of(config.schema, section), "", section.body]
        return "\n".join(rows)

    def payload(self, *, body: bool = True) -> dict[str, object]:
        """The same answer as data, with the prose only where it was asked for (RK9).

        Beside :meth:`stated` since RK1170, and the two differ on purpose: the printed register
        is what a reader scans, and this carries the span a correction replaces and the absence
        reason a client cannot infer.
        """
        task, section = self.task, self.section
        body = None if not body or section is None else section.body
        return {
            "id": task.id,
            "status": task.status,
            "block": task.block,
            "shipped": self.shipped,
            "file": self.file,
            "line": self.entry.lineno,
            "rendered": self.entry.raw,
            # The whole entry, and the span a correction replaces (RK194). Always present, so a
            # caller reads the count rather than inferring one from a key that came and went.
            "lines": [raw.rstrip("\r\n") for raw in self.lines],
            "wrapped": self.wrapped,
            "symptom": task.symptom,
            "why": task.why,
            "deps": [dep.render() for dep in task.deps],
            # What has to be present for this to be finishable (RK1311), which is not a dep and
            # is what `pick --have` filters on. `[]` and never omitted, for `deps`' reason: a
            # key that appears only when it is set is one a reader learns to stop looking for.
            "requires": list(task.requires),
            "ref": task.ref,
            "section": None
            if section is None
            else {**section.payload(self.section_file or ""), "body": body},
            "section_absence": self.section_absence,
            "paths": [{"path": p.path, "exists": p.exists} for p in self.paths],
        }


def show(config: Config, task_id: str) -> View:
    """Join the line, its section and the paths it names. Reads; never writes."""
    entry, role, document = _locate(config, task_id)
    section, section_file, section_role, absence = _rationale(
        config, entry, shipped=role == "changelog"
    )
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
        section_role=section_role,
        section_absence=absence,
        # Both bases, for the reason RK51 gives: the line and its section are read from a
        # file, and a link relative to that file names an artefact the repository has.
        paths=paths_in(
            text,
            config.root,
            near=config.path(role).parent,
            known=lambda: known_directories(config),
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
    raise NoSuchTask(task_id, tuple(asked), _instead(config, task_id))


def _instead(config: Config, given: str) -> str:
    """The verb one word away, where the argument addresses a section (RK1025).

    `show XX` used to answer *"no task XX … never written or was retired"*, which is
    accurate and answers a question nobody asked: `XX` is the shape this tool prints in
    every `→ §XX.1` it writes, and `section show XX` is the verb for it. The refusal said
    what the argument was **not**, in a vocabulary the caller was not using, and the next
    move it left them was a grep of the file the guard exists to keep them out of.

    Two answers and they are not the same claim. A prose file that **declares** the address
    is a fact — the section is there, and this is a redirect. An address the outline merely
    *could* number is a reading of the argument's shape, which is worth saying because a
    caller who typed one is holding a pointer, and is not worth stating as if a section
    existed. A `§` the caller typed is the third: nobody writes a sigil at a task id.

    **Named and never dispatched.** `show` joins a line, its section and its paths; `section
    show` prints one section and its word count. A verb that quietly answered the other
    question would be the second answer to one argument, which is what this repository
    refuses everywhere else — and the caller who wanted the join would get the section and
    no way to see that they had.
    """
    paused = _paused(config, given)
    if paused:
        return paused
    anchor = given.lstrip("§")
    if not anchor:
        return ""
    verb = f"`{invocation()} section show {anchor}`"
    where = declaring(config, anchor)
    if where:
        files = " and ".join(config.relative(config.path(role)) for role in where)
        return f"§{anchor} is a section in {files}, which {verb} prints"
    if given.startswith("§") or addressable(config.schema, anchor):
        return (
            f"{NoSuchTask.ABSENT}, and §{anchor} is a section address rather than an id "
            f"— {verb} reads one"
        )
    return _where_it_went(config, anchor)


def _paused(config: Config, task_id: str) -> str:
    """The store's answer, where the two carriers this read opens have none (RK1341).

    `defer` moves a line out of the backlog on purpose, so every task-addressed read declining
    it is right: `pick` skips it, `list` omits it, and that is the whole point of the verb.
    What none of them said is *where it went* — `show` answered `an id in neither file was
    never written or was retired`, and both of those are false about a line sitting in
    `DEFERRED.md` with a reason beside it.

    First of the three answers here and not last, because it is the strongest: a declared
    carrier holding the id is a fact, where an addressable anchor is a reading of the
    argument's shape and history is evidence the id once existed. It is also the cheapest —
    one parse against `_where_it_went`'s `git log` — and it is asked only after the parse has
    failed, which is the rule that keeps this whole path free.

    Silent where no `deferred` role is declared, that project having no such state to be in.
    """
    if not config.has("deferred") or not config.path("deferred").is_file():
        return ""
    entry = config.document("deferred").by_id().get(task_id)
    if entry is None:
        return ""
    where = config.relative(config.path("deferred"))
    # Both doors, in the order the reader needs them: what it says, then how to undo it. The
    # read comes first because a paused line is usually being *checked*, not resumed.
    return (
        f"{task_id} is paused in {where}:{entry.lineno} — "
        f"`{invocation()} list --role deferred` prints it with the reason it was set aside, "
        f"and `{invocation()} resume {task_id}` returns it to its block"
    )


def _where_it_went(config: Config, task_id: str) -> str:
    """History's answer, where the parse has none (RK1048).

    `Document.by_id()` keys an entry by the id it **leads with**, so an entry delivering two
    things is visible under one of them. Measured in Shio: `docs/CHANGELOG.md:150` opens
    `- **SH154** …` and its sentence also ships `**SH169**`, so `show SH169` answered *never
    written or was retired* about a task that is in the file — while `gaps` resolved it to
    `c843f449 feat(agent): verify and digest see a page's section references (SH154, SH169)`.
    Two readers of one file, disagreeing.

    Asked **only after the parse has failed**, so the answer path costs nothing and a common
    typo costs one `git log` on a refusal that was already being composed. And it says only
    what it found: a commit is evidence the id was written, never a claim about which entry
    holds it — that is `gaps`', and naming it is what this sentence is for.

    Silent where git cannot answer. A shallow clone, a tarball, an unindexed tree: the
    absence is the refusal's own, and inventing a whereabouts from a failed search would be
    the worse half of the defect this closes.
    """
    # Deferred: `history` shells out, and the overwhelming majority of `show` calls resolve.
    from roadkeep.history import HistoryUnavailable, origin_of  # noqa: PLC0415 - RK1002

    try:
        found = origin_of(config, task_id)
    except (HistoryUnavailable, OSError):
        return ""
    commit = found.shipped_in or found.proposed_in
    if commit is None:
        return ""
    return (
        f"{NoSuchTask.ABSENT} — but {commit.short} wrote it "
        f"({commit.subject}), so it is in a line this parse reads under another id: "
        f"`{invocation()} gaps` resolves which"
    )


def _rationale(
    config: Config, entry: Entry, shipped: bool
) -> tuple[Section | None, str | None, str | None, str]:
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
    anchor = _decided_anchor(config, entry) or entry.task.ref or entry.task.id
    # Searched across every prose role and *placed* in the design's two (RK1361). The two
    # questions parted when `decisions` became a prose file: an anchor is resolved wherever a
    # heading may declare it, so a decision's own body is found by `show` — while "where the
    # design would go" is still improvements or strategy, a decisions file being somewhere a
    # task's rationale never goes and so not an absence a `declare` here would close.
    roles = tuple(role for role in PROSE_ROLES if config.has(role))
    designed = tuple(role for role in DESIGN_ROLES if config.has(role))
    if not designed:
        return None, None, None, f"this project declares no {' or '.join(DESIGN_ROLES)} file"
    named = " or ".join(config.relative(config.path(role)) for role in roles)
    # Where the design would go, for every answer that has no section: the first declared
    # role, which is `improvements` wherever a project declares one.
    where = config.relative(config.path(designed[0]))
    on_disk = tuple(role for role in roles if config.path(role).is_file())
    if not on_disk:
        return None, where, None, f"{named} is not on disk yet"
    found = [
        (config.relative(config.path(role)), role, section)
        for role in on_disk
        if (section := find(config.document(role), anchor)) is not None
    ]
    if len(found) == 1:
        return found[0][2], found[0][0], found[0][1], ""
    if found:
        both = " and ".join(file for file, _, _ in found)
        return (
            None,
            None,
            None,
            f"§{anchor} is declared by {both}: one anchor names one section, and a "
            f"pointer resolving to two resolves to neither",
        )
    if shipped:
        # Not a defect: `ship` deletes the section, which is what keeps the prose file a
        # design file rather than a second changelog (RK6).
        return None, where, None, "deleted on ship, which is where the rationale ends"
    return None, where, None, f"§{anchor} is not in {named}: the pointer resolves to nothing"


def _decided_anchor(config: Config, entry: Entry) -> str:
    """Where this id's **decision** keeps its body, if a record here has one (RK1363).

    A ship deletes the design and files the decision, so once a line is in the ledger the
    prose that survives is the decision's — and under `ref_scheme = "id"` this read found it
    already, the anchor being the id either way. Under an outline it did not: the address is
    the `--decides-ref` the record carries, and nothing else in the project spells it.

    Never a shadow of a live line's own design: a decision is filed at the moment a line
    departs, so no id is both an open line and a record here. Empty where the project
    declares no decisions file, which is most of them.
    """
    if not config.has("decisions") or not config.path("decisions").is_file():
        return ""
    recorded = config.document("decisions").by_id().get(entry.task.id)
    return "" if recorded is None else (recorded.task.ref or "")


def paths_in(
    text: str,
    root: Path,
    *,
    near: Path | None = None,
    known: Callable[[], frozenset[str] | None] | None = None,
    has: Callable[[str], bool] | None = None,
) -> tuple[Referenced, ...]:
    """Quoted paths, deduplicated, in order of appearance.

    Public because RK29 joins the same list onto a wider answer, and a second
    implementation would disagree about what counts as a path.

    `near` is the directory the text was read from, and a token resolves against it as
    well as against `root` (RK51). Both conventions are live: this repository writes
    root-relative tokens in its own lines, Shio writes the file-relative ones Markdown
    itself reads — 886 of them — and the question being asked is whether the repository
    has the artefact, not whether the link would render from where it is written.

    `known` answers *which directories the repository knows about*, which is what decides
    whether a token is a claim at all (RK217, and see :func:`_claims_a_file`). A **callable**
    and not the set, because the set costs a git listing and is needed only for a token that
    fails `exists` — which on a healthy repository is none of them (RK222): `show` went from
    1.1 ms to 36.6 ms here and 4.2 ms to 73.4 ms on Turing by computing it up front, on the
    read that starts every task. Called at most once per run of this function, and never
    where every path resolves. Omitted, or answering None, keeps the filesystem answer.

    `has` answers *does the tree being judged hold this artefact*, and the disk is only its
    default (RK225). A run naming a revision may not consult the disk (RK218) and used to
    consult it anyway — 34070 `stat` calls at Turing's pin, every one discarded — and worse,
    `exists` decides **candidacy** here, so the candidate set was still half decided by this
    afternoon while the findings were about a commit.
    """
    out: dict[str, Referenced] = {}
    directories: frozenset[str] | None = None
    asked = False
    for match in _QUOTED.finditer(text):
        token = (match.group(1) or match.group(2)).rstrip(".,;:")
        if not token or _SCHEME.match(token) or token.startswith("#"):
            continue
        # One spelling, whatever platform wrote the line (RK226). A backslash separates on
        # Windows and is an ordinary filename character everywhere else, so `docs\specs\x.md`
        # resolved for its author and was a single unheard-of name in CI — the gate answering
        # by host, which is RK213's shape through a different door. Normalised *toward* the
        # repository's own spelling, because git's listing is forward slashes on every
        # platform; a real filename holding a backslash is the case this gets wrong, and it
        # cannot exist on Windows at all and breaks every Windows checkout where it can.
        token = _LINE_ANCHOR.sub("", token.replace("\\", "/"))
        if token.startswith("/"):
            # Not this repository: `/roadkeep:add` is a slash command, and an absolute
            # path is wrong on every other machine (which `roadkeep.toml` also refuses).
            # Both are slash-shaped, so without this they read as claims about a file
            # that is missing — four of them on one line, in RK25's own text.
            continue
        if _UNRESOLVABLE.search(token) or _SEPARATORS_ONLY.match(token):
            # Nothing on disk can settle it either way, so there is no question to ask.
            continue
        exists = has(token) if has is not None else on_disk(token, root, near)
        # Either the repository really has it, or the token is a decidable claim that it
        # should: a filename whose directory the repository knows (RK55, RK217). A slash
        # alone is not — 60 of Shio's 61 findings were a MIME type, an i18n key or two
        # method names sharing one.
        if not exists and known is not None and not asked:
            directories, asked = known(), True
        if exists or _claims_a_file(token, root, near, directories):
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

    ``names`` is the listing a caller already holds, so a run at a revision passes that
    revision's and this does not ask twice. Absent, the **index** is read and not
    :func:`tracked_now` (RK221): that one subtracts what git calls deleted, which is right
    for "does the tree still have this artefact" and exactly wrong here — a ledger naming
    `lib/gone.py` after the file went would stop being a claim instead of becoming a
    finding, and `show` said the task named no path at all while `lint` reported it missing.

    **None where git cannot answer**, and the caller falls back to the disk. An absent
    answer is not a negative one (RK95, and RK28 one file up): a checkout with no history
    tracks nothing and declares nothing, so reading its silence as "no directory here is
    the repository's" would drop every path claim in the file rather than decide it.

    The root is in the set, because a token written from a governed file's own directory
    can name it — `../outside.txt` from `docs/` is a path at the top of the repository, and
    the repository certainly knows that directory.
    """
    if names is None:
        names = indexed(config)
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


def on_disk(token: str, root: Path, near: Path | None) -> bool:
    """Whether *this working tree* has the artefact, under either convention (RK51).

    Public because it is the default answer to "does the tree being judged hold this" and
    a caller judging a **revision** supplies a different one (RK225). Named for what it
    reads rather than for what it decides, so the two cannot be confused at a call site.
    """
    if Path(token).is_absolute():
        # Refused in a config and meaningless in a line: it is a claim about one machine.
        return False
    bases = (root,) if near is None else (near, root)
    return any((base / token).exists() for base in bases)
