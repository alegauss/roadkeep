"""Writing the line, so the limit is met before the sentence exists (RK5).

This is the module the whole tool is for. Everything before it proves the format can
be read; `add` is where the format starts being *enforced at the moment of writing*
(L1), and the difference is not convenience:

* A linter reports after the prose exists. The tokens are already spent, and the
  author is being asked to delete work they just justified — which is why the ninety-two
  over-length lines that motivated this tool were written by authors who knew the rule.
* `add` refuses an over-length ``why`` **before** a second sentence is composed to fill
  it, and the refusal names the limit, the actual length, and the file the remainder
  belongs in. *The saving is the analysis, not the characters:* the author stops asking
  "is this too long, what would I cut?" and starts calling a command.

Three decisions that are the point of the module rather than details of it:

* **Nothing is written unless everything validates.** :func:`place` renders, inserts and
  re-reads in memory, and the file is touched only after the result round-trips (L3). A
  partial write to a governed file is the failure mode the tool exists to remove.
* **The pointer is derived, never asked for.** Under ``ref_scheme = "id"`` the anchor is
  the task's own id (RK27), so `add` supplies it; passing a different one is refused
  rather than honoured, because a pointer an author can choose is a pointer an author
  can get wrong.
* **The block must already be declared.** A heading is the only thing that declares a
  block (RK37), so `add` files a task under one and never creates one — a heading
  invented by a write puts the task where nothing looks for it.

* **A success that fails the gate is not a success.** Under ``ref_scheme = "id"`` the
  pointer above is derived on every line and `lint` requires it resolve, so `add` alone
  left a tree the gate refused and said nothing about it (RK93). `--section` writes the
  rationale in the *same* transaction — both files validated, then both saved — and
  without it :attr:`Insertion.needs` names the anchor that resolves to nothing. The
  obligation is stated by the command that created it, never discovered from the backstop.

What it deliberately does not do: write prose (L4 — it has no opinion on the sentence,
only its length and count, and `--section` carries the author's paragraph to
:mod:`roadkeep.sections` without composing a word of it), derive the dep markers (RK8
does that on every write, and until then a marker is passed through exactly as typed), or
fix a file that has drifted.

:func:`set_status` (RK7) lives here for the same reason `add` does — it is a write to the
roadmap — and adds exactly one rule: the marker has one home, so a sibling file carrying
one for the same id is refused instead of reconciled.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

from roadkeep import claiming, sections
from roadkeep.backlog import Backlog, NotOpen
from roadkeep.claiming import Followed
from roadkeep.config import PROSE_ROLES, ROLES, Config
from roadkeep.document import (
    Document,
    Entry,
    Heading,
    RepeatedHeading,
    UnknownBlock,
    counted,
    save_all,
    blank,
    read_deps,
)
from roadkeep.ids import next_id, scan
from roadkeep.markers import derive, refresh
from roadkeep.schema import SchemaError, Task
from roadkeep.sections import Section

#: The rationale a line arrives with: the heading, and prose that is either the string itself
#: or a **reader** for it (RK381). A reader is called once, at the last moment it can be — see
#: :func:`_with_section` — so a caller whose paragraph comes off a pipe does not spend it on a
#: call the line's own fields were going to refuse.
Rationale = tuple[str, "str | Callable[[], str]"]


class IdInUse(ValueError):
    """An id is the one decision that cannot be taken back once it is committed."""

    def __init__(self, task_id: str, where: str, lineno: int) -> None:
        self.task_id = task_id
        self.where = where
        self.lineno = lineno
        super().__init__(
            f"{task_id} already occurs at {where}:{lineno}: an id is never reused, "
            f"not even one that was retired — omit --id and it is derived"
        )


class StatusElsewhere(ValueError):
    """A marker in a second file is a status two files can come to disagree about."""

    def __init__(
        self, task_id: str, role: str, where: str, lineno: int, marker: str
    ) -> None:
        self.task_id = task_id
        self.role = role
        super().__init__(
            f"{task_id} already carries {marker} in the {role} at {where}:{lineno}: "
            f"status lives in exactly one file, because two files that both express it "
            f"will eventually express different ones and nothing says which is right"
        )


class DuplicateId(ValueError):
    """Two lines for one id are two statuses for one task, in one file."""

    def __init__(self, task_id: str, where: str, linenos: Sequence[int]) -> None:
        self.task_id = task_id
        self.linenos = tuple(linenos)
        lines = ", ".join(str(number) for number in self.linenos)
        super().__init__(
            f"{task_id} appears at {where}:{lines}: one line per task, and two lines "
            f"carry two statuses — `lint` reports this, and it is fixed by hand"
        )


class DerivedPointer(ValueError):
    """Under the id scheme there is no anchor to choose (RK27)."""

    def __init__(self, task_id: str, given: str) -> None:
        super().__init__(
            f"the pointer is derived from the id (§{task_id}), so --ref {given!r} "
            f"names a section chosen by hand: drop it, or set ref_scheme = \"outline\""
        )


class NoAnchor(ValueError):
    """A rationale asked for on a line that carries no pointer to reach it by (RK93)."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(
            f"{task_id} carries no pointer, so a section written now is one nothing "
            f"names: pass --ref to give the line an anchor, or write the prose after"
        )


