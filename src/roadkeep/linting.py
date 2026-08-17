"""The gate: every governed line, validated where nothing else was watching (RK14).

`add` refuses a field at the moment it is typed (L1), which is where the saving is — but
a file also drifts by the paths `add` does not own: a hand edit, a merge that resolved
into a half-line, a `roadkeep.toml` limit lowered after the lines were written. So this
is the backstop, and the one thing that makes it a gate rather than advice is the exit
code: **exit 1 when anything drifted**, so a pre-commit hook and an Action (RK17) can
both call the same command and neither has to parse a report.

It re-validates rather than re-implements. Every rule read here comes from
:meth:`Schema.validate`, every line from :class:`Document`, every dep resolution from
:mod:`roadkeep.backlog` — a linter with its own regexes over prose would be a second
statement of the format, and the two would disagree in the direction nobody tests.

What it reports, and why each one is a defect the other commands cannot see:

* **A schema violation** on a line that exists — the limit that was raised after the
  line was written, or the line that never went through `add`.
* **A line that does not round-trip** (L3). Reported and never repaired: normalizing a
  line the parser may have misread is the corruption the whole invariant exists to
  prevent, so what this prints is the canonical rendering and the fix stays a human's.
* **A marker-bearing bullet the grammar rejected** — the silent miss `audit` (RK10)
  prints at exit 0. `audit` reports; this fails.
* **One id in two places** — twice in one file, or in both the roadmap and the ledger.
  Two lines carrying one id is two answers to "is this done?", and nothing says which.
* **A dep nothing can satisfy** — an id in neither file (a typo, or a line deleted by
  hand), a dep on a task that was retired (RK32: the record says the work will not
  happen, so the dependent line is the author's next edit), or `Block X` where no
  heading declares X (RK37). An *external* dep is not a finding: real work waits on
  things this backlog does not track, and Turing writes them on purpose.
* **A stale `(deps: … ✅)` annotation** — derived on every write (RK8), so a divergence
  here means the file was edited by something that is not this tool.
* **A cycle** — three tasks waiting on each other are three tasks nothing can start
  (RK13), which is a defect and not a shape.
* **A queue entry naming work that has left** (RK326) — the same resolution, applied to
  the one list that outranks the id order: shipped, retired, set aside, naming nothing,
  or naming a block whose every line has left or been set aside. Written as deps, most already
  failed here; written as a priority they passed at exit 0 while `pick` said only that
  the queue "names nothing ready".

And the same question asked of the prose file, which is RK15's half: **a pointer that
resolves to nothing reads exactly like a design that exists**, which is worse than no
pointer because it makes a reader stop looking. So the `→ §RK<n>` is resolved against
the improvements file, in both directions — a pointer with no section, and a section no
line points at — plus the section's word budget and the paths a line claims. The
pointer is read from the parsed ``ref`` field and never from the line's text: §RK15's
own `why` quotes a pointer as an example, and a scan over the line would report that
quotation as the broken pointer it is not. And once from the prose end alone (RK239): two
files declaring one anchor is a defect at both headings whether or not a line reached it.

And the one block the tool writes **outside** a governed file: a projection of the backlog
is derived rather than restated (RK39), and nothing held the derivation to the files it came
from — so a commit that ships a task and forgets `export` left a README contradicting the
ledger, caught here by a pytest fixture an adopting project does not install (RK104). The
markers are the author's declaration, so a file carrying none is silent; a file carrying them
is spliced in memory and compared, and a difference is one finding naming the command.

And one file the tool never writes: **an always-loaded instruction file has a budget, and
a budget stated in its own prose is what let Shio's `agents.md` reach 186 KB** while
declaring 150 lines at the bottom of itself (RK30). So `roadkeep.toml` declares it and the
exit code holds it, in lines and in bytes — the two units the reader actually pays.

**Two tiers, because the exit code is the contract.** A :class:`Finding` fails the build;
a :class:`Note` is something the gate says at exit 0. Both exist because two real defects
cannot be refused without failing an honest file: `Block P` is a legitimate dep that
happens to name forty-eight open tasks (RK35), and a rationale section edited without its
task line is the shape of a smuggled requirement *and* of a typo fix (RK36). Refusing
either would produce a gate that gets bypassed, which is worth less than a sentence read
at the moment of the commit — the same split `audit` (RK10) makes.

Everything above is decidable from the files as they are. The checks that are about a
*change* are opt-in through ``since``, because `lint` has to keep working in a checkout with
no history: `--since HEAD` in a commit hook, the base branch in CI. The second of them is a
block this commit **emptied or reopened** (RK269) — the transition `ship` computes, states
once to a console and records nowhere, which is what left a project's derived per-block index
claiming a finished block was active while `lint` called the tree clean four times running.

**And one question the absolute count cannot answer: did this change make it worse (RK84).**
An adopting project arrives with history — one live corpus lints at 317 problems, none of
them the current change's — so the gate cannot be wired to its CI, and the number moving by
one or two per task carries no signal. ``baseline`` reads the governed files *at a revision*,
runs everything above over those, and reports only the excess: what this working tree added,
with the standing debt named and forgiven. It exits non-zero on the difference alone, which
is the shape that lets a repository adopt the gate before it has paid the debt off. Two
things it deliberately does **not** vary: the configuration, because a limit is the ruler and
not the thing measured, and the repository, because what a baseline run stashes is the three
files — which is what the hand procedure it replaces did, four commands at a time.

What is deliberately *not* here: normalizing what is mechanical, which is a write and lives
in :mod:`roadkeep.fixing` (RK16). This module answers one question completely and never
writes: *is every line in the governed files a line this format accepts, does everything it
points at exist, and did anything loaded every turn outgrow what it was allowed?*
"""

from __future__ import annotations

import os
import re
import unicodedata
import functools
from collections.abc import Callable, Sequence
from typing import Any
from dataclasses import dataclass, field, replace
from pathlib import Path

from roadkeep import queueing, scoping
from roadkeep.backlog import Backlog, DepStatus, Stage, id_order
from roadkeep.blocking import removable
from roadkeep.config import PROSE_ROLES, ROLES, Config, spent, translated
from roadkeep.kernel.document import Document, Entry, Heading, ending
from roadkeep.exporting import (
    BEGIN,
    DEFAULTS,
    NoMarkers,
    enclosing,
    project,
    splice,
    target_of,
)
from roadkeep.graph import Graph
from roadkeep.history import (
    HistoryUnavailable,
    check_ignore,
    blob_at,
    content_at,
    resolves,
    touched_since,
    tracked_at,
    tracked_now,
)
from roadkeep.markers import derive
from roadkeep.referring import PAIRS
from roadkeep.kernel.schema import (
    CODEPOINT_KINDS,
    TAB,
    Dep,
    DepKind,
    Task,
    codepoint_kind,
    indentation,
    over_by,
    suspect,
)
from roadkeep.sections import Section, anchored, find, references
from roadkeep.sections import owners as section_owners
from roadkeep.showing import known_directories, on_disk, paths_in
from roadkeep.provenance import invocation

#: The governed files whose unit is a task line. The prose files are paragraphs, so
#: their gate is a pointer and a budget — RK15 and RK30, not this. The deferred store is
#: one of them (RK96): a line set aside is still a line, and a store nothing gated would
#: be the one place the format is a convention again.
#: "Nobody has asked yet", which None cannot say here: None is the answer meaning "git
#: could not tell us", and the two have to be different things (RK217).
_UNASKED = object()

LINE_ROLES = ("roadmap", "changelog", "deferred")

#: The two whose lines are still alive, so their rationale section is still there: open
#: work, and work set aside (RK96). The ledger is not among them — `ship` and `retire`
#: delete the section in the transaction that writes the entry.
LIVE_ROLES = ("roadmap", "deferred")

#: The codes both surfaces raise, where this file's own scan is the better half (RK499). The
#: schema refuses these at the door, naming a position inside the argument the caller retypes;
#: `_characters` finds them anywhere in the file, naming the line and the column. One defect,
#: two readings, and the gate prints the one addressed to a reader of the file.
_SCANNED = frozenset({"char.tab", "char.space", "char.invisible"})

_ENDING_NAMES = {"\r\n": "CRLF", "\n": "LF", "\r": "CR"}


@dataclass(frozen=True, slots=True)
class Finding:
    """One defect, at one place. ``code`` is stable; ``message`` names the fix.

    The code is the same string :class:`~roadkeep.kernel.schema.Violation` uses where the
    finding came from the schema, so a caller filtering on `why.sentences` filters the
    same rule whether it was refused at `add` or found here.
    """

    code: str
    file: str
    message: str
    #: 1-based, as an editor counts. ``None`` when the finding is about the file itself.
    lineno: int | None = None
    id: str = ""
    #: 1-based column, for a finding about one character (RK34). An invisible codepoint
    #: cannot be found by eye, so the offset is half of what makes the report usable.
    column: int | None = None
    #: What the remedy is *about*, where that is not the id and not printable as a prefix
    #: (RK420). `id` already doubles as the subject on most codes — a block label, a section
    #: anchor — because it is printed in front of the message and reads correctly there. A
    #: queue token does not: the message opens `queues RK12, …`, so putting it in `id` would
    #: render `RK12: queues RK12`. Last field, so every positional call site still means what
    #: it did.
    subject: str = ""
    #: What this finding has in common with its siblings, where a whole group of them is one
    #: fact and one edit (RK469). Empty on every code but the one that needed it: a report
    #: whose bulk is one sentence repeated is one a reader learns to skip (RK146), and it
    #: buries the findings that are each about a different line.
    #:
    #: Declared by the **emitter**, which is the only place that knows what is shared —
    #: string surgery on the message would be a second reading of a sentence this file
    #: composes. Read only by the terminal report: `--json` keeps one entry per address,
    #: because a consumer acting per address needs the line, and the count that follows the
    #: findings is about addresses either way.
    shared: str = ""
    #: The file this finding is *about*, where that is not the file it is filed against
    #: (RK1070). One code needs it: `grammar.unreadable` lands on `roadkeep.toml`, because
    #: the declaration that broke the file is there and so is the edit (RK1067), and it
    #: explains every per-line failure in the file it names. Two addresses and not one —
    #: `file` is where a reader clicks, `about` is what the finding covers — because
    #: conflating them is how a suppression silences the wrong file.
    about: str = ""

    @property
    def token(self) -> str:
        """What a remedy substitutes: the explicit subject, or the id it usually is."""
        return self.subject or self.id

    @property
    def where(self) -> str:
        if self.lineno is None:
            return self.file
        if self.column is None:
            return f"{self.file}:{self.lineno}"
        return f"{self.file}:{self.lineno}:{self.column}"

    def __str__(self) -> str:
        subject = f"{self.id}: " if self.id else ""
        return f"{self.where}  {self.code}  {subject}{self.message}"


@dataclass(frozen=True, slots=True)
class Note:
    """Something the gate says and does not fail on (RK35).

    A separate list from :class:`Finding` because the exit code is the contract: `Block P`
    is a legitimate dep (RK28) and failing a build over one would fail the honest backlog
    this tool was measured against. But it is one token naming forty-eight open tasks, and
    a reader counting deps to judge how blocked a line is has no way to see that from the
    line — so the expansion is stated, at exit 0, which is the same split `audit` (RK10)
    makes between reporting a miss and being the gate.
    """

    code: str
    file: str
    message: str
    lineno: int | None = None
    id: str = ""
    #: The same field :class:`Finding` grew for the same reason (RK420): a note carries a
    #: remedy too, and the thing it is about is not always printable in front of a message.
    subject: str = ""

    @property
    def token(self) -> str:
        return self.subject or self.id

    def __str__(self) -> str:
        where = self.file if self.lineno is None else f"{self.file}:{self.lineno}"
        subject = f"{self.id}: " if self.id else ""
        return f"{where}  {self.code}  {subject}{self.message}"


@dataclass(slots=True)
class Tree:
    """Where one run reads the governed files from: this working tree, or a revision (RK84).

    Every disk touch a run makes on a file it *governs* goes through here, which is the whole
    of how a baseline is taken — the documents, the budgeted files, and whether a declared
    file is there at all. What does not go through here is the rest of the repository: a
    baseline varies the three files and holds the code constant, because that is the question
    being asked, and because resolving a whole tree would make the comparison a checkout.

    Bytes, and not text: a governed file is compared to its own rendering byte for byte (L3)
    and a budget is spent in them (RK30), so a revision read through newline translation
    would answer both wrongly.
    """

    config: Config
    #: ``None`` for the working tree — the run every other command makes.
    rev: str | None = None
    #: The revision's paths, read once and only if something asks (`ls-tree` is not free).
    _names: frozenset[str] | None = field(default=None, repr=False)
    #: One read per file: `_absent` asks whether it is there and everything else asks what
    #: is in it, which at a revision is two subprocesses for one answer.
    _blobs: dict[Path, bytes | None] = field(default_factory=dict, repr=False)
    #: Every tail of every tracked path, built once (RK173). Unbuilt until something asks,
    #: because only one check needs it and a `ls-files` per run of `show` would be a cost
    #: paid by the callers that never ask about an artefact at all.
    _tails: frozenset[str] | None = field(default=None, repr=False)
    #: What the repository declared untracked, per token (RK213, keyed by RK219). A dict
    #: and not a set-of-the-first-answer: the key is the question, so a second caller — or
    #: a second pass — is answered about what it asked rather than about what came first.
    _ignored: dict[str, bool] = field(default_factory=dict, repr=False)
    #: The directories a path claim is decided against (RK217), or None where git could not
    #: say — a sentinel rather than None-means-unasked, because None is itself the answer.
    _directories: frozenset[str] | None | object = field(default=_UNASKED, repr=False)
    #: The root as a normalised string, so the constant half of a spelling is built once.
    _root: str | None = field(default=None, repr=False)

    def document(self, role: str) -> Document | None:
        """One governed file under its role's schema, or ``None`` when this tree lacks it."""
        if not self.config.has(role):
            return None
        if self.rev is None:
            path = self.config.path(role)
            return self.config.document(role) if path.is_file() else None
        raw = self.blob(self.config.path(role))
        if raw is None:
            return None
        # Deliberately parsed without its path: a document of how a file *was* must not be
        # one call away from being saved over the file as it is.
        return Document.parse(
            raw.decode("utf-8", errors="replace"), schema=self.config.schema_for(role)
        )

    def blob(self, path: Path) -> bytes | None:
        if path in self._blobs:
            return self._blobs[path]
        if self.rev is not None:
            found = blob_at(self.config, self.rev, path)
        else:
            found = path.read_bytes() if path.is_file() else None
        self._blobs[path] = found
        return found

    def present(self, path: Path) -> bool:
        """Whether this tree carried the file at all, without reading one to find out."""
        return path.is_file() if self.rev is None else self.blob(path) is not None

    def carries(self, token: str, near: Path) -> bool:
        """Did this tree have the artefact a line names, under either convention (RK51)?

        Asked only of a revision, and only to *withhold* a `path.missing` the baseline should
        never have credited: a file that was there at the ref and is not here now was deleted
        by this change, and forgiving that would forgive the one true finding this check has
        produced on a live corpus — a class the ledger still names under the directory it was
        renamed inside.
        """
        if self.rev is None:
            return False
        return any(spelling in self.listing() for spelling in self.spellings(token, near))

    def declared_untracked(self, tokens: Sequence[tuple[str, Path]]) -> frozenset[str]:
        """Which tokens name a path the repository has declared it will never track (RK213).

        The next shape along from RK173's widening, and the one an adopter hit first. Claude
        Code Tray's ledger names `bin/Release/net10.0-windows/win-x64/ClaudeTray.exe` while
        explaining why its CI builds rather than publishes — a correct sentence about where
        the build output lands. `bin/` is the first line of its `.gitignore`, and its
        roadkeep job is `checkout` then the action, so `lint` exited 1 on every push and 0
        on the machine of anyone who had just compiled. Invisible locally, and in CI the
        only finding, so the job was simply red.

        **Asked of git, not of a list.** A table of `bin/`, `dist/`, `target/`, `build/`
        here would be convention where the repository already has a declaration (L6), and
        it would be wrong for the project that tracks its `dist/` on purpose.
        `check-ignore` reads the same `.gitignore`, `.git/info/exclude` and core.excludesFile
        the developer's own `git status` reads, so the tool and the author cannot disagree
        about what this repository tracks.

        One call for every candidate, because the candidates are what survived `exists`,
        `carries` and `anywhere` — one or two on a live corpus — and a subprocess each would
        price a check by how broken the file is. Both spellings are asked (RK51): a token is
        relative to the ledger's directory or to the root, and either may be the ignored one.

        No git, no answer, and the finding stands: withholding where the question could not
        be asked would turn "this repository says so" into "nobody could say otherwise".

        Every token asked is recorded, ignored or not, so a repeat costs nothing and a new
        one costs the batch it arrives in (RK219). What is *not* recorded is the difference
        between "git said no" and "git could not be asked", because within one tree that
        cannot change: a run has one repository, and it either has git or it does not.
        """
        unknown = [(token, near) for token, near in tokens if token not in self._ignored]
        if unknown:
            declared = _declared_untracked(self.config, unknown)
            for token, _ in unknown:
                self._ignored[token] = token in declared
        return frozenset(token for token, _ in tokens if self._ignored[token])

    def spellings(self, token: str, near: Path) -> tuple[str, ...]:
        """How git could spell this token, from each base it may be relative to (RK51).

        Computed once and passed down (RK228): `holds` used to ask `carries`, which spelled
        the token, and then spell it again for the directory set — two answers to one
        question, and the profile's largest remaining row was the second one.

        The root prefix is the constant half, so it is normalised once for the whole run
        rather than 34133 times through `os.path.relpath`, which normcases both ends of
        every call. Nothing about the answer changes; only how often the part that cannot
        differ is recomputed.
        """
        return tuple(
            spelling
            for base in (near, self.config.root)
            if (spelling := _spelled(self._prefix(), str(base), token)) is not None
        )

    def _prefix(self) -> str:
        """The repository root as a normalised prefix, with its separator, built once."""
        if self._root is None:
            self._root = os.path.normpath(str(self.config.root))
        return self._root

    def listing(self) -> frozenset[str]:
        """Every path this tree still **has**, read once (RK173, RK217).

        Two checks want it — the tail index and the revision's membership test — so it is
        the tree's rather than each one's, and a run costs one listing however many ask.
        """
        if self._names is None:
            self._names = (
                tracked_now(self.config)
                if self.rev is None
                else tracked_at(self.config, self.rev)
            )
        return self._names

    def holds(self, token: str, near: Path) -> bool:
        """Does the tree this run is judging have what this token names? (RK84, RK218)

        The working tree answers from the disk, which is its subject. A revision answers
        from git, and from **both** shapes a token can name: a file is a tracked path, and
        a directory is a prefix of one — `docs`, `create-shio-app` and thirty-three more
        across the two pins are named as directories and were only ever admitted because
        they happened to be on somebody's disk.

        `exists` is a fact about *now*, so a run naming a revision may not consult it: an
        untracked file created since the ref, which git has never seen, used to silence a
        finding that revision genuinely had.
        """
        if self.rev is None:
            return on_disk(token, self.config.root, near)
        spellings = self.spellings(token, near)
        if any(spelling in self.listing() for spelling in spellings):
            return True
        directories = self.directories() or frozenset()
        return any(spelling in directories for spelling in spellings)

    def directories(self) -> frozenset[str] | None:
        """Which directories this repository knows, for deciding a claim (RK217).

        Not :meth:`listing`, and the difference is the defect: that one drops a file
        deleted from the working tree, which is right for "does the tree still have it" and
        exactly wrong here — a ledger naming `lib/gone.py` after `lib/` was removed would
        stop being a claim instead of becoming a finding. At a revision the two coincide,
        there being no working tree to have deleted anything from.
        """
        if self._directories is _UNASKED:
            # At HEAD the function's own default is the index, which is the listing this
            # question wants (RK221); at a revision the tree's listing already is that.
            self._directories = known_directories(
                self.config, None if self.rev is None else self.listing()
            )
        return self._directories

    def anywhere(self, token: str) -> bool:
        """Does this tree hold the artefact this token names, under **any** prefix? (RK173)

        A monorepo entry writes the path its reader is standing in — the frontend app, the
        showcase skill — because that is what a developer pastes from a terminal already
        inside it. Resolving from the repository root alone reported the difference as a
        missing file: of Turing's eight `path.missing` findings, six named artefacts the
        repository has, which is a signal ratio at which the class stops being read. Worse,
        it points at history — these are shipped entries, so the remedy the wording implies
        is editing what already happened.

        The question this check asks is whether the **repository has the artefact** (RK51),
        so the tail is what answers it, and a rename inside a directory — the one true
        finding this check has produced on a live corpus — still matches nothing.

        **Measured coming out, too** (RK189), because a widening whose cost is an argument
        is a widening nobody can price. Over both pins: Shio exercises the rule zero times
        in 1278 files, and Turing's ledger leaves six tokens unresolved, of which this
        silences five and reports the moved file. Four of the five are two-segment tokens
        matching exactly one tracked file — the match identifies the artefact rather than
        finding a name — and the fifth is the `./package.json` that motivated the rule,
        matching thirteen. So a one-segment token is admitted deliberately: requiring a
        slash would re-report that one and change none of the others. The exposure it
        accepts is real and unrealised — 17% of the files in each tree share a basename —
        and `tests/test_linting.py` is where all four numbers are held.
        """
        if self._tails is None:
            names = self.listing()
            self._tails = frozenset(
                "/".join(segments[start:])
                for name in names
                for segments in (name.split("/"),)
                for start in range(len(segments))
            )
        wanted = token.replace("\\", "/")
        while wanted.startswith("./"):
            wanted = wanted[2:]
        return wanted in self._tails


