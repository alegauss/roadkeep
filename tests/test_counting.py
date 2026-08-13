"""Counting a backlog, and the miss that has to survive the count (RK10).

One claim under test, from three angles: **a count that cannot represent its own
misses is indistinguishable from a clean one.** So every assertion here is about a
line that a grep would have dropped — a broken task line, an undeclared marker, a
task under no block heading — and about the number that has to move when it exists.

The rest is bookkeeping the tool now owns instead of a reader: per block, per marker,
and the longest line, which this repository verified by hand until this task shipped.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import corpora
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.counting import NO_BLOCK, Census
from roadkeep.kernel.document import Document
from roadkeep.kernel.schema import DESIGNED, IDEA, Schema

HERE = Path(__file__).resolve().parents[1]

CLEAN = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- 💭 **RK2** (deps: RK1) **A second symptom** — Because of another reason. → §RK2

## Block B — Authoring

- 📋 **RK3** (deps: —) **A third symptom** — Because of a third reason. → §RK3
"""

LEDGER = """# Shipped

## Block A — The model

- ✅ **RK0** **An earlier symptom** — Because it was done.
"""


def project(tmp_path: Path, roadmap: str = CLEAN, changelog: str = LEDGER) -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    for name, body in {"ROADMAP.md": roadmap, "CHANGELOG.md": changelog}.items():
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


# -- the count, and the number beside it -------------------------------------


def test_a_clean_file_counts_every_line_and_reports_no_miss(tmp_path):
    census = Census.read(project(tmp_path))
    assert (census.total, census.uncounted) == (3, 0)
    assert census.markers() == {DESIGNED: 2, IDEA: 1}


def test_a_broken_line_leaves_the_total_and_moves_the_miss(tmp_path):
    # The failure this task exists to end: eight tasks and one unreadable line must
    # not report the same thing as eight tasks and nothing else.
    broken = CLEAN + "- 📋 **RK4** (deps: —) A symptom with no bold — a reason. → §RK4\n"
    census = Census.read(project(tmp_path, roadmap=broken))
    assert (census.total, census.uncounted) == (3, 1)
    (miss,) = census.missed
    assert miss.block == "B" and miss.lineno == 11
    assert "symptom is not delimited" in miss.reason


def test_an_undeclared_marker_is_a_miss_and_not_prose(tmp_path):
    # A line written with another project's marker matches nothing, so before this it
    # was read as prose: absent from the count *and* absent from the reject list.
    census = Census.read(
        project(tmp_path, roadmap=CLEAN + "- ✨ **RK5** (deps: —) **A symptom** — why.\n")
    )
    assert (census.total, census.uncounted) == (3, 1)
    assert "not a marker this project declares" in census.missed[0].reason


def test_a_shipped_marker_in_the_roadmap_is_counted_and_visible(tmp_path):
    # ✅ must never appear in the roadmap (RK1), and the answer is *not* a miss: the
    # parser reads it, so the marker breakdown shows a ✅ column where there should be
    # none and `lint` (RK14) refuses the line. Dropping it as unreadable would hide a
    # second source of truth behind a number the reader has no reason to distrust.
    config = project(
        tmp_path, roadmap=CLEAN + "- ✅ **RK6** (deps: —) **A symptom** — why.\n"
    )
    census = Census.read(config)
    assert (census.total, census.uncounted) == (4, 0)
    assert census.markers()["✅"] == 1
    codes = {
        v.code
        for entry in census.counted
        for v in census.schema.validate(entry.task)
    }
    assert "status.shipped" in codes


def test_prose_bullets_naming_a_task_are_not_misses(tmp_path):
    # The audit is only useful if it is short: a bullet whose first word is a word is
    # prose, however many bold ids follow it.
    census = Census.read(
        project(tmp_path, roadmap=CLEAN + "- See **RK1** for the design of **RK2**.\n")
    )
    assert (census.total, census.uncounted) == (3, 0)


# -- per block, including the blocks with nothing in them --------------------


def test_a_declared_block_with_no_tasks_is_a_row(tmp_path):
    census = Census.read(project(tmp_path, roadmap=CLEAN + "\n## Block C — Query\n"))
    tallies = {tally.name: tally.counted for tally in census.tallies()}
    assert tallies == {"Block A": 2, "Block B": 1, "Block C": 0}


def test_a_task_under_no_block_heading_is_counted_under_no_block(tmp_path):
    # Shio parks lines under "## Priority queue". Folding them into the block above
    # would make the column disagree with the total in the direction nobody checks.
    parked = (
        "# Roadmap\n\n## Priority queue\n\n"
        "- 📋 **RK9** (deps: —) **A parked symptom** — Because of a reason. → §RK9\n"
        + CLEAN.split("\n", 1)[1]
    )
    census = Census.read(project(tmp_path, roadmap=parked))
    tallies = {tally.name: tally.counted for tally in census.tallies()}
    assert tallies == {"Block A": 2, "Block B": 1, NO_BLOCK: 1}
    assert census.total == sum(tally.counted for tally in census.tallies())


