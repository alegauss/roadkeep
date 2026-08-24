"""The merge git cannot make, in a file only this tool may write (RK120).

`renumber` (RK97) is the repair for two branches that spent one id. This is the door that
stops the collision from arriving as a hand edit. Two worktrees each scan their own tree,
each derive the same next id, and each append under the same block heading — so git sees
two insertions at one line and writes conflict markers into a file whose only legal writer
is this tool. Resolving them means editing the format by hand, which the guard (RK22)
denies and the gate (RK14) refuses. Worse is the case that does **not** conflict: two
branches touching different blocks merge clean, and the duplicate id lands in silence.

A textual merge guesses because it reads lines. This file is a schema, which makes the
merge **decidable**: a task line is keyed by its id and filed under a declared heading, so
"what changed" is a question about ids and never about line numbers.

* **Every id is decided on its own.** Against the ancestor: unchanged on one side takes the
  other side's line, identical on both sides takes either, absent from both is a deletion
  both sides made. Nothing here is a position in a file, so two branches appending under
  one heading is not a conflict at all — it is two additions.
* **Only what both sides spent is singled out.** An id **both branches created**, carrying
  different work, is the collision — reported by id, because `renumber` is what moves one
  of them and a driver that picked a side would be choosing whose task disappears. An id
  both sides *edited* differently is the ordinary content conflict, reported the same way
  and kept apart in the answer: one wants an address, the other wants a sentence.
* **The frame is one side's.** Headings, the preamble and the non-goals are prose, and the
  tool does not merge prose (L4). One side may have changed them — that side's file is the
  frame the entries are written into. Both, differently, and the merge is refused.
* **It gates what it composed.** The merged file is held to
  :func:`~roadkeep.linting.within` and to :func:`~roadkeep.linting.resolving` — what one
  file answers, and what only the backlog can (RK1353) — and the findings it refuses over
  are the ones **no version already had** (RK1352). The second half is not an extra: a dep
  on a line the other side removed exists in no version and in the merged file alone, which
  is the one class a merge is uniquely able to write, and the per-file half cannot be asked
  about it. Measured: one branch adding `RK3 (deps: RK2)` while the other removed `RK2`
  landed clean and failed `lint` afterwards; and a **cycle** is the purer case of it
  (RK1354), well-formed on both sides and present in the merged file alone, so neither
  author ever held the state they would be asked to review.
  A defect the merge creates is one nobody chose and nobody would find, the file having been
  written by a program; a defect it inherited is somebody's committed line, which `lint`
  refuses on that branch and refuses again after this lands.
  Held to every finding until RK1352 measured what that cost: a base whose `RK9` carried an
  over-long `why`, one branch adding `RK1` and the other `RK2`, neither touching `RK9` —
  refused, naming `RK9` to a reviewer mid-merge who did not choose that work, and leaving
  the project without a driver for that file until somebody cleaned a line the merge had no
  opinion about. Compared by `(code, id)` and never by line, a merge moving lines by
  construction. What that trades away is a side making an already-bad field worse: the pair
  is unchanged, so this lets it through and the gate does not — which is the division the
  first sentence of this module states, a driver being a driver.

Anything refused falls back to git's own conflict markers, whole-file, and exits non-zero.
That is not a failure of the driver: it is the driver declining to write a file it cannot
prove, leaving the reviewer exactly where a repository with no driver would have left them.

Registered per file in `.gitattributes` and per checkout in `git config`, so it is opt-in
configuration and never a rule this tool assumes (L6): `merge --register` writes both, and
prints the two lines it wrote. The command it names is derived and absolute (RK255) — a
config value is executed by git months after the shell that printed it exited, so a name
that resolved on that shell's PATH is a driver that fails at the merge it was wired for.
"""

from __future__ import annotations

import shlex
import shutil
from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep.authoring import place, remove_entry
from roadkeep.config import PROSE_ROLES, Config
from roadkeep.kernel.document import Document, Entry
from roadkeep.linting import within
from roadkeep.provenance import invocation, persisted
from roadkeep.kernel.schema import SchemaError

__all__ = [
    "Attributes",
    "Driver",
    "Merge",
    "Registration",
    "Wiring",
    "attributed",
    "config_command",
    "merge",
    "markers",
    "register",
    "registered",
    "role_of",
    "wiring",
]

#: Git's default conflict-marker width, and the labels this driver writes when it declines.
#: Whole-file rather than per-hunk: the driver made no decision, so it has no hunk to name,
#: and a marker pair around the whole file is the honest report of that.
MARKER = 7
OURS = "ours"
THEIRS = "theirs"

#: The line `.gitattributes` carries per governed file, and the driver's name in `git
#: config`. One name, so a project that registers twice registers the same thing.
DRIVER = "roadkeep"

#: The key `.gitattributes` sends git to, and the one :func:`registered` reads back.
DRIVER_KEY = f"merge.{DRIVER}.driver"

#: What `.git/config` holds for this driver, as five distinguishable facts (RK266). Kept apart
#: because the remedies differ and only one of them is a defect: `UNRUNNABLE` is a driver git
#: will call and fail, `MOVED` is one that still works and is not what this machine would write,
#: and reporting the second as the first would be crying wolf on every second checkout.
ABSENT = "absent"
CURRENT = "current"
MOVED = "moved"
UNRUNNABLE = "unrunnable"
#: Some governed files sent to the driver and not others (RK270) — the state a `.gitattributes`
#: reaches when a role was declared after it was written, and the one a whole-file yes/no hides.
PARTIAL = "partial"
#: Not an answer either way: no git, no repository, or a git too old for `config --default`.
UNKNOWN = "unknown"

