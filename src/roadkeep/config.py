"""`roadkeep.toml` — the format's variability, declared per project (RK3, L6).

Three real projects, one format: Shio numbers `SH` and has no strategy file, Turing
numbers `T` and has one, Cursarei keeps its roadmap under `docs/roadmap/`. The moment
any of that is hardcoded the tool serves exactly one repository, so everything that
differs is a key here and everything that does not is in :mod:`roadkeep.kernel.schema`.

Two decisions that matter more than the file format:

* **An unknown key is refused, never ignored.** A mistyped `symptom_max` that silently
  falls back to the default is a limit the author believes is in force and is not —
  the same failure the whole tool exists to remove, one layer down. Refusals are
  batched and name the allowed keys.
* **Config is found by walking up**, like git. A command run from a subdirectory has to
  reach the same backlog as one run from the root, or the answer depends on the shell's
  working directory.

Reading order: `roadkeep.toml` first, then `[tool.roadkeep]` in `pyproject.toml`. A
project that already has one config file does not need a second.
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # a string annotation under `from __future__ import annotations` (RK261)
    from roadkeep.kernel.document import Document
from roadkeep.kernel.schema import (
    DEFAULT_GRAMMARS,
    DEFAULT_HEADING_WORD,
    DEFERRED,
    DROPPABLE,
    MARKER_NAMES,
    OPEN_MARKERS,
    REF_PREFIX_RE,
    REF_SEPARATOR,
    RETIRED,
    SHIPPED,
    UNDESIGNED,
    Dep,
    DepKind,
    Grammar,
    Schema,
)

CONFIG_NAME = "roadkeep.toml"
PYPROJECT = "pyproject.toml"

#: The governed files. A project declares the ones it has; the rest are absent,
#: not empty — `strategy` missing means Shio, not a Shio with an empty strategy. The
#: same is true of `deferred` (RK96), which is why it is not in :data:`DEFAULT_PATHS`:
#: a project that never pauses anything has no store, rather than an empty one.
ROLES = ("roadmap", "changelog", "improvements", "strategy", "deferred")

#: The governed files a `→ §<anchor>` pointer may address (RK172). Both, because `[files]`
#: declares strategy as a governed role and a line pointing at it is already in the model.
#: Here rather than beside either reader, because the gate and `show` resolving against
#: different sets is exactly what RK186 was: one of them called a section the other found.
#: Order is where a design goes when there is none yet — improvements first.
PROSE_ROLES = ("improvements", "strategy")

DEFAULT_PATHS: Mapping[str, str] = {
    "roadmap": "docs/ROADMAP.md",
    "changelog": "docs/CHANGELOG.md",
    "improvements": "docs/IMPROVEMENTS.md",
}

_TOP_KEYS = frozenset(
    {
        "prefix",
        "ids",
        "ref_scheme",
        "files",
        "limits",
        "markers",
        "id_sources",
        "reserved_ids",
        "priority",
        "budgets",
        "ledger",
        "rules",
        "non_goals",
        "headings",
        "report",
        "claims",
        "refs",
        "tools",
        "grammar",
    }
)
#: `[grammar.<role>]` — the shape of a role's records, which L6 declared everything about
#: except (RK1064). Three keys and no fourth: what a record starts from, which markers it
#: may carry, and which slots it does without. `states` is not among them — whether a file
#: *is* a status is a fact about the tool's own roles, so a project may reshape a line and
#: never invent a state for which no verb exists.
_GRAMMAR_KEYS = frozenset({"extends", "markers", "drop"})
#: `[tools]` — what one served tool may cost a session (RK1059). Its own table and not a
#: `[budgets]` entry, because every key there is a **path** and this cost is not a file: it
#: is composed per session from the parser, the config and the `TOOLS` table, so an entry
#: under a name no file has would break the one thing that table's refusals can say.
#:
#: Per tool and not per list, which is the decision RK464 deliberately left open. A ceiling
#: on the total fails on whichever tool is added last and names nothing; a per-tool one is
#: refused by the tool that grew, which is the tool whose description somebody just edited —
#: and `budget --tools` already ranks them, so the read that composes the fix exists.
_TOOLS_KEYS = frozenset({"characters"})
#: `[claims]` — how long a claim on a line reads as held (RK151). Its own table for the reason
#: `[headings]` has one: a bare `held` beside `prefix` would read as one of the limits, and it
#: is not a limit on any field — it is the one number in the claim mechanism that is a
#: judgement about how long work takes.
_CLAIMS_KEYS = frozenset({"held"})
#: `[headings]` — the word a project files work under (RK75). Its own table and not a top
#: key, because the heading is a shape with more than one part and the next question about
#: it (a sub-block that carries no word at all) belongs under the same heading.
_HEADING_KEYS = frozenset({"word"})
#: `[ids]` — the shape of an id, where a project already spells one the format refused
#: (RK106). Its own table for the reason `[headings]` is: the spelling has more than one
#: part, and a bare `pad` beside `prefix` would read as one of the limits.
_IDS_KEYS = frozenset({"pad", "suffix"})
#: `[non_goals]` — the two fields the roadmap's other bullet has (RK70). Opt-in for RK66's
#: reason: two live corpora wrote theirs as free prose, and a default that reported findings
#: on the first run is a gate that gets bypassed instead of adopted.
_SCOPE_KEYS = frozenset({"lead", "why"})
_BUDGET_KEYS = frozenset({"lines", "bytes"})
#: Which slots the ledger's lines carry (RK43, RK48). Its own table because the shape of a
#: file is one decision with two parts, and `markers.ledger` put half of it under a heading
#: that cannot name the other half: a symptom is not a marker.
_LEDGER_KEYS = frozenset({"marker", "symptom"})
#: The rules a role may switch off (`[rules.<role>]`, RK52). Not limits, because they
#: are not numbers, and not `[ledger]`, because that table says which *slots* a line has.
#: `ref` joins them for RK66's reason: whether a line must point at a rationale section is
#: a convention, not a fact about the format, and a project that documents the opposite one
#: gets a finding for obeying itself.
_RULE_KEYS = {
    "one_sentence": "one_sentence",
    "terminator": "terminator",
    "ref": "ref_required",
}
_LIMIT_KEYS = {
    "symptom": "symptom_max",
    "why": "why_max",
    # What a partial entry's qualifier may cost (RK121). Per project like every other
    # limit (L6): `local half` and `the SH22 half` are one corpus's answer to "which part",
    # and a project whose halves have longer names has not made the qualifier a summary.
    "part": "part_max",
    "line": "line_max",
    # A section is prose, so its budget is words and its shape is a width (RK9).
    "section": "section_max",
    "prose": "prose_width",
}
_MARKER_KEYS = frozenset({"open", "shipped", "retired", "deferred", "undesigned"})
# The invisible ones. A marker carrying U+FE0F renders identically and compares
# unequal, so a config that declares one puts every line in the file permanently
# out of round-trip. Refuse it where it is typed.
_INVISIBLE = {"️": "U+FE0F", "‍": "U+200D", "​": "U+200B"}


@dataclass(frozen=True, slots=True)
class Budget:
    """A file that is loaded every turn, and what it is allowed to cost (RK30).

    Declared here rather than in the file's own prose, which is the arrangement that let
    Shio's `agents.md` reach 186 KB while stating a 150-line rule at the bottom of itself:
    a budget nothing reads is a budget nothing enforces. Both numbers are optional and at
    least one is required — an entry that declares neither is refused, because it would
    read as a budget and hold nobody to anything.
    """

    path: Path
    lines: int | None = None
    #: Size on disk. Bytes and not tokens: the tool guesses at nothing, and 186 KB was the
    #: measurement that started this — roughly 46k tokens, spent on every single turn.
    bytes: int | None = None


def spent(raw: bytes) -> dict[str, int]:
    """What an always-loaded file costs, in the two units `[budgets]` declares (RK30).

    Bytes and not text, for the reason the gate reads them that way: a budget is about what
    a loader pays, and an instruction file is not a format this tool has any business
    decoding (L4). Here rather than in either reader, because the gate that refuses the
    overrun (RK30) and the read that reports the room before an edit (RK345) are two callers
    of one measurement — and two spellings of it would be the disagreement RK50 removed.
    """
    return {"lines": raw.count(b"\n") + (0 if raw.endswith(b"\n") or not raw else 1),
            "bytes": len(raw)}


@dataclass(frozen=True, slots=True)
class Scope:
    """What a governed non-goal may say, when a project declares its list governed (RK70).

    Two numbers and no marker, no id and no pointer: a non-goal has no lifecycle to state.
    The list is eight lines that change once a year, and an id would buy them a retirement,
    a rename and a second file to disagree with — so the lead *is* the address.
    """

    #: The bolded head, which is what a `brief` prints and what a duplicate is judged on.
    lead: int = 80
    #: The rest of the bullet. Longer than a task's `why` and not one sentence: the corpus
    #: argues these in two, and the file has no rationale section to send the second to.
    why: int = 320


#: `[claims] held`, in **minutes** — how long a claim reads as held before a later caller
#: steps over it (RK119, RK151). An hour by default: long enough that a worker mid-task still
#: holds the line, short enough that a claim nobody released clears inside one session.
CLAIM_HELD = 60
#: The longest window this will accept. The reason there is an expiry rather than a lock is
#: that a killed worker must not take a line out of the backlog for ever, so a window nobody
#: would wait out is the defect coming back under a config key (RK151) — one working day is
#: where that starts, an abandoned claim past it surviving a night. It is also what turns the
#: unit into a refusal: `held = 3600`, meant as seconds, is refused rather than obeyed.
CLAIM_HELD_MAX = 480


class ConfigError(ValueError):
    """Every problem with the file, not the first one found."""

    def __init__(self, problems: tuple[str, ...], path: Path | None = None) -> None:
        self.problems = tuple(problems)
        self.path = path
        where = f"{path}: " if path else ""
        super().__init__(where + "; ".join(self.problems))


#: The three bytes a Windows editor writes ahead of a UTF-8 file, which `tomllib` refuses by
#: specification — and refuses at line 1, column 1, where the statement is correct.
_BOM = b"\xef\xbb\xbf"


def _marked(path: Path, broken: tomllib.TOMLDecodeError) -> Exception:
    """A TOML refusal, re-read as the byte that caused it where that is what it is (RK1030).

    `Invalid statement (at line 1, column 1)` is `tomllib` answering about the first thing it
    could parse, which is `prefix = "RK"` — correct, and pointing at a line with nothing wrong
    with it. What is wrong is three bytes no editor shows, in the file a project writes before
    it has run anything, and on Windows the default route writes them: PowerShell 5.1's
    `Set-Content -Encoding utf8` and `Out-File` both add the mark.

    **Named and not stripped**, which is the difference from :func:`roadkeep.verbs.reading`'s
    answer to the same byte one file over. A prose field is a sentence somebody typed and the
    mark is the encoder's; this file is the project's own declaration, and a tool that quietly
    accepted one encoding variant of it would teach nothing — the author would meet the mark
    again in `git diff`, in their editor's next save, and in whatever reads the file next.

    Every other TOML error is handed back exactly as `tomllib` wrote it: this reads the bytes
    only after a refusal, and only to answer the one question the refusal could not.
    """
    try:
        if not path.read_bytes().startswith(_BOM):
            return broken
    except OSError:
        return broken
    return ConfigError(
        (
            f"the file opens with a byte-order mark (U+FEFF), which TOML has no reading "
            f"for — so the refusal below is about the first line it could parse and not "
            f"about anything wrong with it ({broken}). Re-save it as UTF-8 without a BOM; "
            f"in PowerShell, `Set-Content -Encoding utf8` and `Out-File` both write one",
        ),
        path,
    )


@dataclass(frozen=True, slots=True)
class Config:
    """Where the governed files are, and which format they are written in."""

    root: Path
    schema: Schema = field(default_factory=Schema)
    paths: Mapping[str, Path] = field(default_factory=dict)
    #: Files to scan for ids beyond the governed four (RK4). This repository keeps
    #: task ids in `agents.md`, and an id the scan misses is an id that gets reused.
    extra_id_sources: tuple[Path, ...] = ()
    #: Ids this project has spoken for without writing them as a line (RK1031). Shio reserves
    #: one per **epic** — `SH25`, `SH62` — each owning a sub-range whose sub-tasks ship under
    #: their own numbers, so the epic id is never a task and never an entry; it exists so a
    #: reader can name a body of work in one token.
    #:
    #: Declared and not inferred, because a reservation and a typo are the same string: the
    #: deriver skips these because they **are** taken, the gate stops reporting them as spent,
    #: and an id that is not on the list still fails exactly as it did.
    reserved: tuple[str, ...] = ()
    #: What jumps the queue, in order: an id or a `Block X`, and nothing else (RK11).
    #: *Declared*, because the alternative is a "## Priority queue" section written in
    #: prose — which Shio has, and which a tool that reads it would be interpreting
    #: rather than validating (L4).
    priority: tuple[str, ...] = ()
    #: Always-loaded files and what each may cost (RK30). Not a governed role: the tool
    #: writes none of these, it only refuses to let one grow unwatched.
    budgets: tuple[Budget, ...] = ()
    #: `[grammar.<role>]` — the shape of one role's records, where a project declares one
    #: (RK1064), keyed by role and applied by :meth:`schema_for`. Empty is every project
    #: that has not spoken about a shape, and then the grammars the tool ships are what
    #: apply: a role nobody declared is not a role without one.
    grammars: Mapping[str, Grammar] = field(default_factory=dict)
    #: `[tools] characters` — what one served tool may cost the session that connects the
    #: server (RK1059), or **None** where the project declares none, which is every project
    #: that does not serve the surface and every one that has not looked at the number yet.
    #: The same argument `budgets` makes about a resident file, about the schema: a cost
    #: nobody counts is a cost that moves, and every flag added to a served verb spends it
    #: in an edit whose diff shows one argument.
    tool_characters: int | None = None
    #: `[limits.<role>]` — the numbers one file is held to instead of the shared ones
    #: (RK50), keyed by role and applied by :meth:`schema_for`. Empty is the common case:
    #: a project declares one only where a file's economics differ, which in practice is a
    #: ledger of history against a roadmap refused at insertion.
    limits: Mapping[str, Mapping[str, int]] = field(default_factory=dict)
    #: `[rules.<role>]` — a prose rule one file is not held to (RK52), applied by
    #: :meth:`schema_for` alongside that file's limits.
    rules: Mapping[str, Mapping[str, bool]] = field(default_factory=dict)
    #: `[refs]` — the namespace a prose role's outline addresses live in (RK340), keyed by
    #: role and applied by :meth:`schema_for`. Empty is every project that has not declared
    #: one, and the behaviour is exactly what it was: one flat set of addresses across both
    #: prose files, which is right for a project whose two files never collide and is the
    #: `section.ambiguous` nothing could configure away for the one where they do.
    refs: Mapping[str, str] = field(default_factory=dict)
    #: `[non_goals]` — declared when this project's non-goals are governed too (RK70), and
    #: **None** when they are prose, which is what every project's were before it opted in.
    non_goals: Scope | None = None
    #: `[report] upstream` — where a capture of a defect *in this tool* would be filed
    #: (RK87), as `owner/repo`. Configuration and not a constant, so a fork reports to
    #: itself (L6); **None** means `report --issue` refuses rather than guessing a
    #: destination, since a wrong one is a private repository's contents in a stranger's
    #: tracker. Nothing is ever sent from here — this only addresses the command a person
    #: runs.
    upstream: str | None = None
    #: `[claims] held` — how many **minutes** a claim on a line reads as held (RK151). Per
    #: project, because how long a task takes is the one thing about a claim that differs
    #: between backlogs (L6), and bounded by :data:`CLAIM_HELD_MAX`, because a window nobody
    #: would wait out is the lock this was designed not to be.
    held: int = CLAIM_HELD
    source: Path | None = None

    # -- construction ------------------------------------------------------

    @classmethod
    def default(cls, root: str | Path = ".") -> Config:
        """The layout of a project that has not declared one."""
        base = Path(root).resolve()
        return cls(
            root=base,
            paths={role: base / rel for role, rel in DEFAULT_PATHS.items()},
        )

    @classmethod
    def discover(cls, start: str | Path = ".") -> Config:
        """Walk up for a config; fall back to the defaults at ``start``."""
        found = find_config(start)
        return cls.load(found) if found else cls.default(start)

    @classmethod
    def load(cls, path: str | Path) -> Config:
        path = Path(path).resolve()
        with path.open("rb") as handle:
            try:
                document = tomllib.load(handle)
            except tomllib.TOMLDecodeError as broken:
                raise _marked(path, broken) from None
        if path.name == PYPROJECT:
            document = document.get("tool", {}).get("roadkeep", {})
        return cls.parse(document, root=path.parent, source=path)

    @classmethod
    def parse(
        cls, data: Mapping[str, object], root: str | Path, source: Path | None = None
    ) -> Config:
        base = Path(root).resolve()
        problems: list[str] = []
        _reject_unknown(data, _TOP_KEYS, "", problems)

        prefixes = _prefixes(data.get("prefix"), problems)
        ids = _ids(data.get("ids"), problems)
        heading_word = _heading_word(data.get("headings"), problems)
        ref_scheme = _string(data, "ref_scheme", "id", problems)
        markers = _markers(data.get("markers"), problems)
        ledger = _ledger(data.get("ledger"), problems)
        limits = _limits(data.get("limits"), problems)
        per_role = _by_role(data.get("limits"), problems)
        rules = _rules(data.get("rules"), problems)
        paths = _paths(data.get("files"), base, problems)
        refs = _refs(data.get("refs"), ref_scheme, paths, problems)
        extras = tuple(
            base / name for name in _string_list(data.get("id_sources"), "id_sources", problems)
        )
        reserved = tuple(
            dict.fromkeys(_string_list(data.get("reserved_ids"), "reserved_ids", problems))
        )
        priority = tuple(_string_list(data.get("priority"), "priority", problems))
        budgets = _budgets(data.get("budgets"), base, problems)
        tool_characters = _tool_budget(data.get("tools"), problems)
        grammars = _grammars(data.get("grammar"), problems)
        non_goals = _scope(data.get("non_goals"), problems)
        upstream = _upstream(data.get("report"), problems)
        held = _held(data.get("claims"), problems)

        schema = None
        if not problems:
            try:
                schema = Schema(
                    prefixes=prefixes,
                    **ids,
                    heading_word=heading_word,
                    ref_scheme=ref_scheme,
                    **markers,
                    **ledger,
                    **limits,
                    # Where each of those numbers was written, so a refusal over one names
                    # the line somebody reviews rather than only the number (RK1067).
                    origins=_origins(source, _scalars(data.get("limits"))),  # RK1067
                )
            except ValueError as error:  # a valid TOML file can still be a wrong format
                problems.append(str(error))
        if schema is not None:
            _check_priority(schema, priority, problems)
            _check_reserved(schema, reserved, problems)
        if problems:
            raise ConfigError(tuple(problems), source)

        assert schema is not None
        return cls(
            root=base,
            schema=schema,
            paths=paths,
            extra_id_sources=extras,
            reserved=reserved,
            priority=priority,
            budgets=budgets,
            tool_characters=tool_characters,
            grammars=grammars,
            limits=per_role,
            rules=rules,
            refs=refs,
            non_goals=non_goals,
            upstream=upstream,
            held=held,
            source=source,
        )

    # -- using it ----------------------------------------------------------

    def has(self, role: str) -> bool:
        return role in self.paths

    def path(self, role: str) -> Path:
        try:
            return self.paths[role]
        except KeyError:
            raise KeyError(
                f"this project declares no {role!r} file (has: "
                f"{', '.join(sorted(self.paths)) or 'none'})"
            ) from None

    def schema_for(self, role: str) -> Schema:
        """The changelog is the same format in its ledger configuration, not another.

        The deferred store (RK96) is the third such configuration and the same claim: one
        format, one marker set per file, and the file a line sits in is what states its
        status — never a second grammar.

        Plus whatever `[limits.<role>]` says (RK50) — the same format again, held to this
        file's own numbers, because a ledger of history and a roadmap line are refused at
        opposite ends of the work.

        The shape comes from a **declaration** since RK1064: the grammar this project wrote
        for the role, or the one the tool ships for it, applied by `Schema.under` either
        way. `as_ledger` and `as_deferred` are still the names those two grammars go by and
        are what every other caller reaches for; what changed is that neither is where the
        shape is stated, so a project overriding one is not overriding a method.
        """
        declared = self.grammars.get(role) or DEFAULT_GRAMMARS.get(role)
        schema = self.schema.under(declared) if declared else self.schema
        own: dict[str, object] = {**self.limits.get(role, {}), **self.rules.get(role, {})}
        if role in self.limits:
            # The role's own citations layered over the shared ones (RK1067), so a `why`
            # refused in the changelog names `[limits.changelog].why` and not the number
            # the roadmap is held to — which is the whole reason RK50 exists, reaching the
            # author at the moment they are standing over one of the two.
            own["origins"] = tuple(
                {**dict(schema.origins), **dict(_origins(self.source, self.limits[role], role))}
                .items()
            )
        # The namespace this role's addresses live in (RK340), carried on the schema for the
        # reason every other per-role difference is: the file travels with the rules it is
        # read under, so nothing downstream has to be handed a role beside a document.
        if role in self.refs:
            own["ref_prefix"] = self.refs[role]
        return replace(schema, **own) if own else schema

    def document(self, role: str) -> Document:
        """Load a governed file under the right schema — the one seam every command uses.

        The project travels with the file, which is what lets a save re-derive the blocks
        projected from it (RK188): a document that arrived any other way has no project and
        writes exactly itself.

        `Document` is reached here and not at module level (RK261). This module is imported by
        every command in the package, and the guard imports it to answer *where* a write was
        going — it never opens the file, and paid 9 ms for the model that would. Measured, it is
        not a cost moved: 22 of the 37 modules import `document` directly, `cli.py` among them,
        so the commands that load a document already had it before this line runs.
        """
        from roadkeep.kernel.document import Document  # noqa: PLC0415 - RK261

        return replace(
            Document.load(self.path(role), self.schema_for(role)), config=self
        )

    def relative(self, path: Path) -> str:
        """A path as the project spells it — output has to be machine-independent."""
        try:
            return Path(path).resolve().relative_to(self.root).as_posix()
        except ValueError:
            return Path(path).as_posix()

    def missing(self) -> tuple[str, ...]:
        """Declared roles with no file on disk — what `init` creates and `lint` reports."""
        return tuple(role for role, path in self.paths.items() if not path.exists())

    def id_sources(self) -> tuple[Path, ...]:
        """Every file that may carry an id, governed or not, in declaration order."""
        seen: dict[Path, None] = {}
        for role in ROLES:
            if role in self.paths:
                seen.setdefault(self.paths[role])
        for extra in self.extra_id_sources:
            seen.setdefault(extra)
        return tuple(seen)


def find_config(start: str | Path = ".") -> Path | None:
    """The nearest `roadkeep.toml`, or a `pyproject.toml` that configures roadkeep."""
    here = Path(start).resolve()
    for directory in (here, *here.parents):
        candidate = directory / CONFIG_NAME
        if candidate.is_file():
            return candidate
        pyproject = directory / PYPROJECT
        if pyproject.is_file() and _declares_roadkeep(pyproject):
            return pyproject
    return None


def _declares_roadkeep(path: Path) -> bool:
    """Whether this `pyproject.toml` configures roadkeep — a probe, and it may not refuse.

    The mark is taken off **here and only here** (RK1030), because this decides whether a
    file is the project's config at all: a marked `pyproject.toml` parsed as-is is a
    `TOMLDecodeError`, which this swallows, so discovery walked past a file that declares
    `[tool.roadkeep]` and every verb then ran on defaults — the encoding defect turning into
    silence rather than a refusal, which is the one outcome worse than the refusal.

    Found here, refused in :meth:`Config.load`, which reads the bytes as they are and says
    what the mark is. The strip is a question about *which file* and never about its content.
    """
    try:
        raw = path.read_bytes()
    except OSError:
        return False
    try:
        data = tomllib.loads(raw.removeprefix(_BOM).decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return False
    return "roadkeep" in data.get("tool", {})


# -- reading one key at a time, collecting what is wrong -------------------


def _reject_unknown(
    data: Mapping[str, object], allowed: frozenset[str], where: str, problems: list[str]
) -> None:
    for key in data:
        if key not in allowed:
            problems.append(
                f"unknown key '{where}{key}' (allowed: "
                f"{', '.join(where + name for name in sorted(allowed))})"
            )


def _string(
    data: Mapping[str, object], key: str, default: str, problems: list[str]
) -> str:
    value = data.get(key, default)
    if not isinstance(value, str):
        problems.append(f"{key} must be a string, got {type(value).__name__}")
        return default
    return value


def _prefixes(raw: object, problems: list[str]) -> tuple[str, ...]:
    """`prefix` — one family, or the list a backlog numbered by track needs (RK74).

    A string stays a string in the file, because three of the four live corpora number one
    family and `prefix = ["RK"]` would be a list nobody asked for. A list is read in
    declaration order: the first is what `add` mints under when no family is named, and
    the order is the author's, so a message that reprints it prints their list back.
    """
    if raw is None:
        return ("RK",)
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, list) and all(isinstance(item, str) for item in raw):
        if not raw:
            problems.append("prefix must name at least one family")
            return ("RK",)
        return tuple(raw)
    problems.append(
        "prefix must be a string, or a list of strings for a backlog that numbers "
        "by track"
    )
    return ("RK",)


def _ids(raw: object, problems: list[str]) -> dict[str, object]:
    """`[ids]` — the width the number is padded to, and whether a sub-letter is legal (RK106).

    Both default to the shape every project had before this table existed, so a config that
    declares nothing reads exactly as it did. Two live corpora declare one: Dumont pads `D01`
    through `D09` on every line, and Turing carries `T24b`, `T221a` and `T227a` from tasks
    split after their numbers were cited in commits and issues.

    What is being declared is a *spelling*, never a scheme — the non-goal is contiguity,
    reuse and ordering, which are properties of real backlogs, and a project stating the
    width it already writes is the opposite of a scheme imposed on it (L6).
    """
    default: dict[str, object] = {"id_pad": 1, "id_suffix": False}
    if raw is None:
        return default
    if not isinstance(raw, Mapping):
        problems.append("ids must be a table with 'pad' and 'suffix'")
        return default
    _reject_unknown(raw, _IDS_KEYS, "ids.", problems)
    pad = raw.get("pad", 1)
    if not isinstance(pad, int) or isinstance(pad, bool) or pad < 1:
        problems.append(
            "ids.pad must be a positive integer: it is the width the number is "
            "zero-filled to, and 1 is an unpadded id"
        )
        pad = 1
    suffix = raw.get("suffix", False)
    if not isinstance(suffix, bool):
        problems.append("ids.suffix must be true or false")
        suffix = False
    return {"id_pad": pad, "id_suffix": suffix}


def _heading_word(raw: object, problems: list[str]) -> str:
    """`[headings] word` — what this project files work under (RK75).

    Defaults to `Block`, so a project that never declares it is unchanged. Declared by the
    three of four adopting corpora that chose otherwise: Dumont files under `## Track A`,
    cursarei under `## Fase 0`, and each was getting a finding per line for its own word.
    """
    if raw is None:
        return DEFAULT_HEADING_WORD
    if not isinstance(raw, Mapping):
        problems.append("headings must be a table with 'word'")
        return DEFAULT_HEADING_WORD
    _reject_unknown(raw, _HEADING_KEYS, "headings.", problems)
    word = raw.get("word", DEFAULT_HEADING_WORD)
    if not isinstance(word, str):
        problems.append("headings.word must be a string")
        return DEFAULT_HEADING_WORD
    return word


def _markers(raw: object, problems: list[str]) -> dict[str, object]:
    """The `[markers]` table as :class:`Schema` keywords — the four the format varies by."""
    default: dict[str, object] = {
        "markers": OPEN_MARKERS,
        "shipped_marker": SHIPPED,
        "retired_marker": RETIRED,
        "deferred_marker": DEFERRED,
        "undesigned": UNDESIGNED,
    }
    if raw is None:
        return default
    if not isinstance(raw, Mapping):
        problems.append(
            "markers must be a table with 'open', 'shipped', 'retired' and 'deferred'"
        )
        return default
    _reject_unknown(raw, _MARKER_KEYS, "markers.", problems)
    open_markers = tuple(_string_list(raw.get("open"), "markers.open", problems))
    shipped = _one_marker(raw, "shipped", SHIPPED, problems)
    retired = _one_marker(raw, "retired", RETIRED, problems)
    deferred = _one_marker(raw, "deferred", DEFERRED, problems)
    if shipped == retired:
        problems.append(
            "markers.shipped and markers.retired must differ: a ledger where both "
            "read the same cannot say whether the work was done"
        )
    if deferred in (shipped, retired):
        # Checked here rather than in the schema, where the open-set clash is: this pair
        # only meets inside `as_ledger`, so a project that spelled them the same would get
        # its refusal from a method call instead of from the file it typed them in.
        problems.append(
            "markers.deferred must differ from shipped and retired: a paused task that "
            "reads as a departure is the one distinction the state exists to make"
        )
    undesigned = _undesigned(raw, open_markers or OPEN_MARKERS, problems)
    for marker in (*open_markers, shipped, retired, deferred):
        _reject_invisible(marker, problems)
    if "ledger" in raw:
        # Moved to its own table by RK48, and refused rather than aliased: two spellings of
        # one flag are two spellings that can disagree, and a config error that names its
        # replacement costs one edit against a setting that silently stops being read.
        problems.append(
            "markers.ledger moved to [ledger] marker (RK48): the ledger's shape is one "
            "table, since [ledger] symptom cannot live under markers"
        )
    return {
        "markers": open_markers or OPEN_MARKERS,
        "shipped_marker": shipped,
        "retired_marker": retired,
        "deferred_marker": deferred,
        "undesigned": undesigned,
    }


def _ledger(raw: object, problems: list[str]) -> dict[str, object]:
    """Which slots the ledger's own lines carry — the marker (RK43) and the symptom (RK48).

    Both default to *present*, so a project that declares nothing keeps the format this
    repository's own ledger is written in, and a ledger written before the tool declares
    the two absences it already has.
    """
    default = {"ledger_marker": True, "ledger_symptom": True}
    if raw is None:
        return default
    if not isinstance(raw, Mapping):
        problems.append("ledger must be a table with 'marker' and 'symptom'")
        return default
    _reject_unknown(raw, _LEDGER_KEYS, "ledger.", problems)
    return {
        "ledger_marker": _flag(raw, "marker", True, problems),
        "ledger_symptom": _flag(raw, "symptom", True, problems),
    }


def _flag(
    raw: Mapping[str, object], key: str, default: bool, problems: list[str]
) -> bool:
    value = raw.get(key, default)
    if not isinstance(value, bool):
        problems.append(f"ledger.{key} must be true or false")
        return default
    return value


def _undesigned(
    raw: Mapping[str, object], open_markers: tuple[str, ...], problems: list[str]
) -> tuple[str, ...]:
    """Which open markers mean the design is still to be written (RK83).

    Undeclared, it is the built-in list narrowed to what this project actually opens with,
    so a backlog whose marker set never spells 💭 gets an empty one instead of a default
    naming a codepoint it does not use. Declared, every entry has to be an open marker:
    a marker `pick` sets aside and no line can carry is a `--designed` that silently does
    nothing, and this is the file it was typed in.
    """
    if "undesigned" not in raw:
        return tuple(m for m in UNDESIGNED if m in open_markers)
    declared = tuple(_string_list(raw.get("undesigned"), "markers.undesigned", problems))
    stray = [m for m in declared if m not in open_markers]
    if stray:
        problems.append(
            f"markers.undesigned names {' '.join(stray)}, which markers.open does not: "
            "a marker no line may carry is a distinction `pick` can never act on"
        )
    return tuple(m for m in declared if m in open_markers)


def _one_marker(
    raw: Mapping[str, object], key: str, default: str, problems: list[str]
) -> str:
    value = raw.get(key, default)
    if not isinstance(value, str):
        problems.append(f"markers.{key} must be a string")
        return default
    return value


def _reject_invisible(marker: str, problems: list[str]) -> None:
    for char, name in _INVISIBLE.items():
        if char in marker:
            problems.append(
                f"marker {marker.replace(char, '')!r} carries {name}, which is "
                f"invisible in an editor and unequal to the bare character: every "
                f"line would be permanently out of round-trip"
            )


def _check_priority(
    schema: Schema, priority: tuple[str, ...], problems: list[str]
) -> None:
    """A priority entry names a task or a block, and is typed by the same code deps are.

    Refused rather than ignored, like every other key here: an entry `pick` cannot
    resolve is a queue the author believes is in force and is not, and a *silent* one is
    worse than none — the tool would then answer "lowest ready id" while looking like it
    had applied a declaration.
    """
    for token in priority:
        kind = schema.classify_dep(Dep(token))
        if kind is DepKind.TASK and not schema.id_pattern().match(token):
            problems.append(f"priority: not an id of this project: {token!r}")
        elif kind in (DepKind.RANGE, DepKind.EXTERNAL):
            problems.append(
                f"priority: {token!r} is neither an id nor 'Block X': a queue is an "
                f"order over work this backlog holds, so nothing else can be first"
            )


def _check_reserved(
    schema: Schema, reserved: tuple[str, ...], problems: list[str]
) -> None:
    """A reserved id is an id of this project, and refused where it is not (RK1031).

    The whole value of the list is that a token on it is *taken* and a token off it is a
    hazard, and both readings are worthless if the list can hold something the deriver
    cannot compare against a number. A word that is not an id would sit there looking like a
    reservation and reserve nothing — which is the silent state this declaration exists to
    replace, wearing the declaration's own name.
    """
    for token in reserved:
        if not schema.id_pattern().match(token):
            problems.append(
                f"reserved_ids: not an id of this project: {token!r} — a reservation is an "
                f"address the deriver skips, so it has to be one the deriver can read"
            )


def _scalars(raw: object) -> dict[str, object]:
    """The keys a table sets directly, less its sub-tables — `[limits]` without a role's."""
    if not isinstance(raw, Mapping):
        return {}
    return {key: value for key, value in raw.items() if not isinstance(value, Mapping)}