@dataclass(frozen=True, slots=True)
class Baseline:
    """What the same gate said at a revision, so this run can report only what it added.

    ``forgiven`` is the standing debt *as it still stands* — findings this working tree has
    and the revision had too. ``resolved`` is the other direction, and it is here for the
    reading that nearly hid a real defect: a run that deleted 160 lines of rationale it
    should not have took the count down by eight, and the drop read as an improvement until
    the two findings it *added* were looked at individually. One number cannot say both.
    """

    rev: str
    forgiven: tuple[Finding, ...] = ()
    resolved: tuple[Finding, ...] = ()

    @property
    def standing(self) -> int:
        return len(self.forgiven)


@dataclass(frozen=True, slots=True)
class Report:
    """What was checked, and everything wrong with it. Emptiness is the pass."""

    findings: tuple[Finding, ...]
    #: The files this run **judged**, as the project spells them — printed even when clean,
    #: because a gate that passed by reading nothing is the failure mode of every gate. Judged
    #: and not merely read, so every finding's file is in here (RK354): `roadkeep.toml` is one
    #: where it carries a queue and is not one where it only said which files to open.
    checked: tuple[str, ...]
    lines: int
    #: Anchored sections read in the prose file — the other half of what was checked.
    sections: int = 0
    #: Always-loaded files whose budget was measured (RK30).
    budgets: int = 0
    #: What the gate observed without failing on it (RK35). Never affects the exit code.
    notes: tuple[Note, ...] = ()
    #: The revision this run was measured against, when it was (RK84). Present means
    #: ``findings`` holds the difference and nothing else.
    baseline: Baseline | None = None

    @property
    def clean(self) -> bool:
        return not self.findings

    @property
    def problems(self) -> int:
        return len(self.findings)

    def stated(self, config: Config, applied: Fix, root: str, quiet: bool) -> None:
        """The gate's report, written as it is composed (RK14, RK35, RK420).

        Beside :meth:`payload` since RK1170 — one answer, on the record both readings are
        about. It **writes** rather than returning rows, which is the one exception this task
        leaves standing: a finding's remedy is fetched per finding and the mechanical class is
        counted while the rest are printed, so building the whole report as a list would hold
        a corpus-sized report in memory to hand it straight to `print`.

        `quiet` is the caller's: what it silences is the *body*, never the summary and never
        the refusals, because a pass that could not prove its own output wrote nothing.
        """
        _report_rows(config, self, applied, root, quiet)

    def payload(self, config: Config, applied: Fix, root: str) -> dict[str, object]:
        """The same answer as data, rooted first (RK299).

        Every path in it is relative to `root`, and a payload a second tool files against the
        wrong project is worse than one it cannot file at all — so the key comes first, spelled
        the way `install --json` already spells it.
        """
        return _lint_json(config, self, applied, root)

    def codes(self) -> dict[str, int]:
        """Findings per code, most first — the summary a report of ninety is read by."""
        found: dict[str, int] = {}
        for finding in self.findings:
            found[finding.code] = found.get(finding.code, 0) + 1
        return dict(sorted(found.items(), key=lambda pair: (-pair[1], pair[0])))


def lint(
    config: Config,
    since: str | None = None,
    baseline: str | None = None,
    at: str | None = None,
) -> Report:
    """Read every governed file and return every defect. Writes nothing, ever.

    ``at`` runs the whole gate over a **revision** instead of the working tree (RK210) —
    the read ``baseline`` already makes, given a name so a caller can make it alone. Both
    ends move together, which is the point: the governed files come from the revision *and*
    so does the repository the path check asks about, so nothing in the answer is half about
    this afternoon. Library-only, with no flag beside it: `--baseline` is the question a
    person asks at a terminal, and "what did the gate say at a revision" has one caller —
    the pinned-corpus fixture, whose whole difficulty was that a config can carry one root
    and a pinned run needs the governed files copied and the tree left where git can read it.

    ``since`` adds the checks that are about a *change* rather than a state — a section edited
    without its line (RK36), and a block this change emptied or reopened (RK269) — against a
    revision, `HEAD` in a pre-commit hook and the base branch in CI. Both are notes, and both
    are only askable of a diff: as states they are "somebody edited prose once" and "this
    block is empty", which are true forever and read by nobody.

    ``baseline`` answers the other question about a change (RK84): the same gate is run over
    the governed files as they were at that revision, and what comes back is the excess —
    so a repository with standing debt gets an exit code about *its own* commit. The two
    compose, and the baseline run makes no ``since`` comparison of its own: a note about a
    section edited since a ref is about this working tree either way.
    """
    if at is not None and not resolves(config, at):
        raise HistoryUnavailable(f"{at} is not a revision this repository knows")
    report = _examine(config, since=since, tree=Tree(config, at))
    if baseline is None:
        return report
    if not resolves(config, baseline):
        # Unlike `since`, this one cannot degrade to silence: the exit code is the answer,
        # and a run that could not read its baseline would report the whole debt as new.
        raise HistoryUnavailable(f"{baseline} is not a revision this repository knows")
    return _subtract(
        report, _examine(config, since=None, tree=Tree(config, baseline)), baseline
    )


def _examine(config: Config, since: str | None, tree: Tree) -> Report:
    """Every check, over whichever tree is being judged.

    A **loop over a declared domain** since RK1172, where it was 21 hand-wired calls whose scan
    kind lived in their parameter lists. What each rule reads is now a field on it, so the five
    inputs are built once here and each kind's iteration — the whole tree, every line-bearing
    role, one role, the prose with its anchor index — is written once below rather than at every
    call site. Adding a rule that scans something new says so; adding one that scans something
    already known costs a row.
    """
    documents: dict[str, Document] = {}
    for role in LINE_ROLES:
        document = tree.document(role)
        if document is not None:
            documents[role] = document
    prose: dict[str, Document] = {}
    for role in PROSE_ROLES:
        document = tree.document(role)
        if document is not None:
            prose[role] = document
    anchors = {role: anchored(document) for role, document in prose.items()}
    sections = tuple(section for found in anchors.values() for section in found)
    scanned = _Scan(
        config=config,
        tree=tree,
        documents=documents,
        prose=prose,
        anchors=anchors,
        since=since,
        # Read before the rules that want it, and not a check: a projection target is a fact
        # about the tree that two rules and the file list all ask for (RK1110).
        targets=_targets(config, tree),
    )

    findings: list[Finding] = []
    notes: list[Note] = []
    for rule in _rules():
        for one in rule.run(scanned):
            (notes if isinstance(one, Note) else findings).append(one)

    targets = scanned.targets
    checked = _checked(config, documents, prose, targets)
    # The second phase, run as the list it is (RK1172). Every rule above reads the *project*;
    # these three read what those produced — a whole file's worth of findings is evidence about
    # the rule rather than about a line (RK1068), what another finding already explains is not a
    # second finding, and the printed order is a fact about the report. Nested calls said the
    # same thing and said it inside out: `_ordered(_untainted(findings), checked)` puts the last
    # step first, and where a fourth fold goes was a question about parentheses.
    for fold in _FOLDS:
        findings = list(fold(findings, config=config, documents=documents, checked=checked))
    return Report(
        findings=tuple(findings),
        checked=checked,
        lines=sum(len(d.entries) for d in documents.values()),
        sections=len(sections),
        budgets=len(config.budgets),
        notes=tuple(notes),
    )


@dataclass(frozen=True, slots=True)
class _Scan:
    """Every input a rule can read, built once (RK1172).

    The five kinds the measurement found — the governed **tree**, the **documents** carrying task
    lines, the **prose** files, the **anchor** index derived from them, and a git **revision** —
    plus the projection targets, which are a reading of the tree that three rules share.

    One record and not a parameter list, so a rule that starts reading a second input changes its
    own row and nothing else: the signature `(config, documents, prose, targets)` was the fourth
    shape invented at a call site, and each new one made `_examine` the only place that knew.
    """

    config: Config
    tree: Tree
    documents: dict[str, Document]
    prose: dict[str, Document]
    anchors: dict[str, tuple[Section, ...]]
    since: str | None
    targets: tuple[Target, ...]

    @property
    def governed(self) -> dict[str, Document]:
        """Both halves, for the rules decided against the whole set and not one file (RK417)."""
        return {**self.documents, **self.prose}


@dataclass(frozen=True, slots=True)
class _Rule:
    """One gate rule: what it reads, and what it reports (RK1172).

    `remedying.py` has been a table keyed by code since RK420, and its argument — that a central
    domain is what a test can be total over — was only half applied: the *remedy* was a table and
    the *check* was sixty functions with signatures invented where they were called.

    :attr:`reads` is the field that removes the hand-wiring. It names one of the kinds
    :class:`_Scan` holds, and the loop below turns that name into the iteration: `role` runs the
    rule once per line-bearing document, `prose_role` once per prose file, `whole` once. A rule
    that fits none of them is the evidence the set is wrong, which is what this task asked for.
    """

    reads: str
    run: Callable[[_Scan], Sequence[Finding | Note]]


# Cached rather than built at import: `within` and half the rules below are defined further down
# this file, and a domain whose construction depended on definition order would break when a rule
# moves. One call, and the tuple is a value a test can be total over.
@functools.lru_cache(maxsize=1)
def _rules() -> tuple[_Rule, ...]:
    """The domain, in the order it runs (RK1172).

    Order is the reader's convenience and not a rule's requirement: `_ordered` sorts the report by
    file and line, and the two folds before it read the whole population — so nothing here depends
    on running before anything else, which is what makes a declared list safe.
    """

    def per_role(one: Callable[[Config, str, Document], Sequence[Finding]]) -> Callable[[_Scan], list[Finding]]:
        return lambda scan: [
            found
            for role, document in scan.documents.items()
            for found in one(scan.config, role, document)
        ]

    def characters(scan: _Scan) -> list[Finding]:
        # The character pass is a second walk over the same file, so the rule `within` holds has
        # to be read here too or the 3,301 findings it exists to replace come back from the other
        # side (RK451). The same predicate and not a second statement of it: `within` owns what
        # "not text" means and this asks it.
        return [
            found
            for role, document in scan.documents.items()
            if not _voided(document)
            for found in _characters(scan.config, role, document)
        ]

    def resolved(scan: _Scan) -> list[Finding]:
        if not scan.prose:
            return []
        found = list(_pointers(scan.config, scan.documents, scan.anchors))
        found += _citations(scan.config, scan.prose, scan.anchors)
        found += _crossing(scan.config, scan.prose, scan.anchors)
        for role, document in scan.prose.items():
            found += _orphans(
                scan.config, scan.documents, document, scan.anchors, role=role
            )
        return found

    def against_baseline(scan: _Scan) -> list[Note]:
        if scan.since is None:
            return []
        found = list(_turned(scan.config, scan.documents, scan.since))
        if scan.prose:
            found += _unpaired(
                scan.config, scan.anchors.get("improvements", ()), scan.since
            )
        return found

    def budgeted(scan: _Scan) -> list[Finding | Note]:
        found, said = _budgets(scan.config, scan.tree)
        return [*found, *said]

    def queued(scan: _Scan) -> list[Finding | Note]:
        found, said = _queue(scan.config, scan.documents)
        return [*found, *said]

    return (
        _Rule("tree", lambda scan: _absent(scan.config, scan.tree)),
        _Rule("role", per_role(within)),
        _Rule("role", characters),
        _Rule("documents", lambda scan: _across(scan.config, scan.documents)),
        _Rule("documents", lambda scan: _scope(scan.config, scan.documents.get("roadmap"))),
        _Rule("documents", queued),
        _Rule("documents", lambda scan: _collective(scan.config, scan.documents)),
        _Rule("tree", lambda scan: _disagreeing(scan.config, scan.tree)),
        _Rule("revision", against_baseline),
        _Rule("prose_role", lambda scan: [
            found
            for role, document in scan.prose.items()
            for found in _marks(scan.config, role, document)
        ]),
        _Rule("anchors", resolved),
        _Rule("governed", lambda scan: _repeated(scan.config, scan.governed)),
        _Rule("tree", lambda scan: _paths(scan.config, scan.documents, scan.tree)),
        _Rule("governed", lambda scan: _projections(scan.config, scan.governed, scan.targets)),
        _Rule("tree", budgeted),
        # Its own rule and not a tail of `budgeted` (RK1192): what a surface costs and whether
        # it is the one this engine ships are two questions, and a check folded into another's
        # return is one nobody finds by reading the list of what this gate asks.
        _Rule("config", lambda scan: _wired(scan.config)),
    )



def _folding(name: str) -> Callable[..., Any]:
    """One rule of the reporting phase, adapted to the one shape a fold has (RK1172).

    The three read different things — a document set, the findings alone, the file order — so
    an adapter is what lets the phase be a list. Written here rather than by changing each
    rule's own signature: what a rule wants is a fact about that rule, and a uniform parameter
    list that every caller then ignores half of is the hand-wiring one layer up.
    """
    def fold(findings: list[Finding], **inputs: Any) -> Sequence[Finding]:
        if name == "grammatical":
            return _grammatical(inputs["config"], inputs["documents"], findings)
        if name == "untainted":
            return _untainted(findings)
        return _ordered(findings, inputs["checked"])

    fold.__name__ = f"fold_{name}"
    return fold


#: The reporting phase, in the order it runs (RK1172). The fold before the drop before the sort,
#: because each reads what the one before it left: the inference needs the whole population, the
#: drop needs the fold's own finding to exist before it can suppress what that explains, and the
#: order is over whatever survived. Three names in a list, where the order used to be the shape
#: of an expression.
_FOLDS: tuple[Callable[..., Sequence[Finding]], ...] = (
    _folding("grammatical"),
    _folding("untainted"),
    _folding("ordered"),
)