#: git's own word for a path carrying no value for the attribute. Spelled here as well as in
#: :mod:`roadkeep.history`, because this module may not import that one at module level (RK260)
#: and a property cannot pay a lazy import — a test holds the two spellings together.
UNSPECIFIED = "unspecified"


@dataclass(frozen=True, slots=True)
class Merge:
    """The result of one three-way merge, and everything the answer has to say."""

    role: str
    #: The merged file, or None when it was refused — the whole clean/not-clean question.
    text: str | None
    #: Ids whose line came from the other side: added there, or edited there alone.
    took: tuple[str, ...] = ()
    #: Ids the other side removed, and this side did not touch.
    removed: tuple[str, ...] = ()
    #: Ids **both branches created**, carrying different work — the collision RK120 names.
    #: `renumber` moves one of them; a driver that picked would be deleting somebody's task.
    doubled: tuple[str, ...] = ()
    #: Ids both branches edited differently. A content conflict, kept apart from the above
    #: because the remedy is a sentence and not an address.
    contested: tuple[str, ...] = ()
    #: Ids one branch **removed** — shipped, retired, deferred out — while the other edited
    #: the line (RK482). The third remedy, and the reason it is not `contested`: nobody wrote
    #: a second sentence, so asking a reviewer to choose one describes a merge that did not
    #: happen. What is decided is whether the removal stands, and where the edit goes.
    withdrawn: tuple[str, ...] = ()
    #: Why it was refused, empty when it was not. Printed, because a driver that exits 1
    #: with no reason is one the reviewer resolves without knowing what it saw.
    reason: str = ""

    @property
    def clean(self) -> bool:
        return self.text is not None


#: The file whose lines send git to this driver. Named here because `install` has to
#: know the path before it writes anything (RK394), and a second spelling at that call site
#: is the two ends of one write disagreeing.
ATTRIBUTES = ".gitattributes"


@dataclass(frozen=True, slots=True)
class Attributes:
    """Which governed files `.gitattributes` sends to this driver, and which it does not (RK270).

    A driver is two writes and RK266 read back one. `.gitattributes` sends git to the driver by
    name; :data:`DRIVER_KEY` says what that name runs. Either alone is a repository where
    nothing happens — the attribute without the config falls back to a textual merge, the
    config without the attribute is never asked — so a check that answers about one of them is
    answering truthfully and not answering the question.

    Kept apart from :class:`Driver` rather than folded into it: this is a committed file and
    that is a per-checkout config, they go missing for different reasons and are repaired by
    different writes, and one dataclass spanning both would have to say which file each of its
    fields was about.
    """

    path: Path
    #: One line per governed file — what the root `.gitattributes` would have to carry.
    wanted: tuple[str, ...]
    #: Those of :attr:`wanted` the root file already carries. `register`'s view, and only that:
    #: where to *put* a line is a decision about this file, and it stays one (RK273).
    present: tuple[str, ...]
    #: Git's own answer per governed path — this driver's name, another's, or `unspecified`
    #: (RK273). The *fact* about what git sends where, which the root file cannot give.
    resolved: tuple[tuple[str, str], ...] = ()
    #: False when git could not be asked, the reading :class:`Driver` already has.
    known: bool = True

    @property
    def missing(self) -> tuple[str, ...]:
        """The lines `register` writes: wanted, not already in the root file, **not claimed**.

        The exclusion is RK274. git takes the *last* matching rule, so appending
        `<path> merge=roadkeep` under somebody's `<path> merge=theirs` wins over it — the
        overridden line is still in the file, inert, which keeps the letter of "every other
        line carried through untouched" and none of its meaning. Measured: `--check` reported
        `docs/CHANGELOG.md → theirs` and the repair it named silently flipped git's answer.

        Where git could not be asked there is no claim to see, so the root file decides alone —
        the same fallback :attr:`state` makes, and the direction that keeps `register` working
        on a machine with no git rather than writing nothing at all.
        """
        skip = {path for path, _ in self.claimed}
        return tuple(
            line
            for line, (path, _) in zip(self.wanted, self.resolved or self._unasked())
            if line not in self.present and path not in skip
        )

    def _unasked(self) -> tuple[tuple[str, str], ...]:
        """What :attr:`resolved` would say if nothing were known — every path undecided."""
        return tuple((line.split(f" merge={DRIVER}")[0], UNSPECIFIED) for line in self.wanted)

    @property
    def sent(self) -> tuple[str, ...]:
        """The governed paths git resolves to **this** driver."""
        return tuple(path for path, value in self.resolved if value == DRIVER)

    @property
    def unsent(self) -> tuple[str, ...]:
        """Governed paths git sends nowhere — undecided, and so the ones `register` settles.

        Claimed paths are **not** here (RK274). They are decided, just not for us: reporting a
        deliberate wiring as a thing still to do is what made the check fail forever on a
        repository that was finished, and it is the same argument RK273 settled when it chose
        to report another driver rather than argue with it.
        """
        claimed = {path for path, _ in self.claimed}
        return tuple(
            path for path, value in self.resolved if value != DRIVER and path not in claimed
        )

    @property
    def claimed(self) -> tuple[tuple[str, str], ...]:
        """Governed paths some **other** driver is named for — a deliberate act, so it is said.

        Invisible to the string comparison this used to be, which could only find its own name
        and read everything else as nothing set. A project that wired a different driver for one
        file did so on purpose, and a check that reports it as unwired is arguing with a choice.
        """
        return tuple(
            (path, value)
            for path, value in self.resolved
            if value not in (DRIVER, UNSPECIFIED, "set", "unset")
        )

    @property
    def state(self) -> str:
        """What git would do with the governed files: the four states, plus :data:`UNKNOWN`.

        Read off :attr:`resolved` and not off the root file, because "would git send this to
        the driver" is git's question — and answering it from one file reported three unsent
        while `check-attr` answered `roadkeep` from `.git/info/attributes` (RK273).

        :data:`CURRENT` is "nothing is undecided" and not "everything is ours" (RK274): a
        governed file another driver is named for is settled, so it does not hold the answer
        open. What it does do is stay in the reported line, because a count that dropped it
        would be a check quietly agreeing that the file is ours after all.
        """
        if not self.known:
            return UNKNOWN
        if not self.unsent:
            return CURRENT
        return ABSENT if not self.sent else PARTIAL

    @property
    def wired(self) -> bool:
        return self.state == CURRENT

    @property
    def routes_here(self) -> bool:
        """Whether any governed file reaches this driver — now, or once `register` has run.

        The one relation between the two halves (RK277). The config exists to answer *for the
        files the attributes route here*, so where none are and none will be, an unset driver
        is not a missing repair: it is the right state of a repository that chose something
        else. Measured on `docs/*.md merge=theirs`, where the check asked for a value no merge
        would ever reach.

        False in exactly two cases, both settled: every governed file is claimed by another
        driver, or the project declares none. An **unregistered** project is not one of them —
        its files are undecided, so they route here the moment the attribute half is repaired,
        and withdrawing the config repair there would answer about the repository as it is
        rather than the one the reader is in the middle of making. That is why this is not the
        `sent`-is-empty test it first looks like.

        Unknown reads as True: nothing was established, and not withdrawing a repair is the
        direction that cannot be wrong by silence.
        """
        return not self.known or bool(self.sent or self.unsent)


