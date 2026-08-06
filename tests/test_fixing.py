"""Normalizing the mechanical, so the remaining report is one somebody reads (RK16).

The claim: a first run against a real backlog reports dozens of violations and gets
ignored wholesale, so what is derived data must be repaired rather than reported, and
what is prose must be reported rather than repaired. Every test here is one side of that
line, plus the invariant that lets a normalizer exist at all.

**Why this needs its own write path.** Every mutator in `document.py` refuses the whole
file when any line it parsed renders back differently (L3) — and measured across this
repository, Shio and Turing, the *only* lines that are non-canonical are the two things
most worth fixing: a marker carrying an invisible codepoint, and a pointer the scheme
derives. So the guard is discharged per line instead of relaxed: a line is replaced only
by the rendering of the task parsed from it, an untouched line is carried through
byte-for-byte, and the result is re-parsed before the disk sees it — or nothing is written.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from roadkeep import fixing
from roadkeep.cli import EXIT_GATE, EXIT_OK, main
from roadkeep.config import Config
from roadkeep.fixing import REPAIRS, fix
from roadkeep.guarding import Review
from roadkeep.linting import lint

CONFIG = (
    'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    'improvements = "IMPROVEMENTS.md"\n'
)

LEDGER = """# Shipped

## Block A — The model

- ✅ **RK1** **An earlier symptom** — Because it was done.
"""

PROSE = """# Design rationale

## Block A — The model

### §RK2 The second design

The reasoning the line has no room for.

### §RK3 The third design

The reasoning the other line has no room for.
"""

CLEAN = """# Roadmap

## Block A — The model