# -- narrowing refuses what would silently return nothing -------------------


def test_selecting_a_block_keeps_that_blocks_misses(tmp_path):
    broken = CLEAN + "- 📋 **RK4** (deps: —) A symptom with no bold — a reason.\n"
    census = Census.read(project(tmp_path, roadmap=broken)).select(block="B")
    assert (census.total, census.uncounted) == (1, 1)


def test_an_undeclared_block_is_refused_rather_than_counted_as_zero(tmp_path):
    census = Census.read(project(tmp_path))
    with pytest.raises(KeyError) as caught:
        census.select(block="Z")
    assert "no heading declares Block Z" in caught.value.args[0]


def test_an_undeclared_marker_filter_is_refused(tmp_path):
    census = Census.read(project(tmp_path))
    with pytest.raises(KeyError) as caught:
        census.select(marker="✨")
    assert "not a marker this project declares" in caught.value.args[0]


def test_a_marker_filter_claims_no_misses(tmp_path):
    # A reject has no trusted status — that is why it was rejected — so a per-marker
    # count must not report a miss it cannot attribute.
    broken = CLEAN + "- 📋 **RK4** (deps: —) A symptom with no bold — a reason.\n"
    census = Census.read(project(tmp_path, roadmap=broken)).select(marker=DESIGNED)
    assert (census.total, census.missed) == (2, ())


# -- the measurement this repository used to do by hand ---------------------


def test_the_longest_line_is_derived_not_asserted(governed):
    # Read off the ledger, which is where this repository's lines are: the roadmap is empty
    # since RK21, and a longest derived from zero lines is derived from nothing.
    census = Census.read(Config.discover(governed), "changelog")
    longest = census.longest()
    assert longest is not None
    assert len(longest.raw) == max(len(e.raw) for e in census.counted)
    assert len(longest.raw) <= census.schema.line_max


def test_this_repositorys_own_files_have_nothing_uncounted(governed):
    config = Config.discover(governed)
    for role in ("roadmap", "changelog"):
        census = Census.read(config, role)
        # `missed` is the claim, and it is the one that means something on an empty file too:
        # nothing was read *and* nothing was skipped in silence. The total is the ledger's
        # floor alone — the roadmap's finished state is zero lines (RK21).
        assert census.missed == (), f"{role}: {census.missed}"
        assert census.total > 0 or role == "roadmap"


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda c: c.name)
def test_a_live_backlog_accounts_for_every_marker_bearing_line(corpus):
    # The corpora are where an unaccounted line would actually be, and the property
    # that matters is not "no misses" but "every miss has a reason". Read at the pin, so a
    # file saved half-written in another session is not this suite's verdict (RK105).
    corpora.require(corpus)
    document = corpora.document(corpus, "roadmap")
    assert document.entries
    assert all(reject.reason for reject in document.rejects)


# -- the commands ------------------------------------------------------------


def test_list_prints_the_source_line_verbatim(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "list", "--block", "A"]) == EXIT_OK
    printed = capsys.readouterr().out.splitlines()
    assert printed == CLEAN.splitlines()[4:6]


def test_list_ids_is_composable(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "list", "--marker", "📋", "--ids"]) == EXIT_OK
    assert capsys.readouterr().out.split() == ["RK1", "RK3"]


def test_list_puts_the_miss_on_stderr_so_stdout_stays_the_file(tmp_path, capsys):
    broken = CLEAN + "- 📋 **RK4** (deps: —) A symptom with no bold — a reason.\n"
    project(tmp_path, roadmap=broken)
    assert main(["-C", str(tmp_path), "list"]) == EXIT_OK
    captured = capsys.readouterr()
    assert len(captured.out.splitlines()) == 3
    assert "1 marker-bearing line(s)" in captured.err and "audit" in captured.err


