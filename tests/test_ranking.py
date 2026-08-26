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
from roadkeep.ranking import NEAREST, VOLUNTEERED, nearest, words

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
    reached: list[str] = []
    missed: list[str] = []
    for retired, partner in pairs:
        assert partner in by_id, f"{retired.task.id} names {partner}, which the ledger lacks"
        block = [
            entry
            for entry in ledger.entries
            if entry.task.block == retired.task.block and entry.task.id != retired.task.id
        ]
        order = nearest(retired.task.symptom, [e.task.symptom for e in block], NEAREST)
        found = [block[index].task.id for index in order]
        (reached if partner in found else missed).append(f"{retired.task.id}→{partner}")
    # **The reach, as a figure** (RK1183). This asserted that every pair lands inside the five,
    # which is a premise and not a measurement: a retirement may name the task that delivered the
    # larger half rather than the one whose symptom matches, and RK1182→RK1152 is that — the read
    # places RK348 first, whose sentence *is* nearly RK1182's own and which delivered the other
    # half. So the pair is outside the five and the ranking is not wrong about it.
    #
    # Ranking against the retirement's `why` was the other repair and is unsound: that field
    # literally contains `superseded by <id>`, so the ground truth would be an input.
    #
    # A floor and not the rate, because the denominator grows with every retirement this project
    # records: what may not regress is how many known partners the read still reaches.
    assert len(reached) >= 4, {"reached": reached, "out of reach": missed}


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


# -- the same read, volunteered by the write (RK1370) --------------------------


def _added(root: Path, symptom: str) -> str:
    assert main(
        ["-C", str(root), "add", "--block", "A", "--symptom", symptom, "--why", "Because."]
    ) == EXIT_OK
    return symptom


def test_the_add_hands_back_the_read_the_author_had_to_remember(tmp_path, capsys):
    """RK1370. `delivered --near` is the read the skill puts before every proposal, and it has
    to be remembered: this project filed RK1369 claiming nothing checked which arguments a
    served verb withholds, that check had existed since RK1099, and the `add` said nothing.

    Volunteered *after* the write and not instead of it, because this is a report and never a
    gate: nothing here refuses a duplicate and RK441 measured that nothing could. What it buys
    is the moment — an id is spent and the design is not written, so `restate` and `retire` are
    one call away."""
    root = project(tmp_path)
    _added(root, "A block heading declared twice in the changelog")
    out = capsys.readouterr().out
    assert "an order and not a verdict" in out
    ranked = [line for line in out.splitlines() if line.strip().startswith("✅")]
    assert len(ranked) == VOLUNTEERED
    # The block's own entry about that claim leads, which is what makes the row worth printing.
    assert "RK6" in ranked[0] or "RK2" in ranked[0]


def test_the_volunteered_rows_carry_no_score(tmp_path, capsys):
    """RK441's rule at the door that did not exist when it was written: the absolute figure
    separates nothing, so a row or a payload carrying one is a turn from a threshold the
    measurement rules out. The rank is the order and is the whole of what is published."""
    root = project(tmp_path)
    assert main(
        [
            "-C", str(root), "add", "--block", "A",
            "--symptom", "A pointer resolving to a section that already shipped",
            "--why", "Because.", "--json",
        ]
    ) == EXIT_OK
    near = json.loads(capsys.readouterr().out)["near"]
    assert [one["rank"] for one in near] == list(range(1, VOLUNTEERED + 1))
    assert all("score" not in one for one in near)
    assert near[0]["id"] == "RK3"


def test_a_block_that_has_delivered_nothing_says_nothing(tmp_path, capsys):
    """Two states with nothing to rank — no changelog, and a block with no entries under it —
    and never a third where the nearest looked too far: filtering those out is the impossible
    gate rebuilt as a silence, which is what `VOLUNTEERED` carries the measurement for."""
    root = project(tmp_path)
    (root / CHANGELOG).write_text("# Shipped\n\n## Block A — The model\n", encoding="utf-8")
    _added(root, "A first symptom under a block that has shipped nothing")
    assert "an order and not a verdict" not in capsys.readouterr().out


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


def test_the_pair_out_of_reach_is_the_one_whose_sentences_are_not_the_pair():
    """RK1183, named so the figure above stays re-readable: the reach is four of five, and which
    one is out is a fact about *retirement* rather than about the ranking.

    RK1182 names RK1152 — the task that delivered the half it called larger — while the read
    places RK348 first, whose sentence is nearly RK1182's own and which delivered the other half.
    Both are right about different things, so this asserts the shape and not a verdict: the read
    reaches the sentence-pair, and a retirement may point elsewhere.
    """
    ledger = Config.discover(HERE).document("changelog")
    by_id = {entry.task.id: entry for entry in ledger.entries}
    retired = by_id["RK1182"]
    block = [
        entry
        for entry in ledger.entries
        if entry.task.block == retired.task.block and entry.task.id != retired.task.id
    ]
    order = nearest(retired.task.symptom, [e.task.symptom for e in block], NEAREST)
    found = [block[index].task.id for index in order]
    # The half whose symptom matches is reached; the half the retirement names is not.
    assert "RK348" in found
    assert "RK1152" not in found