def _checked(
    config: Config,
    documents: dict[str, Document],
    prose: dict[str, Document],
    targets: tuple[Target, ...],
) -> tuple[str, ...]:
    """Every file this run judged, in the order its findings print in (RK365).

    One place, because the list is two things at once: what the report *says* was read, and
    the sort key :func:`_ordered` applies to every finding. It was appended to at five points
    down `_examine`'s body, three of them conditional, so the order findings print in was
    decided by where a check happened to be added rather than by anything anybody wrote down.

    The order is the reader's. The line-bearing files first, because they are what this format
    is about; the prose they point into next; then the files this tool does not own — a
    projection target, an instruction file with a budget — and `roadkeep.toml` last, judged
    only where it carries a queue (RK354) and not a governed file at all.

    Conditional membership is the rule and not the exception: a budgeted file is here because
    `[budgets]` names it, a target because a marked block asked to be projected into it, and
    the config because it declared an order. What decides each is one expression, all four in
    view of each other.
    """
    checked = [config.relative(config.path(role)) for role in documents]
    checked.extend(config.relative(config.path(role)) for role in prose)
    checked.extend(target.where for target in targets)
    checked.extend(config.relative(budget.path) for budget in config.budgets)
    # The config is judged where it declares a queue (RK354) and where it declares what a
    # served tool may cost (RK1059) — the second being the one budget whose subject is not
    # a file, so `roadkeep.toml` is both what declared it and the only place to name.
    if config.priority or config.tool_characters is not None:
        checked.append(_configured(config))
    return tuple(checked)


#: How many lines a file must hold before *all* of them failing the round-trip reads as the
#: rule rather than the lines (RK1068). Two, because one line disagreeing with the schema is
#: an edited line and is exactly what `line.non-canonical` is for — the inference is about a
#: population, and a population of one is a line.
_A_POPULATION = 2


def _grammatical(
    config: Config, documents: Mapping[str, Document], findings: list[Finding]
) -> list[Finding]:
    """Fold a whole file's worth of non-canonical lines into one defect at the rule (RK1068).

    The cost a declared grammar does not remove, caught at the end it is actually about. A
    grammar given as data (RK1064) can be one that cannot read back what it writes, and the
    round-trip guard then refuses the whole file — correctly and by law — so a separator
    declared one character too loose presents as **every line in the corpus** being
    non-canonical, and the report blames a hundred lines for the one line of config that
    broke them.

    **Both ways a line can fail it**, which measuring made the point of: a declaration too
    *loose* renders what it read differently and the file comes back `line.non-canonical`,
    and one too *narrow* — a slot dropped that the file has — stops matching at all and the
    same file comes back `line.unparsed`. The second is what a wrong `drop` actually
    produces, so a fold that watched only the first would miss the failure it was written
    for. A bullet counts either way, which is why the population is entries **and** rejects.

    The inference is deliberately narrow: *every* line-shaped bullet in a role's file, and
    at least :data:`_A_POPULATION` of them. One line differing from its rendering is an
    edited line and is what `line.non-canonical` already says; a file where not one bullet
    survives is not a file somebody hand-edited into that state.

    Paired with RK1067, which is what makes the answer actionable rather than merely
    correct: the finding lands on the declaration's own line, so the report reads as one
    defect at one config line instead of a corpus that stopped conforming.
    """
    explained = next(rule for rule in EXPLAINS if rule.by == "grammar.")
    out = list(findings)
    for role, document in documents.items():
        population = len(document.entries) + len(document.rejects)
        if population < _A_POPULATION:
            continue
        where = config.relative(config.path(role))
        # Counted against the same rule that will suppress them (RK1070), so "which failures
        # is this an explanation of" is one declaration and not a literal here and a
        # predicate there. Nothing is removed by this function: it *reports*, and
        # :func:`_untainted` drops what the report explains — which is what keeps the
        # removal from being identity over a dataclass, where two findings that compare
        # equal on one line went together or not at all.
        broken = sum(
            1 for finding in out if finding.file == where and explained.explains(finding)
        )
        if broken < population:
            continue
        declared = config.grammars.get(role)
        out.append(
            Finding(
                "grammar.unreadable",
                _configured(config) if declared else where,
                f"the grammar for {role} fails on {population} of {population} bullets: "
                f"this is the rule and not the lines, and a file where none survives is "
                f"not one somebody hand-edited"
                + (
                    f" — `[grammar.{role}]` is what to look at"
                    if declared
                    else " — no [grammar] is declared, so the file was written under "
                    "another format"
                ),
                subject=role,
                # What it covers, which is not where it is filed (RK1070): the declaration
                # is in the config and the lines it explains are in the governed file.
                about=where,
            )
        )
    return out


@dataclass(frozen=True, slots=True)
class Explains:
    """One finding that makes another one noise, declared (RK1070).

    Two checks in this module do this and neither said so: a codepoint nobody typed makes
    every other diagnosis of that line a consequence (RK34), and a grammar that fails on a
    whole file makes every per-line failure in it an effect (RK1068). Both were a predicate
    and a set comprehension written out at the call site — so a third arriving is folded
    only if somebody remembers, and *at what scope* was a tuple that happened to be built
    the same way twice.

    :attr:`scope` is the whole of what differs between the two. A codepoint explains the
    other findings **on its line**, because the byte is in that line and the next one is
    judged normally; a grammar explains them **in its file**, because the rule is what
    every line in it was read under. Naming that is what makes the two one mechanism rather
    than two loops that resemble each other.
    """

    #: The code that explains, or its prefix where the family is what explains — `char.`
    #: is nine codes and every one of them makes the same point about the line it is on.
    by: str
    #: What it explains, matched the same way.
    over: tuple[str, ...]
    #: `line` or `file` — how far the explanation reaches.
    scope: str

    def explains(self, finding: Finding) -> bool:
        return any(finding.code.startswith(code) for code in self.over)

    def spoken_by(self, finding: Finding) -> bool:
        return finding.code.startswith(self.by)

    def where(self, finding: Finding, *, speaking: bool = False) -> tuple[str, int | None]:
        """The key two findings share when one explains the other.

        ``speaking`` lets an explanation be filed somewhere other than what it is about,
        which the grammar one has to be: it lands on `roadkeep.toml`, where the declaration
        that broke the file is and where the edit goes (RK1067), and it explains findings in
        the file it names. `about` carries that second address, so the two are not confused
        — the finding's own `file` is where a reader clicks and never what it covers.
        """
        under = finding.about if speaking and finding.about else finding.file
        return (under, finding.lineno if self.scope == "line" else None)


#: Every explanation this gate makes, which is the index RK1070 asked for: a reader asking
#: "does a finding suppress another" reads four lines rather than two functions.
EXPLAINS: tuple[Explains, ...] = (
    # A line carrying a byte nobody typed is not a line this format can judge (RK34): the
    # parser read a string the author cannot see, so every other diagnosis of it names a
    # consequence. Report the codepoint; the rest is decidable on the next run.
    Explains(by="char.", over=("",), scope="line"),
    # A rule that fails on every bullet in a file is what broke them (RK1068), so the
    # per-line failures are the effect and the report is one defect at one declaration.
    Explains(
        by="grammar.",
        over=("line.non-canonical", "line.unparsed"),
        scope="file",
    ),
)


def _untainted(findings: list[Finding]) -> list[Finding]:
    """Every finding except the ones another already explains (RK34, RK1068, RK1070).

    One pass over :data:`EXPLAINS` rather than a function per relation: what each row says
    is which code speaks, which it speaks over and how far, and the loop under that is the
    same four lines it always was. An explanation never suppresses another explanation —
    a codepoint on a line whose file has a bad grammar is still worth reporting, both being
    causes rather than effects.
    """
    kept = list(findings)
    for rule in EXPLAINS:
        # A line-scoped rule needs a line to be about: a finding filed against the file
        # itself explains nothing on any particular one, and taking it as evidence would
        # silence every other file-level finding there.
        spoken = {
            rule.where(f, speaking=True)
            for f in kept
            if rule.spoken_by(f) and (rule.scope == "file" or f.lineno)
        }
        kept = [
            f
            for f in kept
            # Never an explanation: a codepoint on a line whose file has a bad grammar is
            # still worth reporting, both being causes rather than effects of each other.
            if any(one.spoken_by(f) for one in EXPLAINS)
            or not rule.explains(f)
            or rule.where(f) not in spoken
        ]
    return kept


def _ordered(findings: list[Finding], checked: tuple[str, ...]) -> tuple[Finding, ...]:
    """Every finding, in the order the report prints them (RK365).

    `checked` **is** the order, so a file sorts where the reader was told it was read, and the
    two halves of the report cannot disagree about which file came first.

    A finding whose file the list does not name sorts **last**, by falling off the end of the
    index. That was right by accident until RK354 put the config in `checked`, and it is stated
    here rather than left in a `dict.get` default: the report is read against the list, so
    anything the list does not name belongs after everything it does.
    """
    order = {name: index for index, name in enumerate(checked)}
    return tuple(
        sorted(findings, key=lambda f: (order.get(f.file, len(order)), f.lineno or 0, f.code))
    )


def _subtract(now: Report, before: Report, rev: str) -> Report:
    """The findings this working tree added, and the ones it inherited (RK84).

    **Counted per (file, code, task), and never per line number.** A line moves when
    anything above it is inserted, so an identity that included the position would report
    the whole file as new the first time a task was added at the top — which is the failure
    mode that makes a delta gate worth less than no gate. What is compared is therefore how
    many findings of one kind one line has, and the excess is what this change wrote.

    Within a kind the ones that did not move are forgiven first. It changes no count; it
    means the finding *reported* is the one at a position the revision did not have, which
    is the one a reader is being sent to look at.
    """
    standing: dict[tuple[str, str, str], list[Finding]] = {}
    for finding in before.findings:
        standing.setdefault(_debt(finding), []).append(finding)

    here: dict[tuple[str, str, str], list[int]] = {}
    for index, finding in enumerate(now.findings):
        here.setdefault(_debt(finding), []).append(index)

    forgiven: set[int] = set()
    resolved: list[Finding] = []
    for key, indices in here.items():
        there = standing.pop(key, [])
        places = {finding.lineno for finding in there}
        stayed = [i for i in indices if now.findings[i].lineno in places]
        moved = [i for i in indices if now.findings[i].lineno not in places]
        forgiven.update((stayed + moved)[: len(there)])
        resolved.extend(there[len(indices) :])
    for left in standing.values():
        resolved.extend(left)

    return replace(
        now,
        findings=tuple(f for i, f in enumerate(now.findings) if i not in forgiven),
        baseline=Baseline(
            rev=rev,
            forgiven=tuple(now.findings[i] for i in sorted(forgiven)),
            resolved=tuple(resolved),
        ),
    )


def _debt(finding: Finding) -> tuple[str, str, str]:
    """What makes two findings the same standing problem: one kind, one line's worth."""
    return (finding.file, finding.code, finding.id)


def _characters(config: Config, role: str, document: Document) -> list[Finding]:
    """Name the byte, not its consequence (RK34).

    The format is structural Unicode — `—`, `→`, `§` and four emoji markers — so every
    lookalike a human editor produces is invisible exactly where it fails. Measured
    against this parser: `📋` plus U+FE0F is reported as `status.unknown`, which prints as
    "'📋️' is not one of 📋"; a no-break space before the pointer is reported as
    `why.no-terminator`, naming the one thing the line does not lack. Both are correct and
    unusable, because the character that caused them cannot be seen.

    Only the line-bearing files. A paragraph has no parse for an invisible byte to corrupt,
    and §RK34 had to *quote* a variation selector to explain the defect — which a scan over
    prose would have reported as the defect itself.

    **Which codepoints occur is asked before where they are** (RK227). The rule stays
    :func:`suspect`'s — a Unicode category and not a hand-kept list, so a format character
    nobody has met yet is still caught — but it is asked once per *distinct* codepoint
    instead of once per character: 800215 calls over Turing's ledger, every answer no, for
    148 ms of a 660 ms gate. A clean file leaves the walk below unentered, and every file
    this gate passes is a clean file.

    The bodies and not the raw lines, because a line ending is `Cc` and therefore the one
    thing every file would have flagged — :func:`_endings` is what judges those, and a
    sweep that always said "dirty" would have been the loop with a longer preamble.
    """
    file = config.relative(config.path(role))
    ids = {entry.lineno: entry.task.id for entry in document.entries}
    out = _endings(document, file)
    bodies = [raw.rstrip("\r\n") for raw in document.lines]
    # `indent=False`, so a tab counts as a candidate wherever it sits; the walk is what
    # knows whether one is indentation, which is the only place it reads as text (RK146).
    candidates = {char for char in set("".join(bodies)) if suspect(char)}
    if not candidates:
        return out
    found = re.compile(f"[{''.join(re.escape(char) for char in sorted(candidates))}]")
    for number, body in enumerate(bodies, start=1):
        head = indentation(body)
        for match in found.finditer(body):
            column = match.start() + 1
            if not suspect(match.group(), indent=column <= head):
                continue
            out.append(_named(file, number, column, match.group(), ids.get(number, "")))
    return out


#: The one codepoint a prose file is swept for (RK1028). Not the rest of :func:`suspect`'s
#: domain, and §RK34 is why: a design explaining a lookalike has to **quote** it, so a scan
#: over prose would report the paragraph that documents the defect as the defect. A mark is
#: the exception that proves the rule — no design pastes one, they name it `U+FEFF`, and no
#: keyboard produces it. What does produce it is every mainstream Windows editor, ahead of a
#: file `--body-file` then reads whole.
MARK = "﻿"


def _marks(config: Config, role: str, document: Document) -> list[Finding]:
    """A byte-order mark anywhere in a prose file, which is never something anybody wrote.

    The gate half of RK1028. The writer now strips one at position 1 of a stream or a file,
    where it is the encoder's; this is the file that already carries one — from an editor,
    from a paste, from the route that was open before the strip — and it is invisible by
    definition, so the first reader to notice is whoever greps a heading and finds nothing.

    Anywhere and not only at the start, because that is where the hole was: a body read from
    a path lands **mid-file**, under whatever heading the section was placed at, and a rule
    about position 1 would have reported nothing. The code is `char.bom` either way — one
    byte, one meaning, one door.
    """
    file = config.relative(config.path(role))
    out: list[Finding] = []
    for number, raw in enumerate(document.lines, start=1):
        column = raw.find(MARK)
        while column >= 0:
            out.append(
                Finding(
                    "char.bom",
                    file,
                    "U+FEFF byte-order mark inside the prose: not text, invisible in an "
                    "editor, and a byte the round-trip compares",
                    number,
                    "",
                    column + 1,
                )
            )
            column = raw.find(MARK, column + 1)
    return out


def _named(file: str, lineno: int, column: int, char: str, task_id: str) -> Finding:
    point = f"U+{ord(char):04X}"
    name = unicodedata.name(char, "unnamed control character").lower()
    if lineno == 1 and column == 1 and char == "﻿":
        # Its own answer: a byte-order mark is not text at all, and it lands on whatever
        # the first line happens to be — which is a heading, so nothing else reports it.
        return Finding(
            "char.bom",
            file,
            f"{point} byte-order mark at the start of the file: not text, and a byte the "
            f"round-trip compares",
            lineno,
            task_id,
            column,
        )
    # The code and the clause are the schema's (RK499), which is where the door raises the
    # same three about a *field*: a tab past the indentation is a separator this format does
    # not write, a `Zs` renders as a space and is not one, and everything else cannot be seen.
    # What is this function's own is the place — a line and a column, which is what a report
    # is read for and what an argument has none of.
    code, because = CODEPOINT_KINDS[codepoint_kind(char)]
    named = "tab" if char == TAB else name
    return Finding(code, file, f"{point} {named} at column {column}: {because}", lineno, task_id, column)


def _endings(document: Document, file: str) -> list[Finding]:
    """Two kinds of line ending in one file — one line edited by something else.

    A file that is *uniformly* CRLF is not a defect and is not reported: `Document` keeps
    every ending verbatim, so it round-trips, and a repository that checks out CRLF is a
    configuration rather than a mistake (L6). Mixed is the byte nobody typed.
    """
    found: dict[str, int] = {}
    for line in document.lines:
        terminator = ending(line)
        if terminator:
            found[terminator] = found.get(terminator, 0) + 1
    if len(found) < 2:
        return []
    spelled = ", ".join(
        f"{count}× {_ENDING_NAMES[terminator]}" for terminator, count in sorted(found.items())
    )
    return [
        Finding(
            "char.mixed-endings",
            file,
            f"two kinds of line ending in one file ({spelled}): one of them was written "
            f"by something that is not this tool, and the round-trip compares bytes",
        )
    ]


def _budgets(config: Config, tree: Tree) -> tuple[list[Finding], list[Note]]:
    """Every always-loaded file, against what it declared it may cost (RK30).

    Measured in bytes off the tree and lines by counting terminators, so nothing here has
    to decode a file the tool does not govern: a budget is about what a loader pays, and
    an instruction file is not a format this tool has any business parsing (L4). Off the
    tree and not off disk for RK84's reason — an `agents.md` pushed over its budget by this
    change is the finding a baseline exists to keep, and both runs reading the same bytes
    would forgive it.

    Which is exactly why the count is normalised (RK1105): with no baseline the tree *is*
    disk, so this read is a working tree's bytes, and with one it is a git blob's — the same
    gate answering two numbers for one commit, 311 bytes apart on the corpus that found it.
    `spent` drops the terminator's second byte and the second half of that is here, as a
    note: the checkout's real cost is stated and never charged.
    """
    out: list[Finding] = []
    notes: list[Note] = []
    for budget in config.budgets:
        where = config.relative(budget.path)
        raw = tree.blob(budget.path)
        if raw is None:
            out.append(
                Finding(
                    "budget.absent",
                    where,
                    "declares a budget and is not on disk: the entry holds nothing",
                )
            )
            continue
        # One measurement, called and not repeated (RK345): `budget --file` reports the room
        # this refuses, and a second count here is a gate disagreeing with the read that
        # composed the edit.
        measured_in = spent(raw)
        for unit, measured, allowed in (
            ("lines", measured_in["lines"], budget.lines),
            ("bytes", measured_in["bytes"], budget.bytes),
        ):
            if allowed is not None and measured > allowed:
                out.append(
                    Finding(
                        f"budget.{unit}",
                        where,
                        f"{measured} {unit}, budget is {allowed}: this is loaded every "
                        f"turn, so the overrun is paid on every turn",
                    )
                )
        extra = translated(raw)
        if extra and budget.bytes is not None:
            notes.append(
                Note(
                    "budget.translated",
                    where,
                    f"{measured_in['bytes']} bytes counted and {extra} more on this "
                    f"checkout, whose lines end CRLF: the ceiling is the commit's, so a "
                    f"number declared against a working tree has that much room it never "
                    f"voted for",
                    subject=where,
                )
            )
    return out + _served(config), notes


