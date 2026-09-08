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

import pytest

import corpora
from roadkeep.authoring import Neighbours
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.ranking import NEAREST, VOLUNTEERED, claim, nearest, words
from roadkeep.shipping import superseded

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
    """The property test over the real corpus. The `superseded by` entries name the id they
    restate, which makes them the only cases in this repository where the nearest entry has a
    *known* right answer — so the recall claim is re-run rather than asserted, and a ranking
    change that quietly loses one of them fails here.

    Scoped to the retired entry's own block, which is what `delivered --near` ranks over, and
    run in that verb's own shape (RK1477): the **corpus** carries both prose fields and the
    query is the symptom alone. Joining the query here would score the ground truth — a
    retired entry's `why` is written at the retirement and quotes the partner it names — which
    is the same unsoundness the comment below records about ranking against it.
    """
    config = Config.discover(HERE)
    ledger = config.document("changelog")
    by_id = {entry.task.id: entry for entry in ledger.entries}
    pairs = [
        (entry, superseded(entry.task.why))
        for entry in ledger.entries
        if superseded(entry.task.why)
    ]
    assert len(pairs) >= 11, "the corpus this figure is measured on lost its known answers"
    reached: list[str] = []
    missed: list[str] = []
    for retired, partner in pairs:
        assert partner in by_id, f"{retired.task.id} names {partner}, which the ledger lacks"
        block = [
            entry
            for entry in ledger.entries
            if entry.task.block == retired.task.block and entry.task.id != retired.task.id
        ]
        order = nearest(
            retired.task.symptom, [claim(e.task.symptom, e.task.why) for e in block], NEAREST
        )
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
    # The floor moved 4 → 9 when the corpus took the `why` (RK1477), and it is a floor for the
    # reason it always was: the denominator grows with every retirement this project records,
    # so what may not regress is how many known partners the read still reaches.
    assert len(reached) >= 9, {"reached": reached, "out of reach": missed}


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


# -- both prose fields, not the symptom alone (RK1477) -------------------------


def test_a_word_only_the_why_carries_reaches_the_entry():
    """The mechanism, isolated: two entries whose symptoms are the same sentence, one of which
    names the flag at issue in its `why`. That is the measured case in miniature — what two
    authors of one defect share is the field that spells the verbs and flags out."""
    symptom = "budget states the allowance and cannot be handed a draft"
    whys = ["A count is not a limit.", "`--symptom` measures the draft and exits over it."]
    # The symptoms alone are one string twice, so nothing separates them and the corpus order
    # stands — which is the tie `nearest` promises to keep.
    assert nearest("the symptom flag", [symptom, symptom], 2) == (0, 1)
    joined = [claim(symptom, why) for why in whys]
    assert nearest("the symptom flag", joined, 2) == (1, 0)


def test_a_half_that_is_empty_leaves_the_text_it_had():
    # A space-joined pair is one string, so an entry with no `why` must not gain a token or a
    # leading space that a length normalisation would then count.
    assert claim("a symptom", "") == "a symptom"
    assert claim("", "a why") == "a why"
    assert words(claim("a symptom", "A why.")) == ["a", "symptom", "a", "why"]


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


def test_the_corpus_the_readings_measure_is_the_one_the_write_ranks(tmp_path, capsys):
    """RK1623. Three readings of how the two halves share the window rebuilt this corpus by
    hand, and none of them called the code that composes it — so what they measured was *a*
    corpus of that shape, and a change to what `add` includes would have left every figure
    passing about a composition production no longer has. RK1495 is that change, made once.

    So the corpus is `Neighbours` and this is the join: the rows a real `add` volunteered are
    the rows the seam names, off the same block, over the same window. A figure taken from the
    function the caller uses cannot drift from what the caller gets (RK1491, RK1524)."""
    root = project(tmp_path)
    assert main([
        "-C", str(root), "add", "--block", "A", "--symptom",
        "A block heading declared twice in the changelog", "--why", "Because.", "--json",
    ]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)

    config = Config.discover(root)
    filed = config.document("roadmap").by_id()[payload["id"]].task
    held = Neighbours.of(
        filed.block,
        roadmap=config.document("roadmap"),
        ledger=config.document("changelog"),
        without=filed.id,
    )
    shown = [one["id"] for one in payload["near"]]
    assert shown == [
        held.entries[index].task.id
        for index in held.ranked(filed.symptom, filed.why, VOLUNTEERED)
    ]
    # And the two counts the rows are bounded against are the seam's halves, so the boundary
    # every split figure counts from is the one the write reported.
    assert payload["near_recorded"] == held.boundary
    assert payload["near_open"] == len(held.open_lines)