def _limits(raw: object, problems: list[str]) -> dict[str, int]:
    """`[limits]` — the numbers every governed file is held to, before any role says less.

    A sub-table is a role's own (`[limits.changelog]`, RK50) and is read by :func:`_by_role`;
    it is skipped here rather than rejected, so one table can carry both.
    """
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        problems.append("limits must be a table")
        return {}
    scalars = {key: value for key, value in raw.items() if not isinstance(value, Mapping)}
    _reject_unknown(scalars, frozenset(_LIMIT_KEYS), "limits.", problems)
    return _read_limits(scalars, "limits", problems)


def _by_role(raw: object, problems: list[str]) -> dict[str, dict[str, int]]:
    """`[limits.<role>]` — where one file is held to a different number (RK50).

    A roadmap line is refused at insertion, where the refusal costs a retry; a ledger line
    is history, and Turing's reads 938 characters at the median against a `line` of 320.
    Judging the second by the first is a report about work nobody will redo, so the number
    is per role — and per *role*, not per path, because the role is what the format knows.
    """
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, dict[str, int]] = {}
    for role, value in raw.items():
        if not isinstance(value, Mapping):
            continue
        where = f"limits.{role}"
        if role not in ROLES:
            problems.append(
                f"{where}: not a governed role ({', '.join(sorted(ROLES))}): a limit "
                f"for a file the format does not know is a limit nothing reads"
            )
            continue
        _reject_unknown(value, frozenset(_LIMIT_KEYS), f"{where}.", problems)
        found = _read_limits(value, where, problems)
        if found:
            out[role] = found
    return out


