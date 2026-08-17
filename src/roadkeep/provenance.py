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
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import roadkeep

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

#: The directory the modules that are **executing** were imported from. A fact about this
#: process, in the same class as :data:`_LOADED_AT` and deliberately not :attr:`Engine.home`:
#: which files ran is not a field a caller can describe, and the one surface that fabricates an
#: engine to test the note would otherwise be fabricating the traceback too (RK267).
_HOME = Path(__file__).resolve().parent

#: This package's modules on the traceback of the last refusal witnessed in this process, or
#: `None` for *nothing has been witnessed* (RK267) — which is not the same as the empty tuple,
#: *a refusal decided outside this package*. A surface that cannot tell those apart would
#: suppress a note on a refusal it never learned the origin of.
_WITNESSED: tuple[str, ...] | None = None

#: The arguments this process was invoked with, as the surface that parsed them read them, or
#: `()` where nothing set it — which is every in-process caller: the MCP server dispatches a
#: parsed namespace and never an argv (RK24), and a test calls `main([...])`. Set once per
#: process by :func:`~roadkeep.cli.main`, so a retry offered on a refusal is the *caller's own*
#: call and not this interpreter's `sys.argv`, which under a server or a test harness names
#: somebody else's program entirely (RK1149).
_INVOKED: tuple[str, ...] = ()


def _codecs() -> tuple[tuple[str, str], ...]:
    """`name -> encoding/errors` for the three streams, as they are right now.

    `?` and never a raise for a stream with neither attribute: that is `pythonw`'s `None`, or a
    harness's own object, and a fact about provenance is not worth a crash on import.
    """
    return tuple(
        (
            name,
            f"{getattr(stream, 'encoding', None) or '?'}/"
            f"{getattr(stream, 'errors', None) or '?'}",
        )
        for name, stream in (("stdin", sys.stdin), ("stdout", sys.stdout), ("stderr", sys.stderr))
    )


#: The three streams as this process opened them — a fact about this process in the same class
#: as :data:`_LOADED_AT`, and the reason it is read *here* is that here is early enough (RK341).
#: `cli.main` reconfigures all three to UTF-8 in its first three statements, so a capture
#: composed afterwards reads this tool's own hardening off them instead of the environment that
#: broke the session: RK337 arrived that way, a field `UnicodeEncodeError` whose re-run exited 0.
#: Import time is before `main` runs and after nothing this package did, which is exactly the
#: moment wanted — and it is one dict per *interpreter* rather than per module copy, which
#: `cli.main` could not be, since `python -m roadkeep.cli` loads that module twice (as
#: `__main__` and as `roadkeep.cli`) and only one of the two would hold the pristine reading.
STARTUP_CODECS: tuple[tuple[str, str], ...] = _codecs()


def named(module: Path, home: Path) -> str:
    """What this package calls one of its own modules — the path under it, or `""` (RK1073).

    One spelling, because the staleness note is composed from **two** readers of it and they
    disagreed for six tasks. `Engine.stale` was made recursive by RK494, when `verbs/` took
    eight handlers each named after the domain module it calls — so a bare `.name` reports
    `shipping.py` for either of two files — and `raised_in`, which answers the other half of
    the same note, kept a flat test on the frame's parent directory. Every refusal decided
    inside `verbs/` therefore named nothing, and the note compared a recursive answer against
    a shallow one. RK1069 surfaced it by moving two more modules down a directory.

    `""` for anything outside, which is the answer both callers want: a frame in the stdlib
    and a file under someone else's tree are the same non-answer, and neither is worth a
    raise. Resolved, and every filesystem failure allows — a provenance note is the last
    place in this package to start raising.
    """
    try:
        return module.resolve().relative_to(home).as_posix()
    except (OSError, ValueError):
        return ""


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
        # Recursive since RK494, and named by :func:`named` since RK1073 — the one spelling
        # this package has for its own modules, shared with `raised_in` because the note is
        # composed from both and two vocabularies made the comparison meaningless.
        for module in sorted(self.home.rglob("*.py")):
            try:
                if module.stat().st_mtime > _LOADED_AT + _GRACE:
                    changed.append(named(module, self.home))
            except OSError:
                # A module that cannot be stat'd is not evidence of anything. Every other
                # failure in this package allows; a provenance note is the last place to
                # start raising.
                continue
        return tuple(where for where in changed if where)

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


