"""The dependency graph, in both directions (RK13).

A blocked task and a ready one look identical on the page, and a task that unblocks half
the backlog looks exactly like one that unblocks nothing. Both are graph questions, and
an ad-hoc traversal rewritten per session is not merely expensive — it is wrong in ways
nothing checks, which is why the walk lives here with tests over the real files.

Four answers, and each one exists because collapsing it into another loses information:

* **The blocker chain.** "RK36 is blocked" is not actionable; "RK36 → RK14 → RK2, and RK2
  is ready" names the task to start. A chain ends where the walk can go no further: a
  ready blocker, an id in neither file, or work outside the backlog.
* **Transitive readiness.** Direct readiness (RK28) answers "can I start this now"; the
  closure answers "what has to happen first", which is the question a reader of a blocked
  line actually has.
* **Leverage, the reverse direction.** How many tasks a shipment unblocks *is* derivable,
  and it is the only half of prioritisation a tool may supply — value is not derivable and
  the tool does not guess at it (L4). Measured here, RK14 sits in 14 tasks' blocker sets
  and most tasks sit in none: a gap no reading of the file makes visible.
* **Cycles.** A defect, not a shape: three tasks that wait on each other are three tasks
  nothing can start. `deps` prints one; `lint` (RK14) is what will fail on it.

A block or a range dep is **expanded to its open members** before the walk, because
transitive readiness computed over a dep the traversal treats as opaque is wrong rather
than incomplete. How much work such a dep hides is its own report (RK35).
"""

from __future__ import annotations

from dataclasses import dataclass

from roadkeep.backlog import Backlog, DepStatus, Readiness, Resolution, id_order
from roadkeep.config import Config
from roadkeep.kernel.schema import Task

#: How many chains and dependents an answer carries. Bounded because the value of a query
#: is that its output fits in a tool result; the counts stay exact either way.
SHOWN = 6


@dataclass(frozen=True, slots=True)
class Hop:
    """One edge out of a task: what it waits on, and how the line named it."""

    #: The id waited on, or the dep token itself when nothing can be walked into.
    target: str
    #: The token as written — `RK5`, `Block B`, `T451–T457`, `real design partners`.
    via: str
    status: DepStatus
    #: What the resolver already said about this edge, carried where a status alone would
    #: make the chain print something false (RK432). :func:`_terminal_detail` writes three
    #: sentences from the status, and one of them — "outside the backlog: shipping cannot
    #: satisfy it" — is wrong about a label the roadmap declares and nobody has filed under,
    #: which shipping a first line under it is exactly what satisfies. Passing the
    #: resolution's own words through removes a speller rather than adding a carrier; empty
    #: everywhere the status is the whole of the answer.
    detail: str = ""

    @property
    def walkable(self) -> bool:
        """Only an open task of this project continues a chain."""
        return self.status is DepStatus.OPEN

    def __str__(self) -> str:
        return self.target if self.via == self.target else f"{self.target} (via {self.via})"


@dataclass(frozen=True, slots=True)
class Chain:
    """A path from a task to something that blocks it, and how the path ends."""

    hops: tuple[Hop, ...]
    #: Why the walk stopped: the last hop's status, or OPEN for a ready blocker.
    end: DepStatus
    detail: str

    @property
    def root(self) -> str:
        return self.hops[-1].target if self.hops else ""

    def render(self, start: str) -> str:
        return " → ".join([start, *(str(hop) for hop in self.hops)])


@dataclass(frozen=True, slots=True)
class Leverage:
    """What shipping one task would unblock, direct and transitive."""

    direct: tuple[str, ...]
    transitive: tuple[str, ...]
    #: Open tasks other than this one — the denominator that makes the count mean something.
    of: int

    @property
    def count(self) -> int:
        return len(self.transitive)


