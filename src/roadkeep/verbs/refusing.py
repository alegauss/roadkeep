"""The three exit codes, and the one place a raised error becomes one (RK494).

What every handler ends with, so it is what they may not each spell: 0 success, 1 the gate
says no, 2 usage or configuration — the contract :mod:`roadkeep.cli`'s own rules state, held
in the module a verb can import without importing the command surface.

:data:`REFUSALS` is listed once for the same reason it always was: fourteen writing commands
catch the same set, so adding a class to it is one edit rather than fourteen and thirteen of
them enough.
"""

from __future__ import annotations

import sys

from roadkeep import provenance
from roadkeep.kernel.document import RoundTripError, StaleFile
from roadkeep.kernel.schema import SchemaError


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


def _retrying(error: Exception) -> str | None:
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
    return Door(
        argv=tuple(argv), what="the same call, with the address it was refused for"
    ).quoted


def _foreseeing(error: SchemaError) -> list[str]:
    """The read that would have refused this without writing, at most once (RK1435).

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
        door = foreseen(violation.code)
        if door is not None:
            return [f"foresee  {provenance.invocation()} {' '.join(door.argv)}  ({door.what})"]
    return []


def _refused(error: Exception) -> int:
    """One error path for every command that writes. The exit code is the contract.

    And the one place the exception still exists, so it is where the modules that decided it are
    recorded (RK267): below here there is a printed line and an exit code, and a surface reading
    those cannot tell a `why.too-long` from `schema.py` apart from a `ref.missing` from
    `sections.py`. Free on this path — a refusal is already the slow branch — and read by nothing
    a terminal reaches.
    """
    provenance.witness(error)
    if isinstance(error, SchemaError):
        # Every violation at once, each naming its limit: a refusal that reports one
        # problem per run turns a single fix into a conversation.
        print("roadkeep: refused, nothing written:", file=sys.stderr)
        if error.beside:
            # First, and above the fields (RK1256): it is the half a caller cannot fix by
            # editing prose, so a reader who stops at the first line has stopped at the one
            # that decides whether the rest is worth rewriting.
            print(f"  {error.beside}", file=sys.stderr)
        if error.about:
            # Above the fields for the same reason and a narrower one (RK1262): it says which
            # argument the rows below are about, and a reader who reads them first has already
            # started editing the wrong one.
            print(f"  {error.about}", file=sys.stderr)
        for violation in error.violations:
            print(f"  {violation}", file=sys.stderr)
        for row in _foreseeing(error):
            print(f"  {row}", file=sys.stderr)
        retry = _retrying(error)
        if retry is not None:
            print(f"  retry    {retry}", file=sys.stderr)
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
    print(f"roadkeep: {message}", file=sys.stderr)
    # The other refusal that computed an address (RK1149): a `section add` onto one a shipped
    # entry's prose still cites, whose remedy sentence names the free child. Here and not only in
    # the SchemaError branch, because that is where `SectionExists` arrives — a ValueError.
    retry = _retrying(error)
    if retry is not None:
        print(f"  retry    {retry}", file=sys.stderr)
    return EXIT_USAGE
