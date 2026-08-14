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

  The price is one class of defect it cannot re-run, and RK341 is the record of that being
  paid: an interpreter's stdio codecs are settled before its first line executes, so a re-run
  here inherits *this* session's and not the field's. RK337 arrived that way — a
  `UnicodeEncodeError` in an adopting project that exited 0 on the re-run, so the stored
  capture blamed a module that opens its file `rb` and encodes nothing. What is recorded
  instead is the :class:`Environment`: the variables that decide how a process reads and
  writes text, and what the interpreter resolved them to. A fact the re-run cannot supply is
  one the report has to carry.
* **It never writes the claim.** `symptom` and `why` come from the caller, and a capture
  whose claim is over the limit is refused whole (L4). What is rendered for the maintainer
  is the `add` command that files it — a command, not a sentence, and one whose id stays
  derived where the backlog is.
"""

from __future__ import annotations

import contextlib
import io
import json
import locale
import os
import re
import shlex
import sys
import tomllib
import traceback
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from roadkeep import __version__
from roadkeep.config import Config, ConfigError, find_config
from roadkeep.provenance import STARTUP_CODECS, Engine, engine, invocation
from roadkeep.kernel.schema import Schema, Task, Violation

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
#:
#: Spelled by :attr:`HOME` and not written out (RK1000): `RK1` was a literal standing in for
#: a value the schema declares, so a default prefix or an `[ids] pad` that moved would leave
#: this judging a whole line against an id that project's own gate refuses.
_PLACEHOLDER = HOME.spell_id(HOME.prefixes[0], 1)

#: The exit code that means *the call was wrong*, which is this CLI's own contract — 0, 1 for
#: the gate, 2 for usage. Spelled here rather than imported, because `cli` imports this module
#: and the reverse is a cycle; a test holds the two numbers together (RK440).
_USAGE = 2

#: What a capture says about itself when its re-run never reached the rule being reported
#: (RK440). Two of Shio's three field reports carried a refusal that fires *before* the verb
#: does any work — a missing `--why`, an id the ledger already held — and were filed with
#: `reproduces: true` above output that has nothing to do with the claim.
#:
#: An annotation and never a refusal, for two reasons that both come out of this block. RK86
#: exists to make the capture the cheapest move a losing session has, and a report refused at
#: the end of that session is the session lost; and a precondition refusal is sometimes exactly
#: the defect — "it refuses a call that is legal" is a report this tool has no way to tell from
#: a mistyped argv, having no model to judge the claim against the evidence (L4). So the shape
#: is stated and the verdict is left to the reader, which is the one division of labour a
#: capture is built on.
_STOPPED = (
    "usage — the re-run was refused before the verb ran, so nothing below is evidence "
    "about the symptom unless that refusal is itself the defect"
)

#: The same fact said to the one reader who can still act on it (RK440). The capture carries
#: the annotation for the maintainer who reads it later; this is for the session that just took
#: it, which is the only place a mistyped argv can be corrected while the defect is still in
#: reach. It names the move, as every finding this tool prints does (RK420) — and it is a
#: notice and not a non-zero exit, because `report` reporting on its own capture is exactly the
#: second step RK86 measured nobody taking.
STOPPED_NOTICE = (
    "the re-run exited 2 (usage) and never reached the verb — if that refusal is not the "
    "defect, correct the command after `--` and take the capture again"
)


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

    @property
    def stopped(self) -> bool:
        """Whether the re-run was refused before the verb did any work (RK440).

        Read off the **exit code** and never off the message. This CLI's contract is 0, 1 for
        a gate finding and 2 for usage, so the one number already separates "the tool applied
        its rule and I disagree" from "the tool never got that far" — where a list of refusal
        sentences to match would be a second declaration of that contract, drifting one
        reworded message at a time, and would miss precisely the two Shio filed: neither came
        from argparse, and both exited 2.
        """
        return self.exit_code == _USAGE


#: The parts of a capture that carry the *reporting* project rather than the defect, each
#: droppable by name (RK87). Deletion and not filtering: a redaction a reviewer performs by
#: naming a section is one they can verify by reading the output, where a scrubber that
#: promises to find secrets is a promise nobody can check against a repository it never saw.
#: `symptom`, `why`, `block` and the exit code are never droppable — without them there is
#: no claim, and an empty report is worse than no report.
PARTS = (
    "command",
    "engine",
    "where",
    "config",
    "source",
    "document",
    "output",
    "traceback",
    "environment",
)

#: The variables a capture records, and the only reason it records any (RK341). Every one of
#: them decides how a *process* reads and writes text, which is a class of defect whose entire
#: cause sits outside the repository: RK337 was a `UnicodeEncodeError` in the field that exited
#: 0 on the re-run, so the stored capture blamed a module that opens its file `rb` and encodes
#: nothing, and the diagnosis had to be re-derived by reading rather than replayed.
#:
#: An allow-list, and short. `os.environ` is a disclosure — tokens, hostnames, paths, the
#: things RK87 exists to keep out of a tracker — and the answer RK87 gives to a disclosure is a
#: reviewer who can read what leaves before it goes. A dump nobody can read is not that.
TEXT_VARIABLES = (
    "PYTHONIOENCODING",
    "PYTHONUTF8",
    "PYTHONLEGACYWINDOWSSTDIO",
    "LC_ALL",
    "LC_CTYPE",
    "LANG",
)

#: What a replay cannot be staged without (RK88). The tension RK87 leaves behind, named
#: rather than resolved: a capture that embeds nothing is safe and inert, and one that can
#: be re-run somewhere else is one that carried a file out of a repository. So the
#: embedding is opt-in, and a capture that was never asked for it says which part is
#: missing instead of failing halfway through a staging.
#:
#: `document` is not here because it is not always input: a defect in reading
#: `roadkeep.toml` has no governed file in it at all, and demanding one would make the
#: cheapest class of field report the one class that cannot be replayed. It is required
#: exactly when the failure named a file — see :attr:`Capture.missing`. What it then requires
#: is *the declared files*, not one of them (RK344): a staging short of what the command reads
#: is refused by :func:`_unstaged`, so carrying only the file a finding named satisfied this
#: check and failed the next one.
REPLAYABLE = ("command", "config")


@dataclass(frozen=True, slots=True)
class Environment:
    """How the reporting process reads and writes text — what was asked for, and what happened.

    The split is the whole value. `declared` is the request, and it is what a maintainer can
    hand to somebody else to reproduce with; the rest is what the interpreter resolved, which
    is the fact and is not always the request — `PYTHONUTF8=1` and `-X utf8` arrive at the same
    place, `PYTHONIOENCODING` can name a codec the platform does not have, and a variable set
    after the process started changes nothing at all.

    `streams` is read at import (see :data:`roadkeep.provenance.STARTUP_CODECS`) and is the one
    entry here that has to be taken at a moment rather than asked for: everything else is still
    true when the capture is composed, and that one is gone by then.
    """

    #: The variables of :data:`TEXT_VARIABLES` this process actually has, in that order. Absent
    #: ones are absent rather than empty: "not set" and "set to nothing" are different states,
    #: and on Windows the second is how a variable is deleted.
    declared: tuple[tuple[str, str], ...] = ()
    #: `sys.flags.utf8_mode`, which is where `PYTHONUTF8` and `-X utf8` both end up.
    utf8_mode: bool = False
    #: `locale.getpreferredencoding(False)` — cp1252 on the machines this tool was written on,
    #: and the default every un-hardened `open()` in a project takes.
    locale: str = ""
    #: `sys.getfilesystemencoding()`, which is what turns a filename into a `str` — and, with
    #: `surrogateescape`, what puts a lone surrogate into one.
    filesystem: str = ""
    #: `name -> encoding/errors` for the three streams, as `main` found them.
    streams: tuple[tuple[str, str], ...] = ()

    def __str__(self) -> str:
        rows = [
            *((name, value) for name, value in self.declared),
            ("utf8 mode", "on" if self.utf8_mode else "off"),
            ("locale", self.locale),
            ("filesystem", self.filesystem),
            *((name, codec) for name, codec in self.streams),
        ]
        width = max(len(name) for name, _ in rows)
        return "\n".join(f"  {name:<{width}}  {value}" for name, value in rows)

    def as_dict(self) -> dict[str, object]:
        return {
            "declared": dict(self.declared),
            "utf8_mode": self.utf8_mode,
            "locale": self.locale,
            "filesystem": self.filesystem,
            "streams": dict(self.streams),
        }

    @property
    def facts(self) -> dict[str, str]:
        """One flat mapping, which is what a comparison needs (see :func:`_drifted`).

        The three streams collapse to one entry called `stdio`: they are reconfigured together
        by one caller, and reporting three names for one cause is three lines a reader has to
        recombine.
        """
        return {
            **dict(self.declared),
            "utf8 mode": "on" if self.utf8_mode else "off",
            "locale": self.locale,
            "filesystem": self.filesystem,
            "stdio": ", ".join(f"{name}={codec}" for name, codec in self.streams),
        }


def environment() -> Environment:
    """This process's text handling, read now — except the streams, read at import."""
    return Environment(
        declared=tuple((name, os.environ[name]) for name in TEXT_VARIABLES if name in os.environ),
        utf8_mode=bool(sys.flags.utf8_mode),
        locale=locale.getpreferredencoding(False),
        filesystem=sys.getfilesystemencoding(),
        streams=STARTUP_CODECS,
    )


