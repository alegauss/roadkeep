"""What the ledger already undid, before an id is spent on it again (RK416).

A revert is filed as a delivery, so a duplicate check that asks "did a shipped entry already
do this" answers `yes` about the entry saying the work did **not** hold — and misses that the
new line is asking to undo it again. The cost is worse than a duplicate's: a duplicate wastes
an id, this wastes an id plus the argument the revert already had.

Nothing new is stored. RK395's forward pointer is the whole signal, and this reads it back —
which is what keeps the answer from being a second index of what the ledger already says.
"""

from __future__ import annotations

import json
from pathlib import Path

from roadkeep.cli import EXIT_GATE, EXIT_OK, main
from roadkeep.config import Config
from roadkeep.reverting import reversals, undone


def test_the_forward_pointer_is_the_whole_signal(tmp_path):
    config = _project(tmp_path)
    found = reversals(config)
    assert [(one.undone, one.by) for one in found] == [("DX2", "DX9")]
    # The reversing entry's sentence is the argument a fresh proposal is against, which is
    # the half a bare list of ids would leave out.
    assert "did not hold" in found[0].why


def test_a_ledger_with_no_reversal_answers_none(tmp_path):
    config = _project(tmp_path, ledger=_PLAIN)
    assert reversals(config) == ()
    assert undone(config) == frozenset()


def test_a_retirement_is_not_a_reversal(tmp_path):
    """`retire --superseded-by` writes `superseded by RKn: <reason>` on a 🗑 entry, which is
    a line that left without shipping — a different act, and one the roadmap already records.
    The parenthesised clause RK395 appends to a ✅ entry is what this reads."""
    config = _project(tmp_path, ledger=_RETIRED)
    assert reversals(config) == ()


def test_the_read_never_refuses_an_add(tmp_path, capsys):
    # Re-proposing reverted work is sometimes exactly right — the revert may have been about
    # a broken implementation rather than a wrong idea — so this states a fact and decides
    # nothing. The plain listing is exit 0 even when it found something.
    _project(tmp_path)
    assert main(["-C", str(tmp_path), "reversals"]) == EXIT_OK
    assert "DX2" in capsys.readouterr().out


def test_asking_about_one_id_exits_one_when_it_was_undone(tmp_path, capsys):
    # An exit code is what a script branches on without reading either stream, and this is
    # the caller the read exists for: one about to spend an id.
    _project(tmp_path)
    assert main(["-C", str(tmp_path), "reversals", "--id", "DX2"]) == EXIT_GATE
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "reversals", "--id", "DX1"]) == EXIT_OK


def test_the_payload_carries_the_argument_and_not_only_the_ids(tmp_path, capsys):
    _project(tmp_path)
    assert main(["-C", str(tmp_path), "reversals", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    row = payload["reversed"][0]
    assert row["undone"] == "DX2" and row["by"] == "DX9"
    assert "did not hold" in row["why"]


def test_the_clause_is_read_the_way_the_write_renders_it(tmp_path):
    # The reader and the writer of one clause disagreeing is the defect this package is
    # about, so the pattern is built from `_SUPERSEDED` rather than spelled a second time.
    from roadkeep.shipping import _SUPERSEDED

    assert _SUPERSEDED.format(replacement="DX9") == "superseded by DX9"
    assert "DX2" in {one.undone for one in reversals(_project(tmp_path))}


# -- fixtures ----------------------------------------------------------------

_ROADMAP = """# Roadmap

## Block A — The first block

- 📋 **DX1** (deps: —) **A first symptom** — Because of a reason. → §DX1
"""

_PLAIN = """# Shipped

## Block A — The first block

- ✅ **DX2** **A symptom that shipped** — it was done.
"""

#: RK395's shape: the entry that shipped carries the forward pointer, and the entry that
#: reverted it is an ordinary ✅ line — which is exactly why a duplicate check misreads it.
_REVERTED = """# Shipped

## Block A — The first block

- ✅ **DX2** **A symptom that shipped and was undone** — it was done (superseded by DX9).
- ✅ **DX9** **The change that shipped as DX2 made the common case worse** — it is reverted, because the delivery did not hold under the load it was written for.
"""

#: `retire --superseded-by`: a line that left without shipping, which is a different act.
_RETIRED = """# Shipped

## Block A — The first block

- 🗑 **DX2** **A symptom nobody delivered** — superseded by DX9: DX9 shipped the same thing.
"""

_PROSE = """# Design rationale

## Block A — The first block

### §DX1 The first design

The reasoning the first line has no room for.
"""


def _project(tmp_path: Path, ledger: str = _REVERTED) -> Config:
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "DX"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'improvements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    for name, body in (
        ("ROADMAP.md", _ROADMAP),
        ("CHANGELOG.md", ledger),
        ("IMPROVEMENTS.md", _PROSE),
    ):
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)