def _wired(config: Config) -> list[Finding]:
    """The vendored surfaces behind the engine answering here (RK1192).

    `install --check` already answers this exactly, and that is the whole problem: it is a
    command nobody thinks to run. Nothing prompts it, no failure names it, and a project
    reaches it only by already suspecting what it reports.

    Measured on another project. Its committed launcher predated RK1116, so it forwarded
    `guard` and `mcp` and nothing else; the MCP server had not connected; and the skill that
    session read named that launcher as the entry point. Every door was shut at once, and the
    way out was guessing a version directory under the plugin cache — the one route no
    document mentions, because it is not meant to be one.

    So the gate asks it, being what runs anyway: `lint` fires every turn through the `Stop`
    hook, it already reports drift between what a file says and what this tool would write,
    and a wired surface behind the version answering is drift of exactly that kind. The
    remedy is `install`, which is the complete command, so `repair` closes it too.

    **Against the engine answering here and never the newest one.** :func:`~roadkeep.installing.stale`
    plans from `_source()`, the checkout this process is, so what is compared is the copy that
    would do the writing. Three copies are allowed to differ and `engines` is what adjudicates
    that (RK415); a second opinion here about which version is *right* would be this gate
    taking a side in a question another verb exists to report.

    **Filed at the surface**, unlike `budget.tool` one function down: there is a path a reader
    can open, and it is the file that drifted.

    Silent where nothing is vendored, which is every plugin-served project — there is no copy
    to be behind. Silent too where `[install] pinned` says the version is the project's choice
    (L6): a finding on every turn about a decision already taken is noise, and a gate carrying
    noise is one that stops being read.

    Cheap, and measured before it was put on a per-turn path: :func:`~roadkeep.installing.stale`
    is **0.07 ms** unwired — one `is_file` — and **0.86 ms** wired, against RK176's 43 ms
    floor. It declines the workflow gauge, which is the 40 ms of that, by the same field that
    makes the workflow the adopter's after the first write.
    """
    if config.install_pinned:
        return []
    from roadkeep.installing import stale  # noqa: PLC0415 - RK260

    # Every failure inside is silence, as it is for the session-start notice this shares a
    # reader with (RK82, RK234): a gate that fails because a checkout moved is worse than one
    # that says nothing, and `install --check` still answers on demand.
    return [
        Finding(
            "install.stale",
            where,
            f"this surface is behind the roadkeep answering here, so a session reads a "
            f"skill, hook or launcher older than the engine it names — "
            f"`{invocation()} install` rewrites the ones this checkout ships",
            subject=where,
        )
        for where in stale(config.root)
    ]


def _served(config: Config) -> list[Finding]:
    """Every served tool against what one may cost a session (RK1059).

    `_budgets`' argument, about the surface instead of about a file. RK30 held the resident
    prose and RK464 measured the schema and stopped there, deliberately: what a ceiling
    would be *per* was a decision it declined to make without a number in front of it. Here
    it is per tool, because a total names nothing — it fails on whichever tool is added
    last — and a per-tool one is refused by the tool whose description somebody just edited.

    Filed against `roadkeep.toml`, which is the file that declared it and the only file
    involved: the cost is composed per session from the parser, the config and the `TOOLS`
    table, so there is no path a reader could open to see it. `budget --tools` is what
    prints it, and the message says so.

    Silent where nothing is declared, which is every adopting project until it looks at the
    number — a gate that arrived with a ceiling this tool chose would be the guess RK464
    refused to make.

    **And it is cheap, which RK1061 was filed believing it was not.** That task measured 201
    ms against 80 and read it as this check building 52 descriptors on a command CI, the
    pre-commit hook and the Stop hook each run. Measured again, warm: `descriptors` is 1 ms
    and this whole function is **1.4 ms**. The 121 ms was one-time import cost — `serving`
    and the CLI it reaches — attributed to the check by an in-process comparison whose first
    call paid it. The import is still real and is 13 ms on a path where `cli` is already
    loaded, which every path this runs on is. Left as it is, and the measurement kept here
    because the next reader will make the same inference from the same shape.
    """
    if config.tool_characters is None:
        return []
    from roadkeep.serving import surface

    allowed = config.tool_characters
    where = _configured(config)
    sent = surface(config)
    # The same payload `budget --tools` measures, through the same function (RK345): a
    # second estimate here is a gate disagreeing with the read that composed the edit. In
    # its order too — largest first — because the message sends the reader to that ranking,
    # and a report listing the offenders in a different one is two answers to one question.
    out = [
        Finding(
            "budget.tool",
            where,
            f"the {name} tool is {size} characters, budget is {allowed}: this is sent to "
            f"every session that connects the server, so the overrun is paid before the "
            f"first call — `{invocation()} budget --tools` ranks them",
            subject=name,
        )
        for name, size in sent.tools
        if size > allowed
    ]
    # And the sum, where the project declared one (RK1097). Second and not instead: this one
    # names no author, so a report carrying only it would refuse the verb added last for a
    # size the other 51 built.
    #
    # Appended after the per-tool findings and printed before them, which is not a
    # contradiction left standing: every finding here is filed at `roadkeep.toml` with no
    # line, so `_ordered` breaks the tie on the code and `budget.session` sorts under
    # `budget.tool`. Left that way rather than special-cased — one address, one documented
    # order, and the message says no single tool is at fault, which is what a reader arriving
    # at it first needs to know.
    if config.tool_session is not None and sent.characters > config.tool_session:
        out.append(
            Finding(
                "budget.session",
                where,
                f"the served surface is {sent.characters} characters — {len(sent.tools)} "
                f"tool(s) and the handshake — against a budget of {config.tool_session}: "
                f"every session pays this at connect before it calls anything, and no one "
                f"tool is at fault — `{invocation()} budget --session` prints it beside "
                f"what the resident files cost each turn",
                subject="session",
            )
        )
    return out


def _collective(config: Config, documents: dict[str, Document]) -> list[Note]:
    """What a `Block X` or a range actually names, said out loud (RK35).

    Only when it expands to **two or more** open tasks, which is precisely the case the
    line hides: at one there is no surprise to report, and at zero there is nothing to
    name — whether waiting is over there is the standing's answer and not this note's, a
    label with no open member being finished, paused or a heading opened before its lines,
    and only the first of those annotating ✅ (RK8, RK432). A note per token below that
    threshold would be output nobody reads, which is the failure mode RK16 exists to avoid.
    """
    roadmap = documents.get("roadmap")
    if roadmap is None:
        return []
    backlog = Backlog.during(
        config,
        roadmap=roadmap,
        ledger=documents.get("changelog"),
        store=documents.get("deferred"),
    )
    file = config.relative(config.path("roadmap"))
    out: list[Note] = []
    for entry in roadmap.entries:
        for dep in entry.task.deps:
            if not config.schema.classify_dep(dep).collective:
                continue
            members = backlog.expand(dep)
            if len(members) < 2:
                continue
            shown = ", ".join(members[:6]) + (" …" if len(members) > 6 else "")
            out.append(
                Note(
                    "deps.collective",
                    file,
                    f"{dep.id} is one token naming {len(members)} open tasks: {shown}",
                    entry.lineno,
                    entry.task.id,
                )
            )
    return out


def _turned(config: Config, documents: dict[str, Document], since: str) -> list[Note]:
    """A block that emptied or reopened in this change (RK269).

    `ship` is the only verb that computes it — `event T282 Block AI finished` — and says it once,
    to a console. Nothing records it, no later verb can ask, and `lint` reports a clean tree
    either way, which is the gate an author actually trusts. Measured in a repository keeping a
    per-block index beside its ledger, one `(active — see ROADMAP)` per row: two ships emptied a
    block and two adds reopened it across four commits, every row was flipped by hand, and every
    time `lint` passed on the wrong one. The discrepancy was caught by that project's own test
    suite, which asserts the index against the roadmap because this tool does not.

    Three shapes were open and this is the cheapest of them, which is also the one that would
    have caught all four. Not a query verb: `stats --json` already answers which blocks hold
    nothing, so a project's check can be written against roadkeep today. Not ownership of the
    index row either — that is a projection, and a projection roadkeep writes is `export`'s
    contract (RK39), which wants a declared shape rather than a guess at somebody's table.

    Reported with ``since`` and never as a state, which is the whole reason it is quiet enough
    to keep: the shipped pre-commit hook runs `lint --since HEAD`, so this lands at the moment of
    the commit that moved it — while "Block A is empty" is true of this repository forever and a
    line printed forever is a line nobody reads (RK16).

    A **note**, because emptying a block is what finishing one looks like. Only blocks *both*
    trees declare: one that arrived is `block add`'s own event and one that left is `block drop`,
    and neither is a transition of state.

    Emptiness is `Document.holds` and nothing wider — the same *call* the event line makes and
    not a second spelling of it (RK300), because two answers to "is that block empty" is this
    defect with the arrow reversed (RK92: a deferred line is set aside, not open). The counts
    below are presentation and not the decision: how many lines a block held is a fact about
    the baseline that the event line never computes, so it is read where it is printed.
    """
    roadmap = documents.get("roadmap")
    if roadmap is None:
        return []
    if not resolves(config, since):
        # A repository with no commits has no HEAD, which is the shipped hook's default.
        if since == "HEAD":
            return []
        raise HistoryUnavailable(f"{since} is not a revision this repository knows")
    before = Tree(config, since).document("roadmap")
    if before is None:
        return []
    file = config.relative(config.path("roadmap"))
    declared = {h.label for h in before.headings if h.label}
    held = {label for label in declared if before.holds(label)}
    out: list[Note] = []
    for heading in roadmap.headings:
        label = heading.label
        if label is None or label not in declared:
            continue
        now = roadmap.holds(label)
        if label in held and not now:
            out.append(
                Note(
                    "block.emptied",
                    file,
                    f"held {len(before.block(label))} open line(s) at {since} and holds none "
                    f"now: a projection that states which blocks are active is a row this "
                    f"commit moves, and nothing else here will say so",
                    heading.lineno,
                    label,
                )
            )
        elif now and label not in held:
            out.append(
                Note(
                    "block.reopened",
                    file,
                    f"held no open line at {since} and holds {len(roadmap.block(label))} now: "
                    f"the same row, in the other direction",
                    heading.lineno,
                    label,
                )
            )
    return out


def _unpaired(config: Config, sections: tuple[Section, ...], since: str) -> list[Note]:
    """A rationale section edited without touching the line that carries its status (RK36).

    RK15 refuses a pointer at a section that does not exist; this is the mirror, and the
    more expensive direction: the line is the only thing `pick` reads and the section is
    deleted on ship, so a requirement written only into the rationale cannot be picked,
    cannot be shipped, and leaves with the section that held it. It happened three times in
    one session here, every time by an author who had just learned something and wrote it
    where the reasoning was rather than where the status is.

    A **note**, not a finding, and this is the whole judgement: the check cannot tell a
    typo in a paragraph from a smuggled requirement, and a gate that failed every honest
    rationale edit would be bypassed within a week — which is worth less than a sentence
    read at the moment of the commit. It is deliberately not semantic (§RK36 says so): the
    signal is that the section was open and the line was not.
    """
    if not resolves(config, since):
        # A repository with no commits has no HEAD, which is the shipped hook's default —
        # so the initial commit is not the thing this fails on.
        if since == "HEAD":
            return []
        raise HistoryUnavailable(f"{since} is not a revision this repository knows")

    edited = touched_since(config, since, "improvements")
    if not edited.changes:
        return []
    ids = config.schema.id_pattern()
    mentioned = re.compile(rf"\*\*({config.schema.id_fragment})\*\*")
    touched_ids = {
        found
        for role in LINE_ROLES
        for line in touched_since(config, since, role).lines
        for found in mentioned.findall(line)
    }
    # The file as it was, so a *removal* is attributed to the section that held it. Without
    # this a deleted section lands in whichever one now precedes the hole — and the section
    # `ship` just deleted would be reported against its innocent neighbour every time.
    before = anchored(
        Document.parse(content_at(config, since, "improvements"), schema=config.schema)
    )

    opened: set[str] = set()
    for change in edited.changes:
        if not change.text.strip():
            # A blank belongs to no section's prose, and counting it would attribute an
            # appended section to the one whose trailing blank line it starts on.
            continue
        anchor = _section_at(sections if change.added else before, change.lineno)
        if anchor is not None:
            opened.add(anchor)

    here = {section.anchor: section for section in sections}
    out: list[Note] = []
    for anchor in sorted(opened):
        section = here.get(anchor)
        if section is None or not ids.match(anchor) or anchor in touched_ids:
            continue
        out.append(
            Note(
                "section.unpaired",
                config.relative(config.path("improvements")),
                f"§{anchor} was edited and {anchor}'s line was not: the line is the only "
                f"thing `pick` reads, and this section is deleted on ship — so a "
                f"requirement written only here goes with it",
                section.first,
                anchor,
            )
        )
    return out


def _section_at(sections: tuple[Section, ...], lineno: int) -> str | None:
    """The anchor whose span holds this line, or None for prose under no anchor."""
    return next(
        (s.anchor for s in sections if s.first <= lineno <= s.last),
        None,
    )


def _voided(document: Document) -> bool:
    """Whether this file's every byte is NUL — the shape a lost write leaves (RK451).

    Not a heuristic about looking binary, which would be a judgement about files this tool
    did not write. The decidable question is narrower and is the one the failure produces:
    RK118 wrote every byte of a governed file, and none of them was ever a NUL, so a file
    that is nothing but NUL is one whose content did not reach the disk. An empty file is a
    different state — a scaffold before its first line — and stays the gate's other business.
    """
    if not document.lines:
        return False
    return all(character == "\x00" for line in document.lines for character in line)


def _absent(config: Config, tree: Tree) -> list[Finding]:
    """A declared file that is not on disk (`init` creates it: RK18).

    Asked of the tree and not of disk, so a baseline says *was it there then*: a governed
    file deleted since the ref is a finding this change made, and one added since is a file
    the ref cannot be asked to account for.
    """
    return [
        Finding(
            "file.missing",
            config.relative(config.path(role)),
            f"declared as the {role} file and not on disk",
        )
        for role in ROLES
        if config.has(role) and not tree.present(config.path(role))
    ]


def within(config: Config, role: str, document: Document) -> list[Finding]:
    """Everything decidable from one file alone.

    Public because the merge driver gates its own output with it (RK120): a driver holds
    three versions of one file and none of the others, so this is exactly the half of the
    gate it can run — and a second statement of these rules would be a second gate to keep
    in step with this one.
    """
    file = config.relative(config.path(role))
    out: list[Finding] = []

    # Before the line reader (RK451, RK454). A NUL in a governed file is a **lost write**
    # and not a character somebody typed: RK118 wrote every byte of this file and none of
    # them was ever one, so the diagnosis `char.invisible` gives is wrong in kind and the
    # `--fix` it names is worse — on a file a crash left entirely NUL that pass would strip
    # every byte and report the tree clean, and on a partly-lost one it claims all 400
    # findings, writes nothing, and returns the identical report on the next run.
    #
    # So the file states it once. Whole-file rather than per-byte because the loss is,
    # and because a column is a fact about a line that no longer says anything.
    lost = sum(line.count("\x00") for line in document.lines)
    if lost:
        held = sum(len(line) for line in document.lines)
        out.append(
            Finding(
                "file.not-text",
                file,
                (
                    f"holds {held} character(s) and not one of them is text: every byte is "
                    f"NUL"
                    if lost == held
                    else f"holds {lost} NUL byte(s) among its {held} character(s)"
                )
                + ", which is what a crash between a write and its rename leaves — the "
                "content is gone rather than malformed",
            )
        )
        # Nothing below can read a file with no text in it, and every rule here asks what a
        # *line* says. A file that kept some of its lines is a different answer (RK454): its
        # surviving lines have defects of their own, and hiding them would answer a question
        # nobody asked.
        if lost == held:
            return out

    for reject in document.rejects:
        # The line the parser could not read at all. It is reported here and counted
        # nowhere else, which is the difference between `audit` and a gate.
        out.append(Finding("line.unparsed", file, reject.reason, reject.lineno))

    seen: dict[str, int] = {}
    for entry in document.entries:
        task = entry.task
        for violation in document.schema.validate(task):
            if violation.code in _SCANNED:
                # RK499 put the codepoint rule at the door too, and `_characters` already
                # walks every line of this file for it — so surfacing both would report one
                # tab twice under one code, at two different numbers: a position inside a
                # field, and the column of the line. The scan's is what a report is read
                # for, and the schema's is what a *refusal* is read for.
                continue
            out.append(
                Finding(violation.code, file, violation.message, entry.lineno, task.id)
            )
        canonical = document.schema.render(task)
        if canonical != entry.raw:
            # Named, not fixed (L3): the tool may not rewrite a line it might have
            # misread, so the report carries the rendering and the edit stays a human's.
            out.append(
                Finding(
                    "line.non-canonical",
                    file,
                    f"written differently from what the schema renders: {canonical!r}",
                    entry.lineno,
                    task.id,
                )
            )
        if task.id in config.reserved:
            # The check that RK1031 is a fix and not a suppression. A reservation says the
            # address is spoken for and never written as a line; a line that carries one is
            # the two statements disagreeing, and the deriver has been handing out numbers
            # past it on the strength of the declaration.
            out.append(
                Finding(
                    "id.reserved",
                    file,
                    "declared in `reserved_ids` and written here as a line: a reservation "
                    "is an address nothing carries, so one of the two has to go",
                    entry.lineno,
                    task.id,
                )
            )
        first = seen.get(task.id)
        if first is not None:
            out.append(
                Finding(
                    "id.duplicate",
                    file,
                    f"already carried by line {first}: two lines with one id are two "
                    f"answers to whether it is done",
                    entry.lineno,
                    task.id,
                )
            )
        seen.setdefault(task.id, entry.lineno)
    return out