class NoProseFile(ValueError):
    """A rationale asked for by a project that declares nowhere to put one (RK93).

    Every prose role and not one of them (RK230): naming `improvements` was the refusal a
    project declaring `strategy` alone got for a section its own file would have held, and
    "declare it under [files]" then asked for the second prose file it had no use for.
    """

    def __init__(self, task_id: str, role: str = "") -> None:
        self.task_id = task_id
        named = repr(role) if role else " or ".join(repr(r) for r in PROSE_ROLES)
        super().__init__(
            f"this project declares no {named} file, so {task_id} has nowhere to "
            f"carry a section: declare one under [files], or drop --section"
        )


@dataclass(frozen=True, slots=True)
class Insertion:
    """The line that was written, and the document that now holds it.

    Plus, for the door that takes prose (RK93), the rationale written in the same
    transaction — or, when it did not, the anchor the line points at that nothing
    answers yet, which is what makes the follow-up the write's own report instead of
    the gate's.
    """

    document: Document
    entry: Entry
    #: The prose file as this write leaves it, and the section it gained. Both None
    #: unless `--section` was passed: `place` inserts one line into one file.
    prose: Document | None = None
    section: Section | None = None
    #: The anchor this line points at that no declared prose file answers. Set only
    #: when no section was written, because then there is nothing left to report.
    needs: str | None = None
    #: Which role that follow-up would write into (RK197). A project declaring several has
    #: more than one place a section could go, so the command offered names the one it means
    #: — otherwise the author is handed `section add`'s default and a file that refuses it.
    needs_role: str | None = None

    @property
    def rendered(self) -> str:
        return self.entry.raw

    @property
    def lineno(self) -> int:
        return self.entry.lineno

    def save(self) -> None:
        """Write the files. Nothing here can fail on the format — that was decided."""
        save_all(self.document, self.prose)


def compose(
    config: Config,
    *,
    task_id: str,
    block: str,
    symptom: str,
    why: str,
    status: str | None = None,
    deps: Sequence[str] = (),
    ref: str | None = None,
) -> Task:
    """The fields, as a :class:`Task`. Fills in what is derivable; validates nothing.

    Validation stays in :func:`place` so that every violation is reported at once — a
    constructor that raises can only ever name the first thing wrong with a line.
    """
    schema = config.schema
    if schema.ref_scheme == "id":
        if ref is not None and ref != task_id:
            raise DerivedPointer(task_id, ref)
        ref = task_id
    return Task(
        id=task_id,
        # The default is the first marker this project declares, not a hardcoded 📋:
        # the marker set is configuration (L6), so the default has to come from it.
        status=status or schema.markers[0],
        block=block,
        symptom=symptom,
        why=why,
        deps=read_deps(", ".join(deps), schema) if deps else (),
        ref=ref,
    )


def place(
    document: Document,
    task: Task,
    *,
    carrying: Sequence[str] = (),
    where: str = "",
    config: Config | None = None,
    role: str = "",
) -> Insertion:
    """Validate, render, insert — in memory, and refuse before any of it.

    Raises :class:`~roadkeep.schema.SchemaError` with every violation,
    :class:`UnknownBlock` when no heading declares the block,
    :class:`~roadkeep.document.RepeatedHeading` when two do (RK391), and
    :class:`~roadkeep.document.RoundTripError` when either the file already carries a
    line the schema would rewrite or the new line does not read back as it was written.

    ``carrying`` is the lines an entry owns **beyond** the one the schema renders (RK157),
    and only a *move* passes it: re-placing a wrapped ledger entry under another heading has
    to carry its continuation with it, since the schema renders one line and the rest is
    prose no task holds. A newly composed line carries nothing, which is every other caller.

    ``role`` is **which governed file this is**, and it is the one argument to reach for
    (RK412). The refusal needs that file twice over — as a path, so it can be named, and as
    a role, so it can name `block add --organise <role>` where the file declares no heading
    at all (RK405) — and until this those were two arguments, the second spelled out at five
    call sites and derivable from the first at none of them. Nothing held them level: a door
    passing the path and forgetting the role printed the bare `block add`, which on the file
    the sentence is about is one more refusal, and no test and no gate can see the difference
    because it is a sentence. `defer` was in exactly that state. One argument, derived
    together, and the one that can be forgotten stops existing.

    ``where`` is the same file as a path, for the caller that has no role to give: `merge`
    re-places entries into a document it composed itself, and a role would be a claim about a
    file on disk it is not writing. Rendered by the caller in the way `sections` already
    renders its own (RK181, RK257), because this function takes a :class:`Document` and
    `config.relative` is out of its reach. Passing both is refused, being two answers to one
    question — and `role` without a :class:`~roadkeep.config.Config` is refused for the same
    reason it is not a guess: there is nothing to resolve it against.

    ``config`` is what turns the refusal `ref.missing` into an address (RK349). RK312 wired
    that enrichment around `add`'s own call and left `defer` and `resume` — which reach this
    same `check` through their own doors — printing the bare rule, and an asymmetry is worse
    than the original gap: a caller who has met the good refusal once reads the bare one as
    *there is no answer here*. So it is made here, at the seam every line write passes,
    rather than at four call sites that would drift apart again. Omitted, the refusal is the
    schema's own, which is what a caller with no project to read anchors out of gets.
    """
    if role:
        if where:
            raise ValueError(
                "place takes the role or the path it resolves to, not both: they are two "
                "answers to one question and the role is the one that derives the other"
            )
        if config is None:
            raise ValueError(f"place(role={role!r}) needs a config to resolve it against")
        where = config.relative(config.path(role))
    try:
        document.schema.check(task)
    except SchemaError as error:
        # Around `check` rather than before it, so a line that is missing a pointer *and*
        # over on its `why` still hears both (RK312): the schema reports every violation at
        # once, and an early refusal here would trade that for the one sentence it improves.
        raise (
            error
            if config is None
            else sections.naming_the_anchor(config, task.block, error)
        ) from None
    declared = document.declaring(task.block)
    if not declared:
        raise UnknownBlock(
            task.block,
            sorted({h.label for h in document.headings if h.label}),
            where,
            word=document.schema.heading_word,
            # Which file the remedy has to start organising, where it declares no block at
            # all (RK405) — the same fact `where` is, which is why it is derived and not
            # asked for (RK412). Empty only for the caller that gave a path alone.
            organise=role,
        )
    if len(declared) > 1:
        # The ambiguity is not resolved by position (RK391) — see `RepeatedHeading`. Here
        # rather than at `add`, because this is the seam every line write passes and `ship`,
        # `record add` and `move` reach a repeated heading through their own doors.
        raise RepeatedHeading(
            task.block,
            [h.lineno for h in declared],
            where,
            word=document.schema.heading_word,
        )
    heading = declared[0]

    rendered = document.schema.render(task)
    index, payload = _placement(document, heading, rendered, tuple(carrying))
    updated = document
    for offset, raw in enumerate(payload):
        updated = updated.insert_line(index + offset, raw)
    # The new line is canonical by construction — and the guard is the point: a line
    # this tool wrote and cannot read back is exactly what must never reach the disk.
    updated.ensure_writable()

    lineno = index + payload.index(rendered) + 1
    entry = next(e for e in updated.entries if e.lineno == lineno)
    return Insertion(document=updated, entry=entry)


