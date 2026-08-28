"""What a rendered page reads off a payload, as one reader rather than three (RK1405).

Four components render this tool's own answers — the verb tables, the config tables, the
finding pages and the session prices — and each is a place where a *name* has to agree with a
key some `payload()` publishes. Nothing on either side states that agreement, and when it
breaks the build dies on the first page it renders, or worse, renders a column of `undefined`.

So every one of those tests asks the same question: which keys does this component read? It was
written three times before this file existed, and the third copy is where both false positives
were found — which is `surface.py`'s argument about the package's own module list, applied to
the suite's own helpers.

**Two things a naive scan gets wrong**, both met rather than imagined:

* `one.tools.length` is a read of `length` off a *command's* array, not off the tool-price
  payload — so a receiver reached through a dot is somebody else's.
* `import measured from "../data/session.generated.json"` contains `session.generated`, which
  reads as a key off `session`. An import is not a read.
"""

from __future__ import annotations

import re

#: An ES module import, which names files and not fields. Dropped before the scan, because a
#: path like `session.generated.json` otherwise reads as a key off `session`.
_IMPORT = re.compile(r"^\s*import\b.*$", re.MULTILINE)


def read_by(component: str, receiver: str) -> set[str]:
    """Every `<receiver>.<key>` the component source reads, by key name.

    Read off the text rather than by rendering it, for `test_describing`'s reason about the
    config: this suite has no JavaScript to run it with, and the question — does this component
    name a field the payload publishes — is answerable from the source.
    """
    body = _IMPORT.sub("", component)
    return {
        found.group(1)
        for found in re.finditer(rf"(?<![.\w]){re.escape(receiver)}\.([a-z_]+)\b", body)
    }
