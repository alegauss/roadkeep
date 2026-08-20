"""What `roadkeep.toml` may declare, answered by the package that refuses the rest (RK1270).

The frozensets in :mod:`roadkeep.config` — `_TOP_KEYS`, `_LIMIT_KEYS`, `_MARKER_KEYS` and
twelve more — are the complete statement of what that file may say, and their only reader was
`_reject_unknown`. That is enough to refuse a typo and not enough to answer the question asked
*before* anything is typed: what may go here, and what does it mean.

Every consumer needing that answer had written it again. The scaffold `init` emits knows the
tables, `declare` knows `[files]`, and a completion list in an editor would know all of them —
each copy L6 broken from a different side, the shape of a project's own declaration decided
somewhere other than the package that reads it.

**Nothing here is a second statement of the shape.** The keys are read off those frozensets;
the sentence is harvested from the `#:` comment already above each one; the default is read
off a :meth:`~roadkeep.config.Config.default` project, which is the same code the parser runs;
and whether *this* project declared a key is read back off the file it wrote. The one thing
written here is :data:`WHERE` — where each key's value lands — and `tests/test_describing.py`
holds it total against those sets, so a key added tomorrow is a red rather than a silence.

What this is not is a schema for somebody else's validator. What is published is what **this
build** accepts, which is the distinction `ConfigError`'s skew clause exists for: a key nothing
declares is a typo, a key this build predates is an upgrade, and the file cannot tell them
apart. So the answer names the version that gave it, and a reader can conclude the second.
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from roadkeep.config import (
    CLAIM_HELD,
    PROSE_ROLES,
    ROLES,
    Config,
    Scope,
    _BUDGET_KEYS,
    _CLAIMS_KEYS,
    _GRAMMAR_KEYS,
    _HEADING_KEYS,
    _IDS_KEYS,
    _INSTALL_KEYS,
    _LEDGER_KEYS,
    _LIMIT_KEYS,
    _MARKER_KEYS,
    _REPORT_KEYS,
    _READS_KEYS,
    _RULE_KEYS,
    _SCOPE_KEYS,
    _TOOLS_KEYS,
    _TOP_KEYS,
)

__all__ = ["Key", "Shape", "TABLES", "WHERE", "notes", "shape"]

#: Every table this file may carry, and the closed set of names it accepts. The **prefix**
#: `_reject_unknown` is called with is the key, `""` being the top level, so a reader here and
#: the refusal one module over cannot come to disagree about what a table is called — and
#: `tests/test_describing.py` reads those call sites out of the source and holds this total
#: against them. A `<role>` or a `<path>` in a name is a table declared once per something the
#: project names, which is a fact about the address and not about the keys under it.
TABLES: Mapping[str, frozenset[str]] = {
    "": _TOP_KEYS,
    "files": frozenset(ROLES),
    # Keyed by role like `[files]`, and refused by `_refs` rather than by `_reject_unknown`:
    # it is a prose role only, under an outline only, and unique — three refusals a name set
    # cannot make. The names it accepts are still the roles, which is what this answers.
    "refs": frozenset(PROSE_ROLES),
    "ids": _IDS_KEYS,
    "headings": _HEADING_KEYS,
    "install": _INSTALL_KEYS,
    "markers": _MARKER_KEYS,
    "ledger": _LEDGER_KEYS,
    "limits": frozenset(_LIMIT_KEYS),
    "rules.<role>": frozenset(_RULE_KEYS),
    "non_goals": _SCOPE_KEYS,
    "criteria": _SCOPE_KEYS,
    "claims": _CLAIMS_KEYS,
    "report": _REPORT_KEYS,
    "budgets.<path>": _BUDGET_KEYS,
    "grammar.<role>": _GRAMMAR_KEYS,
    "tools": _TOOLS_KEYS,
    "reads": _READS_KEYS,
}


def _is_table(name: str) -> bool:
    """Whether a top-level key opens a table rather than carrying a value.

    Asked of :data:`TABLES` and never listed a second time: a table a project declares once
    per role or per path is spelled with the placeholder there, so `budgets` is found by the
    prefix and `limits` by the name — one reading, and a table added above is covered by it.
    """
    return any(one == name or one.startswith(f"{name}.") for one in TABLES)


def _limit(key: str) -> object:
    return getattr(Config.default().schema, _LIMIT_KEYS[key])


def _rule(key: str) -> object:
    return getattr(Config.default().schema, _RULE_KEYS[key])


#: How each key's value is reached on a project that declared nothing — the one thing this
#: module states rather than derives, and the reason it is a lookup and not a sentence. Every
#: entry is a *call into the code the parser runs*, so a default changed in `Schema` or in
#: `config` changes what this prints without anybody editing it; `None` is a key with no
#: default at all, which is a different fact from a default of `false` and is said as such.
#:
#: Held total against :data:`TABLES` by a test, for `composing.SITES`' reason: a key nobody
#: accounted for reads exactly like a key that has no default.
WHERE: Mapping[tuple[str, str], object] = {
    # The top level. Every table name among them is a table and carries no value of its own,
    # which is why they answer `None` here and are listed under their own name below.
    ("", "prefix"): lambda: Config.default().schema.prefixes[0],
    ("", "ref_scheme"): lambda: Config.default().schema.ref_scheme,
    ("", "id_sources"): lambda: (),
    ("", "reserved_ids"): lambda: (),
    ("", "priority"): lambda: (),
    ("", "blocks"): lambda: (),
    **{("", name): None for name in _TOP_KEYS if _is_table(name)},
    # `[files]`, whose keys are the roles: no default beyond the three a scaffold writes, and
    # `Config.default()` declares none at all — an absent role is absent and not empty.
    **{("files", role): None for role in ROLES},
    **{("refs", role): None for role in PROSE_ROLES},
    ("ids", "pad"): lambda: Config.default().schema.id_pad,
    ("ids", "suffix"): lambda: Config.default().schema.id_suffix,
    ("headings", "word"): lambda: Config.default().schema.heading_word,
    ("headings", "permanent"): lambda: False,
    ("install", "pinned"): lambda: False,
    ("install", "enforced"): lambda: False,
    ("markers", "open"): lambda: Config.default().schema.markers,
    ("markers", "shipped"): lambda: Config.default().schema.shipped_marker,
    ("markers", "retired"): lambda: Config.default().schema.retired_marker,
    ("markers", "deferred"): lambda: Config.default().schema.deferred_marker,
    ("markers", "undesigned"): lambda: Config.default().schema.undesigned,
    ("ledger", "marker"): lambda: Config.default().schema.ledger_marker,
    ("ledger", "symptom"): lambda: Config.default().schema.ledger_symptom,
    **{("limits", key): (lambda k=key: _limit(k)) for key in _LIMIT_KEYS},
    **{("rules.<role>", key): (lambda k=key: _rule(k)) for key in _RULE_KEYS},
    ("non_goals", "lead"): lambda: Scope().lead,
    ("non_goals", "why"): lambda: Scope().why,
    ("criteria", "lead"): lambda: Scope().lead,
    ("criteria", "why"): lambda: Scope().why,
    ("claims", "held"): lambda: CLAIM_HELD,
    ("report", "upstream"): None,
    ("budgets.<path>", "lines"): None,
    ("budgets.<path>", "bytes"): None,
    ("grammar.<role>", "extends"): lambda: "roadmap",
    ("grammar.<role>", "markers"): lambda: (),
    ("grammar.<role>", "drop"): lambda: (),
    ("tools", "characters"): None,
    ("tools", "session"): None,
    ("reads", "brief"): None,
}


@dataclass(frozen=True, slots=True)
class Key:
    """One key this file may carry, as a reader outside the package needs it."""

    #: The table it lives under, `""` for the top level. `<role>` and `<path>` stand for the
    #: name the project chooses, which is the address and never one of the keys.
    table: str
    name: str
    #: The Python type of the default, or `""` where there is no default to read one off.
    type: str
    #: What this build uses when nobody declares it, already rendered — or `None`, which says
    #: there is no default rather than that the default is empty.
    default: str | None
    #: Did *this* project declare it, read back off the file the project wrote.
    declared: bool
    #: What it wrote there, rendered the way the default is (RK1278) — `None` where nobody
    #: declared it, which is a different fact from one declared as zero and is said as such.
    #: A table's own row carries none: what a table *is* is the keys under it. `None` too
    #: where **several** addresses declared it (RK1282) — one of them printed as the value is
    #: a number a reader can act on and should not, and :attr:`at` is the fact instead.
    set: str | None = None
    #: How many addresses declared it (RK1282). 0 or 1 for an ordinary table, and above one
    #: where a placeholder table was written per role or per path; which of them applies is
    #: `budget --file`'s and `govern`'s, both of which take the address.
    at: int = 0
    #: The sentence the source already carries above the set this key belongs to, harvested
    #: and never restated. `""` where the source is not readable or carries none.
    note: str = ""

    @property
    def address(self) -> str:
        return f"{self.table}.{self.name}" if self.table else self.name


@dataclass(frozen=True, slots=True)
class Shape:
    """Every key, and the build that answered — which is half of what makes it usable."""

    keys: tuple[Key, ...]
    version: str
    #: The file read back for :attr:`Key.declared`, or `None` on a project with no config.
    source: str | None = None

    def under(self, table: str) -> tuple[Key, ...]:
        return tuple(one for one in self.keys if one.table == table)

    def tables(self) -> tuple[str, ...]:
        """Every table, in declaration order, so a listing groups the way the file does."""
        return tuple(dict.fromkeys(one.table for one in self.keys))


#: A run of `#:` comment lines immediately above a name this module reads. Sphinx's own
#: spelling, which is what the source already uses — so nothing here asks an author to write a
#: second kind of comment for this reader's benefit.
_DOC = re.compile(
    r"((?:^#:.*\n)+)^(?P<name>_?[A-Za-z][A-Za-z0-9_]*)\s*[:=]", re.MULTILINE
)


def notes(source: Path | None = None) -> Mapping[str, str]:
    """The `#:` sentence above each module-level name in `config.py`, by name (RK1270).

    Harvested rather than restated, which is the whole of why the note is worth printing: the
    sentence above `_MARKER_KEYS` is the one an author of that table already wrote, and a
    second copy here would be the one that goes stale the first time somebody edits the real
    one — which is the failure this task is an instance of, one file out.

    Read off the text and not the AST: a `#:` run is a *comment*, so no tree carries it, and
    the alternative is a tokenize pass to find what one regular expression anchored on the
    assignment already answers. Empty where the source cannot be read — a build without it
    answers the shape and not the prose, which is an absence and never an invention.
    """
    from roadkeep import config as module  # noqa: PLC0415 - RK260

    path = source or Path(module.__file__ or "")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    out: dict[str, str] = {}
    for match in _DOC.finditer(text):
        lines = [
            line.removeprefix("#:").strip() for line in match.group(1).splitlines()
        ]
        out[match.group("name")] = " ".join(part for part in lines if part)
    return out


#: Which name's `#:` sentence describes each table. The frozenset itself wherever one exists,
#: because that is where the author wrote it; `_TOP_KEYS` carries none and says so.
_DESCRIBED = {
    "files": "ROLES",
    "ids": "_IDS_KEYS",
    "headings": "_HEADING_KEYS",
    "install": "_INSTALL_KEYS",
    "markers": "_MARKER_KEYS",
    "ledger": "_LEDGER_KEYS",
    "limits": "_LIMIT_KEYS",
    "rules.<role>": "_RULE_KEYS",
    "non_goals": "_SCOPE_KEYS",
    "criteria": "_SCOPE_KEYS",
    "claims": "_CLAIMS_KEYS",
    "report": "_REPORT_KEYS",
    "budgets.<path>": "_BUDGET_KEYS",
    "grammar.<role>": "_GRAMMAR_KEYS",
    "tools": "_TOOLS_KEYS",
    "reads": "_READS_KEYS",
}


#: A sentence's end, where the stop is not inside a parenthesised citation or a version. The
#: harvested prose is this repository's own, so `(RK106).` and `0.1.1` are the two shapes that
#: are not ends, and both are excluded by requiring whitespace after the stop.
_STOP = re.compile(r"(?<=[.!?])\s")


def _opening(note: str) -> str:
    """The first sentence of a harvested run — what a listing prints (RK1270)."""
    parts = _STOP.split(note, maxsplit=1)
    return parts[0].strip()


def _how(one: Key) -> str:
    """What a listing says about a key this project declared, or did not (RK1278, RK1282).

    Three answers and not two, because a placeholder table is declared per address: nothing,
    the value where exactly one address wrote it, and the count where several did. The last
    is the one this exists for — printing one of them looked exactly like a key with one
    value, and `budget --file` and `govern` are the reads that take the address.
    """
    if not one.declared:
        return "—"
    if one.at > 1:
        return f"declared at {one.at} addresses"
    return "declared" if one.set is None else f"declared {one.set}"


def _rendered(value: object) -> str:
    """A default as the file would spell it, so what is printed is what may be typed."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, tuple | list):
        return "[" + ", ".join(_rendered(one) for one in value) + "]"
    return str(value)


