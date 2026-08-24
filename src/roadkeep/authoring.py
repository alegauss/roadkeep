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
from pathlib import Path

from roadkeep import claiming, sections
from roadkeep.backlog import Backlog, DepStatus, NotOpen, Whereabouts
from roadkeep.claiming import Followed
from roadkeep.config import PROSE_ROLES, ROLES, Config
from roadkeep.kernel.document import (
    Document,
    Entry,
    Heading,
    RepeatedHeading,
    UnknownBlock,
    counted,
    save_all,
    blank,
    read_deps,
    read_requires,
)
from roadkeep.ids import CARRIERS, IdRef, Promise, carried, derivation, scan
from roadkeep.markers import derive, refresh
from roadkeep.kernel.schema import SchemaError, Task, width as measured_width
from roadkeep.sections import Section

#: The rationale a line arrives with: the heading, and prose that is either the string itself
#: or a **reader** for it (RK381). A reader is called once, at the last moment it can be — see
#: :func:`_with_section` — so a caller whose paragraph comes off a pipe does not spend it on a
#: call the line's own fields were going to refuse.
Rationale = tuple[str, "str | Callable[[], str]"]


class IdInUse(ValueError):
    """An id is the one decision that cannot be taken back once it is committed.

    ``flag`` is which argument this caller's number arrived on (RK1212). Written for `add
    --id`, where every word of it is right, and shared by RK4 with every door that moves a
    task onto a number — so `renumber --to TT1` answered *omit `--id` and it is derived* at a
    verb that declares no `--id`, and said so itself one call later. The advice underneath is
    correct at all of them, which is what makes the wrong spelling worse than no remedy: it
    reads as typeable, and costs a call to find out it is not.

    An argument and not a lookup here, the shape :class:`~roadkeep.kernel.document.UnknownBlock`
    already has for `--organise`: the raiser is the one thing that knows which door it is.
    """

    def __init__(self, task_id: str, where: str, lineno: int, *, flag: str = "--id") -> None:
        self.task_id = task_id
        self.where = where
        self.lineno = lineno
        self.flag = flag
        super().__init__(
            f"{task_id} already occurs at {where}:{lineno}: an id is never reused, "
            f"not even one that was retired — omit {flag} and it is derived"
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


class NoSuchDep(ValueError):
    """A dep naming an id neither governed file carries (RK500).

    The gate's `deps.unknown`, asked where the token is typed. Measured by RK498's register
    as one of the five findings a write accepted, and the one that costs more than it reads:
    the write already treats the token as an id, so the next derived number steps **over** it
    (RK431) — an unresolvable dep is therefore not ignored, it spends an address.

    Decidable from what the verb is already holding. `Backlog` is loaded to place the line
    and to derive the annotation, and it is the same reader the gate asks; nothing here needs
    git, a second file or a listing.

    Only `UNKNOWN`, which is the resolver's own answer and not a guess about the token: work
    outside this backlog and a paused dep both resolve to something else, and refusing either
    would refuse a line that states a fact honestly (RK92).
    """

    def __init__(self, task_id: str, deps: Sequence[str], where: str) -> None:
        self.task_id = task_id
        self.deps = tuple(deps)
        named = ", ".join(self.deps)
        super().__init__(
            f"{task_id} would wait on {named}, which {'are' if len(self.deps) > 1 else 'is'} "
            f"in neither {where} nor the changelog: nothing can say whether it is done — "
            f"state the dep it meant, or `gaps` reads where the id went"
        )


class CyclicDep(ValueError):
    """A dep that would leave the line waiting on itself (RK500).

    The gate's `deps.cycle`, asked before the line exists. Two shapes reach it and the
    refusal is one: a dep whose own blockers walk back to this task, and a `Block X` dep
    naming the block the line is being **filed into** — the block cannot empty until this
    line ships, so the line waits on itself.

    The second needs saying explicitly, because it is the one the graph cannot see: the line
    is not in the backlog yet, so expanding `Block X` yields the members it has *now* and
    this task is not among them. It becomes a member the moment the write lands, which is
    what makes the answer decidable and not a prediction.
    """

    def __init__(self, task_id: str, dep: str, *, joins: bool = False) -> None:
        self.task_id = task_id
        self.dep = dep
        super().__init__(
            f"{task_id} would wait on {dep}, "
            + (
                f"which is the block this line is filed under: the block cannot empty "
                f"until this line ships, so no amount of shipping anything else makes it "
                f"ready"
                if joins
                else f"whose own blockers walk back to {task_id}, so nothing in the group "
                f"can be started"
            )
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
    #: The family that follow-up's anchor extends, where that role declares none yet (RK1205).
    #: One address up and the same verb, because `section add I.1` on a file with no §I is
    #: `UnknownParent` — so without this the command handed over is one that cannot run, which
    #: is RK197's own claim about a *file* nobody created, made one level down.
    opens: str | None = None
    #: The family this write **declared**, where the design it wrote is a block's first
    #: (RK1258). Distinct from :attr:`opens`, which is a call still owed: this one already ran,
    #: inside the same transaction, and what it left is a heading with no prose under it. Said
    #: out loud because the write touched a second address the caller did not name, and because
    #: the words it took are the block's — which is the one thing an author may want to correct.
    opened: str | None = None
    #: The id a sentence promised that deriving this one stepped over (RK431). Set only
    #: where the id was *derived* — a caller that named its own spent nothing — and only
    #: where the number below it is a mention no line ever took.
    promise: Promise | None = None
    #: The outline section this line's pointer just bound itself into (RK452), where the
    #: design was written before the line. Distinct from :attr:`section`, which is a section
    #: this write *created*: nothing was gained here, an existing heading stopped belonging
    #: to nobody, and a caller reporting one as the other would say a paragraph was written
    #: that was not. Always None under `ref_scheme = "id"`, where the anchor is the id.
    bound: Section | None = None
    #: Every path :meth:`save` wrote, projections included (RK1129) — set by :func:`add` off
    #: the save's own return, and empty on an insertion nothing has written yet. This is the
    #: list a `git add --` takes, which is the one thing the report could not say.
    wrote: tuple[Path, ...] = ()

    @property
    def rendered(self) -> str:
        return self.entry.raw

    @property
    def lineno(self) -> int:
        return self.entry.lineno

    def save(self) -> tuple[Path, ...]:
        """Write the files, and answer which paths that touched.

        The return is :func:`~roadkeep.kernel.document.save_all`'s own, projections included
        (RK1129): a write that refreshes a derived block owes the caller the fact, because the
        caller is composing a commit and the block is what a clean checkout calls stale. It was
        discarded here, so the report had nothing to name.
        """
        return save_all(self.document, self.prose)

    def follow_up(self) -> str | None:
        """The `section add` that closes a pointer this write just created (RK93, RK197).

        `--role` only where it is not the default, which keeps the sentence every project sees
        the one it already saw — and makes the exception the case that needs it: a project whose
        only prose file is the strategy one would otherwise be handed `section add`'s default and
        a role it does not declare, which is a follow-up that cannot run.

        On the record since RK1170, with the two registers that print it: the anchor and the
        role are both fields here, and a helper in the door was the *third* place that pair had
        to be read together.
        """
        if self.needs is None:
            return None
        return f"section add {self.needs} --title …{self._named()}"

    def _named(self) -> str:
        return "" if self.needs_role in (None, "improvements") else f" --role {self.needs_role}"

    def follow_ups(self) -> tuple[str, ...]:
        """Every call between this write and a pointer that resolves, in order (RK1205).

        One normally, and that one is :meth:`follow_up`. Two where the anchor extends a family
        no prose file declares yet: `section add` refuses that child with `UnknownParent`, so
        the single command this used to hand over was one the author would run and be refused
        by — worse than silence, because a printed call is read as a call that works.

        The parent's own title is not composed here and never could be (L4): what is derived
        is that a call is needed and what its address is, which is everything except the words.
        """
        if self.needs is None:
            return ()
        opening = (
            () if self.opens is None
            else (f"section add {self.opens} --title …{self._named()}",)
        )
        return (*opening, f"section add {self.needs} --title …{self._named()}")

    def event(self, config: Config) -> dict[str, object]:
        """What this write did to the block it landed in (RK38), off the file it wrote."""
        from roadkeep.rendering import _event  # noqa: PLC0415 - RK260

        return _event(self.entry.task.id, self.entry.task.block, self.document, config)

    def added(self, config: Config, capture: str | None, stamped: bool) -> str:
        """`add`'s own answer, as a reader is told it (RK93, RK431, RK452).

        **Named for the verb and not `stated`** (RK1170), which is the same choice
        :class:`~roadkeep.shipping.Departure` makes for its second door: this record is
        *embedded* by three other transactions — a pause's store line, a departure's ledger
        line, a record's — and a method called `stated` on it would answer about an `add` from
        inside each of them. There is no default door here to take the plain name.

        `capture` and `stamped` are parameters for the reason `wrote` is elsewhere: the stamp
        happens after the save and outside this transaction (RK1141), so they are facts about
        the call and a record holding them would be claiming a write it did not make.
        """
        from roadkeep.rendering import (  # noqa: PLC0415 - RK260
            _event_rows,
            _prose_file,
            _staging_rows,
        )
        from roadkeep.provenance import invocation  # noqa: PLC0415 - RK260

        # The file the write actually chose (RK230), read off the document `_with_section` left
        # rather than composed from the improvements default: a report that names the role and a
        # write that derives it are two answers, and one of them is wrong on every project that
        # declares `strategy` alone.
        prose = _prose_file(config, self.prose)
        rows = [self.rendered]
        if self.opened is not None:
            # Above the design and not below it, because that is the order the file now reads
            # in — and with the correction named, the title being the block's rather than one
            # this write composed (RK1258).
            rows.append(
                f"opened   §{self.opened} → {prose}, titled from Block "
                f"{self.entry.task.block}  (`section amend {self.opened} --title` renames it)"
            )
        if self.section is not None:
            rows.append(
                f"design   §{self.section.anchor} → {prose}:{self.section.first}  "
                f"{self.section.words} words"
            )
        elif self.needs is not None:
            # Backticked and carrying the invocation, like every other route this tool composes
            # (RK476): the bare argv is the *field*, and a line printed for a reader is the form
            # `serving._rerouted` already spells as a tool where there is no shell.
            # Every call and not the last one (RK1205): where the anchor extends a family this
            # file has not opened, the closing command refuses until the opening one has run,
            # and naming one of the two is the staircase RK1198 took out of the door above.
            rows += [
                f"needs    `{invocation()} {one}`  "
                f"(the pointer above resolves to nothing until then)"
                if one == self.follow_ups()[-1]
                else f"needs    `{invocation()} {one}`  "
                f"(§{self.needs} extends it, and no prose file declares it yet)"
                for one in self.follow_ups()
            ]
            # And the call that would not have needed any of them (RK1218). `add --section`
            # has written both halves in one transaction since RK93, and this row — printed on
            # every `add` that omits it — named only the *follow-up*, so what the tool taught,
            # once per task, was the two-command path. Measured across fourteen sessions
            # driving another project's backlog: every task filed in two commands, with the
            # roadmap between them in the state this project's own gate calls `ref.unresolved`.
            #
            # Under the row rather than instead of it: this call is already made and its
            # pointer already dangles, so the follow-up is what closes *this* one and this is
            # what closes the next. A line that replaced the remedy with advice would be the
            # tool answering a question the caller has not asked yet.
            # A **flag** and never a composed command, which is the one care this row needs.
            # `add` has already run here, so an argv printed with the invocation on it would
            # read as a call to make — and making it files a second task. RK1209's sweep finds
            # a command by exactly that prefix, so the shape is also what keeps this row out
            # of it: what is offered is the argument to add next time, not a call to run now.
            rows.append(
                'or       pass `--section "<its title>"` to `add` next time: both halves in '
                "one transaction, under the same limits"
            )
            # And **what that body may weigh**, at the moment the caller is about to write it
            # (RK1309). The row above names the command and the limit it enforces reached the
            # author only as a refusal: measured in pportal, 2026-08-22, a body written to a
            # file and passed with `--section-body-file` came back 266 words against 250 — a
            # good refusal, arriving after the paragraph, with the retry paying for every word
            # of it again. The figure is a fact about the role and needs no id, so this is the
            # one place it costs nothing to state: the id was just minted and the prose has
            # not been composed, which is the whole of L1 said about one field.
            rows.append(f"weighs   {_body_aim(config, self.needs, self.prose)}")
        elif self.bound is not None:
            # Said, because the write touched a second file the caller did not name (RK452) —
            # and because the heading now carries an id, which is the fact `ship` and the gate
            # both read as "this design belongs to that task".
            rows.append(
                f"bound    §{self.bound.anchor} → {prose}:{self.bound.first}  "
                f"the design was written first, so this line's id is now in its heading"
            )
        if self.promise is not None:
            # Beside the line and not instead of it: the `add` succeeded, and what this reports
            # is a sentence somewhere else that has just stopped being true (RK431).
            rows.append(f"promise  {self.promise.sentence}")
        if capture:
            # Said either way: a stamp that did not land is the row `stats` will still count,
            # and silence about it is how a second step comes to be forgotten (RK86).
            rows.append(
                f"capture  {capture} now names {self.entry.task.id}"
                if stamped
                else f"capture  {capture} could not be stamped: the line is filed, the "
                f"link is not"
            )
        # The projection this write refreshed is in here (RK1129): the roadmap and the rationale
        # are files the caller named, and the README is one they did not — so a commit took the
        # two and left the third, green against the tree and `export.stale` in a clean checkout.
        rows += _staging_rows(config.relative(one) for one in self.wrote)
        rows += _event_rows(self.event(config), config=config)
        return "\n".join(rows)

    def addition(
        self, config: Config, capture: str | None, stamped: bool
    ) -> dict[str, object]:
        """The same answer as data, with both derived addresses (RK249)."""
        from roadkeep.rendering import (  # noqa: PLC0415 - RK260
            _promise_json,
            _prose_file,
        )

        prose = _prose_file(config, self.prose)
        return {
            "id": self.entry.task.id,
            # The other derived address (RK249). Reported for the reason `id` is: under
            # `ref_scheme = "outline"` the write derives it, and the only other readings were
            # the tail of `rendered` and the anchor inside the `needs` sentence — which is null
            # exactly when `--section` wrote the rationale here, the composition RK93 recommends.
            "ref": self.entry.task.ref,
            "file": config.relative(config.path("roadmap")),
            "line": self.lineno,
            "rendered": self.rendered,
            "length": measured_width(self.rendered),
            "section": None if self.section is None else self.section.payload(prose),
            # The family this write declared on the way in (RK1258): null on every add that
            # extended one already there, so a client tells a heading it now owns from one it
            # merely wrote under. An address and not a section — what is there is a heading.
            "opened": self.opened,
            # Not a section this write *created* (RK452): an existing outline heading stopped
            # belonging to nobody, and a caller reading one key for both would report a
            # paragraph that was never written.
            "bound": None if self.bound is None else self.bound.payload(prose),
            # The follow-up as data: null when the pointer already resolves, so a caller acts
            # on a field instead of matching a sentence (RK93). The **first** call and not the
            # closing one (RK1205) — which is the same value on every project not meeting that
            # defect, and a call that runs on the one that is: this key has always meant *what
            # to do next*, and where a family is missing the closing command is not it.
            "needs": None if self.needs is None else self.follow_ups()[0],
            # And the whole sequence, because the first alone is the staircase again: empty
            # where the pointer resolves, one call normally, two where a family has to be
            # opened before the design can extend it.
            "needs_path": list(self.follow_ups()),
            # And what the body that follow-up writes may weigh (RK1309), beside the call that
            # writes it: the limit reached the author only as a refusal, and this is the one
            # moment it costs nothing to state — the id is minted and the prose is not composed.
            # `null` where the pointer already resolves, there being no body still to write.
            "weighs": None
            if self.needs is None
            else _body_weight(config, self.needs, self.prose),
            # Null on almost every add, and the whole point when it is not (RK431): the id
            # below the one just written was a sentence, not a line.
            "promise": _promise_json(self.promise),
            # Every path this write touched, projections included (RK1129) — the same key a
            # departure's scope carries, so a client staging one stages the other.
            "wrote": [config.relative(one) for one in self.wrote],
            # Which capture this line files, where one was named (RK1141) — null where none
            # was, and false where the stamp could not be written, so a client tells "not
            # asked" from "asked and did not land".
            "capture": None if not capture else {"path": capture, "stamped": stamped},
            "event": self.event(config),
        }


def compose(
    config: Config,
    *,
    task_id: str,
    block: str,
    symptom: str,
    why: str,
    status: str | None = None,
    deps: Sequence[str] = (),
    requires: Sequence[str] = (),
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
        # Through the file's own reader for `deps`' reason (RK1297): what an author types
        # and what the parser reads back out of the line are split by one function, so a
        # group the writer and the reader disagree about is not a state this can reach.
        requires=read_requires(", ".join(requires)) if requires else (),
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

    Raises :class:`~roadkeep.kernel.schema.SchemaError` with every violation,
    :class:`UnknownBlock` when no heading declares the block,
    :class:`~roadkeep.kernel.document.RepeatedHeading` when two do (RK391), and
    :class:`~roadkeep.kernel.document.RoundTripError` when either the file already carries a
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
    # Computed before `check` and raised after it (RK1256), which is the seam this closes.
    # `UnknownBlock` and `SchemaError` are two whole halves — each names every problem of its
    # own class — and a call wrong in both was refused twice, learning one class per round
    # trip. The block is answerable here regardless of the prose: it is a heading in a
    # document already read, so nothing about it waits on the fields being legal.
    declared = document.declaring(task.block)
    unopened = (
        UnknownBlock(
            task.block,
            sorted({h.label for h in document.headings if h.label}),
            where,
            word=document.schema.heading_word,
            # Which file the remedy has to start organising, where it declares no block at
            # all (RK405) — the same fact `where` is, which is why it is derived and not
            # asked for (RK412). Empty only for the caller that gave a path alone.
            organise=role,
        )
        if not declared
        else None
    )
    try:
        document.schema.check(task)
    except SchemaError as error:
        # Around `check` rather than before it, so a line that is missing a pointer *and*
        # over on its `why` still hears both (RK312): the schema reports every violation at
        # once, and an early refusal here would trade that for the one sentence it improves.
        refusal = (
            error
            if config is None
            else sections.naming_the_anchor(config, task.block, error)
        )
        if unopened is not None:
            # The other half, carried rather than merged: `UnknownBlock` renders a remedy
            # a bare violation line would lose, and folding it into `violations` would make
            # a rule of this schema out of a fact about a heading.
            refusal.beside = str(unopened)
        raise refusal from None
    if unopened is not None:
        raise unopened
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


def refuse_deps(config: Config, backlog: Backlog, task: Task) -> None:
    """Refuse the two deps a write can decide about the backlog in front of it (RK500).

    L1 for the dep field: the gate reports `deps.unknown` and `deps.cycle` about a line that
    is already in the file, and both are answerable from the :class:`~roadkeep.backlog.Backlog`
    this verb loaded to place the line and derive its annotation.

    **What stays the gate's, and why the boundary is not arbitrary.** `deps.retired` and
    `deps.stale` become true when a *later* write moves the line the dep names — the write
    that stated it was correct when it ran, so there was nothing to refuse. These two are
    false the moment they are written.

    The cycle walk uses :func:`~roadkeep.graph._hops` on the task **as it would be**, which
    is why it is that function and not :meth:`Graph.of`: the line may not be in the backlog
    yet, and asking the graph about an id it has never seen answers about nothing.
    """
    # Deferred: `graph` reads a backlog and this module writes one, so the edge runs one way
    # at import and the other at call time (RK260).
    from roadkeep.graph import Graph, _hops  # noqa: PLC0415 - RK500

    where = config.relative(config.path("roadmap"))
    unknown = [
        resolution.dep.id
        for resolution in backlog.resolve(task)
        # A line naming **itself** is the schema's `deps.self`, decided from the field alone
        # and with a message of its own. Answering it here first would report a dep in
        # neither file, which is true and is the less useful of the two things to say.
        if resolution.status is DepStatus.UNKNOWN and resolution.dep.id != task.id
    ]
    if unknown:
        raise NoSuchDep(task.id, unknown, where)
    schema = backlog.config.schema
    for dep in task.deps:
        # The block this line is filed under, which the expansion below cannot know about.
        if schema.classify_dep(dep).collective and dep.id == f"Block {task.block}":
            raise CyclicDep(task.id, dep.id, joins=True)
    graph = Graph.of(backlog)
    for hop in _hops(backlog, task):
        if not hop.walkable:
            continue
        if hop.target == task.id or task.id in graph.reach(hop.target):
            raise CyclicDep(task.id, hop.via)


def add(
    config: Config,
    *,
    block: str,
    symptom: str,
    why: str,
    status: str | None = None,
    deps: Sequence[str] = (),
    requires: Sequence[str] = (),
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

    ``requires`` is what has to be *present* for the work to be finishable (RK1297) — never
    derived and never inferred, because nothing in either file can see the room the caller
    is in. Every token is refused here unless `[requirements] declared` names it (L1), so a
    requirement `pick` could never match is not a line this door writes.

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
    promise: Promise | None = None
    if task_id is None:
        # Read before the write and not after it: this `add` is about to put the derived id
        # into a file the scan reads, and from that moment the corpus no longer says which
        # of the two numbers was a line and which was a sentence (RK431).
        derived = derivation(config, family)
        task_id, promise = derived.id, derived.promise
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
        requires=requires,
        ref=ref,
    )
    # The pointer, against the same history `section add` reads (RK1177). One command earlier
    # than it used to be: `add --ref XIV.29` was accepted and `section add XIV.29` then refused
    # it, so the repair was an `amend --ref` against a line that should never have been written
    # — and the `ref.unresolved` state in between is indistinguishable from the honest one every
    # two-command task passes through, so a reader cannot tell *not written yet* from *can never
    # be written*. The check already existed and already knew the answer; what it lacked was
    # being asked here, which costs one lookup.
    _refuse_retired(config, task)
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
    backlog = Backlog.load(config)
    # Before `place`, which is where the line stops being a proposal: a dep nothing carries
    # and one that closes a loop are both facts about this backlog, and both are false now
    # rather than later (RK500).
    refuse_deps(config, backlog, task)
    insertion = replace(
        place(
            config.document("roadmap"),
            derive(backlog, task),
            role="roadmap",
            config=config,
        ),
        promise=promise,
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
            insertion,
            needs=insertion.entry.task.ref,
            needs_role=role,
            opens=_unopened(config, role, insertion.entry.task.ref),
        )
    else:
        insertion = _binding(config, insertion)
    # The paths ride back on the record (RK1129), because the caller composing a commit is the
    # one who needs them and `save` is the only reader that knows what a projection refreshed.
    return replace(insertion, wrote=insertion.save())


def _unopened(config: Config, role: str, anchor: str) -> str | None:
    """The family this anchor extends that the prose file has not opened yet (RK1205).

    ``None`` wherever the follow-up runs as it stands: an anchor whose parent is declared, a
    top-level one under an outline — which :func:`~roadkeep.sections.place_for` places after
    the last top level (RK166) — and the id scheme, where an anchor carries no place at all
    and a `§RK9` extending nothing is a section for a task rather than a child of anything.

    Asked here rather than left to `section add`, because this is the moment the command is
    *composed*: the refusal one door over is correct and arrives one call too late, after the
    author has spent a retry on a call that was never available (RK1149).

    The address alone, and never a title. What a family is called is editorial and L4's to
    leave alone — the same reason `block add` takes the title `add` will not compose.
    """
    document = config.document(role)
    if sections._top_level(document, anchor) or document.schema.ref_scheme == "id":
        return None
    if sections._extends(document, anchor) is not None:
        return None
    # The address one segment up, which is what `section add` will look for and not find. A
    # one-segment anchor under the id scheme left above; here it means the file is an outline
    # and the anchor is a child, so there is always a segment to drop.
    parent = anchor.rsplit(".", 1)[0]
    return None if parent == anchor else parent


def _binding(config: Config, insertion: Insertion) -> Insertion:
    """Bind this line's id into the outline heading it just started naming (RK452).

    Under an outline the id in the heading is the binding (RK262), and two writes made it:
    `section add` renders it when a live line already points at the anchor, and
    `add --section` because it holds the line. Neither runs when the **design is written
    first**. `section add I.1 --title "…"` on an anchor nothing points at yet composes a
    heading naming no task, and the `add --ref I.1` that follows creates the pointer and
    never returns to the heading — so which of two writes came first decided whether the
    section ever belonged to anybody.

    The second order costs permanently and quietly: `ship` reports the section *kept*, as
    prose belonging to none, `lint` exits 0 on exactly that reading, and the rationale for
    shipped work stays in the prose file, which is what RK6 exists to stop. The recovery was
    a `section amend --title "<title> (<id>)"` derived from a field called `kept`, a round
    after the evidence had scrolled away.

    So the pointer write does from the other end what `section add` does, in the same
    transaction. Not a heuristic about the prose (RK236): the anchor is claimed by exactly
    the line that would have bound it had it been written first, and the rendering is
    :func:`~roadkeep.sections.amend`'s, so one function still writes a heading.

    Three states it leaves alone, and each is somebody else's answer. A heading that already
    names a task is :func:`~roadkeep.sections.owners`' `yes` and never overwritten. **Two
    live claimants is RK64's ambiguity and stays the author's**, as it does at `section add`
    — a binding chosen here would be this tool deciding whose design it is. And under
    `ref_scheme = "id"` there is no heading to bind, the anchor being the id already.
    """
    task = insertion.entry.task
    if config.schema.ref_scheme != "outline" or not task.ref:
        return insertion
    role = prose_role(config, on_disk=True)
    if role is None:
        return insertion
    document = config.document(role)
    section = sections.find(document, task.ref)
    if section is None or sections.owners(section, config.schema.id_pattern()):
        return insertion
    # Every *other* live line naming this anchor. One is RK64's ambiguity — the design the
    # author has to place — and the line just written is not one of them, its own claim being
    # the thing being rendered.
    claimants = [
        entry.task.id
        for entry in insertion.document.entries
        if entry.task.ref == task.ref and entry.task.id != task.id
    ]
    if claimants:
        return insertion
    # `bind` and not `section amend --title`: nobody asked for a title here, and a retitle
    # restyles the heading on purpose (RK388) — so routing through it would take the `§` an
    # author wrote as the silent price of a binding.
    prose = sections.bind(config.document(role), section, task.id)
    bound = sections.find(prose, task.ref)
    return replace(insertion, prose=prose, bound=bound)


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
        config.schema_for(role),
        task.ref,
        title,
        body,
        task,
        known=sections.known(config, task.ref, task),
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
    opens = _opens_the_family(config, role, task)
    placed = sections.add(
        config,
        role,
        task.ref,
        title,
        body() if callable(body) else body,
        task=task,
        opens=opens,
    )
    return replace(
        insertion,
        prose=placed.document,
        section=placed.section,
        opened=None if opens is None else opens[0],
    )


def _opens_the_family(config: Config, role: str, task: Task) -> tuple[str, str] | None:
    """The family a block's first `add --section` declares in the same write (RK1258).

    ``(anchor, title)``, or None wherever the call already runs as it stands — which is every
    `add` on a project under the id scheme, and every one into a block whose prose has started.

    Four conditions, and each of them is what keeps this from guessing. The anchor's
    **immediate parent** has to be the one thing missing (:func:`_unopened`), and it has to be
    a *top level*: a hole two generations deep is RK1208's refusal and stays one, because the
    address in between names a subtree whose title nobody has written. The block has to have
    **no family at all** — this is a block's first task by definition, and a block that already
    numbers its prose somewhere is a caller who typed the wrong numeral, which is a typo and
    not an opening. And the block's heading has to give a title, since that title is what the
    family takes.

    The title is the block's own and never composed (L4): a family under an outline is the
    block's prose, so the words are already written down one file over. Wrong words are
    `section amend <family> --title`, which is a door that exists — where composing them here
    would be the tool holding an opinion no verb could correct it out of.
    """
    from roadkeep.blocking import _title  # noqa: PLC0415 - RK260
    from roadkeep.history import families_of_block  # noqa: PLC0415 - RK260

    if not task.ref or (family := _unopened(config, role, task.ref)) is None:
        return None
    if "." in family or families_of_block(config, task.block):
        return None
    heading = config.document("roadmap").heading(task.block)
    if heading is None or not (title := _title(heading)):
        return None
    return family, title


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
    #: Every path this write took, projections included (RK1130) — the list a `git add --`
    #: takes, so the report a caller composes a commit from can name the file it refreshed.
    wrote: tuple[Path, ...] = ()

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

    def event(self, config: Config) -> dict[str, object]:
        """What this write did to the block it landed in (RK38), off the document it wrote."""
        from roadkeep.rendering import _event  # noqa: PLC0415 - RK260

        return _event(self.entry.task.id, self.entry.task.block, self.document, config)

    def stated(self, config: Config) -> str:
        """What the marker did, as a reader is told it (RK7, RK158).

        Beside :meth:`payload` since RK1170. The no-op reading is here too, and that is the
        point of moving it: a line that already carried the marker still followed its claim and
        still has a standing to report, which is one answer with a branch in it and not two.
        """
        from roadkeep.rendering import (  # noqa: PLC0415 - RK260
            _event_rows,
            _followed_rows,
            _staging_rows,
        )

        where = f"{config.relative(config.path('roadmap'))}:{self.lineno}"
        if not self.changed:
            rows = [f"{self.entry.task.id} is already {self.after}  {where}"]
            return "\n".join(
                rows + _followed_rows(self, config)
                + _event_rows(self.event(config), "  ", config=config)
            )
        rows = [f"{self.entry.task.id} {self.before} → {self.after}  {where}"]
        if self.refreshed:
            rows.append(f"  derived  {', '.join(self.refreshed)} (dep annotations re-derived)")
        rows += _followed_rows(self, config)
        rows += _staging_rows(config.relative(one) for one in self.wrote)
        rows += _event_rows(self.event(config), "  ", config=config)
        return "\n".join(rows)

    def payload(self, config: Config) -> dict[str, object]:
        """The same answer as data, with the claim this marker took or dropped (RK158)."""
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "id": self.entry.task.id,
            "from": self.before,
            "to": self.after,
            "changed": self.changed,
            "file": config.relative(config.path("roadmap")),
            "line": self.lineno,
            "rendered": self.rendered,
            "refreshed": list(self.refreshed),
            "claim": str(self.claim) or None,
            **_wrote_json(config, self.wrote),
            "event": self.event(config),
        }


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
            Whereabouts.of(config, task_id),
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
    wrote = derived.document.save()
    return StatusChange(
        wrote=wrote,
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
    #: Every path this write took, projections included (RK1130) — the list a `git add --`
    #: takes, so the report a caller composes a commit from can name the file it refreshed.
    wrote: tuple[Path, ...] = ()

    @property
    def changed(self) -> tuple[str, ...]:
        """Which fields actually differ, in field order — empty when nothing was written.

        **`requires` is one of them** (RK1311), and its absence here was the worse half of that
        defect: `amend <id> --requires console --why "<the sentence it already had>"` wrote the
        requirement onto the line and answered *unchanged: every field already reads that way*.
        Both cannot be true, and the one printed is the one that stops a caller retrying — it
        was visible at all only because the roadmap line was read straight afterwards.

        The field is what this walks and not a list somebody keeps in step: `amend` grew a
        fourth argument (RK1297) and this tuple was written when there were three.
        """
        return tuple(
            name
            for name in ("why", "deps", "requires", "ref")
            if getattr(self.before, name) != getattr(self.entry.task, name)
        )

    @property
    def was(self) -> dict[str, str | tuple[str, ...]]:
        """What each changed field said before, keyed by field name (RK1133).

        The reading this record held and did not answer. `status` reports `from` beside `to`
        and `restate` reports `was` beside `now`; an amend reported *which* fields moved and
        never their old values, so a client rendering one could show the new line and not the
        sentence it replaced — on `why`, the field this verb exists to correct.

        Only the fields in :attr:`changed`, because a field that did not move has no *before*
        to report: sending its current value under this name would let a reader show a diff
        where there is none. Deps are rendered as the line spells them, which is the one
        spelling every other payload here uses — a `Dep` is a record, and handing one to a
        client outside this process is the thing :data:`UNSENT` refuses for a document.
        """
        return {
            name: tuple(dep.render() for dep in self.before.deps)
            if name == "deps"
            else getattr(self.before, name)
            for name in self.changed
        }

    @property
    def rendered(self) -> str:
        return self.entry.raw

    def stated(self, config: Config) -> str:
        """What this correction did, as a reader is told it (RK65).

        Beside :meth:`payload` since RK1170, for the reason :class:`Restatement`'s pair is: both
        registers were in the handler, and a write verb's answer is what the transaction
        produced rather than something the door composes about it.
        """
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        where = config.relative(config.path("roadmap"))
        if not self.changed:
            return f"{self.entry.task.id} unchanged: every field already reads that way"
        rows = [
            f"{self.entry.task.id} amended  {where}:{self.entry.lineno}"
            f"  ({', '.join(self.changed)})",
            f"  {self.rendered}",
        ]
        if self.refreshed:
            rows.append(f"  derived  {', '.join(self.refreshed)} (dep annotations re-derived)")
        rows += _staging_rows(config.relative(one) for one in self.wrote)
        return "\n".join(rows)

    def payload(self, config: Config) -> dict[str, object]:
        """The same answer as data, carrying what each changed field said before (RK1133)."""
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "id": self.entry.task.id,
            "file": config.relative(config.path("roadmap")),
            "line": self.entry.lineno,
            "changed": list(self.changed),
            "rendered": self.rendered,
            # What each changed field said before (RK1133), beside which ones moved: `status`
            # answers `from`/`to` and `restate` answers `was`/`now`, and this was the one write
            # whose client could show the new line and nothing else.
            "was": {
                name: list(value) if isinstance(value, tuple) else value
                for name, value in self.was.items()
            },
            "refreshed": list(self.refreshed),
            **_wrote_json(config, self.wrote),
        }


def amend(
    config: Config,
    task_id: str,
    *,
    why: str | None = None,
    deps: Sequence[str] | None = None,
    requires: Sequence[str] | None = None,
    ref: str | None = None,
    lines: int | None = None,
) -> Amendment:
    """Correct one open line's `why`, `deps`, `requires` or `ref`. At input, or nothing (RK65).

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
            Whereabouts.of(config, task_id),
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
        # The whole group or nothing, exactly as `--dep` replaces its own (RK1297): a
        # requirement that no longer holds is removed by restating the ones that do, and a
        # flag that only ever added would leave a line nothing could ever offer again.
        requires=entry.task.requires
        if requires is None
        else read_requires(", ".join(requires)),
        ref=entry.task.ref if ref is None else ref,
    )
    if deps is not None:
        refuse_deps(config, backlog, wanted)
    # Derived on write like every other annotation (RK8): the author names the dep and the
    # tool states whether it shipped.
    updated = sections.checked(config, derive(backlog, wanted), schema=roadmap.schema)
    if updated == entry.task:
        return Amendment(document=roadmap, entry=entry, before=entry.task)
    # Asked after the no-op check, so an amend that alters nothing never demands a count for
    # a write it is not going to make. No `keeps_tail` here or at `restate` (RK1057): on the
    # roadmap the count authorises a deletion and only that, no multi-line task line being a
    # non-goal — so a wrapped line is a hand-written note the format is asserting over, and
    # offering to write it back would be offering the shape this file does not have.
    counted(
        task_id,
        config.relative(config.path("roadmap")),
        entry,
        lines,
        verb="correcting it",
    )
    derived = refresh(replace(backlog, roadmap=roadmap.rewrite_entry(entry, updated)))
    wrote = derived.document.save()
    return Amendment(
        wrote=wrote,
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
    #: Every path this write took, projections included (RK1130) — the list a `git add --`
    #: takes, so the report a caller composes a commit from can name the file it refreshed.
    wrote: tuple[Path, ...] = ()
    #: The anchor of the design that argues from the claim this call replaced (RK1196), where
    #: the pointer resolves to exactly one live section. Empty where it resolves to none or to
    #: two, which are a `lint` finding and not this verb's to settle — `deferring._carried`
    #: spells the same three outcomes at the door that keeps a section rather than naming it.
    design: str = ""
    #: Which prose role holds that anchor, so the follow-up names `--role` where the project's
    #: design does not live in the default file (RK196).
    design_role: str = ""

    @property
    def changed(self) -> bool:
        return self.before.symptom != self.entry.task.symptom

    @property
    def follow_up(self) -> tuple[str, ...]:
        """The edits the two other statements of the replaced claim need (RK1196).

        Composed once and read by both registers, which is what keeps the printed row and the
        payload from being two spellings of one answer (RK1170). Empty on a `--typo`, which is
        the caller declaring the claim was the one intended: a slip of the pen leaves the `why`
        and the design arguing the premise they were written for, so asking for two edits there
        would be the record describing a decision nobody took (RK414). Empty too where nothing
        changed, the file already stating this symptom.
        """
        if self.typo or not self.changed:
            return ()
        edits = [f"amend {self.entry.task.id} --why -"]
        if self.design:
            named = "" if self.design_role == "improvements" else f" --role {self.design_role}"
            edits.append(f"section amend {self.design}{named} --body -")
        return tuple(edits)

    @property
    def rendered(self) -> str:
        return self.entry.raw

    @property
    def lineno(self) -> int:
        return self.entry.lineno

    def stated(self, config: Config) -> str:
        """What this correction did, as a reader is told it (RK178, RK414).

        Beside :meth:`payload` since RK1170. Both registers were in the handler, which is where a
        write verb's answer least belongs: the record is what the transaction produced, and the
        door only chose which reading to print.
        """
        from roadkeep.rendering import _premise_rows, _staging_rows  # noqa: PLC0415 - RK260

        where = config.relative(config.path("roadmap"))
        if not self.changed:
            return f"{self.entry.task.id} unchanged: the line already states that symptom"
        rows = [
            f"{self.entry.task.id} restated  {where}:{self.lineno}",
            f"  was      {self.before.symptom}",
            f"  now      {self.entry.task.symptom}",
            f"  {self.rendered}",
            # Said out loud, because keeping them is the whole argument for the verb: the work
            # never changed, so nothing the history is keyed on moves.
            "  kept     the id, the deps and the section: the work never changed",
            # Which of the two acts it was (RK414): the default sentence claims a premise turned
            # out false, and printing that over a misspelt word is the record describing a
            # decision nobody took.
            "  spelling the claim is the one intended — a slip of the pen, not a false premise"
            if self.typo
            else "  claim    the premise this line asserted turned out to be false",
        ]
        # Said after the claim and before the staging line, which is the order the author acts
        # in: what this call did, then the two edits it did not (RK1196).
        rows += _premise_rows(self.follow_up, self.design)
        if self.refreshed:
            rows.append(f"  derived  {', '.join(self.refreshed)} (dep annotations re-derived)")
        rows += _staging_rows(config.relative(one) for one in self.wrote)
        return "\n".join(rows)

    def payload(self, config: Config) -> dict[str, object]:
        """The same answer as data, with both readings of the claim (RK178)."""
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "id": self.entry.task.id,
            "file": config.relative(config.path("roadmap")),
            "line": self.lineno,
            # Both readings, which is what makes this recorded rather than hidden: a reviewer
            # sees a claim replaced where a flag would show a word changing.
            "was": self.before.symptom,
            "now": self.entry.task.symptom,
            "changed": self.changed,
            # Which of the two acts this was (RK414), so a consumer counting how often a claim
            # actually moved is not counting spelling fixes with them.
            "typo": self.typo,
            # The two other places the replaced claim is written, as the doors that reach them
            # (RK1196) — empty on a typo and on a no-op, exactly as the printed rows are.
            "premise": {
                "design": self.design or None,
                "role": self.design_role or None,
                "next": list(self.follow_up),
            },
            "rendered": self.rendered,
            "refreshed": list(self.refreshed),
            **_wrote_json(config, self.wrote),
        }


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
            Whereabouts.of(config, task_id),
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
    wrote = derived.document.save()
    design, role = _arguing(config, updated)
    return Restatement(
        wrote=wrote,
        document=derived.document,
        entry=next(e for e in derived.document.entries if e.lineno == entry.lineno),
        before=entry.task,
        refreshed=tuple(name for name in derived.changed if name != task_id),
        typo=typo,
        design=design,
        design_role=role,
    )


def _body_aim(config: Config, anchor: str, role: str) -> str:
    """What a body under this anchor may weigh, before one is written (RK1309).

    `add`'s own help states the rule this closed: *a limit reported after the prose exists is
    a limit discovered too late to save the tokens it was meant to save*. The prose fields are
    exactly where it still landed — measured in pportal, 2026-08-22, at 266 words against 250,
    discovered by writing 266, with the retry carrying every word again.

    Through :func:`~roadkeep.budgeting.body_budget`, which is the reader the `budget` verb and
    the gate both use, so the number here and the refusal one call later cannot disagree. Any
    failure to price is silence rather than a broken `add`: the write has landed, and a row
    about a limit is not worth a traceback on top of it.
    """
    from roadkeep.budgeting import body_budget  # noqa: PLC0415 - RK260

    try:
        return body_budget(config, anchor, role).stated()
    except (KeyError, OSError, ValueError):
        return ""


def _body_weight(config: Config, anchor: str, role: str) -> dict[str, object] | None:
    """The same figure as data (RK1309), off the same reader as the row above it.

    :meth:`~roadkeep.budgeting.Body.payload` and not a shape composed here: the caller reaching
    this through the served answer is the one the whole pre-write read is for, and a second
    spelling of a limit is the drift this package exists to stop.
    """
    from roadkeep.budgeting import body_budget  # noqa: PLC0415 - RK260

    try:
        return body_budget(config, anchor, role).payload()
    except (KeyError, OSError, ValueError):
        return None


def _arguing(config: Config, task: Task) -> tuple[str, str]:
    """The one live section written from the claim this restatement replaced (RK1196).

    Resolved here rather than at either printer, because it is a fact about the transaction
    and not about the register it is read in — the shape `wrote` and `refreshed` already have.

    A pointer that resolves to nothing or to two files answers the empty pair, so the report
    names the `why` alone. Both are findings `lint` already holds and neither is this verb's
    to settle: a follow-up naming one of two ambiguous files would be a guess printed as an
    instruction, and `deferring._carried` declines the same guess at the door beside this one.
    """
    if not task.ref:
        return "", ""
    roles = sections.declaring(config, task.ref)
    return (task.ref, roles[0]) if len(roles) == 1 else ("", "")


def _refuse_sibling_status(config: Config, task_id: str) -> None:
    """Any other governed file carrying a marker for this id is the disagreement.

    Except the one shape the tool creates on purpose (RK121, RK1080, RK1114). `ship --part`
    writes an entry naming a half and *leaves the line open* at ⏳, so a ⏳ line beside a
    qualified ✅ is the two files agreeing rather than disagreeing — and refusing it closed the
    only door that starts work: measured on dockerdesk, `pick` named the line, `brief` called
    it ready, and `brief --claim` answered that status lives in exactly one file. It does; the
    roadmap holds it, and an id in the ledger is a finished task only when the line is gone.

    :attr:`~roadkeep.kernel.schema.Task.in_halves` and never a second test of the qualifier,
    which is where RK1080 folded the two readings this rule has: the gate skips the same pair
    for the same reason (`linting._carried`), and a door disagreeing with it would refuse a
    state the gate calls clean.
    """
    for role in ROLES:
        if role == "roadmap" or not config.has(role) or not config.path(role).is_file():
            continue
        found = config.document(role).by_id().get(task_id)
        if found is not None and not found.task.in_halves:
            raise StatusElsewhere(
                task_id,
                role,
                config.relative(config.path(role)),
                found.lineno,
                found.task.status,
            )


def refuse_reuse(config: Config, task_id: str, *, flag: str = "--id") -> None:
    """Refuse an id anything already mentions, anywhere (RK4).

    Public because every door that **moves a task onto** a number needs the same refusal,
    and an id rule with a second implementation is an id rule two commands can disagree
    about: `add` (RK5), `renumber` and `record renumber` all call this one. A mention is
    refused as well as a line, and that is right here: landing a task on a number some
    sentence already names silently re-points the sentence at work it was not about.

    ``flag`` is the one thing that is **not** shared (RK1212): the rule is one and the
    argument carrying the number is each verb's own, so the remedy is passed rather than
    assumed — `renumber` and `record renumber` take `--to`, and the sentence naming `--id` at
    them was a call the parser refuses, one step further down.

    :func:`refuse_occupied` is the *other* rule, for the door that gives a number the line
    it is missing rather than taking one over (RK1051). Two functions and not a flag,
    because they enforce different things — this one that a number is unspoken for, that
    one that no line holds it.
    """
    clash = next((ref for ref in scan(config) if ref.id == task_id), None)
    if clash is not None:
        raise IdInUse(task_id, config.relative(clash.path), clash.lineno, flag=flag)


def refuse_occupied(config: Config, task_id: str) -> IdRef | None:
    """Refuse an id a **line** holds, and hand back the mention it tolerates (RK1051).

    Measured in Shio: one ledger entry recorded two shipped tasks, so the second had no
    entry of its own — invisible to `show`, to both counts, and reported by the gate as a
    broken promise. `record add --id` is the repair, and it refused, because that id
    occurred **eight** times: its own half, plus seven entries citing its rule. The guard
    was inverted for exactly this case — the better documented a decision is, the less
    repairable its record — and the rule was never at stake, since nothing is being
    *reused* by an id that has no line.

    So the question asked here is :func:`~roadkeep.ids.carried`'s, which is the parse's and
    not the scan's: does some governed file hold this id as a task, an entry or a paused
    line, or has the project reserved it? Any of those is an allocation and is refused with
    the same :class:`IdInUse` as ever. A bare mention is **returned**, never swallowed: the
    caller reports it, because writing the line a sentence promised is the good case and
    writing one it did not is a fact the author has to see.
    """
    occurrences = [ref for ref in scan(config) if ref.id == task_id]
    if task_id not in carried(config):
        return occurrences[0] if occurrences else None
    # The address is the *line's* and not the first mention's: a refusal is read by
    # somebody about to click it, and sending them to a sentence citing the id when a
    # task line holds it names the wrong file for the wrong reason.
    holders = {
        config.path(role)
        for role in CARRIERS
        if config.has(role) and config.path(role).is_file()
    }
    clash = next(
        (ref for ref in occurrences if ref.path in holders),
        occurrences[0] if occurrences else None,
    )
    raise IdInUse(
        task_id,
        config.relative(clash.path) if clash else config.relative(config.source or config.root),
        clash.lineno if clash else 0,
    )


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
    asked one task earlier, and the refusal is :class:`~roadkeep.kernel.document.UnknownBlock`
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
    command: see :class:`~roadkeep.kernel.document.UnknownBlock`.
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


def _refuse_retired(config: Config, task: Task) -> None:
    """Refuse a line whose pointer names an address a ship already took (RK1177).

    The same rule and the same reader as `section add`'s own refusal, asked one command earlier.
    Nothing is duplicated: this calls what that verb calls, so the sentence a caller gets and the
    address it recommends are the one answer — and a project whose history cannot be read is
    silent here exactly as it is there, because what is lost is a refusal and never a file.

    Silent under ``ref_scheme = "id"``, where the pointer is the id and reuse is `refuse_reuse`'s
    question one file over — a second opinion about a closed one would fire on every `add`.

    Only a **retired** address: a pointer at a section that exists is how every task after the
    first cites its own design, and one at an address nobody ever used is the normal case this
    tool derives.
    """
    if task.ref is None or not task.ref:
        return
    from roadkeep.sections import PROSE_ROLES, _refuse_reuse  # noqa: PLC0415 - RK260

    for role in PROSE_ROLES:
        if config.has(role):
            _refuse_reuse(config, role, task.ref, config.relative(config.path(role)))
            return
