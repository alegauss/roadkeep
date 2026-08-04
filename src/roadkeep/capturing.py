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
import json
import re
import shlex
import traceback
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from roadkeep.config import find_config
from roadkeep.provenance import Engine, engine, invocation
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
PARTS = ("command", "engine", "where", "config", "source", "document", "output", "traceback")

#: What a replay cannot be staged without (RK88). The tension RK87 leaves behind, named
#: rather than resolved: a capture that embeds nothing is safe and inert, and one that can
#: be re-run somewhere else is one that carried a file out of a repository. So the
#: embedding is opt-in, and a capture that was never asked for it says which part is
#: missing instead of failing halfway through a staging.
#:
#: `document` is not here because it is not always input: a defect in reading
#: `roadkeep.toml` has no governed file in it at all, and demanding one would make the
#: cheapest class of field report the one class that cannot be replayed. It is required
#: exactly when the failure named a file — see :attr:`Capture.missing`.
REPLAYABLE = ("command", "config")


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
    #: The whole file that line is in, embedded only when the caller asked (RK88): it is
    #: the input half of a test, and it is also a file leaving a repository. One file, the
    #: one the finding named — never the project.
    document: str | None = None
    document_path: str | None = None
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
                *shlex.split(invocation()),
                "add",
                "--block",
                self.block,
                "--symptom",
                self.symptom,
                "--why",
                self.why,
            ]
        )

    def _head(self) -> list[str]:
        """The labelled facts, in the order a reader needs them to decide what this is."""
        fields = [
            ("command", self.failure.command if self.shows("command") else None),
            ("exit", str(self.failure.exit_code)),
            ("engine", str(self.engine) if self.shows("engine") else None),
            ("where", self.failure.where if self.shows("where") else None),
            ("config", self.config_path if self.shows("config") else None),
            # Named, because a capture that quietly drops a section is one a maintainer
            # reads as evidence that did not exist.
            ("omitted", ", ".join(sorted(self.hidden)) if self.hidden else None),
        ]
        return [f"  {label:<8} {value}" for label, value in fields if value]

    def _blocks(self) -> list[str]:
        """The verbatim evidence, each under a heading that says what it is."""
        parts = [
            ("source", "the line it objected to", self.source),
            ("traceback", "traceback", self.failure.traceback),
            ("output", "output", self.failure.output.rstrip() or "(nothing)"),
            ("config", "roadkeep.toml as it was read", self.config),
            ("document", f"{self.document_path} as it was read", self.document),
        ]
        lines: list[str] = []
        for part, title, text in parts:
            if self.shows(part) and text is not None:
                lines += ["", f"--- {title} ---", text.rstrip()]
        return lines

    def __str__(self) -> str:
        return "\n".join(
            [
                "roadkeep capture — what the session that hit this knew, before it ended",
                "",
                f"  symptom  {self.symptom}",
                f"  why      {self.why}",
                f"  block    {self.block}",
                "",
                *self._head(),
                *self._blocks(),
                "",
                "File it:",
                f"  {self.filing}",
            ]
        )

    @property
    def missing(self) -> tuple[str, ...]:
        """The parts a replay would need and does not have (RK88)."""
        held = {
            "command": bool(self.failure.argv),
            "config": self.config is not None,
            "document": self.document is not None and self.document_path is not None,
        }
        needed = list(REPLAYABLE)
        if self.shows("where") and self.failure.where:
            # The failure named a file, so that file is half the input.
            needed.append("document")
        return tuple(part for part in needed if not (self.shows(part) and held[part]))

    @property
    def replayable(self) -> bool:
        return not self.missing

    def as_dict(self) -> dict[str, object]:
        """The capture as a corpus file holds it — redaction applied, not recorded around.

        A dropped part is absent here exactly as it is absent from the printed text: one
        artefact, one set of contents, so what a reviewer approved is what gets stored and
        replayed. `reproduces` is this repository's standing expectation, and the only
        field a *reader* of the capture writes: flipping it is how a fix is recorded.
        """
        data: dict[str, object] = {
            "symptom": self.symptom,
            "why": self.why,
            "block": self.block,
            "exit": self.failure.exit_code,
            "reproduces": True,
        }
        if self.shows("command"):
            data["argv"] = list(self.failure.argv)
        if self.shows("engine"):
            data["engine"] = str(self.engine)
        if self.shows("where") and self.failure.where:
            data["where"] = self.failure.where
        if self.shows("output"):
            data["output"] = self.failure.output
        if self.shows("traceback") and self.failure.traceback:
            data["traceback"] = self.failure.traceback
        if self.shows("config") and self.config is not None:
            data["config"] = self.config
        if self.shows("source") and self.source is not None:
            data["source"] = self.source
        if self.shows("document") and self.document is not None:
            data["document"] = self.document
            data["document_path"] = self.document_path
        if self.hidden:
            data["omitted"] = sorted(self.hidden)
        return data


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
            f'  {invocation()} report --symptom "…" --why "…" -- {shlex.join(argv)}',
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
            f"  {invocation()} report … --issue | gh issue create -R {upstream} "
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
    symptom: str,
    why: str,
    block: str,
    argv: Sequence[str],
    root: str | Path = ".",
    embed: bool = False,
) -> Capture:
    """Run the failing command and compose the report. The claim is already validated.

    ``embed`` carries the file the finding named, which is what makes the capture a test
    somewhere else (RK88) and also what makes it a file leaving a repository (RK87) — so it
    is asked for, never assumed.
    """
    failure = observe(argv)
    config_path, config = _configuration(root)
    document_path, document = _document(failure.where, root) if embed else (None, None)
    return Capture(
        symptom=symptom,
        why=why,
        block=block,
        failure=failure,
        engine=engine(),
        config=config,
        config_path=config_path,
        source=_source(failure.where, root),
        document=document,
        document_path=document_path,
    )


