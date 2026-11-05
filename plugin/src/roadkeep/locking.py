"""Serialising the write path, so an id is spent by whoever minted it (RK117).

`next_id` (RK4) is *derived* — one past the highest id anywhere — and that is right: a
counter file would be a second source of truth, and it would drift the first time somebody
edited the roadmap by hand. What was missing is that the answer is computed at one moment
and spent at another. Two agents adding in the same checkout both scan a tree whose highest
is RK115, are both told RK116, and both write it.

So what is made indivisible here is **the whole span from scan to save**, not the scan.
A mutating command reads its own inputs and lives for milliseconds, so putting every one of
them behind a single exclusive lock costs nothing measurable and closes the window entirely.
The query surface never takes it, which is what keeps `pick` and `brief` answering during a
write — and what keeps `guard` (RK22), which runs before every write in the session, from
waiting on the write it was called about.

Three things this is not:

* **Not a second store (L2).** It holds no fact about any task: it is transient, it lives
  outside the repository entirely, and deleting it while nothing is running loses nothing.
* **Not a promise about other writers.** A lock orders the processes that agree to take it.
  An editor, a `git checkout` or a hand edit takes nothing — those are :class:`StaleFile`'s
  subject (RK116), and the two mechanisms are complementary rather than alternatives.
* **Not waited on forever.** The holder may have been killed, and a lock nobody will ever
  release is an unusable checkout. So the holder's pid is asked first (RK1719): a holder
  that is not running is reaped at once and the caller is told so — `os.kill(pid, 0)` on
  POSIX, `OpenProcess` and `GetExitCodeProcess` through `ctypes` on Windows, where
  `os.kill` would terminate the process it asks about. Where that answer is unknown (no
  permission, no pid in the file) abandonment is judged by **age**: past :data:`STALE`
  seconds the lock is reaped and the waiter proceeds. The wait is much shorter than that,
  deliberately — a caller learns in seconds that the checkout is busy, and only a lock old
  enough that no command could still be running is taken away from a holder that may live.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import re
import sys
import tempfile
import time
from collections.abc import Iterator
from pathlib import Path

#: How long a lock may be held before it is read as abandoned rather than held. Three
#: orders of magnitude above what a mutating command takes, because reaping a lock somebody
#: still holds is the one failure worse than waiting — it hands two writers one checkout,
#: which is the defect rather than the fix.
STALE = 60.0
#: How long a command waits before it refuses. Far **below** :data:`STALE`, and the gap is
#: the whole design: a waiter that gave up only when it was also entitled to reap would
#: never refuse at all, and would steal the lock of every command slower than it expected.
#: So a busy checkout is reported in seconds, and an abandoned one is cleared in a minute.
WAIT = 5.0
#: How often the waiter looks. Small enough that ordinary contention is invisible.
POLL = 0.05

#: How many times this process has taken the lock. `report` and `replay` re-enter
#: :func:`roadkeep.cli.main` in the same process to run the command they are about (RK85),
#: and a lock that deadlocked on that would make the capture tool unusable against exactly
#: the commands worth capturing. Re-entrant here rather than remembered at those two call
#: sites, because the hazard is a property of the lock and not of its callers.
_depth = 0


class LockBusy(RuntimeError):
    """Another roadkeep process is writing to this checkout and did not finish (RK117).

    Reported and never worked around: proceeding is the duplicate id this exists to stop.
    Raised only about a holder that is running or could not be asked, since a dead one is
    reaped before this is reached (RK1719) — so it says how long the lock has been held and
    when the age rule would take it, which is the answer to *wait, or delete it?*
    """

    def __init__(self, path: Path, holder: str = "", held: float | None = None) -> None:
        self.path = path
        self.holder = holder
        self.held = held
        who = f" ({holder})" if holder else ""
        age = (
            f"; it has held the lock {held:.0f}s and is read as abandoned at {STALE:.0f}s"
            if held is not None
            else ""
        )
        super().__init__(
            f"another roadkeep process is writing to this checkout{who} and did not "
            f"release its lock within {WAIT:.0f}s{age} — re-run the command, or delete "
            f"{path} if nothing is running"
        )


def sidecar(root: Path | str, suffix: str) -> Path:
    """One transient file belonging to this checkout, living outside it.

    In the temp directory and not in the repository, because a file the tool creates in a
    project's root is a file every adopting project has to add to its `.gitignore` before
    the first `git status` reads as dirty. Keyed by the *resolved* root so two checkouts of
    one project are independent — which is the scope the defect has: two agents in one
    working tree. The digest carries the directory's name in front of it so a human looking
    at a temp directory can tell which project the file belongs to.

    Shared with :mod:`roadkeep.storing` (RK330) rather than copied: two transient files keyed
    by one checkout through two digests would be two answers to "which project is this", and
    the one that drifts is whichever was written second. This is what the lock has in common
    with the store and all it has — its own state is the *existence* of a file, which is the
    one thing both platforms make atomic, and a lock that had to be parsed to be taken would
    be a lock with the race in it that this module exists to close.
    """
    resolved = Path(root).resolve()
    digest = hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"roadkeep-{resolved.name}-{digest}.{suffix}"


def lock_path(root: Path | str) -> Path:
    """Where this checkout's lock lives — outside it, keyed by its resolved path."""
    return sidecar(root, "lock")


