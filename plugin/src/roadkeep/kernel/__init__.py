"""The format's mechanism: a record's shape, its identity, and a file that round-trips.

Everything above this package is *this backlog's rules* — a dependency graph, blocks, a
queue, a ledger with three doors. What is here is the half a second format could use, and
the boundary is one rule: **it imports nothing above itself**. RK1065 measured that and held
it with a test; RK1069 made it a directory, so the violation is an import that reads wrong
where it was a test somebody had to know existed.

Two allowances survive the move and are named in `tests/test_kernel.py` rather than here,
because a permission stated beside the code it excuses is one nobody counts: the projection
refresh a transaction owes (RK188), which genuinely runs the other way and is imported inside
the function that needs it, and `Config` under `TYPE_CHECKING`, which is a name for an
annotation and never a read.

**Not a distribution**, and that is a standing decision rather than a step not taken yet
(RK1065). A library is a runtime dependency and this tool's argument against taking `click`
and `pydantic` applies to itself; an abstraction designed from a single client is a framework
that client contorts into; and a supported Python API is a non-goal this collides with head
on. The internal boundary costs no release and is reversible. Publishing waits on a second
real format to prove the shape, and there is not one.

No re-exports. A shim keeping the old `roadkeep.schema` alive would erase the only thing the
move bought: a caller reaching past the boundary has to write the address that says so.
"""
