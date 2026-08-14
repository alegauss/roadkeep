"""Running the report back, so a clean tree costs one call instead of one per finding (RK422).

RK420 made the remedy a fact; this is the verb that spends it. Without one, a caller holding
eight findings composes eight command lines, makes eight tool calls and gets eight chances to
mistype a flag — which is the cost that task *measured* and did not remove. An agent pays it
in turns, and a turn is the unit this whole tool is trying to save.

**Three classes, and only the first two are run.** The mechanical pass (`--fix`) goes first,
unchanged and reused rather than reimplemented, because a normalizer written twice is two
normalizers to keep in step. Then every finding whose remedy is a complete argv is executed
in the order the report gives. What is left — a title to write, a sentence to shorten, a
choice between two doors — is *printed*, because that is where the caller's judgement was
always required and where L4 says the tool stops. The exit code stays the gate's: 0 when the
tree came back clean, 1 when a decision is still outstanding.

**One repair per pass, and the report re-read between them.** This is the decision that makes
the verb correct rather than merely convenient. Half the remedies address a line by number —
`record drop <id> --line 275` — and the first write moves every line after it, so a batch
computed from one report and applied in sequence would address the file as it *was* from the
second command on. Re-linting after each write costs a parse per repair and buys the property
that every argv is derived from the tree it runs against. A repair that leaves the report
unchanged ends the loop: no progress is the one state a retry cannot improve, and it is also
what stops a rule that reports what its own remedy writes from spinning.

**`--dry-run` prints and runs nothing**, for two reasons that point the same way. A verb that
rewrites four governed files unasked is the opposite of a barrier; and the printed list is
itself the answer for a caller who wants to read before it acts, which is the same argument
`install --check` and `adopt` are built on.

The runner is **injected** rather than imported. `repair` executes roadkeep's own subcommands,
which live in :mod:`roadkeep.cli`, which imports this module — so the dependency is passed in
at the call site and this file stays a thing the tests can drive with a recording stub.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from .config import Config
from .fixing import Fix, fix
from .linting import Finding, Report, lint
from .remedying import Door, Remedy, remedy

#: The bound on the loop. Not a budget — a backstop. Progress is what actually ends the loop
#: (a pass that changes nothing stops it), and this only decides what happens if a repair and
#: a rule ever disagree forever. High enough that no honest backlog reaches it, low enough
#: that the disagreement surfaces as a report rather than as a hung process.
MAX_PASSES = 200


@dataclass(frozen=True, slots=True)
class Step:
    """One command this run executed, or would have."""

    code: str
    where: str
    argv: tuple[str, ...]
    what: str
    #: The command's own exit code. ``None`` under `--dry-run`, where nothing was run.
    exit: int | None = None

    @property
    def ok(self) -> bool:
        return self.exit in (0, None)

    def __str__(self) -> str:
        mark = "would" if self.exit is None else ("ran  " if self.ok else "FAILED")
        return f"{mark}  {' '.join(self.argv)}  — {self.what}"


@dataclass(frozen=True, slots=True)
class Left:
    """One finding this run did not close, and what it is waiting for."""

    finding: Finding
    remedy: Remedy | None

    def __str__(self) -> str:
        if self.remedy is None:
            # The state RK421's test exists to make impossible. Printed rather than hidden:
            # a finding with no door is a defect in this tool, and saying so is how it gets
            # reported instead of worked around.
            return f"{self.finding}\n    no remedy is declared for {self.finding.code}"
        return f"{self.finding}\n" + "\n".join(
            f"    {line}" for line in str(self.remedy).splitlines()
        )


@dataclass(frozen=True, slots=True)
class Repaired:
    """What one run did, what it could not do, and whether the gate passes now."""

    steps: tuple[Step, ...] = ()
    left: tuple[Left, ...] = ()
    applied: Fix = field(default_factory=Fix)
    passes: int = 0
    clean: bool = False
    dry_run: bool = False
    #: Set when the loop stopped on :data:`MAX_PASSES` rather than on running out of work.
    exhausted: bool = False

    @property
    def failed(self) -> tuple[Step, ...]:
        return tuple(step for step in self.steps if not step.ok)

    def stated(self, root: str) -> str:
        """What ran, what is left, and the two numbers that are not one (RK422, RK471).

        Beside :meth:`payload` since RK1170. Runs and attempts are counted apart: this counted
        the steps, so a run that dispatched three and had two refused closed with `3 repair(s)
        ran` three lines under two the same output had already marked `FAILED` — and the count
        is the line a person acts on, so a caller read `3 ran` against `34 left` and concluded
        the tree moved three findings closer when it moved one. `Step.ok` already separates
        them at the point they are decided; only the sum did not ask.

        The exit code is untouched and stays 1 while anything is left: two refusals are not a
        failure of `repair`, whose whole design is that what it cannot close it prints.
        """
        from roadkeep.rendering import _tree  # noqa: PLC0415 - RK260

        rows = self.applied.stated()
        rows += [str(step) for step in self.steps]
        rows += [str(left) for left in self.left]
        verb = "would run" if self.dry_run else "ran"
        ran = len(self.steps) - len(self.failed)
        refused = f", {len(self.failed)} refused" if self.failed else ""
        rows.append(
            f"{ran} repair(s) {verb}{refused}, {len(self.left)} left for you{_tree(root)}"
        )
        return "\n".join(rows)

    def warnings(self) -> list[str]:
        """What this run has to say on **stderr**: a pass that wrote nothing, and a loop that
        stopped on its own ceiling rather than on running out of work."""
        rows = self.applied.refusals()
        if self.exhausted:
            rows.append(
                f"roadkeep: stopped after {MAX_PASSES} repairs with work still reported: a "
                f"rule and its own remedy disagree, which is a defect in this tool"
            )
        return rows

    def payload(self, root: str, served: str = "") -> dict[str, object]:
        return {
            "root": root,
            "clean": self.clean,
            "dry_run": self.dry_run,
            "passes": self.passes,
            "exhausted": self.exhausted,
            "steps": [
                {
                    "code": step.code,
                    "where": step.where,
                    "argv": list(step.argv),
                    "what": step.what,
                    "exit": step.exit,
                }
                for step in self.steps
            ],
            "left": [
                {
                    "code": left.finding.code,
                    "where": left.finding.where,
                    "message": left.finding.message,
                    **(
                        {}
                        if left.remedy is None
                        else {"remedy": left.remedy.payload(served)}
                    ),
                }
                for left in self.left
            ],
        }


def repair(
    config: Config,
    run: Callable[[Sequence[str]], int],
    *,
    dry_run: bool = False,
) -> Repaired:
    """Close every finding that has a runnable remedy; report the rest.

    ``run`` takes an argv without the program name and returns its exit code — the CLI
    passes its own dispatcher, and a test passes a stub that records.
    """
    if dry_run:
        # One read and no loop: nothing is written, so every later pass would report the
        # same file. What comes back is the list in report order — what this would do, not
        # a simulation of what each one would then reveal.
        report = lint(config)
        return Repaired(
            steps=tuple(_mechanical(report, config) + _every(report, config)),
            left=tuple(
                Left(finding, remedy(finding, config))
                for finding in report.findings
                if not _taken(finding, config)
            ),
            passes=0,
            clean=report.clean,
            dry_run=True,
        )

    applied = fix(config)
    steps: list[Step] = []
    passes = 0
    #: Every argv already attempted. A command that ran and left its own finding standing is
    #: not retried: the second attempt writes the same bytes, and the loop would become the
    #: retry loop this verb exists to remove, one level up.
    tried: set[tuple[str, ...]] = set()
    exhausted = False

    while passes < MAX_PASSES:
        step = _next(lint(config), config, tried)
        if step is None:
            break
        passes += 1
        tried.add(step.argv)
        steps.append(Step(step.code, step.where, step.argv, step.what, run(step.argv)))
    else:
        exhausted = True

    # Everything still standing is left over, and no second rule is needed to say which:
    # the loop only stopped because nothing runnable remained, so a finding here either
    # never had a door or had one that ran and did not close it.
    final = lint(config)
    return Repaired(
        steps=tuple(steps),
        left=tuple(
            Left(finding, remedy(finding, config)) for finding in final.findings
        ),
        applied=applied,
        passes=passes,
        clean=final.clean and not applied.refused,
        exhausted=exhausted,
    )


def _next(report: Report, config: Config, tried: set[tuple[str, ...]]) -> Step | None:
    """The first finding in this report with a complete argv nothing has attempted yet."""
    for step in _every(report, config):
        if step.argv not in tried:
            return step
    return None


def _every(report: Report, config: Config) -> list[Step]:
    """Every finding in this report whose remedy is one command, in report order."""
    steps: list[Step] = []
    seen: set[tuple[str, ...]] = set()
    for finding in report.findings:
        door = _door(finding, config)
        # Deduplicated, because several findings can share one remedy — five stale README
        # counts are one `export`, and running it five times is four writes of the same bytes.
        if door is None or door.argv in seen:
            continue
        seen.add(door.argv)
        steps.append(Step(finding.code, finding.where, door.argv, door.what))
    return steps


def _mechanical(report: Report, config: Config) -> list[Step]:
    """The normalizing pass, as one step, where this report has anything for it.

    A real run calls :func:`~roadkeep.fixing.fix` before the loop and never reaches here.
    The dry run has to state it anyway and has to state it *once*: listing `lint --fix`
    under each of nine character findings is the report the mechanical class was folded
    into a summary line to avoid (RK420), arriving through the verb built to shorten it.
    """
    for finding in report.findings:
        found = remedy(finding, config)
        if found is not None and found.kind == "fix":
            door = found.doors[0]
            return [Step("(mechanical)", finding.file, door.argv, door.what)]
    return []


def _taken(finding: Finding, config: Config) -> bool:
    """Whether a dry run would close this one, by either of the two passes it lists."""
    found = remedy(finding, config)
    return found is not None and found.kind in ("fix", "run") and found.runnable


def _door(finding: Finding, config: Config) -> Door | None:
    """The one complete command that closes this finding, where there is exactly one.

    `fix` is excluded because the pass at the top of :func:`repair` already ran it, and
    `compose` and `decide` are excluded because both are the caller's — the first needs a
    sentence the tool may not write (L4), the second a choice it may not make.
    """
    found = remedy(finding, config)
    if found is None or found.kind != "run" or not found.runnable:
        return None
    return found.doors[0]