@dataclass(frozen=True, slots=True)
class Replay:
    """One capture re-run against the tree that is here now (RK88).

    The question a field report cannot otherwise answer. *Reproduces* is the recorded exit
    code and the recorded address both turning up again — not an output comparison, because
    a message this repository improved is not a defect that came back.
    """

    reproduces: bool
    recorded_exit: int
    exit_code: int
    output: str
    #: Non-empty when nothing was run: the capture was never made replayable, and saying so
    #: is the whole answer. A staging that guessed at the missing half would be a test whose
    #: input this repository invented, which is the thing RK88 exists to avoid.
    missing: tuple[str, ...] = ()

    @property
    def ran(self) -> bool:
        return not self.missing

    def __str__(self) -> str:
        if self.missing:
            return f"not replayable: the capture has no {', '.join(self.missing)}"
        verdict = "still reproduces" if self.reproduces else "no longer reproduces"
        return f"{verdict}: recorded exit {self.recorded_exit}, now {self.exit_code}"


def replay(recorded: Mapping[str, object], workdir: str | Path) -> Replay:
    """Stage the capture's own inputs in ``workdir`` and run its argv against them.

    The reporter's repository is never needed and never reached: what is written is the
    `roadkeep.toml` and the one file the capture carries, and the `-C` in the recorded argv
    is repointed at the staging. Everything else in that argv is passed through untouched —
    a replay that rewrote the flags would be testing a command nobody ran.
    """
    needed = list(REPLAYABLE) + (["document"] if recorded.get("where") else [])
    missing = tuple(part for part in needed if not recorded.get(_FIELD[part]))
    recorded_exit = int(recorded.get("exit", 0) or 0)
    if missing:
        return Replay(False, recorded_exit, 0, "", missing)

    root = Path(workdir)
    (root / "roadkeep.toml").write_text(str(recorded["config"]), encoding="utf-8")
    if recorded.get("document"):
        document = root / str(recorded["document_path"])
        document.parent.mkdir(parents=True, exist_ok=True)
        # `newline=""`: the round-trip invariant is about bytes, and a translated line
        # ending is a different file from the one that failed.
        with document.open("w", encoding="utf-8", newline="") as handle:
            handle.write(str(recorded["document"]))

    failure = observe(_repointed([str(part) for part in recorded["argv"]], root))
    where = recorded.get("where")
    reproduces = failure.exit_code == recorded_exit and (
        where is None or str(where) in failure.output
    )
    return Replay(reproduces, recorded_exit, failure.exit_code, failure.output)


#: Which key of a stored capture each replayable part lives under.
_FIELD = {"command": "argv", "config": "config", "document": "document"}

