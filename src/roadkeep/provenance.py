"""Which tree answered, and at what commit (RK79).

The plugin carries its own `src/roadkeep/`, and a developer of this tool has a checkout of
the same package. RK57's launcher puts the plugin's copy first on `sys.path`, so the hook
and the MCP server run the cache while `python -m roadkeep.cli` runs the checkout — two
engines, both reporting `0.1.0`, with nothing observable between them. Measured live: 14
files differing and two modules present in one tree only.

**Making them distinguishable is the fix, not making them the same.** A cache is allowed to
lag a checkout; what is not survivable is being unable to say which one produced an answer,
because that turns every other symptom into a guess about which code ran.

So the version string carries where it came from. `__version__` stays the one literal
(RK19) — this adds no second number, only the two facts a release number cannot hold: the
directory the modules were imported from, and the commit those files are at. The directory
alone already separates a cache from a checkout; the commit separates two checkouts, and
names the case `/plugin update` cannot fix, where the cache is current with a remote the
work has not reached.

Git is asked about **the package's own directory**, never the governed project's — a
different question from :mod:`roadkeep.history`, which reads the repository a `Config` points
at. It is asked at most once per process and never on a path that writes: a subprocess on
every `add` would buy nothing and cost the tool's own budget. A tree that git cannot answer
for (an installed wheel, no git on PATH) is not an error — the directory is still the
answer, and it is the half that distinguishes the two engines above.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import roadkeep

# The package's one call to git: its timeout, its encoding and its single failure type.
# Duplicating a `subprocess.run` here would be duplicating those three decisions.
from roadkeep.history import HistoryUnavailable, _run as _git

#: What the revision reads as when git cannot place these files: no repository, no git on
#: PATH, or a package directory nothing in the surrounding tree tracks — an installed copy
#: that happens to sit under someone else's checkout must not borrow that checkout's HEAD.
UNTRACKED = "untracked"

#: Appended to the commit when the files differ from it, because the commit is then a
#: description of what was edited rather than of what is running.
MODIFIED = "modified"


@dataclass(frozen=True, slots=True)
class Engine:
    """The answering copy of this package: its version, its files, and their commit."""

    version: str
    #: The directory the modules were imported from — always known, and on its own enough
    #: to tell a plugin cache from a checkout.
    home: Path
    #: Short sha of the commit those files are at, or `None` when git cannot place them.
    commit: str | None
    #: Whether the files differ from that commit. Scoped to `home`: a governed file edited
    #: elsewhere in the same repository does not make the engine modified.
    modified: bool = False

    @property
    def revision(self) -> str:
        if self.commit is None:
            return UNTRACKED
        return f"{self.commit} {MODIFIED}" if self.modified else self.commit

    def __str__(self) -> str:
        return f"roadkeep {self.version} ({self.revision}, {self.home})"


@lru_cache(maxsize=1)
def engine() -> Engine:
    """Describe the copy of this package that is running. Cached: one git call per process."""
    home = Path(roadkeep.__file__).resolve().parent
    commit, modified = _placed(home)
    return Engine(version=roadkeep.__version__, home=home, commit=commit, modified=modified)


def _placed(home: Path) -> tuple[str | None, bool]:
    try:
        # `ls-files` first: it answers "does this tree track these very files", which
        # `rev-parse` does not — an installed package under an unrelated repository would
        # otherwise report that repository's HEAD as its own provenance.
        if not _git(home, "ls-files").strip():
            return None, False
        commit = _git(home, "rev-parse", "--short", "HEAD").strip()
        modified = bool(_git(home, "status", "--porcelain", ".").strip())
    except HistoryUnavailable:
        return None, False
    return commit or None, modified
