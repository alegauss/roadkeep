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


def id_scanner(prefixes: str | Sequence[str]) -> re.Pattern[str]:
    """`<prefix><n>` as it appears in running text, with no zero padding.

    Padding is excluded on purpose: `RK007` and `RK7` would otherwise be two
    spellings of one id, and the maximum is taken over the numbers these capture.

    Every family the project declares matches (RK74), longest first so the alternation
    reads as though the order mattered even where :func:`~roadkeep.schema._check_prefixes`
    has already made it impossible for it to.
    """
    if isinstance(prefixes, str):
        prefixes = (prefixes,)
    ordered = sorted(prefixes, key=lambda p: (-len(p), p))
    families = "|".join(re.escape(prefix) for prefix in ordered)
    return re.compile(rf"\b({families})([1-9][0-9]*)\b")


def scan(config: Config) -> tuple[IdRef, ...]:
    """Every id occurrence in every configured source, in file order.

    A source that does not exist is skipped rather than raised: `init` (RK18) creates
    the files, and refusing to answer "what is the next id" because a strategy file is
    absent would be an obstacle rather than a guardrail.
    """
    pattern = id_scanner(config.schema.prefixes)
    found: list[IdRef] = []
    for path in config.id_sources():
        if not path.is_file():
            continue
        with path.open("r", encoding="utf-8", newline="") as handle:
            for lineno, line in enumerate(handle, start=1):
                for match in pattern.finditer(line):
                    found.append(
                        IdRef(
                            id=match.group(0),
                            number=int(match.group(2)),
                            path=path,
                            lineno=lineno,
                            family=match.group(1),
                        )
                    )
    return tuple(found)


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


def next_id(config: Config, family: str | None = None) -> str:
    """One past the highest id *in this family*, never the first unused number.

    ``family`` is the caller's declaration, defaulting to the first the project declares.
    Nothing infers it: the letter is which track the work belongs to, and a tool that
    guessed it from a block heading would be holding an opinion about someone else's
    backlog (RK74).
    """
    chosen = family or config.schema.prefix
    if chosen not in config.schema.prefixes:
        raise UnknownFamily(chosen, config.schema.prefixes)
    top = highest(config, chosen)
    number = top.number + 1 if top else 1
    return f"{chosen}{number}"


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
