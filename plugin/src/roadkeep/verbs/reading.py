"""Prose on the way in: a pipe, a path, and the encoding both are read under (RK494).

Three things a verb needs before it has anything to validate, and one module because they
are one act: a paragraph arrives on stdin (RK9) or by path (RK381), and either way it is
read under an encoding this process had to force — the default Windows console encoding is
cp1252, and a substituted character round-trips out of the file it lands in (L3).

:func:`harden` is where the `global` lives now. `main` used to set that flag in `cli`'s own
namespace and every reader of it sat alongside; with the readers here the write belongs here
too — one process, one answer, and the module that answers is the module that decides.
"""

from __future__ import annotations

import codecs
import io
import re
import sys
from collections.abc import Callable
from pathlib import Path

from roadkeep.authoring import Rereadable


def _verbatim(path: Path) -> str:
    """One of git's three versions, read the way `Document.load` reads a governed file."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


#: The spelling every prose argument here reads as "take it off the pipe". One string, for
#: :attr:`~roadkeep.serving.Prose.sentinel`'s reason: a second would be a second thing to know.
STDIN = "-"


#: The line terminators a pipe adds and nobody typed (RK329). All of them, so a file
#: ending in a blank line reads as the sentence it holds — and nothing else, so a trailing
#: space stays the author's and stays refused.
_TRAILING_NEWLINES = re.compile(r"[\r\n]+\Z")

#: The byte order mark an encoder writes ahead of the stream, which nobody typed (RK1023).
_BOM = "﻿"


def _unmarked(text: str) -> str:
    """A stream's first character, less the mark its encoder opened with (RK1023).

    Windows PowerShell 5.1 pipes to a native command through `$OutputEncoding`, whose UTF-8
    encoder emits a preamble — so the first character this tool reads is U+FEFF, and
    `char.invisible` refuses the field. The refusal is correct about the codepoint and wrong
    about who wrote it, and it then names *stdin* as the remedy for a byte stdin added:
    the author is told to take the route they already took, and nothing in their command
    names the encoding that put it there. `$OutputEncoding = UTF8Encoding.new($false)` does
    not help either, which is what makes this the reader's to fix.

    **One, and only at position 1.** A mark there is a byte order mark doing its job; the
    same codepoint anywhere else in the sentence is prose that no keyboard produces, and the
    scan that refuses it is untouched. `str.removeprefix` is that distinction exactly, and
    the reason this is not `utf-8-sig`: a codec would eat one wherever a read began, and the
    governed files are read by `Document`, where a stripped byte is a file that stopped
    round-tripping (L3).
    """
    return text.removeprefix(_BOM)


def _piped(value: str | None) -> str | None:
    """A prose argument, read off stdin where it spells `-` (RK329).

    The asymmetry this closes was backwards. `--section-body` documented the pipe because a
    paragraph is long; `--why` is the field that reliably carries an apostrophe, a backtick, an
    em dash and a `§` — its sentence names types, files and prior ids — and every one of those
    is read by a shell before this program sees it. Measured twice in one session against an
    adopting repo: a `ship --why` lost to a PowerShell parse, another to a bash single-quoted
    string containing `T293's`, both recovered by writing the prose to a variable first, which
    is what stdin exists to avoid.

    **The failure is silent in the bad direction**, which is why it is worth a door: a shell
    that eats a backtick does not refuse, it hands over prose subtly unlike what was written
    and the line lands. A quote terminating early is the loud case, and the lucky one.

    No validation changes. The sentence is still refused for a missing terminator or a length
    it cannot have — what changes is how it arrives.

    **The line terminator is the pipe's and not the author's**, so it comes off. `echo`,
    `printf` and every heredoc end with one, and `why.whitespace` firing on it would make the
    affordance unusable by the tools that reach for it — the refusal correct about the bytes
    and wrong about who wrote them. Only the terminators: a trailing *space* is the author's
    and is still refused, and an interior newline is still `why.newline`, because prose that
    arrived in two lines is a second sentence however it got here.
    """
    if value != STDIN:
        return value
    _refuse_unhardened()
    # Both ends of the stream belong to the encoder and not to the author (RK1023): the
    # terminator it closed with, and the mark it opened with.
    return _TRAILING_NEWLINES.sub("", _unmarked(sys.stdin.read()))


def _body_reader(literal: str | None, path: str | None) -> Callable[[], str]:
    """Where a paragraph comes from, as a reader nobody calls until it is needed (RK381).

    Three sources and one function, because the caller that has to know which of them a given
    argv chose is the caller that gets it wrong: a path, a string, and the pipe that both an
    omitted argument and the documented `-` reach. Returned rather than read, so the ordering
    :func:`~roadkeep.authoring.add` now guarantees is available to every door — a body fetched
    at the call site is a body spent before the field that refuses has been looked at.

    A file is read whole, in UTF-8, and its bytes are the author's: the trailing newline every
    editor writes is `_normalize`'s to take off, exactly as it is for the pipe, and nothing
    here reflows or strips. A path that is not there raises `OSError`, which is in
    :data:`REFUSALS` and exits 2 like every other bad input.
    """
    # Two of the three are **re-readable**, and saying so is what lets `add` refuse both
    # fields at once (RK426): a path costs a file read to fetch twice and a literal costs
    # nothing, while the pipe is the one source spent by looking at it. RK381's deferral is
    # unchanged for that one — it is the only case its argument was ever about.
    if path is not None:
        # The same mark, by the shorter route (RK1028): every mainstream Windows editor
        # writes one, and a path is the source a caller reaches for when the prose is long.
        return Rereadable(lambda: _unmarked(Path(path).read_text(encoding="utf-8")))
    if literal is not None and literal != STDIN:
        return Rereadable(lambda: literal)
    _refuse_unhardened()
    # The same preamble reaches a body, and by a shorter route: a paragraph is the field a
    # caller pipes first, so the escape hatch fails here before it fails on a `why` (RK1023).
    return lambda: _unmarked(sys.stdin.read())


def _refuse_unhardened() -> None:
    """Stop a prose read this process cannot make strictly (RK455).

    A `ValueError`, so it lands in :data:`REFUSALS` and exits 2 with every other bad input —
    the caller passed an argv this process cannot honour, which is exactly what a usage
    refusal is. Raised at the point of *reading* and never at startup: the overwhelming
    majority of calls never touch stdin, and refusing them would be the crash this replaced
    with an exit code stapled on.
    """
    said = _unhardened()
    if said is not None:
        raise ValueError(said.removeprefix("roadkeep: "))


def _one_body(named: str, literal: str | None, path: str | None) -> str | None:
    """Why an argv naming a paragraph twice is refused, or None (RK381).

    :func:`_one_pipe`'s rule for the other pair. A string and a path are two answers to one
    question, and honouring either silently is how a caller comes to believe the file is what
    landed — which is worse than the refusal, because the wrong prose is in the file and the
    command said it worked.

    And the dash, which is the other way to name a source twice (RK406). Measured filing a
    task in this repository: `--section-body-file -` opened a file called `-` and answered
    `[Errno 2] No such file or directory: '-'`, from a door whose body **already** comes from
    stdin unless a path is given. The refusal is by name and not a second reading of it: `-`
    is already this CLI's spelling on the *literal* flag, and taking it here too would be two
    spellings of one thing on one pair of arguments — which is what this function exists to
    refuse. So the sentence says where the body comes from, which is the fact the caller
    typing it did not have.
    """
    if path == STDIN:
        return (
            f"{named}-file takes a path and {STDIN!r} is not one: the body already comes "
            f"from stdin unless a path is given, so pass no source at all — or {named} "
            f"{STDIN} where a flag is wanted"
        )
    if literal in (None, STDIN) or path is None:
        return None
    return (
        f"{named} and {named}-file are two answers to one question: pass the prose or "
        f"the path it is in, not both"
    )


def _one_pipe(*asked: tuple[str, bool]) -> str | None:
    """Why an argv that sent two arguments to one pipe is refused, or None (RK329).

    There is one stdin and it is read to EOF, so a call whose `why` and whose section body
    both want it has asked for a split no rule here can make. Refused rather than given to the
    first: a body that silently absorbed the sentence meant for the line would be the quiet
    corruption this whole task is about, one layer further in.
    """
    named = [name for name, reached in asked if reached]
    if len(named) < 2:
        return None
    return (
        f"{' and '.join(named)} both read stdin, and there is one: pass one of them as a "
        f"string. A pipe is read to EOF, so splitting it between two fields is a guess"
    )


def _force_utf8(stream: object, errors: str = "backslashreplace") -> bool:
    """Harden one stream, and say whether it took (RK455).

    A text stream that has **already been read** refuses `reconfigure`, and the refusal is a
    raise — so `main` died out of this line with the verb never reached, on a stream this
    tool did not open and cannot assume it may re-encode. Measured with `pytest -n 8`, where
    an xdist worker is bootstrapped over its own stdin so fd 0 arrives read: nine to sixteen
    tests failed here, none of them about what they assert. The same shape reaches any host
    that embeds this CLI and hands over a used stdin.

    **Not a bare `pass`.** `errors="strict"` on the way in is what keeps input that is not
    UTF-8 refused rather than repaired, because a substituted character round-trips into a
    governed file and stays (L3) — a stdin that silently keeps cp1252 is that defect with no
    report. So the failure is returned rather than swallowed, and :func:`_unhardened` is
    where a verb that actually reads the stream says what it could not apply.
    """
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(encoding="utf-8", errors=errors)
        except (io.UnsupportedOperation, ValueError, OSError):
            # Every way a stream says no: already read, or detached.
            return _already_utf8(stream)
        return True
    return _already_utf8(stream)


def _already_utf8(stream: object) -> bool:
    """Whether this stream needs no hardening, having no decoding to get wrong (RK455).

    The narrowing that keeps the refusal about the defect. What `errors="strict"` buys is
    that bytes which are not UTF-8 are **refused rather than substituted**, and a stream with
    no `encoding` is decoding nothing — a `StringIO` a caller handed over is already `str`,
    so there is no codec that could be silently keeping cp1252. One that names UTF-8 is the
    same answer arriving the other way.

    Read after the reconfigure rather than instead of it: hardening also sets `errors`, which
    a stream already in UTF-8 may still have as `replace`. That is a residual this states
    rather than hides — the substitution it would make is of *undecodable* bytes, which by
    then are not a codec question, and refusing every such caller would take the pipe away
    from the hosts this exists to keep working.
    """
    named = getattr(stream, "encoding", None)
    if named is None:
        return True
    return codecs.lookup(str(named)).name == "utf-8"


#: Whether stdin arrived as a stream this process could make strict UTF-8 (RK455). Module
#: state because `main` decides it once per process and the reader that needs it is four
#: frames down a handler — and because it is a fact about the *process*, not about a call.
_STDIN_HARDENED = True


def harden() -> None:
    """Force the three standard streams to UTF-8, and record what stdin allowed (RK494).

    `main` did this inline while the flag and every reader of it were in one file. The readers
    are here now, so the write is too: a `global` reaches one module's namespace, and a caller
    rebinding its own imported copy would leave :func:`_unhardened` answering about a stream
    nobody hardened.

    stdin is strict on the way in — input that is not UTF-8 is refused, never repaired, because
    a substituted character round-trips out of the file it lands in (L3). stdout and stderr are
    not: the markers are emoji and the default Windows console encoding is cp1252, which raises
    mid-write and leaves a half-printed report. What these three were before is
    `provenance.STARTUP_CODECS`, recorded at import because after this the fact is gone (RK341)
    — and recorded rather than assumed (RK455), a stream this tool did not open being one it
    cannot insist on re-encoding, with the verb running either way.
    """
    global _STDIN_HARDENED  # noqa: PLW0603 - one process, one answer, decided here
    _STDIN_HARDENED = _force_utf8(sys.stdin, errors="strict")
    _force_utf8(sys.stdout)
    _force_utf8(sys.stderr)


def unread_prose(*, named: str = "--body") -> str:
    """The clause an answer adds where it left the prose alone (RK1109).

    A title-only `section amend` does not read the pipe, by design and correctly — `None` stays
    `None` so a call with nothing to read never blocks on a stream nobody opened. What that cost
    was silence: a caller who piped the replacement prose *and* passed `--title` got the title
    compared alone, and where it already read that way the answer was `unchanged: it already
    reads that way` at exit 0, over a paragraph that was never read.

    **Said rather than detected**, which is the whole reading. "Is a body waiting on stdin" has
    no portable answer, and the one that looks right — stdin is not a tty — is wrong exactly
    where this tool is used most: the MCP server owns stdin for the protocol, so every served
    `section_amend` would be refused for a pipe that is the transport. A sentence naming what
    the call did not do is true unconditionally, costs no test, and cannot false-positive.

    The flag it names is the one that would work here: over a stream this process could not make
    strict UTF-8 the pipe is not available at all, and `--body-file` is the door (RK455).
    """
    if _STDIN_HARDENED:
        return f"the prose was not read; pass {named} - to replace it"
    return (
        f"the prose was not read, and this process cannot read a pipe; "
        f"{named}-file <path> is the door"
    )


def _unhardened() -> str | None:
    """Why this process may not read prose off stdin, or None where it may (RK455).

    The refusal a verb makes instead of assuming a strictness it failed to apply. Only the
    commands that actually read the stream are refused: a `lint` in a worker whose stdin was
    consumed has nothing to lose by it, and refusing there would be the crash this replaced
    wearing an exit code.
    """
    if _STDIN_HARDENED:
        return None
    return (
        "roadkeep: stdin was already read by this process's host, so it could not be made "
        "strict UTF-8 — and prose decoded by whatever codec it kept would round-trip into a "
        "governed file (L3). Pass the text as an argument, or `--body-file <path>`."
    )