def raised_in(error: BaseException) -> tuple[str, ...]:
    """This package's modules on a refusal's traceback, outermost frame first (RK267).

    The half of the staleness note that :attr:`Engine.stale` cannot supply. An mtime says a file
    moved; this says which files were *executing* when the refusal was decided, and only the two
    together answer the question a reader actually has — whether the drift reaches the verb that
    refused. Measured on RK255: a `why.too-long` decided by `schema.py`, unchanged, arrived
    naming `cli.py`, `merging.py` and `provenance.py`, three modules that could not have decided
    it, and closing with the reader being asked to know the call graph of a refusal they did not
    raise.

    **Every** package frame and not only the deepest, because a refusal is usually raised one or
    two calls below the module that owns the rule — `Schema.validate` raising out of
    `authoring.add` is two modules that both decided it, and naming only the raiser would put the
    note back to guessing. What this still cannot see is a helper whose frame has already
    returned; §RK267 states that as the miss it accepts, and it is why the changed modules this
    does not name are kept *behind* the ones it does rather than dropped.

    Reads the traceback and nothing else — no import machinery, no `sys.modules`: the frames carry
    filenames, and a file directly under :data:`_HOME` is one of these modules by the same
    directory relation :attr:`Engine.stale` globs. Names and not paths, because that is what
    `stale` answers and the two are compared. Order is the traceback's own, so the outermost
    package frame reads first, as a printed traceback has it.
    """
    seen: list[str] = []
    frame = error.__traceback__
    while frame is not None:
        where = Path(frame.tb_frame.f_code.co_filename)
        # Not resolved first: a frame filename may be `<string>` or a path this filesystem
        # will not place, and a provenance note is the last place to start raising (`stale`'s
        # own rule). Resolution is attempted only once the name looks like ours.
        if where.suffix == ".py":
            # **Anywhere under the package**, through the same :func:`named` `stale` uses
            # (RK1069, RK1073). A check for the *parent directory* meant a `why.too-long`
            # raised in `kernel/schema.py` named nothing at all — and the note is compared
            # against `stale`, so the two spell a module one way or not at all.
            under = named(where, _HOME)
            if under and under not in seen:
                seen.append(under)
        frame = frame.tb_next
    return tuple(seen)


def witness(error: BaseException | None) -> None:
    """Record which modules decided a refusal, for the surface that will report it (RK267).

    The seam this needs and had not got. A refusal reaches the MCP server as **text**: the CLI's
    one error path prints it and returns an exit code, so by the time :mod:`roadkeep.serving` sees
    `exit 1` the exception is gone and with it the only evidence of what decided it. Passing it
    through would mean an error channel beside the exit code, which is the contract every other
    caller reads.

    So it is stated here rather than threaded: one slot, written by the path that consumes the
    exception and read by the path that composes the note. Safe for exactly the reason it looks
    unsafe — a write is serialised by RK117's lock and the server answers one message at a time,
    and the reader clears it (`witness(None)`) *before* the call it is about, so a note can never
    be attributed to an earlier refusal. Nothing else may read it: it is not a public fact about
    the process, it is one call's out-parameter.
    """
    global _WITNESSED
    _WITNESSED = None if error is None else raised_in(error)


def witnessed() -> tuple[str, ...] | None:
    """What :func:`witness` last recorded — `None` when nothing was, which is not `()` (RK267)."""
    return _WITNESSED


def read_by() -> str:
    """`— read by <engine>`, the clause a config refusal ends with (RK155, RK1150).

    Two surfaces refuse a `roadkeep.toml` and only one of them said which build was reading it.
    Over MCP that clause has been there since RK155, because a key the file declares and the code
    does not know is the shape stale code produces; at a terminal the same refusal named the file,
    the key and the allowed set — every word true, and no way to reach the real answer, since the
    one fact separating *typo* from *this engine is older* is which roadkeep is running.

    A function rather than a literal at each end: the clause is one sentence about this process,
    and two spellings of it would be two answers to a question with one.
    """
    return f" — read by {engine()}"


