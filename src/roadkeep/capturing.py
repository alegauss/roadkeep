"""The report the losing session can write and the narration afterwards cannot (RK85).

Four projects drive this tool through agents, and the defects they find are found in
sessions that end. What reaches the maintainer is a sentence composed after the fact — in
exactly the genre this repository exists to distrust, since the 142-word roadmap line was
the same author writing the same way about a different subject.

**The asymmetry is that none of what identifies a defect is prose.** The argv, the exit
code, the engine that answered, `roadkeep.toml` as it was read and the offending
`file:line:column` are facts the process already holds. So the failing command is re-run
under observation and those facts are emitted; the two things a machine cannot supply —
what does not work, and why it matters — are *arguments*, validated here against this
repository's own schema. A report that arrives inside the limits was refused in the
session that made the claim, instead of in a maintainer's review of an issue.

Three boundaries this does not cross:

* **It is a capture, not a client.** No network in this path, nothing to authenticate, no
  identity. It prints, and stops. Filing is a second command *a person runs* (RK87),
  because auto-filing saves one command and stakes a private repository's contents on a
  process in a state it did not anticipate, where an explicit hand-off stakes nothing. What
  leaves is composed of :data:`PARTS` a reviewer can delete by name in the same terminal —
  a deletion they can verify, not a scrubber promising to recognise a secret it has never
  seen — and `gh issue create -F -` borrows an authentication the operator already made.
* **It re-runs, in this process.** A subprocess would be a second engine to be wrong about
  — the whole reason RK79 comes first — so the command runs through the same
  :func:`roadkeep.cli.main` this interpreter loaded, and the capture states which tree that
  was. A crash is caught and kept: a traceback is the most identifying fact there is.
* **It never writes the claim.** `symptom` and `why` come from the caller, and a capture
  whose claim is over the limit is refused whole (L4). What is rendered for the maintainer
  is the `add` command that files it — a command, not a sentence, and one whose id stays
  derived where the backlog is.
"""

from __future__ import annotations

import contextlib
import io
import re
import shlex
import traceback
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep.config import find_config
from roadkeep.provenance import Engine, engine
from roadkeep.schema import Schema, Task, Violation

#: How much of the failing command's output is kept. A capture is read by a person, and a
#: `lint` over an adopted corpus prints hundreds of findings — the first of which is the
#: one being reported, and the rest of which is the corpus.
_MOST_OUTPUT_LINES = 40

#: `file:line[:column]`, the address every finding this tool prints leads with (RK15). The
#: column is optional because half of them have no column to name — a budget is about a
#: file and a dep is about a line. Matched over the captured output rather than passed in:
#: the caller reporting the defect is not the caller who knows which line was objected to.
_WHERE = re.compile(r"^(?P<file>[^\s:][^:]*):(?P<line>\d+)(?::(?P<column>\d+))?", re.MULTILINE)

#: The claim is checked against **this** repository's schema and never the reporting
#: project's: the line is destined for this backlog, so a project with a looser limit would
#: otherwise export a line the maintainer's own `add` refuses.
HOME = Schema()

#: A placeholder, so the two prose fields can be judged the way a real line is. The id and
#: the pointer are derived where the line is actually filed, and both are `add`'s to mint —
#: this exists only to make :meth:`Schema.validate` judge a whole line.
_PLACEHOLDER = "RK1"


@dataclass(frozen=True, slots=True)
class Failure:
    """What the observed command did, with nothing about it interpreted."""

    argv: tuple[str, ...]
    exit_code: int
    output: str
    #: Present when the command raised instead of exiting — the single most identifying
    #: fact a capture can carry, and the one a narration never reproduces.
    traceback: str | None = None

    @property
    def command(self) -> str:
        return shlex.join(("roadkeep", *self.argv))

    @property
    def where(self) -> str | None:
        """The first `file:line:column` the output named, or ``None``."""
        found = _WHERE.search(self.output)
        return found.group(0) if found else None