def _scope(config: Config, roadmap: Document | None) -> list[Finding]:
    """The non-goals, for a project that declared them governed (RK70).

    Silent otherwise, and that is the whole of the opt-in: two live corpora wrote their lists
    as free prose years before this grammar existed, and a gate that reported fifteen findings
    on the first run is a gate that gets bypassed rather than adopted (RK66).

    What is judged is what the schema can judge — the shape, the two lengths, and a lead
    claimed twice. Not the wrap: a filled bullet is written at insertion (L1) and a
    hand-wrapped one is whitespace inside prose, which `--fix` is the door for (RK16).
    """
    if roadmap is None or config.non_goals is None:
        return []
    file = config.relative(config.path("roadmap"))
    out: list[Finding] = []
    for lineno, raw in scoping.rejects(roadmap):
        out.append(
            Finding(
                scoping.SHAPE,
                file,
                f"a governed non-goal is `- **<lead>** <why>`, so this bullet has no lead "
                f"to be addressed by: {raw.strip()[:60]!r}",
                lineno,
            )
        )
    seen: dict[str, int] = {}
    for non_goal in scoping.read(roadmap):
        # The two lengths, only where the shape held (RK233). A bullet the reader now returns
        # unshaped already carries the finding above, whose remedy is the rewrite — charging
        # its sentence-lead against `lead` on top of that is a second finding the first one
        # subsumes, and Turing's `is **not** a path` would add a third for the `*` a bold run
        # this module never wrote is made of.
        if non_goal.shaped:
            for violation in scoping.validate(config, non_goal.lead, non_goal.why):
                out.append(Finding(violation.code, file, violation.message, non_goal.first))
        # The address is checked for every bullet, because every bullet now has one: two
        # constraints a reader looks up by the same words are two answers about one scope
        # whichever shape they are written in, and `drop` would take the later one either way.
        lead = scoping.address(non_goal.lead)
        first = seen.get(lead)
        if first is not None:
            out.append(
                Finding(
                    "non-goal.duplicate",
                    file,
                    f"already led on line {first}: the lead is the address, so two bullets "
                    f"carrying it are two answers about one scope",
                    non_goal.first,
                )
            )
        seen.setdefault(lead, non_goal.first)
    return out


def _configured(config: Config) -> str:
    """Where a finding about `roadkeep.toml`'s own keys goes, as the project spells it.

    One expression, because :attr:`Report.checked` names this file and `_queue` files against
    it: two spellings of the same path is a count and a finding disagreeing (RK354).
    """
    return config.relative(config.source) if config.source else "roadkeep.toml"


def _queue(
    config: Config, documents: dict[str, Document]
) -> tuple[list[Finding], list[Note]]:
    """Every entry in the queue that outranks the id order, resolved (RK326).

    `Config._check_priority` types a token and stops there, a config parser having no
    roadmap to resolve it against — so `priority = ["QQ1", "Block Z", "QQ9"]` with QQ1
    shipped, no heading declaring Z and QQ9 in no file lints clean, while `pick` answers
    "the declared priority names nothing ready": one sentence covering three deaths and
    naming none. Written as deps, two of those tokens are already findings here.

    Since RK325 the list is in the roadmap, so the resolution is the one
    :class:`~roadkeep.backlog.Backlog` already does and the codes are the states a token
    can be **dead** in: shipped, retired, set aside, naming nothing, and naming a block
    whose every line has left or is set aside — plus one named twice, which is two answers
    about where the same work sits. At `file:line:column` like everything else (RK34).

    Two states are deliberately **not** findings. An entry naming a merely blocked task is
    a queue doing its job — that is what a queue is *for* — and a declared block holding
    nothing **yet** is legitimate, `block add` writing the heading before the lines. Which
    of those a label is in is :class:`~roadkeep.backlog.Stage`'s answer and not this
    module's (RK434); what stays here is which code and which tier each state costs a queue.

    And a `priority` still in `roadkeep.toml` beside a section that now holds the order is
    the third note: it is read (:func:`~roadkeep.queueing.declared` says the section wins),
    and a queue quietly coming from the other file is the failure RK325 is about.

    A queue the **config** declares is resolved too, against `roadkeep.toml` and without a
    line: that is where the defect was measured, and a project that has not written the
    section is exactly the one whose queue nothing else reads.
    """
    roadmap = documents.get("roadmap")
    if roadmap is None:
        return [], []
    backlog = Backlog.during(
        config,
        roadmap=roadmap,
        ledger=documents.get("changelog"),
        store=documents.get("deferred"),
    )
    file = config.relative(config.path("roadmap"))
    found = queueing.read(roadmap, config)

    out: list[Finding] = []
    notes: list[Note] = []
    for lineno, raw in found.rejects:
        out.append(
            Finding(
                "priority.shape",
                file,
                f"a queue entry is `- <id>` or `- Block X` and nothing else, so this "
                f"bullet addresses no work: {raw.strip()[:60]!r}",
                lineno,
            )
        )

    if found.declared_in:
        if config.priority:
            notes.append(
                Note(
                    "priority.config",
                    _configured(config),
                    f"declares priority = {list(config.priority)} while "
                    f"{file} holds the queue: the section wins, so the config's order is "
                    f"read by nothing and `priority drop` cannot reach it",
                )
            )
        places = [
            (entry.token, entry.lineno, entry.raw.index(entry.token) + 1)
            for entry in queueing.entries(roadmap, config)
        ]
    else:
        file = _configured(config)
        places = [(token, None, None) for token in config.priority]

    seen: dict[str, int | None] = {}
    for token, lineno, column in places:
        if token in seen:
            first = f" on line {seen[token]}" if seen[token] else ""
            out.append(
                Finding(
                    "priority.duplicate",
                    file,
                    f"{token} is already queued{first}: an entry is an address, so a "
                    f"second one is two answers about where the same work sits",
                    lineno,
                    subject=token,
                    column=column,
                )
            )
            continue
        seen[token] = lineno
        finding = _dead(config, backlog, token, file, lineno, column)
        if isinstance(finding, Note):
            notes.append(finding)
        elif finding is not None:
            out.append(finding)
    return out, notes


def _dead(
    config: Config,
    backlog: Backlog,
    token: str,
    file: str,
    lineno: int | None,
    column: int | None,
) -> Finding | Note | None:
    """How this one entry is dead, or nothing where the tier can still fire.

    One resolution, from the code that resolves a dep, so a token cannot mean one thing in
    an annotation and another in the order (RK11's rule, and :func:`~roadkeep.queueing.typed`
    at the other end).

    The block half opens no file of its own since RK434: the states it used to read out of
    the ledger are :class:`~roadkeep.backlog.Stage`'s, read off the same backlog this
    resolution came from — which was already built from those documents.
    """
    resolution = backlog.resolve_dep(Dep(token))
    if resolution.kind is DepKind.BLOCK:
        return _dead_block(config, backlog, token, file, lineno, column, resolution.detail)
    if resolution.status is DepStatus.SHIPPED:
        return Finding(
            "priority.shipped",
            file,
            f"queues {token}, which is {resolution.detail}: work that left the roadmap "
            f"cannot be first, and the queue is the one list its departure did not reach",
            lineno,
            column=column,
            subject=token,
        )
    if resolution.status is DepStatus.DEFERRED:
        return Finding(
            "priority.deferred",
            file,
            f"queues {token}, which is {resolution.detail}: `pick` never offers a paused "
            f"line, so the order is over work nothing can start",
            lineno,
            column=column,
            subject=token,
        )
    if resolution.status is DepStatus.UNKNOWN:
        return Finding(
            "priority.unknown",
            file,
            f"queues {token}, which is {resolution.detail}: nothing can be first because "
            f"of an id no file carries",
            lineno,
            column=column,
            subject=token,
        )
    if resolution.status is DepStatus.UNRESOLVABLE:
        return Finding(
            "priority.retired",
            file,
            f"queues {token}, which is {resolution.detail}",
            lineno,
            column=column,
            subject=token,
        )
    # OPEN, which includes blocked: a queue naming work that is waiting is a queue doing
    # its job, and the tier fires the moment the blocker ships.
    return None


def _dead_block(
    config: Config,
    backlog: Backlog,
    token: str,
    file: str,
    lineno: int | None,
    column: int | None,
    detail: str,
) -> Finding | Note | None:
    """The half of :func:`_dead` about a `Block X` entry, and what each state costs a queue.

    The states are :class:`~roadkeep.backlog.Stage`'s and not this function's (RK434). They
    were worked out here first — a heading the ledger files entries under is a block that
    emptied, one with neither is a heading written before its lines — and RK429 wrote the
    same walk as :meth:`~roadkeep.backlog.Backlog.standing`, because `brief`, `pick` and
    `list` needed it too. The copy that goes is this one, and not for being second: it read
    the roadmap and the ledger and never the store, though `lint` already loads all three,
    so a block whose lines were set aside was reported as one nothing had been filed under
    yet — a finding arguing from the opposite of what the file says.

    What stays is the **codes and the tier**, which are the gate's and not a property of a
    block. `empty` is a note because `block add` writes the heading before the lines, which
    is the order this tool prescribes and so is a plan rather than a defect; the other
    three fail a build, `paused` for the reason a queued id in the store does
    (`priority.deferred`) — the same fact must not change tier by whether it was written as
    an id or as the label above it. `live` is the one state with nothing to say, so it is
    the fall-through: a stage this does not name yet is a silence, and a code naming a
    state the file is not in is worse than no code.

    ``detail`` is the resolver's sentence for the same label, which since RK432 *is*
    :attr:`Standing.sentence` — one oracle reached two ways, and it is taken as an argument
    rather than re-read so that a message and the dep report quoting it cannot drift.
    """
    label = config.schema.block_of_dep(Dep(token))
    # Never None here: `_dead` calls this only where `classify_dep` answered `BLOCK`, which
    # is the same pattern `block_of_dep` matches.
    standing = backlog.standing(label)
    if standing.stage is Stage.UNKNOWN:
        return Finding(
            "priority.block",
            file,
            f"queues {token} and {detail}",
            lineno,
            column=column,
            subject=token,
        )
    if standing.stage is Stage.PAUSED:
        return Finding(
            "priority.block-paused",
            file,
            f"queues {token}, which has nothing open and {standing.paused} set aside: "
            f"`pick` never offers a paused line, so the order is over work nothing can "
            f"start",
            lineno,
            column=column,
            subject=token,
        )
    if standing.stage is Stage.CURRENT:
        # Silent (RK1180): a tier over a standing category is an order waiting for the next
        # finding, which is what that kind of block is for — the finding below is about a tier
        # that fires on nothing *from now on*, and this one will fire again.
        return None
    if standing.stage is Stage.FINISHED:
        return Finding(
            "priority.block-empty",
            file,
            f"queues {token}, whose every line has shipped or left: a tier that fires on "
            f"nothing is an order the author believes is in force",
            lineno,
            column=column,
            subject=token,
        )
    if standing.stage is Stage.EMPTY:
        return Note(
            "priority.block-unstarted",
            file,
            f"queues {token}, which no line is filed under yet: the tier fires on nothing "
            f"until one is",
            lineno,
            subject=token,
        )
    return None


def _across(config: Config, documents: dict[str, Document]) -> list[Finding]:
    """What needs both files: one id in two of them, a block only one declares, and every
    dep resolved."""
    roadmap = documents.get("roadmap")
    if roadmap is None:
        return []
    ledger = documents.get("changelog")
    backlog = Backlog.during(
        config, roadmap=roadmap, ledger=ledger, store=documents.get("deferred")
    )
    file = config.relative(config.path("roadmap"))
    out: list[Finding] = []

    if ledger is not None:
        out.extend(_undeclared_blocks(config, roadmap, ledger, file))
    out.extend(_carried(config, backlog))

    for entry in roadmap.entries:
        out.extend(_deps(backlog, entry.task, file, entry.lineno))
        derived = derive(backlog, entry.task)
        if derived.deps != entry.task.deps:
            out.append(
                Finding(
                    "deps.stale",
                    file,
                    f"the annotation caches another line's status and this one is out "
                    f"of date: derived, it reads "
                    f"({', '.join(d.render() for d in derived.deps)})",
                    entry.lineno,
                    entry.task.id,
                )
            )

    out.extend(_cycles(backlog, file))
    return out


def _disagreeing(config: Config, tree: Tree) -> list[Note]:
    """The pen and the judge, where they are two versions of this tool (RK415).

    An adopting project runs three copies — the plugin its hook and skill run, the action its
    workflow gates on, and whatever `roadkeep` the caller invokes. Measured live: a checkout
    at 0.1.418 doing every write while the plugin at 0.1.285 denied the hand edits, 133
    versions apart, in a project whose backlog reasoned about *the plugin this repository
    runs* while a newer copy held the pen. Nothing said so, and the facts were local the
    whole time.

    Here because this is the gate, and once per commit is the right frequency: the same
    sentence on every `add` is noise the author learns to skip, and `engines` is the verb for
    asking on purpose. A **note**, so the exit code does not move — a cache lagging a
    checkout is allowed, and what is not survivable is not being told (RK79).

    Never over a **revision** (`--baseline`, `--at`): those runs judge the files as they were
    and the engines are a fact about right now, so the same note subtracted from itself would
    be reported as resolved debt the moment the versions agreed again.
    """
    if tree.rev is not None:
        return []
    from roadkeep.installing import engines  # noqa: PLC0415

    found = engines(config.root)
    if found.agree or found.plugin is None:
        return []
    return [
        Note(
            "engine.disagreement",
            config.relative(config.root),
            f"this gate is {found.running.version} and the plugin wired to this project is "
            f"{found.plugin.version}: a hook's refusal is that copy's rule — `engines` "
            f"reads all three, and `/plugin update` moves the judge",
        )
    ]


def _repeated(config: Config, files: dict[str, Document]) -> list[Finding]:
    """One label declared by two headings in one file — the gate's half of RK391.

    RK390 made `init` refuse it, which closed one of four doors: a hand edit, an `adopt`, and
    a merge of two branches all reach the same file, and there `lint` said *clean* while
    `add --block A` filed under the last of the two. That is L1 read the wrong way round —
    the law is that the schema is enforced where the text is created *and* the gate is the
    backstop, not that the write path is the only way in. Every other rule here has both
    ends; this one had the first alone.

    A **finding**, not a note, and the exit code is the argument: a file no verb can address
    is not a stylistic drift, and `add`, `ship` and `record add` now all refuse over it
    (:class:`~roadkeep.kernel.document.RepeatedHeading`) — a gate that stayed quiet would be the
    only thing in this tool that saw the state and let it stand. A project mid-adoption that
    has not reached its duplicate yet is what `--baseline` answers (RK84), which is the
    general answer to standing debt and not a reason to weaken one rule.

    Every governed file with headings, prose included: the rationale file is filed under the
    same block headings, and `section add` resolves a block there the same way.

    Reported once per label, at the **second** heading and naming the first. The second is
    the one that was added, and the message needs both addresses because the fix is an
    editorial merge of two regions that nothing but their line numbers locates.

    **And it names the verb where the verb works** (RK417). One of two headings often stands
    over nothing — measured on a real corpus — and `block drop <label>` takes exactly that
    one out, in one command and with no editorial judgement at all; a report that stopped at
    the diagnosis left the author to research it. The clause is conditional, because that
    removal is all-or-nothing across the governed set: a file where nothing is removable
    refuses the whole run, so the condition is asked of every file that declares the label
    and :func:`~roadkeep.blocking.removable` is the one expression both sides read. If the
    repair is `block merge` (RK403), the message references the first heading because the
    merge keeps that first heading and folds the later region into it. Where both regions
    hold work there is no command to name, and saying so is still the useful half — it
    tells the reader which of the two cases they are in.

    """
    word = config.schema.heading_word
    out: list[Finding] = []
    for role, document in files.items():
        where = config.relative(config.path(role))
        for label in dict.fromkeys(h.label for h in document.headings if h.label):
            declared = document.declaring(label)
            if len(declared) < 2:
                continue
            first, *rest = declared
            remedy = (
                f"`block drop {label}` takes the empty one out"
                if closes_by_drop(document, rest[0], files, label)
                # `block merge` is that command, and this clause read "a merge by hand"
                # until RK425 — prose left behind when RK403 shipped the verb. It named an
                # edit the guard denies, and the obvious reading of it is a *rename*, which
                # detaches every entry beneath the second heading: measured, renaming five
                # produced 83 findings and had to be reverted. So the sentence says what the
                # command does, because the caller's next question is whether their lines
                # survive it.
                else f"`block merge {label}` folds the later region into the first"
            )
            for later in rest:
                out.append(
                    Finding(
                        "block.repeated",
                        where,
                        f"{word} {label} is already declared on line {first.lineno}: one "
                        f"label is one region, neither of these is inside the other, and a "
                        f"write files under the first by position alone — {remedy}"
                        + _moving(document, later, files, label),
                        later.lineno,
                        # The label rather than a task id: this finding is about a heading,
                        # and it is what `block merge` takes (RK420).
                        subject=label,
                    )
                )
    return out


def _moving(
    document: Document, later: Heading, files: dict[str, Document], label: str
) -> str:
    """What the merge would move, where there is a merge to make (RK425).

    Said only on the branch that names `block merge`: the drop branch removes a region that
    holds nothing, so a count of zero beside it is a sentence about the absence of a fact.
    """
    if closes_by_drop(document, later, files, label):
        return ""
    held = _under(document, later)
    return f", moving the {held} line(s) under it and keeping the file's order"