def _read(recorded: object) -> Environment | None:
    """One stored capture's `environment` back as the class, or `None` where it has none.

    Forgiving by design: this reads corpus files written by older versions of this tool, and a
    capture that predates the field is a capture with no environment rather than a broken one.
    """
    if not isinstance(recorded, Mapping):
        return None
    declared = recorded.get("declared")
    streams = recorded.get("streams")
    return Environment(
        declared=tuple(declared.items()) if isinstance(declared, Mapping) else (),
        utf8_mode=bool(recorded.get("utf8_mode")),
        locale=str(recorded.get("locale", "")),
        filesystem=str(recorded.get("filesystem", "")),
        streams=tuple(streams.items()) if isinstance(streams, Mapping) else (),
    )


def _drifted(recorded: object) -> tuple[str, ...]:
    """Which of a capture's recorded text-handling facts this process does not share.

    Named rather than counted, and one-directional: a variable the capture recorded and this
    process does not have has drifted, and one *this* process adds is not the capture's
    business — a replay is asked whether the recorded conditions still hold, not whether the
    two machines are the same machine.
    """
    stored = _read(recorded)
    if stored is None:
        return ()
    here = environment().facts
    return tuple(name for name, value in stored.facts.items() if here.get(name, "") != value)


#: A version inside the engine line a capture stamps — `roadkeep 0.1.645 (3153c8…`. Read
#: out of the string rather than stored beside it, because every capture ever taken carries
#: this field and a second one would reach only the reports filed after it (RK443's rule).
_STAMPED = re.compile(r"^roadkeep (?P<version>\d+(?:\.\d+)*)")