def test_the_volunteered_rows_say_they_are_bounded_and_where_the_rest_are(tmp_path, capsys):
    """RK1374. RK442's guarantee on the half a write volunteers: the unbounded listing was
    deliberate, because the entry that got elided is the one nobody read — so a bounded answer
    says it is bounded, in the same two phrases `--near` uses, or it inherits what it gave up.

    The block's own listing is the door and never a `--near` rendered with the symptom in it:
    that argument is a sentence the caller has just written, and quoting it back is the second
    grammar RK313 declined."""
    root = project(tmp_path)
    _added(root, "A block heading declared twice in the changelog")
    said = capsys.readouterr().out
    # Shown against held, so three rows never read as a three-entry block.
    assert f"{VOLUNTEERED} nearest of 6 delivered" in said
    assert "delivered A` is all 6" in said

    assert main(
        ["-C", str(root), "add", "--block", "A", "--symptom", "A second one", "--why",
         "Because.", "--json"]
    ) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    # The **ledger's** count and not the roadmap's: an `add` files no delivery, so this is the
    # same six either way — which is the number the rows are bounded against.
    assert payload["near_recorded"] == 6
    assert len(payload["near"]) == VOLUNTEERED


def test_an_open_line_is_in_the_corpus_the_next_proposal_is_ranked_against(tmp_path, capsys):
    """RK1495. The corpus was the ledger alone, so two callers filing one defect within the
    hour could not see each other — which is precisely when a duplicate is cheapest to catch
    and most likely to happen. Measured here: RK1472 was filed against `budget` taking no
    `--requires` while RK1461 said the same thing in almost the same words and was **open**;
    ranked against the delivered corpus afterwards it comes back second, so the window was
    right and the corpus had no open lines in it."""
    root = project(tmp_path)
    capsys.readouterr()
    _added(root, "A vendored decoder crashes on a truncated frame")
    capsys.readouterr()
    # The second session, minutes later, saying the same thing in its own words.
    assert main([
        "-C", str(root), "add", "--block", "A", "--json",
        "--symptom", "The vendored decoder crashes when a frame is truncated",
        "--why", "Because.",
    ]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    # The open line leads, which is the whole finding: it was invisible before.
    assert payload["near"][0]["symptom"] == "A vendored decoder crashes on a truncated frame"
    # Counted apart, so a reader knows which corpus each row came from — and each row already
    # carries its marker, which is what tells a delivery from a claim somebody is making.
    assert payload["near_open"] >= 1
    assert payload["near_recorded"] == 6


def test_the_two_corpora_are_counted_apart_in_the_row_a_terminal_reads(tmp_path, capsys):
    # Both numbers, because the commands that show the rest are different: `delivered <block>`
    # is the ledger's and the open lines are the roadmap's own listing.
    root = project(tmp_path)
    _added(root, "A first thing")
    capsys.readouterr()
    _added(root, "A second thing")
    said = capsys.readouterr().out
    assert "delivered and" in said
    assert "open under this block" in said
    # Both doors, since RK1528: RK442's guarantee is that a bounded answer names where the rest
    # are, and it was given about a corpus that was the ledger alone. With the open half counted
    # and unnamed, the reader who suspects the fourth-nearest can open one of the two.
    assert "delivered A` is all 6" in said
    assert "list --block A` the 1 open" in said


def test_the_row_names_one_door_where_there_is_one_corpus(tmp_path, capsys):
    """RK1528's other half, and the reason the second clause is conditional: this row prints on
    every `add`, and a project whose block has no open lines is told about a listing that would
    answer with nothing. RK1374 got the row to its size by refusing a second wording."""
    root = project(tmp_path)
    _added(root, "The only line in this block")
    said = capsys.readouterr().out
    assert "delivered A` is all 6" in said
    assert "list --block" not in said, "no open half, so no door to it"


def test_both_doors_are_commands_this_cli_accepts(tmp_path, capsys):
    """The rule every composed door here is held to (RK1209): a row a reader is meant to run
    that names an argv this parser refuses is a door that is not one."""
    from composing import commands
    from roadkeep.cli import build_parser

    root = project(tmp_path)
    _added(root, "A first thing")
    capsys.readouterr()
    _added(root, "A second thing")
    argv = [one for one in commands(capsys.readouterr().out) if one[:1] in (["delivered"], ["list"])]
    assert [one[0] for one in argv] == ["delivered", "list"], argv
    for one in argv:
        assert build_parser().parse_args(one)


def test_the_line_being_filed_is_not_ranked_against_itself(tmp_path, capsys):
    # The roadmap read is the pre-write one and the id is excluded besides, so the words a
    # caller has just written are never handed back to them as a neighbour.
    root = project(tmp_path)
    assert main([
        "-C", str(root), "add", "--block", "A", "--json",
        "--symptom", "A wholly unprecedented symptom nothing else says",
        "--why", "Because.",
    ]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    filed = payload["id"]
    assert filed not in [one["id"] for one in payload["near"]]


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


# -- the half of the ranking nothing can score (RK1500) ------------------------


def _known_pairs():
    """The retirements whose partner is named on the line, which is the only ground truth
    this ledger holds — and, since RK1500, the reason one half of the read is unmeasured."""
    ledger = Config.discover(HERE).document("changelog")
    return [
        (entry, superseded(entry.task.why))
        for entry in ledger.entries
        if superseded(entry.task.why)
    ]


def test_the_ground_truth_is_written_into_the_field_a_query_would_join():
    """RK1500. RK1477 measured the corpus half and could only argue the other: a retired
    entry's `why` is written *at* the retirement and names its partner, so a query taking that
    field scores the ledger's own bookkeeping. The argument was a paragraph and nothing held
    it — and the figure it warns about looks like an improvement, which is what makes a later
    session likely to take it.

    Measured rather than asserted: all eleven, not most."""
    pairs = _known_pairs()
    assert len(pairs) >= 11, "the corpus this reasoning is measured on lost its known answers"
    naming = [
        f"{retired.task.id}→{partner}"
        for retired, partner in pairs
        if partner in retired.task.why
    ]
    assert len(naming) == len(pairs), {
        "the why names its partner": naming,
        "it does not": [
            f"{r.task.id}→{p}" for r, p in pairs if p not in r.task.why
        ],
    }


def test_joining_the_query_scores_the_bookkeeping_and_looks_like_a_gain():
    """The other half of the same point, and why the paragraph alone was not enough: the
    unsound reading is *better*. Held as the shape and not as a pair of numbers — what may not
    happen is somebody reading a rise here as a measurement of the read."""
    pairs = _known_pairs()
    ledger = Config.discover(HERE).document("changelog")

    def first(query) -> int:
        found = 0
        for retired, partner in pairs:
            block = [
                one
                for one in ledger.entries
                if one.task.block == retired.task.block and one.task.id != retired.task.id
            ]
            order = nearest(
                query(retired), [claim(e.task.symptom, e.task.why) for e in block], NEAREST
            )
            if [block[index].task.id for index in order][:1] == [partner]:
                found += 1
        return found

    honest = first(lambda one: one.task.symptom)
    scored = first(lambda one: claim(one.task.symptom, one.task.why))
    # The rise is real and means nothing: the field it comes from contains the answer, which
    # the test above measures. Asserted as an inequality rather than as two constants, so the
    # claim survives a corpus that grows.
    assert scored >= honest, {"symptom alone": honest, "with the why": scored}
    assert honest, "the honest reading reached nothing: this comparison is about nothing"


def test_the_two_corpora_do_not_compete_for_the_volunteered_rows():
    """RK1527. RK1495 doubled what the near rows are drawn from — a block's deliveries and now
    its open lines — and left the window at three, so two halves compete for the same rows with
    no reading of how often either wins one. This is that reading.

    Measured in `add`'s own shape: both prose fields on both sides, the block's shipped entries
    followed by its open ones, over the eleven pairs this ledger knows the answer to. The open
    half takes one slot of thirty-three, which is what makes three still the right number —
    and a ranking change that makes them compete is a red here rather than a silence."""
    config = Config.discover(HERE)
    ledger, roadmap = config.document("changelog"), config.document("roadmap")
    pairs = [
        (entry, superseded(entry.task.why))
        for entry in ledger.entries
        if superseded(entry.task.why)
    ]
    assert len(pairs) >= 11
    taken = 0
    for retired, _ in pairs:
        # `add`'s own corpus and not a rebuilt list of that shape (RK1623): the boundary this
        # counts from is `Neighbours.boundary`, so a change to what `add` includes moves this
        # figure rather than leaving it passing about a composition production has not got.
        held = Neighbours.of(
            retired.task.block,
            roadmap=roadmap,
            ledger=ledger,
            without=retired.task.id,
        )
        order = held.ranked(retired.task.symptom, retired.task.why, VOLUNTEERED)
        taken += sum(1 for index in order if held.opened(index))
    # A ceiling and not an equality: a delivery filed tomorrow moves the order, and what may
    # not happen is the open half taking the rows the measurement says it does not need.
    assert taken <= VOLUNTEERED, {"slots the open half took": taken}


def _slots(ledger, roadmap, width: int) -> dict[str, tuple[int, int, int, int]]:
    """Per block, how many of the volunteered rows an open line's own siblings take.

    The **block** is the unit, which is RK1566's correction to itself: the ratio §RK1566 was
    filed about is per project, and `nearest` never sees a project — it ranks a block. Shio is
    668 deliveries against 20 open lines and its block L is 13 against 8, which is the spread
    the reading needed and the reason it did not have to be looked for in another repository.

    Each open line is a query, standing in for the `add` that would have written it: the
    caller these rows arrive at is composing a line, and the eleven retirements RK1527 used
    are delivered entries — the right ground truth for recall and the wrong population for
    a share, there being no `add` on this side of them.
    """
    blocks: dict[str, list] = {}
    for one in roadmap.entries:
        blocks.setdefault(one.task.block, []).append(one)
    found = {}
    for block, asking_all in blocks.items():
        took = slots = 0
        delivered = 0
        for asking in asking_all:
            # Through `add`'s own composer (RK1623), once per query, because that is what the
            # exclusion is about: each open line stands in for the `add` that wrote it, so the
            # corpus is the block minus that line — which is `without` and not a filter here.
            held = Neighbours.of(
                block, roadmap=roadmap, ledger=ledger, without=asking.task.id
            )
            delivered = held.boundary
            if not held.entries:
                continue
            order = held.ranked(asking.task.symptom, asking.task.why, width)
            slots += len(order)
            took += sum(1 for index in order if held.opened(index))
        if slots:
            found[block] = (delivered, len(asking_all), took, slots)
    return found


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda one: one.name)
def test_the_open_half_takes_a_share_and_never_the_window(corpus):
    """RK1566. RK1527 set the window from one ledger's ratio and said so: 167 entries against
    a block's nine open lines, and *a project whose backlog outnumbers its deliveries would
    measure the other way*. This is the second reading, and the first thing it found is that
    §RK1566 was wrong about where to take it — Turing at its pin holds **three** open lines
    against 901 deliveries, which is this repository's shape and not its inverse.

    Shio is where the ratio moves, per block, which is the unit that matters: block L is 13
    delivered against 8 open — a 38% open share, against 3.8% in this repository's Block C —
    and the open half takes 5 of 24 slots there against 2 of 21 here. So the share tracks the
    ratio and does not swamp the window: at ten times the open share it is a fifth of the
    rows, and a delivered neighbour is never crowded out of three.

    The bound is a **ceiling and not the figure**, because a corpus moves: what may not happen
    is the open half taking a window it was measured not to need."""
    corpora.require(corpus)
    ledger = corpora.document(corpus, "changelog")
    roadmap = corpora.document(corpus, "roadmap")
    found = _slots(ledger, roadmap, VOLUNTEERED)
    if not found:
        pytest.skip(f"{corpus} carries no open line to rank against its own block")
    took = sum(one[2] for one in found.values())
    slots = sum(one[3] for one in found.values())
    assert took * 2 <= slots, {
        "block": {
            name: f"{one[0]} delivered, {one[1]} open, {one[2]} of {one[3]} slots"
            for name, one in found.items()
        }
    }


def test_the_rows_an_add_shows_are_not_the_rows_the_named_read_would(tmp_path):
    """RK1567. The `near` rows were described in two places as `delivered --near`
    volunteered, and RK1495 widened the corpus under that sentence: `add` ranks the block's
    deliveries **and** its open lines, `delivered` ranks the ledger by its own subject. So a
    caller running the read the description named got a different answer from the one shown.

    Measured over every open line here, standing in for the `add` that filed it: the two
    reads differ on **half** the queries, and on 15 of those 18 a shown row is one
    `delivered --near` cannot reach at its own wider window — because it is an open line, and
    no width reaches a corpus a verb does not rank. Shio measures the same, 10 of 20 and 8.

    Which is what settles the three ways §RK1567 named: this is not a wording that agrees
    with the read nearly always, so the row keeps `delivered`'s two **phrases** (RK1375) and
    stops claiming to be its rows. The door for each half is already printed (RK1528)."""
    config = Config.discover(HERE)
    ledger, roadmap = config.document("changelog"), config.document("roadmap")
    differ = unreachable = total = 0
    for asking in roadmap.entries:
        # `add`'s corpus, and the ledger half alone beside it — which is `delivered --near`'s,
        # a corpus with no open lines in it (RK1623). Both through the one composer, so the
        # difference these two figures are about is the halves and never a rebuild.
        both = Neighbours.of(
            asking.task.block, roadmap=roadmap, ledger=ledger, without=asking.task.id
        )
        delivered = Neighbours(delivered=both.delivered)
        if not (both.entries and delivered.entries):
            continue

        def ranked(corpus, count, asking=asking):
            return [
                corpus.entries[index].task.id
                for index in corpus.ranked(asking.task.symptom, asking.task.why, count)
            ]

        total += 1
        shown = ranked(both, VOLUNTEERED)
        if shown == ranked(delivered, VOLUNTEERED):
            continue
        differ += 1
        # The half that makes this a description defect rather than a difference of window:
        # a row the named read cannot produce however wide it is asked to be.
        unreachable += any(one not in ranked(delivered, NEAREST) for one in shown)
    assert total >= 20, "the backlog this is measured over lost its open lines"
    # A floor and not the figure: what may not happen is this becoming a claim that the two
    # reads agree, which is the sentence RK1567 removed.
    #
    # **A fifth and no longer a quarter**, because the rate decays as the backlog drains and
    # that is the point rather than a defect. Measured across one session's six ships: 15 of 37
    # at its first commit, 13 of 41, 8 of 34 — the open half of a block's corpus is what makes
    # the two reads differ, so shipping lines out of it makes them agree more often. The claim
    # this protects is not the rate: it is that `add`'s rows are not `delivered --near`'s, and
    # the sharp half below carries it — every differing query here has a row that read cannot
    # reach at any width, 8 of 8.
    assert differ * 5 >= total, {"differ": differ, "of": total}
    assert unreachable * 2 >= differ, {"unreachable at any width": unreachable, "differ": differ}


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda one: one.name)
def test_widening_the_window_gives_the_open_half_more_and_not_less(corpus):
    """The other direction, and the one that decides whether three is too narrow *for the
    half RK1495 added*. It is not: on Shio the open share rises 13.3% → 15.0% → 17.0% across
    three, four and five, so a wider window buys the open lines rows and buys the deliveries
    nothing. Which is the same verdict `test_widening_the_window_reaches_no_pair_three_does_not`
    reaches from the recall side, arrived at from the other corpus and the other half."""
    corpora.require(corpus)
    ledger = corpora.document(corpus, "changelog")
    roadmap = corpora.document(corpus, "roadmap")
    shares = []
    for width in (VOLUNTEERED, VOLUNTEERED + 1, VOLUNTEERED + 2):
        found = _slots(ledger, roadmap, width)
        if not found:
            pytest.skip(f"{corpus} carries no open line to rank against its own block")
        shares.append(
            (sum(one[2] for one in found.values()), sum(one[3] for one in found.values()))
        )
    assert all(slots for _, slots in shares)
    # Monotone and never a drop: a widening that took rows *off* the open half would mean the
    # order is not a ranking, which is the one reading this figure could carry that is a defect.
    assert [took for took, _ in shares] == sorted(took for took, _ in shares), shares


