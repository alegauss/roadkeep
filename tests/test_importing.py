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

Anything else is either spelled or it is not, which is decided without judgement. What the
first run found: six names across four modules — `guarding`, `linting`, `remedying` and
`shipping` — imported and never spelled again, gone in the commit that added this.

**An AST alone cannot decide it** (RK1194). A plain `ast.Name` walk has no scopes, so a
function's own local answered for a module-level import: `verbs/querying.py` imported `record`
with nothing reading it and stayed green for as long as a local of that name existed. Three
narrower fixes were measured and each was wrong — `Load` context alone finds nothing, since
the local was read; disqualifying every rebound name reports 32 and most are false; and
`symtable`, which has the scopes, is blind to annotations and reports `Config` and `Sequence`
in nearly every module here. So the scan is a hybrid, and each half is where its question has
an answer. Five dead imports were live behind the old reading.

**And the one binding that reading calls live** (RK1636). A name a module imports and then
defines at its own level is resolved by Python in favour of the later statement, silently: the
name *is* referenced, so the scan above is green while the import is dead. Two were standing —
RK1581's `declares`, found by a `TypeError` three frames away, and `installing`'s `Engine`,
which left `Engines.running` annotated with the wrong record for as long as RK1549 had been
shipped. :func:`rebound` is that question, and it is narrow on purpose: not a rule about
shadowing, one shape that is never intentional.
"""

from __future__ import annotations

import ast
import symtable
from dataclasses import dataclass

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


def _statements(body: list[ast.stmt]) -> list[ast.stmt]:
    """Every statement at a module's **own** level, through the guards it wraps them in.

    An `if TYPE_CHECKING:` and a `try/except ImportError:` are not scopes: what they hold runs
    at module level and binds there. A `def` or a `class` is, and its body is not walked —
    a name bound inside one is a local, which is :func:`_referenced`'s question and not this
    one.
    """
    found: list[ast.stmt] = []
    for node in body:
        if isinstance(node, ast.If):
            found += _statements(node.body) + _statements(node.orelse)
        elif isinstance(node, ast.Try):
            found += _statements(node.body)
            for handler in node.handlers:
                found += _statements(handler.body)
            found += _statements(node.orelse) + _statements(node.finalbody)
        else:
            found.append(node)
    return found


def _defined(tree: ast.Module) -> dict[str, int]:
    """Every name this module binds at its own level with a definition, and where (RK1636).

    A `def`, a `class` or an assignment, and the **first** line that binds it: what is being
    read is that the name is spoken for here, not which statement won.
    """
    found: dict[str, int] = {}
    for node in _statements(tree.body):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found.setdefault(node.name, node.lineno)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found.setdefault(target.id, target.lineno)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            found.setdefault(node.target.id, node.target.lineno)
    return found


def _imported(tree: ast.Module) -> dict[str, int]:
    """The same reading as :func:`_bound`, at module level only and keyed by name (RK1636).

    Module level because that is where the collision is silent. A call-time import inside a
    function binding a name the module also defines is a local shadowing a global, which is
    deliberate at every one of the sites RK260 argues for here — and reporting it would make
    this a style rule about shadowing rather than the narrow finding it is.
    """
    found: dict[str, int] = {}
    for node in _statements(tree.body):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if getattr(node, "module", None) == DIRECTIVE:
            continue
        for alias in node.names:
            if alias.name == "*":
                continue
            found.setdefault(alias.asname or alias.name.split(".")[0], node.lineno)
    return found


def rebound(surface) -> dict[str, list[str]]:
    """Which modules import a name they then define at module level (RK1636).

    Python resolves it silently and in favour of the later statement, so the two bindings can
    never both be live: one of them is a dead line or a bug, and both want removing. RK1581 is
    the measurement — `from roadkeep.config import declares` into a module with a public
    `declares` of its own, and `plan` called the wrong one until a `TypeError` three frames
    away in `os.path.relpath`. That was luck: the two return types were incompatible. Two
    functions that both return a string collide into a wrong answer with a green suite.

    Nothing above reports it, and nothing above can. :func:`_spelled` reads the name as *used*,
    because it is — just not the imported one, and neither `symtable` nor an annotation walk is
    asked which binding a reference reached.

    **Narrow on purpose.** Not a rule about shadowing: a local named `found` over a builtin is
    not this, and a call-time import shadowing a module's own name is the seam RK260 argues
    for. What is reported is one shape — a name this module imported and then defined — which
    is never intentional.
    """
    found: dict[str, list[str]] = {}
    for module in surface:
        tree = ast.parse(module.text)
        imports, defs = _imported(tree), _defined(tree)
        for name in sorted(set(imports) & set(defs)):
            found.setdefault(module.where, []).append(
                f"{name}: imported at {imports[name]}, defined at {defs[name]}"
            )
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


def _annotated(tree: ast.Module) -> set[str]:
    """Every name an annotation names (RK1194).

    From the AST and never from a scope, because under `from __future__ import annotations` an
    annotation is **never evaluated**: it is a string at runtime, so it has no scope to be read
    in and every name in one is a use of the import that supplies it. This is the half
    :mod:`symtable` cannot see, and it is most of this package's import lists.
    """
    found: set[str] = set()
    for node in ast.walk(tree):
        subtrees: list[ast.expr] = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            subtrees = [
                one.annotation
                for one in (
                    *args.posonlyargs,
                    *args.args,
                    *args.kwonlyargs,
                    args.vararg,
                    args.kwarg,
                )
                if one is not None and one.annotation is not None
            ]
            if node.returns is not None:
                subtrees.append(node.returns)
        elif isinstance(node, ast.AnnAssign):
            subtrees = [node.annotation]
        for subtree in subtrees:
            found |= {one.id for one in ast.walk(subtree) if isinstance(one, ast.Name)}
    return found


def _comprehended(tree: ast.Module) -> set[str]:
    """What a comprehension reads, minus its own targets (RK1194).

    The reads :mod:`symtable` loses: since PEP 709 a comprehension at module level is inlined,
    and 3.13's tables report neither the elided scope's references nor the module's. Read from
    the AST instead, with the generator targets subtracted — those are the comprehension's own
    names, and counting them is exactly the shadowing this whole scan is about.
    """
    found: set[str] = set()
    kinds = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
    for node in ast.walk(tree):
        if not isinstance(node, kinds):
            continue
        bound = {
            one.id
            for gen in node.generators
            for one in ast.walk(gen.target)
            if isinstance(one, ast.Name)
        }
        reads = {
            one.id
            for one in ast.walk(node)
            if isinstance(one, ast.Name) and isinstance(one.ctx, ast.Load)
        }
        found |= reads - bound
    return found


def _referenced(table: symtable.SymbolTable, name: str, top: bool = True) -> bool:
    """Whether some scope reads this name as something other than its own local (RK1194).

    At module level the import *is* the assignment, so a reference there is a use. In a nested
    scope an assignment means the name belongs to that scope, and the reads are its own — which
    is the whole defect: `verbs/querying.py` imported `record` with no reader in the module,
    and a local of that name inside one function was answering for it.
    """
    for symbol in table.get_symbols():
        if symbol.get_name() != name:
            continue
        if symbol.is_referenced() and (top or not symbol.is_assigned()):
            return True
    return any(_referenced(child, name, top=False) for child in table.get_children())


def _spelled(text: str, where: str) -> set[str]:
    """Every name the module actually uses, with scopes (RK1194).

    Three readers and not one, because no single one of them is right. A plain `ast.Name` walk
    is scope-blind and counted a function's own local as a module-level use — five dead imports
    were live behind that. :mod:`symtable` has the scopes and is blind to annotations, which
    under PEP 563 are most of what this package imports. So the annotations come from the AST,
    where they have no scope to need, and everything else from the table, where it does.
    """
    tree = ast.parse(text)
    table = symtable.symtable(text, where, "exec")
    scoped = {
        name for _, name in _bound(tree) if _referenced(table, name)
    }
    return scoped | _annotated(tree) | _comprehended(tree)


def unspelled(surface) -> dict[str, list[str]]:
    """Which modules of ``surface`` import a name nothing spells, by line.

    The surface is an argument and not a reach, for the reason `test_configured` gives: a
    property names what it sweeps, and `test_invariants` reads that off the holder.
    """
    found: dict[str, list[str]] = {}
    for module in surface:
        tree = ast.parse(module.text)
        allowed = _published(tree) | _spelled(module.text, module.where)
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


def test_no_module_imports_a_name_it_then_defines():
    """RK1636. The one binding Python decides silently, and the one the scan above reads as
    live: the name *is* referenced, so `unspelled` is green while the import is dead.

    Two were standing when this was written and neither had broken anything visible. RK1581's
    was found by a `TypeError` three frames away and cost ten minutes; the other was
    `installing`'s `Engine`, imported from `provenance` and re-declared by RK1549 three
    thousand lines later — so `Engines.running`, the field that names *the copy this process
    is*, was annotated with the record `uninstall --engine` weighs instead. Nothing broke,
    because an annotation is never evaluated here. It was simply false to every reader.
    """
    assert rebound(modules()) == {}


def test_the_rebinding_is_read_where_the_dead_import_is_not():
    """The two halves are one file and two questions, so each is asked of a fixture that
    answers only it: a name imported and then defined is spelled, and a name imported and
    never spelled is not defined. Written together because either check alone reads the
    other's case as clean — which is how both of RK1636's instances survived."""
    ate = (
        "from __future__ import annotations\n"
        "from x import n\n"
        "def n(a):\n"
        "    return a\n"
        "V = n(1)\n"
    )
    assert rebound([_Fixture("ate.py", ate)]) == {
        "ate.py": ["n: imported at 2, defined at 3"]
    }
    # And the reader that misses it, on the same text: the name is spelled, so nothing here.
    assert unspelled([_Fixture("ate.py", ate)]) == {}

    # A guard is not a scope: `if TYPE_CHECKING` and a fallback `except ImportError` both bind
    # at module level, which is where the collision is silent.
    guarded = (
        "from __future__ import annotations\n"
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n"
        "    from x import N\n"
        "class N:\n"
        "    pass\n"
        "V: N = N()\n"
    )
    assert rebound([_Fixture("guarded.py", guarded)]) == {
        "guarded.py": ["N: imported at 4, defined at 5"]
    }

    # A `def` is a scope, so a local of the imported name is not this finding — that is the
    # shadowing `unspelled` already reports, and reporting it twice would make this a style
    # rule about names rather than one about bindings.
    local = "from __future__ import annotations\nfrom x import n\ndef f(a):\n    n = a\n    return n\n"
    assert rebound([_Fixture("local.py", local)]) == {}

    # And an aliased import collides with nothing, which is the remedy both instances took.
    aliased = (
        "from __future__ import annotations\n"
        "from x import n as theirs\n"
        "def n(a):\n"
        "    return theirs(a)\n"
        "V = n(1)\n"
    )
    assert rebound([_Fixture("aliased.py", aliased)]) == {}


def test_the_re_export_exclusion_is_load_bearing():
    """The exclusion is the scan's whole risk, so it is measured rather than trusted.

    If no module re-exported a name it does not otherwise spell, the `__all__` branch above
    would be dead code that could only ever hide a real finding. Two do, so the branch is the
    difference between this scan and one that reddens a module for publishing something.
    """
    reexports = {}
    for module in modules():
        tree = ast.parse(module.text)
        spelled = _spelled(module.text, module.where)
        quiet = {
            name
            for _, name in _bound(tree)
            if name in _published(tree) and name not in spelled
        }
        if quiet:
            reexports[module.where] = sorted(quiet)
    assert reexports, "nothing re-exports an unspelled name: the exclusion hides more than it admits"


@dataclass(frozen=True, slots=True)
class _Fixture:
    """A module that is not on disk, in the shape :func:`unspelled` reads."""

    where: str
    text: str


def test_a_local_of_the_same_name_is_not_a_use():
    """RK1194's property, on fixtures rather than on this tree — which no longer holds one.

    Four shapes, because each is a reader this scan needs and three of them were wrong alone:
    a shadowed import is dead, a read one is not, an annotation-only one is not, and a name a
    comprehension reads is not. Written together because a fix to any one of them broke another
    when they were tried separately.
    """
    shadowed = "from __future__ import annotations\nfrom x import n\ndef f(a):\n    n = a\n    return n\n"
    assert unspelled([_Fixture("shadowed.py", shadowed)]) == {"shadowed.py": ["2: n"]}

    read = "from __future__ import annotations\nfrom x import n\ndef f():\n    return n\n"
    assert unspelled([_Fixture("read.py", read)]) == {}

    annotated = "from __future__ import annotations\nfrom x import N\ndef f(a: N) -> N:\n    return a\n"
    assert unspelled([_Fixture("annotated.py", annotated)]) == {}

    comprehended = "from __future__ import annotations\nfrom x import n\nV = [n(one) for one in ()]\n"
    assert unspelled([_Fixture("comprehended.py", comprehended)]) == {}


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


# -- a record two modules build is reached by name (RK1586, RK1587) ------------


def _records() -> dict[str, tuple[str, bool, int]]:
    """Every dataclass this package declares once, as `(home, keyword-only, fields)`.

    Declared **once**, which is the distinction that makes the reading honest: twenty names
    here belong to two classes apiece — `Dropped` is one record in `criteria` and another in
    `shipping` — and keying by the bare name would report a record shared where two modules
    happen to have written the same word.
    """
    found: dict[str, tuple[str, bool, int]] = {}
    seen: dict[str, int] = {}
    for module in modules():
        for node in ast.parse(module.text).body:
            if not isinstance(node, ast.ClassDef):
                continue
            if not any(
                (isinstance(one, ast.Call) and getattr(one.func, "id", "") == "dataclass")
                or getattr(one, "id", "") == "dataclass"
                for one in node.decorator_list
            ):
                continue
            seen[node.name] = seen.get(node.name, 0) + 1
            found[node.name] = (
                module.where,
                any(
                    isinstance(word, ast.keyword) and word.arg == "kw_only"
                    for one in node.decorator_list
                    if isinstance(one, ast.Call)
                    for word in one.keywords
                ),
                len(
                    [
                        one
                        for one in node.body
                        if isinstance(one, ast.AnnAssign) and isinstance(one.target, ast.Name)
                    ]
                ),
            )
    return {name: one for name, one in found.items() if seen[name] == 1}


def _construction() -> tuple[dict[str, set[str]], dict[str, list[str]]]:
    """Where each record is built, and where it is built **by position** with two or more."""
    built: dict[str, set[str]] = {}
    ordered: dict[str, list[str]] = {}
    for module in modules():
        for node in ast.walk(ast.parse(module.text)):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                continue
            built.setdefault(node.func.id, set()).add(module.where)
            if len(node.args) >= 2:
                ordered.setdefault(node.func.id, []).append(f"{module.where}:{node.lineno}")
    return built, ordered


def test_no_record_two_modules_build_is_reached_by_position():
    """RK1587. RK1586 made `Part` keyword-only after one inserted field moved a published
    figure in silence, and the population sharing that hazard was never counted. It is two
    properties and the hazard is their **intersection**: a record more than one module builds
    has an order nobody owns, and one built positionally has an order somebody relies on.

    Measured: fifteen records of six or more fields are one or the other and none is both, so
    `Part` was the only instance and the sweep RK1587 weighed is declined. What is held is the
    property rather than the list — the day a record becomes both, this is the red."""
    records = _records()
    built, ordered = _construction()
    hazard = [
        name
        for name, (home, kw, fields) in records.items()
        if not kw
        and fields >= 6
        and built.get(name, set()) - {home}
        and ordered.get(name)
    ]
    assert not hazard, {
        one: {"built in": sorted(built[one]), "by position at": ordered[one]} for one in hazard
    }


def test_both_halves_of_that_intersection_are_populated():
    """The reading is only worth having while each half exists: an intersection of two empty
    sets is empty for a reason that says nothing, which is the vacuous green this suite refuses
    everywhere it counts a population."""
    records = _records()
    built, ordered = _construction()
    wide = {name for name, (_, kw, fields) in records.items() if not kw and fields >= 6}
    shared = {one for one in wide if built.get(one, set()) - {records[one][0]}}
    positional = {one for one in wide if ordered.get(one)}
    assert len(shared) >= 4, sorted(shared)
    assert len(positional) >= 4, sorted(positional)
