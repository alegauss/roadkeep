"""The cheap test that decides whether the expensive one loads (RK176).

RK128 widened the `PreToolUse` matcher to `Bash`, and paid the tax on an argument rather
than on a number. Measured, the harness spawns an interpreter and waits **184 ms** for it
on every shell command in a governed project, of which **148 ms** is spent before the hook
has looked at anything: 36 ms of interpreter, then 111 ms importing `roadkeep.cli` — a
hundred-odd modules, none of them dominant, because the launcher's one import pulls the
whole package. The substring tests RK128 called free are free; what was never weighed is
everything that has to exist before they can run.

So this is the exit taken *before* that import, and the shape of it is what keeps it
honest: **it never decides a refusal, only whether the decision gets made.** A `False` here
means the full guard would certainly have said nothing — a claim about the absence of any
governed path in a string, not a judgement about a write. Anything it cannot be certain of
answers `True` and pays the 148 ms, which is what makes an over-approximation safe where a
second copy of the rule would not be. `tests/test_screening.py` holds that direction: what
this skips, :func:`roadkeep.guarding.guard` allows anyway.

Three consequences of that asymmetry:

* **Every guarded tool is screened, each by its own question** (RK204). A shell command
  only *mentions* a path, so the test is a substring of the command; a write tool **names**
  the file it writes, so the test is path equality and the config is the one above that
  path rather than above `cwd`. RK176 screened only `Bash` and left `Edit` at 164 ms, which
  is the tool the guard was written for. What settles it is not how often an `Edit` names a
  governed file but what the trade costs either way: skipping saves 107 ms, and loading
  anyway costs the stat and the parse, about 2 ms — so the screen loses only where more
  than 98% of writes in a governed project go to governed files, and every one of the 638
  in this repository's history was made by a verb rather than by a write tool.
* **A project that declares no `[files]` is never screened.** `Config` supplies defaults
  for one that omits the table, and reproducing those defaults here is exactly the second
  copy this module exists not to be. So the absence of the table is an uncertainty and
  loads, which costs the full price on a configuration `init` does not write.
* **Nothing outside the standard library is imported.** `tomllib` and `pathlib` are the
  whole dependency: importing any `roadkeep` module runs the package's `__init__`, which
  RK199 then took from 23 ms to 0.6 ms — this rule is what made that worth doing.
"""

from __future__ import annotations

import json
import os
import tomllib
from pathlib import Path

#: The file a project declares itself with. Spelled here rather than imported for the reason
#: in the docstring — and asserted equal to :data:`roadkeep.config.CONFIG_NAME` by a test,
#: because a name that drifted would make this screen every payload out.
CONFIG_NAME = "roadkeep.toml"

#: The tool whose payload only *mentions* a path (RK128), answered by a substring test.
MENTIONING = ("Bash",)

#: The tools whose payload *names* the file (RK22), answered by path equality against the
#: config above that path. Held against :data:`roadkeep.guarding.WRITE_TOOLS` by a test.
NAMING = ("Edit", "MultiEdit", "NotebookEdit", "Write")

#: Both, and asserted equal to :data:`roadkeep.guarding.GUARDED_TOOLS`: a tool added to the
#: matcher and not here is one that quietly keeps paying the full price.
SCREENED = (*NAMING, *MENTIONING)

#: Where a tool's input spells the file, as `guarding._PATH_KEYS` lists them.
_PATH_KEYS = ("file_path", "notebook_path", "path")


def worth_loading(text: str, root: str | Path = ".") -> bool:
    """Whether this hook payload needs the package loaded to be answered.

    ``text`` is stdin as read, because stdin can be read once: the launcher hands over the
    string it already has rather than the stream. Every branch that is not *certain* the
    guard would stay silent returns ``True``.
    """
    try:
        payload = json.loads(text or "{}")
    except ValueError:
        return True  # not JSON, and what the guard does about that is the guard's rule
    if not isinstance(payload, dict):
        return True
    tool = payload.get("tool_name")
    if tool not in SCREENED:
        # `SessionStart` and `Stop` arrive once a session and once a turn, so the load is
        # not a tax; anything else is a tool the matcher does not send here at all.
        return True
    raw = payload.get("tool_input")
    if not isinstance(raw, dict):
        return True
    base = _cwd(payload, root)
    return _mentions(raw, base) if tool in MENTIONING else _names(raw, base)