def _under(document: Document, heading: Heading) -> int:
    """How many entries sit in **this heading's region** — the lines a merge would move.

    Printed because it is the caller's next question, and the one the report could answer
    all along: `block merge` moves exactly these, and a number beside the verb is the
    difference between running it and reading the source first.

    The region ends at the next heading of **any level**, which is the second fact RK425 is
    about: a `###` cannot group entries inside a block, so a subheading between two regions
    ends the first one — and a count that ignored the level would promise to move lines the
    merge leaves where they are.
    """
    after = [one.lineno for one in document.headings if one.lineno > heading.lineno]
    end = min(after) if after else len(document.lines) + 1
    return sum(1 for e in document.entries if heading.lineno < e.lineno < end)


def closes_by_drop(
    document: Document, later: Heading, files: dict[str, Document], label: str
) -> bool:
    """Whether `block drop` would **close this finding** rather than merely run (RK468).

    Two questions and the conjunction, where `_droppable` alone was read as both. That one
    asks whether the verb will refuse — it is all-or-nothing across files, so a label with
    work under it anywhere stops the run — and it says nothing about *which* heading comes
    out. Measured: a repeat in the ledger beside an empty `## Block A` in the roadmap
    answered droppable, and `block drop` then withdrew the roadmap's heading and left the
    finding standing, correctly reporting `block merge` on the next run.

    So the region this finding is about has to be the empty one too. `_under` is that
    question, per heading and per file, and it is the same count `_moving` prints — which is
    what keeps the sentence, the remedy and the number one answer instead of three.

    Public because `remedying` asks it (RK468): the finding's message branched here and its
    remedy came from a table that could not, so on a droppable one the two named different
    commands and `repair` ran the one the sentence did not.
    """
    return _under(document, later) == 0 and _droppable(files, label)


def _droppable(files: dict[str, Document], label: str) -> bool:
    """Whether `block drop <label>` would remove a heading rather than refuse (RK417).

    Asked of every file that declares the label, because that verb is all-or-nothing: one
    file where nothing is removable refuses the run, including the files whose heading *was*
    removable. The ledger is the exception it is at the door — its headings hold history and
    are skipped rather than refused over — so a ledger with nothing removable is not what
    stops the rest.
    """
    declaring = {
        role: document for role, document in files.items() if document.declaring(label)
    }
    if not declaring:
        return False
    return any(
        removable(document, label) is not None for document in declaring.values()
    ) and all(
        role == "changelog" or removable(document, label) is not None
        for role, document in declaring.items()
    )


def _undeclared_blocks(
    config: Config, roadmap: Document, ledger: Document, file: str
) -> list[Finding]:
    """A block planning work the ledger cannot receive it into (RK380).

    Measured in Turing: `## Block BV` carried eight open lines for months and `CHANGELOG.md`
    declared no such heading. Nothing said so — every one of those lines is valid, its deps
    resolve, its pointer resolves — and the fact surfaced at the first `ship`, which is the
    end of a task rather than the start. :func:`~roadkeep.authoring.declaring` closes the
    door for lines written from here on; this is the state a project already in it is in, and
    reporting it costs one pass rather than one ship.

    **Only where the block has open lines**, which is what makes it a defect rather than an
    observation. A roadmap heading over nothing is a block being drafted, and one whose lines
    have all shipped or left keeps a ledger heading anyway — so the finding fires exactly
    when there is work that cannot be delivered.

    Reported at the roadmap's heading and not at each line under it: one heading is missing,
    one command adds it, and a finding per open line would report an eight-line block eight
    times for a single omission.

    A ledger organised by **nothing** is one finding and not one per block (RK403, RK411).
    It was silent for a week, because `block add` did not start organising such a file and
    the sentence would have named a verb that refuses; `--organise <role>` is that remedy now
    (RK405), and what is restored is deliberately not the per-block shape. There is one thing
    wrong with that project — its ledger has no headings — and saying it once per roadmap
    heading is the same omission reported as many defects. So the finding is about the
    **file**, reported against the ledger and at no line, which is where `file.missing`
    already reports a whole-file fact. It names one label, because `--organise` is needed for
    the first heading and never for the second.
    """
    out: list[Finding] = []
    word = config.schema.heading_word
    if not any(heading.label for heading in ledger.headings):
        return _unorganised(config, roadmap, word)
    for heading in roadmap.headings:
        if heading.label is None or ledger.heading(heading.label) is not None:
            continue
        open_lines = roadmap.block(heading.label)
        if not open_lines:
            continue
        out.append(
            Finding(
                "block.unrecorded",
                file,
                f"{word} {heading.label} plans {len(open_lines)} open line(s) and "
                f"{config.relative(config.path('changelog'))} declares no heading for it: "
                f"the first ship in this block refuses — "
                f'`block add {heading.label} --title "<its title>"`',
                heading.lineno,
                subject=heading.label,
            )
        )
    return out


def _unorganised(config: Config, roadmap: Document, word: str) -> list[Finding]:
    """The whole-file half of :func:`_undeclared_blocks`: a ledger with no heading at all.

    Every `ship` in this project refuses, and one command ends it — so the count that matters
    is how much work is waiting rather than which block is first, and the label named is only
    there to make the remedy copyable. Silent where nothing is open: a ledger organised by
    nothing is how every project starts, and it is a defect only once there is work it cannot
    receive.
    """
    planned = [
        (heading.label, roadmap.block(heading.label))
        for heading in roadmap.headings
        if heading.label
    ]
    waiting = [(label, lines) for label, lines in planned if lines]
    if not waiting:
        return []
    label = waiting[0][0]
    lines = sum(len(entries) for _, entries in waiting)
    return [
        Finding(
            "block.unorganised",
            config.relative(config.path("changelog")),
            f"declares no {word.lower()} heading at all, and "
            f"{config.relative(config.path('roadmap'))} plans {lines} open line(s) under "
            f"{len(waiting)} of them: every ship here refuses until one exists — "
            f'`block add {label} --title "<its title>" --organise changelog`',
            None,
            subject=label,
        )
    ]


def _carried(config: Config, backlog: Backlog) -> list[Finding]:
    """Every pair of governed files holding a line for one id (RK1082).

    One loop over `referring.PAIRS` rather than a rule per pair. Three files can hold a line
    — RK96 added the third — and the gate read two of the three pairs, each by its own copy
    of this loop: RK1081 wrote the second by copying the first, which is the arrangement
    RK1077 was filed about one layer up. The pairs are a cross product over
    :data:`~roadkeep.ids.CARRIERS`, so a fourth role that can hold a line is covered by
    arithmetic instead of by somebody remembering.

    The **wording** stays per pair, which is the line RK1081 drew: open-and-gone is not the
    sentence open-and-paused is, and the doors differ too. What is shared is which pairs
    exist and the walk over them; a pair the declaration carries with no code is one nobody
    has walked into, and it is skipped here and named there.

    `in_halves` is the one tolerated shape (RK121, RK1080) and belongs to the **ledger's own
    entry**: an entry naming a half is the file saying work arrived in halves, and whatever
    sits beside it agrees rather than disagrees. No other file can say so, which is why the
    roadmap–store pair has no tolerance at all.

    Read off whichever side *is* the changelog and no longer off `second` (RK1215). Two of
    the three pairs put the ledger second and the third puts it first, so the qualifier was
    being looked for on the store's line — where it never appears — and `id.paused-and-gone`
    fired on a half-shipped line the store legitimately holds. A tolerance applied to a
    position rather than to the file that carries the fact is one that works by coincidence.
    """
    # Off the `Backlog` the run already holds (RK1085), which is the reader that opens all
    # three carriers once — the shape `_deps` and `_queued` are handed. Reaching for
    # `config.document` per pair was one extra parse today and one per pair as carriers are
    # added, on a check whose caller had the documents in scope the whole time.
    carriers = {
        "roadmap": backlog.roadmap,
        "changelog": backlog.ledger,
        "deferred": backlog.store,
    }
    out: list[Finding] = []
    for pair in PAIRS:
        first, second = carriers.get(pair.first), carriers.get(pair.second)
        if not pair.code or first is None or second is None:
            continue
        elsewhere = second.by_id()
        where = config.relative(config.path(pair.second))
        filed = config.relative(config.path(pair.first))
        for task_id, entry in first.by_id().items():
            held = elsewhere.get(task_id)
            if held is None:
                continue
            recorded = (
                entry if pair.first == "changelog"
                else held if pair.second == "changelog"
                else None
            )
            if recorded is not None and recorded.task.in_halves:
                continue
            out.append(
                Finding(
                    pair.code,
                    # The pair's own first file and not the roadmap's (RK1084): the third
                    # pair is filed against the changelog, which is where its line is.
                    filed,
                    f"also on line {held.lineno} of {where}: {pair.says}",
                    entry.lineno,
                    task_id,
                )
            )
    return out


def _deps(backlog: Backlog, task: Task, file: str, lineno: int) -> list[Finding]:
    """Deps nothing will ever satisfy — three of the four kinds, for three reasons."""
    out: list[Finding] = []
    for resolution in backlog.resolve(task):
        kind, dep = resolution.kind, resolution.dep
        if resolution.status is DepStatus.UNKNOWN:
            out.append(
                Finding(
                    "deps.unknown",
                    file,
                    f"waits on {dep.id}, which is in neither the roadmap nor the "
                    f"changelog: nothing can say whether it is done",
                    lineno,
                    task.id,
                )
            )
        elif resolution.status is not DepStatus.UNRESOLVABLE:
            continue
        elif kind is DepKind.TASK:
            out.append(
                Finding(
                    "deps.retired",
                    file,
                    f"waits on {dep.id}, which left without shipping: "
                    f"{resolution.detail}",
                    lineno,
                    task.id,
                )
            )
        elif kind is DepKind.BLOCK:
            out.append(
                Finding(
                    "deps.block",
                    file,
                    f"waits on {dep.id} and {resolution.detail}",
                    lineno,
                    task.id,
                )
            )
        # An external dep falls through on purpose: waiting on work this backlog does
        # not track is a fact about the work, and reporting it would fail every file
        # that states one honestly. A deferred one falls through for the same reason
        # (RK92) — it is recorded, findable and revivable, and the gate reported it as a
        # missing id for as long as the resolver had no fifth answer to give.
    return out


def _pointers(
    config: Config,
    documents: dict[str, Document],
    anchors: dict[str, tuple[Section, ...]],
) -> list[Finding]:
    """Every `→ §<anchor>` on a line that still has a design, resolved against **every**
    governed prose file (RK15, widened by RK172) — open, or set aside and still pointing at
    the rationale a resume needs (RK96).

    Read from the parsed ``ref`` and never from the line's text, which is the whole
    subtlety: §RK15's own sentence quotes a pointer as an example of one, and a scan
    over the raw line reports that quotation as a design that does not exist.

    Measured adopting Turing: six open GEO lines carry `→ §X.3` and `→ §X.4`, which
    `docs/STRATEGY.md` declares and this resolved against the improvements file alone — so
    the gate called six correct pointers unresolved, and the only ways to satisfy it were to
    repoint a line at an unrelated section or to move positioning prose out of the file the
    config declares for it. Where **two** roles declare one anchor the answer is neither
    file: `ref.ambiguous` names both, because reading the first is what billed T354's `§X.1`
    365 words of somebody else's subtree without saying so.
    """
    declared = _declared(anchors)
    where = " or ".join(config.relative(config.path(role)) for role in anchors)
    out: list[Finding] = []
    for role in LIVE_ROLES:
        if role not in documents:
            continue
        file = config.relative(config.path(role))
        for entry in documents[role].entries:
            ref = entry.task.ref
            if not ref:
                continue
            found = declared.get(ref, ())
            if not found:
                out.append(
                    Finding(
                        "ref.unresolved",
                        file,
                        f"points at §{ref}, which is not in {where}: a pointer to a "
                        f"section that does not exist reads as a design that does",
                        entry.lineno,
                        entry.task.id,
                        # The remedy is about the **anchor** and the report is about the line
                        # (RK1206). Under `ref_scheme = "id"` the two are the same string, so
                        # composing the door from the id was right here and wrong everywhere
                        # else: on an outline, `TT1` points at `§I.1`, and `section add TT1`
                        # writes a section the line does not point at — leaving the finding
                        # standing with a second orphan beside it. `subject` is the field
                        # RK420 added for exactly this split, so the prefix stays the id a
                        # reader clicks and the substitution becomes the address that failed.
                        subject=ref,
                    )
                )
            elif len(found) > 1:
                named = " and ".join(
                    config.relative(config.path(other)) for other in found
                )
                out.append(
                    Finding(
                        "ref.ambiguous",
                        file,
                        f"points at §{ref}, which {named} both declare: one anchor names "
                        f"one section, and a pointer resolving to two resolves to neither"
                        f"{_namespace_remedy(config)}",
                        entry.lineno,
                        entry.task.id,
                    )
                )
    return out


def _citations(
    config: Config,
    prose: dict[str, Document],
    anchors: dict[str, tuple[Section, ...]],
) -> list[Finding]:
    """Every `§<anchor>` a section's **prose** makes, resolved like a pointer (RK1106).

    The fourth relation, and the gap the other three left between them. `_pointers` reads the
    ref a task line carries and `_orphans` reads what points at a section; a citation inside a
    paragraph is neither, so `ship` deletes a design another design argues from and the gate
    reports clean. Measured on Shio: four citations of retired addresses — `§II.1`, `§II.7`,
    `§III.1`, `§III.10` — over 641 lines the gate called clean.

    Not a duplicate of what the writers already say. `ship` and `section drop` name the
    sections citing what *they* are deleting, in the transaction that creates the dangling
    reference, which is the L1 door and the cheaper moment. This is the backstop for the
    caller who was told and did not act, and for the hand edit and the merge — and it reads
    :func:`~roadkeep.sections.references`, the same scan those two select from, so a project
    never gets two counts of its own dead citations.

    **Resolved against every prose file, exactly as a pointer is**, which is why `declared` is
    the index and not one document's anchors: a citation of `§S:I.2` from the improvements
    file is a reference into the strategy file, and asking one document would report the
    correct half of a project's prose as dangling.
    """
    if not prose:
        return []
    declared = _declared(anchors)
    where = " or ".join(config.relative(config.path(role)) for role in anchors)
    out: list[Finding] = []
    for role, document in prose.items():
        file = config.relative(config.path(role))
        for cited in references(document):
            if cited.anchor in declared:
                continue
            out.append(
                Finding(
                    "ref.dangling",
                    file,
                    f"§{cited.by} cites §{cited.anchor}, which is not in {where}: prose "
                    f"arguing from a section that is gone reads exactly like a typo, and "
                    f"from the next command on nothing can tell the two apart",
                    cited.lineno,
                    # The **citing** section and not the cited one, which is the subject every
                    # other reference code carries: `ref.unresolved` names the task holding the
                    # pointer, not the heading nothing answers. The edit is here too.
                    subject=cited.by,
                )
            )
    return out


def _namespace_remedy(config: Config) -> str:
    """The configuration that makes two colliding addresses two addresses (RK340).

    Named at the finding and not only in the docs, because the state it reports is one a
    project cannot edit its way out of: both files number their own outline from `I`, so
    "rename one of them" is a renumbering of somebody's whole document. Silent where the
    project already declares a namespace for both — there the collision is inside one of
    them, and `[refs]` has nothing left to say about it.
    """
    if all(role in config.refs for role in PROSE_ROLES if config.has(role)):
        return ""
    return (
        " — `[refs] <role> = \"<prefix>\"` in roadkeep.toml gives one of the two files its "
        "own namespace, so its addresses are written §<prefix>:<x.y>"
    )


def _crossing(
    config: Config,
    prose: dict[str, Document],
    anchors: dict[str, tuple[Section, ...]],
) -> list[Finding]:
    """A citation that resolves into the **other** prose file while a local one exists (RK1168).

    Declaring `[refs]` re-addresses every heading in a file at once — 48 of them in the run this
    was measured on — and carries none of that file's own citations. Seven became `ref.dangling`,
    which the gate reports; **twenty-one kept resolving**, into the other file's section of the
    same address, because both files declared it — which is why they collided at all and why the
    key was declared in the first place. Nothing said a word about those.

    That is worse than a dead reference: a dangling citation stops a reader, and this one hands
    them somebody else's design under the address they meant. So the shape reported is exactly
    that state — the citing file gives its own headings a namespace, the citation is written bare,
    and the namespaced address it would have meant is a section that exists here.

    Not every bare citation into another file. A project's prose argues from the other file all
    the time and `§S:I.2` is how it says so; what makes this a finding is that the same address
    resolves **both** ways and the local one is the file the sentence is in.
    """
    declared = _declared(anchors)
    out: list[Finding] = []
    for role, document in prose.items():
        namespace = document.schema.ref_prefix
        if not namespace:
            continue
        file = config.relative(config.path(role))
        for cited in references(document):
            local = f"{namespace}:{cited.anchor}"
            if local not in declared or role in declared.get(cited.anchor, ()):
                continue
            elsewhere = declared.get(cited.anchor, ())
            if not elsewhere:
                continue  # `ref.dangling` is that finding, and one state is one code
            named = " and ".join(config.relative(config.path(one)) for one in elsewhere)
            out.append(
                Finding(
                    "ref.crossed",
                    file,
                    f"§{cited.by} cites §{cited.anchor}, which resolves into {named} while "
                    f"§{local} is this file's own: a namespace re-addressed the headings and "
                    f"not the prose citing them, so the reference reads as correct and answers "
                    f"with somebody else's design",
                    cited.lineno,
                    subject=cited.by,
                )
            )
    return out


def _declared(anchors: dict[str, tuple[Section, ...]]) -> dict[str, tuple[str, ...]]:
    """Which prose roles declare which anchor — one index, read by resolution and by budget.

    A role that declares an anchor twice says so once here: `section.duplicate` is that
    file's own finding, and counting it again would make one file's mistake read as two
    files disagreeing.
    """
    out: dict[str, list[str]] = {}
    for role, found in anchors.items():
        for anchor in dict.fromkeys(section.anchor for section in found):
            out.setdefault(anchor, []).append(role)
    return {anchor: tuple(roles) for anchor, roles in out.items()}