@dataclass(frozen=True, slots=True)
class Driver:
    """What this checkout's `git config` holds for the driver, against what it would hold now.

    RK255 made the stored command absolute and named the condition that ends it. This is the
    other half: naming an expiry is not observing one, and the value lives in `.git/config`,
    which nothing in this tool read — so the first evidence a driver rotted was git writing
    conflict markers into the file whose whole point is that its merge is decidable.
    """

    #: The command found under :data:`DRIVER_KEY`, empty when the key is not set.
    stored: str
    #: The command :func:`register` would write now, from :func:`~roadkeep.provenance.persisted`.
    wanted: str
    #: False when git could not be asked at all — the answer is absent, not negative, the same
    #: reading :class:`~roadkeep.history.HistoryUnavailable` gets everywhere else.
    known: bool = True

    @property
    def state(self) -> str:
        """One of the five above. Runnability is asked before equality, deliberately.

        A driver that differs from what this machine would write is not thereby broken: a
        checkout registered where the console script was on PATH keeps working after this
        package also grows a launcher. What git cannot execute is the defect; what merely
        moved is a fact, and answering the second question first would report both as one.
        """
        if not self.known:
            return UNKNOWN
        if not self.stored:
            return ABSENT
        if not _resolves(self.stored):
            return UNRUNNABLE
        return CURRENT if self.stored == self.wanted else MOVED

    @property
    def wired(self) -> bool:
        """Whether git has a driver here it can actually run — the one yes/no a caller needs."""
        return self.state in (CURRENT, MOVED)


@dataclass(frozen=True, slots=True)
class Wiring:
    """Both halves of the driver, and the questions only the two together answer (RK278).

    The halves are read apart because they go missing for different reasons and are repaired by
    different writes — that is RK270 and it stands. What kept going wrong is everything that
    needs *both*: RK272's per-half repair, RK277's "no governed file routes here", and the
    qualifier RK277 then shipped to one surface out of two. Three commits, three facts one
    caller knew and another did not, each repaired where it showed rather than where it came
    from.

    So the joining is a value, computed once and passed. A caller that has this cannot render
    half the answer, because there is no half to reach for.
    """

    attributes: Attributes
    driver: Driver

    @property
    def needs_attributes(self) -> bool:
        """Whether governed files are still undecided — the half `merge --register` repairs."""
        return self.attributes.state in (ABSENT, PARTIAL)

    @property
    def demands_driver(self) -> bool:
        """Whether a driver has to be configured: git has none it can run, **and** files reach it.

        The conjunction RK277 established. Where every governed file is claimed by another
        driver, or none is declared, an unset driver is not a missing repair but the settled
        state of a repository that chose otherwise — so this narrows what is *demanded* and
        never what is reported, which stays :attr:`driver` and is printed either way.
        """
        return self.driver.state in (ABSENT, UNRUNNABLE) and self.attributes.routes_here

    def repairs(self) -> list[str]:
        """The repair of each half that is actually broken, in the order reported (RK272).

        Measured before it was written: one `merge --register` named for both halves sent a
        reader into a loop — the verb writes the attribute lines and *prints* the config line,
        so the check that suggested it answered identically afterwards. Advice a reader can
        follow and land back on is worse than none, because it is the kind they stop reading.

        Two halves, two remedies, and neither is `register` running `git config` after all:
        that write is outside the files this tool was given (L2), and the half left to the
        reader is a decision rather than an oversight. `UNKNOWN` gets none — the question was
        never resolved, so naming a repair for it would be answering one nobody asked.
        """
        from roadkeep.provenance import invocation  # noqa: PLC0415 - RK260

        out = []
        if self.needs_attributes:
            # `UNKNOWN` is excluded by that property, not here: a question git could not
            # answer (RK273) names no repair, the same overreach the config half declines.
            out.append(f"{invocation()} merge --register")
        if self.demands_driver:
            out.append(config_command())
        return out

    def stated(self) -> str:
        """Both halves and what each needs, which is the whole of `--check` (RK270, RK277)."""
        from roadkeep.rendering import (  # noqa: PLC0415 - RK260
            _attributes_line,
            _wiring_line,
        )

        rows = [
            f"  attributes  {_attributes_line(self.attributes)}",
            f"  config      {_wiring_line(self)}",
        ]
        rows += [f"  fix         {one}" for one in self.repairs()]
        return chr(10).join(rows)

    def payload(self, config: Config) -> dict[str, object]:
        """The halves as fields, because they are two lines for a reason (RK275).

        The MCP surface reaches this as `merge_check` and passes `--json` on every call: a
        caller that got one string would have to parse which half is broken out of prose this
        tool is free to reword. `sound` is the exit code as a boolean, so nothing has to infer
        it from the absence of repairs.
        """
        from roadkeep.rendering import (  # noqa: PLC0415 - RK260
            _attributes_line,
            _wiring_line,
        )

        return {
            "attributes": {
                "state": self.attributes.state,
                "file": config.relative(self.attributes.path),
                "reported": _attributes_line(self.attributes),
                "routes_here": self.attributes.routes_here,
            },
            "driver": {"state": self.driver.state, "reported": _wiring_line(self)},
            "sound": self.sound,
            "fix": self.repairs(),
        }

    @property
    def sound(self) -> bool:
        """Whether git would run this driver over everything routed to it."""
        return not (self.needs_attributes or self.demands_driver)