def _mentions(raw: dict[str, object], base: Path) -> bool:
    """Whether a shell command spells a governed path anywhere in it (RK128)."""
    command = raw.get("command")
    if not isinstance(command, str) or not command:
        return True
    declared = _files(base)
    if declared is None:
        return True
    # The certain answer: no path this project declares occurs in the string at all, so
    # `guarding._mentioned` would return `None` and the guard would print nothing.
    # `normcase` for the reason `guarding._comparable_text` gives — on Windows it settles
    # the separator as well as the case, so `docs/ROADMAP.md` and a declared `docs\…` match.
    spelled = os.path.normcase(command)
    return any(
        os.path.normcase(form) in spelled
        for value, path in declared
        for form in (value, str(path))
    )


def _names(raw: dict[str, object], base: Path) -> bool:
    """Whether a write tool's payload names a governed file (RK204).

    Equality and not a substring, because the payload holds the path itself: `README.md` is
    not `docs/README.md`, and a guard that refused on containment would refuse the file
    beside the one it governs. The config is found by walking up from **that path**, which
    is `guarding.governed`'s own rule and the reason RK176 left this tool out.
    """
    targets = []
    for key in _PATH_KEYS:
        value = raw.get(key)
        if isinstance(value, str) and value:
            candidate = Path(value)
            targets.append(candidate if candidate.is_absolute() else base / candidate)
    if not targets:
        return False  # nothing to judge, which is the guard's own silence
    for target in targets:
        declared = _files(target.parent)
        if declared is None:
            return True
        wanted = _comparable(target)
        if wanted is None or any(_comparable(path) == wanted for _, path in declared):
            return True
    return False


def _comparable(path: Path) -> str | None:
    """A path as this filesystem compares them, or ``None`` where it cannot be resolved.

    `normcase` after `resolve`, exactly as `guarding._comparable` does it: on Windows
    `docs/ROADMAP.md` and `docs/roadmap.md` are one file, and a screen that missed that
    would skip the write it exists to let the guard refuse.
    """
    try:
        return os.path.normcase(str(path.resolve()))
    except OSError:
        return None


def _cwd(payload: dict[str, object], root: str | Path) -> Path:
    value = payload.get("cwd")
    return Path(value if isinstance(value, str) and value else root)


def _files(start: Path) -> tuple[tuple[str, Path], ...] | None:
    """Every governed path as declared and as resolved against the config, or ``None``.

    ``None`` and an empty tuple are different answers: no `roadkeep.toml` above ``start``
    means there is no project here and the guard is silent, while a table this cannot read
    means the question was not settled and the package should decide it.

    Both spellings, because the two screens ask different questions of them (RK204): a
    command may name the file either way and only a substring can tell, while a write tool's
    payload is one path and only equality may judge it.
    """
    found = _find(start)
    if found is None:
        return ()
    try:
        data = tomllib.loads(found.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    files = data.get("files")
    if not isinstance(files, dict) or not files:
        # `Config` fills in defaults here, and copying them would be the second rule.
        return None
    base = found.parent
    declared: list[tuple[str, Path]] = []
    for value in files.values():
        if not isinstance(value, str) or not value:
            return None
        declared.append((value, base / value))
    return tuple(declared)


def _find(start: Path) -> Path | None:
    """The nearest `roadkeep.toml` at or above ``start``, walking up as discovery does."""
    try:
        here = start.resolve()
    except OSError:
        return None
    for directory in (here, *here.parents):
        candidate = directory / CONFIG_NAME
        if candidate.is_file():
            return candidate
    return None
