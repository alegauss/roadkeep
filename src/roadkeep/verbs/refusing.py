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
from roadkeep.document import RoundTripError, StaleFile
from roadkeep.schema import SchemaError


EXIT_OK = 0
EXIT_GATE = 1
EXIT_USAGE = 2


#: What a write may fail with, listed once because every writing command catches the same
#: set and :func:`_refused` decides the code. Written out at fourteen call sites, adding
#: :class:`StaleFile` (RK116) to the tuple would have been fourteen edits and thirteen of
#: them enough — a command that missed it would print a traceback instead of a refusal.
REFUSALS = (RoundTripError, StaleFile, KeyError, ValueError, OSError)


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
        for violation in error.violations:
            print(f"  {violation}", file=sys.stderr)
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
    return EXIT_USAGE