def _aged(recorded: object) -> str:
    """How far the engine that took this capture is behind the one replaying it (RK1078).

    The cheap fact already in the payload, and the one triage was paying a session for. Four
    captures arrived from one Shio session against plugin 0.1.645 while the checkout stood at
    0.1.676, and **three of the four named work that was already shipped** — an id occupancy
    check (RK1051, 0.1.648), a wrapped-entry correction (RK1049, 0.1.646) and a refusal's
    second clause (RK1057). The reporter was right every time about what they saw; the engine
    they saw it with was the stale copy the marketplace had not refreshed.

    A sentence and not a boolean, for :attr:`Replay.drifted`'s reason: this qualifies a
    verdict rather than being one. A capture that does not reproduce *and* was taken thirty
    patch versions back is a closed report, and one that does not reproduce against the same
    version is a defect that went away for some other reason — two different next steps, and
    the difference is a string comparison this reader can make for nothing.

    `""` where there is nothing to compare: no engine recorded, an unparseable stamp, or the
    same version. Never a guess about which is newer than which beyond the ordering the
    numbers give — a commit is stamped too and this deliberately does not read it, two
    checkouts at one version being a question `engines` answers and this one cannot.
    """
    stamp = _STAMPED.match(str(recorded or ""))
    if stamp is None:
        return ""
    taken = tuple(int(part) for part in stamp.group("version").split("."))
    here = tuple(int(part) for part in __version__.split("."))
    if taken >= here:
        return ""
    return (
        f"taken on {stamp.group('version')} and replayed on {__version__}: work shipped "
        f"between them is work this capture could not have seen"
    )


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
    #: Where this capture was aimed: the repository a defect in **roadkeep** is filed against,
    #: from `--to` or `[report] upstream` (RK1161). In the artefact for RK89's reason — a capture
    #: is evidence, and where it was sent is part of it — and read back by `capture filed`, so the
    #: stamp that records delivery elsewhere does not ask for a repository the config declares.
    #:
    #: `None` where the reporting project declared none, which keeps the refusal that reading
    #: replaces: a bare id no governed file holds is still a link to nothing.
    upstream: str | None = None
    #: `path -> contents` for the governed files, embedded only when the caller asked (RK88):
    #: they are the input half of a test, and they are also files leaving a repository.
    #:
    #: Every file the config **declares**, and not the one the finding named (RK344). One file
    #: was the smaller disclosure and it stopped being a staging: `lint` — the command the fault
    #: offer suggests most — reads all of them, so a capture of it from an ordinary three-file
    #: project stages two files short and is refused. The governed documents are also the least
    #: sensitive files a project has, being the ones this tool exists to write. Never anything
    #: else in the repository, and still never without `--embed`.
    documents: tuple[tuple[str, str], ...] = ()
    #: How the reporting process reads and writes text (RK341) — the half of the input that is
    #: not in the repository and that a re-run in this interpreter silently supplies from
    #: wherever it happens to be running.
    environment: Environment | None = None
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
            # Beside the exit code it is derived from, and above the evidence it qualifies
            # (RK440): a reader who meets this after the output has already read the output
            # as the thing the symptom claims.
            ("stopped", _STOPPED if self.failure.stopped else None),
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
            *(("document", f"{path} as it was read", text) for path, text in self.documents),
            (
                "environment",
                "how this process reads and writes text",
                str(self.environment) if self.environment is not None else None,
            ),
        ]
        lines: list[str] = []
        for part, title, text in parts:
            if self.shows(part) and text is not None:
                lines += ["", f"--- {title} ---", text.rstrip()]
        return lines

    def __str__(self) -> str:
        return "\n".join(
            [
                # The program name and the verb no longer sit together here (RK1142): `filed`
                # made that pair a command, and a title shaped like one is a line a reader may
                # type. `test_no_message_spells_an_invocation_it_did_not_derive` is what
                # noticed — it holds every literal invocation to being derived — and this was
                # never an invocation at all, so the fix is the wording and not a derivation.
                "A roadkeep field report — what the session that hit this knew, before it ended",
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
            "document": bool(self.documents),
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
        # Written only when it is true (RK440), so every capture already on disk reads back
        # unchanged. It sits beside `reproduces` and does not touch it: the argv *does*
        # reproduce — the same command earns the same refusal, which is what `replay` asserts
        # — and what is in doubt is whether that refusal is the symptom above it.
        if self.failure.stopped:
            data["stopped"] = "usage"
        # One row per key, so the two rules — the part is shown, and there is something to
        # store — are stated once instead of at every field. `document` is two rows because it
        # is two keys and one decision: a path without the file it names is not evidence.
        rows: tuple[tuple[str, str, object], ...] = (
            ("command", "argv", list(self.failure.argv)),
            ("engine", "engine", str(self.engine)),
            ("where", "where", self.failure.where),
            ("output", "output", self.failure.output),
            ("traceback", "traceback", self.failure.traceback),
            ("config", "config", self.config),
            ("source", "source", self.source),
            # Not a redactable part of its own: it is this project's own configuration value and
            # the tracker body already names it, so `config` is the part that governs it.
            ("config", "upstream", self.upstream),
            # `path -> contents`, so a capture that carries three files is three entries and
            # not three parallel lists a reader has to zip back together.
            ("document", "documents", dict(self.documents) or None),
            (
                "environment",
                "environment",
                self.environment.as_dict() if self.environment is not None else None,
            ),
        )
        for part, key, value in rows:
            if self.shows(part) and value is not None:
                data[key] = value
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
    """The two lines a fault closes with: the sentence, and the command to run.

    The failing argv is already substituted, because the move has to cost nothing to take.
    The two prose fields stay as ellipses — they are the caller's, and this composes no
    part of a claim.

    *Which* failures close with it is `cli._may_offer`'s and never this function's: a verdict a
    read was asked for is not one (RK271), and the caller is the only place that knows whether
    the exit code it is holding is an answer or a fall.
    """
    if _transient(argv):
        return "\n".join([_OFFER, f"  {_MERGE_OFFER}"])
    return "\n".join(
        [
            _OFFER,
            f'  {invocation()} report --symptom "…" --why "…" -- {shlex.join(argv)}',
        ]
    )


#: git's own name for the files it hands a merge driver. Matched rather than assumed from the
#: verb, because `merge` run by hand takes three real paths and the offer is good there.
_TEMPORARY = ".merge_file_"

#: What the offer says where the argv cannot be re-run (RK484). Not a command, because there
#: is none: the three inputs are gone, and printing one that fails is the defect being fixed.
#: What is durable is the merge — git holds both commits — so that is what is asked for.
_MERGE_OFFER = (
    "the three inputs were git's own temporary files and are already deleted, so there is "
    "no argv to re-run: file it with the two revisions instead — `git rev-parse HEAD "
    "MERGE_HEAD` names them, and both are in this repository"
)


def _transient(argv: Sequence[str]) -> bool:
    """Whether this argv names files that will not exist by the time anybody reads it.

    Measured end to end: a real `git merge` reaching the driver closed with `report … --
    merge .merge_file_tbx68e …`, and the three files were gone before the line finished
    printing. The one verb where RK86's offer is worth most is the one where it was never
    takeable.
    """
    return argv[:1] == ["merge"] and any(one.startswith(_TEMPORARY) for one in argv)


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
    upstream: str | None = None,
) -> Capture:
    """Run the failing command and compose the report. The claim is already validated.

    ``embed`` carries the governed files, which is what makes the capture a test somewhere
    else (RK88) and also what makes them files leaving a repository (RK87) — so it is asked
    for, never assumed.
    """
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
        documents=_documents(root) if embed else (),
        environment=environment(),
        upstream=upstream,
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
    #: Governed files the staged config declares that the capture did not carry (RK343). A
    #: second reason not to run, and a different one: :attr:`missing` is a *part* the capture
    #: lacks, and this is a file the project had and the capture never held a copy of.
    unstaged: tuple[str, ...] = ()
    #: Which of the capture's recorded text-handling facts this process does not share (RK341),
    #: and `None` where it recorded none to compare. Not a verdict of its own: it is the reason
    #: a verdict may be about a different machine than the one the defect was on.
    drifted: tuple[str, ...] | None = None
    #: How far behind the engine that took the capture is, or `""` where there is nothing to
    #: compare (RK1078). The fourth reason a verdict may be about something other than the
    #: symptom, and the one that decides whether a report is closed rather than live.
    aged: str = ""
    #: Whether the capture's own re-run was refused before the verb ran (RK440), read back
    #: here so the reader who *triages* gets the annotation and not only the one who took it
    #: (RK443). The third reason not to trust a verdict, and the third to be stated beside
    #: the sentence rather than folded into :attr:`reproduces`: this one reproduces by
    #: construction — the same argv earns the same refusal every time — so the boolean is
    #: right and what it is about is the refusal rather than the symptom above it.
    #:
    #: Derived from the recorded `exit` and never from a stored field, which is what makes it
    #: reach the two captures Shio filed before RK440 existed — the whole population this is
    #: about. The corpus gate is deliberately **not** wired to it: refusing such an entry
    #: would fail this repository's own suite on captures that are honest records of a
    #: mistyped argv, and which of the two a capture is takes meaning this tool has none of.
    stopped: bool = False

    @property
    def ran(self) -> bool:
        return not (self.missing or self.unstaged)

    def __str__(self) -> str:
        if self.missing:
            return f"not replayable: the capture has no {', '.join(self.missing)}"
        if self.unstaged:
            # Said differently from the above on purpose: the capture is not incomplete, the
            # *staging* is — and what to do about it is to take the capture again, not to stop
            # redacting it.
            # Naming the flag to a reader who cannot pass it (RK481): they hold a finished
            # capture and the session that took it is gone, so the door is *asking* rather
            # than running — which is a thing this reader can actually do, and the reason
            # RK313 gives for closing on something rather than on the fact alone. The
            # instruction lives where it can be followed: `report` says it as it writes.
            return (
                f"not replayable: the config declares {', '.join(self.unstaged)}, "
                f"which the capture does not carry — ask for one taken with `--embed`"
            )
        verdict = "still reproduces" if self.reproduces else "no longer reproduces"
        said = f"{verdict}: recorded exit {self.recorded_exit}, now {self.exit_code}"
        # First of the three, and the only one that qualifies what the verdict is *about*
        # rather than what it was reached under (RK443). Said on both verdicts, because a
        # capture that stopped at a usage refusal is one whose evidence never reached the
        # rule either way — and said first, since a reader who meets it after the caveat
        # about environments has already read the sentence as being about the symptom.
        if self.stopped:
            return (
                f"{said} — the capture's own re-run was refused before the verb ran, so "
                f"this repeats that refusal and not the symptom it was filed under"
            )
        # A *negative* verdict is an inference from an absence, and an unstaged environment is
        # another absence — so the two are said together or the first reads as a fix (RK341).
        # A positive one needs no caveat: the run just demonstrated it.
        if self.drifted:
            return f"{said}, under a different {', '.join(self.drifted)} than the capture recorded"
        # Before the environment clause and only where the verdict is negative: a capture
        # that still reproduces is live whatever version took it, and one that does not is
        # the case triage was reading the package to decide (RK1078).
        if self.aged and not self.reproduces:
            return f"{said} — {self.aged}"
        if self.drifted is None and not self.reproduces:
            return f"{said}, and the capture records no environment to have staged"
        return said


def replay(recorded: Mapping[str, object], workdir: str | Path) -> Replay:
    """Stage the capture's own inputs in ``workdir`` and run its argv against them.

    The reporter's repository is never needed and never reached: what is written is the
    `roadkeep.toml` and the one file the capture carries, and the `-C` in the recorded argv
    is repointed at the staging. Everything else in that argv is passed through untouched —
    a replay that rewrote the flags would be testing a command nobody ran.

    And a staging that is not the project answers nothing (RK343). Measured on `list --block Z`:
    exit 2 recorded and exit 2 replayed, where the second 2 was `No such file or directory` and
    the verdict was `still reproduces`. Every declared file is checked for before the run,
    because after it the exit code has already collapsed the two causes into one number — and
    what closed the gap on the other side is `--embed` carrying all of them (RK344).

    What this **cannot** stage is the environment (RK341), and the reason is two boundaries
    this deliberately keeps. :func:`observe` runs the argv through the `main` this interpreter
    already loaded, because a subprocess would be a second engine to be wrong about (RK79) —
    and an interpreter's stdio codecs are settled before its first line runs, so no assignment
    here reaches them. It then redirects both streams into a `StringIO`, which has no codec at
    all, so the encoding path is not even on the route a replay takes. Hence the *comparison*:
    the recorded facts are held against this process's, and a verdict reached under different
    ones says so rather than reading as a fix.
    """
    carried = _carried(recorded)
    held = {"command": recorded.get("argv"), "config": recorded.get("config"), "document": carried}
    needed = list(REPLAYABLE) + (["document"] if recorded.get("where") else [])
    missing = tuple(part for part in needed if not held[part])
    recorded_exit = int(recorded.get("exit", 0) or 0)
    stored = recorded.get("environment")
    drifted = _drifted(stored) if stored is not None else None
    # From the engine line every capture stamps (RK1078), so this reaches every report ever
    # filed rather than only the ones taken after the field existed.
    aged = _aged(recorded.get("engine"))
    # From the recorded exit code and never from a stored field (RK443), which is what makes
    # this reach the reports filed before RK440 wrote one: every capture ever taken carries
    # `exit`, and 2 is this CLI's own word for "the call was wrong".
    stopped = recorded_exit == _USAGE
    if missing:
        # Keyword arguments from here down: four optional fields in one constructor is where a
        # positional call starts assigning one reason to another's slot.
        return Replay(
            False, recorded_exit, 0, "", missing=missing, drifted=drifted,
            stopped=stopped, aged=aged
        )

    root = Path(workdir)
    (root / "roadkeep.toml").write_text(str(recorded["config"]), encoding="utf-8")
    for name, text in carried.items():
        document = root / name
        document.parent.mkdir(parents=True, exist_ok=True)
        # `newline=""`: the round-trip invariant is about bytes, and a translated line
        # ending is a different file from the one that failed.
        with document.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)

    # Before the run and not after it (RK343): the exit code is the whole of the evidence
    # wherever the failure named no address, and a staging the command cannot read produces the
    # same 2 as a usage error and the same 1 as a finding. Nothing was going to be learned, so
    # nothing is claimed.
    unstaged = _unstaged(root)
    if unstaged:
        return Replay(
            False, recorded_exit, 0, "", drifted=drifted, unstaged=unstaged,
            stopped=stopped, aged=aged
        )

    failure = observe(_repointed([str(part) for part in recorded["argv"]], root))
    where = recorded.get("where")
    reproduces = failure.exit_code == recorded_exit and (
        where is None or str(where) in failure.output
    )
    return Replay(
        reproduces,
        recorded_exit,
        failure.exit_code,
        failure.output,
        drifted=drifted,
        stopped=stopped,
        aged=aged,
    )