@dataclass(frozen=True, slots=True)
class Graph:
    """The backlog as edges, walked in both directions. Reads; never writes."""

    backlog: Backlog
    #: id → the hops it is waiting on. A satisfied dep is not an edge: it cannot block.
    edges: dict[str, tuple[Hop, ...]]

    @classmethod
    def load(cls, config: Config) -> Graph:
        return cls.of(Backlog.load(config))

    @classmethod
    def of(cls, backlog: Backlog) -> Graph:
        edges = {
            entry.task.id: _hops(backlog, entry.task) for entry in backlog.roadmap.entries
        }
        return cls(backlog=backlog, edges=edges)

    # -- forward: what has to happen first ---------------------------------

    def blockers(self, task_id: str) -> frozenset[str]:
        """Every task in this one's transitive blocker set, itself excluded."""
        return self.reach(task_id) - {task_id}

    def reach(self, task_id: str) -> frozenset[str]:
        """Everything walkable from here, *including* this task when a cycle returns.

        Keeping the self-reaching case is what makes :meth:`cycles` two lines rather than
        a second traversal with its own bugs.
        """
        seen: set[str] = set()
        stack = [task_id]
        while stack:
            current = stack.pop()
            for hop in self.edges.get(current, ()):
                if not hop.walkable or hop.target in seen:
                    continue
                seen.add(hop.target)
                stack.append(hop.target)
        return frozenset(seen)

    def chains(self, task_id: str) -> tuple[Chain, ...]:
        """Every blocking path, each ending where the walk can go no further.

        Bounded by :data:`SHOWN`: a backlog with a wide dep graph has combinatorially many
        paths, and a report nobody can read is the failure `deps` exists to fix.
        """
        found: list[Chain] = []
        self._walk(task_id, (), set(), found)
        return tuple(found[:SHOWN])

    def _walk(
        self, current: str, hops: tuple[Hop, ...], path: set[str], found: list[Chain]
    ) -> None:
        if len(found) >= SHOWN:
            return
        outgoing = self.edges.get(current, ())
        if not outgoing:
            if hops:
                found.append(Chain(hops, DepStatus.OPEN, "open and ready to start"))
            return
        for hop in outgoing:
            if not hop.walkable:
                found.append(
                    Chain((*hops, hop), hop.status, hop.detail or _terminal_detail(hop))
                )
                continue
            if hop.target in path or hop.target == current:
                found.append(
                    Chain((*hops, hop), DepStatus.OPEN, "a cycle: this path returns here")
                )
                continue
            self._walk(hop.target, (*hops, hop), path | {current}, found)

    # -- reverse: what shipping this would unblock -------------------------

    def leverage(self, task_id: str) -> Leverage:
        """Which open tasks have this one in their blocker set.

        Ordered by :func:`~roadkeep.backlog.id_order`, which is the one answer `pick`, `lint`
        and `--fix` sort by (RK109) — and not by the text, which put `RK10` and `RK11` ahead of
        `RK2`. Nothing read it while the whole roster was published: an unordered set spelled
        in full is the same set. RK1301 cut the roster to a handful, and a handful taken off a
        lexical sort is an arbitrary four rather than the lowest four — so the bound is what
        made the ordering a fact anybody reads.
        """
        by_id = (lambda one: id_order(one, self.backlog.config.schema))
        direct = tuple(
            sorted(
                (
                    other
                    for other, hops in self.edges.items()
                    if any(hop.target == task_id and hop.walkable for hop in hops)
                ),
                key=by_id,
            )
        )
        transitive = tuple(
            sorted(
                (
                    other
                    for other in self.edges
                    if other != task_id and task_id in self.blockers(other)
                ),
                key=by_id,
            )
        )
        return Leverage(direct=direct, transitive=transitive, of=len(self.edges) - 1)

    # -- the defect ---------------------------------------------------------

    def cycles(self) -> tuple[tuple[str, ...], ...]:
        """Every group of tasks that wait on each other, ids sorted inside each group.

        A group and not a path: a cycle is a property of the tasks, not of the node a walk
        happened to enter it from, and the same cycle reported rotated twice would read as
        two defects. Mutual reachability is the definition, so it is also the code.
        """
        looping = {node for node in self.edges if node in self.reach(node)}
        out: list[tuple[str, ...]] = []
        placed: set[str] = set()
        for node in sorted(looping):
            if node in placed:
                continue
            group = tuple(
                sorted(
                    other
                    for other in looping
                    if other == node
                    or (other in self.reach(node) and node in self.reach(other))
                )
            )
            placed.update(group)
            out.append(group)
        return tuple(out)

    def cycle_of(self, task_id: str) -> tuple[str, ...]:
        """The cycle this task is in, or an empty tuple. What `deps` reports per id."""
        return next((c for c in self.cycles() if task_id in c), ())

    # -- the answer a reader of one line wants -----------------------------

    def readiness(self, task_id: str) -> Readiness:
        entry = self.backlog.entry(task_id)
        if entry is None:
            raise KeyError(f"no open task {task_id}")
        return self.backlog.readiness(entry.task)