- 📋 **RK2** (deps: RK1 ✅) **A second symptom** — Because of a reason. → §RK2
- 💭 **RK3** (deps: RK1 ✅, RK2) **A third symptom** — Because of another reason. → §RK3
"""


def project(tmp_path: Path, roadmap: str = CLEAN, config: str = CONFIG) -> Config:
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8")
    for name, body in {
        "ROADMAP.md": roadmap,
        "CHANGELOG.md": LEDGER,
        "IMPROVEMENTS.md": PROSE,
    }.items():
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def roadmap_of(config: Config) -> str:
    with (config.root / "ROADMAP.md").open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def reasons(applied) -> list[str]:
    return [reason for repair in applied.repairs for reason in repair.reasons]


# -- nothing to do ------------------------------------------------------------


def test_a_clean_file_is_not_rewritten(tmp_path):
    # Idempotence is the property that makes this safe to put in a hook: a pass with
    # nothing to say must not move the file's mtime, let alone its bytes.
    config = project(tmp_path)
    before = (tmp_path / "ROADMAP.md").read_bytes()
    applied = fix(config)
    assert applied.repairs == () and applied.files == ()
    assert (tmp_path / "ROADMAP.md").read_bytes() == before


# -- the derived: repaired, not reported --------------------------------------


def test_an_annotation_whose_target_shipped_is_derived(tmp_path):
    # The one field that goes stale with nobody editing it (RK8): RK1 is in the ledger.
    config = project(tmp_path, roadmap=CLEAN.replace("(deps: RK1 ✅)", "(deps: RK1)"))
    applied = fix(config)
    assert reasons(applied) == ["dep annotation derived"]
    assert "(deps: RK1 ✅)" in roadmap_of(config)
    assert lint(config).clean


def test_an_annotation_that_claims_too_much_is_corrected(tmp_path):
    # RK2 is open, so the ✅ on it is false in the direction that makes a ready task
    # read as blocked — which is how a backlog quietly stalls.
    config = project(tmp_path, roadmap=CLEAN.replace("RK2) **A third", "RK2 ✅) **A third"))
    applied = fix(config)
    assert reasons(applied) == ["dep annotation derived"]
    assert "(deps: RK1 ✅, RK2 📋)" in roadmap_of(config)


def test_deps_are_ordered_when_every_token_is_an_id(tmp_path):
    config = project(tmp_path, roadmap=CLEAN.replace("RK1 ✅, RK2)", "RK2, RK1 ✅)"))
    assert "deps ordered" in reasons(fix(config))
    assert "(deps: RK1 ✅, RK2)" in roadmap_of(config)


def test_a_field_of_prose_and_ids_keeps_the_order_it_was_written_in(tmp_path):
    # `Block P` and `real design partners` have no order, and sorting a mixed field would
    # move prose somebody wrote — which is exactly what a normalizer may not do.
    mixed = CLEAN.replace("(deps: RK1 ✅, RK2)", "(deps: RK2, real design partners)")
    config = project(tmp_path, roadmap=mixed)
    fix(config)
    assert "(deps: RK2, real design partners)" in roadmap_of(config)


def test_a_dep_listed_twice_is_dropped_once(tmp_path):
    config = project(tmp_path, roadmap=CLEAN.replace("(deps: RK1 ✅)", "(deps: RK1 ✅, RK1)"))
    assert "duplicate dep dropped" in reasons(fix(config))
    assert "(deps: RK1 ✅)" in roadmap_of(config)


def test_whitespace_around_a_field_is_trimmed(tmp_path):
    # The schema refuses this rather than trimming it, because the tool does not silently
    # rewrite text it did not author. `--fix` is the caller asking out loud.
    config = project(tmp_path, roadmap=CLEAN.replace("**A second symptom**", "**A second symptom **"))
    applied = fix(config)
    assert reasons(applied) == ["symptom trimmed"]
    assert "**A second symptom** —" in roadmap_of(config)


# -- the two lines L3 would not let anything else write -----------------------


def test_an_invisible_codepoint_on_the_marker_is_dropped(tmp_path):
    # Renders identically to a real marker and compares unequal to it, so the line was
    # non-canonical: no other write path in this tool could have touched this file.
    config = project(tmp_path, roadmap=CLEAN.replace("📋", "📋️", 1))
    # Reported before as `char.invisible`, naming the codepoint and its column (RK34);
    # repaired here, because a marker is a field the format derives rather than prose.
    assert [f.code for f in lint(config).findings] == ["char.invisible"]
    applied = fix(config)
    # One rule and not two (RK126): the character pass removes what is not text wherever it
    # is, so the marker slot is no longer a case of its own.
    assert reasons(applied) == ["control character(s) removed: U+FE0F"]
    assert "️" not in roadmap_of(config)
    assert lint(config).clean


def test_a_pointer_the_scheme_derives_is_rewritten(tmp_path):
    # RK27's own migration was a throwaway script for want of this.
    config = project(tmp_path, roadmap=CLEAN.replace("→ §RK2", "→ §RK9"))
    applied = fix(config)
    assert reasons(applied) == ["pointer derived from the id"]
    assert "→ §RK2" in roadmap_of(config) and "§RK9" not in roadmap_of(config)
    assert lint(config).clean


# -- the editorial: reported, not repaired ------------------------------------


def test_a_second_sentence_is_left_for_a_human(tmp_path):
    editorial = CLEAN.replace("Because of a reason.", "Because of a reason. And a second.")
    config = project(tmp_path, roadmap=editorial)
    applied = fix(config)
    assert applied.repairs == ()
    assert "why.sentences" in [f.code for f in lint(config).findings]
    assert "And a second." in roadmap_of(config)


def test_a_line_the_grammar_rejected_is_never_guessed_at(tmp_path):
    # No parse, so a fix would be an invention. The rest of the file is still normalized.
    broken = CLEAN.replace("(deps: RK1 ✅)", "(deps: RK1)") + "- 📋 **RK4** **No deps** — Nope.\n"
    config = project(tmp_path, roadmap=broken)
    applied = fix(config)
    assert reasons(applied) == ["dep annotation derived"]
    assert "- 📋 **RK4** **No deps** — Nope." in roadmap_of(config)
    assert "line.unparsed" in [f.code for f in lint(config).findings]


def test_a_fix_that_would_break_the_line_is_kept_and_reported(tmp_path):
    # The derived ✅ makes the line two characters longer, so a line at the cap cannot
    # take it. Forcing the field and breaking the limit is the wrong half to prefer.
    # 74 is exactly RK2's line with a bare dep; the derived ✅ takes it to 76.
    tight = CONFIG + "\n[limits]\nline = 74\n"
    config = project(tmp_path, roadmap=CLEAN.replace("(deps: RK1 ✅)", "(deps: RK1)"), config=tight)
    applied = fix(config)
    assert applied.repairs == () and len(applied.skipped) == 1
    # The line's own limit, reported on the field that would have to absorb it (RK183).
    assert "why.too-long" in applied.skipped[0].reason
    assert "limit of 74" in applied.skipped[0].reason
    assert "(deps: RK1)" in roadmap_of(config)


# -- rule 3: prove the output, or write nothing -------------------------------


def test_nothing_is_written_when_the_pass_cannot_prove_its_own_output(tmp_path, monkeypatch):
    # A normalizer that dropped or renamed a task is the failure no per-line check would
    # notice, so the whole file is re-parsed and compared before the disk sees any of it.
    import roadkeep.fixing as fixing
    from dataclasses import replace as dataclass_replace

    def rogue(schema, task, backlog, role):
        return dataclass_replace(task, id="RK99"), ["dep annotation derived"]

    monkeypatch.setattr(fixing, "_normalize", rogue)
    config = project(tmp_path)
    before = (tmp_path / "ROADMAP.md").read_bytes()
    applied = fixing.fix(config)
    assert applied.repairs == () and applied.files == ()
    assert applied.refused and "lost RK1" in applied.refused[0]
    assert (tmp_path / "ROADMAP.md").read_bytes() == before


# -- the command --------------------------------------------------------------


def test_the_command_normalizes_then_reports_what_is_left(tmp_path, capsys):
    both = CLEAN.replace("(deps: RK1 ✅)", "(deps: RK1)").replace(
        "Because of another reason.", "Because of another reason. And a second sentence."
    )
    project(tmp_path, roadmap=both)
    assert main(["-C", str(tmp_path), "lint", "--fix"]) == EXIT_GATE
    out = capsys.readouterr().out
    assert "fixed  RK2: dep annotation derived" in out
    assert "1 line(s) normalized" in out
    assert "why.sentences" in out and "1 problem(s)" in out


def test_a_file_left_clean_by_the_fix_exits_zero(tmp_path, capsys):
    project(tmp_path, roadmap=CLEAN.replace("(deps: RK1 ✅)", "(deps: RK1)"))
    assert main(["-C", str(tmp_path), "lint", "--fix"]) == EXIT_OK
    assert "clean" in capsys.readouterr().out


def test_json_carries_what_was_fixed_and_what_was_kept(tmp_path, capsys):
    project(tmp_path, roadmap=CLEAN.replace("(deps: RK1 ✅)", "(deps: RK1)"))
    assert main(["-C", str(tmp_path), "lint", "--fix", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["clean"] is True and payload["findings"] == []
    (fixed,) = payload["fixed"]
    assert fixed["id"] == "RK2" and fixed["reasons"] == ["dep annotation derived"]
    assert "(deps: RK1)" in fixed["before"] and "(deps: RK1 ✅)" in fixed["after"]


def test_the_file_keeps_its_line_endings(tmp_path):
    crlf = CLEAN.replace("\n", "\r\n").replace("(deps: RK1 ✅)", "(deps: RK1)")
    config = project(tmp_path, roadmap=crlf)
    fix(config)
    text = roadmap_of(config)
    assert "\r\n" in text and "\n" not in text.replace("\r\n", "")


# -- the damage inside a line, which no verb reached (RK126) ------------------

#: Shio's shape: an entry whose prose wraps onto a line the parser reads as nothing, with
#: two U+0008 in it. Every write verb takes a whole entry, so this had no repair at all.
CONTINUED = """# Shipped