#: The parts of a capture that carry the *reporting* project rather than the defect, each
#: droppable by name (RK87). Deletion and not filtering: a redaction a reviewer performs by
#: naming a section is one they can verify by reading the output, where a scrubber that
#: promises to find secrets is a promise nobody can check against a repository it never saw.
#: `symptom`, `why`, `block` and the exit code are never droppable — without them there is
#: no claim, and an empty report is worse than no report.
PARTS = ("command", "engine", "where", "config", "source", "output", "traceback")


@dataclass(frozen=True, slots=True)
class Capture:
    """One defect, as the session that hit it can state it."""

    #: The caller's, never composed here (L4), and refused before this exists.
    symptom: str
    why: str
    block: str
    failure: Failure
    #: Which tree answered (RK79). Without it a stale plugin cache and a real defect are
    #: the same report, and the maintainer pays the difference.
    engine: Engine
    #: The reporting project's configuration, as it was read. A limit that is wrong is a
    #: defect whose evidence is this file.
    config: str | None = None
    config_path: str | None = None
    #: The input line the engine objected to, verbatim, and where it lives.
    source: str | None = None
    #: Parts the operator deleted before this went anywhere (RK87). Held rather than
    #: applied to the data, so one capture can be read whole in the terminal and emitted
    #: redacted — and *named* in the output, because a report missing a section without
    #: saying so is one a maintainer reads as a section that was empty.
    hidden: frozenset[str] = frozenset()

    def without(self, *parts: str) -> Capture:
        """The same capture with those parts omitted from everything it renders."""
        unknown = [part for part in parts if part not in PARTS]
        if unknown:
            raise ValueError(
                f"no such part of a capture: {', '.join(unknown)} — "
                f"the parts are {', '.join(PARTS)}"
            )
        return replace(self, hidden=self.hidden | frozenset(parts))

    def shows(self, part: str) -> bool:
        return part not in self.hidden

    @property
    def title(self) -> str:
        """What a tracker would put in its subject line: the claim, already inside 120."""
        return self.symptom

    @property
    def filing(self) -> str:
        """The command that files this in the maintainer's backlog, id left derived."""
        return shlex.join(
            [
                "roadkeep",
                "add",
                "--block",
                self.block,
                "--symptom",
                self.symptom,
                "--why",
                self.why,
            ]
        )

    def __str__(self) -> str:
        lines = [
            "roadkeep capture — what the session that hit this knew, before it ended",
            "",
            f"  symptom  {self.symptom}",
            f"  why      {self.why}",
            f"  block    {self.block}",
            "",
        ]
        if self.shows("command"):
            lines.append(f"  command  {self.failure.command}")
        lines.append(f"  exit     {self.failure.exit_code}")
        if self.shows("engine"):
            lines.append(f"  engine   {self.engine}")
        if self.shows("where") and self.failure.where:
            lines.append(f"  where    {self.failure.where}")
        if self.shows("config") and self.config_path:
            lines.append(f"  config   {self.config_path}")
        if self.hidden:
            # Named, because a capture that quietly drops a section is one a maintainer
            # reads as evidence that did not exist.
            lines.append(f"  omitted  {', '.join(sorted(self.hidden))}")
        if self.shows("source") and self.source is not None:
            lines += ["", "--- the line it objected to ---", self.source]
        if self.shows("traceback") and self.failure.traceback:
            lines += ["", "--- traceback ---", self.failure.traceback.rstrip()]
        if self.shows("output"):
            lines += ["", "--- output ---", self.failure.output.rstrip() or "(nothing)"]
        if self.shows("config") and self.config is not None:
            lines += ["", "--- roadkeep.toml as it was read ---", self.config.rstrip()]
        lines += ["", "File it:", f"  {self.filing}"]
        return "\n".join(lines)


#: What every failure ends with (RK86). Conditional and never an admission: this tool has
#: no way to know whether the rule it just applied was the right one, and no model to guess
#: (L4). What it can do is make the capture the cheapest next move instead of the invisible
#: one — an agent that meets a wrong limit otherwise has exactly one option left, which is
#: to work around the tool quietly, and that loses the sessions with the most to say.
_OFFER = "If roadkeep itself is what is wrong here, capture it before the session ends:"


