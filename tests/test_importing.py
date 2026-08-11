"""An import list is an answer, so nothing in it may be unspelled (RK1020).

A module's imports are what a reader asks it what it needs, and this package argues about
that answer more than most: the deferred imports RK260 argues for, the one-way edge `verbs/`
was split to keep, the two modules `test_configured` exempts because a default is declared
there. Every one of those arguments is read off an import list, and a name nobody spells
makes the list a false answer without breaking anything — which is why they accumulate.

Nothing reported one before this, and nothing could: this tree has no linter and takes no
dev dependency that would bring one, which is the same decision it makes about runtime
dependencies and for the same reason. So the check is here, over the set `surface.py`
declares, with the shape `test_configured` gave the scan that holds L6.

**The two exclusions, and why each is not a judgement.**

*`__all__`.* A re-export is a module's own statement of what it publishes, so the name is
used by being listed — `budgeting`'s `CHARS_PER_WORD` and `shipping`'s `Wrapped` are both
live instances, which is what keeps this from being an exemption nobody needs.

*`__future__`.* `from __future__ import annotations` binds nothing a reader could spell; it
is a compiler directive wearing an import's syntax. Every module here carries it, so without
this the scan reports fifty-nine hits and is the red nobody keeps.

Anything else is either spelled or it is not, which an AST decides without judgement. What
the first run found: six names across four modules — `guarding`, `linting`, `remedying` and
`shipping` — imported and never spelled again, gone in the commit that added this.
"""

from __future__ import annotations

import ast

from surface import modules

#: The one module whose imports bind nothing: a `__future__` statement is a directive to the
#: compiler, and the name it appears to bind is never a name a reader could spell.
DIRECTIVE = "__future__"


def _bound(tree: ast.Module) -> list[tuple[int, str]]:
    """Every name an import statement binds, with the line that binds it.

    `import a.b` binds `a`, `import a.b as c` binds `c`, and `from x import *` binds a set
    the AST does not know — the last is skipped rather than guessed at, and none exists here.
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if getattr(node, "module", None) == DIRECTIVE:
            continue
        for alias in node.names:
            if alias.name == "*":
                continue
            found.append((node.lineno, alias.asname or alias.name.split(".")[0]))
    return found


def _published(tree: ast.Module) -> set[str]:
    """What `__all__` names, read as string constants wherever the list is composed.

    Walked rather than indexed, so a `__all__` built from two lists or a tuple answers the
    same: what is being read is *which names this module says it publishes*, and the syntax
    it says it in is the module's business.
    """
    published: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            continue
        published |= {
            inner.value
            for inner in ast.walk(node.value)
            if isinstance(inner, ast.Constant) and isinstance(inner.value, str)
        }
    return published


def _spelled(tree: ast.Module) -> set[str]:
    """Every name the module actually uses.

    An :class:`ast.Name` is the whole domain and that is not an approximation: an attribute
    access roots in one, and `from __future__ import annotations` is on every module here, so
    an annotation is a string at runtime and still a `Name` in the tree this reads.
    """
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def unspelled(surface) -> dict[str, list[str]]:
    """Which modules of ``surface`` import a name nothing spells, by line.

    The surface is an argument and not a reach, for the reason `test_configured` gives: a
    property names what it sweeps, and `test_invariants` reads that off the holder.
    """
    found: dict[str, list[str]] = {}
    for module in surface:
        tree = ast.parse(module.text)
        allowed = _published(tree) | _spelled(tree)
        for lineno, name in _bound(tree):
            if name not in allowed:
                found.setdefault(module.where, []).append(f"{lineno}: {name}")
    return found


def test_no_module_imports_a_name_it_never_spells():
    """The property. Six were live on the first run and none of them broke anything, which
    is the whole argument for holding it here: an import list that is wrong costs nothing
    until somebody reads it to decide what a module depends on, and then it costs the
    decision."""
    assert unspelled(modules()) == {}


def test_the_re_export_exclusion_is_load_bearing():
    """The exclusion is the scan's whole risk, so it is measured rather than trusted.

    If no module re-exported a name it does not otherwise spell, the `__all__` branch above
    would be dead code that could only ever hide a real finding. Two do, so the branch is the
    difference between this scan and one that reddens a module for publishing something.
    """
    reexports = {}
    for module in modules():
        tree = ast.parse(module.text)
        spelled = _spelled(tree)
        quiet = {
            name
            for _, name in _bound(tree)
            if name in _published(tree) and name not in spelled
        }
        if quiet:
            reexports[module.where] = sorted(quiet)
    assert reexports, "nothing re-exports an unspelled name: the exclusion hides more than it admits"


def test_the_directive_exclusion_covers_every_module_that_imports_at_all():
    """`from __future__ import annotations` is this package's convention rather than an
    exception to it, so the exclusion is a statement about the syntax and never about a
    module that got a pass. The only file without one imports nothing at all — `verbs/`'s
    `__init__` is a docstring, which is this project's rule for what a subpackage publishes.
    """
    missing = []
    for module in modules():
        tree = ast.parse(module.text)
        directive = any(
            isinstance(node, ast.ImportFrom) and node.module == DIRECTIVE
            for node in ast.walk(tree)
        )
        if not directive and _bound(tree):
            missing.append(module.where)
    assert missing == [], missing
