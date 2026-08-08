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
  or naming a block whose every line is gone. Written as deps, most of these already
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
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path

from roadkeep import queueing, scoping
from roadkeep.backlog import Backlog, DepStatus, id_order
from roadkeep.blocking import removable
from roadkeep.config import PROSE_ROLES, ROLES, Config, spent
from roadkeep.document import Document, Entry, Heading, ending
from roadkeep.exporting import BEGIN, DEFAULTS, NoMarkers, project, splice
from roadkeep.graph import Graph
from roadkeep.history import (
    HistoryUnavailable,
    check_ignore,
    indexed,
    blob_at,
    content_at,
    resolves,
    touched_since,
    tracked_at,
    tracked_now,
)
from roadkeep.markers import derive
from roadkeep.schema import PARTIAL, Dep, DepKind, Task, over_by
from roadkeep.sections import Section, anchored, find
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

#: Variation selectors, which are `Mn` and not a format category: invisible all the same,
#: and the class the parser already had to defend against (`_looks_like_marker`, RK2).
_VARIATION_SELECTORS = frozenset(
    chr(point) for point in (*range(0xFE00, 0xFE10), *range(0xE0100, 0xE01F0))
)

_ENDING_NAMES = {"\r\n": "CRLF", "\n": "LF", "\r": "CR"}