def wiring(config: Config) -> Wiring:
    """Read both halves of the driver's wiring in one call — the only way they are read."""
    return Wiring(attributes=attributed(config), driver=registered(config))


@dataclass(frozen=True, slots=True)
class Registration:
    """What `merge --register` wrote: the attribute lines, and the config it needs."""

    attributes: Path
    added: tuple[str, ...]
    #: Already present, so not written again — re-running is not an accumulating file.
    present: tuple[str, ...]
    #: `git config merge.roadkeep.driver <…>`, as it must be set. Printed and not run: a
    #: driver command is a path into somebody's checkout, and running `git config` for them
    #: would be this tool writing outside the files it was given (L2).
    command: str
    #: What would stop that command resolving later (RK255) — the half of the answer a value
    #: this tool prints once and git executes months afterwards cannot leave to the reader.
    invalidated_by: str = ""
    #: What `git config` holds **now** (RK266), read after the attribute lines were written:
    #: the re-run that reports three lines already there is exactly the one where the config
    #: is the half that moved, so the answer that says nothing changed must not be the whole
    #: Both halves as they stand **now** (RK266, RK278), read after the attribute lines were
    #: written: the re-run that reports three lines already there is exactly the one where the
    #: config is the half that moved, so an answer saying nothing changed must not be the whole
    #: answer — and the report needs the attribute verdict too, or it names a driver the check
    #: has stopped asking for. `None` only where a caller constructed this without asking.
    wiring: Wiring | None = None
    #: Governed files left alone because another driver is named for them (RK274), with that
    #: driver's name. Reported and never written over: git takes the last matching rule, so a
    #: line added under theirs would win, and a repair that overrides what the check just
    #: reported is this tool arguing with a decision it can see.
    left_alone: tuple[tuple[str, str], ...] = ()


def merge(config: Config, role: str, base: str, ours: str, theirs: str) -> Merge:
    """Merge three versions of one governed file, or refuse with a reason.

    Refuses — text None — when any version carries a line this tool cannot reproduce (L3),
    when both sides changed the prose around the entries, when an id was spent or edited
    twice, or when the result is a file the gate would refuse.
    """
    schema = config.schema_for(role)
    versions = {
        "the ancestor": Document.parse(base, schema),
        OURS: Document.parse(ours, schema),
        THEIRS: Document.parse(theirs, schema),
    }
    for name, document in versions.items():
        if document.non_canonical:
            named = ", ".join(e.task.id for e in document.non_canonical)
            return Merge(role, None, reason=_unreadable(name, named))
    ancestor, mine, yours = versions["the ancestor"], versions[OURS], versions[THEIRS]
    if role in PROSE_ROLES:
        return _merge_prose(config, role, ancestor, mine, yours)

    decided, doubled, contested, withdrawn = _decide(ancestor, mine, yours)
    if doubled or contested or withdrawn:
        return Merge(
            role,
            None,
            doubled=doubled,
            contested=contested,
            withdrawn=withdrawn,
            reason=_spent(doubled, contested, withdrawn),
        )

    frame, source = _frame(ancestor, mine, yours)
    if frame is None:
        return Merge(role, None, reason=_both_sides_moved_the_prose())

    took = tuple(
        task_id
        for task_id, entry in decided.items()
        if entry is not None and _raw(frame, task_id) != entry.raw
    )
    removed = tuple(
        task_id for task_id, entry in decided.items() if entry is None and _raw(frame, task_id)
    )
    result = _materialize(frame, decided, where=config.relative(config.path(role)))
    findings = _introduced(config, role, result, *versions.values())
    if findings:
        return Merge(role, None, took=took, removed=removed, reason=_refused(findings))
    return Merge(
        role,
        result.render(),
        took=took,
        removed=removed,
        reason="" if source is None else f"prose taken from {source}",
    )


def markers(ours: str, theirs: str, *, width: int = MARKER) -> str:
    """The whole file, between conflict markers — what a refusal leaves in the worktree.

    Git's own fallback, written by this driver rather than left to it: once the driver runs,
    git has handed the merge over, and a non-zero exit with an untouched `%A` would leave the
    reviewer a file that looks like one side won.
    """
    mark = "<" * width, "=" * width, ">" * width
    return (
        f"{mark[0]} {OURS}\n{_terminated(ours)}{mark[1]}\n{_terminated(theirs)}"
        f"{mark[2]} {THEIRS}\n"
    )


def role_of(config: Config, path: str | Path) -> str | None:
    """Which governed file this pathname is, or None — the driver's one lookup.

    Compared as resolved paths, because git hands the driver `%P` as the path *in the
    repository* and the command may be run from anywhere inside it.
    """
    target = (config.root / Path(path)).resolve()
    for role in config.paths:
        if config.path(role).resolve() == target:
            return role
    return None


