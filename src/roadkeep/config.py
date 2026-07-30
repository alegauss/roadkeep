"""`roadkeep.toml` — the format's variability, declared per project (RK3, L6).

Three real projects, one format: Shio numbers `SH` and has no strategy file, Turing
numbers `T` and has one, Cursarei keeps its roadmap under `docs/roadmap/`. The moment
any of that is hardcoded the tool serves exactly one repository, so everything that
differs is a key here and everything that does not is in :mod:`roadkeep.schema`.

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

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from roadkeep.document import Document
from roadkeep.schema import OPEN_MARKERS, RETIRED, SHIPPED, Dep, DepKind, Schema

CONFIG_NAME = "roadkeep.toml"
PYPROJECT = "pyproject.toml"

#: The four governed files. A project declares the ones it has; the rest are absent,
#: not empty — `strategy` missing means Shio, not a Shio with an empty strategy.
ROLES = ("roadmap", "changelog", "improvements", "strategy")

DEFAULT_PATHS: Mapping[str, str] = {
    "roadmap": "docs/ROADMAP.md",
    "changelog": "docs/CHANGELOG.md",
    "improvements": "docs/IMPROVEMENTS.md",
}

_TOP_KEYS = frozenset(
    {
        "prefix",
        "ref_scheme",
        "files",
        "limits",
        "markers",
        "id_sources",
        "priority",
        "budgets",
        "ledger",
    }
)
_BUDGET_KEYS = frozenset({"lines", "bytes"})
#: Which slots the ledger's lines carry (RK43, RK48). Its own table because the shape of a
#: file is one decision with two parts, and `markers.ledger` put half of it under a heading
#: that cannot name the other half: a symptom is not a marker.
_LEDGER_KEYS = frozenset({"marker", "symptom"})
_LIMIT_KEYS = {
    "symptom": "symptom_max",
    "why": "why_max",
    "line": "line_max",
    # A section is prose, so its budget is words and its shape is a width (RK9).
    "section": "section_max",
    "prose": "prose_width",
}
_MARKER_KEYS = frozenset({"open", "shipped", "retired"})
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


class ConfigError(ValueError):
    """Every problem with the file, not the first one found."""

    def __init__(self, problems: tuple[str, ...], path: Path | None = None) -> None:
        self.problems = tuple(problems)
        self.path = path
        where = f"{path}: " if path else ""
        super().__init__(where + "; ".join(self.problems))


@dataclass(frozen=True, slots=True)
class Config:
    """Where the governed files are, and which format they are written in."""

    root: Path
    schema: Schema = field(default_factory=Schema)
    paths: Mapping[str, Path] = field(default_factory=dict)
    #: Files to scan for ids beyond the governed four (RK4). This repository keeps
    #: task ids in `agents.md`, and an id the scan misses is an id that gets reused.
    extra_id_sources: tuple[Path, ...] = ()
    #: What jumps the queue, in order: an id or a `Block X`, and nothing else (RK11).
    #: *Declared*, because the alternative is a "## Priority queue" section written in
    #: prose — which Shio has, and which a tool that reads it would be interpreting
    #: rather than validating (L4).
    priority: tuple[str, ...] = ()
    #: Always-loaded files and what each may cost (RK30). Not a governed role: the tool
    #: writes none of these, it only refuses to let one grow unwatched.
    budgets: tuple[Budget, ...] = ()
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
            document = tomllib.load(handle)
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

        prefix = _string(data, "prefix", "RK", problems)
        ref_scheme = _string(data, "ref_scheme", "id", problems)
        markers = _markers(data.get("markers"), problems)
        ledger = _ledger(data.get("ledger"), problems)
        limits = _limits(data.get("limits"), problems)
        paths = _paths(data.get("files"), base, problems)
        extras = tuple(
            base / name for name in _string_list(data.get("id_sources"), "id_sources", problems)
        )
        priority = tuple(_string_list(data.get("priority"), "priority", problems))
        budgets = _budgets(data.get("budgets"), base, problems)

        schema = None
        if not problems:
            try:
                schema = Schema(
                    prefix=prefix,
                    ref_scheme=ref_scheme,
                    **markers,
                    **ledger,
                    **limits,
                )
            except ValueError as error:  # a valid TOML file can still be a wrong format
                problems.append(str(error))
        if schema is not None:
            _check_priority(schema, priority, problems)
        if problems:
            raise ConfigError(tuple(problems), source)

        assert schema is not None
        return cls(
            root=base,
            schema=schema,
            paths=paths,
            extra_id_sources=extras,
            priority=priority,
            budgets=budgets,
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
        """The changelog is the same format in its ledger configuration, not another."""
        return self.schema.as_ledger() if role == "changelog" else self.schema

    def document(self, role: str) -> Document:
        """Load a governed file under the right schema — the one seam every command uses."""
        return Document.load(self.path(role), self.schema_for(role))

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
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
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


def _markers(raw: object, problems: list[str]) -> dict[str, object]:
    """The `[markers]` table as :class:`Schema` keywords — the four the format varies by."""
    default: dict[str, object] = {
        "markers": OPEN_MARKERS,
        "shipped_marker": SHIPPED,
        "retired_marker": RETIRED,
    }
    if raw is None:
        return default
    if not isinstance(raw, Mapping):
        problems.append("markers must be a table with 'open', 'shipped' and 'retired'")
        return default
    _reject_unknown(raw, _MARKER_KEYS, "markers.", problems)
    open_markers = tuple(_string_list(raw.get("open"), "markers.open", problems))
    shipped = _one_marker(raw, "shipped", SHIPPED, problems)
    retired = _one_marker(raw, "retired", RETIRED, problems)
    if shipped == retired:
        problems.append(
            "markers.shipped and markers.retired must differ: a ledger where both "
            "read the same cannot say whether the work was done"
        )
    for marker in (*open_markers, shipped, retired):
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


def _limits(raw: object, problems: list[str]) -> dict[str, int]:
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        problems.append("limits must be a table")
        return {}
    _reject_unknown(raw, frozenset(_LIMIT_KEYS), "limits.", problems)
    out: dict[str, int] = {}
    for key, field_name in _LIMIT_KEYS.items():
        if key not in raw:
            continue
        value = raw[key]
        if not isinstance(value, int) or isinstance(value, bool):
            problems.append(f"limits.{key} must be an integer")
            continue
        out[field_name] = value
    return out


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