def remove_entry(document: Document, entry: Entry) -> Document:
    """Take the entry out, and the blank line the removal doubled. The inverse of `place`.

    A task line sits between blanks when it is the last one in its block, so removing it
    leaves a paragraph break the file never had. Both spellings round-trip, which is
    exactly why nothing downstream would catch it.

    The **whole** entry, which is the same fact `place` needed (RK157): a wrapped ledger
    entry's continuation lines are the removal's to take, and leaving them behind would file
    somebody's paragraph under whatever bullet the deletion left above them. Takes the entry
    rather than its index for exactly that reason — an index is the half of the answer that
    was wrong.

    Here rather than in one caller because a line now leaves the roadmap by four doors —
    three of them departures (RK6, RK32) and one of them reversible (RK91) — and a second
    copy of this rule is a second opinion about the shape of the file it leaves behind.
    """
    index = entry.index
    updated = document.remove_lines(index, entry.stop)
    lines = updated.lines
    if index > 0 and index < len(lines) and blank(lines[index - 1]) and blank(lines[index]):
        return updated.remove_line(index)
    if index >= len(lines) and index > 0 and blank(lines[index - 1]):
        # The block was last in the file: its trailing blank has nothing left to separate.
        return updated.remove_line(index - 1)
    return updated


def add(
    config: Config,
    *,
    block: str,
    symptom: str,
    why: str,
    status: str | None = None,
    deps: Sequence[str] = (),
    ref: str | None = None,
    task_id: str | None = None,
    family: str | None = None,
    section: Rationale | None = None,
) -> Insertion:
    """Insert one task into the roadmap and save it. The whole write path.

    The id is derived unless one is given, and a given id that occurs anywhere is
    refused (:class:`IdInUse`) — including in prose, because a number a document
    already mentions is a number two designs would share in the history.

    ``family`` picks which track the derived id counts in (RK74) and defaults to the first
    the project declares, which is the only answer for the projects that declare one. It
    is never inferred from the block: a track is not a block, and a tool that mapped one
    to the other would be holding an opinion about someone else's backlog.

    The dep annotations are derived here too (RK8), so `--dep RK1` renders `RK1 ✅` when
    RK1 has shipped and the author never types a marker. Only this line is derived: no
    existing line can name an id that did not exist a moment ago.

    **Both headings, not one** (RK380): the roadmap's is `place`'s refusal, and
    :func:`declaring` asks the same question of the ledger — the one the first `ship` in this
    block would otherwise ask at the end of the task instead of the start.

    ``section`` is the rationale as ``(title, body)``, and the reason this door takes
    prose at all (RK93). Under ``ref_scheme = "id"`` every line renders a pointer `lint`
    requires to resolve, so an `add` on its own could not leave a gate-clean tree and the
    author learned the follow-up from the backstop — the inversion L1 exists to prevent.
    Given, both files are validated and then both are written, so the line and the design
    it points at arrive together or neither does. Omitted, nothing is invented (L4):
    :attr:`Insertion.needs` carries the anchor that resolves to nothing, so the command
    that created the obligation is the one that states it.

    Its body may be a **reader** rather than a string, and the ordering below is the whole
    reason (RK381). Every refusal the *line* can raise — a spent id, a `why` three words
    over, an undeclared block, a rendered line past its limit — happens above
    :func:`_with_section`, and the docstring at the top of this module says why that is
    right. What it stopped short of is that a caller reading the paragraph off a pipe has
    already spent it by the time the refusal arrives, and a pipe does not rewind: measured
    against Turing, a `--why` 15 characters over cost a 184-word body a second time, to
    correct three words in a different argument. So the prose is not fetched until the line
    it belongs to has passed.
    """
    if task_id is None:
        task_id = next_id(config, family)
    else:
        refuse_reuse(config, task_id)
    task = compose(
        config,
        task_id=task_id,
        block=block,
        symptom=symptom,
        why=why,
        status=status,
        deps=deps,
        ref=ref,
    )
    # Both fields' breaches in one refusal, where the body is already in hand (RK426). A
    # call whose `why` is fifteen characters over and whose body is fifty words over used to
    # cost two full resubmissions, the second for a limit the first refusal had already
    # measured — and re-passing the prose is exactly what `--section-body-file` exists to
    # avoid, so the tool had conceded the cost and then charged it for a field it never read.
    #
    # **Only where the body is a string.** RK381's ordering is not relaxed: a body arriving
    # off a *pipe* is spent by reading it, and a pipe does not rewind, so for that one shape
    # the line still has to pass before the paragraph is fetched. A `str` costs nothing to
    # look at twice, which is the whole distinction and the reason it is drawn on the type.
    _refuse_together(config, task, section)
    insertion = place(
        config.document("roadmap"),
        derive(Backlog.load(config), task),
        role="roadmap",
        config=config,
    )
    # After the roadmap's own refusal and before the prose is read (RK380, RK381): a label
    # neither file declares is one mistake, and hearing it named against the file the line
    # was going into is the half that tells a typo from a block only half opened.
    declaring(config, block)
    if section is not None:
        insertion = _with_section(config, insertion, *section)
    elif insertion.entry.task.ref and (
        role := _unresolved(config, insertion.entry.task.ref)
    ):
        insertion = replace(
            insertion, needs=insertion.entry.task.ref, needs_role=role
        )
    insertion.save()
    return insertion