def test_widening_the_window_reaches_no_pair_three_does_not():
    """The other half of the same decision, and the one that would have been an assumption:
    the window is not too small either. Four and five reach exactly what three reaches — the
    two pairs outside are the two RK1183 recorded as correctly out of reach, where the
    retirement names the task that delivered the larger half rather than the nearest symptom."""
    config = Config.discover(HERE)
    ledger, roadmap = config.document("changelog"), config.document("roadmap")
    by_id = {entry.task.id: entry for entry in ledger.entries}
    pairs = [
        (entry, superseded(entry.task.why))
        for entry in ledger.entries
        if superseded(entry.task.why)
    ]
    reached = {}
    for count in (VOLUNTEERED, VOLUNTEERED + 1, VOLUNTEERED + 2):
        found = 0
        for retired, partner in pairs:
            block = retired.task.block
            delivered = [
                one
                for one in ledger.entries
                if one.task.block == block and one.task.id != retired.task.id
            ]
            entries = [*delivered, *(one for one in roadmap.entries if one.task.block == block)]
            order = nearest(
                claim(retired.task.symptom, retired.task.why),
                [claim(one.task.symptom, one.task.why) for one in entries],
                count,
            )
            found += partner in [entries[index].task.id for index in order]
        reached[count] = found
    assert by_id, "the ledger this is measured over is readable"
    assert len(set(reached.values())) == 1, reached