def _unstaged(root: Path) -> tuple[str, ...]:
    """The governed files the staged config declares and the capture never carried (RK343).

    Asked of :meth:`Config.missing`, which is the reader `lint` already uses to report
    `file.missing` — one rule and one implementation, so a role added to the format is staged
    and surveyed by the same list. Loaded from the written path rather than discovered, because
    a search upward from a scratch directory can find somebody else's project.

    A config that does not parse declares nothing, deliberately. A defect in *reading*
    `roadkeep.toml` is this repository's own first corpus entry: it has no governed file in its
    input at all, and demanding files from a config nobody could read would refuse to replay
    the one class of report that needs none.
    """
    try:
        config = Config.load(root / "roadkeep.toml")
    except (ConfigError, tomllib.TOMLDecodeError, OSError):
        return ()
    return tuple(config.relative(config.path(role)) for role in config.missing())


def _carried(recorded: Mapping[str, object]) -> dict[str, str]:
    """`path -> contents` for the files one stored capture holds, in either spelling.

    `documents` is what a capture written since RK344 carries. `document`/`document_path` is
    what every one before it carries, and reading both is what keeps a report already on
    somebody's disk runnable — a corpus that only accepts the current format is a corpus that
    loses the field reports it exists to keep.
    """
    documents = recorded.get("documents")
    if isinstance(documents, Mapping):
        return {str(name): str(text) for name, text in documents.items()}
    single, name = recorded.get("document"), recorded.get("document_path")
    return {str(name): str(single)} if single and name else {}

