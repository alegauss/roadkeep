"""A command a message spells is one this CLI accepts, flags included (RK1022).

`add` refuses a line with no pointer and names `--ref`; the refusal sends the author to
`anchors --block <x>`, and that listing used to end `— pick one, then --family it`. There
is a `--family`, and it belongs to `anchors` — but the author is mid-`add`, so the bare
flag reads as a second flag of the verb they were writing, and `add --family` is an
argparse error. One validation refusal, which explains itself, becomes two, the second of
which does not.

So the fix is the spelling — the whole command, with an address off the listing the caller
is already looking at — and this is what holds it: **every command a message spells with a
flag is a command that declares that flag.** Reassembled from f-strings, because almost
every message here is one and a scan reading `ast.Constant` alone sees `anchors --family `
as a fragment between two substitutions.

**What was measured and not built.** The design proposed sweeping every hint for `--word`
and asking the parser about it. Over this package that is 446 strings holding a flag, of
which 379 name no verb — most of them `cli.py`'s own `add_argument("--json")`, which *is*
the declaration, and the rest refusals from a verb the reader just ran, where naming it
again is noise. An allow-list of 379 is the red nobody keeps, which is the argument
`test_configured` already makes about numbers and help strings. Bounded to *a command
spelled with its flags* the same sweep is 45 pairs and decidable, and it covers the class
this defect is in: a message that hands over an argv hands over one that runs.
"""

from __future__ import annotations

import argparse
import ast
import re

from asking import verbs
from surface import modules

#: A long option as this package writes one. Short flags are not swept: `-C` and `-m` are
#: single letters that appear in ordinary prose, and the class of defect here is a message
#: composing an argv, which this project always spells long.
FLAG = re.compile(r"--[a-z][a-z0-9-]*")


def options() -> dict[str, set[str]]:
    """Every verb this CLI parses, and the long flags each declares.

    Read off the parser rather than listed, for `surface.py`'s reason: a second view of the
    surface agrees with the first until somebody adds a flag, which is the one moment either
    of them matters.
    """
    return {
        name: {
            option
            for action in parser._actions
            for option in action.option_strings
            if option.startswith("--")
        }
        for name, parser in verbs().items()
    }


def _spelled(node: ast.AST) -> str | None:
    """One message as a reader sees it, with every substitution collapsed to a placeholder.

    An f-string is a :class:`ast.JoinedStr` whose constant parts are fragments, so a scan
    reading constants alone finds `anchors --family ` and never the backtick that opens it.
    Concatenation is followed too: a refusal long enough to wrap is two literals and one
    sentence.
    """
    if isinstance(node, ast.JoinedStr):
        return "".join(
            part.value if isinstance(part, ast.Constant) else "<>" for part in node.values
        )
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _spelled(node.left), _spelled(node.right)
        return None if left is None or right is None else left + right
    return None


def commands(text: str, declared) -> list[tuple[str, str]]:
    """Every `(verb, flag)` a message spells as one command, in a code span.

    The backtick is what makes this decidable rather than noisy: `pick --line` inside an
    English sentence is the word "pick" beside a flag of something else, and nobody reads it
    as an argv. Inside a code span it is an argv, and it is the thing a reader copies.
    """
    paths = "|".join(re.escape(one) for one in sorted(declared, key=len, reverse=True))
    written = re.compile(
        rf"`[^`]*?(?<![\w-])({paths})((?:\s+(?:--[a-z][a-z0-9-]*|[^\s`]+))*)"
    )
    return [
        (found.group(1), flag)
        for found in written.finditer(text)
        for flag in FLAG.findall(found.group(2))
    ]


def spellings(surface):
    """Every command spelled with a flag across ``surface``, with its address.

    The surface is an argument and not a reach, for the reason `test_configured` gives: a
    property names what it sweeps, and `test_invariants` reads that off the holder to check
    the row still describes the rule it claims.
    """
    declared = options()
    for module in surface:
        tree = ast.parse(module.text)
        docs = {
            id(node.body[0].value)
            for node in ast.walk(tree)
            if isinstance(
                node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            )
            and ast.get_docstring(node) is not None
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and id(node) in docs:
                continue
            text = _spelled(node)
            if not text:
                continue
            for verb, flag in commands(text, declared):
                yield f"{module.where}:{node.lineno}", verb, flag


def test_every_command_a_message_spells_declares_the_flags_it_is_spelled_with():
    """The property. A message that hands over an argv hands over one that runs — otherwise
    the reader's next step is an argparse error, which is the one refusal in this tool that
    explains nothing."""
    declared = options()
    wrong = [
        (where, f"{verb} {flag}")
        for where, verb, flag in spellings(modules())
        if flag not in declared[verb]
    ]
    assert wrong == [], wrong


def test_the_listing_that_sends_a_caller_to_a_family_spells_the_command():
    """The instance, held by name because the general property above cannot see it: the flag
    was always a real one, and what was wrong was that no command was named beside it. A
    regression here reads as a passing sweep and a caller back at `--help`."""
    where = next(
        module for module in modules() if module.where == "verbs/querying.py"
    )
    tree = ast.parse(where.text)
    # A **declaration** is not a message (RK1171). Since the parser moved in beside the
    # handler, this module spells `--family` twice more: as the flag itself, and inside
    # `--block`'s own help. Neither hands a caller a route — argparse prints them under a
    # `--help` that already names the verb, which is exactly what a message has to supply.
    declared = {
        id(inner)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "attr", "") in ("add_argument", "add_parser")
        for inner in ast.walk(node)
    }
    said = [
        text
        for node in ast.walk(tree)
        if id(node) not in declared and (text := _spelled(node)) and "--family" in text
    ]
    assert said, "verbs/querying.py stopped naming --family at all"
    for text in said:
        assert "anchors --family" in text, text


def test_the_sweep_reaches_the_messages_and_not_only_the_declarations():
    """A scan reading `ast.Constant` alone answers about `cli.py`'s `add_argument` calls and
    almost nothing else, because every message here is an f-string. Asserted rather than
    assumed: the count going to zero would be a green sweep over nothing, which is the
    failure `surface.py` exists for one surface over."""
    found = list(spellings(modules()))
    assert len(found) >= 40, len(found)
    assert any(where.startswith("verbs/") for where, _, _ in found), found[:5]


def test_every_verb_the_sweep_names_is_one_this_cli_parses():
    """The domain is the parser's, so a message naming a verb that left is a message nobody
    can run — and the sweep would silently stop looking at it rather than fail."""
    parsed = verbs()
    for where, verb, _ in spellings(modules()):
        assert verb in parsed, f"{where}: no such verb {verb!r}"
        assert isinstance(parsed[verb], argparse.ArgumentParser)
