"""A name bound twice in one body is one definition nothing runs (RK1219).

Found by reading, which is the whole reason this file exists. `Share.payload` was declared at
two places in `budgeting.py`, twenty-seven lines apart, with byte-identical return dicts and
two different docstrings. Python keeps the second and discards the first — a class body is a
namespace and a rebound name is legal, so there is no warning, no failure and no finding.

Dead code is mild. Dead code **shaped exactly like live code** is not: the record in question
publishes the numbers this whole tool exists to state before prose is written, and the copy a
reader lands on first is the copy that never runs. The next edit to that answer lands in
whichever one the editor's search reached.

Held here rather than in `lint`, which is the question RK1219's design left open and this is
the answer: the gate's subject is a project's governed files, and this is a claim about the
package's own source — the same boundary `test_importing` and `test_caches` sit on. There is
no linter in this tree and no dev dependency that would bring one, for the reason there is no
runtime dependency, so a survey is the only thing that can hold it.

Over the set `surface.py` declares (RK496), never a `glob` of its own: a survey written
against today's layout is one that keeps passing while it stops covering the files added
after it.

**The exemptions are syntactic and none of them is a judgement.** A `@x.setter` or
`@x.deleter` rebinds its property's name by design, and `@overload` declares a signature
rather than a body. Anything else is either bound once or it is not, which is decided without
reading what the two copies say — an equality check between them would exempt the pair this
task is about the moment somebody edited one of the docstrings, which is exactly how it got
here.

Only the **direct** body of a module or a class is walked. A `def` inside an `if` or a `try`
is an alternative and not a redefinition, and a nested function is its own scope.
"""

from __future__ import annotations

import ast

from surface import modules

#: Decorators that rebind a name on purpose. `setter` and `deleter` complete a property, and
#: `overload` declares a signature whose body is discarded by design — matched by the attribute
#: or the bare name, because both spellings reach this package's own imports.
DELIBERATE = frozenset({"setter", "deleter", "overload"})


def _deliberate(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        (isinstance(one, ast.Attribute) and one.attr in DELIBERATE)
        or (isinstance(one, ast.Name) and one.id in DELIBERATE)
        for one in node.decorator_list
    )


def _rebound(scope: ast.Module | ast.ClassDef) -> dict[str, list[int]]:
    """Every name this body's own `def`s bind more than once, with the lines that bind it."""
    found: dict[str, list[int]] = {}
    for item in scope.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and not _deliberate(item):
            found.setdefault(item.name, []).append(item.lineno)
    return {name: at for name, at in found.items() if len(at) > 1}


def _scopes(tree: ast.Module) -> list[tuple[str, ast.Module | ast.ClassDef]]:
    """The module's own body and every class body in it, each addressed by name."""
    return [("<module>", tree)] + [
        (node.name, node) for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    ]


def test_no_module_or_class_defines_one_name_twice():
    """The sweep RK1219 was found without. One hit when it was written, and it was the finding."""
    shadowed = [
        f"{module.where}:{scope} defines {name} at {', '.join(str(one) for one in at)}"
        for module in modules()
        for scope, body in _scopes(ast.parse(module.text))
        for name, at in _rebound(body).items()
    ]
    assert shadowed == [], shadowed


def test_a_deliberate_rebinding_cannot_hide_an_accidental_one():
    """The one part of the rule above that is not syntax, held so it stays narrow.

    :data:`DELIBERATE` excuses a *decorator*, never a name: a body carrying `@x.setter` beside
    two plain `def x` is still the defect, and an exemption keyed on the name would swallow it.
    Zero decorated rebindings in this package today, so this sweeps nothing and is here for the
    same reason the exemption is — a property setter is ordinary Python and the day one arrives
    is the day the exemption starts deciding something.
    """
    hidden = [
        f"{module.where}:{scope} defines {name} {plain} times undecorated beside a "
        f"deliberate rebinding"
        for module in modules()
        for scope, body in _scopes(ast.parse(module.text))
        for name, (plain, marked) in _by_name(body).items()
        if marked and plain > 1
    ]
    assert hidden == [], hidden


def _by_name(
    scope: ast.Module | ast.ClassDef,
) -> dict[str, tuple[int, int]]:
    """Each name this body binds, counted as `(undecorated, deliberately rebound)`."""
    found: dict[str, tuple[int, int]] = {}
    for item in scope.body:
        if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        plain, marked = found.get(item.name, (0, 0))
        found[item.name] = (
            (plain, marked + 1) if _deliberate(item) else (plain + 1, marked)
        )
    return found