@dataclass(frozen=True, slots=True)
class Rereadable:
    """A body that can be fetched more than once, so it may be validated early (RK426).

    RK381 made the body a *reader* because a paragraph off a pipe is spent by reading it and
    a pipe does not rewind — so a `why` fifteen characters over cost a 184-word body a second
    time. That argument holds for one of the three sources and not the other two: a literal
    string and a path both cost nothing to look at twice.

    Collapsing all three into a bare lambda lost that, and with it the only distinction that
    decides whether both fields can be refused in one call. So the two cheap sources arrive
    wrapped and the pipe stays a plain callable — the type is the answer, rather than a flag
    the caller has to remember to pass and `add` has to trust.
    """

    read: Callable[[], str]

    def __call__(self) -> str:
        return self.read()


def _refuse_together(
    config: Config, task: Task, section: Rationale | None
) -> None:
    """Raise once for every field breached across the line and its section (RK426).

    Silent unless *both* halves are checkable now: a body that is a reader is RK381's case
    and stays deferred, and a task with no anchor or a project with no prose file are
    refusals :func:`_with_section` makes for reasons of their own. What this adds is the one
    thing neither pass could see — the other pass's findings — so it reports and never
    decides, and every rule below it still runs exactly as it did.
    """
    if section is None:
        return
    title, body = section
    if isinstance(body, Rereadable):
        # Cheap to fetch twice, which is the whole condition: a path re-read costs a file
        # read and a literal costs nothing, while a pipe is spent by looking at it.
        body = body()
    if not isinstance(body, str) or not task.ref:
        return
    role = prose_role(config)
    if role is None:
        return
    found = tuple(config.schema_for("roadmap").validate(task)) + sections.violations(
        config.schema_for(role), task.ref, title, body, task
    )
    if found:
        raise SchemaError(found)


def _with_section(
    config: Config, insertion: Insertion, title: str, body: str | Callable[[], str]
) -> Insertion:
    """Validate the rationale against the line that is not on disk yet (RK93).

    Every refusal the prose file has — the word budget, an undeclared block, an anchor
    already taken — arrives here, *before* the roadmap is written: a transaction that
    wrote the line and then refused the section would leave exactly the dangling pointer
    this closes, and one the author did not choose.

    A reader is called at the **last** moment it can be (RK381), which is below the two
    refusals this function makes itself: a line with no anchor and a project with no prose
    file are both facts known before a paragraph is needed, and reading one to discard it is
    the cost this door exists to stop paying. What is left above the read is
    :func:`sections.add`'s own anchor and title checking, which cannot be split from the
    body's without giving up reporting every violation at once — and that residue is what a
    body named by *path* answers instead, the retry re-reading the file.
    """
    task = insertion.entry.task
    if not task.ref:
        raise NoAnchor(task.id)
    role = prose_role(config)
    if role is None:
        raise NoProseFile(task.id)
    prose, written = sections.add(
        config, role, task.ref, title, body() if callable(body) else body, task=task
    )
    return replace(insertion, prose=prose, section=written)