#: Where a capture lands before anybody decides what to do with it (RK89). A fifth path in
#: a repository that declared four — and one the repository never has to see, because the
#: same run teaches git to ignore it.
REPORTS = Path(".roadkeep") / "reports"

#: The line appended to `.gitignore`, and every spelling that already covers it. Nothing
#: here enters a history, a diff, or a review by somebody who never installed this tool.
IGNORE_RULE = ".roadkeep/"
_COVERED = frozenset({".roadkeep", ".roadkeep/", "/.roadkeep", "/.roadkeep/", ".roadkeep/**"})


#: A stamp naming a task in **another** repository: `owner/repo#ID` (RK1160). One spelling, and
#: it is the one every tracker already uses for a cross-repository reference, so an author who
#: types it is typing what they would paste into an issue.
#:
#: The id half is deliberately loose — a prefix and a number, with the optional suffix RK110
#: reads — because it belongs to a backlog whose `[ids]` this project cannot see. What is strict
#: is the **shape**: a qualifier without a repository is a local id with punctuation in it, and
#: this must never accept one, since the whole point is that it clears a row nothing checks.
DELIVERED = re.compile(r"^(?P<repo>[A-Za-z0-9._-]+/[A-Za-z0-9._-]+)#(?P<id>[A-Za-z]+\d+[a-z]?)$")