@dataclass(frozen=True, slots=True)
class Dependencies:
    """What one line is waiting on, and what waits on it (RK9, RK92).

    The result `deps` had none of (RK1170): the door gathered six values off a backlog and a
    graph and composed both registers from them, so neither reading had anything to be derived
    *from* — which is the shape that task is about. Nothing here is stored: :meth:`of` reads
    them together, and the two registers read this.
    """

    task_id: str
    readiness: Readiness
    resolutions: tuple[Resolution, ...]
    blockers: tuple[str, ...]
    chains: tuple[Chain, ...]
    leverage: Leverage
    #: The group nothing in can be started, where this id is in one. A defect and not a shape:
    #: printed here, failed by `lint` (RK14).
    cycle: tuple[str, ...] = ()

    @classmethod
    def of(cls, backlog: Backlog, task_id: str) -> Dependencies:
        """Every reading of one id, off one backlog. Raises `KeyError` where no line holds it."""
        entry = backlog.entry(task_id)
        if entry is None:
            raise KeyError(task_id)
        graph = Graph.of(backlog)
        return cls(
            task_id=entry.task.id,
            readiness=backlog.readiness(entry.task),
            resolutions=tuple(backlog.resolve(entry.task)),
            blockers=tuple(sorted(graph.blockers(task_id))),
            chains=tuple(graph.chains(task_id)),
            leverage=graph.leverage(task_id),
            cycle=tuple(graph.cycle_of(task_id)),
        )

    def stated(self) -> str:
        """Each dep with what became of it, then the readiness the set adds up to."""
        from roadkeep.rendering import _leverage_rows  # noqa: PLC0415 - RK260

        if not self.resolutions:
            return "\n".join(
                [f"{self.task_id}: {self.readiness} (no deps)", *_leverage_rows(self.leverage)]
            )
        width = max(len(one.dep.id) for one in self.resolutions)
        rows = [
            f"  {one.dep.id:<{width}}  {one.status:<13}{one.kind:<9}{one.detail}"
            for one in self.resolutions
        ]
        rows.append(f"{self.task_id}: {self.readiness}")
        rows += [
            f"  chain    {chain.render(self.task_id)}  — {chain.detail}"
            for chain in self.chains
        ]
        if self.cycle:
            rows.append(
                f"  cycle    {' ↔ '.join(self.cycle)}: nothing in this group can be started"
            )
        rows += _leverage_rows(self.leverage)
        return "\n".join(rows)

    def payload(self) -> dict[str, object]:
        """The same answer as data, with each chain's path spelled from this id outward."""
        return {
            "id": self.task_id,
            "readiness": str(self.readiness),
            "deps": [
                {
                    "dep": one.dep.id,
                    "kind": str(one.kind),
                    "status": str(one.status),
                    "detail": one.detail,
                }
                for one in self.resolutions
            ],
            "blockers": list(self.blockers),
            "chains": [
                {
                    "path": [self.task_id, *(hop.target for hop in chain.hops)],
                    "via": [hop.via for hop in chain.hops],
                    "end": str(chain.end),
                    "detail": chain.detail,
                }
                for chain in self.chains
            ],
            "unblocks": {
                "direct": list(self.leverage.direct),
                "transitive": list(self.leverage.transitive),
                "count": self.leverage.count,
                "of": self.leverage.of,
            },
            "cycle": list(self.cycle),
        }


def _hops(backlog: Backlog, task: Task) -> tuple[Hop, ...]:
    """One task's unsatisfied deps as edges, blocks and ranges expanded to members."""
    schema = backlog.config.schema
    out: list[Hop] = []
    for dep in task.deps:
        resolution = backlog.resolve_dep(dep)
        if resolution.satisfied:
            continue  # a shipped dep, a finished block, a range with nothing open
        kind = schema.classify_dep(dep)
        if kind.collective:
            members = backlog.expand(dep)
            out.extend(
                Hop(target=member, via=dep.id, status=DepStatus.OPEN) for member in members
            )
            if not members:
                # An unsatisfied collective dep with nothing to expand into is still an
                # edge, and this fired only for the block no heading declares (RK37). A
                # heading written before its first line expands to nothing too, and so does
                # one whose every line is in the store (RK432) — and dropping the edge left
                # the dependent with a verdict and no chain under it at all. The token is
                # the terminal, carrying the status and the sentence that say why the walk
                # ends there.
                out.append(
                    Hop(
                        target=dep.id,
                        via=dep.id,
                        status=resolution.status,
                        detail=resolution.detail,
                    )
                )
            continue
        out.append(Hop(target=dep.id, via=dep.id, status=resolution.status))
    return tuple(out)


def _terminal_detail(hop: Hop) -> str:
    """The sentence a status alone implies, for the hops that carry none of their own.

    Kept beside :attr:`Hop.detail` rather than replaced by it: a task dep's terminal hop is
    one id and the status is the whole answer, so composing a second sentence per edge would
    be words nobody reads. A collective token is where that stops holding, and there the
    resolution's own words travel with the hop (RK432).
    """
    if hop.status is DepStatus.UNKNOWN:
        return "in neither the roadmap nor the changelog"
    if hop.status is DepStatus.DEFERRED:
        # The one terminal end that is not terminal (RK92): the walk stops because the
        # store holds no deps to follow, and saying "shipping cannot satisfy it" would
        # name the chain unresolvable when what it needs is a `resume`.
        return "set aside in the deferred store: a resume ends this chain"
    return "outside the backlog: shipping cannot satisfy it"