def _named(value: object) -> str:
    """The TOML type of a default, named as that format names it and not as Python does."""
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, tuple | list):
        return "array"
    return "table"


def _declared(source: Path | None) -> Mapping[tuple[str, str], tuple[object, ...]]:
    """Every `(table, key)` the project wrote, and **every value it wrote there** (RK1278).

    The file and not the parsed :class:`~roadkeep.config.Config`, and the difference is the
    question: a config carries the *effective* value, where a limit left out and a limit
    declared at the default are the same number and a different fact about the project.

    The value comes with it because the same parse already had it, and printing the default
    beside a key somebody set is two true statements arranged to read as one false one — met
    by the reader hovering the key they are about to change, which is the moment the value
    matters and the default does not.

    A **tuple** and not one value (RK1282). A table spelled with a placeholder is declared once
    per something the project names, so one published address can carry several — this project
    budgets two files — and reporting the last of them looked exactly like a key with one
    value. The count is the fact; which of the several applies is `budget --file`'s and
    `govern`'s, both of which take the address.

    What comes back is TOML's own scalar, string or list, rendered by the same writer the
    default is: resolving it into what the schema makes of it would be this module re-deciding
    what the parser decided, which is the second reading it exists to make unnecessary.
    """
    if source is None:
        return {}
    try:
        raw = tomllib.loads(source.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    if "tool" in raw and "roadkeep" in raw.get("tool", {}):
        raw = raw["tool"]["roadkeep"]
    out: dict[tuple[str, str], list[object]] = {}
    for name, value in raw.items():
        # A table's own row carries no value of its own: what it *is* is the keys under it,
        # and a rendered dict there would be the whole subtree printed as a default.
        out.setdefault(("", name), []).append(None if isinstance(value, Mapping) else value)
        if isinstance(value, Mapping):
            for address, each in _under(name, value):
                out.setdefault(address, []).append(each)
    return {key: tuple(values) for key, values in out.items()}


def _under(
    name: str, value: Mapping[str, object]
) -> tuple[tuple[tuple[str, str], object], ...]:
    """One table's declared keys and their values, descending the level a placeholder adds.

    Pairs and not a mapping (RK1282): under `budgets.<path>` or `limits.<role>` the address is
    one the project chooses, so two of them can write the same published key — and a mapping
    here would keep the last, which is the value that looked like the answer.
    """
    generic = next((one for one in TABLES if one.startswith(f"{name}.")), None)
    under = generic or name
    known = TABLES.get(under, frozenset())
    out: list[tuple[tuple[str, str], object]] = []
    for key, inner in value.items():
        # A sub-table under a name this table has no key for is the **same** table declared
        # once per something the project chose — `[limits.changelog]`, `[budgets."agents.md"]`
        # — so its keys land on the published address rather than on the name it was spelled
        # with, which is not a key and never appears in the shape.
        if isinstance(inner, Mapping) and key not in known:
            out.extend(((under, each), one) for each, one in inner.items())
            continue
        out.append(((under, key), inner))
    return tuple(out)


def shape(config: Config, table: str | None = None) -> Shape:
    """Every key this build accepts, with what this project declared (RK1270).

    ``table`` narrows to one, spelled as :data:`TABLES` spells it — `""` for the top level,
    and `rules.<role>` for a table a project declares once per role. A name nothing declares
    is refused rather than answered empty, that answer being read as evidence.
    """
    from roadkeep import __version__  # noqa: PLC0415 - RK260

    if table is not None and table not in TABLES:
        known = ", ".join(repr(one) for one in TABLES)
        raise KeyError(
            f"no table {table!r} in roadkeep.toml: this build accepts {known} — a name it "
            f"does not is a typo here and never a key this project has yet to declare"
        )
    sentences = notes()
    written = _declared(config.source)
    out: list[Key] = []
    for name, keys in TABLES.items():
        if table is not None and name != table:
            continue
        note = sentences.get(_DESCRIBED.get(name, ""), "")
        for key in sorted(keys):
            reader = WHERE[(name, key)]
            value = None if reader is None else reader()
            # What the project wrote, beside what this build would use (RK1278): the same
            # parse that answers *whether* a key is declared already has *what* — and
            # printing the default beside a key somebody set is two true statements arranged
            # to read as one false one.
            declared = written.get((name, key), ())
            # One value or a count, never one of several (RK1282): a placeholder table is
            # declared per address, so the number is the answer only where there is one.
            only = declared[0] if len(declared) == 1 else None
            out.append(
                Key(
                    table=name,
                    name=key,
                    type="" if value is None else _named(value),
                    default=None if value is None else _rendered(value),
                    declared=bool(declared),
                    set=None if only is None else _rendered(only),
                    at=len(declared),
                    note=note,
                )
            )
    return Shape(
        keys=tuple(out),
        version=__version__,
        source=None if config.source is None else config.relative(config.source),
    )


def stated(found: Shape) -> str:
    """The shape as a reader is told it: one row per key, grouped by the table it is under."""
    where = found.source or "nothing (this project declares no roadkeep.toml)"
    rows = [
        f"{len(found.keys)} key(s) this build accepts, read against {where}",
        f"  build    roadkeep {found.version} — what is listed is what *this* copy takes, "
        f"which is how a key it predates is told from a typo",
    ]
    for name in found.tables():
        under = found.under(name)
        rows.append(f"[{name or 'top level'}]")
        # The first sentence and not the run, which is the split between the two answers: a
        # listing is read by somebody deciding what to declare, and the whole paragraph — 90
        # words on `[files]` — is what `--json` carries for the completion list RK1271 hovers.
        if under and under[0].note:
            rows.append(f"  {_opening(under[0].note)}")
        for one in under:
            default = "no default" if one.default is None else f"default {one.default}"
            spelled = f"{one.type}, " if one.type else ""
            # What the project set, where it set one (RK1278): the number in use is the one a
            # reader hovering the key they are about to change is asking about, and the
            # default is the fact that stops mattering the moment there is a value.
            mark = _how(one)
            rows.append(f"  {one.name:<12} {spelled}{default}  ({mark})")
    return "\n".join(rows)


def payload(found: Shape) -> dict[str, object]:
    """The same answer as data — what a completion list reads (RK1270, RK1271)."""
    return {
        "version": found.version,
        "source": found.source,
        "keys": [
            {
                "table": one.table,
                "key": one.name,
                "address": one.address,
                "type": one.type,
                "default": one.default,
                "declared": one.declared,
                # And what was declared (RK1278) — `null` where nobody did, which is a
                # different fact from a value of zero and is said as such.
                "set": one.set,
                # And how many addresses wrote one (RK1282), which is the fact where the
                # value is not: above one, `set` is null and this is why.
                "addresses": one.at,
                "note": one.note,
            }
            for one in found.keys
        ],
    }


def tables(names: Sequence[str] = ()) -> tuple[str, ...]:
    """The table names, for a caller that wants the addresses and not the keys."""
    return tuple(names) or tuple(TABLES)