def prose_role(config: Config, *, on_disk: bool = False) -> str | None:
    """Which prose role a section written now goes into, or None where none is declared (RK230).

    Improvements wherever it is declared — `section add`'s own default and where `--section`
    has always written — and otherwise the **first declared role**, which is the only answer
    for a project that declares one. That is the whole fix: naming the role outright refused
    `add --section` to exactly the projects RK172, RK186, RK196 and RK197 each taught one more
    reader about, and left them the two commands and the dangling pointer RK93 closed.

    **Derived, and never a flag on `add`.** The role is already said in `section add --role`,
    and a second place to say it is a second thing that can disagree; a project declaring both
    roles has a real choice, and taking that two-command route deliberately is how an author
    makes it — which is not the same as being handed it by a refusal.

    `on_disk` narrows it to roles whose file exists, which is what a *follow-up* needs (RK197):
    a command naming a file nobody created cannot run. A write does not ask, because
    `section add` writes into a declared file whether or not this run is the one creating it.
    """
    roles = tuple(
        role
        for role in PROSE_ROLES
        if config.has(role) and (not on_disk or config.path(role).is_file())
    )
    if not roles:
        return None
    return "improvements" if "improvements" in roles else roles[0]


def _unresolved(config: Config, ref: str) -> str | None:
    """The role a follow-up would write this pointer's section into, or None if one answers.

    RK15's finding, asked early — and asked of **every declared prose role** (RK197). Reading
    the improvements file alone told a project that declares `strategy` its pointer resolved
    to nothing, for an anchor `docs/STRATEGY.md` holds and `lint` resolves: the follow-up
    named a `section add` that would write a second copy, and the second copy is
    `ref.ambiguous` — one anchor in two roles, resolving to neither. That is worse than the
    read half it mirrors (RK186), because what it spends is prose the project already has and
    the tool cannot write it (L4), so the cost lands on the author.

    None when the project declares no prose file or has not created one yet: the pointer is
    then unresolvable for a reason no `section add` fixes, and a follow-up naming a command
    that cannot run is worse than the silence this replaces.

    The **role** and not just the fact, because a project declaring several has more than one
    place a section could go and the follow-up has to name the one it means — the same
    derivation the write itself now makes (RK230), so the command offered writes where
    `--section` would have.
    """
    role = prose_role(config, on_disk=True)
    if role is None or sections.declaring(config, ref):
        return None
    return role


@dataclass(frozen=True, slots=True)
class StatusChange:
    """The line as it now reads, and the marker it carried before (RK7)."""

    document: Document
    entry: Entry
    before: str
    #: Other lines whose dep annotation this write made true again (RK8).
    refreshed: tuple[str, ...] = ()
    #: What this write did to the claim on the line (RK158). Reported, because a marker change
    #: is not obviously an assertion of ownership to whoever typed it — and a claim taken or
    #: dropped without being said is the silence RK119 argued against for the answer itself.
    claim: Followed = Followed.NEITHER

    @property
    def after(self) -> str:
        return self.entry.task.status

    @property
    def changed(self) -> bool:
        return self.before != self.after

    @property
    def rendered(self) -> str:
        return self.entry.raw

    @property
    def lineno(self) -> int:
        return self.entry.lineno


def set_status(config: Config, task_id: str, marker: str) -> StatusChange:
    """Write one task's marker in the roadmap, and refuse if a sibling carries one.

    A marker is maturity, and maturity has one home. Two files that both express it will
    eventually express different values, and at that point there is no rule that says
    which one is the status — so the second one is refused rather than reconciled
    (:class:`StatusElsewhere`), and so is a second line for the same id in this file
    (:class:`DuplicateId`).

    ✅ is refused here by the schema itself, not by a special case: shipped work is the
    ledger's to state, and `ship` (RK6) is the only thing that puts it there.

    A marker this task's dependents cached is stale the moment it changes, so the write
    re-derives every annotation in the file (RK8) and names the lines it corrected.

    The claim follows the marker (RK158): 🛠 dates one and any other marker drops one, which is
    the rule the *read* already assumed and this door was the one exception to. It happens on
    the no-op path too — re-asserting the marker a line already carries is a re-assertion of
    the claim, the same way re-taking an expired one is a new claim — while the file itself is
    still left untouched, an unchanged file with a moved mtime reading as an edit.

    Which makes this the door that refuses a **taken** line (RK160), because it is the door
    every claim is written by: writing 🛠 over a live claim used to re-date it in the holder's
    name and say nothing. A release is never refused — that is any other marker.
    """
    backlog = Backlog.load(config)
    roadmap = backlog.roadmap
    entry = roadmap.by_id().get(task_id)
    if entry is None:
        raise NotOpen(
            task_id,
            config.relative(config.path("roadmap")),
            shipped=task_id in backlog.shipped(),
        )
    twins = tuple(e.lineno for e in roadmap.entries if e.task.id == task_id)
    if len(twins) > 1:
        raise DuplicateId(task_id, config.relative(config.path("roadmap")), twins)
    _refuse_sibling_status(config, task_id)
    # Before the write, beside every other refusal this door already makes (RK160): the
    # in-progress marker is an assertion that somebody is on the line, and one live claim is
    # all it takes for that to be somebody else's.
    claiming.refuse_taken(config, task_id, marker, roadmap.entries)

    # The **file's** schema and not the project's (RK401): `config.schema` is the default
    # grammar with no `[rules.<role>]` or `[limits.<role>]` applied, so on a project that
    # configured this file away from the default the gate called a line legal and this door
    # refused to correct it — leaving the hand edit the guard denies as the only way out.
    # `roadmap.schema` is what `Config.document` already resolved, which is the seam
    # `renumber` reaches through and the one `adopt` settled this argument on (RK76).
    updated = sections.checked(
        config, replace(entry.task, status=marker), schema=roadmap.schema
    )
    if updated.status == entry.task.status:
        # Nothing to write: rewriting the same bytes would make a no-op look like an
        # edit to every tool that watches the file.
        return StatusChange(
            document=roadmap,
            entry=entry,
            before=entry.task.status,
            claim=claiming.follow(config.root, task_id, marker, roadmap.entries),
        )
    derived = refresh(replace(backlog, roadmap=roadmap.replace_task(entry, updated)))
    derived.document.save()
    return StatusChange(
        document=derived.document,
        entry=next(e for e in derived.document.entries if e.lineno == entry.lineno),
        before=entry.task.status,
        refreshed=tuple(name for name in derived.changed if name != task_id),
        # After the save, and never a condition of it: the registry is transient state whose
        # worst failure is a claim lost, which is the behaviour before claims existed.
        claim=claiming.follow(config.root, task_id, marker, derived.document.entries),
    )


