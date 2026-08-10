"""Which governed bytes a verb actually left, so an approved shell write is recorded (RK175).

RK128 closed the *silence* at the shell boundary: a `Bash` command naming a governed path is
surfaced and the user answers. What it could not close is what happens after they say yes.
`review` (RK60) then runs `lint` narrowed to the lines the turn changed, and a hand-edit
producing a **conforming** line passes every one of those checks — the annotations are right
because nothing was inserted, the pointer resolves because the anchor existed, and a reworded
`why` is a legal `why`. The file changed, no verb wrote it, and every gate agrees it is correct.

RK128's third option was to compare the governed files against `git` and refuse a change no
verb made. That is not what this does, for the reason the option was left open: a user who
approved a `sed` made a choice, and re-litigating it at the end of the turn spends the
approval the `ask` exists to collect. The defect in the symptom is narrower and it is real —
**no record of who wrote it** — so what is built is the record, not a second refusal.

The mechanism is one digest per governed file, taken where every write already passes:

* **The baseline is the last verb, not `HEAD`.** Against `HEAD` this would report the whole
  turn's legitimate work — every `add` and every `ship` — and a report that fires on the
  normal path is one nobody reads. Against what the last verb left, the only thing that
  differs is bytes that arrived some other way, which is exactly the claim being made.
* **Recorded in :func:`roadkeep.cli.dispatch`, under the lock.** One choke point, and the
  one both surfaces share: the MCP server dispatches parsed args in-process and never goes
  through `main` (RK24), so a record kept anywhere else is one the write path walks around.
  A query never attests, which is what keeps a `list` between two hand-edits from silently
  adopting the second one as the baseline.
* **Not a second store (L2), and not a lock.** It holds no fact about any task: it is a
  digest, it lives in the temp directory beside the write lock (RK117) and the claim
  registry (RK119) under the same resolved-root key, and deleting it while nothing is
  running loses nothing — every file simply reads as attested until the next verb runs.

Two rules that keep it honest. **Every failure is silence**, on the guard's own argument
(:mod:`roadkeep.guarding`): an unreadable sidecar must not block a turn, and `lint` still
judges the file. And **reporting re-baselines** — the current bytes become the new record —
so one unattested change is stated once and the turn ends on the next attempt, rather than
the same fact blocking every turn until somebody commits.

Which is what :func:`survey` is for (RK200). Re-baselining makes the `Stop` block a report a
turn receives once and can never ask for again, so the question "which governed files did no
verb write" had exactly one answer at exactly one moment — the arrangement RK161 ended for
claims, and L5 says every question is a command. It reads the same two dictionaries and
**moves nothing**: a query that changed the answer to the next query would launder the write
this module exists to name, which is the rule a query already obeys here. The three states are
what the pair of dictionaries actually says — recorded and equal, recorded and different, or
never recorded, the last being the silence :func:`unattested` returns and not a finding.

What this cannot say is *who*. There is no owner here for the same reason there is none on a
claim: the identity behind a write lives outside the repository, and the commit is where it
belongs. The claim made is only that the bytes were not put there by a verb.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from roadkeep.config import Config
from roadkeep.provenance import served_by
from roadkeep.remedying import Door
from roadkeep.storing import Store, path, read, write

#: What this module's rows are called inside the shared store (RK330). One file beside the
#: lock, one grammar, and this is the table — a second encoding for a second sidecar was
#: what made a fourth feature's fourth encoding the obvious next move.
TABLE = "writes"


@dataclass(frozen=True, slots=True)
class Unattested:
    """The governed files whose current bytes no verb wrote."""

    #: Role and path, as this project spells it — a report quoting an absolute path is a
    #: report about one machine.
    files: tuple[tuple[str, str], ...]
    #: The prefix this session's tools arrive under, or `""` where it has none (RK479). The
    #: same field :class:`~roadkeep.guarding.Review` carries, and this was the last of the
    #: four messages that block a turn still naming one route for every session — on the one
    #: that is shown *once*, because reporting re-baselines. A field and not a call: one hook
    #: process serves every repository a session touches, so it is a fact about this project.
    served: str = ""

    def __str__(self) -> str:
        named = ", ".join(path for _, path in self.files)
        plural = "s" if len(self.files) > 1 else ""
        return "\n".join(
            [
                f"{named} changed since the last roadkeep verb wrote {'them' if plural else 'it'}, "
                f"so whatever produced the current bytes was not one — an approved shell "
                f"command, an editor, or a checkout. The line{plural} may be perfectly valid; "
                f"what was missing is any record of who wrote {'them' if plural else 'it'}, "
                f"and this is that record.",
                "",
                "Nothing is undone and nothing is asked back: the approval stands. Say which "
                "command changed the file and end the turn again — this blocks once, and the "
                "bytes that are there now are the new baseline.",
                "",
                # The second clause names no route on purpose: the refusal it points at has
                # spelled both since RK24, so this line has one command to get right — and
                # since RK488 it does not spell that one either, `Door.named` being the one
                # reader of which spelling this session has.
                f"`{Door(('lint',), '').named(self.served)}` judges the format; the verbs "
                f"that write it are in the refusal every governed edit already prints.",
            ]
        )


def attest(config: Config) -> None:
    """Record every governed file as the verb that just ran left it.

    Called for its effect and never for an answer, so it raises nothing: a temp directory
    that cannot be written is a missing record, not a failed write.
    """
    _store(config, _digests(config))


def unattested(config: Config) -> Unattested | None:
    """The governed files whose bytes differ from what the last verb left, or ``None``.

    Silence where nothing was ever recorded: a checkout in which no verb has run this
    session has no baseline to differ from, and reporting every file in it would report the
    history the project arrived with rather than anything this turn did.
    """
    recorded = _recorded(config)
    if not recorded:
        return None
    current = _digests(config)
    found = tuple(
        (role, config.relative(path))
        for role, path in config.paths.items()
        if role in recorded and recorded[role] != current.get(role)
    )
    if not found:
        return None
    _store(config, current)
    return Unattested(files=found, served=served_by(config.root))


class State(StrEnum):
    """What the record says about one governed file (RK200).

    Three, because the digest sidecar holds one thing and means three: a role it never
    recorded is not a file that drifted, and reporting the two as one figure would count the
    history a fresh checkout arrived with as something this turn did.
    """

    #: The bytes on disk are the ones the last verb left.
    ATTESTED = "attested"
    #: They are not — an approved shell command, an editor, or a checkout. The row to act on.
    UNATTESTED = "unattested"
    #: No verb has run against this role, so there is nothing to differ from. Not a finding.
    UNRECORDED = "unrecorded"


#: Unattested first: the axis a reader is scanning is what to act on, and the one row worth a
#: second look is the one a listing must not bury under the files that are fine.
_ORDER = (State.UNATTESTED, State.UNRECORDED, State.ATTESTED)


@dataclass(frozen=True, slots=True)
class Attested:
    """One governed file as the record and the disk together describe it (RK200)."""

    role: str
    #: As this project spells it — a report quoting an absolute path is one about a machine.
    path: str
    state: State
    #: Whether the file is on disk at all: an absent one is `attested` where the record agrees
    #: it is absent, and that reads as agreement rather than as a file nobody can find.
    present: bool


def survey(config: Config) -> tuple[Attested, ...]:
    """Every declared role against the record, the rows to act on first (RK200).

    The read :func:`unattested` was not. It takes no lock and **writes nothing** — the same
    rule a query already obeys here, and the one thing that separates asking from the `Stop`
    block, which consumes the fact it reports. Silence is not one of its answers either: a
    checkout where no verb has run says so, per role, rather than returning nothing and
    leaving the caller to guess whether that meant clean.
    """
    recorded = _recorded(config)
    current = _digests(config)
    rows = [
        Attested(
            role=role,
            path=config.relative(path),
            state=_state(role, recorded, current),
            present=current.get(role) is not None,
        )
        for role, path in config.paths.items()
    ]
    return tuple(sorted(rows, key=lambda row: _ORDER.index(row.state)))


def _state(
    role: str, recorded: dict[str, str | None], current: dict[str, str | None]
) -> State:
    if role not in recorded:
        return State.UNRECORDED
    return State.ATTESTED if recorded[role] == current.get(role) else State.UNATTESTED


def record_path(root: Path | str) -> Path:
    """Where this checkout's digests live — in the shared store, outside the repository."""
    return path(root)


def _digests(config: Config) -> dict[str, str | None]:
    """One digest per declared role, ``None`` for a file that is not on disk.

    Absence is a value and not a gap: a governed file *deleted* by a shell command is the
    change this most wants to state, and a dictionary that simply omitted it would read as
    agreement with whatever was recorded before.
    """
    out: dict[str, str | None] = {}
    for role, path in config.paths.items():
        try:
            out[role] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        except OSError:
            out[role] = None
    return out


def _recorded(config: Config) -> dict[str, str | None]:
    """The digests the last verb left, out of the shared store's own table (RK330)."""
    return dict(read(config.root).writes)


def _store(config: Config, digests: dict[str, str | None]) -> None:
    """Replace this module's table, and leave the claims beside it exactly as they were.

    Read-modify-write under the checkout's exclusive lock, which is where every writer of
    the store runs (:func:`roadkeep.cli.dispatch`) — and where this one in particular runs,
    the record being taken after the handler and before the lock is given up.
    """
    write(config.root, Store(claims=read(config.root).claims, writes=digests))
