"""The three exit codes, and the one place a raised error becomes one (RK494).

What every handler ends with, so it is what they may not each spell: 0 success, 1 the gate
says no, 2 usage or configuration — the contract :mod:`roadkeep.cli`'s own rules state, held
in the module a verb can import without importing the command surface.

:data:`REFUSALS` is listed once for the same reason it always was: fourteen writing commands
catch the same set, so adding a class to it is one edit rather than fourteen and thirteen of
them enough.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from roadkeep import provenance
from roadkeep.kernel.document import RoundTripError, StaleFile
from roadkeep.kernel.schema import SchemaError

if TYPE_CHECKING:  # RK260 — the runtime import stays inside `_retrying`, where it always was
    from roadkeep.remedying import Door


EXIT_OK = 0
EXIT_GATE = 1
EXIT_USAGE = 2


#: What a write may fail with, listed once because every writing command catches the same
#: set and :func:`_refused` decides the code. Written out at fourteen call sites, adding
#: :class:`StaleFile` (RK116) to the tuple would have been fourteen edits and thirteen of
#: them enough — a command that missed it would print a traceback instead of a refusal.
REFUSALS = (RoundTripError, StaleFile, KeyError, ValueError, OSError)


#: Where a refusal that computed an address keeps it. Two names and not one field: the first is
#: a channel the kernel declares for the layer above it (`SchemaError.offered`), the second is a
#: refusal class's own answer that its callers and its tests already read (`SectionExists.free`).
#: Both are addresses this tool derived while explaining why it refused, which is the whole
#: population RK1149 is about — and a third one is a row here rather than a second function.
_OFFERS = ("offered", "free")


def beneath(said: str) -> None:
    """Write one line to **stderr** that has to land under what stdout already holds (RK1612).

    Off a terminal, Python buffers stdout fully and leaves stderr unbuffered, so a verb that
    prints an answer and then a note into one pipe emits them in the wrong order: the note
    arrives above the report it is about, and a line out of order is a line misread.

    A function and not a discipline, which is the whole of this task. Two callers had worked it
    out separately — `cli._may_offer`, whose comment says why, and `verbs.adopting._report`,
    which carried a bare `sys.stdout.flush()` with nothing saying why at all. A rule discovered
    twice and written down neither time is a rule that gets discovered a third time.

    Swept before the repair: 34 functions in this package print to both streams and 2 flushed
    between them. That number is loose on purpose — most of the 34 write an answer *or* a
    refusal, which are mutually exclusive and need nothing — and no scan separates the set that
    writes both in one run, which is exactly the set this is for. So the deliverable is the
    seam, and a caller that goes through it cannot get the order wrong.

    Only where stdout is a **pipe** is the flush load-bearing; at a terminal it is line
    buffered and the order is already right. Done unconditionally anyway: a flush on an empty
    buffer costs nothing, and a rule that fires only in the case nobody tests by hand is the
    rule this exists to take out of two heads.
    """
    sys.stdout.flush()
    print(said, file=sys.stderr)


@dataclass(frozen=True, slots=True)
class _Retry:
    """The caller's own call, and the one token in it this tool derived (RK1600).

    A pair because the payload needs both halves and the sentence needs one. RK1149 composed
    the call and rendered it into a row; the row is prose, and the argv inside it is the one
    part of a refusal a reader executes rather than reads — so an agent wanting the command
    parsed a paragraph to find it, which is the arrangement RK1584's payload was added to end
    one row further down.
    """

    door: Door
    #: The address this tool derived while explaining the refusal — the one token that differs
    #: from what the caller typed. Published beside the argv rather than left to be diffed:
    #: it is the whole content of the retry, and a consumer holding only the call would have
    #: to compare it against its own to learn what this run worked out.
    address: str

    def payload(self) -> dict[str, object]:
        """``argv`` as a list, because every argv this package publishes goes on the wire as
        one — a consumer runs it (RK1324).

        Its **own** key and not `doors`, which is that rule's own permitted exception: a door
        is a command this tool composed for a caller to choose, and this is the caller's
        command with one token replaced — they already chose it. The distinction is not
        academic, because the same refusal can carry the `foresee` read as well, and a flat
        list would leave a consumer unable to tell *run this instead* from *run this first
        next time*. `what` is dropped for the same reason: a remedy door's sentence says what
        choosing it means, and here there is nothing to choose.
        """
        return {"argv": list(self.door.argv), "address": self.address}


def _retrying(error: Exception) -> _Retry | None:
    """The caller's own call with the address it was refused for, or ``None`` (RK1149).

    `lint` findings have carried a door since RK15 — the command, pre-filled — and a write
    refusal carried prose alone. Two of them had already *done the work*: the free anchor is
    computed to explain the rule and then handed over as a sentence to read, extract and retype
    into an otherwise identical call. Measured on a project on the outline scheme: seven tasks
    filed, five refused first for exactly this, five retries carrying no new information.

    Two conditions, and both are absences rather than judgements. No offered address — which is
    every refusal about anything else, and the two anchor cases that decline to guess (RK360) — is
    nothing to substitute. And **no recorded argv is a caller that made none**: the MCP server
    dispatches a parsed namespace (RK24), so there is no call of theirs to hand back, and the
    served `add` withholds `--ref` anyway — under an id scheme it is derived — which is why the
    sentence there names `anchors`, a read that surface does serve (RK444, RK463). That the slot
    is *empty* rather than stale is `serving`'s to guarantee, and it clears it where a call begins.

    **The address the caller typed is replaced wherever it sits**, which is one rule for two
    shapes: `--ref XXIII.7` on a task line and the bare positional `section add XXIII.7`. The
    second refusal is the one RK1149 measured as worse than the first — the address is burnt, the
    author had no way to know, and the retry is the same call one token different. Where nothing
    matches, nothing was typed, and the flag is appended.

    A `Door`, so the spelling is the one every other command's remedy uses (RK254) — this engine
    as this machine can reach it, and never a console script no `pip install` put on PATH. Quoted,
    this being the first door whose argv carries the caller's own prose: a symptom and a why with
    spaces and apostrophes in them, and an unquoted line is one that runs as eight arguments.

    Returned **with the address that was substituted** since RK1600, and no longer as the shell
    line: the row wants the quoting and the payload wants the list, and a function answering in
    the rendered string left the second to re-derive what this one had. See :class:`_Retry`.
    """
    from roadkeep.provenance import invocation_argv  # noqa: PLC0415 - RK260
    from roadkeep.remedying import Door  # noqa: PLC0415 - RK260

    offered = next((getattr(error, one, "") for one in _OFFERS if getattr(error, one, "")), "")
    if not offered:
        return None
    argv = list(invocation_argv())
    if not argv:
        return None
    # **Which token the address replaces is the error's to say** (RK1378). Every refusal here
    # until now offered an address for the one the caller *spent* — `anchor` — so substituting
    # it was one rule. `NotASibling` offers one for the **destination**: the source is where the
    # heading is and the free child is where it may go, so replacing the anchor composes a call
    # that moves a different section to the address just refused. Read off `to` first, and only
    # where the error carries one, which no other refusal in `_OFFERS` does.
    destination = getattr(error, "to", "")
    burnt = getattr(error, "anchor", "")
    if destination and destination in argv:
        argv[argv.index(destination)] = offered
    elif burnt and burnt in argv:
        argv[argv.index(burnt)] = offered
    elif "--ref" in argv:
        at = argv.index("--ref")
        argv[at + 1 : at + 2] = [offered]
    else:
        argv += ["--ref", offered]
    return _Retry(
        Door(argv=tuple(argv), what="the same call, with the address it was refused for"),
        offered,
    )


def _foreseeing(error: SchemaError) -> Door | None:
    """The read that would have refused this without writing, at most once (RK1435).

    A `Door` and no longer a row since RK1642. It composed the sentence and returned it, so
    the read was in `said` and in no field of the payload — leaving a caller reading fields
    with the rule that refused and not the command that would have made the refusal
    unnecessary, which is the half RK1600 published for the retry and left here.

    A refusal teaches the verb whose **absence** caused a visible failure, and teaches nothing
    about the verb whose whole purpose is that the failure never happens — so a session learns
    `section add` in one round trip and finds `budget` on its last day, from `--help`, twenty
    refusals later. This is the one surface where that is fixable: the caller is reading it
    because their write just failed, which is the moment the preventive read is worth having.

    **One row, whatever the batch.** A `SchemaError` carries every violation on purpose, and a
    refusal that grew a teaching line per field would bury the diagnosis it is attached to
    under advice about the same command said four ways. The first violation that has a read
    decides which one, so the row is about the field the reader is already looking at.

    Silent where nothing predicts it, which is most refusals: a duplicate id, a dep nothing
    satisfies and a marker the project does not declare are all states no draft measurement
    would have caught, and a row offering one is the advice RK16 refuses.
    """
    from roadkeep.remedying import foreseen  # noqa: PLC0415 - RK260

    for violation in error.violations:
        # With the ceiling that refused (RK1538): a `why` inside its own maximum and a `why`
        # a full line refused are two states, and the read that prevents the second prices
        # the line — the first was being offered on both, and says the draft fits.
        door = foreseen(violation.code, violation.bound)
        if door is not None:
            return door
    return None


def _payload(
    error: Exception,
    said: str,
    retry: _Retry | None = None,
    foresee: Door | None = None,
) -> None:
    """The refusal as data on stdout, where the caller asked for data (RK1584).

    **The one answer this package published as prose alone.** `add --json`, `lint --json` and
    `brief --json` all answer a caller in fields; a refused call printed nothing to stdout and
    left the diagnosis on stderr as English — so an agent that needs which field, which rule or
    which of two ceilings matched a sentence, which is the reading RK1503 was filed to remove
    and then left where nothing structural could reach it.

    Read off a slot this run recorded and not threaded through eighty-one call sites (under
    RK1149's rules): the register asked for is a fact about the invocation, `asked_fields` is
    written before dispatch and read only where a refusal is being rendered, and a parameter
    would be one edit per handler and eighty of them enough.

    Its **own** slot since RK1613, and that is the whole of that task. This read `--json` out of
    `invocation_argv`, which is a different question — what the caller typed, so a retry can
    hand the call back — and the served surface empties that one deliberately, having no call of
    the caller's to offer. So the payload was published at a terminal, whose reader parses prose
    already, and withheld from the agent it was filed for.

    **Beside the text and never instead of it.** The transport's own argument is that the
    refusal an agent reads over MCP is byte-identical to the one a terminal reads, so this adds
    a channel rather than replacing one — `said` is the whole sentence, published so a caller
    that has the payload has not lost the prose it came from. The exit code stays the contract:
    this is what a caller reads *after* it has decided.

    **And the retry, which was in `said` and nowhere else** (RK1600). That is the one part of a
    refusal a reader executes rather than reads, so a payload carrying the rules and the
    sentence and not the command left an agent parsing a paragraph for the row RK1149 had
    already composed. `absent` and never `"retry": null` — the rule `rendering._reading_door`
    states for a door: a consumer reading the key at all is one that acts on it, and a null is
    a row it has to test first. Most refusals have none, which is a fact about them and not a
    field they are missing.

    **And the other command in the same refusal** (RK1642). A refused write can print two, and
    they are not the same offer: the retry is the caller's own call with one token replaced —
    they already chose it — and the `foresee` read is the command that would have refused the
    same draft *without writing*, which is a choice. So it goes under `doors`, which is
    RK1324's rule for every payload publishing a runnable command, and the retry keeps the
    exception RK1600 argued for it. `Door.payload()` says the rest — what it is for, whether
    it writes, and that its argv is **incomplete**: `<draft>` is the caller's prose, so the row
    is a template, and a consumer that ran it verbatim would be asking about a literal.
    """
    if not provenance.asked_fields():
        return
    from roadkeep.kernel.schema import SchemaError as _SchemaError  # noqa: PLC0415 - RK260

    payload: dict[str, object] = (
        error.payload() if isinstance(error, _SchemaError) else {"refused": [], "beside": "", "about": ""}
    )
    offer: dict[str, object] = {"retry": retry.payload()} if retry is not None else {}
    # A list of one, and always a list (RK1324): one name and one shape wherever a payload
    # publishes a runnable command, so a consumer reads them with one loop.
    #
    # No `served` prefix, and the reason is this path rather than the door: `served_by` takes
    # a root and a refusal is rendered where the project has gone out of scope — the argv is
    # what every consumer before RK449 reads anyway, and discovering a tree here to name a
    # tool would be a filesystem read on the error path.
    if foresee is not None:
        offer["doors"] = [foresee.payload()]
    print(json.dumps({**payload, **offer, "said": said}, indent=2))


def _refused(error: Exception) -> int:
    """One error path for every command that writes. The exit code is the contract.

    And the one place the exception still exists, so it is where the modules that decided it are
    recorded (RK267): below here there is a printed line and an exit code, and a surface reading
    those cannot tell a `why.too-long` from `schema.py` apart from a `ref.missing` from
    `sections.py`. Free on this path — a refusal is already the slow branch — and read by nothing
    a terminal reaches.

    It is also where the **payload** is published (RK1584), for the same reason: this is the
    last place the structure exists, and every writing command already ends here.
    """
    provenance.witness(error)
    if isinstance(error, SchemaError):
        # Every violation at once, each naming its limit: a refusal that reports one
        # problem per run turns a single fix into a conversation.
        #
        # Collected before it is printed (RK1584), so the payload beside it carries the same
        # sentence rather than a second rendering of the same facts — one composition, two
        # channels, which is the arrangement `Schema.render` holds one layer down.
        rows = ["roadkeep: refused, nothing written:"]
        if error.beside:
            # First, and above the fields (RK1256): it is the half a caller cannot fix by
            # editing prose, so a reader who stops at the first line has stopped at the one
            # that decides whether the rest is worth rewriting.
            rows.append(f"  {error.beside}")
        if error.about:
            # Above the fields for the same reason and a narrower one (RK1262): it says which
            # argument the rows below are about, and a reader who reads them first has already
            # started editing the wrong one.
            rows.append(f"  {error.about}")
        rows += [f"  {violation}" for violation in error.violations]
        foresee = _foreseeing(error)
        if foresee is not None:
            rows.append(
                f"  foresee  {provenance.invocation()} {' '.join(foresee.argv)}  "
                f"({foresee.what})"
            )
        retry = _retrying(error)
        if retry is not None:
            rows.append(f"  retry    {retry.door.quoted}")
        said = "\n".join(rows)
        print(said, file=sys.stderr)
        _payload(error, said, retry, foresee)
        return EXIT_USAGE
    if isinstance(error, (RoundTripError, StaleFile)):
        # The file drifted before this command ran, so the gate says no: normalizing a
        # line the parser may have misread is the corruption L3 forbids — and a file that
        # moved between the read and the write is the same refusal one layer down (RK116),
        # where what would be lost is somebody else's line rather than this one's shape.
        print(f"roadkeep: {error}", file=sys.stderr)
        return EXIT_GATE
    # KeyError renders its message in quotes, which reads as a stray token in a report.
    message = error.args[0] if isinstance(error, KeyError) else error
    rows = [f"roadkeep: {message}"]
    # The other refusal that computed an address (RK1149): a `section add` onto one a shipped
    # entry's prose still cites, whose remedy sentence names the free child. Here and not only in
    # the SchemaError branch, because that is where `SectionExists` arrives — a ValueError.
    retry = _retrying(error)
    if retry is not None:
        rows.append(f"  retry    {retry.door.quoted}")
    said = "\n".join(rows)
    print(said, file=sys.stderr)
    # With an empty `refused` and not with a key omitted (RK1584): a refusal this class raises
    # carries a sentence and no rules, and `[]` says *no violation decided this* where a
    # missing key says only that somebody did not write one. The retry goes the other way
    # (RK1600) and for the reason that distinction states: `[]` is an answer to *which rules
    # decided this*, and there is no comparable question a null retry would be answering.
    _payload(error, said, retry)
    return EXIT_USAGE
