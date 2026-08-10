"""The pre-add read, bounded by the question it is asked (RK442).

`delivered` was the last query that answered by printing the file. What is asserted here is
the two halves that make the narrower answer safe rather than merely shorter:

* **The recall is measured, not assumed.** This repository's own ledger records four
  `superseded by` pairs — the only four cases where the right answer is known — and the test
  below re-runs the ranking against them. It is a property test over a real corpus, for the
  reason the round-trip one is: a fixture proves the arithmetic and a corpus proves the
  claim, and the claim is what `NEAREST` is set from.
* **A bounded answer says it is bounded.** The unbounded listing was deliberate — the entry
  that got elided is exactly the one nobody read — so `--near` inherits that guarantee only
  by printing what it left out.

And one thing that must never arrive: a score. RK441 measured that the absolute figure
separates nothing, so a payload or a row carrying it is one turn from a threshold that
cannot exist.
"""

from __future__ import annotations

import json
from pathlib import Path

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.ranking import NEAREST, nearest, words

HERE = Path(__file__).resolve().parents[1]

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"

BACKLOG = """# Roadmap

## Block A — The model
"""

LEDGER = """# Shipped

## Block A — The model

- ✅ **RK1** **A dep nothing satisfies is reported without the group it is in** — It works.
- ✅ **RK2** **The changelog heading is written twice by a textual merge** — It works.
- ✅ **RK3** **A pointer resolves to a section that shipped** — It works.
- ✅ **RK4** **The marker is not the codepoint the config declares** — It works.
- ✅ **RK5** **A dep group is rendered out of the order it was typed** — It works.
- ✅ **RK6** **A block heading is declared twice in the ledger** — It works.
"""


def project(tmp_path: Path) -> Path:
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n',
        encoding="utf-8",
    )
    for name, body in {ROADMAP: BACKLOG, CHANGELOG: LEDGER}.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return tmp_path


# -- the ranking ---------------------------------------------------------------


def test_the_nearest_entry_is_the_one_sharing_the_rare_words():
    corpus = [entry for entry in LEDGER.splitlines() if entry.startswith("- ")]
    order = nearest("A block heading declared twice in the changelog", corpus, 2)
    assert "RK6" in corpus[order[0]] or "RK2" in corpus[order[0]]


def test_a_query_sharing_nothing_still_gets_an_order():
    """"These are the nearest" is true of a block whose every entry is far, and an empty
    answer would mean two things again — nothing near, and nothing at all."""
    corpus = ["the first symptom", "the second symptom"]
    assert nearest("zzz qqq", corpus, 2) == (0, 1)


def test_a_tie_keeps_the_ledgers_own_order():
    corpus = ["one word", "one word"]
    assert nearest("one word", corpus, 2) == (0, 1)


def test_nothing_to_rank_is_an_empty_order_and_never_an_error():
    assert nearest("anything", [], 5) == () and nearest("anything", ["one"], 0) == ()


def test_a_word_said_twice_in_a_query_is_emphasis_and_not_evidence():
    # A symptom is one sentence; counting a repeated query term twice would let an author
    # move an entry up the order by saying the word again, which is not a fact about the
    # ledger. The corpus side still counts frequency — that is the entry's own text.
    once = nearest("heading", ["a heading", "a marker"], 2)
    twice = nearest("heading heading", ["a heading", "a marker"], 2)
    assert once == twice


def test_the_tokens_are_runs_of_letters_and_digits():
    assert words("RK442: `delivered --near`, and UTF-16!") == [
        "rk442", "delivered", "near", "and", "utf", "16",
    ]


# -- the measurement `NEAREST` is set from -------------------------------------


