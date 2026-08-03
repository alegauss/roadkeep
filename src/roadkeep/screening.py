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

* **Only `Bash` is screened.** It is the tool RK128 added and the one this is about; a
  write tool names its file, arrives far less often, and would need the config discovered
  from the *path* rather than from `cwd`. Loading for those costs a correctness argument
  nothing here is buying.
* **A project that declares no `[files]` is never screened.** `Config` supplies defaults
  for one that omits the table, and reproducing those defaults here is exactly the second
  copy this module exists not to be. So the absence of the table is an uncertainty and
  loads, which costs the full price on a configuration `init` does not write.
* **Nothing outside the standard library is imported.** `tomllib` and `pathlib` are the
  whole dependency: importing any `roadkeep` module runs the package's `__init__`, and that
  alone is 23 ms of the budget this is trying to spend.
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

#: The one tool screened, and the one RK128 added. Held against
#: :data:`roadkeep.guarding.ASK_TOOLS` by a test, so widening that set again is a failure
#: here rather than a hole that quietly keeps paying.
SCREENED = ("Bash",)


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
    if payload.get("tool_name") not in SCREENED:
        # Every other event — a write tool, `SessionStart`, `Stop` — is either rare enough
        # that 148 ms is not a tax or needs a config this cannot discover from `cwd`.
        return True
    command = _command(payload)
    if command is None:
        return True
    declared = _declared(_cwd(payload, root))
    if declared is None:
        return True
    # The certain answer, and the only one this module makes: no path this project declares
    # occurs in the string at all, so `_mentioned` would return `None` and the guard would
    # print nothing. `normcase` for the reason `guarding._comparable_text` gives — on
    # Windows it settles the separator as well as the case.
    spelled = os.path.normcase(command)
    return any(form in spelled for form in declared)


def _command(payload: dict[str, object]) -> str | None:
    raw = payload.get("tool_input")
    if not isinstance(raw, dict):
        return None
    command = raw.get("command")
    return command if isinstance(command, str) and command else None


def _cwd(payload: dict[str, object], root: str | Path) -> Path:
    value = payload.get("cwd")
    return Path(value if isinstance(value, str) and value else root)


def _declared(start: Path) -> tuple[str, ...] | None:
    """Every spelling of every governed path, or ``None`` where certainty ran out.

    ``None`` and an empty tuple are different answers: no `roadkeep.toml` above ``start``
    means there is no project here and the guard is silent, while a table this cannot read
    means the question was not settled and the package should decide it.
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
    forms: list[str] = []
    for value in files.values():
        if not isinstance(value, str) or not value:
            return None
        forms.append(os.path.normcase(value))
        forms.append(os.path.normcase(str(base / value)))
    return tuple(forms)


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
