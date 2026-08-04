"""Which governed bytes a verb actually left, so an approved shell write is recorded (RK175).

RK128 closed the *silence* at the shell boundary: a `Bash` command naming a governed path is
surfaced and the user answers. What it could not close is what happens after they say yes.
`review` (RK60) then runs `lint` narrowed to the lines the turn changed, and a hand-edit
producing a **conforming** line passes every one of those checks — the annotations are right
because nothing was inserted, the pointer resolves because the anchor existed, and a reworded
`why` is a legal `why`. The file changed, no verb wrote it, and every gate agrees it is correct.

RK128's third option was to compare the governed files against `git` and refuse a change no
verb made. That is not what this does, for the reason the option was left open: a user who
approved a `sed` made a choice, and re-litigating it at the end of the turn spends the
approval the `ask` exists to collect. The defect in the symptom is narrower and it is real —
**no record of who wrote it** — so what is built is the record, not a second refusal.

The mechanism is one digest per governed file, taken where every write already passes:

* **The baseline is the last verb, not `HEAD`.** Against `HEAD` this would report the whole
  turn's legitimate work — every `add` and every `ship` — and a report that fires on the
  normal path is one nobody reads. Against what the last verb left, the only thing that
  differs is bytes that arrived some other way, which is exactly the claim being made.
* **Recorded in :func:`roadkeep.cli.dispatch`, under the lock.** One choke point, and the
  one both surfaces share: the MCP server dispatches parsed args in-process and never goes
  through `main` (RK24), so a record kept anywhere else is one the write path walks around.
  A query never attests, which is what keeps a `list` between two hand-edits from silently
  adopting the second one as the baseline.
* **Not a second store (L2), and not a lock.** It holds no fact about any task: it is a
  digest, it lives in the temp directory beside the write lock (RK117) and the claim
  registry (RK119) under the same resolved-root key, and deleting it while nothing is
  running loses nothing — every file simply reads as attested until the next verb runs.

Two rules that keep it honest. **Every failure is silence**, on the guard's own argument
(:mod:`roadkeep.guarding`): an unreadable sidecar must not block a turn, and `lint` still
judges the file. And **reporting re-baselines** — the current bytes become the new record —
so one unattested change is stated once and the turn ends on the next attempt, rather than
the same fact blocking every turn until somebody commits.

What this cannot say is *who*. There is no owner here for the same reason there is none on a
claim: the identity behind a write lives outside the repository, and the commit is where it
belongs. The claim made is only that the bytes were not put there by a verb.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from roadkeep.config import Config
from roadkeep.locking import sidecar
from roadkeep.provenance import invocation

#: The sidecar's suffix, beside `.lock` and the claim registry and keyed by the same resolved
#: root — a third way of spelling "this checkout" is a third answer that can drift (RK117).
SUFFIX = "writes"


@dataclass(frozen=True, slots=True)
class Unattested:
    """The governed files whose current bytes no verb wrote."""

    #: Role and path, as this project spells it — a report quoting an absolute path is a
    #: report about one machine.
    files: tuple[tuple[str, str], ...]

    def __str__(self) -> str:
        named = ", ".join(path for _, path in self.files)
        plural = "s" if len(self.files) > 1 else ""
        return "\n".join(
            [
                f"{named} changed since the last roadkeep verb wrote {'them' if plural else 'it'}, "
                f"so whatever produced the current bytes was not one — an approved shell "
                f"command, an editor, or a checkout. The line{plural} may be perfectly valid; "
                f"what was missing is any record of who wrote {'them' if plural else 'it'}, "
                f"and this is that record.",
                "",
                "Nothing is undone and nothing is asked back: the approval stands. Say which "
                "command changed the file and end the turn again — this blocks once, and the "
                "bytes that are there now are the new baseline.",
                "",
                f"`{invocation()} lint` judges the format; the verbs that write it are in "
                f"the refusal every governed edit already prints.",
            ]
        )


def attest(config: Config) -> None:
    """Record every governed file as the verb that just ran left it.

    Called for its effect and never for an answer, so it raises nothing: a temp directory
    that cannot be written is a missing record, not a failed write.
    """
    _store(config, _digests(config))


def unattested(config: Config) -> Unattested | None:
    """The governed files whose bytes differ from what the last verb left, or ``None``.

    Silence where nothing was ever recorded: a checkout in which no verb has run this
    session has no baseline to differ from, and reporting every file in it would report the
    history the project arrived with rather than anything this turn did.
    """
    recorded = _recorded(config)
    if not recorded:
        return None
    current = _digests(config)
    found = tuple(
        (role, config.relative(path))
        for role, path in config.paths.items()
        if role in recorded and recorded[role] != current.get(role)
    )
    if not found:
        return None
    _store(config, current)
    return Unattested(files=found)


def record_path(root: Path | str) -> Path:
    """Where this checkout's digests live — outside it, keyed by its resolved path."""
    return sidecar(root, SUFFIX)


def _digests(config: Config) -> dict[str, str | None]:
    """One digest per declared role, ``None`` for a file that is not on disk.

    Absence is a value and not a gap: a governed file *deleted* by a shell command is the
    change this most wants to state, and a dictionary that simply omitted it would read as
    agreement with whatever was recorded before.
    """
    out: dict[str, str | None] = {}
    for role, path in config.paths.items():
        try:
            out[role] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        except OSError:
            out[role] = None
    return out


def _recorded(config: Config) -> dict[str, str | None]:
    try:
        data = json.loads(record_path(config.root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        role: value
        for role, value in data.items()
        if isinstance(role, str) and (value is None or isinstance(value, str))
    }


def _store(config: Config, digests: dict[str, str | None]) -> None:
    try:
        record_path(config.root).write_text(
            json.dumps(digests, indent=2, sort_keys=True), encoding="utf-8"
        )
    except OSError:
        return