def test_every_pair_this_ledger_knows_the_answer_to_lands_inside_the_count():
    """The property test over the real corpus. Four `superseded by` entries name the id they
    restate, which makes them the only four cases in this repository where the nearest entry
    has a *known* right answer — so the recall claim is re-run rather than asserted, and a
    ranking change that quietly loses one of them fails here.

    Scoped to the retired entry's own block, which is what `delivered --near` ranks over.
    """
    config = Config.discover(HERE)
    ledger = config.document("changelog")
    by_id = {entry.task.id: entry for entry in ledger.entries}
    pairs = [
        (entry, entry.task.why.split("superseded by ", 1)[1].split(":", 1)[0].strip())
        for entry in ledger.entries
        if "superseded by " in entry.task.why
    ]
    assert len(pairs) >= 4, "the corpus this figure is measured on lost its known answers"
    for retired, partner in pairs:
        assert partner in by_id, f"{retired.task.id} names {partner}, which the ledger lacks"
        block = [
            entry
            for entry in ledger.entries
            if entry.task.block == retired.task.block and entry.task.id != retired.task.id
        ]
        order = nearest(retired.task.symptom, [e.task.symptom for e in block], NEAREST)
        found = [block[index].task.id for index in order]
        assert partner in found, (
            f"{retired.task.id} → {partner} fell outside the nearest {NEAREST} "
            f"of {len(block)}: {found}"
        )


# -- what the command prints ---------------------------------------------------


def test_the_bounded_answer_says_what_it_left_out(tmp_path, capsys):
    """The unbounded listing was deliberate: the entry that got elided is exactly the one
    nobody read. So a bounded one has to say it is bounded, or it inherits a guarantee it
    just gave up."""
    root = project(tmp_path)
    assert main(["-C", str(root), "delivered", "A", "--near", "a doubled block heading"]) == EXIT_OK
    out = capsys.readouterr().out
    assert f"{NEAREST} nearest of 6 delivered" in out
    assert "an order and not a verdict" in out
    assert "delivered A" in out  # the rest of the block, one command away and named
    assert len([line for line in out.splitlines() if line.startswith("  ✅")]) == NEAREST


def test_the_unbounded_listing_is_untouched(tmp_path, capsys):
    root = project(tmp_path)
    assert main(["-C", str(root), "delivered", "A"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "6 delivered" in out and "nearest" not in out
    assert len([line for line in out.splitlines() if line.startswith("  ✅")]) == 6


def test_no_surface_carries_a_score(tmp_path, capsys):
    """RK441: the absolute figure separates nothing — two of four true pairs score below the
    13th percentile of what a proposal with no duplicate produces — so a caller handed one is
    a caller one turn from the threshold that measurement rules out. The order is published
    and the number is not."""
    root = project(tmp_path)
    argv = ["-C", str(root), "delivered", "A", "--near", "a doubled block heading"]
    assert main(argv) == EXIT_OK
    assert "score" not in capsys.readouterr().out
    assert main([*argv, "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["near"] == "a doubled block heading"
    assert payload["recorded"] == 6 and len(payload["delivered"]) == NEAREST
    assert [row["rank"] for row in payload["delivered"]] == list(range(1, NEAREST + 1))
    assert not any("score" in row for row in payload["delivered"])


def test_the_rank_is_absent_where_the_order_is_the_ledgers(tmp_path, capsys):
    root = project(tmp_path)
    assert main(["-C", str(root), "delivered", "A", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["near"] is None and payload["recorded"] == 6
    assert not any("rank" in row for row in payload["delivered"])


def test_an_empty_near_is_refused_and_never_answered_with_the_whole_block(tmp_path, capsys):
    """The flag arriving empty used to fall through to the unbounded listing — a different
    question, answered as if it were this one, and indistinguishable from the narrow answer
    until the caller counts the rows. A read is where that costs most: nothing exits
    non-zero, so a wrong answer is the only signal there is."""
    root = project(tmp_path)
    for empty in ("", "   "):
        assert main(["-C", str(root), "delivered", "A", "--near", empty]) == EXIT_USAGE
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "--near is the symptom" in captured.err


def test_a_label_nothing_declares_is_still_refused_before_anything_is_ranked(tmp_path, capsys):
    root = project(tmp_path)
    assert main(["-C", str(root), "delivered", "Z", "--near", "anything"]) == EXIT_USAGE
    assert "no heading declares" in capsys.readouterr().err