## Block A — The model

- ✅ **RK1** **An earlier symptom** — Because it was done.
  A continuation line, carrying \b\b two control characters.
"""


def test_a_control_character_outside_any_entry_is_removed(tmp_path):
    config = project(tmp_path)
    with (tmp_path / "CHANGELOG.md").open("w", encoding="utf-8", newline="") as handle:
        handle.write(CONTINUED)
    config = Config.discover(tmp_path)
    assert [f.code for f in lint(config).findings] == ["char.invisible", "char.invisible"]

    applied = fix(config)

    assert reasons(applied) == ["control character(s) removed: U+0008"]
    body = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "\b" not in body
    assert "A continuation line, carrying  two control characters." in body
    # The entry above it is untouched: rule 2, on a pass that reached past the entries.
    assert "- ✅ **RK1** **An earlier symptom** — Because it was done." in body
    assert lint(Config.discover(tmp_path)).findings == ()


def test_the_repair_names_the_line_and_not_a_task_that_is_not_there(tmp_path):
    config = project(tmp_path)
    with (tmp_path / "CHANGELOG.md").open("w", encoding="utf-8", newline="") as handle:
        handle.write(CONTINUED)
    applied = fix(Config.discover(tmp_path))
    (repair,) = applied.repairs
    assert repair.id == "" and repair.lineno == 6
    assert str(repair).startswith("CHANGELOG.md:6  fixed  control character(s)")


def test_a_tab_is_text_and_is_left_where_it_is(tmp_path):
    # A control character with a rendering, and the indentation of a nested line is part of
    # the model (RK49): a pass that stripped it would re-parent somebody's task.
    config = project(tmp_path, roadmap=CLEAN.replace("- 💭 **RK3**", "\t- 💭 **RK3**"))
    applied = fix(config)
    assert "control character" not in " ".join(reasons(applied))
    assert "\t- 💭 **RK3**" in roadmap_of(config)


def test_a_tab_past_the_indentation_becomes_the_space_the_format_writes(tmp_path):
    # RK146: the finding a tab used to carry could be cleared by no verb. Past the
    # indentation it is a separator this format writes as a space, so the repair is a
    # substitution — deleting it would glue two fields into a line that no longer parses.
    config = project(tmp_path, roadmap=CLEAN.replace("A second symptom", "A second\tsymptom"))
    applied = fix(config)
    assert "**A second symptom**" in roadmap_of(config)
    assert "U+0009" in " ".join(reasons(applied))
    assert lint(Config.discover(tmp_path)).clean


def test_a_space_that_is_not_a_space_is_reported_and_never_replaced(tmp_path):
    # The other half of the split: a `Zs` renders as a space, so turning one into a space
    # is a change to somebody's text and stays the author's.
    config = project(tmp_path, roadmap=CLEAN.replace("Because of a reason.", "Because of\u00a0a reason."))
    applied = fix(config)
    assert applied.repairs == ()
    assert "\u00a0" in roadmap_of(config)
    assert [f.code for f in lint(config).findings] == ["char.space"]


def test_a_bullet_rejected_because_of_a_control_character_becomes_an_entry(tmp_path):
    # The one case rule 3 had to be asked in the other direction: the pass removed a
    # reject and added an id, which is the outcome and not a failure.
    marred = CLEAN.replace("- 📋 **RK2**", "- 📋​ **RK2**")
    config = project(tmp_path, roadmap=marred)
    # Named as the character and nothing else, which is RK34's rule: the reject the line
    # also is would only be reported as a consequence of the byte above.
    assert [f.code for f in lint(config).findings][0] == "char.invisible"
    assert [e.task.id for e in config.document("roadmap").entries] == ["RK3"]

    applied = fix(config)

    assert applied.refused == () and applied.files == ("ROADMAP.md",)
    assert "- 📋 **RK2** (deps: RK1 ✅) **A second symptom**" in roadmap_of(config)
    after = Config.discover(tmp_path)
    assert [e.task.id for e in after.document("roadmap").entries] == ["RK2", "RK3"]
    assert after.document("roadmap").rejects == ()


# -- the queue's one mechanical repair (RK328) --------------------------------


QUEUED = """# Roadmap