@dataclass(frozen=True, slots=True)
class Amendment:
    """One line as it now reads, and as it read before (RK65).

    Not a :class:`StatusChange` with more fields: the marker has its own door because status is
    maturity, and this one exists for the fields a project *adopting* the tool has to correct —
    which is a different question with a different refusal.
    """

    document: Document
    entry: Entry
    before: Task
    #: Other lines whose dep annotation this write made true again (RK8).
    refreshed: tuple[str, ...] = ()

    @property
    def changed(self) -> tuple[str, ...]:
        """Which fields actually differ, in field order — empty when nothing was written."""
        return tuple(
            name
            for name in ("why", "deps", "ref")
            if getattr(self.before, name) != getattr(self.entry.task, name)
        )

    @property
    def rendered(self) -> str:
        return self.entry.raw


def amend(
    config: Config,
    task_id: str,
    *,
    why: str | None = None,
    deps: Sequence[str] | None = None,
    ref: str | None = None,
    lines: int | None = None,
) -> Amendment:
    """Correct one open line's `why`, `deps` or `ref`. Validated at input, or nothing (RK65).

    The three fields a project that adopted the tool has to be able to fix: a pointer it never
    had, a dep naming an id that is in neither file, and the compression of a `why` that was a
    paragraph before the limit existed. `retire` plus `add` would lose the id, and the id is
    what the history is keyed on.

    `symptom` is deliberately absent: it is the falsifiable claim the line *is*, so a different
    one is a different task — and the corpus says it is not the problem (0 of Shio's 78 over the
    limit, against 70 of its whys). `status` is absent because :func:`set_status` is its door.

    Nothing is written when nothing differs: rewriting the same bytes makes a no-op look like an
    edit to every hook watching the file.

    And refused on a **wrapped** line unless `lines` says how many it replaces (RK195). The
    ledger's rule (RK179) one file over, for the reason that made it worth counting rather
    than assuming: this is the door a project *adopting* the tool reaches for, and an adopted
    roadmap is the only place a wrapped line can come from — `add` refuses to write one, so
    every governed roadmap reads as zero and the population is the backlogs nobody has
    imported yet.
    """
    backlog = Backlog.load(config)
    roadmap = backlog.roadmap
    entry = roadmap.by_id().get(task_id)
    if entry is None:
        raise NotOpen(
            task_id,
            config.relative(config.path("roadmap")),
            shipped=task_id in backlog.shipped(),
        )
    twins = tuple(e.lineno for e in roadmap.entries if e.task.id == task_id)
    if len(twins) > 1:
        raise DuplicateId(task_id, config.relative(config.path("roadmap")), twins)

    wanted = replace(
        entry.task,
        why=entry.task.why if why is None else why,
        deps=entry.task.deps
        if deps is None
        else read_deps(", ".join(deps), roadmap.schema),
        ref=entry.task.ref if ref is None else ref,
    )
    # Derived on write like every other annotation (RK8): the author names the dep and the
    # tool states whether it shipped.
    updated = sections.checked(config, derive(backlog, wanted), schema=roadmap.schema)
    if updated == entry.task:
        return Amendment(document=roadmap, entry=entry, before=entry.task)
    # Asked after the no-op check, so an amend that alters nothing never demands a count for
    # a write it is not going to make.
    counted(
        task_id,
        config.relative(config.path("roadmap")),
        entry,
        lines,
        verb="correcting it",
    )
    derived = refresh(replace(backlog, roadmap=roadmap.rewrite_entry(entry, updated)))
    derived.document.save()
    return Amendment(
        document=derived.document,
        entry=next(e for e in derived.document.entries if e.lineno == entry.lineno),
        before=entry.task,
        refreshed=tuple(name for name in derived.changed if name != task_id),
    )


