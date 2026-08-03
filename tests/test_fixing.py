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
from pathlib import Path

from roadkeep.cli import EXIT_GATE, EXIT_OK, main
from roadkeep.config import Config
from roadkeep.fixing import fix
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
    assert "line.too-long" in applied.skipped[0].reason
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