@dataclass(frozen=True, slots=True)
class Finding:
    """One defect, at one place. ``code`` is stable; ``message`` names the fix.

    The code is the same string :class:`~roadkeep.schema.Violation` uses where the
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
    """Every check, over whichever tree is being judged."""
    findings: list[Finding] = []
    findings.extend(_absent(config, tree))

    documents: dict[str, Document] = {}
    for role in LINE_ROLES:
        document = tree.document(role)
        if document is not None:
            documents[role] = document

    for role, document in documents.items():
        findings.extend(within(config, role, document))
        findings.extend(_characters(config, role, document))
    findings.extend(_across(config, documents))
    findings.extend(_scope(config, documents.get("roadmap")))
    queued, queue_notes = _queue(config, documents)
    findings.extend(queued)
    notes: list[Note] = _collective(config, documents)
    notes.extend(queue_notes)
    notes.extend(_disagreeing(config, tree))
    if since is not None:
        notes.extend(_turned(config, documents, since))

    prose: dict[str, Document] = {}
    for role in PROSE_ROLES:
        document = tree.document(role)
        if document is not None:
            prose[role] = document
    anchors = {role: anchored(document) for role, document in prose.items()}
    sections = tuple(section for found in anchors.values() for section in found)
    if prose:
        findings.extend(_pointers(config, documents, anchors))
        for role, document in prose.items():
            findings.extend(_orphans(config, documents, document, anchors, role=role))
        if since is not None:
            notes.extend(_unpaired(config, anchors.get("improvements", ()), since))
    # After both halves are loaded, because the remedy this names is decided against the
    # *whole* governed set and not against the file the duplicate is in (RK417).
    findings.extend(_repeated(config, {**documents, **prose}))
    findings.extend(_paths(config, documents, tree))

    targets = _targets(config, tree)
    findings.extend(_projections(config, documents, targets))
    findings.extend(_budgets(config, tree))

    checked = _checked(config, documents, prose, targets)
    return Report(
        findings=_ordered(_untainted(findings), checked),
        checked=checked,
        lines=sum(len(d.entries) for d in documents.values()),
        sections=len(sections),
        budgets=len(config.budgets),
        notes=tuple(notes),
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
    if config.priority:
        checked.append(_configured(config))
    return tuple(checked)


def _untainted(findings: list[Finding]) -> list[Finding]:
    """Every finding except the ones a codepoint already explains (RK34).

    A line carrying a byte nobody typed is not a line this format can judge: the parser read a
    string the author cannot see, so every other diagnosis of it names a consequence. Report
    the codepoint; the rest is decidable on the next run.
    """
    tainted = {
        (f.file, f.lineno) for f in findings if f.code.startswith("char.") and f.lineno
    }
    return [
        f
        for f in findings
        if f.code.startswith("char.") or (f.file, f.lineno) not in tainted
    ]


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


def suspect(char: str, *, indent: bool = False) -> bool:
    """Is this codepoint invisible, or a space that is not the space?

    Defined by Unicode category rather than a hand-kept list, so a control or format
    character nobody has met yet is caught too: `Cc` and `Cf` are not text, `Zl` and `Zp`
    are line breaks inside a line, and a `Zs` other than U+0020 renders as a space while
    comparing unequal to one. Variation selectors are `Mn` and named explicitly — U+FE0F
    on a marker is the case the parser already had to defend against (RK2).

    `indent` is where the one control character that **renders** stops being suspect at all
    (RK146). A tab is `Cc`, so this reported it as "invisible in an editor", which of a tab
    is untrue — and RK126 rightly withheld it from `--fix`, because the indentation of a
    nested line is read off the file and written back verbatim (RK49). Two correct decisions
    left a project that indents with tabs holding a finding no command could ever clear,
    which is what teaches a reader to stop reading the report. In the indentation a tab is
    text; past it, it is a separator where this format writes a space, and :func:`_named`
    says so instead.
    """
    if char in _VARIATION_SELECTORS:
        return True
    if char == TAB:
        return not indent
    category = unicodedata.category(char)
    return category in ("Cc", "Cf", "Zl", "Zp") or (category == "Zs" and char != " ")


#: The one control character with a rendering, and the one the model keeps (RK49).
TAB = "\t"
#: What a line may be indented with, and the span :func:`suspect` reads a tab as text in.
_INDENT = " \t"


def indentation(body: str) -> int:
    """How many leading characters of this line are its indentation, tabs included.

    One reading, shared by the gate and the fixer, because a tab is text in this span and a
    separator past it — and two functions deciding where the span ends is one pair that
    would disagree about a line somebody nested (RK146).
    """
    return len(body) - len(body.lstrip(_INDENT))


def repaired(char: str, *, indent: bool = False) -> str | None:
    """What `--fix` writes in place of a suspect codepoint, or None to leave it (RK126).

    :func:`suspect` is what the gate reports; this is what a normalizer may act on, and the
    split is RK16's own: a control or format character is **not text under any reading**, so
    removing it is not a decision about anybody's prose — while a `Zs` that is not U+0020
    *renders* as a space, and turning one into a space is a change to text that the author
    is the one to make.

    A tab is the case that needs the position (RK146): inside the indentation it is left
    alone, because deleting it re-parents somebody's task, and past it the repair is a
    **space** rather than a deletion — the format writes one there, and removing the
    separator would glue two fields into a line that no longer parses.

    Here rather than in :mod:`roadkeep.fixing` because it is the same law as the report one
    function up, and a second list of codepoints is the one that would drift.
    """
    if char == TAB:
        return None if indent else " "
    if char in _VARIATION_SELECTORS:
        return ""
    if unicodedata.category(char) in ("Cc", "Cf", "Zl", "Zp"):
        return ""
    return None


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
    if char == TAB:
        # Past the indentation, which is the only place `suspect` still reports one: the
        # defect is not that it cannot be seen but that it is a separator this format does
        # not write, and `--fix` turns it into the space that was meant (RK146).
        return Finding(
            "char.tab",
            file,
            f"{point} tab at column {column}: the format separates fields with a space, "
            f"so a tab here is a separator the grammar reads as part of a field",
            lineno,
            task_id,
            column,
        )
    if unicodedata.category(char) == "Zs":
        return Finding(
            "char.space",
            file,
            f"{point} {name} at column {column}: renders as a space and is not one, so "
            f"the grammar reads a word where a separator was meant",
            lineno,
            task_id,
            column,
        )
    return Finding(
        "char.invisible",
        file,
        f"{point} {name} at column {column}: invisible in an editor, so every other "
        f"diagnosis of this line names the consequence instead",
        lineno,
        task_id,
        column,
    )


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


def _budgets(config: Config, tree: Tree) -> list[Finding]:
    """Every always-loaded file, against what it declared it may cost (RK30).

    Measured in bytes off the tree and lines by counting terminators, so nothing here has
    to decode a file the tool does not govern: a budget is about what a loader pays, and
    an instruction file is not a format this tool has any business parsing (L4). Off the
    tree and not off disk for RK84's reason — an `agents.md` pushed over its budget by this
    change is the finding a baseline exists to keep, and both runs reading the same bytes
    would forgive it.
    """
    out: list[Finding] = []
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
    return out


def _collective(config: Config, documents: dict[str, Document]) -> list[Note]:
    """What a `Block X` or a range actually names, said out loud (RK35).

    Only when it expands to **two or more** open tasks, which is precisely the case the
    line hides: at one there is no surprise to report, and at zero the annotation already
    reads ✅ because the dep is satisfied (RK8). A note per token below that threshold
    would be output nobody reads, which is the failure mode RK16 exists to avoid.
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
            if config.schema.classify_dep(dep) not in (DepKind.BLOCK, DepKind.RANGE):
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

    `ship` is the only verb that computes it — `event T282 Block AI empty` — and says it once,
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

    for reject in document.rejects:
        # The line the parser could not read at all. It is reported here and counted
        # nowhere else, which is the difference between `audit` and a gate.
        out.append(Finding("line.unparsed", file, reject.reason, reject.lineno))

    seen: dict[str, int] = {}
    for entry in document.entries:
        task = entry.task
        for violation in document.schema.validate(task):
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
    whose every line has left — plus one named twice, which is two answers about where the
    same work sits. At `file:line:column` like everything else (RK34).

    Two states are deliberately **not** findings. An entry naming a merely blocked task is
    a queue doing its job — that is what a queue is *for* — and a declared block holding
    nothing **yet** is legitimate, `block add` writing the heading before the lines; the
    two are told apart by whether the ledger has entries under that heading, which is the
    only record that work ever left it.

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
        finding = _dead(config, backlog, token, file, lineno, column, documents)
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
    documents: dict[str, Document],
) -> Finding | Note | None:
    """How this one entry is dead, or nothing where the tier can still fire.

    One resolution, from the code that resolves a dep, so a token cannot mean one thing in
    an annotation and another in the order (RK11's rule, and :func:`~roadkeep.queueing.typed`
    at the other end).
    """
    resolution = backlog.resolve_dep(Dep(token))
    if resolution.kind is DepKind.BLOCK:
        return _dead_block(
            config, backlog, token, file, lineno, column, documents, resolution.detail
        )
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
    documents: dict[str, Document],
    detail: str,
) -> Finding | Note | None:
    """The half of :func:`_dead` about a `Block X` entry, whose three states differ.

    A block nothing declares is the dep resolver's own answer. Between the other two the
    ledger is what decides: a heading with entries under it and no open line is a block
    that **emptied**, and one with neither is a heading written before its lines — which is
    the order `block add` prescribes, so it is a note.
    """
    label = config.schema.block_of_dep(Dep(token))
    if label not in backlog.declared_blocks():
        return Finding(
            "priority.block",
            file,
            f"queues {token} and {detail}",
            lineno,
            column=column,
            subject=token,
        )
    if backlog.open_in_block(label):
        return None
    ledger = documents.get("changelog")
    if ledger is not None and ledger.block(label):
        return Finding(
            "priority.block-empty",
            file,
            f"queues {token}, whose every line has shipped or left: a tier that fires on "
            f"nothing is an order the author believes is in force",
            lineno,
            column=column,
            subject=token,
        )
    return Note(
        "priority.block-unstarted",
        file,
        f"queues {token}, which no line is filed under yet: the tier fires on nothing "
        f"until one is",
        lineno,
        subject=token,
    )


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
        shipped = ledger.by_id()
        for task_id, entry in roadmap.by_id().items():
            if task_id in shipped and not _in_halves(entry, shipped[task_id]):
                out.append(
                    Finding(
                        "id.two-files",
                        file,
                        f"also on line {shipped[task_id].lineno} of "
                        f"{config.relative(config.path('changelog'))}: open and "
                        f"recorded as gone are not both true",
                        entry.lineno,
                        task_id,
                    )
                )

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
    (:class:`~roadkeep.document.RepeatedHeading`) — a gate that stayed quiet would be the
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
                if _droppable(files, label)
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
                        f"label is one heading, and a write files under this one by "
                        f"position alone — {remedy}"
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
    if _droppable(files, label):
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


