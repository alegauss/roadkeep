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


def address(module: str) -> str:
    """Where a module lives **now**, asked by its module name — `schema` → `kernel/schema.py`.

    The lookup RK1074 was filed for. RK496 declared the module *set* once and had the surveys
    ask for it; the addresses stayed hand-written, so moving two files into `kernel/` broke
    seven surveys one at a time, each because a path literal somewhere had to be edited. A
    test that asks for `address("document")` is one the next reorganisation does not touch.

    Refused rather than defaulted where the name is ambiguous or unknown, which is the whole
    value: a survey that quietly kept a stale address is what this replaces, and two modules
    sharing a name — `shipping.py` and `verbs/shipping.py` — is the case RK494 measured, so
    the caller passes `verbs/shipping` there and gets an answer rather than a coin toss.
    """
    wanted = f"{module}.py"
    found = [one.where for one in modules() if one.where in (wanted, module)]
    if not found:
        found = [one.where for one in modules() if one.where.endswith(f"/{wanted}")]
    if len(found) != 1:
        known = ", ".join(sorted(one.where for one in modules()))
        raise LookupError(
            f"{module!r} names {len(found)} modules ({', '.join(found) or 'none'}): "
            f"pass the path under the package where two share a name — {known}"
        )
    return found[0]


def addresses(value: str) -> bool:
    """Whether a literal is an address **into this package** rather than any path (RK1074).

    Two narrowings, and both are what keeps the rule from being one somebody exempts their
    way around. A bare `schema.py` is not enough: a test writing that name into its own
    `tmp_path` is naming a fixture, and a check that could not tell the two apart would fire
    on half the suite. And a directory is not enough either — `test_baseline` writes
    `src/gone.py` and `lib/later.py` into a fixture repository, which are paths and not
    addresses.

    So the first component has to be a subpackage this package actually has, read from the
    census rather than listed: `kernel/` is one because RK1069 made it one, and the next will
    be recognised the day it exists rather than the day somebody remembers this function.
    """
    directory, _, name = value.partition("/")
    if not name or not name.endswith(".py"):
        return False
    return directory in {
        one.where.partition("/")[0] for one in modules() if "/" in one.where
    }


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


@lru_cache(maxsize=1)
def suite() -> tuple[Path, ...]:
    """Every test module of this suite, in name order — the sweeps' own surface (RK1448).

    :func:`modules` is about the package and this is about the tests, and it is here for the
    same reason: RK496 declared the package's set once because a survey deriving its own view
    agrees with every other right up until the layout moves. A second sweep over `tests/`
    would be that failure in the other directory, and this one arrived the moment a rule about
    assertions needed the same set `test_invariants` already reads.

    `test_invariants` keeps its own glob deliberately: it is the module that *checks* this
    declaration, and a check that read the declaration would be the declaration checking
    itself. Every other sweep asks here.
    """
    return tuple(sorted(Path(__file__).resolve().parent.glob("test_*.py")))