def _rules(raw: object, problems: list[str]) -> dict[str, dict[str, bool]]:
    """`[rules.<role>]` — a rule one file is not held to (RK52, RK66).

    Only per role: `why` is one sentence ending in a stop *because* the remainder belongs in
    the section the line points at. That reasoning is a roadmap's. A ledger adopted with
    history in it holds 233 paragraphs that were written before the rule existed, and no edit
    available to their author makes them one sentence — so the project declares the file
    exempt, rather than the tool deciding the rule never mattered there. The write path reads
    the same declaration, so what a project exempts it may also record.

    `ref = false` is the third, and it is the same shape of decision: Shio's process guide
    says a task with no rationale section carries no pointer, and three of its lines are a
    finding for obeying it. Both positions are defensible, which is what makes this
    configuration rather than a default to argue about (L6). It defaults to *required*, so
    nothing changes for a project that never declares it — and only the demand is
    negotiable, never the resolution: a pointer that is written must still point at
    something, which :mod:`roadkeep.linting` checks whatever this says.
    """
    if not isinstance(raw, Mapping):
        if raw is not None:
            problems.append("rules must be a table of per-role tables")
        return {}
    out: dict[str, dict[str, bool]] = {}
    for role, value in raw.items():
        where = f"rules.{role}"
        if role not in ROLES:
            problems.append(
                f"{where}: not a governed role ({', '.join(sorted(ROLES))}): a rule for a "
                f"file the format does not know is a rule nothing reads"
            )
            continue
        if not isinstance(value, Mapping):
            problems.append(f"{where} must be a table of rule = true|false")
            continue
        _reject_unknown(value, frozenset(_RULE_KEYS), f"{where}.", problems)
        if role == "changelog" and "ref" in value:
            # The ledger has no pointer to demand or to waive: `ship` deletes §<id> in the
            # same transaction that writes the entry, so `ref = true` here would put every
            # line that ever ships permanently in violation, and `ref = false` states what
            # `as_ledger` already guarantees. Refused rather than ignored, like every other
            # key in this file.
            problems.append(
                f"{where}.ref: the ledger carries no pointer at all — the rationale "
                f"section is deleted when the task ships, so there is none to require"
            )
            continue
        found = {
            field: _flag(value, key, True, problems)
            for key, field in _RULE_KEYS.items()
            if key in value
        }
        if found:
            out[role] = found
    return out