def _orphans(
    config: Config,
    documents: dict[str, Document],
    prose: Document,
    anchors: dict[str, tuple[Section, ...]],
    *,
    role: str,
) -> list[Finding]:
    """One prose file read from its own side: a section, and what points at it.

    A pointer resolves one way only, so nothing in `_pointers` can see a section that
    survived its task. Three ways that happens and one budget, all at the anchor's line.

    Called **per governed prose role** (RK172), because a strategy file is a prose file: its
    sections are pointed at, budgeted and orphaned by the same rules, and a gate that read
    one of the two would leave the other ungoverned in exactly the way the roadmap is not.

    The budget is charged against **what a pointer hands a reader**, which is the one
    reading that keeps RK9's rule and this repository's own file both true: a section a
    line points at is measured with its subsections (`show` prints them, so a rationale
    that doubled by growing a `§RK34.1` is caught), and one nothing points at is measured
    on its own prose (`§0` is a container whose three anchored children are each inside
    the budget, and charging it 461 words would fail a file with no long paragraph in it).
    An anchor **two** files declare is charged as pointed at by nobody: which of the two a
    line meant is what `ref.ambiguous` asks the author, and billing one of them 365 words of
    the other's subtree in the meantime is the silent half of that defect.

    Which is also reported **here**, at the heading, and that is RK239: `ref.ambiguous`
    fires from the pointer end, so the state is named only where a task line happens to
    reach it. Turing at `f08304fcb1` declares thirteen anchors in both prose files, one is
    pointed at, and the other twelve were reported by nothing — while `show`, `brief`,
    `ship` and `defer` all already refuse to resolve them (RK186/RK196/RK229) and
    `_budget` above charges them as unreachable. `section.ambiguous` is the same word from
    the file that made the claim, once per heading, because the remedy is an edit at each
    of the two and `id.duplicate` is the shape an editor can act on twice. Not `--fix`'s:
    which of the two is the design is editorial (RK16).
    """
    file = config.relative(config.path(role))
    sections = anchors[role]
    declared = _declared(anchors)
    # A deferred task's section is carried, not deleted (RK96), so the line that owns it is
    # in the store rather than the roadmap — and reporting it orphaned would make the gate
    # demand the deletion of exactly what a resume restores.
    lines = {
        task_id: entry
        for role in LIVE_ROLES
        if role in documents
        for task_id, entry in documents[role].by_id().items()
    }
    kept = set(lines)
    gone = documents["changelog"].by_id() if "changelog" in documents else {}
    pointed = {
        entry.task.ref
        for document in documents.values()
        for entry in document.entries
        if entry.task.ref and len(declared.get(entry.task.ref, ())) == 1
    }
    claimed = _claimed(documents)
    ids = config.schema.id_pattern()
    seen: dict[str, int] = {}
    out: list[Finding] = []

    for section in sections:
        anchor = section.anchor
        first = seen.get(anchor)
        if first is not None:
            out.append(
                Finding(
                    "section.duplicate",
                    file,
                    f"§{anchor} is already at line {first}: an anchor names one "
                    f"section, and a pointer that resolves to two resolves to neither",
                    section.first,
                    anchor,
                )
            )
        elif len(declared.get(anchor, ())) > 1:
            # Once per file and never per copy, for the reason `_declared` dedupes a role:
            # a file that declares the anchor twice already carries the finding above, and
            # counting it again here would read as three files disagreeing.
            elsewhere = " and ".join(
                config.relative(config.path(other))
                for other in declared[anchor]
                if other != role
            )
            out.append(
                Finding(
                    "section.ambiguous",
                    file,
                    f"§{anchor} is declared in {elsewhere} as well: one anchor names one "
                    f"section, so no pointer here resolves and every verb that reads one "
                    f"refuses{_namespace_remedy(config)}",
                    section.first,
                    anchor,
                    # The fact these findings **share** (RK469): the pair of files, not the
                    # address. Measured on Turing, 27 of them filled 80% of the report with
                    # one sentence and one remedy repeated, and a single `[refs]` line closes
                    # every one — so the reader is told the pair once and the addresses under
                    # it. The findings stay one per address, because the addresses are the
                    # evidence an author picking which file takes the namespace reads.
                    shared=f"declared in {elsewhere} as well",
                )
            )
        seen.setdefault(anchor, section.first)
        out.extend(_budget(prose, section, pointed=anchor in pointed, file=file))
        out.extend(_query(section, file))
        out.extend(_hollow(prose, section, file, pointed=anchor in pointed))
        out.extend(_promise(config, section, file))
        owners = section_owners(section, ids)
        # Prose that belongs to no task is nobody's orphan — `§0.1` under the id scheme, and
        # any outline heading that names no id — the same rule `section add` applies (RK9).
        if not owners:
            continue
        if any(owner in kept for owner in owners):
            finding = _unreachable(section, file, owners=owners, lines=lines, claimed=claimed)
        else:
            finding = _unowned(
                section,
                file,
                shipped=any(owner in gone for owner in owners),
                owners=owners,
                claimants=tuple(claimed.get(anchor, ())),
            )
        if finding is not None:
            out.append(finding)
    return out


def _claimed(documents: dict[str, Document]) -> dict[str, list[str]]:
    """Which open lines point at which anchor — :func:`~roadkeep.sections.pointers`' index.

    Rebuilt from the documents this run already read rather than from disk, because a
    baseline run judges a revision and the gate has to ask its questions of that tree.
    """
    out: dict[str, list[str]] = {}
    for role in LIVE_ROLES:
        for entry in documents[role].entries if role in documents else ():
            if entry.task.ref:
                out.setdefault(entry.task.ref, []).append(entry.task.id)
    return out


def _unreachable(
    section: Section,
    file: str,
    *,
    owners: tuple[str, ...],
    lines: dict[str, Entry],
    claimed: dict[str, list[str]],
) -> Finding | None:
    """A section whose task is alive and points somewhere else (RK135).

    The gap the three neighbouring checks leave between them, measured on Shio: `XV.21` and
    `XV.22` carried the same title — one an earlier draft of the other — and SH265 points at
    `XV.22`. `section.orphan` did not fire, the id in the title being an open line;
    `section.duplicate` did not fire, the anchors differing; `ref.unresolved` did not fire,
    the pointer resolving somewhere. Twenty-three lines of superseded design lint clean, and
    the only reason it was found is that a reader compared two adjacent headings.

    Reachability is the pointer index and never the title, so the two readers RK134 split
    apart stay one: a section **any** open line points at is reached, and so is one under an
    anchor a pointer names — `§RK34.1` is handed to a reader by the `§RK34` its parent's
    pointer resolves to, which is the same subtree `show` prints and `_budget` measures.

    Not an orphan, and the remedy is not a drop: the task is alive, one of the two sections
    is its design and the other is history, and which is which is a reading.
    """
    if _reached(section.anchor, claimed):
        return None
    elsewhere = [
        (owner, lines[owner].task.ref)
        for owner in owners
        if owner in lines and lines[owner].task.ref
    ]
    if not elsewhere:
        return None
    named = ", ".join(f"{owner} points at §{ref}" for owner, ref in elsewhere)
    return Finding(
        "section.unreachable",
        file,
        f"{named}, so no pointer resolves here: the task is alive and its design is "
        f"somewhere else, which makes one of the two history rather than a deletion",
        section.first,
        section.anchor,
    )


def _reached(anchor: str, claimed: dict[str, list[str]]) -> bool:
    """Does an open line's pointer hand a reader this section — directly or by its parent?

    Segment by segment and never by string, the care :func:`~roadkeep.sections._extends`
    takes at the other end: `§0.1` is not under `§0.10`, and reading it as one would silence
    a check on a section nobody can reach.
    """
    segments = anchor.split(".")
    return any(
        ".".join(segments[:depth]) in claimed for depth in range(1, len(segments) + 1)
    )


def _query(section: Section, file: str) -> list[Finding]:
    """The `roadkeep-remaining` block a design may declare, held to its grammar (RK492).

    The backstop half of L1 for a fence: `remaining` refuses one it cannot read, but that verb
    is asked by whoever is continuing the migration, and a query nobody has run since it was
    typed is exactly the one that is wrong. So the gate reads it on every run, which costs one
    string scan per section and answers the only question the fence can be wrong about.

    A section declaring none is silent, which is every section here: this reports a block that
    exists and does not parse, never the absence of one. The count itself is `remaining`'s and
    never a finding — sites left are work, and work is not a defect in a file.
    """
    from roadkeep.remaining import (  # noqa: PLC0415 - RK260
        EVIDENCE,
        FENCE,
        QueryError,
        declared,
    )

    # Both fences, and one rule (RK1184): the criterion is the same grammar with the sign
    # flipped, so a block it cannot read is the same finding — and reporting one kind and
    # not the other would be the gate holding half of what the parser accepts.
    found: list[Finding] = []
    for tag in (FENCE, EVIDENCE):
        if tag not in section.body:
            continue
        try:
            declared(section.body, tag)
        except QueryError as error:
            found.append(
                Finding(
                    "remaining.format",
                    file,
                    f"§{section.anchor} declares a `{tag}` block this grammar cannot "
                    f"read: {error}",
                    section.first,
                    section.anchor,
                )
            )
    return found


def _promise(config: Config, section: Section, file: str) -> list[Finding]:
    """A design naming an id no line carries, once a file already holds one (RK1003).

    The backstop half of L1 for the rule RK1002 put at the door, and :func:`_query`'s shape
    exactly: `section add` refuses the body, and this reads what is already on disk. The
    three ways one gets there without passing a door are the three the backstop exists for —
    an adopted backlog, a hand edit and a textual merge.

    Reproduced the hour RK1002 shipped: a design edited to name an unclaimed id left `lint`
    clean while `next-id` warned about it inside another command's output, hedged, with
    nothing that had to act on the warning.

    **Not repairable, and it says so through its remedy rather than through `--fix`**: which
    of two ids an author meant is a judgement about a sentence, and the tool has no model of
    one (L4). The finding names the same two ways out the refusal does.

    Under the same code the door raises, which is what :class:`Finding` promises about every
    rule the two surfaces share: a caller filtering on `body.promise` filters one rule.
    """
    # Deferred beside `_query`'s, and one-way for the same reason (RK260).
    from roadkeep.sections import known, promised  # noqa: PLC0415 - RK1003

    return [
        Finding("body.promise", file, f"§{section.anchor} {one.message}", section.first, section.anchor)
        for one in promised(config.schema_for("roadmap"), section.body, known(config, section.anchor, None))
    ]


def _hollow(prose: Document, section: Section, file: str, *, pointed: bool) -> list[Finding]:
    """A section a pointer resolves to that gives the reader nothing (RK1012).

    The two states RK1004's register measured as reachable and reported by nothing: a heading
    with no prose under it, and one addressed with no title. `section add` refuses both — the
    door's own words are *a section with no prose is a heading* and *a section is named by its
    heading* — and a file carrying either lints clean.

    Neither is cosmetic, and the pointer is why. A line renders `→ §<id>` and the gate holds
    that the address resolves, so a heading with nothing under it satisfies that check while
    giving the reader none of what the pointer promised: `show` prints it and `brief` hands it
    to whoever starts the task, both answering with a title and a blank.

    The five rows beside them in that register stay silent and are a different answer: a
    heading is one line, so a newline in a title is about an argument, and an address this
    scheme cannot read is not parsed as a section at all — the heading is prose, and prose in
    a prose file is allowed.

    Not repairable, which is why both are `compose`: what the paragraph should say and what
    the heading should be called are the author's, and the tool writes neither (L4).

    **Only a section a line points at**, which is the symptom's own wording and the thing that
    makes it decidable. A heading nothing addresses is prose under a heading — this file's own
    `§0` is one, a container whose children are the rationale — and `section.orphan` is what
    names one of those. The subtree is read for the same reason `_budget` reads it: the walk
    hands over a section's own paragraph, and a parent's argument is its children.
    """
    if not pointed:
        return []
    whole = find(prose, section.anchor) or section
    out: list[Finding] = []
    if not section.title.strip():
        out.append(
            Finding(
                "title.empty",
                file,
                f"§{section.anchor} is addressed and unnamed: a section is named by its "
                f"heading, and a pointer resolving here reaches an address and no subject",
                section.first,
                section.anchor,
            )
        )
    if not whole.body.strip():
        out.append(
            Finding(
                "body.empty",
                file,
                f"§{section.anchor} has a heading and no prose: the line pointing here "
                f"promised a rationale, and `show` answers with a title and a blank",
                section.first,
                section.anchor,
            )
        )
    return out


def _budget(
    prose: Document, section: Section, *, pointed: bool, file: str
) -> list[Finding]:
    handed = (find(prose, section.anchor) if pointed else None) or section
    # The prose file's own budget where it declares one (RK50): `[limits.improvements]` is
    # the same declaration `[limits.changelog]` is, and this is the file it governs.
    limit = prose.schema.section_max
    if handed.words <= limit:
        return []
    return [
        Finding(
            "section.too-long",
            file,
            f"{over_by(handed.words, limit, unit='word')}; a section this long is "
            f"two sections, or a paragraph that belongs in the commit",
            section.first,
            section.anchor,
        )
    ]


def _unowned(
    section: Section,
    file: str,
    *,
    shipped: bool,
    owners: tuple[str, ...],
    claimants: tuple[str, ...] = (),
) -> Finding | None:
    """A section whose task no open line carries — gone, or never there.

    `owners` is what the section says it belongs to, which is the anchor under the id scheme
    and the ids in the heading under an outline (RK61). Named in the message, because
    `§XVI.12` alone tells a reader nothing about which task left.

    `claimants` is the other reader of the same fact, and until RK134 the two disagreed:
    this check decided from the ids in the heading while `section drop` decides from the
    pointers that resolve, so a section **still pointed at by** four open lines was reported
    stale and the only remedy the finding named was the one the tool refuses. RK64 already
    settled it for `ship` — a section another open line points at is kept, and the reason is
    reported — so the state this reports is the one `ship` itself writes. Shio's `VI.1` is
    the live case: SH22 shipped, SH44-SH47 are open against the same design, and the only
    way out was to retitle the heading by hand. A finding whose remedy the tool refuses is
    worse than no finding, which is the split RK16 exists to keep.
    """
    if claimants:
        return None
    named = ", ".join(owners)
    if shipped:
        return Finding(
            "section.stale",
            file,
            f"{named} is in the changelog and this rationale is still here: "
            f"`ship` deletes the section, so this survived a hand edit",
            section.first,
            section.anchor,
        )
    return Finding(
        "section.orphan",
        file,
        f"no line in any governed file carries {named}, so nothing can ever point "
        f"at this section",
        section.first,
        section.anchor,
    )


def _paths(config: Config, documents: dict[str, Document], tree: Tree) -> list[Finding]:
    """Paths a *shipped* line claims, resolved against disk (RK15, narrowed by RK46).

    Two exemptions, and both turn on which file is being read rather than on the token.

    Lines only: an unshipped design's whole job is to describe a file that does not exist
    yet — §RK26 names `.claude-plugin/marketplace.json` and is right to — so resolving a
    section's prose would fail every honest forward reference.

    And the ledger only, which is the same reasoning applied one file up. A roadmap
    describes work that has **not happened**, so the paths in it are disproportionately
    the artefacts its tasks exist to write; naming one is what a task line is for. Shio
    had eight such findings and all eight were false. A shipped line is the opposite
    claim — the work is done, so a path it names and the repository lacks is a real
    defect, and the only one here worth exit 1.

    The one place a baseline run resolves against the *revision* rather than the working
    tree (RK84). It has to: this finding is the only one whose subject is outside the
    governed files, so an artefact deleted since the ref would otherwise be missing in both
    runs and forgiven — and a rename the ledger did not follow is precisely the true finding
    this check produced on the corpus that motivated it.

    **And the working tree is then not a reader at all** (RK218). Half of that resolution
    moved and half did not: `carries` and `anywhere` asked git at the ref while
    `referenced.exists` still asked this disk, so a file created since the ref — untracked,
    never committed, invisible to git — silenced a finding the revision genuinely had. The
    same commit answered two ways depending on somebody's scratch file. So at a revision the
    filesystem is skipped outright rather than corrected: `exists` is a fact about now, and
    a run that names a revision is not asking about now.
    """
    document = documents.get("changelog")
    if document is None:
        return []
    file = config.relative(config.path("changelog"))
    near = config.path("changelog").parent
    # One pass, keeping what it found (RK223). The candidates have to be gathered before
    # `.gitignore` is asked, because one call for all of them is what keeps that question
    # cheap (RK213) — and gathering them with a comprehension of its own made the findings
    # comprehension repeat the whole scan: 1602 entries into `paths_in` for 801 entries,
    # and 2.9 s of a `lint` that a pre-commit hook waits for (RK17).
    unresolved = [
        (entry, token)
        for entry in document.entries
        for token in _candidates(tree, entry.raw, near)
    ]
    untracked = tree.declared_untracked([(token, near) for _, token in unresolved])
    left = _left_the_repository(config, tree, [token for _, token in unresolved])
    return [
        Finding(
            "path.missing",
            file,
            f"names {token}, which is not in the repository",
            entry.lineno,
            entry.task.id,
        )
        for entry, token in unresolved
        # Not a path this repository has declared it will never track (RK213): a build
        # output is absent from a bare checkout and present for whoever just compiled, so
        # a gate that read the filesystem alone answered by machine.
        if token not in untracked
        # And not one it *had* when the entry was written (RK1217): a shipped sentence is a
        # claim about the tree that shipped it, and a file later extracted into its own
        # repository makes history a finding on every run for ever.
        and token not in left
    ]


