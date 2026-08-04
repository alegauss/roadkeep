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

The same two facts answer a second question the server needs (RK155): the config is re-read
per message, deliberately, but the *code* reading it was imported once at session start — so
`[claims] held` added to `roadkeep.toml` and to `config.py` in one commit made every MCP write
refuse `unknown key 'claims'` while the CLI in a terminal accepted it. :attr:`Engine.stale`
names the modules that moved under the running process, so the refusal states the cause instead
of describing a config that is correct. It never reloads: see that attribute for why.

Git is asked about **the package's own directory**, never the governed project's — a
different question from :mod:`roadkeep.history`, which reads the repository a `Config` points
at. It is asked at most once per process and never on a path that writes: a subprocess on
every `add` would buy nothing and cost the tool's own budget. A tree that git cannot answer
for (an installed wheel, no git on PATH) is not an error — the directory is still the
answer, and it is the half that distinguishes the two engines above.
"""

from __future__ import annotations

import shutil
import time
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

#: When this process loaded the package, which is the only clock staleness can be measured
#: against (RK155). Not a module mtime and not :func:`engine`'s cache: the question is whether
#: the files changed *after* the code answering was imported, and only the process knows when
#: that was. Set at import, so a server that starts late measures from when it started.
_LOADED_AT = time.time()

#: How much later than :data:`_LOADED_AT` a file must be to count. One second, because a file
#: written in the same second the process started is the process's own installer, not an edit,
#: and a server that called itself stale on every start would be a warning nobody reads.
_GRACE = 1.0


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

    @property
    def stale(self) -> tuple[str, ...]:
        """This package's own modules that changed after the process imported them (RK155).

        Read from disk on every call and never cached, unlike everything else here: identity
        is a fact about the process and this is a fact about right now — a server whose answer
        to "am I current" was decided at startup would be answering the wrong question.

        An mtime comparison and deliberately nothing more. Re-executing the package is possible
        — the server holds no state between messages — and is the kind of cleverness that fails
        as a half-loaded module; the harness already restarts a plugin whose version moved
        (RK153), which is why every commit bumps the patch. So what is left here is not
        reloading but *saying*, which costs one `stat` per module and cannot be wrong.
        """
        changed = []
        for module in sorted(self.home.glob("*.py")):
            try:
                if module.stat().st_mtime > _LOADED_AT + _GRACE:
                    changed.append(module.name)
            except OSError:
                # A module that cannot be stat'd is not evidence of anything. Every other
                # failure in this package allows; a provenance note is the last place to
                # start raising.
                continue
        return tuple(changed)

    def carried_by(self, root: Path) -> bool:
        """Whether the code answering lives **inside** the project it is answering about (RK246).

        Which of the two wirings started this process, asked as a fact rather than guessed from
        the harness's directory layout. A plugin's `mcpServers` is versioned by `plugin.json`, so
        RK153's patch bump reloads it; a project running the tool from its own checkout is wired
        by `.mcp.json` → `scripts/roadkeep.py`, which carries no version at all — nothing about
        that process is addressed by a bump, and restarting the session is the only remedy.

        The two cases differ in exactly this: the plugin's copy is a cache somewhere else, and a
        checkout's is under the governed root. Measured in this repository, where five bumps in
        one session left the server stale while its own note named the bump as the fix.

        `root` is expected resolved, which every `Config.root` is; a relation this cannot
        establish reads as the plugin, because that branch also ends in "restart the session"
        and is the half of the sentence that is true either way.
        """
        return root in self.home.parents

    def __str__(self) -> str:
        return f"roadkeep {self.version} ({self.revision}, {self.home})"


#: The console script `pyproject.toml` declares, which is what a message may name only where a
#: PATH lookup finds it (RK254).
CONSOLE = "roadkeep"

#: The launcher the package ships beside itself (RK57), relative to :attr:`Engine.home`. Named
#: here because :func:`invocation` is the only reader and it is a fact about this distribution's
#: layout, not about any project.
LAUNCHER = ("scripts", "roadkeep.py")


@lru_cache(maxsize=1)
def invocation() -> str:
    """How a shell reaches this engine **on this machine** (RK254).

    Every message offering a shell command used to spell `roadkeep <verb>` literally, and RK57's
    own finding is that the console script exists only after `pip install roadkeep` and only if
    the interpreter's scripts directory is on PATH — so on a plugin-installed machine, and in this
    repository, the tool's most-read message named a command that answers `command not found`.
    That is the family RK242, RK246, RK250 and RK253 each removed one instance of, at the traffic
    of every denied edit.

    Three answers, most specific first, and each one observed rather than assumed:

    * the console script, where a PATH lookup finds it;
    * the launcher this package ships beside itself, where it is on disk — spelled relative to the
      working directory when it is under it, because an absolute path is a message about one
      machine (the same reason :class:`~roadkeep.guarding.Refusal` quotes the project's spelling);
    * `python -m roadkeep.cli`, which is right whenever the package is importable at all and is
      the only answer left when neither of the two above is there.

    `python` and not :data:`sys.executable`: the plugin's own `hooks.json` and `.mcp.json` spell
    it that way, so this is the project's established assumption rather than a second one, and a
    quoted absolute interpreter path is not what a reader copies.

    Cached: neither PATH nor the package's own layout changes inside one process, and the deny
    path this is read on is the one place a `which` scan would be paid for repeatedly.
    """
    if shutil.which(CONSOLE):
        return CONSOLE
    launcher = engine().home.parents[1].joinpath(*LAUNCHER)
    if launcher.is_file():
        return f"python {_spelled(launcher)}"
    return "python -m roadkeep.cli"


def _spelled(launcher: Path) -> str:
    """The launcher as a reader would type it: forward slashes, quoted only where a space forces it.

    `as_posix` and not the native separator, because the shell this is copied into is the agent's,
    and there a `\\` is an escape rather than a path component — `scripts\\roadkeep.py` reaches
    `scriptsroadkeep.py`. Windows `python` accepts forward slashes either way, so one spelling is
    right on both platforms and the native one is right on neither reader.
    """
    try:
        shown = launcher.relative_to(Path.cwd()).as_posix()
    except (OSError, ValueError):  # another drive, another tree, or no readable cwd
        shown = launcher.as_posix()
    return f'"{shown}"' if " " in shown else shown


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