def test_the_reading_before_the_answer_is_published_and_never_stored(tmp_path, capsys):
    """RK1535. RK1500 held that the retirement corpus cannot score the query half of this read:
    every known answer is written into the field a query would join, so the ground truth is an
    input. The population that could score it is the reading given **before** the answer was
    known — the rows an `add` volunteers — and nothing records those.

    Nothing here starts to. What is asserted is that the payload already carries what a later
    join needs, so a session keeping its transcripts has the corpus without this tool storing a
    log of readings, which is not a fact about the backlog (L2)."""
    root = project(tmp_path)
    _added(root, "A first thing")
    capsys.readouterr()
    assert main([
        "-C", str(root), "add", "--block", "A", "--json",
        "--symptom", "A second thing that is nearly the first",
        "--why", "Because of a reason.",
    ]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    rows = payload["near"]
    assert rows, "nothing volunteered: this join is about nothing"
    # The two fields a later `retire --superseded-by` joins on: which line was named, and how
    # near it was said to be. Without either, a transcript records that something was shown.
    assert [one["rank"] for one in rows] == list(range(1, len(rows) + 1))
    assert all(one["id"] for one in rows)
    # And which corpus each came from, since RK1495 made it two — a hit against an open line
    # and one against a delivery are different claims about the read.
    assert {"near_recorded", "near_open"} <= set(payload)
    assert all(one["marker"] for one in rows)


def test_the_id_the_ledger_would_join_on_is_the_one_the_rows_carry(tmp_path, capsys):
    """The join stated as itself: a retirement names its partner by id, and that is the field
    these rows publish — so *was the partner volunteered, and at what rank* is answerable from
    a transcript and a ledger, with nothing in between."""
    root = project(tmp_path)
    _added(root, "A vendored decoder crashes on a truncated frame")
    capsys.readouterr()
    assert main([
        "-C", str(root), "add", "--block", "A", "--json",
        "--symptom", "The vendored decoder crashes when a frame is truncated",
        "--why", "Because of a reason.",
    ]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    named = {one["id"]: one["rank"] for one in payload["near"]}
    # The partner is in it, which is the case the read exists for — and the rank is what a
    # scoring pass reports, rather than a score this tool refuses to publish (RK441).
    assert named, payload["near"]
    assert min(named.values()) == 1