def test_stats_prints_the_uncounted_row_even_at_zero(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "stats"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "uncounted     0" in out.replace("  ", "  ")
    assert "uncounted" in out and "total" in out


def test_stats_json_carries_both_numbers_per_block(tmp_path, capsys):
    broken = CLEAN + "- 📋 **RK4** (deps: —) A symptom with no bold — a reason.\n"
    project(tmp_path, roadmap=broken)
    assert main(["-C", str(tmp_path), "stats", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["total"] == 3 and payload["uncounted"] == 1
    assert payload["blocks"] == [
        {"block": "A", "counted": 2, "uncounted": 0, "markers": {"📋": 1, "💭": 1}},
        {"block": "B", "counted": 1, "uncounted": 1, "markers": {"📋": 1}},
    ]
    assert payload["longest"]["limit"] == 320


def test_audit_names_the_line_the_reason_and_the_block(tmp_path, capsys):
    broken = CLEAN + "- 📋 **RK4** (deps: —) A symptom with no bold — a reason.\n"
    project(tmp_path, roadmap=broken)
    assert main(["-C", str(tmp_path), "audit"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "ROADMAP.md:11" in out and "Block B" in out
    assert "RK4" in out and "3 counted, 1 uncounted" in out


def test_audit_reports_a_clean_file_as_counted_rather_than_saying_nothing(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "audit"]) == EXIT_OK
    assert "3 counted, none uncounted" in capsys.readouterr().out


def test_audit_exits_zero_because_reporting_is_not_the_gate(tmp_path):
    broken = CLEAN + "- 📋 **RK4** (deps: —) A symptom with no bold — a reason.\n"
    project(tmp_path, roadmap=broken)
    assert main(["-C", str(tmp_path), "audit"]) == EXIT_OK


def test_the_longest_line_is_the_longest_the_gate_will_measure(tmp_path, capsys):
    """`stats` is the number a project ratchets against, so it counts what refuses (RK430).

    It reported code points while the consumer's gate counted UTF-16 units, which is how
    a line certified at "320 of 320" failed a build — and the ratchet is exactly the
    reader that has no way to notice a systematic difference of one.
    """
    project(tmp_path)
    assert main(["-C", str(tmp_path), "stats", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)["longest"]
    raw = next(
        line
        for line in CLEAN.splitlines()
        if line.startswith("- ") and payload["id"] in line
    )
    assert payload["length"] == len(raw) + 1  # the marker is one surrogate pair
    # And the unit is published beside it, because a bare number is what let two readers
    # both be right and disagree.
    assert payload["unit"] == "utf-16-code-units"


def test_an_undeclared_block_exits_two_naming_what_is_declared(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "list", "--block", "Z"]) == EXIT_USAGE
    assert "no heading declares Block Z" in capsys.readouterr().err


# -- which silence this is (RK429) -------------------------------------------

#: Block C declared in the roadmap and filed under by nobody: a heading before its lines.
UNFILED = CLEAN + "\n## Block C — Query\n"

#: Block D's last line shipped and `block drop` took the roadmap heading, which is the
#: state `list` refused as though the label had never existed.
DELIVERED = LEDGER + "\n## Block D — The gate\n\n- ✅ **RK7** **A symptom** — Because.\n"


def test_a_block_whose_heading_only_the_ledger_keeps_is_not_a_typo(tmp_path, capsys):
    # It refused with "no heading declares Block D in ROADMAP.md", which is true about
    # that file and false about the project — the same answer a mistyped letter gets.
    project(tmp_path, changelog=DELIVERED)
    assert main(["-C", str(tmp_path), "list", "--block", "D"]) == EXIT_OK
    out = capsys.readouterr()
    # stdout stays exactly what the file holds, so a listing piped anywhere is unchanged
    # by this: the sentence goes where the uncounted note goes.
    assert out.out == ""
    assert "Block D is finished" in out.err and "records 1 filed under it" in out.err


def test_a_declared_block_nothing_was_ever_filed_under_says_which_it_is(tmp_path, capsys):
    project(tmp_path, roadmap=UNFILED)
    assert main(["-C", str(tmp_path), "list", "--block", "C"]) == EXIT_OK
    out = capsys.readouterr()
    assert out.out == "" and "Block C is empty" in out.err


def test_the_listing_carries_the_state_of_the_block_it_was_scoped_to(tmp_path, capsys):
    project(tmp_path, roadmap=UNFILED)
    assert main(["-C", str(tmp_path), "list", "--block", "C", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["total"] == 0 and payload["tasks"] == []
    assert payload["standing"]["state"] == "empty"
    # Null and not absent where nothing narrowed the listing: a key that appears only
    # sometimes is one a caller writes a branch for before it can read it.
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "list", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["standing"] is None


def test_nothing_is_said_about_a_block_whose_own_lines_the_filter_missed(tmp_path, capsys):
    # `--marker` matching none of Block A's two open lines is a fact about the filter,
    # and a sentence about the block would be the tool answering a question nobody asked.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "list", "--block", "A", "--marker", "🛠"]) == EXIT_OK
    out = capsys.readouterr()
    assert out.out == "" and out.err == ""


def test_a_live_block_missing_from_the_counted_file_is_still_a_refusal(tmp_path, capsys):
    # The narrow case is a block with nothing left anywhere. Block B has open work and no
    # ledger heading yet, so "no heading declares Block B in CHANGELOG.md" is true about
    # that file and is the answer — a silent zero here would hide the count's own scope.
    project(tmp_path)
    argv = ["-C", str(tmp_path), "list", "--role", "changelog", "--block", "B"]
    assert main(argv) == EXIT_USAGE
    assert "no heading declares Block B in CHANGELOG.md" in capsys.readouterr().err


def test_an_undeclared_marker_is_refused_on_the_empty_block_too(tmp_path, capsys):
    # The path that answers a finished block still narrows by marker first: a filter
    # nobody validated is one that silently matches nothing, which is the answer a clean
    # file gives — the whole ambiguity this module exists to remove.
    project(tmp_path, changelog=DELIVERED)
    argv = ["-C", str(tmp_path), "list", "--block", "D", "--marker", "🍕"]
    assert main(argv) == EXIT_USAGE
    assert "is not a marker this project declares" in capsys.readouterr().err


def test_the_state_of_the_scope_reaches_every_payload_that_narrows_by_one(tmp_path, capsys):
    project(tmp_path, changelog=DELIVERED)
    for verb in ("list", "stats", "audit"):
        assert main(["-C", str(tmp_path), verb, "--block", "D", "--json"]) == EXIT_OK
        payload = json.loads(capsys.readouterr().out)
        assert payload["standing"]["state"] == "finished", verb
        assert payload["standing"]["recorded"] == 1, verb


def test_the_same_sentence_reaches_the_other_two_readers_of_one_file(tmp_path, capsys):
    # `stats` and `audit` narrow through the same census, so the label that was a typo
    # to one of them was a typo to all three.
    project(tmp_path, changelog=DELIVERED)
    assert main(["-C", str(tmp_path), "stats", "--block", "D"]) == EXIT_OK
    assert "Block D is finished" in capsys.readouterr().err
    assert main(["-C", str(tmp_path), "audit", "--block", "D"]) == EXIT_OK
    assert "Block D is finished" in capsys.readouterr().err


def test_the_ledger_is_counted_under_its_own_schema(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "stats", "--role", "changelog", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["total"] == 1 and payload["markers"] == {"✅": 1}
    assert payload["uncounted"] == 0


# -- the debt a query counts where a session looks (RK1139) ----------------------


def _capture(root: Path, symptom: str, name: str = "20260101T000000Z-run-a.json") -> None:
    directory = root / ".roadkeep" / "reports"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(
        json.dumps({"symptom": symptom, "why": "Because of a reason.", "block": "A"}),
        encoding="utf-8",
    )


def test_stats_counts_the_captures_and_names_the_unfiled(tmp_path, capsys):
    """RK1139's second answer, and the one it says matters: a capture nothing counts is a note in
    a drawer, and this tool's whole argument is against those. Measured on this repository the
    moment it worked — two captures, zero filed, while `stats` had been answering `total 2`."""
    project(tmp_path)
    _capture(tmp_path, "A symptom nobody filed")
    assert main(["-C", str(tmp_path), "stats"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "captures" in printed and "0 filed" in printed
    assert ".roadkeep/reports/20260101T000000Z-run-a.json" in printed


def test_a_capture_whose_claim_the_backlog_states_is_filed(tmp_path, capsys):
    # An exact symptom match, which is what the pre-filled `add` produces: the capture's
    # symptom is verbatim what `--symptom` receives, so running it closes this row.
    filed = "- 📋 **RK9** (deps: —) **A symptom nobody filed** — Because of a reason. → §RK9\n"
    project(tmp_path, roadmap=CLEAN + filed)
    _capture(tmp_path, "A symptom nobody filed")
    assert main(["-C", str(tmp_path), "stats"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "1 filed" in printed and "unfiled" not in printed


def test_a_project_with_no_captures_gets_no_row_at_all(tmp_path, capsys):
    # Not the rule the counts above follow, and the reason is stated: `uncounted` is about the
    # file this command reports on, and a capture is not — a permanent `captures 0` would be a
    # row about nothing on every run of every project that never hit a defect in this tool.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "stats"]) == EXIT_OK
    assert "captures" not in capsys.readouterr().out


def test_the_payload_carries_the_same_three_answers(tmp_path, capsys):
    project(tmp_path)
    _capture(tmp_path, "A symptom nobody filed")
    assert main(["-C", str(tmp_path), "stats", "--json"]) == EXIT_OK
    held = json.loads(capsys.readouterr().out)["captures"]
    assert held["kept"] == 1 and held["filed"] == 0
    assert held["unfiled"] == [".roadkeep/reports/20260101T000000Z-run-a.json"]