def register(config: Config) -> Registration:
    """Write one `.gitattributes` line per governed file, and name the config it needs.

    Additive and idempotent: a line already there is reported and not written twice, and
    every other line in the file is carried through untouched — it is the repository's file
    and this command owns three lines in it, the same contract `install` keeps (RK100).

    The driver command is :func:`~roadkeep.provenance.persisted` and never the console script
    literal (RK255). What is named here is stored in `.git/config` and **executed by git**
    when a governed file conflicts, so a name PATH happened to resolve in the terminal that
    ran `register` is a driver that fails at the one moment this file exists for — and git's
    fallback is conflict markers in the file whose whole point is that its merge is decidable.

    A governed file some **other** driver is named for is skipped and reported (RK274). Writing
    under it would win — git takes the last matching rule — so the promise that every other
    line is carried through untouched would be kept while the line stopped meaning anything.
    """
    before = attributed(config)
    if before.missing:
        body = "".join(f"{line}\n" for line in before.missing)
        current = before.path.read_text(encoding="utf-8") if before.path.is_file() else ""
        if current and not current.endswith("\n"):
            current += "\n"
        before.path.write_text(current + body, encoding="utf-8", newline="")
    stored = persisted()
    return Registration(
        attributes=before.path,
        added=before.missing,
        present=before.present,
        command=config_command(),
        invalidated_by=stored.invalidated_by,
        wiring=wiring(config),
        left_alone=before.claimed,
    )


def attributed(config: Config) -> Attributes:
    """Which governed files git sends to this driver, and what the root file carries (RK270/273).

    The read half of :func:`register`, which is why that function is written on top of it: two
    computations of "the line this role wants" would be the way the check and the write drift
    apart, and a check that agreed with nothing but itself is worse than no check.

    Two questions, deliberately, because they have two answers. What the root `.gitattributes`
    holds decides what `register` writes — a decision about one file, and one this tool owns
    three lines of. What git *resolves* decides whether a merge reaches the driver at all, and
    that is asked of git (RK273): the attribute may be set in a subdirectory, in
    `.git/info/attributes`, or in `core.attributesFile`, none of which the root file mentions.
    """
    # Imported here and not at module level (RK260), the reason :func:`registered` gives: the
    # driver runs on git's merge path and `history` reaches `backlog` and `sections`.
    from roadkeep.history import HistoryUnavailable, check_attr  # noqa: PLC0415

    path = config.root / ATTRIBUTES
    existing = _attribute_lines(path)
    paths = tuple(config.relative(config.path(role)) for role in config.paths)
    wanted = tuple(f"{name} merge={DRIVER}" for name in paths)
    try:
        answered = check_attr(config.root, "merge", paths)
        known = True
    except HistoryUnavailable:
        answered, known = {}, False
    return Attributes(
        path=path,
        wanted=wanted,
        present=tuple(line for line in wanted if line in existing),
        resolved=tuple((name, answered.get(name, UNSPECIFIED)) for name in paths),
        known=known,
    )


def config_command() -> str:
    """The `git config …` line that wires the config half — the repair, spelled once (RK272).

    Composed here rather than at the two call sites, because `register` prints it as what to do
    next and `merge --check` prints it as what to do *now*: two spellings would be two repairs,
    and the one the check names is the one that has to work.

    Never run, in either. Setting somebody's git config is a write outside the files this tool
    was given (L2) — the half that is not written is not an oversight, and RK272 is about the
    check naming that half accurately rather than about closing it.
    """
    return f'git config {DRIVER_KEY} "{driver_value(persisted().command)}"'


def driver_value(command: str) -> str:
    """The `.git/config` value for a driver reached by `command` — git's four placeholders.

    One spelling, read by :func:`register` when it composes the line and by :func:`registered`
    when it compares what a checkout actually holds: two spellings would make every registered
    driver read as :data:`MOVED` the day one of them gained a placeholder.
    """
    return f"{command} merge %O %A %B --path %P"


def registered(config: Config) -> Driver:
    """Read this checkout's driver back out of `git config` (RK266).

    A read and never a write: setting somebody's git config is outside the files this tool was
    given (L2), which is why `register` prints that line rather than running it — and it is the
    same reason nothing had read it back until now.

    `--default ""` and not a bare `--get`, because git exits 1 for a key that is not set and
    exits 1 for a repository that is not there, and the two are a wired-nothing and a
    question-that-could-not-be-asked. A git too old for `--default` answers :data:`UNKNOWN`,
    which is the honest reading of a tool that could not tell us either way.
    """
    # Imported here and not at module level (RK260): the driver itself is on git's merge path
    # and every governed write reaches this module, while `history` pulls in `backlog` and
    # `sections` — modules a merge never asks anything of.
    from roadkeep.history import HistoryUnavailable, _run as _git  # noqa: PLC0415

    wanted = driver_value(persisted().command)
    try:
        stored = _git(config.root, "config", "--default", "", "--get", DRIVER_KEY).strip()
    except HistoryUnavailable:
        return Driver(stored="", wanted=wanted, known=False)
    return Driver(stored=stored, wanted=wanted)


def _resolves(command: str) -> bool:
    """Whether the thing a stored driver command names is still on this machine.

    Asked of the file and never by running it: a driver is invoked by git with three paths and
    a `--path`, and this tool executing somebody's recorded command to find out whether it
    executes is a side effect nobody asked for.

    `python <script>` is the launcher case, and there the interpreter is the part that stays
    while the script is the part a plugin update moves — so both halves are asked about, which
    is exactly the failure :func:`~roadkeep.provenance.persisted` names as the expiry.
    """
    try:
        argv = shlex.split(command)
    except ValueError:  # an unbalanced quote is a value no shell would run either
        return False
    if not argv:
        return False
    head = argv[0]
    if not Path(head).is_file() and not shutil.which(head):
        return False
    if len(argv) > 1 and Path(head).stem.startswith("python") and argv[1].endswith(".py"):
        return Path(argv[1]).is_file()
    return True