def delivered(stamp: str) -> str:
    """The repository a stamp names, or `""` where it names an id of this project's own.

    The reading RK1160 needed, and the reason it is a *shape* and not a lookup: a capture of a
    defect in this tool belongs in this tool's backlog and never in the project that hit it
    (`report --to OWNER/REPO`), so the id it was filed as is one no governed file here holds. Both
    readers resolved that stamp against the local backlog, so the row never cleared, and the two
    ways to silence it were a stamp from the wrong repository or deleting the evidence.

    A qualified stamp is therefore *filed by construction*: this cannot check another backlog and
    does not pretend to, so what it verifies is that the author named where the work went.
    """
    found = DELIVERED.match(stamp.strip())
    return found["repo"] if found else ""


@dataclass(frozen=True, slots=True)
class Held:
    """One capture the report directory already holds, and the claim it states (RK1139)."""

    path: Path
    #: The capture's own `symptom`, which is verbatim what `add --symptom` would receive — so
    #: an author who ran the pre-filled command produces an exact match and anything else
    #: reads as unfiled. Conservative in the safe direction: it nags rather than reassures.
    symptom: str
    #: The id this capture was filed as, where :func:`stamp` wrote one (RK1141). The reading
    #: that does not depend on prose: an author who reworded the symptom still clears the row,
    #: and a capture filed before this existed falls back to the match above.
    filed: str = ""
    #: Where it was aimed, where the capture recorded one (RK1161) — what lets a stamp of a bare
    #: id become the delivery it was, instead of asking for a repository twice declared.
    upstream: str = ""


