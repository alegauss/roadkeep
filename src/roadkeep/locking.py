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
  release is an unusable checkout. There is no portable way to ask whether a pid is alive,
  so abandonment is judged by **age**: past :data:`STALE` seconds the lock is reaped and the
  waiter proceeds. The wait is much shorter than that, deliberately — a caller learns in
  seconds that the checkout is busy, and only a lock old enough that no command could still
  be running is taken away from whoever left it.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
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
    Names the file, because a lock whose holder died is deleted by hand in the one case the
    age rule is too slow for.
    """

    def __init__(self, path: Path, holder: str = "") -> None:
        self.path = path
        self.holder = holder
        who = f" ({holder})" if holder else ""
        super().__init__(
            f"another roadkeep process is writing to this checkout{who} and did not "
            f"release its lock within {WAIT:.0f}s — re-run the command, or delete "
            f"{path} if nothing is running"
        )


def lock_path(root: Path | str) -> Path:
    """Where this checkout's lock lives — outside it, keyed by its resolved path.

    In the temp directory and not in the repository, because a file the tool creates in a
    project's root is a file every adopting project has to add to its `.gitignore` before
    the first `git status` reads as dirty. Keyed by the *resolved* root so two checkouts of
    one project lock independently — which is the scope the defect has: two agents in one
    working tree. The digest carries the directory's name in front of it so a human looking
    at a temp directory can tell which project the file belongs to.
    """
    resolved = Path(root).resolve()
    digest = hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"roadkeep-{resolved.name}-{digest}.lock"


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
            if _abandoned(target):
                _reap(target)
                continue
            if time.monotonic() >= deadline:
                raise LockBusy(target, _holder(target)) from None
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