def _in_halves(open_line: Entry, recorded: Entry) -> bool:
    """Do the two files *say* this id is a live partial, rather than contradict each other?

    `id.two-files` was written for one shape — a line somebody shipped and forgot to delete
    — and half a delivery is the other one, where open and recorded are both true (RK122).
    The two are told apart by what the files declare, and the test is the one
    :func:`~roadkeep.shipping._already_recorded` already applies at the door `ship` refuses
    at: a ⏳ line, or an entry naming a half. Either alone is enough, because a project that
    adopted the format writes only the first — Shio's ⏳ SH238 carries a bare id in the
    ledger, and it was **the only one of seven** in that state the gate reported, the six
    others being silent behind a parenthetical the parser could not read (RK121). A finding
    whose only avoidance is a syntax error teaches the syntax error.
    """
    return open_line.task.status == PARTIAL or bool(recorded.task.part)


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
                )
            )
        seen.setdefault(anchor, section.first)
        out.extend(_budget(prose, section, pointed=anchor in pointed, file=file))
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
    # Which directories the repository knows, at whichever tree this run is judging (RK217):
    # a claim is about the repository, so the disk's current shape is not what decides it.
    # The bound method and not its answer (RK222): it caches, so passing it makes the
    # listing lazy for free — a ledger whose every path resolves asks git nothing.
    known = tree.directories
    # One pass, keeping what it found (RK223). The candidates have to be gathered before
    # `.gitignore` is asked, because one call for all of them is what keeps that question
    # cheap (RK213) — and gathering them with a comprehension of its own made the findings
    # comprehension repeat the whole scan: 1602 entries into `paths_in` for 801 entries,
    # and 2.9 s of a `lint` that a pre-commit hook waits for (RK17).
    unresolved = [
        (entry, referenced.path)
        for entry in document.entries
        for referenced in paths_in(
            entry.raw,
            config.root,
            near=near,
            known=known,
            has=lambda token: tree.holds(token, near),
        )
        if not referenced.exists and not tree.anywhere(referenced.path)
    ]
    untracked = tree.declared_untracked([(token, near) for _, token in unresolved])
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
    ]


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
    for flag, (name, shape) in DEFAULTS.items():
        path = config.root / name
        raw = tree.blob(path)
        if raw is None:
            continue
        text = raw.decode("utf-8", errors="replace")
        if BEGIN in text:
            out.append(Target(flag, config.relative(path), shape, text))
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
            if splice(target.text, projection.body(target.shape), target.where) == target.text:
                continue
        except NoMarkers as error:
            # A begin with no end, or the two in the wrong order: the block has no extent, so
            # there is nothing to compare and `export` refuses the same file for the same
            # reason. Reported with the message that names the two lines to paste.
            out.append(
                Finding("export.unmarked", target.where, str(error), _marked(target.text))
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