#: Where a capture lands before anybody decides what to do with it (RK89). A fifth path in
#: a repository that declared four — and one the repository never has to see, because the
#: same run teaches git to ignore it.
REPORTS = Path(".roadkeep") / "reports"

#: The line appended to `.gitignore`, and every spelling that already covers it. Nothing
#: here enters a history, a diff, or a review by somebody who never installed this tool.
IGNORE_RULE = ".roadkeep/"
_COVERED = frozenset({".roadkeep", ".roadkeep/", "/.roadkeep", "/.roadkeep/", ".roadkeep/**"})


@dataclass(frozen=True, slots=True)
class Kept:
    """One capture on disk, and what had to be said about getting it there."""

    path: Path
    #: `None` when git was already told to ignore the directory or has just been told.
    #: A sentence when it could not be — never an exception, because the capture is the
    #: point and an unwritable `.gitignore` is a thing to mention, not to fail over.
    complaint: str | None = None


def keep(found: Capture, root: str | Path = ".") -> Kept:
    """Write the capture before it is printed (RK89).

    Evidence that lives for the length of one stdout depends on the caller taking a second
    step, and RK86 is this block's own record of second steps not being taken. So this is
    unconditional and has no flag: a capture nobody pruned costs kilobytes, and a capture
    nobody kept costs the only session that could have identified the defect.

    Retention is deliberately unsolved. Rotation, dedup by argv, an age limit, a command
    that lists what was never sent — every one of them is easier to add to a directory
    with files in it than to reconstruct from sessions that ended.

    What is written is what was produced: `--without` applied, `--embed` or not. One
    artefact and one set of contents, so the file on disk is the text that was reviewed.
    """
    base = Path(root)
    directory = base / REPORTS
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / _filename(found)
    path.write_text(
        json.dumps(found.as_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return Kept(path=path, complaint=_ignore(base))


def _filename(found: Capture) -> str:
    """Sortable, and it says what failed. Uniqueness is the clock plus the claim's digest:
    two captures of one command in one second are still two captures."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = sha256(f"{found.symptom}{found.failure.command}".encode()).hexdigest()[:8]
    return f"{stamp}-{_slug(_subcommand(found.failure.argv))}-{digest}.json"


def _subcommand(argv: Sequence[str]) -> str:
    """Which command failed, asked of the parser rather than guessed from the argv.

    The first non-flag word is the *value* of `-C` half the time, and a filename naming a
    directory instead of a command is a directory listing nobody can read.
    """
    from roadkeep.cli import build_parser

    with contextlib.redirect_stderr(io.StringIO()):
        try:
            known, _ = build_parser().parse_known_args(list(argv))
        except SystemExit:
            return "run"
    return getattr(known, "command", None) or "run"


def _slug(word: str) -> str:
    kept = [character if character.isalnum() else "-" for character in word.lower()]
    return "".join(kept).strip("-") or "run"


def _ignore(root: Path) -> str | None:
    """Teach git to ignore the directory, once, without touching a line already there.

    Append-only and never rendered: `.gitignore` is not a governed file, it does not
    round-trip, and reordering somebody's ignore rules to add one is the kind of write
    this tool refuses everywhere else.
    """
    path = root / ".gitignore"
    try:
        existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    except (OSError, UnicodeDecodeError) as error:
        return f"could not read {path}: {error}"
    if any(line.strip() in _COVERED for line in existing.splitlines()):
        return None
    prefix = "" if not existing or existing.endswith("\n") else "\n"
    try:
        with path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(f"{prefix}{IGNORE_RULE}\n")
    except OSError as error:
        # The capture is already on disk. This is a sentence, not a failure.
        return f"could not add {IGNORE_RULE} to {path}: {error}"
    return None


def _repointed(argv: list[str], root: Path) -> list[str]:
    """The recorded argv with its `-C` aimed at the staging, and nothing else touched."""
    out = list(argv)
    for index, word in enumerate(out[:-1]):
        if word in ("-C", "--directory"):
            out[index + 1] = str(root)
    if not any(word in ("-C", "--directory") for word in out):
        out = ["-C", str(root), *out]
    return out


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


def _document(where: str | None, root: str | Path) -> tuple[str | None, str | None]:
    """The file the finding named, whole and verbatim — one file, never the project."""
    if where is None:
        return None, None
    name = where.partition(":")[0]
    try:
        return name, (Path(root) / name).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None, None


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