@dataclass(frozen=True, slots=True)
class Restatement:
    """One line's falsifiable claim, corrected under the id that keeps it (RK178).

    Not an :class:`Amendment` with a fourth field, and the separation is the whole answer:
    `amend` reaches the fields a description gets *wrong about work that did not change*, and
    it excludes this one because a different symptom is normally a different task (RK65). That
    reason is sound and its outcome was not — a premise that turns out false leaves the file
    this tool exists to keep true asserting something false, in the field a reader sees first.

    So the correction is a verb rather than a flag, and this shape is what makes it *recorded*
    instead of hidden: the act has a name in the history, and the answer prints both readings,
    so a reviewer sees a restatement where a `--symptom` inside `amend` would have shown a
    word changing. What it deliberately does **not** carry is a reason — there is no field in
    the format for one, and an argument the tool cannot store is an argument it must not
    pretend to take (L4). The commit that removes the false claim is where it belongs.
    """

    document: Document
    entry: Entry
    before: Task
    #: Other lines whose dep annotation this write made true again (RK8). Normally empty: a
    #: symptom is nobody's dependency, and this is here because the write path derives it.
    refreshed: tuple[str, ...] = ()
    #: Whether the caller declared this a slip of the pen rather than a false premise (RK414).
    #: Declared and **never inferred**: which of the two a rewording is cannot be read off two
    #: strings, and a tool that guessed would be filing the caller's intent under its own.
    typo: bool = False

    @property
    def changed(self) -> bool:
        return self.before.symptom != self.entry.task.symptom

    @property
    def rendered(self) -> str:
        return self.entry.raw

    @property
    def lineno(self) -> int:
        return self.entry.lineno


def restate(
    config: Config,
    task_id: str,
    symptom: str,
    *,
    lines: int | None = None,
    typo: bool = False,
) -> Restatement:
    """Correct one open line's symptom, keeping its id, its deps and its section (RK178).

    ``typo`` splits the two acts this door had to carry as one (RK414). The verb is
    documented for the case it was written for — the premise itself turned out false — and a
    misspelt word is not that: the claim is the one intended, and repairing it through a
    door whose answer reads *the work never changed, the premise did* files a decision
    nobody took. So the caller says which, the answer says which, and `restate`'s every
    other occurrence still means what its documentation says, which is the only thing that
    makes it greppable.

    Declared and never inferred, deliberately. Whether "the annotaton is stale" → "the
    annotation is stale" is a spelling fix and "the annotation is stale" → "the annotation
    is absent" is a new claim cannot be read off the two strings — the difference is what
    the author meant — so a tool that decided would be recording its guess as the record.
    Nothing is validated differently either: a typo's symptom faces the same schema, because
    a slip of the pen that lands over the limit is still over the limit.

    The door RK65 was right to leave shut and the one nothing else opened. Measured in
    claude-tray: T210 was written from a list of response headers, executing it meant reading
    the files, and the premise was false — nothing there derived what the line asserted. The
    `why` was corrected, the marker dropped to an idea, the rationale rewritten to open by
    refuting itself, and the symptom could not be touched at all.

    The designed exit was `retire` plus `add`, and it costs twice: it spends an id, deletes a
    section that was already right, and records a departure where none happened — and RK125
    shows a project that cannot retire at all. None of that is a price a *correction* should
    pay, because the work never changed. So the id stays, which is what the history is keyed
    on, and every other field with it.

    Nothing is written when nothing differs, as at the door next to this one: rewriting the
    same bytes makes a no-op look like an edit to every hook watching the file.

    A claim is deliberately not consulted. `status` refuses a held line because writing 🛠 is
    an *assertion of ownership* (RK160), and this write touches no marker: the person who
    discovers a premise is false is normally the one holding the line, and a rule that refused
    them would be a rule against the case this verb exists for.
    """
    backlog = Backlog.load(config)
    roadmap = backlog.roadmap
    entry = roadmap.by_id().get(task_id)
    if entry is None:
        raise NotOpen(
            task_id,
            config.relative(config.path("roadmap")),
            shipped=task_id in backlog.shipped(),
        )
    twins = tuple(e.lineno for e in roadmap.entries if e.task.id == task_id)
    if len(twins) > 1:
        raise DuplicateId(task_id, config.relative(config.path("roadmap")), twins)

    updated = sections.checked(
        config,
        derive(backlog, replace(entry.task, symptom=symptom)),
        schema=roadmap.schema,
    )
    if updated == entry.task:
        return Restatement(document=roadmap, entry=entry, before=entry.task, typo=typo)
    # The same count as the door next to this one (RK195): a restatement rewrites the line's
    # prose, so on a wrapped line it strands the same tail.
    counted(
        task_id,
        config.relative(config.path("roadmap")),
        entry,
        lines,
        verb="restating it",
    )
    derived = refresh(replace(backlog, roadmap=roadmap.rewrite_entry(entry, updated)))
    derived.document.save()
    return Restatement(
        document=derived.document,
        entry=next(e for e in derived.document.entries if e.lineno == entry.lineno),
        before=entry.task,
        refreshed=tuple(name for name in derived.changed if name != task_id),
        typo=typo,
    )


def _refuse_sibling_status(config: Config, task_id: str) -> None:
    """Any other governed file carrying a marker for this id is the disagreement."""
    for role in ROLES:
        if role == "roadmap" or not config.has(role) or not config.path(role).is_file():
            continue
        found = config.document(role).by_id().get(task_id)
        if found is not None:
            raise StatusElsewhere(
                task_id,
                role,
                config.relative(config.path(role)),
                found.lineno,
                found.task.status,
            )


