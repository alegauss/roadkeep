"""roadkeep — the roadmap format as a schema, enforced where the text is created.

The names below are `schema`'s, re-exported so a reader importing the package gets the
format's vocabulary without knowing which module holds it. They are resolved **on first
access** rather than at import (RK199), because a package `__init__` runs before any module
in it does and there is no entry point that can decline it.

Measured, the eager version cost 23ms of the 43ms floor RK176 spent a whole task reaching:
`import roadkeep.screening` — a module whose entire argument is that it imports nothing but
the standard library — loaded `schema`, and through it `dataclasses`, `inspect`, `re` and
`enum`. Counted across `src/`, **no module in the package reaches a name through here**:
every `from roadkeep import …` in the tree names a submodule or `__version__`. The
re-export list exists for readers, and readers are not who was paying for it.

PEP 562 and not a shorter list, because dropping the names would be a breaking change to a
published package's declared surface for a saving laziness gets anyway. Each name is bound
into the module on first use, so the cost is paid once and only where somebody asks.
"""

from __future__ import annotations

__all__ = [
    "ARROW",
    "DESIGNED",
    "EM_DASH",
    "IDEA",
    "IN_PROGRESS",
    "NO_DEPS",
    "OPEN_MARKERS",
    "PARTIAL",
    "SHIPPED",
    "Dep",
    "Id",
    "Schema",
    "SchemaError",
    "Task",
    "Violation",
]
#: The one place the version is written (RK19). `pyproject.toml` declares it `dynamic` and
#: reads this literal, so a release cannot ship a number the package disagrees with — which
#: is also why it stays eager: a build backend parses this file, it does not import it.
__version__ = "0.1.98"

#: What the names above are, resolved once each. A frozenset and not a `TYPE_CHECKING`
#: import of them: the conventional block would pull `typing` into every startup — 5.6ms,
#: measured, and 90% of what is left of this file — to serve a checker that does not read
#: this package anyway, since it ships no `py.typed` (PEP 561). What the surface promises is
#: held by `tests/test_packaging.py` instead, which is a stronger claim than an annotation.
_EXPORTED = frozenset(__all__)


def __getattr__(name: str) -> object:
    """Resolve a re-exported name out of `schema`, once (PEP 562).

    Bound into `globals()` on the way out, so the second access is the dict lookup an eager
    import would have given — the laziness is about the import, not about every read.
    """
    if name not in _EXPORTED:
        raise AttributeError(f"module 'roadkeep' has no attribute {name!r}")
    from roadkeep import schema

    value = getattr(schema, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """The re-exports included, so `dir(roadkeep)` answers what `__all__` promises."""
    return sorted(_EXPORTED | set(globals()))
