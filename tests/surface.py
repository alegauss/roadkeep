"""The package's own source, as the one set a suite-wide survey quantifies over (RK496).

Seven tests sweep every module of `roadkeep` — for a cache decorator, a spelled command, a
hard-coded verb, a `.block(` call, a missing `__init__.py`, an index entry. Each derived its
own file set inline, and each was written against the layout that existed on the day.

RK494 measured what that costs. Adding `src/roadkeep/verbs/` and its eight modules broke two
of the seven loudly — a census keyed by `Path.name` let `verbs/shipping.py` answer under
`shipping.py`, counting one file as another — and left **three passing while covering nothing
new**, each a `glob("*.py")` from when the package was flat. RK488 had built two of those
precisely to say how many spellings were left; afterwards they answered about 43 of 51 files
and said so nowhere. A red test is a message; a green one that stopped looking is a claim.

So the set is declared once, here, and the surveys ask for it. Two properties follow that
could not be stated before: `test_invariants` can record a row naming this surface (RK491 has
two rows whose surface is "every module of this package", with no address to put in them), and
one test can hold that nothing derives a second view of the package — which is what keeps the
next survey from being written against today's layout.

Addressed by :attr:`Module.where`, the path **under** the package, and never by filename: two
directories are allowed to hold a `shipping.py`, and a survey that cannot tell them apart is
one that silently reports about the wrong one.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from functools import cached_property, lru_cache
from pathlib import Path

#: The package's source tree. Read from this file's location rather than from an import, for
#: the reason `test_caches` gives about its own read: importing the package to enumerate it
#: finds only what happens to have been imported.
PACKAGE = Path(__file__).resolve().parents[1] / "src" / "roadkeep"


# No `slots`: :func:`cached_property` writes the read into the instance dictionary, which a
# slotted class does not have — and the read is what the cache is for.
@dataclass(frozen=True)
class Module:
    """One `.py` file of the package, addressed the way a survey should report it."""

    #: Its path under the package, in posix spelling — `cli.py`, `verbs/shipping.py`. This is
    #: the address: unique, stable across platforms, and the thing to print in a failure.
    where: str
    #: The file itself, for a survey that needs to stat it or read its parent.
    path: Path

    @cached_property
    def text(self) -> str:
        """Its source, read once per run: six surveys ask for the same fifty files."""
        return self.path.read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def modules() -> tuple[Module, ...]:
    """Every module of the package, recursively, in `where` order.

    Recursive is the whole point: a subpackage is where the next eight modules arrive, and a
    survey that stops at the top level keeps passing while it stops covering them.

    Cached so that the same :class:`Module` objects come back to every caller, which is what
    makes :attr:`Module.text` a read per file rather than a read per survey.
    """
    return tuple(
        Module(where=path.relative_to(PACKAGE).as_posix(), path=path)
        for path in sorted(PACKAGE.rglob("*.py"))
        if "__pycache__" not in path.parts
    )


def address(module: str) -> str:
    """Where a module lives **now**, asked by its module name — `schema` → `kernel/schema.py`.

    The lookup RK1074 was filed for. RK496 declared the module *set* once and had the surveys
    ask for it; the addresses stayed hand-written, so moving two files into `kernel/` broke
    seven surveys one at a time, each because a path literal somewhere had to be edited. A
    test that asks for `address("document")` is one the next reorganisation does not touch.

    Refused rather than defaulted where the name is ambiguous or unknown, which is the whole
    value: a survey that quietly kept a stale address is what this replaces, and two modules
    sharing a name — `shipping.py` and `verbs/shipping.py` — is the case RK494 measured, so
    the caller passes `verbs/shipping` there and gets an answer rather than a coin toss.
    """
    wanted = f"{module}.py"
    found = [one.where for one in modules() if one.where in (wanted, module)]
    if not found:
        found = [one.where for one in modules() if one.where.endswith(f"/{wanted}")]
    if len(found) != 1:
        known = ", ".join(sorted(one.where for one in modules()))
        raise LookupError(
            f"{module!r} names {len(found)} modules ({', '.join(found) or 'none'}): "
            f"pass the path under the package where two share a name — {known}"
        )
    return found[0]


def addresses(value: str) -> bool:
    """Whether a literal is an address **into this package** rather than any path (RK1074).

    Two narrowings, and both are what keeps the rule from being one somebody exempts their
    way around. A bare `schema.py` is not enough: a test writing that name into its own
    `tmp_path` is naming a fixture, and a check that could not tell the two apart would fire
    on half the suite. And a directory is not enough either — `test_baseline` writes
    `src/gone.py` and `lib/later.py` into a fixture repository, which are paths and not
    addresses.

    So the first component has to be a subpackage this package actually has, read from the
    census rather than listed: `kernel/` is one because RK1069 made it one, and the next will
    be recognised the day it exists rather than the day somebody remembers this function.
    """
    directory, _, name = value.partition("/")
    if not name or not name.endswith(".py"):
        return False
    return directory in {
        one.where.partition("/")[0] for one in modules() if "/" in one.where
    }


def names() -> tuple[str, ...]:
    """What the Layout index in `agents.md` has to name, which is not the module set (RK494).

    A different question from :func:`modules`, and the reason it is a second function rather
    than a filter: the index names the top level, and a **subpackage as one entry** — its own
    `__init__` docstring being the authority on what is inside it, which is this project's
    rule for every other module too. So `verbs` appears and `verbs/shipping` does not.
    """
    return tuple(
        sorted(
            {path.stem for path in PACKAGE.glob("*.py") if path.stem != "__init__"}
            | {path.name for path in PACKAGE.iterdir() if (path / "__init__.py").exists()}
        )
    )


@lru_cache(maxsize=1)
def suite() -> tuple[Path, ...]:
    """Every test module of this suite, in name order — the sweeps' own surface (RK1448).

    :func:`modules` is about the package and this is about the tests, and it is here for the
    same reason: RK496 declared the package's set once because a survey deriving its own view
    agrees with every other right up until the layout moves. A second sweep over `tests/`
    would be that failure in the other directory, and this one arrived the moment a rule about
    assertions needed the same set `test_invariants` already reads.

    `test_invariants` keeps its own glob deliberately: it is the module that *checks* this
    declaration, and a check that read the declaration would be the declaration checking
    itself. Every other sweep asks here.
    """
    return tuple(sorted(Path(__file__).resolve().parent.glob("test_*.py")))


def calling(source: str, spelled: str) -> tuple[int, ...]:
    """Every line where a call to ``spelled`` is made, by syntax and not by characters (RK1644).

    ``spelled`` is the tail of the call as the source writes it — `block`, `stdout.flush`,
    `save_all` — matched against the unparsed callee, so a dotted form is as addressable as a
    bare one and neither reaches a docstring.

    **The failure this replaces is measured twice.** RK1542 refused a second site recovering
    `superseded by <id>` by hand as a regex over lines matching four string methods; `reverting`
    used a fifth, so the guard read it as clean for that rule's whole life. Widening the pattern
    then matched `reverting`'s own docstring, which quotes the regex it had just stopped using —
    a sentence recording why a coupling went is not a coupling, and a scan over characters
    cannot tell them apart. Both failures are properties of the reading (RK1602).

    What is **not** claimed is that a name identifies a method: two classes may both declare
    `block`, exactly as the character scan could not tell them apart either. What this fixes is
    the prose, which is the half that produced both defects.
    """
    found: list[int] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and ast.unparse(node.func).endswith(spelled):
            found.append(node.lineno)
    return tuple(sorted(set(found)))


def naming(source: str, spelled: str) -> tuple[int, ...]:
    """Every line where ``spelled`` is **read** as a name or a dotted attribute (RK1644).

    :func:`calling`'s other half, for the guards whose subject is a reference rather than a
    call: `in_halves` passed as a predicate, `task.part` read off a record. A docstring naming
    either is prose, which is the whole distinction.
    """
    found: list[int] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Name) and node.id == spelled:
            found.append(node.lineno)
        elif isinstance(node, ast.Attribute) and ast.unparse(node).endswith(spelled):
            found.append(node.lineno)
    return tuple(sorted(set(found)))


def bodies(source: str) -> dict[str, str]:
    """Every function and method this source declares, by name, as source of its own (RK1644).

    So a guard about *what one handler reaches* can ask :func:`calling` about that handler
    rather than splitting the file on `def <name>(` — which is the shape that reads a nested
    definition, a docstring mentioning the name, and the next function's body as one span.

    Last wins where a name is declared twice, which `test_shadowing` already refuses for this
    package: two bodies under one address is the state that guard exists to keep out.
    """
    return {
        node.name: ast.unparse(node)
        for node in ast.walk(ast.parse(source))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def commented(module: str, name: str) -> str:
    """The comment block immediately above where ``name`` is bound (RK1638).

    Prose addressed by **the thing it is attached to**, which is how this file addresses a
    module and `USES` a caller. The checks in `test_naming` found their span by splitting the
    source on a phrase somebody had written — so an author rewording the opening clause did
    not break the test, they emptied it, which is the drift that file exists to end one level
    up. RK1539 was prose drifting from its table; that was a check drifting from its prose,
    failing the same way: silently, green, covering nothing.

    ``name`` is a dotted binding — `TOOLS`, or `_accepting.line` for one inside a function —
    spelled the way `composing.census` spells a site, because a bare name is not an address:
    `line` is assigned in a dozen functions of `cli.py`, and a reader that took the first
    would be the coin toss :func:`address` refuses one question over.

    Refused rather than defaulted in both directions that could be silent: a name this module
    binds nowhere or in several places, and a binding with no comment above it. Either is the
    empty read the phrase-split produced, and answering `""` would reintroduce it here.
    """
    where = address(module)
    return beside(next(one.text for one in modules() if one.where == where), name, where=where)


def beside(text: str, name: str, *, where: str = "<text>") -> str:
    """:func:`commented`'s reading, over source rather than over a module of this package.

    Apart so the refusals can be exercised on a fixture: what makes this a fix and not a
    reshuffle is that the three silent readings a phrase-split had — no such name, several of
    them, no comment at all — are refusals here, and a test cannot reword this package's own
    comments to prove it.
    """
    lines = text.splitlines()
    found = [node.lineno for path, node in _bindings(ast.parse(text)) if path == name]
    if len(found) != 1:
        raise LookupError(
            f"{name!r} is bound {len(found)} times in {where}: a comment is addressed by one "
            f"binding, so pass the dotted path — `<function>.<name>` — that names it"
        )
    said: list[str] = []
    at = found[0] - 1
    while at > 0 and lines[at - 1].lstrip().startswith("#"):
        at -= 1
        stripped = lines[at].lstrip()
        said.append(stripped.removeprefix("#:").removeprefix("#").strip())
    if not any(said):
        raise LookupError(
            f"{name!r} in {where} has no comment above it, so there is no prose beside this "
            f"table to hold it to"
        )
    return "\n".join(reversed(said))


def _bindings(tree: ast.Module) -> list[tuple[str, ast.stmt]]:
    """Every name this module assigns, as `<scope path>.<name>` and the statement (RK1638).

    Scoped, for :func:`commented`'s reason: the address has to be unique or the read is a
    guess. A `for` target and a `with` alias are not here — nothing in this package puts a
    table under one, and a reader that guessed at every binding form would be answering about
    whichever shape it happened to walk first.
    """
    found: list[tuple[str, ast.stmt]] = []

    def walk(node: ast.AST, scope: tuple[str, ...]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                walk(child, (*scope, child.name))
                continue
            targets: list[ast.expr] = []
            if isinstance(child, ast.Assign):
                targets = list(child.targets)
            elif isinstance(child, ast.AnnAssign):
                targets = [child.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    found.append((".".join((*scope, target.id)), child))
            if not targets:
                walk(child, scope)

    walk(tree, ())
    return found


#: A backticked single word — a verb, a flag, a key, a tool name. The span is one word because
#: that is what a *claim about a table* looks like: `` `init` and `adopt` are deliberately
#: absent`` names two members, and `` `roadkeep add --block A` `` is a command, which
#: `composing` already reads under its own rule.
_WORD = re.compile(r"`([a-z][a-z0-9_-]*)`")


#: A digit group standing as **its own word**, which is what tells a measurement from an
#: address (RK1588, generalised by RK1639). `RK1506` is where a decision was made, `L5` is a
#: law, `UTF-8` is an encoding and `utf-16-code-units` is a unit — every one of them glued to
#: a letter or a hyphen, and none of them a number somebody took once. `943` and `2,947` are
#: not glued to anything, and those are the figures that go stale.
#:
#: One line of pattern and not a table of exceptions, which is the whole reason the sweep is
#: cheap enough to point at a second set of prose.
_MEASURED = re.compile(r"(?<![\w-])\d[\d,]*(?![\w-])")


def measured(prose: str) -> tuple[str, ...]:
    """Every figure one span quotes **as a figure**, in order (RK1639).

    RK1588's reading, lifted for its second caller. A number frozen in prose beside a surface
    that moves is a claim nothing re-takes: `budget --decides`' reason quoted *2947 characters
    against 2850* while the tool measured 2758 the same session, `cost --deny` said *19 of
    room* where the read reports hundreds, and `anchors --retired` said *943 of 983* against a
    repository that now holds over a thousand. None of the three broke anything, which is the
    point — a decision defended by a stale figure reads exactly like one that is right.

    **The extraction and never the verdict**, which is `claimed`'s division one function up:
    whether a figure here is a defect or a date depends on who reads the prose, and
    `tests/test_figures.py` is where that is declared per table.
    """
    return tuple(_MEASURED.findall(prose))


def claimed(prose: str) -> tuple[str, ...]:
    """Every backticked word one span of prose names, in order and once each (RK1585).

    The shared half of *the prose beside a table names what the table holds*. RK1539 found one
    instance — a comment naming two collisions where the enumeration finds one, both examples
    written from the tool table and neither checked against the parser — and closed it with a
    regex at the call site. This is that regex, lifted, because the shape has more than one
    instance and a rule written per instance is a rule that stops being applied.

    **The extraction and never the assertion**, which is the whole of what generalises: what a
    span claims about its table differs per table — `TOOLS`' preamble names four verbs it says
    are *absent*, the guard's comment names collisions it says are *present* — and a helper
    that decided which would be inventing the claim. `tests/test_naming.py` is where each is
    stated, and it says which are decidable.
    """
    found: list[str] = []
    for word in _WORD.findall(prose):
        if word not in found:
            found.append(word)
    return tuple(found)