@contextlib.contextmanager
def exclusive(root: Path | str) -> Iterator[Path]:
    """Hold this checkout's write lock for the whole of a mutating command.

    Around the *command* and not around the write, which is the only placement that helps:
    the id is decided by a scan at the start and spent by a save at the end, and a lock
    taken between them would be held for the half of the span that was never in doubt.
    """
    global _depth
    target = lock_path(root)
    if _depth:
        # Already ours. Nothing to claim and — crucially — nothing to release either, or
        # the inner command would hand the outer one's lock to whoever is waiting.
        _depth += 1
        try:
            yield target
        finally:
            _depth -= 1
        return

    token = _claim(target)
    _depth = 1
    try:
        yield target
    finally:
        _depth = 0
        _release(target, token)


def _claim(target: Path) -> str:
    """Create the lock exclusively, waiting for one that is held and reaping one that is not.

    `O_CREAT | O_EXCL` is the whole mechanism: it is one atomic syscall on both POSIX and
    Windows, so two processes reaching it together produce exactly one winner. Nothing here
    reads the file to decide — a check followed by a create is the race this replaces.
    """
    token = _token()
    deadline = time.monotonic() + WAIT
    while True:
        try:
            handle = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            holder = _holder(target)
            if _alive(_pid(holder)) is False:
                # Gone, so nothing can still be writing: reaped now rather than waited on for
                # the minute the age rule would take, and said, because a lock vanishing
                # under a caller is a thing to know happened.
                _reap(target)
                sys.stderr.write(
                    f"roadkeep: took the write lock {holder or 'left'} held, whose process "
                    f"is no longer running\n"
                )
                continue
            if _abandoned(target):
                _reap(target)
                continue
            if time.monotonic() >= deadline:
                raise LockBusy(target, holder, _age(target)) from None
            time.sleep(POLL)
            continue
        with os.fdopen(handle, "w", encoding="utf-8") as writer:
            writer.write(token)
        return token


def _token() -> str:
    """What is written into the lock: enough to name the holder, and to recognise it later.

    The pid alone would be ambiguous across a reap — a reaped lock retaken by a process that
    happens to reuse the pid would be released by the wrong one. The claim time makes it
    unique in practice, and it is the thing a reader most wants to see anyway.
    """
    return f"pid {os.getpid()} at {time.time():.6f}\n"


def _holder(target: Path) -> str:
    """What the lock says about who holds it, or nothing if it cannot be read."""
    try:
        return target.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


#: The pid a token names, as :func:`_token` spells it.
_PID = re.compile(r"^pid (\d+) at ")


def _pid(holder: str) -> int | None:
    found = _PID.match(holder)
    return int(found.group(1)) if found else None


def _alive(pid: int | None) -> bool | None:
    """Whether a process with this pid is running: True, False, or None where it cannot tell.

    None is the answer that keeps the age rule, so this only ever shortens a wait. Never
    `os.kill` on Windows — there it terminates the process rather than asking about it.
    """
    if pid is None or pid <= 0:
        return None
    if pid == os.getpid():
        return True
    if os.name == "nt":
        return _alive_windows(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # it exists, and belongs to somebody else
    except OSError:
        return None
    return True


def _alive_windows(pid: int) -> bool | None:
    import ctypes  # noqa: PLC0415 - Windows only, and stdlib
    from ctypes import wintypes  # noqa: PLC0415

    query = 0x1000  # PROCESS_QUERY_LIMITED_INFORMATION
    still_active = 259
    invalid_parameter = 87  # no process has this pid
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        handle = kernel32.OpenProcess(query, False, pid)
        if not handle:
            return False if ctypes.get_last_error() == invalid_parameter else None
        try:
            code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return None
            return code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    except (OSError, AttributeError):
        return None


def _age(target: Path) -> float | None:
    """How long the lock on disk has existed, or None if it is gone."""
    try:
        return max(0.0, time.time() - target.stat().st_mtime)
    except OSError:
        return None


def _abandoned(target: Path) -> bool:
    """Is this lock older than any command that could still be running?

    False when the file is gone: it was released or reaped between the failed create and
    this call, and the caller's next attempt is the one that finds out.
    """
    try:
        return time.time() - target.stat().st_mtime > STALE
    except OSError:
        return False


def _reap(target: Path) -> None:
    with contextlib.suppress(OSError):
        target.unlink()


def _release(target: Path, token: str) -> None:
    """Give up the lock, but only while it is still the one this process took.

    The check matters because reaping exists: a holder slow enough to be declared abandoned
    would otherwise delete the lock of whoever reaped it, and hand a third process a
    checkout two are writing to. Reading before unlinking leaves a window of microseconds
    where that is still possible; what it removes is the case where it is *certain*.
    """
    try:
        if target.read_text(encoding="utf-8") == token:
            target.unlink()
    except OSError:
        pass