def _left_the_repository(
    config: Config, tree: Tree, tokens: Sequence[str]
) -> frozenset[str]:
    """Which of these paths this repository once held and no longer does (RK1217).

    Asked **last and only of what already failed**, which is the whole of its cost: `exists`,
    `anywhere` and `check-ignore` have each answered before a token reaches here, so a healthy
    repository asks git nothing and a corpus with stale entries pays one call per token — six
    on the ledger that motivated this, against 801 entries.

    Skipped at a revision, where the question is already being asked of history: a run naming a
    `--baseline` resolves the tree at that ref (RK218), and reaching past it to *every* ref
    would forgive a path the baseline's own tree never had.
    """
    if tree.rev is not None or not tokens:
        return frozenset()
    from roadkeep.history import left_the_repository  # noqa: PLC0415 - RK260

    return frozenset(
        token
        for token in dict.fromkeys(tokens)
        if left_the_repository(config.root, token)
    )


def _candidates(tree: Tree, text: str, near: Path) -> tuple[str, ...]:
    """Every path one sentence names that this tree does not have, before `.gitignore`.

    The half :func:`_paths` and :func:`unresolved` share, so the gate and the write path
    cannot come to disagree about what counts as missing — which they would, being written
    weeks apart against the same six rules (RK55, RK173, RK213, RK217, RK218).

    ``known`` is the bound method and not its answer (RK222): it caches, so passing it makes
    the listing lazy for free, and a sentence whose every path resolves asks git nothing.
    """
    return tuple(
        referenced.path
        for referenced in paths_in(
            text,
            tree.config.root,
            near=near,
            known=tree.directories,
            has=lambda token: tree.holds(token, near),
        )
        if not referenced.exists and not tree.anywhere(referenced.path)
    )


def unresolved(config: Config, text: str) -> tuple[str, ...]:
    """The paths a sentence about *shipped* work names that this repository lacks (RK497).

    The gate's own `path.missing` rule, asked before the prose exists rather than after it
    lands — which is L1, and the reason this is here rather than a second reading in
    :mod:`roadkeep.shipping`: one definition of missing, called from both ends.

    Measured cost, and why a write can afford it: `paths_in` asks the filesystem per token
    and asks git only for a token that fails (RK222), and `check-ignore` runs only for what
    survives that (RK213). A sentence whose paths resolve — every sentence anybody means to
    write — costs one `stat` each and no subprocess at all.

    Resolved against the **working tree**, never a revision: the caller is writing the entry
    now, so "now" is the only tree the question can be about.
    """
    near = config.path("changelog").parent
    tree = Tree(config)
    found = _candidates(tree, text, near)
    untracked = tree.declared_untracked([(token, near) for token in found])
    return tuple(token for token in found if token not in untracked)


def _declared_untracked(
    config: Config, tokens: Sequence[tuple[str, Path]]
) -> frozenset[str]:
    """The tokens `check-ignore` says this repository will never track (RK213).

    Both spellings per token — under the ledger's own directory and under the root (RK51) —
    so a `bin/…` written from `docs/` is asked about as the repository spells it. The answer
    is mapped back to the token, because that is what the finding names.
    """
    if not tokens:
        return frozenset()
    asked: dict[str, str] = {}
    for token, near in tokens:
        for base in (near, config.root):
            spelling = _spelled(os.path.normpath(str(config.root)), str(base), token)
            # None is a path above the root, which is nothing this repository's
            # `.gitignore` could have declared — and git refuses the **whole**
            # invocation over one of them (RK220), through the same door as "there is
            # no git here", where nothing is withheld. The *spelling* is dropped and
            # not the token, because the other base may still be inside.
            if spelling is not None:
                asked.setdefault(spelling, token)
    if not asked:
        return frozenset()
    try:
        answered = check_ignore(config.root, tuple(asked))
    except HistoryUnavailable:
        # The question could not be asked, so nothing is withheld: silence here would read
        # as "this repository declared it untracked", which is the one thing it did not.
        return frozenset()
    return frozenset(asked[name] for name in answered if name in asked)


def _spelled(root: str, base: str, token: str) -> str | None:
    """How git would spell this token from this base — decided **lexically** (RK225).

    `Config.relative` resolves the path, which is right where a junction has to be followed
    and ruinous where a check asks it per token: 34326 `realpath` calls at Turing's pin,
    7.4 s of an 11.5 s run. Every path compared against git's listing here is built from the
    config's own root, so the prefix already agrees and normalising the `..` segments
    textually gives the answer that listing holds — without touching the filesystem, which
    is the whole point of judging a revision.

    None where the spelling climbs out of the repository: git has nothing to say about a
    path above the root, and one of them refuses a whole `check-ignore` batch (RK220).
    """
    joined = os.path.normpath(os.path.join(base, token))
    if joined == root:
        return "."
    if not joined.startswith(root + os.sep):
        # Above the root, or on another mount: either way not a path git can be asked
        # about. A prefix test rather than `os.path.relpath`, which normcases and splits
        # both ends per call — 342330 `normcase` calls under 34133 of them (RK228) — and
        # cannot say more here, because both sides are built from the same config root.
        return None
    return joined[len(root) + 1 :].replace(os.sep, "/")


@dataclass(frozen=True, slots=True)
class Target:
    """A file carrying a projection of the backlog, as this tree holds it (RK104)."""

    #: The `export` flag that writes it, which is what the repair is named by.
    flag: str
    #: The path as the project spells it.
    where: str
    #: Which of the two shapes belongs between its markers.
    shape: str
    text: str


def _targets(config: Config, tree: Tree) -> tuple[Target, ...]:
    """Every file `export` writes that has been given somewhere to write (RK104).

    **The markers are the declaration**, so a file carrying none is not a target and is not
    read again (RK37): a README restating nothing cannot restate it wrongly, and demanding the
    container would be a gate inventing what only the author may put there — which is why
    `docs/index.html` here, a pitch with no strip in it, is not one.
    """
    out: list[Target] = []
    for flag, kind in DEFAULTS.items():
        # Through the resolver the write uses (RK1110), never a path spelled again here: a
        # target is a literal name or a governed role, and a gate that decided that for itself
        # would be a gate over a file nothing writes — which passes for the same reason the
        # drift got in.
        path = target_of(config, flag)
        raw = None if path is None else tree.blob(path)
        if raw is None:
            continue
        text = raw.decode("utf-8", errors="replace")
        if BEGIN in text:
            out.append(Target(flag, config.relative(path), kind.shape, text))
    return tuple(out)


def _projections(
    config: Config, documents: dict[str, Document], targets: tuple[Target, ...]
) -> list[Finding]:
    """The derived block in a file this tool does not own, checked where it was written (RK104).

    RK39 made the README's status table derived rather than restated, on the argument that a
    file repeating a backlog it cannot re-read is stale from the first ship. The derivation
    shipped and the gate over it did not, so a commit that ships a task and forgets `export`
    leaves a table contradicting the ledger — and what caught that here was a pytest fixture,
    which an adopting project does not install with the plugin.

    Two decisions, and each is the same one made elsewhere in this module:

    * **The block is compared, never repaired.** Every character of it is derived, so the
      repair is one command and the finding names it; writing it from here would make the
      linter a writer (L4), and `--fix` is where a derived field is normalised (RK16).
    * **The finding lands on the begin marker.** It is a defect about that block and the block
      has a place, the same reading RK34 makes of a column — so the report is usable, and the
      `Stop` hook's own narrowing (RK60) leaves a turn that merely moved a marker alone. What
      a projection goes stale against is a commit, and the commit is where this bites.

    The block is derived from the tree's own documents, so a baseline run compares a revision's
    README against the counts *that* revision's files render: a stale block is standing debt to
    be named and forgiven (RK84), not something every commit after it is charged for.
    """
    if not targets or "roadmap" not in documents:
        return []
    projection = project(config, documents)
    out: list[Finding] = []
    for target in targets:
        try:
            rendered = projection.body(target.shape, omit=enclosing(target.text))
            if splice(target.text, rendered, target.where) == target.text:
                continue
        except NoMarkers as error:
            # A begin with no end, or the two in the wrong order: the block has no extent, so
            # there is nothing to compare and `export` refuses the same file for the same
            # reason. Reported with the message that names the two lines to paste.
            out.append(
                Finding(
                    "export.unmarked",
                    target.where,
                    str(error),
                    _marked(target.text),
                    # The flag, so the door under the message names the same projection the
                    # message does (RK1110) — with a third target a literal `--readme` in the
                    # remedy contradicted it, which is the half a reader trusts.
                    subject=target.flag,
                )
            )
            continue
        out.append(
            Finding(
                "export.stale",
                target.where,
                f"the block between the roadkeep markers is not what the governed files "
                f"render: `{invocation()} export --{target.flag}` rewrites it, and every "
                f"character of it is derived",
                _marked(target.text),
                subject=target.flag,
            )
        )
    return out


def _marked(text: str) -> int | None:
    """Where the block starts, as an editor counts — the line the report sends a reader to."""
    for number, line in enumerate(text.split("\n"), start=1):
        if line.strip() == BEGIN:
            return number
    return None


def _cycles(backlog: Backlog, file: str) -> list[Finding]:
    """A group of tasks that wait on each other, anchored on its lowest id."""
    out: list[Finding] = []
    schema = backlog.config.schema
    for group in Graph.of(backlog).cycles():
        anchor = min(group, key=lambda i: id_order(i, schema))
        entry = backlog.entry(anchor)
        # A group of one is the same defect through a `Block X` dep the task is itself a
        # member of: the block cannot empty until this line ships, so the line waits on
        # itself. Worth its own sentence — "wait on each other" reads as a tool bug.
        message = (
            f"{' ↔ '.join(group)} wait on each other, so nothing in the group can be "
            f"started"
            if len(group) > 1
            else f"{anchor} is in its own blocker set, so no amount of shipping "
            f"anything else makes it ready"
        )
        out.append(
            Finding(
                "deps.cycle",
                file,
                message,
                None if entry is None else entry.lineno,
                anchor,
            )
        )
    return out


# -- the gate's own two readings (RK1170) -------------------------------------
#
# Here and no longer in `rendering`, which is where they were cut to when that module was made
# out of an 8,489-line `cli.py`: theirs was the cut with no import cycle, which is a fix for a
# file's size and not for where a verb's answer lives. `Report` is what both are about, so both
# are on it — and the finding-level helpers below are private to them.


def _report_rows(config: Config, report: Report, applied: Fix, root: str, quiet: bool) -> None:
    from roadkeep.rendering import _print, _tree  # noqa: PLC0415 - RK260

    if not quiet:
        _print(applied.stated())
        # Notes before the findings and the summary: a note is what the gate says about a
        # file it is passing, and after an exit-1 report nobody would read it (RK35).
        for note in report.notes:
            print(str(note))
    for line in applied.refusals():
        print(line, file=sys.stderr)
    if report.clean:
        # The files are named on the way out even when there is nothing to say: a gate
        # that passed by reading nothing looks exactly like a gate that passed.
        print(
            f"{', '.join(report.checked) or 'nothing'}: {_measured(report)}, clean"
            f"{_standing_line(report)}{_tree(root)}"
        )
        return
    mechanical = 0
    if not quiet:
        mechanical = _print_findings(config, report)
    added = "new " if report.baseline is not None else ""
    print(
        f"{report.problems} {added}problem(s) in {_measured(report)} across "
        f"{len(report.checked)} file(s): {_codes_line(report)}{_standing_line(report)}{_tree(root)}"
    )
    if mechanical:
        # Said once and never per line (RK420): the mechanical class is the one remedy that
        # is identical on every finding it answers, so repeating it under each of them would
        # spend the report's length on the findings that cost the reader nothing.
        print(f"{mechanical} of them need no decision: {invocation()} lint --fix")


def _print_findings(config: Config, report: Report) -> int:
    """Every finding, with a group that is one fact said once (RK469).

    A finding is per line and stays per line — the addresses are the evidence. What is said
    once is the *sentence and the remedy* where a whole run of them shares both: measured on
    Turing, 27 `section.ambiguous` findings and their 26 remedies were 80% of a 15,894-char
    report, two distinct messages once the anchor was taken off, and one `[refs]` line in
    `roadkeep.toml` closes every one.

    The same argument RK420 already makes one line down, where the mechanical remedy is
    counted rather than repeated under each finding, and the same one RK451 made about a file
    a crash left NUL: one finding because the loss is one. A report whose bulk is one sentence
    repeated is one a reader learns to skip (RK146), and it buries the four findings here that
    are each about a different line.

    Grouped by what the **emitter** declared they share, and only for runs of two or more: a
    single member is its own sentence, and a group of one printed as a group would be a
    heading over nothing.
    """
    mechanical = 0
    # By the key and not by adjacency: a report interleaves files, so the members of one
    # group are rarely consecutive — and a grouping that only folded runs would fold Turing's
    # and leave a fixture's alone, which is the shape that passes a test and misses the case.
    # Printed at the first member's place, so the report's order is otherwise the one it had.
    groups: dict[tuple[str, str, str], list[Finding]] = {}
    for finding in report.findings:
        if finding.shared:
            groups.setdefault((finding.code, finding.file, finding.shared), []).append(finding)
    printed: set[tuple[str, str, str]] = set()
    for finding in report.findings:
        key = (finding.code, finding.file, finding.shared)
        run = groups.get(key, []) if finding.shared else []
        if len(run) < 2:
            print(str(finding))
            mechanical += _print_remedy(finding, config)
            continue
        if key in printed:
            continue
        printed.add(key)
        first = finding
        # The pair once, the addresses under it: `file:line` each, which is what an editor
        # opens and what an author choosing which file takes the namespace counts.
        print(f"{first.file}  {first.code}  {len(run)} addresses {first.shared}")
        print(f"    {'  '.join(f'{one.token}:{one.lineno}' for one in run)}")
        mechanical += _print_remedy(first, config)
    return mechanical


def _print_remedy(finding: Finding, config: Config) -> int:
    """Print what closes this finding, and return 1 where that was `--fix`'s (RK420).

    Printed by default rather than behind a flag. The defect being answered is a caller
    spending a *turn* to learn the command, so a report that carries it only on request has
    the cost exactly where it was: the second call is the thing being removed.

    The mechanical class is counted instead of printed, and every other kind gets its line —
    including `decide`, whose whole content is the two doors and what separates them, since
    a decision printed as one word is a decision made by running one and reading its refusal.
    """
    from roadkeep.remedying import remedy  # noqa: PLC0415 - RK260

    found = remedy(finding, config)
    if found is None or found.kind == "fix":
        return 1 if found is not None else 0
    for line in str(found).splitlines():
        print(f"    {line}" if not line.startswith("    ") else line)
    return 0


def _lint_json(config: Config, report: Report, applied: Fix, root: str) -> dict[str, object]:
    baseline = report.baseline
    return {
        # First, because every path below is relative to it and a payload a second tool files
        # against the wrong project is worse than one it cannot file at all (RK299). The same
        # key `install --json` already uses, spelled the same way.
        "root": root,
        "clean": report.clean and not applied.refused,
        # Absent without `--baseline`, so a caller reading `problems` cannot mistake a
        # difference for a total: with it, `findings` holds only what this tree added.
        **(
            {}
            if baseline is None
            else {
                "baseline": {
                    "rev": baseline.rev,
                    "standing": baseline.standing,
                    "forgiven": [_finding_json(f, config) for f in baseline.forgiven],
                    "resolved": [_finding_json(f, config) for f in baseline.resolved],
                }
            }
        ),
        "fixed": [
            {
                "file": repair.file,
                "line": repair.lineno,
                "id": repair.id,
                "reasons": list(repair.reasons),
                "before": repair.before,
                "after": repair.after,
                # A key on the same list rather than a `removed` list beside `fixed` (RK357):
                # `line` means the pre-pass position here, and a consumer resolving addresses
                # has to know that from the payload rather than from an empty `after`.
                "removed": repair.removed,
            }
            for repair in applied.repairs
        ],
        "kept": [
            {"file": s.file, "line": s.lineno, "id": s.id, "reason": s.reason}
            for s in applied.skipped
        ],
        "refused": list(applied.refused),
        "checked": list(report.checked),
        "lines": report.lines,
        "sections": report.sections,
        "budgets": report.budgets,
        "problems": report.problems,
        "codes": report.codes(),
        "findings": [_finding_json(f, config) for f in report.findings],
        "notes": [
            {
                "code": note.code,
                "file": note.file,
                "line": note.lineno,
                "id": note.id or None,
                "message": note.message,
                **_remedy_json(note, config),
            }
            for note in report.notes
        ],
    }


def _standing_line(report: Report) -> str:
    """What the baseline forgave, and what left — said out loud, both of them (RK84).

    Both, because either number alone is the misreading §RK84 was written about: the run
    that deleted 160 lines of rationale took the count *down* by eight, and the drop read as
    an improvement right up until the two findings it added were looked at individually.
    """
    baseline = report.baseline
    if baseline is None:
        return ""
    counts = f"{baseline.standing} standing"
    if baseline.resolved:
        counts += f", {len(baseline.resolved)} resolved"
    return f" against {baseline.rev} ({counts})"


def _measured(report: Report) -> str:
    """What was read, in its own units: task lines, sections, and budgeted files."""
    scope = f"{report.lines} line(s), {report.sections} section(s)"
    return scope if not report.budgets else f"{scope}, {report.budgets} budget(s)"


def _codes_line(report: Report) -> str:
    return "  ".join(f"{code} {count}" for code, count in report.codes().items())


def _finding_json(finding: Finding, config: Config) -> dict[str, object]:
    return {
        "code": finding.code,
        "file": finding.file,
        "line": finding.lineno,
        # Only a character finding has one (RK34), and it is what makes an invisible
        # codepoint findable: `file:line:column` is what an editor jumps to.
        "column": finding.column,
        "id": finding.id or None,
        "message": finding.message,
        **_remedy_json(finding, config),
    }


def _remedy_json(finding: object, config: Config) -> dict[str, object]:
    """The remedy, as a key that is absent rather than null when the table has none (RK420).

    Absent and not `"remedy": null`, because a consumer that reads the key at all is one
    about to run what is in it, and a null is a shape it has to branch on before it can
    tell "no command exists" from "this build predates the field".
    """
    from roadkeep.remedying import remedy  # noqa: PLC0415 - RK260

    found = remedy(finding, config)
    return {} if found is None else {"remedy": found.payload(_served(config))}