def _refs(
    raw: object, ref_scheme: str, declared: Mapping[str, Path], problems: list[str]
) -> dict[str, str]:
    """`[refs]` — which namespace a prose role's outline addresses live in (RK340).

    Its own table and not a fourth key under `[rules.<role>]`, which says which rules a file
    is *not held to* and whose every value is a flag: a namespace is a name, and a string
    among booleans is the shape that made `markers.ledger` carry half of two decisions.

    Three refusals, each of them a way for a namespace to fail to be one:

    * **A prose role only.** The roadmap and the ledger hold lines and not headings, so a
      prefix on one addresses nothing — and the deferred store carries the section a pause
      kept, which is the prose role it came from and not a fourth namespace.
    * **Under an outline only.** The id scheme's anchor *is* the id, and ids are already one
      namespace this format refuses to spend twice; prefixing them would put a second address
      on a section whose first one the roadmap derives.
    * **Unique.** Two roles sharing a prefix is the collision this exists to end, one level
      up, and it would be the harder one to see: the addresses would agree and the files
      would not.

    A role a project does not declare is refused too. It reads as configuration nothing
    applies, and the one thing worse than an unresolvable address is a declaration the author
    believes resolved it.
    """
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        problems.append("refs must be a table of role = \"<prefix>\"")
        return {}
    out: dict[str, str] = {}
    for role, value in raw.items():
        where = f"refs.{role}"
        if role not in PROSE_ROLES:
            problems.append(
                f"{where}: not a prose role ({', '.join(PROSE_ROLES)}): only a file that "
                f"declares headings has addresses to put in a namespace"
            )
            continue
        if not isinstance(value, str) or not REF_PREFIX_RE.match(value):
            problems.append(
                f"{where} must be one word of letters and digits starting with a letter: "
                f"it is written in front of an address as <prefix>{REF_SEPARATOR}<x.y>"
            )
            continue
        if ref_scheme != "outline":
            problems.append(
                f"{where}: a namespace is for ref_scheme = \"outline\" — under \"id\" the "
                f"anchor is the task's own id, which is already unique across the project"
            )
            continue
        if role not in declared:
            problems.append(
                f"{where}: this project declares no {role!r} file, so the namespace "
                f"addresses nothing — declare it under [files], or drop this line"
            )
            continue
        taken = next((other for other, one in out.items() if one == value), None)
        if taken is not None:
            problems.append(
                f"{where}: {value!r} is already {taken}'s namespace, and two roles sharing "
                f"one is the collision a namespace exists to end"
            )
            continue
        out[role] = value
    return out


