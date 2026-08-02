"""roadkeep — the roadmap format as a schema, enforced where the text is created."""

from roadkeep.schema import (
    ARROW,
    DESIGNED,
    EM_DASH,
    IDEA,
    IN_PROGRESS,
    NO_DEPS,
    OPEN_MARKERS,
    PARTIAL,
    SHIPPED,
    Dep,
    Id,
    Schema,
    SchemaError,
    Task,
    Violation,
)

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
#: reads this literal, so a release cannot ship a number the package disagrees with.
__version__ = "0.1.0"