def invoked(argv: Sequence[str]) -> None:
    """Record the arguments this run was given, for a refusal that can offer the retry (RK1149).

    Here rather than read from `sys.argv` where it is wanted, because `sys.argv` is only the
    caller's own call at *one* of this tool's surfaces: over MCP it names the server's process
    and under pytest it names pytest. A refusal spelling a retry off that would print a command
    nobody ran — the failure mode RK254 removed from remedies, arriving through the argument
    rather than through the engine.

    One slot for :func:`witness`'s reason and under its rules: written by the surface that owns
    the invocation, read only where a refusal is being rendered, and never a public fact about
    the process. It is set **before** dispatch, so nothing can read an earlier call's argv.
    """
    global _INVOKED
    _INVOKED = tuple(argv)


def invocation_argv() -> tuple[str, ...]:
    """The argv :func:`invoked` recorded, or `()` where this surface has none."""
    return _INVOKED



#: The console script `pyproject.toml` declares, which is what a message may name only where a
#: PATH lookup finds it (RK254).
CONSOLE = "roadkeep"

#: The launcher the package ships beside itself (RK57), relative to :attr:`Engine.home`. Named
#: here because :func:`invocation` is the only reader and it is a fact about this distribution's
#: layout, not about any project.
LAUNCHER = ("scripts", "roadkeep.py")


@dataclass(frozen=True, slots=True)
class Persisted:
    """An invocation written into a file that outlives this process, and what ends it (RK255)."""

    #: The command, absolute and quoted for the shell it will be executed by.
    command: str
    #: The condition under which it stops resolving — always known, because every answer
    #: below has one and a stored command whose expiry nobody stated is one nobody re-runs.
    invalidated_by: str


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


#: The MCP server this distribution declares — the same name in both scopes, and the reason
#: the two spellings below differ only by what wraps it.
SERVER = "roadkeep"

#: The prefix a project that declares the server itself gets — the first of :func:`serving`'s
#: two answers, named because it is also the one a message built by hand means (RK488). Held
#: here and not spelled at the surface that defaults to it: two literals of one prefix is the
#: drift this module exists to remove, one scope down.
WIRED = f"mcp__{SERVER}__"

#: Where a plugin states its own name, relative to the tree that carries it.
_MANIFEST = (".claude-plugin", "plugin.json")

#: What a project declares its own servers in, relative to its root.
_PROJECT_MCP = ".mcp.json"


def serving(root: Path) -> str | None:
    """The prefix this session's roadkeep tools arrive under, or ``None`` where there are none.

    One engine, two names, each right in one scope (RK333): a **project** `.mcp.json`
    produces `mcp__roadkeep__add` — this checkout, and any project `install` wired — while a
    server a **plugin** provides arrives as `mcp__plugin_roadkeep_roadkeep__add`, measured
    against the published payload with `claude --plugin-dir <tree> -p …` from a project that
    is not this one. `Refusal` stated the first unconditionally, so in the plugin's own
    audience the route it named first was one that session cannot call — worse than the shell
    form it demotes, because that one at least fails loudly.

    **Decided by what the two scopes actually put on disk**, in the same spirit as
    :func:`invocation`: an adopting project has no `.mcp.json` and gets its tools from the
    plugin tree the engine is running out of, while a wired project has one naming this
    server. The environment is not asked — `${CLAUDE_PLUGIN_ROOT}` is substituted into a
    command line rather than exported, which `tests/test_plugin.py` measured from the other
    end — and the hook payload says which tool was denied, never which server offered it.

    **And there is a third state, which used to be answered with a guess** (RK444, RK447).
    RK333 chose the bare name wherever neither scope spoke, on the argument that it is what
    every project that ran `install` has and that naming a plugin nobody installed would be
    the same defect with the scopes swapped. That argument is sound and it is about a choice
    *between two prefixes*. A project that pip-installed roadkeep and never ran `install` has
    neither — no tools at all — and both surfaces that name a route were handing it one it
    cannot call: the notice that every session reads, and the denial that stops an edit. So
    the answer here is allowed to be ``None``, and each caller says what it does with that.
    """
    # And this branch is why `WIRED` **is** the declared case, which is a fact callers read
    # off the prefix rather than asking twice (RK1244): a project that declares the server
    # gets the bare name, and nothing else does.
    if _declared_by(root):
        return WIRED
    plugin = _plugin_name()
    return None if plugin is None else f"mcp__plugin_{plugin}_{SERVER}__"