def stamp(path: str | Path, task_id: str) -> bool:
    """Write into a capture the id it was filed as (RK1141). True where it landed.

    The fact lives in the **artefact**, which is the reading RK89 chose for everything in that
    directory: a capture is evidence, and what happened to it is part of the evidence. RK1139
    counted captures and cleared a row by an exact symptom match — right for an author who ran
    the pre-filled `add`, and permanent for one who reworded the sentence, which left this
    repository holding a row that could never reach zero.

    Never a condition of the write that calls it. `add` has already placed the line and saved
    the governed files by the time this runs, so a capture that cannot be stamped costs the
    link and never the task — the rule :func:`~roadkeep.claiming.follow` keeps for a claim, for
    the same reason: the durable half is in the repository and this is the transient one.

    Keeps every other key exactly as it was, because a capture is what a replay runs from: the
    payload is re-serialised from what was read, and a file this cannot parse is left alone.
    """
    target = Path(path)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return False
        payload["filed"] = task_id
        target.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    except (OSError, ValueError):
        return False
    return True


@dataclass(frozen=True, slots=True)
class Read:
    """One capture, and what this project can honestly say about it (RK1162).

    Three states and not two, because `filed` was two facts wearing one number: a stamp
    resolved against this project's own ids is a **resolution**, and a stamp naming another
    repository is a **claim** nothing here can check — which is what RK1160 made the row clear
    on. A tuple growing a third position would have carried the distinction and named neither.
    """

    path: Path
    filed: bool
    #: The repository a delivery names, or `""` for a capture this project resolved itself.
    elsewhere: str = ""


@dataclass(frozen=True, slots=True)
class Debt:
    """The captures a project holds that its backlog has not answered for (RK1139).

    A record and no longer a bare tuple read twice (RK1170): `stats` composed both registers
    from the same list, and each half called the reader again — so a project with captures paid
    the glob and the parse of three governed files once per register that asked.
    """

    held: tuple[Read, ...] = ()

    @property
    def unfiled(self) -> tuple[Path, ...]:
        return tuple(one.path for one in self.held if not one.filed)

    def stated(self, config: Config, width: int) -> list[str]:
        """The captures this project owes an entry for, and the total behind them (RK1143).

        Rows **only where one is unfiled**, which is not the rule the counts beside this follow
        — they print at zero because a field that appears only when it is non-zero is one a
        reader stops looking for. Two differences decide it. `uncounted` is about the file the
        command reports on and a capture is not; and a row that says nothing is owed is never
        the next step, which is RK1121's finding one command over — measured here, where
        `captures 2  2 filed` printed on every run of a tree with no debt at all, for ever,
        because nothing deletes a capture.

        The **total rides on the row** rather than being lost with it: the number a reader wants
        beside "one is unfiled" is how many there are. What silence costs is that the directory
        has files at all, and that is what :meth:`payload` keeps — a key costs a client nothing
        to skip, where a line costs every reader the same attention on every run.
        """
        unfiled = self.unfiled
        if not unfiled:
            return []
        rows = [f"  {'captures':<{width}}  {len(self.held):>4}  {len(unfiled)} unfiled"]
        # Named and not only counted: this is the list the tool asks every project to hold its
        # debt in, and a count with nothing behind it is the silent file again.
        rows += [
            f"  {'unfiled':<{width}}  {config.relative(one)}" for one in unfiled
        ]
        return rows

    def payload(self, config: Config) -> dict[str, object]:
        """The three states, told apart (RK1162).

        `filed` counted a stamp this project resolved and a stamp nothing here can check as one
        number, so a consumer reading `filed: 2` could not tell two closed rows from one closed
        row and one somebody says is closed elsewhere.
        """
        return {
            "kept": len(self.held),
            # Resolutions only: `kept` is still the total, and a client that added `filed` to
            # `delivered` gets what this key used to mean.
            "filed": sum(1 for one in self.held if one.filed and not one.elsewhere),
            "delivered": [
                {"path": config.relative(one.path), "repository": one.elsewhere}
                for one in self.held
                if one.elsewhere
            ],
            "unfiled": [config.relative(one) for one in self.unfiled],
        }