## Priority

What jumps the id order.

- RK1
- RK2
- RK9
- Block A

## Block A — The model

- 📋 **RK2** (deps: RK1 ✅) **A second symptom** — Because of a reason. → §RK2
- 💭 **RK3** (deps: RK1 ✅, RK2) **A third symptom** — Because of another reason. → §RK3
"""

#: The ledger with a retirement beside the shipment, which is the other terminal state.
RETIRED = LEDGER + "- 🗑 **RK4** **A fourth symptom** — Because nobody will do it.\n"


def test_the_entry_whose_task_shipped_is_dropped_and_named(tmp_path):
    # There is exactly one repair, it chooses nothing, and no sentence of anybody's is
    # touched — the same class as a stale dep annotation.
    config = project(tmp_path, roadmap=QUEUED)
    assert [f.code for f in lint(config).findings] == ["priority.shipped", "priority.unknown"]

    applied = fix(config)

    assert "- RK1\n" not in roadmap_of(config)
    assert reasons(applied) == ["queued work that shipped"]
    assert [(r.lineno, r.id) for r in applied.repairs] == [(7, "RK1")]


def test_a_retired_entry_is_the_other_terminal_state_and_goes_the_same_way(tmp_path):
    config = project(
        tmp_path, roadmap=QUEUED.replace("- RK9\n", "- RK4\n")
    )
    (tmp_path / "CHANGELOG.md").write_text(RETIRED, encoding="utf-8")
    config = Config.discover(tmp_path)

    applied = fix(config)

    assert reasons(applied) == ["queued work that shipped", "queued work that was retired"]
    assert "- RK4\n" not in roadmap_of(config)


def test_what_stays_is_the_order_and_every_entry_that_is_still_about_work(tmp_path):
    # Order is the author's whole statement; a blocked task is live; an id no file carries
    # is as likely a typo as a deletion; and a block is reopened by an `add`.
    config = project(tmp_path, roadmap=QUEUED)
    fix(config)
    assert "- RK2\n- RK9\n- Block A\n" in roadmap_of(config)


def test_emptying_the_queue_leaves_the_section_and_not_a_paragraph_break(tmp_path):
    # `without` is the removal, so the blank a one-entry queue sits between cannot double.
    config = project(tmp_path, roadmap=QUEUED.replace("- RK2\n- RK9\n- Block A\n", ""))
    fix(config)
    assert "What jumps the id order.\n\n## Block A" in roadmap_of(config)
    assert lint(Config.discover(tmp_path)).clean


def test_a_queue_repair_is_the_whole_reason_a_file_is_written(tmp_path):
    # Nothing else on this roadmap is wrong, so a pass that only ever wrote after a
    # re-render would leave the finding standing and report having done nothing.
    config = project(tmp_path, roadmap=QUEUED.replace("- RK9\n- Block A\n", ""))
    applied = fix(config)
    assert applied.files == ("ROADMAP.md",) and applied.changed == 1
    assert [f.code for f in lint(Config.discover(tmp_path)).findings] == []


def test_the_hook_that_already_runs_fix_clears_it(tmp_path, capsys):
    # `roadkeep-lint-fix` is the command, and every drop is in its report rather than
    # silent: a fixer that shortens a plan quietly is worse than the stale entry.
    project(tmp_path, roadmap=QUEUED.replace("- RK9\n", ""))
    assert main(["-C", str(tmp_path), "lint", "--fix"]) == EXIT_OK
    printed = capsys.readouterr().out
    # `gone` and not `fixed`, in the column `kept` already sits in (RK357).
    assert "ROADMAP.md:7  gone   RK1: queued work that shipped" in printed


# -- the one repair whose address outlives its line (RK357) -------------------


def test_the_address_of_a_removal_says_the_line_is_gone(tmp_path):
    """The defect, in the fixture that holds it (RK357).

    `- RK1`, `- RK2`, `- RK9` with RK1 shipped reported `ROADMAP.md:7  fixed  RK1`, and line 7
    of the file the pass had just written was `- RK2` — an entry the run never touched, under
    an address that named the one it did. Both halves are asserted: the line that moved up is
    still what lives at that address, which is why the verb has to carry the difference.
    """
    config = project(tmp_path, roadmap=QUEUED)
    applied = fix(config)
    repair = applied.repairs[0]
    assert (repair.lineno, repair.removed) == (7, True)
    assert roadmap_of(config).splitlines()[6] == "- RK2"
    assert str(repair) == "ROADMAP.md:7  gone   RK1: queued work that shipped"


def test_a_rewrite_is_still_fixed_and_its_address_still_resolves(tmp_path):
    """The other direction, which is what makes the verb worth reading: every repair but this
    one replaces a line in place, so its `file:line` means the same thing after the write."""
    config = project(tmp_path, roadmap=CLEAN.replace("(deps: RK1 ✅)", "(deps: RK1)"))
    repair = fix(config).repairs[0]
    assert repair.removed is False
    assert str(repair).endswith("fixed  RK2: dep annotation derived")
    assert roadmap_of(config).splitlines()[repair.lineno - 1] == repair.after.rstrip("\n")


def test_two_removals_in_one_pass_each_name_where_they_were_read(tmp_path):
    """The compounding case: the linenos are read before any removal, so the second entry's
    address is off by one more once the first is gone. Which is correct, and now says so."""
    project(tmp_path, roadmap=QUEUED.replace("- RK9\n", "- RK4\n"))
    (tmp_path / "CHANGELOG.md").write_text(RETIRED, encoding="utf-8")
    applied = fix(Config.discover(tmp_path))
    assert [(r.lineno, r.id, r.removed) for r in applied.repairs] == [
        (7, "RK1", True),
        (9, "RK4", True),
    ]


def test_the_run_says_once_which_tree_those_addresses_are_in(tmp_path, capsys):
    """Once per run rather than on every line (RK357). Reporting the position *before* the
    write is deliberate — the reader who wants to see what was taken needs the line and not
    the gap — so what was missing was the sentence naming which of the two trees it is."""
    project(tmp_path, roadmap=QUEUED)
    assert main(["-C", str(tmp_path), "lint", "--fix"]) == EXIT_GATE
    printed = capsys.readouterr().out
    assert "1 of them removed, at the line each was read from" in printed


def test_the_payload_carries_the_removal_on_the_list_a_consumer_already_reads(tmp_path, capsys):
    """A key and not a third list: `fixed` is the one list, and a consumer resolving addresses
    learns which are pre-pass from the payload instead of inferring it from an empty `after`."""
    project(tmp_path, roadmap=QUEUED)
    main(["-C", str(tmp_path), "lint", "--fix", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert "removed" not in payload
    assert [(f["line"], f["removed"]) for f in payload["fixed"]] == [(7, True)]


# -- the six statements of the split, held against the fixer (RK355) ----------

HERE = Path(__file__).resolve().parents[1]

#: Where each copy of RK16's split is, and the phrase that finds the statement inside it.
#: An inventory of **readers** and not of repairs: the repairs are `fixing.REPAIRS`, which is
#: what makes this a gate rather than a seventh copy. Paths because nothing derives who chose
#: to explain the split, phrases because each file says it in its own voice and the sentence a
#: hook prints is not the sentence a README writes.
STATED = (
    ("agents.md", "`--fix` repairs only the **derived**"),
    ("README.md", "`--fix` repairs only what the format"),
    ("commands/lint.md", "Whitespace, a marker's codepoint"),
    ("skills/roadkeep/SKILL.md", "`--fix` repairs only"),
)


def _statement(text: str, phrase: str) -> str:
    """The one paragraph or bullet a copy lives in, ending where the next one starts.

    Tight on purpose: `commands/lint.md` puts the derived list one bullet below a structural
    one that names a pointer, so a window taking the whole list would pass on a copy that
    named five of six. The bullet the phrase is in, and nothing after it.
    """
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if phrase in line)
    stop = start + 1
    while stop < len(lines) and lines[stop].strip():
        if re.match(r"\s*([-*]\s|\d+\.\s|#)", lines[stop]):
            break
        stop += 1
    return " ".join(lines[start:stop])


def _unnamed(statement: str) -> list[str]:
    return [word for word in REPAIRS if word not in statement.lower()]


@pytest.mark.parametrize("path,phrase", STATED, ids=[path for path, _ in STATED])
def test_every_file_that_states_the_split_names_every_repair(path, phrase):
    """RK328 added the sixth repair and reached three of the six copies (RK355).

    Nothing went red, because no test compared any of those sentences to anything — and the
    copy with the most readers, the `Stop` hook's, was one of the three left behind. This is
    RK203's shape applied to a list instead of an index: the fact is derivable, so it moves
    into something that fails, and it moves *one direction only* — that a repair is named is
    decidable, that a name has outlived its repair would mean reading the English (L4).

    Held here rather than exported and interpolated. A `reasons()` the four copies quote would
    make `guarding` import `fixing`, which is the import RK260 spent milliseconds removing
    from the hook's path, and it would flatten six deliberate phrasings into one.
    """
    statement = _statement((HERE / path).read_text(encoding="utf-8"), phrase)
    assert _unnamed(statement) == [], statement


def test_the_module_that_writes_the_repairs_states_them_too():
    """The authority is prose in the same file, so it is checked like every other copy."""
    assert fixing.__doc__ is not None
    assert _unnamed(_statement(fixing.__doc__, "**mechanical**")) == []


def test_the_copy_an_agent_reads_is_the_one_the_hook_prints(tmp_path):
    """`guarding.Review`, which is the copy RK328 left saying five (RK355).

    Built and read rather than grepped: the sentence is an f-string carrying the invocation
    this machine has, so the only honest way to hold it is to make the hook say it.
    """
    editorial = CLEAN.replace("Because of a reason.", "Because of a reason. And a second.")
    config = project(tmp_path, roadmap=editorial)
    printed = str(Review(lint(config)))
    statement = _statement(printed, "repairs what is derived")
    assert _unnamed(statement) == [], statement
