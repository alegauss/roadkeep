"""Deriving the next id (RK4).

Real backlogs are non-contiguous: an epic claims a sub-range, a superseded task is
retired and its id is never reused, and a block's header range says nothing about what
comes next. So the next id is **one past the highest id anywhere**, and the two words
that matter are *highest* and *anywhere*.

* **Highest, not first-free.** Filling the hole left by a retired id makes two
  different tasks share a number in the history — a `git log -S RK7` that returns two
  unrelated designs is worse than a gap.
* **Anywhere.** The changelog holds shipped ids, `agents.md` mentions ids in prose, and
  either is enough to make a "free" id a collision. Every file in
  :meth:`Config.id_sources` is scanned as text, not as a task list.

A counter file would be a second source of truth, and it would drift the first time
someone edited the roadmap by hand. The maximum is derivable, so it is derived — and
the result carries *where* it came from, because an id is the one decision that cannot
be taken back once it is committed.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from roadkeep.config import Config
from roadkeep.kernel.schema import Schema


@dataclass(frozen=True, slots=True)
class IdRef:
    """One occurrence of an id, and where it was found."""

    id: str
    number: int
    path: Path
    lineno: int
    #: Which family it belongs to (RK74). Carried rather than re-derived, because the
    #: maximum `next_id` takes is a maximum *within* a family and the scan is the only
    #: place that already knows which one matched.
    family: str = ""


def id_scanner(schema: Schema) -> re.Pattern[str]:
    """`<prefix><n>` as it appears in running text, spelled the way this project spells it.

    Three named groups, always: `family`, the `number` the maximum is taken over, and the
    `sub` letter — empty where `[ids] suffix` declares none, so a caller reads the same
    shape whatever the project wrote.

    Takes the schema and not the prefixes alone (RK106), because padding and the
    sub-letter are two more declarations about what an id *is*: a scan that knew only the
    family would read `T24b` as no id at all, and the number a document already spends is
    exactly what the next one must clear. It asks the schema to *join* them too (RK109) —
    this used to assemble its own copy, and a scan spelling an id differently from the gate
    is how a number the pattern refuses stays invisible to the counter that would clear it.
    """
    return re.compile(rf"\b{schema.id_groups}\b")


def scan(config: Config) -> tuple[IdRef, ...]:
    """Every id occurrence in every configured source, in file order.

    A source that does not exist is skipped rather than raised: `init` (RK18) creates
    the files, and refusing to answer "what is the next id" because a strategy file is
    absent would be an obstacle rather than a guardrail.
    """
    pattern = id_scanner(config.schema)
    found: list[IdRef] = []
    # The reservations first, as occurrences of the config itself (RK1031): an epic id owns a
    # sub-range and is never written as a line, so a scan over the files alone would hand the
    # next `add` an address the project has already spoken for. `source` is the file that
    # declares them, which is what makes the provenance a reader can act on.
    declared_at = _declared_at(config)
    for token in config.reserved:
        match = pattern.fullmatch(token)
        if match is not None:
            found.append(
                IdRef(
                    id=token,
                    number=int(match.group("number")),
                    path=config.source or config.root,
                    lineno=declared_at.get(token, 0),
                    family=match.group("family"),
                )
            )
    for path in config.id_sources():
        if not path.is_file():
            continue
        with path.open("r", encoding="utf-8", newline="") as handle:
            for lineno, line in enumerate(handle, start=1):
                for match in pattern.finditer(line):
                    found.append(
                        IdRef(
                            id=match.group(0),
                            number=int(match.group("number")),
                            path=path,
                            lineno=lineno,
                            family=match.group("family"),
                        )
                    )
    return tuple(found)


def _declared_at(config: Config) -> dict[str, int]:
    """Which line of `roadkeep.toml` each reservation is written on (RK1031).

    A refusal names `file:line` and a reader clicks it, so `roadkeep.toml:0` would be the one
    address in this tool that opens nothing. Read off the text rather than tracked through
    the parse: `tomllib` keeps no positions, and a config that spells its list across four
    lines is the shape a project with four epics writes.
    """
    if not config.reserved or config.source is None:
        return {}
    try:
        text = config.source.read_text(encoding="utf-8")
    except OSError:
        return {}
    found: dict[str, int] = {}
    for lineno, line in enumerate(text.splitlines(), start=1):
        for token in config.reserved:
            if token not in found and f'"{token}"' in line:
                found[token] = lineno
    return found


def highest(config: Config, family: str | None = None) -> IdRef | None:
    """The largest id, with its provenance. None when that family has no ids yet.

    ``family`` defaults to every one the project declares, which is the same answer as
    before for the projects that declare one. It is passed by :func:`next_id`, where the
    maximum has to be per family (RK74): two tracks sharing a counter are two tracks that
    renumber each other, and cursarei's `C##` reaching 40 must not push `V##` past its 05.
    """
    refs = [ref for ref in scan(config) if family is None or ref.family == family]
    if not refs:
        return None
    return max(refs, key=lambda ref: ref.number)


#: The roles whose files carry an id as a **line** — a task, an entry, a paused line. Every
#: other occurrence of an id anywhere is a mention in a sentence, and the scan cannot tell
#: the two apart because every id starts as one (RK431).
CARRIERS = ("roadmap", "changelog", "deferred")


def carried(config: Config) -> frozenset[str]:
    """Every id some governed file holds as a line rather than names in a sentence.

    Read off the parsed documents and not off the scan: the scan is deliberately textual
    (that is what makes `agents.md` count), and what is wanted here is the complement —
    the ids that are *occupied*, which only a parse can say.
    """
    # The reservations are among them (RK1031): a reserved id is *taken*, so a design naming
    # one names work this project has spoken for rather than promising an address. What it is
    # not is a line, which is why `lint` still reports one that becomes a line.
    out: set[str] = set(config.reserved)
    for role in CARRIERS:
        if not config.has(role) or not config.path(role).is_file():
            continue
        out.update(config.document(role).by_id())
    return frozenset(out)


@dataclass(frozen=True, slots=True)
class Promise:
    """An id a sentence named and no line ever took (RK431)."""

    #: The id the prose promised — one below :attr:`derived`, and the number the author
    #: probably meant this task to have.
    id: str
    #: Where the sentence is, relative to the project root, as `file:line`.
    where: str
    #: The id handed out instead, because the mention had already raised the maximum.
    derived: str

    @property
    def sentence(self) -> str:
        """The one spelling, so `add` and `next-id` say it in the same words."""
        return (
            f"{self.id} is named at {self.where} and no line carries it, so {self.derived} "
            f"was derived past it: if that sentence promised this task, it now names an id "
            f"nothing will occupy"
        )


@dataclass(frozen=True, slots=True)
class Derivation:
    """The next id, and the promise deriving it stepped over (RK431)."""

    id: str
    #: None on the overwhelming majority of derivations, where the highest id is a line.
    promise: Promise | None = None

    def stated(self) -> str:
        """The id and nothing else.

        Stdout here is the id, because this command exists to be captured in a shell — a
        second line in that capture is a broken id, which is why the promise goes to stderr.
        """
        return self.id

    def notice(self) -> list[str]:
        """The promise deriving this stepped over, for **stderr** (RK431)."""
        return [] if self.promise is None else [f"roadkeep: {self.promise.sentence}"]

    def payload(self, config: Config, family: str) -> dict[str, object]:
        """The same answer with where the maximum was found, so it can be audited."""
        from roadkeep.rendering import _promise_json  # noqa: PLC0415 - RK260

        top = highest(config, family)
        return {
            "next": self.id,
            "prefix": family,
            "prefixes": list(config.schema.prefixes),
            "highest": None
            if top is None
            else {
                "id": top.id,
                "file": config.relative(top.path),
                "line": top.lineno,
            },
            # Beside `highest` and not folded into it (RK431): that field says which
            # occurrence set the maximum, and this says the occurrence was a sentence rather
            # than a line — which is the whole difference nothing recorded.
            "promise": _promise_json(self.promise),
            "sources": [
                config.relative(path) for path in config.id_sources() if path.is_file()
            ],
        }


def derivation(config: Config, family: str | None = None) -> Derivation:
    """The next id, and whether the number below it was a promise nobody kept (RK431).

    Shipping SH207 meant recording a defect it had uncovered, and the ledger entry said
    *"filed as SH614"* — the id `next-id` had just reported. `add` then handed the new task
    **SH615**, because the entry had by then been written into a file the scan reads, so
    the highest id in the corpus was the one the sentence had promised. Nothing
    malfunctioned: the deriver cannot tell an id that was *declared* from one merely
    *mentioned*, and every id starts as a mention.

    The cost is quiet — the `add` succeeds, the number looks unremarkable, and the only
    signal is a prose reference to an id nothing will occupy, in a file the guard forbids
    hand-editing. It is also a gap `gaps` cannot cover: that verb explains an id in neither
    file, and this one *is* in one.

    So the derivation says so, and does nothing else. It does not reserve the number
    (a second source of truth, which is the counter file this module exists without) and
    it does not refuse: which of the two ids the author wanted is a judgement about the
    meaning of a sentence, and this tool has no model of one (L4).
    """
    chosen = family or config.schema.prefix
    if chosen not in config.schema.prefixes:
        raise UnknownFamily(chosen, config.schema.prefixes)
    top = highest(config, chosen)
    number = top.number + 1 if top else 1
    identifier = config.schema.spell_id(chosen, number)
    if top is None or top.id in carried(config):
        return Derivation(identifier)
    return Derivation(
        identifier,
        Promise(
            id=top.id,
            where=f"{config.relative(top.path)}:{top.lineno}",
            derived=identifier,
        ),
    )


def next_id(config: Config, family: str | None = None) -> str:
    """One past the highest id *in this family*, never the first unused number.

    ``family`` is the caller's declaration, defaulting to the first the project declares.
    Nothing infers it: the letter is which track the work belongs to, and a tool that
    guessed it from a block heading would be holding an opinion about someone else's
    backlog (RK74).

    Spelled by :meth:`Schema.spell_id`, so a project that declared a width gets `D10` and
    not the `D1` its own gate would refuse a moment later (RK106).

    The id alone, for the callers that only need one. :func:`derivation` is the same answer
    with the promise it may have stepped over (RK431), and is what the two doors that
    *report* a derived id call.
    """
    return derivation(config, family).id


class UnknownFamily(ValueError):
    """An id was asked for under a prefix this project does not number."""

    def __init__(self, family: str, declared: Sequence[str]) -> None:
        self.family = family
        self.declared = tuple(declared)
        super().__init__(
            f"{family!r} is not a family this project numbers "
            f"({', '.join(declared)}): an id minted outside them is an id "
            f"nothing else in the backlog can read"
        )
