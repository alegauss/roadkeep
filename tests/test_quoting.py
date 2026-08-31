"""A field name quoted in prose is a claim about the format, held to the template (RK1441).

`--have` on `pick` and `brief` read: *a ready line whose `(needs: …)` names anything
undeclared is set aside*. The schema writes `(requires: …)` and its parser matches only
that, so a caller who took the help at its word and wrote `(needs: ps5)` onto a line had
written prose the grammar does not read as a requirement at all.

**It was not one slip.** `config.py` called `[requirements]` "the words a `(needs: …)` group
may draw on" in two places and once more about what a token may not contain, and
`picking.py`'s own docstring said the same. Four sites agreed with each other and disagreed
with the one that decides, which is how a wrong spelling survives review: it reads as the
convention.

**What makes it reachable** is that nothing joined the two. The line format is a template of
named slots this package can enumerate — `kernel.schema.TEMPLATE` — and every `(word: …)`
a sentence spells in backticks is naming one of them. So the correction is three edits and
this is the half worth having: what stops the fourth site.

The idiom is the search. A **backticked** group with a colon is how this package quotes the
format at a reader; a Python signature, an f-string and an ordinary parenthesis are not, and
a sweep that took them in would be a sweep nobody could keep green.
"""

from __future__ import annotations

import re
from pathlib import Path

from surface import modules

from roadkeep.kernel.schema import TEMPLATE

HERE = Path(__file__).resolve().parents[1]

#: Every surface that quotes the format at a reader: the package, the skill the plugin ships,
#: the slash commands, the resident file and the README. One list, because a spelling is wrong
#: in the same way wherever it is written and the four were corrected one file at a time.
QUOTED = (
    # Through `surface.modules` and never a glob of its own: that module is the one place
    # allowed to ask the filesystem what this package holds, and a survey deriving a second
    # view agrees with it right up to the moment the layout moves (RK496).
    *(one.path for one in modules()),
    *sorted((HERE / "skills").rglob("*.md")),
    *sorted((HERE / "commands").glob("*.md")),
    HERE / "agents.md",
    HERE / "README.md",
)

#: A backticked group naming a field: `` `(deps: …)` ``. Bounded to one line and stopping at
#: the first `)`, exactly as the slot it is quoting does.
GROUP = re.compile(r"`\((?P<name>[a-z][a-z-]*): [^`)]*\)`")


def quoted() -> dict[str, list[str]]:
    """Every group name this repository spells, and where — the census the join is over."""
    found: dict[str, list[str]] = {}
    for path in QUOTED:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for at, line in enumerate(text.split("\n"), start=1):
            for match in GROUP.finditer(line):
                where = f"{path.relative_to(HERE).as_posix()}:{at}"
                found.setdefault(match.group("name"), []).append(where)
    return found


def test_every_group_a_sentence_quotes_is_a_slot_the_template_declares():
    """The join itself. `(needs: …)` was written four times and read by nothing: the parser
    matches `(requires: …)` and only that, so the help was quoting a grammar that does not
    exist — and a caller copying it writes prose no verb reaches."""
    slots = {slot.name for slot in TEMPLATE}
    spelled = quoted()
    unknown = {name: where for name, where in spelled.items() if name not in slots}
    assert not unknown, f"quoted groups no slot of the template declares: {unknown}"


def test_the_census_is_not_empty_so_a_green_run_is_evidence():
    """A regular expression that stopped matching passes this file in silence, which is the
    one way a sweep decays: the surveys in `tests/surface.py` exist because a green test that
    stopped looking is a claim. Both slots that can carry a group are spelled somewhere."""
    spelled = quoted()
    assert "requires" in spelled, spelled
    assert "deps" in spelled, spelled
