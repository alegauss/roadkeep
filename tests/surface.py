"""The package's own source, as the one set a suite-wide survey quantifies over (RK496).

Seven tests sweep every module of `roadkeep` — for a cache decorator, a spelled command, a
hard-coded verb, a `.block(` call, a missing `__init__.py`, an index entry. Each derived its
own file set inline, and each was written against the layout that existed on the day.

RK494 measured what that costs. Adding `src/roadkeep/verbs/` and its eight modules broke two
of the seven loudly — a census keyed by `Path.name` let `verbs/shipping.py` answer under
`shipping.py`, counting one file as another — and left **three passing while covering nothing
new**, each a `glob("*.py")` from when the package was flat. RK488 had built two of those
precisely to say how many spellings were left; afterwards they answered about 43 of 51 files
and said so nowhere. A red test is a message; a green one that stopped looking is a claim.

So the set is declared once, here, and the surveys ask for it. Two properties follow that
could not be stated before: `test_invariants` can record a row naming this surface (RK491 has
two rows whose surface is "every module of this package", with no address to put in them), and
one test can hold that nothing derives a second view of the package — which is what keeps the
next survey from being written against today's layout.

Addressed by :attr:`Module.where`, the path **under** the package, and never by filename: two
directories are allowed to hold a `shipping.py`, and a survey that cannot tell them apart is
one that silently reports about the wrong one.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property, lru_cache
from pathlib import Path

#: The package's source tree. Read from this file's location rather than from an import, for
#: the reason `test_caches` gives about its own read: importing the package to enumerate it
#: finds only what happens to have been imported.
PACKAGE = Path(__file__).resolve().parents[1] / "src" / "roadkeep"


# No `slots`: :func:`cached_property` writes the read into the instance dictionary, which a
# slotted class does not have — and the read is what the cache is for.
@dataclass(frozen=True)
class Module:
    """One `.py` file of the package, addressed the way a survey should report it."""

    #: Its path under the package, in posix spelling — `cli.py`, `verbs/shipping.py`. This is
    #: the address: unique, stable across platforms, and the thing to print in a failure.
    where: str
    #: The file itself, for a survey that needs to stat it or read its parent.
    path: Path

    @cached_property
    def text(self) -> str:
        """Its source, read once per run: six surveys ask for the same fifty files."""
        return self.path.read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def modules() -> tuple[Module, ...]:
    """Every module of the package, recursively, in `where` order.

    Recursive is the whole point: a subpackage is where the next eight modules arrive, and a
    survey that stops at the top level keeps passing while it stops covering them.

    Cached so that the same :class:`Module` objects come back to every caller, which is what
    makes :attr:`Module.text` a read per file rather than a read per survey.
    """
    return tuple(
        Module(where=path.relative_to(PACKAGE).as_posix(), path=path)
        for path in sorted(PACKAGE.rglob("*.py"))
        if "__pycache__" not in path.parts
    )


def names() -> tuple[str, ...]:
    """What the Layout index in `agents.md` has to name, which is not the module set (RK494).

    A different question from :func:`modules`, and the reason it is a second function rather
    than a filter: the index names the top level, and a **subpackage as one entry** — its own
    `__init__` docstring being the authority on what is inside it, which is this project's
    rule for every other module too. So `verbs` appears and `verbs/shipping` does not.
    """
    return tuple(
        sorted(
            {path.stem for path in PACKAGE.glob("*.py") if path.stem != "__init__"}
            | {path.name for path in PACKAGE.iterdir() if (path / "__init__.py").exists()}
        )
    )