def served_by(root: Path) -> str:
    """:func:`serving`'s answer as a **prefix to concatenate**, or `""` where none (RK488).

    One reader for the six places that carry it. Each of them wanted the same two things —
    the optional collapsed, because below there it is a string to put in front of a tool name,
    and the empty case meaning *there is no call to publish*, which is what every renderer
    already branches on — and each spelled `serving(root) or ""` for itself, which is four
    mechanisms for one fact and a fifth waiting to be written slightly differently.

    Not a second answer: the distinction :func:`serving` keeps between ``None`` and a prefix is
    real and stays there, for the caller that has to tell *this project has no server* from
    *this project's server is named so*. This is that answer for the callers that do not.
    """
    return serving(root) or ""


@lru_cache(maxsize=8)
def _declared_by(root: Path) -> bool:
    """Does this project declare the server itself? Cached per root, read once per process.

    Unreadable is *not* declared: a `.mcp.json` this cannot parse is one the session could
    not launch a server from either, so the plugin is the likelier route and a crash inside a
    hook would deny the edit and print a traceback instead of the command to run.
    """
    # Imported here and not at module level, the reason `_placed` gives: this is read on
    # the denial path alone, and every other caller of this module pays for the import.
    import json  # noqa: PLC0415

    try:
        declared = json.loads((root / _PROJECT_MCP).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    servers = declared.get("mcpServers") if isinstance(declared, dict) else None
    return isinstance(servers, dict) and SERVER in servers


@lru_cache(maxsize=1)
def _plugin_name() -> str | None:
    """The name the tree this engine runs out of publishes itself under, if it is a plugin.

    Read from the manifest rather than from the directory: a plugin is installed under a
    path the marketplace chooses, and the name in the payload is the one the manifest states.
    """
    import json  # noqa: PLC0415

    try:
        manifest = json.loads(
            engine().home.parents[1].joinpath(*_MANIFEST).read_text(encoding="utf-8")
        )
    except (OSError, ValueError, IndexError):
        return None
    name = manifest.get("name") if isinstance(manifest, dict) else None
    return name if isinstance(name, str) and name else None


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
def persisted() -> Persisted:
    """How a **stored** invocation must be spelled, and what would stop it (RK255).

    :func:`invocation` answers for a message a reader copies now. This answers for a string
    written into `.git/config`, which git executes at merge time — in a shell nobody chose,
    from a working directory this process never sees. Two of that function's three answers
    are wrong the moment they are stored: the console script is a name PATH resolves, and a
    PATH is per-shell, so a GUI client's is not the terminal's; the launcher is spelled
    relative to the working directory, and a value in `.git/config` outlives it.

    The same three answers, resolved to absolute paths, each carrying the condition that
    ends it. **Nothing here refuses.** Every machine has a last answer, and a `merge
    register` that failed on the machine most likely to want one would send its author back
    to the hand edit this tool exists to stop — so what a persisted command cannot promise
    is *stated* rather than withheld, which is the one place this tool reports after rather
    than refusing before, because the alternative reports nothing at all.

    Cached with :func:`invocation` and for the same reason: neither PATH nor this package's
    layout moves inside one process.
    """
    found = shutil.which(CONSOLE)
    if found:
        return Persisted(
            _absolute(Path(found)),
            f"the interpreter that installed {CONSOLE} being replaced or removed",
        )
    launcher = engine().home.parents[1].joinpath(*LAUNCHER)
    if launcher.is_file():
        return Persisted(
            f"python {_absolute(launcher)}",
            "a plugin update installing this package under a new directory",
        )
    return Persisted(
        "python -m roadkeep.cli",
        f"{engine().home.parent.as_posix()} not being importable from the merging repository",
    )


def _absolute(path: Path) -> str:
    """A path a stored command can hold: absolute, forward-slashed, single-quoted if spaced.

    Single quotes and not the double ones :func:`_spelled` uses, because this string is nested
    inside the double-quoted value of a `git config` argument — a second `"` there would end
    the value at the first space rather than quote the path across it.
    """
    try:
        path = path.resolve()
    except OSError:  # an unreadable cwd or a path this filesystem will not answer for
        path = path.absolute()
    shown = path.as_posix()
    return f"'{shown}'" if " " in shown else shown


@lru_cache(maxsize=2)
def engine(placed: bool = True) -> Engine:
    """Describe the copy of this package that is running. Cached: one git call per process.

    ``placed=False`` answers the two facts that cost nothing — the version and the directory
    — and leaves the commit unknown, which is the state a marketplace row with no sha already
    puts every reader in (RK1237). Measured here: `ls-files`, `rev-parse` and `status
    --porcelain` are 14, 14 and 16 ms, so a placed reading is **45 ms**, against a floor of 43
    for a whole command. That is affordable once per session and not once per write, and the
    caller that pays it per write is :func:`~roadkeep.installing.behind`, which asks unplaced
    first and only pays where the versions match.

    Two entries in the cache and not one: a process that asks both questions asks each once,
    and the cheap answer is not a cache miss for the expensive one.
    """
    home = Path(roadkeep.__file__).resolve().parent
    commit, modified = _placed(home) if placed else (None, False)
    return Engine(version=roadkeep.__version__, home=home, commit=commit, modified=modified)


def _placed(home: Path) -> tuple[str | None, bool]:
    # The package's one call to git: its timeout, its encoding and its single failure type.
    # Duplicating a `subprocess.run` here would be duplicating those three decisions.
    #
    # Imported here and not at module level (RK260): `history` reaches `backlog` and `sections`,
    # measured at 29 ms and four modules, and this is the only function in the file that asks git
    # anything. The guard imports this module for :func:`invocation`, which reads a directory —
    # so a denial paid for the git wrapper it never calls.
    from roadkeep.history import HistoryUnavailable, _run as _git  # noqa: PLC0415

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


#: Where the harness keeps the registry of installed plugins, under its config directory —
#: `CLAUDE_CONFIG_DIR` where the environment sets one, and `~/.claude` otherwise, which is
#: the same pair the harness itself resolves. Read and never written: this file is the
#: harness's, and a tool that edited it would be answering a question by changing it.
_REGISTRY = ("plugins", "installed_plugins.json")

#: The name this package is published under, matched against the registry key's `<name>@
#: <marketplace>` left half. A literal, and not configuration (L6): every other name in this
#: tool is the adopting project's, and this one is *ours* — the question being asked is which
#: copy of **this** plugin a project has, so a project that could answer it differently would
#: be answering about something else.
PLUGIN = "roadkeep"


@dataclass(frozen=True, slots=True)
class Installed:
    """The plugin copy the harness has wired to one project (RK415).

    The second of the three engines an adopting project runs, and the one no other reader in
    this package could name: the checkout answers for itself, the workflow states its ref in
    a file, and this one is a row in the harness's own registry.
    """

    version: str
    #: Where the marketplace unpacked it — the directory a hook and the MCP server run out of.
    home: Path | None
    #: The commit the marketplace recorded for that copy, or None where it recorded none.
    commit: str | None
    #: `project` or `user`, as the registry spells it: which scope wired this project to it.
    scope: str = ""

    @property
    def revision(self) -> str:
        return UNTRACKED if self.commit is None else self.commit[:7]


def installed(root: Path) -> Installed | None:
    """The plugin the harness has installed **for this project**, or None (RK415).

    Measured live: a checkout at 0.1.418 did every write in a project whose hooks ran the
    plugin at 0.1.285 — 133 versions apart, both correct on their own terms, and nothing
    anywhere said so. The facts were local the whole time; what was missing was a reader.

    Matched on the **project path** and not on the marketplace, because a project is wired to
    one copy and the question is which one judges *this* tree. Rows are the harness's own
    format, so every field is read defensively and a registry this cannot parse is None
    rather than a refusal: nothing here is worth failing a write over.

    Not cached. `engine()` is a fact about the running process and this is a fact about a
    file somebody else writes — a `/plugin update` between two calls is exactly the change
    this exists to report, and an answer decided at import would hide it.

    **The first matching row is not the answer** (RK1167). A project accumulates one row per
    install and the harness prunes the directories, not the records: measured on a corpus whose
    registry held `0.1.285` dated the 5th with no install left, and `0.1.820` dated the 13th with
    one. Returning on the first put the retired version in `engines`, which then printed the
    sentence telling the author to run `/plugin update` — after the update had landed, and
    unfollowably, since running it again writes a fourth row the same scan skips.

    So a row naming an install that is gone is a **record** and not an install (RK1166 made the
    launcher read it that way), and among the rows that do resolve the newest `lastUpdated` is
    the one the harness will load. A row naming no path keeps its claim: older harnesses wrote
    none, and dropping those would answer *no plugin* where there is one.
    """
    import json  # noqa: PLC0415

    import os  # noqa: PLC0415

    home = os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude"
    try:
        payload = json.loads(Path(home).joinpath(*_REGISTRY).read_text(encoding="utf-8"))
        wanted = root.resolve()
    except (OSError, ValueError):
        return None
    plugins = payload.get("plugins") if isinstance(payload, dict) else None
    if not isinstance(plugins, dict):
        return None
    found: list[dict[str, object]] = []
    for key, rows in plugins.items():
        if not isinstance(key, str) or key.partition("@")[0] != PLUGIN:
            continue
        for row in rows if isinstance(rows, list) else ():
            if not isinstance(row, dict) or not _is(row.get("projectPath"), wanted):
                continue
            if not isinstance(row.get("version"), str) or not row.get("version"):
                continue
            found.append(row)
    row = _loaded(found)
    if row is None:
        return None
    place = row.get("installPath")
    commit = row.get("gitCommitSha")
    return Installed(
        version=str(row["version"]),
        home=Path(place) if isinstance(place, str) and place else None,
        commit=commit if isinstance(commit, str) and commit else None,
        scope=row.get("scope") if isinstance(row.get("scope"), str) else "",
    )


def _loaded(rows: list[dict[str, object]]) -> dict[str, object] | None:
    """Which of a project's rows the harness would actually load (RK1167).

    Two readings the file already carries and the scan skipped. An `installPath` that is not
    there names an install the harness pruned, and a record of one is not one; `lastUpdated`
    orders what is left, because a project accumulates a row per install and the newest is the
    one loaded. Compared as text, which is what an ISO timestamp is written for — parsing it
    would be this reader deciding a format somebody else owns.

    Falls back to the rows as written where **none** resolves: an answer of *no plugin* about a
    project the registry names is a worse reading than a stale version, and `engines` prints the
    install directory beside the number, so a reader sees what this could not confirm.
    """
    if not rows:
        return None
    live = [one for one in rows if _present(one.get("installPath"))]
    return max(live or rows, key=lambda one: str(one.get("lastUpdated") or ""))


def _present(stated: object) -> bool:
    """Whether the install a row names is still on disk — True where it names none (RK1167).

    The same reading `hooks/roadkeep-launch.py` makes of the same field (RK1166), and stated
    twice because the two readers may not import each other: that file runs with nothing on
    `sys.path` but the standard library, which is the whole of what it is for.
    """
    if not isinstance(stated, str) or not stated:
        return True
    try:
        return Path(stated).is_dir()
    except OSError:
        return False


def _is(stated: object, wanted: Path) -> bool:
    """Whether a registry row's project path is this tree — resolved, and never as text.

    The harness writes the path the way its platform spells it, so a Windows row and a
    posix-spelled config are one project written twice and a string compare calls them two.
    """
    if not isinstance(stated, str) or not stated:
        return False
    try:
        return Path(stated).resolve() == wanted
    except OSError:
        return False