def refuse_reuse(config: Config, task_id: str) -> None:
    """Refuse an id anything already mentions, anywhere (RK4).

    Public because every door that mints an id needs the same refusal, and an id rule
    with a second implementation is an id rule two commands can disagree about: `add`
    (RK5) and `record` (RK41) both call this one.
    """
    clash = next((ref for ref in scan(config) if ref.id == task_id), None)
    if clash is not None:
        raise IdInUse(task_id, config.relative(clash.path), clash.lineno)


def declaring(config: Config, block: str) -> None:
    """Refuse a block the **ledger** does not declare, at the door that opens it (RK380).

    The roadmap's own heading is `place`'s refusal and this is the other half. Measured in
    Turing: Block BV carried eight open lines and no `## Block BV` in `CHANGELOG.md`, and the
    first `ship` in that block refused — correctly, and at the worst possible moment. A ship
    is the *end* of a task: the code is written, the tests pass, the commit is drafted, and
    the author is then told the backlog was mis-set-up before any of it started. The fact was
    available at the `add` that opened the block, where nothing is at stake and the retry
    costs one command.

    So the condition is exactly `ship`'s — the ledger declares no heading for this label —
    asked one task earlier, and the refusal is :class:`~roadkeep.document.UnknownBlock`
    itself, spelling the same file and the same `block add` remedy. A second sentence for one
    condition is a second thing to keep true.

    Not a write, which is the option this deliberately does not take (RK141): `block add`
    takes the **title** because naming a block is editorial, and `add` holds a label and no
    title. A heading composed here would be one nobody looks under, and L4 forbids the tool
    inventing the words for it.

    Silent where the project declares no ledger and where its file is not on disk yet: a
    refusal about a file nothing reads is one the author cannot act on, and `ship` on such a
    project has nothing to refuse over either.

    **A ledger organised by nothing is asked too** — and for a week it was not (RK403,
    RK411), which is the one fact this docstring exists to keep straight. Measured on a fresh
    project whose changelog was prose: this refused and named `block add`, which answered *A
    is already declared in docs/ROADMAP.md: nothing to open*, because a file declaring no
    block is not one that verb started organising. A refusal naming a remedy that refuses is
    worse than silence, so the check was narrowed to ledgers that declare a block. RK405 gave
    that verb `--organise <role>`, the remedy exists, and the narrowing's whole reason went
    with it — restored here, and it is the premise having moved rather than a decision
    reversed. The refusal names the argument, so the author is never sent to the refusing
    command: see :class:`~roadkeep.document.UnknownBlock`.
    """
    if not config.has("changelog") or not config.path("changelog").is_file():
        return
    ledger = config.document("changelog")
    if ledger.heading(block) is not None:
        return
    raise UnknownBlock(
        block,
        sorted({heading.label for heading in ledger.headings if heading.label}),
        config.relative(config.path("changelog")),
        word=ledger.schema.heading_word,
        # The one raiser whose two files differ (RK404): the labels are the ledger's and the
        # line is the roadmap's, and unsaid that reads as the label being wrong.
        into=config.relative(config.path("roadmap")),
        # And the argument that opens a first heading, where this file has none (RK411):
        # without it this door is the one that sends the author to a refusing command.
        organise="changelog",
    )


def _placement(
    document: Document, heading: Heading, rendered: str, carrying: tuple[str, ...] = ()
) -> tuple[int, list[str]]:
    """Where the line goes, and the lines to insert there — blank ones included.

    After the block's last task when it has one, which needs no blank-line reasoning at
    all. An empty block does: the heading may be followed by a blank line, by the next
    heading, or by nothing, and a task glued to either side of a heading reads as
    belonging to the wrong one.

    An empty block also carries its own prose down with it (RK108) — the paragraph that
    says what the block is for stays above the first task, because the line after the
    heading's blank is where the introduction is and not where the backlog starts.
    """
    entries = document.block(heading.label)
    if entries:
        # The last entry's *end*, not the line after its first line (RK157): a ledger entry
        # written before this tool existed wraps, and the lines under it parse as nothing —
        # so inserting one line down put the new bullet inside the previous entry and left
        # its paragraph reading as the sentence somebody else shipped. Silent, because both
        # bullets round-trip and no rule says a continuation line belongs to the bullet above.
        return entries[-1].stop, [rendered, *carrying]

    lines = document.lines
    index = _after_preamble(document, heading)
    before: list[str] = []
    if index < len(lines) and blank(lines[index]):
        index += 1
    else:
        before = [""]
    at_end = index >= len(lines)
    after = [] if at_end or blank(lines[index]) else [""]
    return index, [*before, rendered, *carrying, *after]


def _after_preamble(document: Document, heading: Heading) -> int:
    """The line past the heading's own prose — 0-based, and the heading's own line when
    there is none, which is every block in this repository and was the whole rule (RK108).

    *Own* is the boundary the document draws (RK115): any heading ends it, because prose
    under a nested heading belongs to that heading and a line placed after it would sit
    under the wrong one. Trailing blanks are not prose, so what comes back is the blank
    that separates the paragraph from the block — which the caller then reads exactly as it
    reads the blank after a bare heading.
    """
    start = heading.lineno  # 0-based: the line after the heading
    end = document.prose_end(heading)
    index = start
    for offset in range(start, end):
        if not blank(document.lines[offset]):
            index = offset + 1
    return index