def debt(config: Config) -> Debt:
    """Each capture this project holds, and whether the backlog already states its claim.

    The reading RK1139 asked for, and the cheap order matters: the directory is globbed first,
    so a project with no captures — which is every project that has never hit a defect in this
    tool — pays one `glob` and never the parse of three governed files.

    "Filed" is an **exact symptom match**, because the capture's symptom is verbatim what
    `add --symptom` receives: an author who ran the pre-filled command produces one, and an
    author who reworded it reads as unfiled. Wrong in the direction that nags.
    """
    from roadkeep.backlog import Backlog  # noqa: PLC0415 - RK260

    held = captures(config.root)
    if not held:
        return Debt()
    backlog = Backlog.load(config)
    documents = [
        one for one in (backlog.roadmap, backlog.ledger, backlog.store) if one is not None
    ]
    stated = {entry.task.symptom for one in documents for entry in one.entries}
    ids = {entry.task.id for one in documents for entry in one.entries}
    # The stamp first and the prose second (RK1141): an author who ran the pre-filled `add`
    # cleared this row by the act that closed it, and one who reworded the symptom is why the
    # match alone left a row that could never reach zero. An id no file holds does not clear it
    # — a stamp naming a task that was renumbered away is a link and not an outcome.
    # **Unless the stamp names another repository** (RK1160): a capture of a defect in this tool
    # belongs in this tool's backlog, so its id is one no governed file here will ever hold, and
    # both readings above left a row that could only be silenced by a stamp from the wrong
    # repository or by deleting the evidence. Filed by construction, because this cannot read
    # that backlog and does not pretend to.
    return Debt(
        tuple(
            Read(
                path=one.path,
                filed=bool(delivered(one.filed))
                or (one.filed in ids if one.filed else one.symptom in stated),
                elsewhere=delivered(one.filed),
            )
            for one in held
        )
    )


def captures(root: str | Path = ".") -> tuple[Held, ...]:
    """Every capture on disk, in filename order — which is time order (RK1139).

    A capture was write-only: `report` printed `kept <path>`, and nothing listed, counted or
    contradicted it. Measured directly — a session ran `report` twice, read that line as
    "filed", and reported the work done; `stats` answered `total 2` and was right, which is
    what made the mistake invisible. This is the reader that lets a count disagree.

    Read defensively, one file at a time: a capture is evidence somebody may have hand-edited,
    and a directory that cannot be parsed must not stop a query. What a file without a
    `symptom` is is not a capture this can say anything about, so it is skipped rather than
    counted as unfiled — a number that included junk would be a number nobody trusts.
    """
    directory = Path(root) / REPORTS
    out: list[Held] = []
    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        symptom = payload.get("symptom") if isinstance(payload, dict) else None
        if isinstance(symptom, str) and symptom:
            stamped = payload.get("filed")
            aimed = payload.get("upstream")
            out.append(
                Held(
                    path=path,
                    symptom=symptom,
                    filed=stamped if isinstance(stamped, str) else "",
                    upstream=aimed if isinstance(aimed, str) else "",
                )
            )
    return tuple(out)


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


def _documents(root: str | Path) -> tuple[tuple[str, str], ...]:
    """Every governed file the config declares, whole and verbatim — never the project (RK344).

    Declared and not discovered: what leaves is the list a reader can check against the
    `roadkeep.toml` printed beside it, which is the form of disclosure RK87 asks for. A file
    that is declared and absent is simply not carried — that is a finding of its own
    (`file.missing`), and inventing an empty one would stage a project the reporter did not have.
    """
    try:
        config = Config.discover(root)
    except (ConfigError, tomllib.TOMLDecodeError, OSError):
        # The config is the defect. There is nothing declared to carry, and `_unstaged` reads
        # that same unparseable file back to the same conclusion.
        return ()
    carried: list[tuple[str, str]] = []
    for role in config.paths:
        path = config.path(role)
        try:
            carried.append((config.relative(path), path.read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError):
            continue
    return tuple(carried)


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