def offer(argv: Sequence[str]) -> str:
    """The two lines a failure closes with: the sentence, and the command to run.

    The failing argv is already substituted, because the move has to cost nothing to take.
    The two prose fields stay as ellipses — they are the caller's, and this composes no
    part of a claim.
    """
    return "\n".join(
        [
            _OFFER,
            f'  roadkeep report --symptom "…" --why "…" -- {shlex.join(argv)}',
        ]
    )


def body(found: Capture) -> str:
    """The capture as a tracker takes it: the same text, fenced so nothing is re-rendered.

    Byte-for-byte what the terminal showed, because that is the whole claim RK87 makes —
    a reviewer approves what they read, and a body composed differently from the preview
    is a body nobody reviewed.
    """
    return "\n".join(["```", str(found), "```"])


def handoff(found: Capture, upstream: str) -> str:
    """The command *somebody else* runs to file it. Never run here (L2, and RK87).

    `gh` borrows an authentication the operator already made, on a machine that already
    trusts it. The alternative is this tool holding a token — a credential, a config key
    to leak it through, and a socket in a package whose whole promise is that the store is
    the repository and nothing talks to anything.
    """
    return "\n".join(
        [
            "Nothing was sent. To file it, after reading what is above:",
            f"  roadkeep report … --issue | gh issue create -R {upstream} "
            f"-t {shlex.quote(found.title)} -F -",
        ]
    )


def check(symptom: str, why: str, block: str) -> tuple[Violation, ...]:
    """Judge the claim against this repository's schema, before anything is run."""
    task = Task(
        id=_PLACEHOLDER,
        status=HOME.markers[0],
        block=block,
        symptom=symptom,
        why=why,
        ref=_PLACEHOLDER,
    )
    return HOME.validate(task)


def observe(argv: Sequence[str]) -> Failure:
    """Re-run one roadkeep command in this process and keep everything it did.

    Both streams into one buffer, in the order they were written: a capture that separates
    them loses which finding preceded the traceback, and that order is the diagnosis.
    """
    from roadkeep.cli import main  # here, because the CLI is what builds a capture

    buffer = io.StringIO()
    trace: str | None = None
    code = 0
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        try:
            code = main(list(argv))
        except SystemExit as exit_:  # argparse's own refusals leave this way
            code = exit_.code if isinstance(exit_.code, int) else 2
        except Exception:
            # A crash *is* the report. `Exception` and not `BaseException`: an interrupt is
            # the user asking for the session back, and a capture is not worth taking it.
            trace = traceback.format_exc()
            code = 1
    return Failure(
        argv=tuple(argv), exit_code=code, output=_tail(buffer.getvalue()), traceback=trace
    )


def capture(
    symptom: str, why: str, block: str, argv: Sequence[str], root: str | Path = "."
) -> Capture:
    """Run the failing command and compose the report. The claim is already validated."""
    failure = observe(argv)
    config_path, config = _configuration(root)
    return Capture(
        symptom=symptom,
        why=why,
        block=block,
        failure=failure,
        engine=engine(),
        config=config,
        config_path=config_path,
        source=_source(failure.where, root),
    )


def _tail(output: str) -> str:
    lines = output.splitlines()
    if len(lines) <= _MOST_OUTPUT_LINES:
        return output
    dropped = len(lines) - _MOST_OUTPUT_LINES
    # Stated, because a truncated listing that does not say so reads as a complete one.
    return "\n".join([f"… {dropped} earlier line(s) not kept", *lines[-_MOST_OUTPUT_LINES:]])


def _configuration(root: str | Path) -> tuple[str | None, str | None]:
    found = find_config(Path(root))
    if found is None:
        return None, None
    try:
        return str(found), found.read_text(encoding="utf-8")
    except OSError:
        return str(found), None


def _source(where: str | None, root: str | Path) -> str | None:
    """The line the engine named, read back verbatim — never reconstructed."""
    if where is None:
        return None
    name, _, rest = where.partition(":")
    number = int(rest.partition(":")[0])
    path = Path(root) / name
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    return lines[number - 1] if 1 <= number <= len(lines) else None
