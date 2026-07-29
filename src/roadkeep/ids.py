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


def id_scanner(prefix: str) -> re.Pattern[str]:
    """`<prefix><n>` as it appears in running text, with no zero padding.

    Padding is excluded on purpose: `RK007` and `RK7` would otherwise be two
    spellings of one id, and the maximum is taken over the numbers these capture.
    """
    return re.compile(rf"\b{re.escape(prefix)}([1-9][0-9]*)\b")


def scan(config: Config) -> tuple[IdRef, ...]:
    """Every id occurrence in every configured source, in file order.

    A source that does not exist is skipped rather than raised: `init` (RK18) creates
    the files, and refusing to answer "what is the next id" because a strategy file is
    absent would be an obstacle rather than a guardrail.
    """
    pattern = id_scanner(config.schema.prefix)
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
                            number=int(match.group(1)),
                            path=path,
                            lineno=lineno,
                        )
                    )
    return tuple(found)


def highest(config: Config) -> IdRef | None:
    """The largest id, with its provenance. None when the project has no ids yet."""
    refs = scan(config)
    if not refs:
        return None
    return max(refs, key=lambda ref: ref.number)


def next_id(config: Config) -> str:
    """One past the highest id anywhere, never the first unused number."""
    top = highest(config)
    number = top.number + 1 if top else 1
    return f"{config.schema.prefix}{number}"