# -- the decision ------------------------------------------------------------


def _decide(
    ancestor: Document, mine: Document, yours: Document
) -> tuple[dict[str, Entry | None], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """One answer per id: the line it ends up with, None for gone, or a conflict.

    Read off the raw lines and not off the parsed fields, because "did this side change it"
    is a question about what was written — two spellings of one task are two lines, and the
    round-trip guarantee above is what makes comparing them exact.
    """
    decided: dict[str, Entry | None] = {}
    doubled: list[str] = []
    contested: list[str] = []
    withdrawn: list[str] = []
    was, here, there = ancestor.by_id(), mine.by_id(), yours.by_id()
    for task_id in dict.fromkeys((*was, *here, *there)):
        before, ours, theirs = was.get(task_id), here.get(task_id), there.get(task_id)
        if _raw(mine, task_id) == _raw(yours, task_id):
            decided[task_id] = ours
        elif _raw(mine, task_id) == _raw(ancestor, task_id):
            decided[task_id] = theirs
        elif _raw(yours, task_id) == _raw(ancestor, task_id):
            decided[task_id] = ours
        elif before is None:
            doubled.append(task_id)
        elif ours is None or theirs is None:
            # One side's line is *gone* (RK482) — shipped, retired, deferred out — and the
            # other edited it. Kept apart from `contested` for RK120's reason: that clause
            # asks a reviewer to choose a sentence, and nobody wrote a second one here. The
            # decision is whether the removal stands and where the edit goes.
            withdrawn.append(task_id)
        else:
            contested.append(task_id)
    return decided, tuple(doubled), tuple(contested), tuple(withdrawn)


def _merge_prose(
    config: Config, role: str, ancestor: Document, mine: Document, yours: Document
) -> Merge:
    """The same merge, over §sections instead of task lines (RK483).

    A rationale file has no task lines at all, so `_skeleton` was the whole file and `_frame`
    compared three whole files: any two differing sides refused. `ship` drops a section and
    one task is one commit, so two branches that shipped anything landed there — measured on
    a scaffold as two disjoint drops answering *both branches changed the prose*.

    The address is what makes it decidable, and this file has one: a §section is keyed by the
    anchor `section drop` already takes, so *which section changed* is a question about
    anchors and never about line numbers. Every rule above is reused with that key.

    **L4 is not weakened.** Taking a whole section from one side is the decision the roadmap
    makes; merging *inside* one is prose, so a body differing on both sides is `contested`
    and stays the reviewer's. What is outside the sections is the frame, and both sides
    moving that still refuses.
    """
    decided, doubled, contested, withdrawn = _decide_sections(ancestor, mine, yours)
    if doubled or contested or withdrawn:
        return Merge(
            role,
            None,
            doubled=doubled,
            contested=contested,
            withdrawn=withdrawn,
            reason=_spent(doubled, contested, withdrawn),
        )
    frame, source, other = _prose_frame(ancestor, mine, yours)
    if frame is None:
        return Merge(role, None, reason=_both_sides_moved_the_prose())
    held = _sections_of(frame)
    took = tuple(
        anchor for anchor, lines in decided.items() if lines is not None and held.get(anchor) != lines
    )
    removed = tuple(anchor for anchor, lines in decided.items() if lines is None and anchor in held)
    result = Document.parse(_written(frame, other, decided), config.schema_for(role))
    findings = _introduced(config, role, result, ancestor, mine, yours)
    if findings:
        return Merge(role, None, took=took, removed=removed, reason=_refused(findings))
    return Merge(
        role,
        result.render(),
        took=took,
        removed=removed,
        reason="" if source is None else f"prose taken from {source}",
    )


def _sections_of(document: Document) -> dict[str, tuple[str, ...]]:
    """Every §section's raw lines, keyed by anchor — the unit a prose merge decides.

    **Trailing blanks are off the comparison.** `Section.last` runs to whatever follows, so
    dropping the section *below* one extends its region to the end of the file — and the
    first run of this read reported the section nobody touched as `withdrawn`. The blank is
    a separator between sections and not a fact about either, so it is normalised the way
    `_skeleton` normalises line endings, and for the same reason: refusing over it refuses
    every merge.
    """
    from roadkeep.sections import anchored  # noqa: PLC0415 - RK260, the prose path only

    found = {}
    for section in anchored(document):
        lines = list(document.lines[section.first - 1 : section.last])
        while lines and not lines[-1].strip():
            lines.pop()
        found[section.anchor] = tuple(lines)
    return found


def _decide_sections(
    ancestor: Document, mine: Document, yours: Document
) -> tuple[dict[str, tuple[str, ...] | None], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """`_decide`'s four-way rule with the anchor as the key and the region as the text."""
    decided: dict[str, tuple[str, ...] | None] = {}
    doubled: list[str] = []
    contested: list[str] = []
    withdrawn: list[str] = []
    was, here, there = _sections_of(ancestor), _sections_of(mine), _sections_of(yours)
    for anchor in dict.fromkeys((*was, *here, *there)):
        before, ours, theirs = was.get(anchor), here.get(anchor), there.get(anchor)
        if ours == theirs:
            decided[anchor] = ours
        elif ours == before:
            decided[anchor] = theirs
        elif theirs == before:
            decided[anchor] = ours
        elif before is None:
            doubled.append(anchor)
        elif ours is None or theirs is None:
            withdrawn.append(anchor)
        else:
            contested.append(anchor)
    return decided, tuple(doubled), tuple(contested), tuple(withdrawn)


def _prose_skeleton(document: Document) -> tuple[str, ...]:
    """The file with its §sections taken out — what `_skeleton` is for a roadmap."""
    from roadkeep.sections import anchored  # noqa: PLC0415 - RK260, the prose path only

    inside: set[int] = set()
    for section in anchored(document):
        inside |= set(range(section.first, section.last + 1))
    return tuple(
        line.rstrip("\r\n")
        for number, line in enumerate(document.lines, start=1)
        if number not in inside
    )


def _prose_frame(
    ancestor: Document, mine: Document, yours: Document
) -> tuple[Document | None, str | None, Document | None]:
    """Whose frame the merged file keeps, and the other side, whose new sections still land."""
    was, here, there = (
        _prose_skeleton(ancestor),
        _prose_skeleton(mine),
        _prose_skeleton(yours),
    )
    if there == was or here == there:
        return mine, None, yours
    if here == was:
        return yours, THEIRS, mine
    return None, None, None


def _written(
    frame: Document, other: Document | None, decided: dict[str, tuple[str, ...] | None]
) -> str:
    """The frame with every decided section written into it, and the other side's new ones.

    A walk and not a head/tail split, because a `## Block` heading sits *between* sections in
    every file organised by blocks, and slicing around the first and last would swallow it.

    A section the frame never had is placed after the anchor that preceded it on its own
    side, so the order that side chose survives. The ones nothing of the frame's precedes go
    after the last section rather than at the end of the file — and the ones that follow
    nothing go before the first. Written down because the first cut of this dropped the
    trailing case on the floor while reporting it as `took`, which is the silent loss this
    whole driver exists to refuse.
    """
    from roadkeep.sections import anchored  # noqa: PLC0415 - RK260, the prose path only

    held = _sections_of(frame)
    leading, before, trailing = _arriving(frame, other, decided)
    spans = sorted((one.first, one.last, one.anchor) for one in anchored(frame))
    blank = frame.newline
    # How many blank lines the frame kept after each section, so an unchanged file comes
    # back byte-identical (L3). `_sections_of` takes them off to compare, and assuming one
    # back added a line at EOF on every corpus this was run against.
    pad = {
        anchor: last - (first - 1) - len(held.get(anchor, ()))
        for first, last, anchor in spans
    }
    out: list[str] = []
    at = 0
    for index, (first, last, anchor) in enumerate(spans):
        out.extend(frame.lines[at : first - 1])
        if index == 0:
            out.extend(_spaced(leading, blank))
        out.extend(_spaced(before.get(anchor, []), blank))
        lines = decided.get(anchor, held.get(anchor))
        if lines is not None:
            out.extend(lines)
            out.extend([blank] * pad.get(anchor, 1))
        if index == len(spans) - 1:
            out.extend(_spaced(trailing, blank))
        at = last
    if not spans:  # a frame with no section at all: everything arriving goes after the prose
        out.extend(frame.lines)
        out.extend(_spaced([*leading, *before.values(), *trailing], blank))
        return "".join(out)
    out.extend(frame.lines[at:])
    return "".join(out)


def _spaced(blocks: list[list[str]], blank: str) -> list[str]:
    """Section blocks with one blank line after each — the separator `_sections_of` took off."""
    out: list[str] = []
    for block in blocks:
        out.extend(block)
        out.append(blank)
    return out


def _arriving(
    frame: Document, other: Document | None, decided: dict[str, tuple[str, ...] | None]
) -> tuple[list[list[str]], dict[str, list[list[str]]], list[list[str]]]:
    """New sections as (before the first, before a named anchor, after the last).

    Three buckets rather than one, because a new section can precede every anchor the frame
    has, follow every one, or sit between two — and a single map keyed by "what comes after"
    has no key for the last case.
    """
    from roadkeep.sections import anchored  # noqa: PLC0415 - RK260, the prose path only

    leading: list[list[str]] = []
    before: dict[str, list[list[str]]] = {}
    trailing: list[list[str]] = []
    if other is None:
        return leading, before, trailing
    held = _sections_of(frame)
    order = [one.anchor for one in anchored(other)]
    for index, anchor in enumerate(order):
        lines = decided.get(anchor)
        if anchor in held or lines is None:
            continue
        following = next((one for one in order[index + 1 :] if one in held), None)
        preceding = next((one for one in reversed(order[:index]) if one in held), None)
        if following is not None:
            before.setdefault(following, []).append(list(lines))
        elif preceding is not None:
            trailing.append(list(lines))
        else:
            leading.append(list(lines))
    return leading, before, trailing


def _frame(
    ancestor: Document, mine: Document, yours: Document
) -> tuple[Document | None, str | None]:
    """Whose headings and prose the merged file keeps, and None when both sides moved them.

    The skeleton is every line that is not a task line, which is exactly the part of a
    governed file this tool does not write (L4). One side changing it is a decision the
    merge can carry; both changing it differently is prose, and prose is the reviewer's.
    """
    was, here, there = _skeleton(ancestor), _skeleton(mine), _skeleton(yours)
    if there == was or here == there:
        return mine, None
    if here == was:
        return yours, THEIRS
    return None, None


def _skeleton(document: Document) -> tuple[str, ...]:
    """The file with its task lines taken out, endings normalised.

    Normalised because a branch checked out on Windows and one on Linux differ in every
    line, and refusing a merge over that is refusing every merge.
    """
    entries = {entry.lineno for entry in document.entries}
    return tuple(
        line.rstrip("\r\n")
        for number, line in enumerate(document.lines, start=1)
        if number not in entries
    )


def _materialize(
    frame: Document, decided: dict[str, Entry | None], *, where: str = ""
) -> Document:
    """Write the decided lines into the frame: replace, remove, then place what is new.

    In that order and re-located by id at every step, because each edit reparses and a line
    number held across one is a line number that has already moved — the care every mutator
    in :mod:`roadkeep.kernel.document` takes, for the same reason.

    ``where`` is the file being merged, which is what makes a refusal here readable (RK361):
    this is the fourth caller of `place` and it was the one passing neither the path nor an
    id, so a merged line the schema refuses reported a rule and a number about a file the
    caller is holding two versions of.
    """
    result = frame
    for task_id, entry in decided.items():
        held = result.by_id().get(task_id)
        if entry is not None and held is not None and held.raw != entry.raw:
            result = result.replace_line(held.index, entry.raw)
    for task_id, entry in decided.items():
        held = result.by_id().get(task_id)
        if entry is None and held is not None:
            result = remove_entry(result, held)
    for task_id, entry in decided.items():
        if entry is not None and task_id not in result.by_id():
            # `place` re-renders from the task, which is the same bytes: every version was
            # held to the round-trip above, so nothing arrives here that would come back
            # spelled differently — and the blank-line and block rules are `add`'s, once.
            # True of the *rendering* and not of the schema, which is why the refusal below
            # is reachable at all: a dep this tool re-derives during the merge grows the line
            # by the two characters RK348 was filed about.
            try:
                result = place(result, entry.task, where=where).document
            except SchemaError as error:
                raise _naming_the_merged_line(task_id, where, error) from None
    return result


def _naming_the_merged_line(task_id: str, where: str, error: SchemaError) -> SchemaError:
    """The same refusal, told which id and which file it is about (RK361).

    RK348's rule, at the one door that did not keep it: a length is reported against a line
    somebody can find, never as a bare number. Here the number is about a line neither side
    typed in this state — it is one branch's line landing in the other's file — so a caller
    reading it has two versions open and nothing saying which one the count belongs to.

    Not `anchors`, which is the clause the other three doors carry (RK349): this caller is
    inside git's merge driver rather than at a prompt, and a command they cannot run until
    the merge is over is noise on a refusal that already needs reading twice.
    """
    at = f" merging {where}" if where else " in the merge"
    said = f" — on {task_id}'s line,{at}"
    return type(error)(
        tuple(replace(one, message=f"{one.message}{said}") for one in error.violations)
    )


def _raw(document: Document, task_id: str) -> str | None:
    entry = document.by_id().get(task_id)
    return entry.raw if entry is not None else None


def _attribute_lines(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines()}


def _terminated(text: str) -> str:
    return text if text.endswith("\n") or not text else text + "\n"


# -- the reasons -------------------------------------------------------------


def _unreadable(version: str, named: str) -> str:
    return (
        f"{version} carries {named} written differently from what the schema renders: a "
        f"merge of lines this tool cannot reproduce would normalise work nobody reviewed"
    )


def _spent(
    doubled: tuple[str, ...], contested: tuple[str, ...], withdrawn: tuple[str, ...] = ()
) -> str:
    out = []
    if doubled:
        out.append(
            f"both branches created {', '.join(doubled)}: one address, two tasks — "
            f"`{invocation()} renumber <id>` on one side, then merge again"
        )
    if contested:
        out.append(
            f"both branches rewrote {', '.join(contested)}: one line, two sentences — "
            f"the wording is the reviewer's and this driver does not pick one"
        )
    if withdrawn:
        # Not "rewrote" (RK482): one side's line is gone and the other edited it, so what is
        # asked for is not a sentence. Taking the removal would delete the edit silently,
        # which is the ground RK97 refuses to pick on for `doubled`.
        out.append(
            f"one branch removed {', '.join(withdrawn)} and the other edited it: a line that "
            f"shipped, retired or deferred against an edit to the same line — decide whether "
            f"the removal stands, then where that edit goes"
        )
    return "; ".join(out)


def _both_sides_moved_the_prose() -> str:
    return (
        "both branches changed the headings or the prose around the entries, and this "
        "tool does not merge prose (L4)"
    )


def _introduced(
    config: Config, role: str, result: Document, *inputs: Document
) -> list:
    """The findings this merge composed, which are the ones it may refuse over (RK1352).

    The driver gated its output against `within` and asked nothing about its inputs, so a
    defect in the ancestor blocked every merge of that file until somebody cleaned it — and
    cleaning it is a different task from the merge. Reproduced: a base whose `RK9` carries a
    283-character `why`, one branch adding `RK1`, the other adding `RK2`, neither touching
    `RK9` — refused, naming `RK9` to somebody mid-merge who did not choose that work.

    Keyed by `(code, id)` and never by line: a merge moves lines by construction, so a
    position is the one part of a finding that cannot survive the comparison. What that
    trades away is the case where a side makes an already-bad field worse — the pair is
    unchanged, so the driver lets it through and `lint` refuses it, which is the right
    division: this is a driver, and the gate is the gate (RK120).

    The gate stays for what it is for — a merge that *creates* a defect is one nobody chose
    and nobody would find, the file having been written by a program.
    """
    from roadkeep.linting import resolving, within  # noqa: PLC0415 - the module's own edge

    def asked(document: Document) -> list:
        # Both halves (RK1353): what one file answers, and what only the backlog can. A dep
        # naming a line the other side removed exists in no version and in the merged file
        # alone, which is the one class a merge is uniquely able to write — and the half
        # `within` runs cannot be asked about it.
        return [*within(config, role, document), *resolving(config, role, document)]

    held = {(finding.code, finding.id) for document in inputs for finding in asked(document)}
    return [finding for finding in asked(result) if (finding.code, finding.id) not in held]


def _refused(findings: list) -> str:
    named = "; ".join(str(finding) for finding in findings[:3])
    more = f" (+{len(findings) - 3} more)" if len(findings) > 3 else ""
    return f"the merged file is one the gate refuses: {named}{more}"