def _read_limits(raw: Mapping[str, object], where: str, problems: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for key, field_name in _LIMIT_KEYS.items():
        if key not in raw:
            continue
        value = raw[key]
        if not isinstance(value, int) or isinstance(value, bool):
            problems.append(f"{where}.{key} must be an integer")
            continue
        out[field_name] = value
    return out


def _scope(raw: object, problems: list[str]) -> Scope | None:
    """`[non_goals]` — declared at all means governed, and each number may be left default.

    An empty table is legal and is the shortest way to opt in: what a project is declaring
    is *that* the list is a schema, and the two limits are what it may then also tune (L6).
    """
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        problems.append("non_goals must be a table of lead = …, why = …")
        return None
    _reject_unknown(raw, _SCOPE_KEYS, "non_goals.", problems)
    numbers: dict[str, int] = {}
    for key in sorted(_SCOPE_KEYS):
        if key not in raw:
            continue
        value = raw[key]
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            problems.append(f"non_goals.{key} must be a positive integer")
            continue
        numbers[key] = value
    return Scope(**numbers)


#: `[report]` — one key, and refused like every other. A table with room for a token or a
#: URL is a table somebody puts a token in; the only thing declarable here is *where* a
#: defect in this tool would be filed, and filing it is still a command a person types.
_REPORT_KEYS = frozenset({"upstream"})

#: `owner/repo`, which is what `gh --repo` takes. Checked because the alternative to a
#: shape here is a shape guessed by whatever the operator pipes the capture into.
_UPSTREAM = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")


def _held(raw: object, problems: list[str]) -> int:
    """`[claims] held` — minutes, bounded at both ends (RK151).

    The bound is the design and not a guard rail. Below a minute a claim expires before the
    worker has read the brief it came with; above :data:`CLAIM_HELD_MAX` an abandoned claim
    outlives the session that abandoned it, which is the lock this mechanism exists not to be.
    Between them the number is a judgement about this backlog, which is why it is declarable
    at all — and the refusal names the unit, because the one way to be badly wrong here is to
    write seconds in a key that reads minutes.
    """
    if raw is None:
        return CLAIM_HELD
    if not isinstance(raw, Mapping):
        problems.append("claims must be a table of held = <minutes>")
        return CLAIM_HELD
    _reject_unknown(raw, _CLAIMS_KEYS, "claims.", problems)
    value = raw.get("held")
    if value is None:
        return CLAIM_HELD
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= CLAIM_HELD_MAX:
        problems.append(
            f"claims.held must be minutes, from 1 to {CLAIM_HELD_MAX}: a claim shorter than "
            f"that expires before the brief is read, and a longer one is the lock an expiry "
            f"exists not to be"
        )
        return CLAIM_HELD
    return value


def _upstream(raw: object, problems: list[str]) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        problems.append("report must be a table of upstream = 'owner/repo'")
        return None
    _reject_unknown(raw, _REPORT_KEYS, "report.", problems)
    value = raw.get("upstream")
    if value is None:
        return None
    if not isinstance(value, str) or not _UPSTREAM.match(value):
        problems.append("report.upstream must be 'owner/repo'")
        return None
    return value


def _budgets(raw: object, base: Path, problems: list[str]) -> tuple[Budget, ...]:
    """`[budgets]` — a path to what it may cost. Refused, like every other key here."""
    if raw is None:
        return ()
    if not isinstance(raw, Mapping):
        problems.append("budgets must be a table of path = { lines = …, bytes = … }")
        return ()
    out: list[Budget] = []
    for name, value in raw.items():
        where = f"budgets.'{name}'"
        if not isinstance(value, Mapping):
            problems.append(f"{where} must be a table with 'lines' and/or 'bytes'")
            continue
        _reject_unknown(value, _BUDGET_KEYS, f"{where}.", problems)
        if Path(name).is_absolute():
            problems.append(
                f"{where} must be relative to the project root: an absolute path is "
                f"checked in and then wrong on every other machine"
            )
            continue
        if not _BUDGET_KEYS & set(value):
            # Declared *nothing*, which is a different mistake from declaring a number
            # this rejected: reporting both would send the reader to fix the wrong line.
            problems.append(
                f"{where} declares neither lines nor bytes: an entry that holds nobody "
                f"to anything reads as a budget and is the arrangement being replaced"
            )
            continue
        numbers = _positive(value, where, problems)
        if numbers:
            out.append(Budget(path=(base / name).resolve(), **numbers))
    return tuple(out)


def _positions(source: Path | None) -> dict[tuple[str, str], int]:
    """Which line of the config each `table.key` is written on (RK1067).

    Read off the text and never through the parse, for :func:`_declared_at`'s reason:
    `tomllib` keeps no positions, and a refusal that cited `roadkeep.toml:0` would be the
    one address in this tool that opens nothing. Coarse on purpose — the first assignment
    of a key under a header — because what a reader needs is the line to go and look at,
    and a second parser written to be exact about it is a second parser to keep right.
    """
    if source is None:
        return {}
    try:
        text = source.read_text(encoding="utf-8")
    except OSError:
        return {}
    found: dict[tuple[str, str], int] = {}
    table = ""
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        header = re.match(r"^\[([^\]]+)\]$", stripped)
        if header:
            table = header.group(1)
            continue
        key = re.match(r'^([A-Za-z_][A-Za-z0-9_]*|"[^"]+")\s*=', stripped)
        if key and (table, key.group(1)) not in found:
            found[(table, key.group(1))] = lineno
    return found


def _origins(
    source: Path | None, declared: Mapping[str, object], role: str = ""
) -> tuple[tuple[str, str], ...]:
    """Where each limit this project set was declared, as the clause a refusal prints.

    Only the keys the project actually wrote: a limit it never declared has no line, and
    :meth:`Schema.source_of` says *this tool's default* rather than inventing a citation —
    which of the two numbers a refusal is about being exactly the fact the author needs.
    """
    if source is None:
        return ()
    where = source.name
    table = f"limits.{role}" if role else "limits"
    at = _positions(source)
    out: list[tuple[str, str]] = []
    for key, attribute in _LIMIT_KEYS.items():
        # Either spelling, because the two callers hold different ones: the top-level table
        # arrives as it was written (`why`) and a role's arrives already translated to the
        # field it sets (`why_max`), and a citation that only knew one would silently drop
        # every per-role number — the ones RK50 exists for and the ones most worth citing.
        if key not in declared and attribute not in declared:
            continue
        lineno = at.get((table, key))
        address = f"{where}:{lineno}" if lineno else where
        out.append((attribute, f"{address} [{table}].{key}"))
    return tuple(out)


def _grammars(raw: object, problems: list[str]) -> dict[str, Grammar]:
    """`[grammar.<role>]` — one role's shape, refused key by key like every other table.

    Every name is checked against a closed set and never taken (RK1064): a `drop` naming a
    field this format does not have is a slot the author believes is gone, which is the
    same failure an unignored `symptom_max` typo is one layer down. The role itself is
    checked too — a grammar for a file `[files]` does not declare is a shape nothing reads.
    """
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        problems.append("grammar must be a table of role = { extends = …, drop = […] }")
        return {}
    out: dict[str, Grammar] = {}
    for role, value in raw.items():
        where = f"grammar.{role}"
        if role not in ROLES:
            problems.append(f"{where} is not a role ({', '.join(ROLES)})")
            continue
        if not isinstance(value, Mapping):
            problems.append(f"{where} must be a table with {', '.join(sorted(_GRAMMAR_KEYS))}")
            continue
        _reject_unknown(value, _GRAMMAR_KEYS, f"{where}.", problems)
        extends = value.get("extends", "roadmap")
        if not isinstance(extends, str) or extends not in ROLES:
            problems.append(f"{where}.extends is not a role ({', '.join(ROLES)})")
            continue
        markers = _named(value.get("markers"), MARKER_NAMES, f"{where}.markers", problems)
        drop = _named(value.get("drop"), DROPPABLE, f"{where}.drop", problems)
        # The states a role carries are the tool's own and not a project's to declare, so
        # what a shipped grammar said stays said: a project reshapes the line under it.
        states = DEFAULT_GRAMMARS.get(role, Grammar()).states
        out[role] = Grammar(extends=extends, markers=markers, drop=drop, states=states)
    return out


def _named(
    raw: object, allowed: Mapping[str, str], where: str, problems: list[str]
) -> tuple[str, ...]:
    """A list of names from a closed set, or a problem naming what the set holds."""
    if raw is None:
        return ()
    names = _string_list(raw, where, problems)
    unknown = [name for name in names if name not in allowed]
    if unknown:
        problems.append(
            f"{where} names {', '.join(unknown)}, which is not one of "
            f"{', '.join(sorted(allowed))}"
        )
        return ()
    return tuple(dict.fromkeys(names))


def _tool_budget(raw: object, problems: list[str]) -> int | None:
    """`[tools] characters` — what one served tool may cost (RK1059).

    Refused like every other key here rather than defaulted: a ceiling this tool chose for
    somebody's surface would be a number nobody looked at, which is the state RK464 named
    and declined to fix by guessing.
    """
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        problems.append("tools must be a table of { characters = … }")
        return None
    _reject_unknown(raw, _TOOLS_KEYS, "tools.", problems)
    if "characters" not in raw:
        # The same mistake `[budgets]` names: an entry that holds nobody to anything reads
        # as a budget and is exactly the arrangement being replaced.
        problems.append(
            "tools declares no characters: a table that holds nobody to anything reads "
            "as a budget and is the arrangement being replaced"
        )
        return None
    number = raw["characters"]
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        problems.append("tools.characters must be a positive integer")
        return None
    return number


def _positive(
    value: Mapping[str, object], where: str, problems: list[str]
) -> dict[str, int]:
    """The budget's two numbers, each one a positive integer or a problem."""
    out: dict[str, int] = {}
    for key in sorted(_BUDGET_KEYS):
        if key not in value:
            continue
        number = value[key]
        if not isinstance(number, int) or isinstance(number, bool) or number < 1:
            problems.append(f"{where}.{key} must be a positive integer")
            continue
        out[key] = number
    return out


def _paths(raw: object, base: Path, problems: list[str]) -> dict[str, Path]:
    if raw is None:
        return {role: base / rel for role, rel in DEFAULT_PATHS.items()}
    if not isinstance(raw, Mapping):
        problems.append("files must be a table of role = path")
        return {}
    _reject_unknown(raw, frozenset(ROLES), "files.", problems)
    out: dict[str, Path] = {}
    for role in ROLES:
        if role not in raw:
            continue
        value = raw[role]
        if not isinstance(value, str):
            problems.append(f"files.{role} must be a string path")
            continue
        candidate = Path(value)
        if candidate.is_absolute():
            problems.append(
                f"files.{role} must be relative to the project root: an absolute "
                f"path is checked in and then wrong on every other machine"
            )
            continue
        out[role] = (base / candidate).resolve()
    return out


def _string_list(raw: object, where: str, problems: list[str]) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        problems.append(f"{where} must be a list of strings")
        return []
    return list(raw)
