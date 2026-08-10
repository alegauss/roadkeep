"""One module per verb family, and where a handler lives is what its verb does (RK494).

`cli.py` grew to 8,489 lines holding the parser, the handlers and every printer. RK493 took
the printers; this takes the handlers, which were the part with no name — each reached
through `set_defaults(handler=…)` and grouped by nothing, so 82 concepts shared one
docstring while every other module in the package is one gerund its own docstring is the
authority on.

The names are the domain modules' own, and where a handler lives is derived from what its
verb does: the command that writes a task line sits in :mod:`roadkeep.verbs.authoring`,
beside the module it calls. Two more hold what a verb needs before it has an answer —
:mod:`roadkeep.verbs.refusing` for the exit codes and the one translation of a raised error
into one, and :mod:`roadkeep.verbs.reading` for the prose that arrives on a pipe or a path.

The import direction is `build_parser` importing these, never the other way, which is why
RK493 was a dep: a handler still reaching a printer left in `cli.py` would import the module
that imports it. Two of them genuinely need the parser — `repair` runs whole commands back
through it and `merge` names the flag its own parser declared — and both take it through a
function-level import, which is how :mod:`roadkeep.serving` and :mod:`roadkeep.capturing`
already reach the same two names.

What did not move, and why this is a split and not a rewrite: `build_parser` stays one
function, because :mod:`roadkeep.serving` derives every MCP tool, its description and its
stdin declaration from that one object; and `dispatch` stays one, because RK489's rule is
that one place refuses two answers.
"""
