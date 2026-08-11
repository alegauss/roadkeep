"""The gate, and the one property that makes it one (RK14).

Every assertion here is about a file that got past `add` — hand-edited, merged badly,
or written before a limit moved — because that is the only population `lint` exists for.
Two claims are load-bearing and the rest are the codes:

* **A defect exits 1.** A report at exit 0 is advice, and advice is what the 92 lines
  measured in Shio already had.
* **A defect is never repaired.** The file is compared byte-for-byte after the run:
  normalizing a line the parser may have misread is the corruption L3 forbids, so the
  report carries the canonical rendering and the edit stays a human's.

And the fixture that proves the format rather than asserting it: this repository's own
`docs/` must come back clean under its own `roadkeep.toml`.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from pathlib import Path

import pytest

import corpora
from conftest import GOVERNED
from surface import names
from roadkeep import linting
from roadkeep.cli import EXIT_GATE, EXIT_OK, main
from roadkeep.config import Config
from roadkeep.exporting import BEGIN, END
from roadkeep.exporting import project as exported
from roadkeep.history import HistoryUnavailable, tracked_at
from roadkeep.linting import Tree, _paths, lint, within
from roadkeep.picking import take

HERE = Path(__file__).resolve().parents[1]
#: A backlog that never heard of this tool, read where it lives and never written to.
#: Absent on any machine but the author's, so the test skips rather than fails.
SHIO = Path("D:/Git/viglet/shio/latest")

CLEAN = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- 💭 **RK2** (deps: RK1) **A second symptom** — Because of another reason. → §RK2
"""

LEDGER = """# Shipped

## Block A — The model

- ✅ **RK5** **An earlier symptom** — Because it was done.
"""

#: The same ledger with the second block declared, and the helper's default: a roadmap that
#: opens Block B and a ledger that does not is its own finding (RK380), so a fixture about
#: anything else declares both. `LEDGER` itself is what the tests *about* that state pass.
LEDGER_AB = LEDGER + "\n## Block B — Authoring\n"

PROSE = """# Design rationale

## Block A — The model

### §RK1 The first design

The reasoning the first line has no room for.

### §RK2 The second design

The reasoning the second line has no room for.
"""

CONFIG = (
    'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    'improvements = "IMPROVEMENTS.md"\n'
)


def project(
    tmp_path: Path,
    roadmap: str = CLEAN,
    changelog: str | None = LEDGER_AB,
    improvements: str | None = PROSE,
    config: str = CONFIG,
) -> Config:
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8")
    files = {"ROADMAP.md": roadmap}
    if changelog is not None:
        files["CHANGELOG.md"] = changelog
    if improvements is not None:
        files["IMPROVEMENTS.md"] = improvements
    for name, body in files.items():
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def codes(report) -> list[str]:
    return [finding.code for finding in report.findings]


# -- the fixture, and the pass -----------------------------------------------


def test_this_repository_passes_its_own_gate(checkout):
    # The format is proven by the artefact: a limit that cannot express these lines is
    # the wrong limit rather than a set of wrong lines.
    #
    # The live tree and not the `governed` copy (RK315), because `path.missing` resolves the
    # paths this ledger names against the project root: on a copy holding only the governed
    # files every one of them is a finding about the fixture. So this gets the other answer —
    # a loud skip where a concurrent session rewrote what is about to be read.
    checkout.steady(*GOVERNED)
    report = lint(Config.discover(HERE))
    assert report.clean, [str(f) for f in report.findings]
    # A floor and not a count: the lines only grow, but `ship` deletes the rationale
    # section, so the number of sections falls as the backlog empties (10 as RK22 landed).
    assert report.lines > 30 and report.sections > 3
    assert report.checked == (
        "docs/ROADMAP.md",
        "docs/CHANGELOG.md",
        "docs/IMPROVEMENTS.md",
        # The one file here the tool does not own, read because it carries the markers that
        # say it restates the backlog (RK104). `docs/index.html` carries none, so it is not
        # in this tuple — a pitch that states no count cannot state one wrongly.
        "README.md",
        "agents.md",
        ".claude/CLAUDE.md",
        # Judged because it declares what one served tool may cost (RK1059) — the one budget
        # whose subject is not a file, so the config is both what declared it and the only
        # address a finding about it can carry.
        "roadkeep.toml",
    )
    # The instruction files are inside the budget they declare, which is the reading that
    # matters: this repository is the file that reached 186 KB in the project next door.
    assert report.budgets == 2


def test_a_clean_project_exits_zero(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "clean" in out and "ROADMAP.md" in out and "CHANGELOG.md" in out


def test_a_foreign_backlog_is_judged_at_a_pin_and_the_number_is_exact():
    """The population the tool was measured against, read where it cannot move (RK105).

    `within` is the half of the gate that is decidable from one file, which is what makes
    the number below sayable at all: `lint` reads the working tree, so a magnitude asserted
    through it is one another session can change. 90-odd lines averaging 142 words against a
    one-sentence rule is what this corpus was for, and **zero** is what it holds at this pin,
    because Shio rewrote them under the limits it adopted. That is the finding, and stating
    it exactly is the difference between a corpus and a floor: the day the number moves, this
    fails on a pin somebody moved on purpose rather than on somebody else's afternoon.
    """
    corpora.require(corpora.SHIO)
    findings = within(
        corpora.config(corpora.SHIO), "roadmap", corpora.document(corpora.SHIO, "roadmap")
    )
    assert [str(f) for f in findings] == []


def test_the_gate_runs_over_a_foreign_backlog_and_writes_nothing():
    # The other half, and the one that has to read the live tree: a whole `lint` run over
    # somebody else's checkout must produce a report rather than an exception, and leave
    # every byte alone. No magnitude is asserted — that is the test above, at the pin.
    roadmap = SHIO / "docs" / "ROADMAP.md"
    if not roadmap.is_file():
        pytest.skip(f"{roadmap} is not on this machine")
    config = Config.parse(
        {"prefix": "SH", "ref_scheme": "outline", "files": {"roadmap": "docs/ROADMAP.md"}},
        root=SHIO,
    )
    before = roadmap.read_bytes()
    report = lint(config)
    assert report.lines == len(config.document("roadmap").entries)
    assert roadmap.read_bytes() == before


# -- the resident file's budget, and what it is spent on (RK203) --------------


def _layout_index() -> str:
    """The fenced block under `## Layout` in this repository's `agents.md`."""
    lines = (HERE / "agents.md").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("```"))
    stop = next(i for i, line in enumerate(lines[start + 1 :], start + 1) if line.startswith("```"))
    return "\n".join(lines[start + 1 : stop])


def test_every_module_is_named_in_the_layout_index():
    """The index grows with the package, so what holds it is a gate and not a habit (RK203).

    `agents.md` sat at 125 of 125 lines and nothing checked what those lines *said*, so the
    only thing anything held about the index was its cost: naming a module took an unrelated
    entry's second line, and two modules — `claiming` and `locking` — were simply never
    added. An index that silently stops being an index is worse than no index, because a
    turn reads it and concludes the module is not there.

    Measured before deciding, which is what the idea asked for: the fenced block is a fifth
    of the line budget and a quarter of the bytes, and the file binds on lines. So the answer
    is none of deriving it (a module's purpose is prose, L4), budgeting it apart (two numbers
    where one was the point) or moving it out (a read on the turn that needs it) — the cost
    was never the problem. It is held here, and paid for out of the prose the budget was
    written to refuse.

    One direction only. That a module is named is decidable; that a name has outlived its
    module would mean reading the entry's English, and this repository does not do that (L4).

    A **subpackage is named as one entry** and not module by module (RK494): `verbs/` holds a
    module per verb family, each named after the domain module it calls, so naming them here
    would spend the index's room re-stating names it already carries — and the package's own
    `__init__` docstring is the authority on what is in it, which is this file's rule for
    every other module too. What is held is that the directory appears.
    """
    index = _layout_index()
    assert names()
    unnamed = [
        module
        for module in names()
        # Word boundaries that exclude `-` too: `blocking` must not answer for `locking`,
        # which is the false negative that hid one of the two missing entries.
        if not re.search(rf"(?<![\w-]){re.escape(module)}(?![\w-])", index)
    ]
    assert unnamed == []


#: Top-level entries the index does not name, and why each is not a surface (RK1016). A list
#: rather than a rule, for `_MAY_SPELL`'s reason: an exemption nobody can see reads exactly
#: like a rule being kept, and the next entry added to this tree is a decision somebody makes
#: rather than a silence somebody inherits.
UNINDEXED = {
    "LICENSE": "a file a repository has, not a surface anything runs",
    "README.md": "the projection, named in the prose that governs it rather than the index",
    "pyproject.toml": "how the package is built, which `agents.md` states as a section",
    ".gitignore": "one line about a directory the tree does not carry",
    ".githooks": "named where it is wired, in the committing section",
    ".vscode": "this checkout's own editor settings, which no adopting project gets",
    ".claude": "the instruction file, whose budget the index is inside",
}


def _named(index: str, entry: str) -> bool:
    """Is this top-level entry addressed in the index, as the index spells addresses?

    A directory is written with its slash — `editor/`, `src/roadkeep/`, `docs/ROADMAP.md` —
    and a file by its own name. The slash is what makes this a check and not a word search:
    the prose beside an entry says *the editor host*, and matching that would let a sentence
    about a surface stand in for an entry naming it, which is the index quietly stopping.
    """
    spelled = f"{entry}/" if (HERE / entry).is_dir() else entry
    return re.search(rf"(?<![\w./-]){re.escape(spelled)}", index) is not None


def test_every_surface_this_repository_carries_is_named_in_the_index():
    """RK203's gate, over the half it left to a reader (RK1016).

    That task made the index a gate for `src/roadkeep` and stopped there. The lines under it
    name the other surfaces by hand — the gate's three, the plugin's five — and nothing
    checked those: `editor/` and `scripts/build_vsix.py` shipped with the index mentioning
    neither, and the count in the prose beside them was wrong.

    The failure is the one RK203 named, one level out. An index that silently stops being an
    index is worse than no index, because a turn reads it and concludes the thing is not
    there — and a *surface* is exactly what a turn looks for before deciding where a change
    goes.

    Decidable the same way the module check is, and the exemptions are the whole risk: what
    is not named has to be named **here**, with a reason, which is what keeps the list from
    growing into a way of not writing an index entry.
    """
    index = _layout_index()
    # What the **repository** carries and never what the disk holds: a cache directory is
    # somebody's afternoon and an index that had to name one would be an index of this
    # machine (RK217 draws the same line for a path claim).
    listed = subprocess.run(
        ["git", "-C", str(HERE), "ls-files"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if listed.returncode != 0:
        pytest.skip("git cannot list this tree, so there is nothing to compare the index to")
    carried = {line.split("/", 1)[0] for line in listed.stdout.splitlines() if line}
    unnamed = [
        name
        for name in sorted(carried)
        if name not in UNINDEXED and not _named(index, name)
    ]
    assert unnamed == [], unnamed


def test_nothing_is_exempted_from_the_index_that_the_tree_no_longer_carries():
    """The other direction, for :data:`UNHELD`'s reason: an exemption for a path that left is
    a sentence nobody can check, and the list is only worth what it still describes."""
    gone = [name for name in UNINDEXED if not (HERE / name).exists()]
    assert gone == [], gone


def test_the_index_is_a_fifth_of_the_budget_and_the_prose_is_the_rest():
    """The number the next compression should read before it compresses the index.

    Stated as a bound rather than an exact figure: the point is which of the two kinds of
    text dominates, and a test that failed on one line moving would be re-run rather than
    read. The budget itself is `[budgets]` in `roadkeep.toml` and `lint` is what holds it —
    this only says what the room is going to.
    """
    text = (HERE / "agents.md").read_text(encoding="utf-8")
    index = _layout_index()
    share = len(index.splitlines()) * 100 // len(text.splitlines())
    assert 15 <= share <= 30, share


# -- what the tail rule silences, counted rather than argued (RK189) ----------


def _unresolved(corpus):
    """Every `path.missing` the pinned ledger produces, with and without RK173's tail rule.

    `_paths` is called rather than re-derived: it is the function being measured, and the
    three conditions it composes — on disk, beside the ledger, anywhere in the tree — are
    stated there once. A test that restated them would measure a copy, and the copy is what
    would still pass the day the original changed.
    """
    corpora.require(corpus)
    # `checkout` and not `config` (RK192): every read below names the revision itself —
    # `Tree(…, rev)` runs git — so this is the one place a live root is the input.
    config = corpora.checkout(corpus)
    documents = {"changelog": corpora.document(corpus, "changelog")}
    tree = Tree(config, rev=corpus.rev)
    with_tail = _paths(config, documents, tree)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(Tree, "anywhere", lambda self, token: False)
        without_tail = _paths(config, documents, Tree(config, rev=corpus.rev))
    return config, with_tail, without_tail


def test_the_tail_rule_silences_nothing_at_all_on_shio():
    """Half the population RK173 was justified over contributes no evidence either way.

    Every path Shio's ledger names resolves from the root or from the ledger's own directory
    (RK51), so the widening is exercised zero times across 1278 tracked files. Worth an
    assertion rather than a shrug: a widening argued from one corpus and measured on two is
    a widening measured on one, and the day this stops being zero is the day Shio grew the
    monorepo shape the rule is for.
    """
    _, with_tail, without_tail = _unresolved(corpora.SHIO)
    assert with_tail == [] and without_tail == []


def test_the_tail_rule_earns_four_of_its_five_silences_on_a_unique_file():
    """The floor §RK189 asked for, and it refuses the narrowing it proposed.

    Turing's ledger leaves six tokens unresolved from the root and from `docs/`. The tail
    rule silences five and reports one — `frontend/apps/site/scripts/emit-model-catalog.mjs`,
    a file that moved, which is the only true finding this check has ever produced on a live
    corpus and is still produced.

    Four of the five silences are two-segment tokens matching **exactly one** tracked file,
    so the match identifies the artefact rather than merely finding a name. The fifth is the
    one-segment `./package.json` that motivated RK173, and it matches thirteen — the widening
    at its widest, on the one token where "does the repository have it" is genuinely all a
    reader means.

    So requiring a slash, the narrowing the idea proposed, buys nothing: it would re-report
    that `package.json` — false by this check's own question — and change none of the other
    five. Measured, not argued, and this is the number that says so.
    """
    config, with_tail, without_tail = _unresolved(corpora.TURING)
    assert [f.id for f in with_tail] == ["T759"]
    assert len(without_tail) == 6

    silenced = sorted(
        f.message.removeprefix("names ").removesuffix(", which is not in the repository")
        for f in without_tail
        if f not in with_tail
    )
    assert silenced == [
        "./package.json",
        "references/return-policy.md",
        "scripts/check-size.mjs",
        "scripts/prerender.mjs",
        "scripts/rma.py",
    ]
    names = [name for name in tracked_at(config, corpora.TURING.rev) if name]
    matches = {
        token: sum(1 for name in names if name.endswith(token.removeprefix(".")))
        for token in silenced
    }
    assert matches == {
        "./package.json": 13,
        "references/return-policy.md": 1,
        "scripts/check-size.mjs": 1,
        "scripts/prerender.mjs": 1,
        "scripts/rma.py": 1,
    }


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda c: c.name)
def test_the_exposure_the_tail_rule_accepts_is_a_sixth_of_the_tree(corpus):
    """What a one-segment match *could* be wrong about, so the ledgers' record is readable.

    17% of the files in each corpus share a basename with at least one other file — 16
    `package.json` in Shio, 23 `README.md` in Turing. That is the risk the rule takes, and
    the two tests above are what say it was not realised: the ledgers write two segments
    where they mean a file and one segment only where they mean the repository.
    """
    corpora.require(corpus)
    names = [name for name in tracked_at(corpora.checkout(corpus), corpus.rev) if name]
    counts = Counter(name.split("/")[-1] for name in names)
    ambiguous = sum(count for count in counts.values() if count > 1)
    assert 15 <= ambiguous * 100 // len(names) <= 19


# -- the schema, re-read where nothing was watching --------------------------


def test_a_second_sentence_is_found_in_a_file_add_never_saw(tmp_path):
    # The rule `add` refuses at input, on a line that arrived by hand.
    drifted = CLEAN.replace(
        "Because of a reason.", "Because of a reason. And then a second sentence."
    )
    report = lint(project(tmp_path, roadmap=drifted))
    assert "why.sentences" in codes(report)
    assert report.findings[0].id == "RK1"
    assert report.findings[0].lineno == 5


def test_an_over_length_line_names_the_limit(tmp_path):
    padded = CLEAN.replace("Because of a reason.", "Because of " + "a long reason " * 20)
    report = lint(project(tmp_path, roadmap=padded))
    # One finding for one overrun (RK183): the `why` carries the line's own limit, so
    # `line.too-long` beside it would be the same characters counted a second way.
    assert "why.too-long" in codes(report)
    assert "line.too-long" not in codes(report)


def test_a_shipped_marker_in_the_roadmap_fails(tmp_path):
    report = lint(project(tmp_path, roadmap=CLEAN.replace("📋", "✅", 1)))
    assert "status.shipped" in codes(report)


def test_a_task_under_no_block_heading_is_a_finding(tmp_path):
    # `stats` calls it "(no block)" and counts it; here it is the defect it is.
    homeless = CLEAN.replace("## Block A — The model", "## Priority queue")
    report = lint(project(tmp_path, roadmap=homeless))
    assert codes(report).count("block.missing") == 2


# -- the line the parser could not read at all -------------------------------


def test_a_marker_bearing_line_the_grammar_rejected_fails_the_gate(tmp_path):
    # `audit` (RK10) prints this at exit 0 because reporting is not the gate. This is.
    broken = CLEAN + "- 📋 **RK3** **No deps field** — Because it was hand-written.\n"
    report = lint(project(tmp_path, roadmap=broken))
    assert "line.unparsed" in codes(report)
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_GATE


# -- L3: reported, never repaired --------------------------------------------


def test_a_line_that_does_not_round_trip_is_named_and_left_alone(tmp_path):
    # The pointer is derived from the id (RK27), so a hand-chosen anchor both violates
    # the schema and stops round-tripping — two findings on one line, and no rewrite.
    wrong_anchor = CLEAN.replace("→ §RK1", "→ §RK9")
    config = project(tmp_path, roadmap=wrong_anchor)
    before = (tmp_path / "ROADMAP.md").read_bytes()
    report = lint(config)
    assert {"ref.mismatch", "line.non-canonical"} <= set(codes(report))
    assert (tmp_path / "ROADMAP.md").read_bytes() == before
    canonical = next(f for f in report.findings if f.code == "line.non-canonical")
    assert "§RK1" in canonical.message


# -- one id, two answers ------------------------------------------------------


def test_one_id_twice_in_one_file_is_a_finding(tmp_path):
    twice = CLEAN + "- 📋 **RK1** (deps: —) **A repeat** — Because it was pasted. → §RK1\n"
    report = lint(project(tmp_path, roadmap=twice))
    duplicate = next(f for f in report.findings if f.code == "id.duplicate")
    assert duplicate.id == "RK1" and "line 5" in duplicate.message


def test_an_id_in_both_files_is_a_finding(tmp_path):
    both = LEDGER + "- ✅ **RK1** **The same task** — Because it shipped.\n"
    report = lint(project(tmp_path, changelog=both))
    assert "id.two-files" in codes(report)


def test_an_entry_naming_a_half_is_not_a_contradiction(tmp_path):
    # RK122: the ledger's own way of saying "this much landed" (RK121). Reporting it would
    # make the gate loud about precisely the entries written the way the tool writes them.
    half = LEDGER + "- ✅ **RK1 (local half)** **The same task** — Because half shipped.\n"
    report = lint(project(tmp_path, changelog=half))
    assert "id.two-files" not in codes(report)


def test_a_partial_line_the_ledger_names_plainly_is_not_a_contradiction(tmp_path):
    # The measured case: Shio's ⏳ SH238 carries a bare id in the ledger, which is the
    # honest way to write a half — and it was the *only one of seven* the gate reported,
    # the six others being silent behind a parenthetical the parser could not read.
    both = LEDGER + "- ✅ **RK1** **The same task** — Because half of it shipped.\n"
    halved = CLEAN.replace("- 📋 **RK1**", "- ⏳ **RK1**")
    report = lint(project(tmp_path, roadmap=halved, changelog=both))
    assert "id.two-files" not in codes(report)


def test_a_line_shipped_and_left_behind_is_still_the_finding(tmp_path):
    # The shape the rule was written for stays loud: an ordinary open marker, and an entry
    # qualifying nothing. Neither file says halves, so open and gone are not both true.
    both = LEDGER + "- ✅ **RK2** **The same task** — Because it shipped.\n"
    report = lint(project(tmp_path, changelog=both))
    two_files = next(f for f in report.findings if f.code == "id.two-files")
    assert two_files.id == "RK2" and "CHANGELOG.md" in two_files.message


# -- deps nothing will satisfy ------------------------------------------------


def test_a_dep_in_neither_file_is_a_finding(tmp_path):
    report = lint(project(tmp_path, roadmap=CLEAN.replace("(deps: RK1)", "(deps: RK9)")))
    unknown = next(f for f in report.findings if f.code == "deps.unknown")
    assert unknown.id == "RK2" and "RK9" in unknown.message


def test_a_dep_on_a_retired_task_is_a_finding(tmp_path):
    # RK32's other door: the record says the work will not happen, so the dependent
    # line is the author's next edit — reported at `retire`, gated here.
    gone = LEDGER + "- 🗑 **RK7** **A dropped symptom** — abandoned: the premise went.\n"
    report = lint(
        project(tmp_path, roadmap=CLEAN.replace("(deps: RK1)", "(deps: RK7)"), changelog=gone)
    )
    assert "deps.retired" in codes(report)


def test_a_dep_on_a_block_no_heading_declares_is_a_finding(tmp_path):
    report = lint(
        project(tmp_path, roadmap=CLEAN.replace("(deps: RK1)", "(deps: Block Z)"))
    )
    assert "deps.block" in codes(report)


def test_a_dep_on_a_block_declared_before_its_first_line_is_a_finding(tmp_path):
    # The gate and the queue answer this state differently on purpose (RK432): a tier that
    # fires on nothing is harmless and is a Note, while a *dep* on an unstarted block gates
    # a line on work that nobody has filed, which is what `deps.block` is for.
    report = lint(
        project(
            tmp_path,
            roadmap=CLEAN.replace("(deps: RK1)", "(deps: Block B)") + "\n## Block B — Authoring\n",
        )
    )
    (found,) = [f for f in report.findings if f.code == "deps.block"]
    assert found.id == "RK2" and "is empty" in found.message


def test_a_dep_on_a_block_with_work_in_the_store_is_not_a_finding(tmp_path):
    # A deferred dep is recorded, findable and revivable, so it falls through here as a
    # task-level one does (RK92) — and the ⏸ the annotation now derives is not yet in the
    # file, which is `deps.stale`'s job and `--fix`'s door.
    config = CONFIG + 'deferred = "DEFERRED.md"\n'
    (tmp_path / "DEFERRED.md").write_text(
        "## Block B — Authoring\n"
        "- ⏸ **RK6** (deps: —) **A symptom** — set aside: waiting. → §RK6\n",
        encoding="utf-8",
    )
    report = lint(
        project(
            tmp_path,
            roadmap=CLEAN.replace("(deps: RK1)", "(deps: Block B)") + "\n## Block B — Authoring\n",
            config=config,
        )
    )
    assert "deps.block" not in codes(report)
    assert "deps.stale" in codes(report)


def test_a_dep_outside_the_backlog_is_not_a_finding(tmp_path):
    # Turing writes `(deps: real design partners)` and means it: failing every file that
    # states an honest external dep would make the gate unadoptable.
    outside = CLEAN.replace("(deps: RK1)", "(deps: real design partners)")
    assert lint(project(tmp_path, roadmap=outside)).clean


def test_a_dep_on_another_declared_block_is_not_a_finding(tmp_path):
    # Shio's `(deps: Block P)` is legitimate: a block with open work is a dep that is
    # merely unsatisfied, which is what `deps` answers and not what the gate refuses.
    two_blocks = CLEAN.replace(
        "- 💭 **RK2** (deps: RK1)",
        "\n## Block B — Authoring\n\n- 💭 **RK2** (deps: Block A)",
    )
    assert lint(project(tmp_path, roadmap=two_blocks)).clean


def test_a_block_dep_the_task_is_itself_inside_is_a_cycle(tmp_path):
    # Block A cannot empty until RK2 ships, so RK2 waits on itself — one member, and a
    # sentence that says so instead of "wait on each other".
    inside = CLEAN.replace("(deps: RK1)", "(deps: Block A)")
    report = lint(project(tmp_path, roadmap=inside))
    (cycle,) = [f for f in report.findings if f.code == "deps.cycle"]
    assert cycle.id == "RK2" and "its own blocker set" in cycle.message


# -- the annotation that goes stale by itself (RK8) --------------------------


def test_an_annotation_that_no_longer_matches_its_target_is_a_finding(tmp_path):
    stale = CLEAN.replace("(deps: RK1)", "(deps: RK1 ✅)")
    report = lint(project(tmp_path, roadmap=stale))
    finding = next(f for f in report.findings if f.code == "deps.stale")
    assert "RK1 📋" in finding.message


# -- one label, two headings (RK391) -----------------------------------------


def test_a_label_two_headings_declare_is_a_finding_naming_both(tmp_path):
    twice = CLEAN + "\n## Block A — The model again\n"
    report = lint(project(tmp_path, roadmap=twice))
    (finding,) = [f for f in report.findings if f.code == "block.repeated"]
    # At the second, naming the first: the fix is an editorial merge of two regions, and
    # nothing but the two addresses locates it.
    assert finding.file == "ROADMAP.md" and finding.lineno == 8
    assert "already declared on line 3" in finding.message
    assert not report.clean


def test_the_rationale_file_is_judged_by_the_same_rule(tmp_path):
    # `section add` resolves a block there the way `add` does in the roadmap, so the file
    # filed under the same headings gets the same rule.
    twice = PROSE + "\n## Block A — The model again\n"
    report = lint(project(tmp_path, improvements=twice))
    (finding,) = [f for f in report.findings if f.code == "block.repeated"]
    assert finding.file == "IMPROVEMENTS.md"


def test_the_finding_names_the_verb_where_the_verb_would_work(tmp_path):
    # RK417, measured on a real corpus: one of the two stood over nothing and the removal
    # took exactly that one out, in one command — and the report stopped at the diagnosis.
    twice = CLEAN + "\n## Block A — The model again\n"
    report = lint(project(tmp_path, roadmap=twice, improvements=None))
    (finding,) = [f for f in report.findings if f.code == "block.repeated"]
    assert "`block drop A` takes the empty one out" in finding.message


def test_two_regions_that_both_hold_work_are_told_the_verb_that_folds_them(tmp_path):
    # The clause is conditional, and that is what makes it honest: the *removal* refuses a
    # heading with work under it, so naming it here would name a command that refuses. What
    # it named instead was "a merge by hand" — prose left behind when RK403 shipped the verb
    # that does exactly this, and an edit the guard denies (RK425).
    both = CLEAN + (
        "\n## Block A — The model again\n\n"
        "- 📋 **RK3** (deps: —) **A third symptom** — Because of a third. → §RK3\n"
    )
    report = lint(project(tmp_path, roadmap=both, improvements=None))
    (finding,) = [f for f in report.findings if f.code == "block.repeated"]
    assert "block merge A" in finding.message
    assert "moving the 1 line(s) under it" in finding.message
    assert "block drop" not in finding.message


def test_a_file_where_nothing_is_removable_silences_the_offer_for_the_others(tmp_path):
    # That removal is all-or-nothing across the governed set: one file it would refuse on
    # refuses the run, including the files whose heading *was* removable.
    twice = CLEAN + "\n## Block A — The model again\n"
    prose = PROSE + "\n## Block A — The model again\n\n### §RK9 A design\n\nProse.\n"
    report = lint(project(tmp_path, roadmap=twice, improvements=prose))
    assert all(
        "block drop" not in f.message
        for f in report.findings
        if f.code == "block.repeated"
    )


def test_three_headings_under_one_label_are_reported_twice(tmp_path):
    thrice = CLEAN + "\n## Block A — Again\n\n## Block A — And again\n"
    report = lint(project(tmp_path, roadmap=thrice))
    repeats = [f for f in report.findings if f.code == "block.repeated"]
    # Each later heading is its own line to delete, and each names the first one.
    assert [f.lineno for f in repeats] == [8, 10]
    assert all("already declared on line 3" in f.message for f in repeats)


def test_the_same_label_in_two_files_is_the_normal_state(tmp_path):
    # Block A is declared in the roadmap, the ledger and the rationale file: the rule is
    # about one label twice in *one* file, and every governed file names the same blocks.
    assert not [
        f for f in lint(project(tmp_path)).findings if f.code == "block.repeated"
    ]


# -- the pen and the judge, where they are two versions (RK415) --------------


def test_a_plugin_older_than_the_gate_is_a_note_and_not_a_finding(tmp_path, monkeypatch):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_provenance import wired

    config = project(tmp_path)
    wired(tmp_path / "config", tmp_path)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "config"))

    report = lint(config)
    # A cache lagging a checkout is allowed; what is not survivable is not being told (RK79),
    # so the exit code does not move and the sentence is said once per commit.
    assert report.clean
    (note,) = [n for n in report.notes if n.code == "engine.disagreement"]
    assert "the plugin wired to this project is 0.1.285" in note.message


def test_a_run_over_a_revision_says_nothing_about_engines(tmp_path, monkeypatch):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_provenance import wired

    config = project(tmp_path)
    wired(tmp_path / "config", tmp_path)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "config"))

    # `--baseline` judges the files as they were and the engines are a fact about right now,
    # so the same note subtracted from itself would read as debt the moment they agreed.
    assert not [
        n for n in linting._examine(config, since=None, tree=Tree(config, "HEAD")).notes
        if n.code == "engine.disagreement"
    ]


# -- the block the ledger cannot receive work into (RK380) -------------------

PLANNED = (
    CLEAN
    + """
## Block B — Authoring

- 📋 **RK3** (deps: —) **A third symptom** — Because of a third reason. → §RK3
- 📋 **RK4** (deps: —) **A fourth symptom** — Because of a fourth reason. → §RK4
"""
)


def test_a_block_with_open_lines_and_no_ledger_heading_is_a_finding(tmp_path):
    report = lint(project(tmp_path, roadmap=PLANNED, changelog=LEDGER, improvements=None))
    (finding,) = [f for f in report.findings if f.code == "block.unrecorded"]
    # At the heading, once, counting the work that cannot be delivered — and naming the
    # verb, so the answer is the command rather than a diagnosis to research.
    assert finding.file == "ROADMAP.md" and finding.lineno == 8
    assert "2 open line(s)" in finding.message
    assert 'block add B --title "<its title>"' in finding.message
    assert not report.clean


FLAT = "# Shipped\n\nProse, and no block heading anywhere in it.\n"


def test_a_ledger_organised_by_nothing_is_one_finding_about_the_file(tmp_path):
    # One thing is wrong with that project — its ledger has no headings — and saying it once
    # per roadmap heading is the same omission reported as many defects (RK411).
    report = lint(project(tmp_path, roadmap=PLANNED, changelog=FLAT, improvements=None))
    assert not [f for f in report.findings if f.code == "block.unrecorded"]
    (finding,) = [f for f in report.findings if f.code == "block.unorganised"]
    # Against the ledger and at no line, where `file.missing` already reports a whole-file
    # fact — and counting the work waiting rather than naming every block it is under.
    assert finding.file == "CHANGELOG.md" and finding.lineno is None
    assert "plans 4 open line(s) under 2 of them" in finding.message
    # One label, because `--organise` is needed for the first heading and never the second.
    assert 'block add A --title "<its title>" --organise changelog' in finding.message


def test_a_ledger_organised_by_nothing_over_a_backlog_with_no_open_line_is_clean(tmp_path):
    # How every project starts. It is a defect only once there is work it cannot receive.
    empty = "# Roadmap\n\n## Block A — The model\n"
    report = lint(project(tmp_path, roadmap=empty, changelog=FLAT, improvements=None))
    assert not [f for f in report.findings if f.code == "block.unorganised"]


def test_a_roadmap_heading_over_nothing_is_a_block_being_drafted(tmp_path):
    empty = CLEAN + "\n## Block B — Authoring\n"
    report = lint(project(tmp_path, roadmap=empty, changelog=LEDGER))
    assert not [f for f in report.findings if f.code == "block.unrecorded"]


# -- the defect the graph finds ----------------------------------------------


def test_a_cycle_is_reported_once_for_the_group(tmp_path):
    looping = CLEAN.replace("(deps: —)", "(deps: RK2)")
    report = lint(project(tmp_path, roadmap=looping))
    cycles = [f for f in report.findings if f.code == "deps.cycle"]
    assert len(cycles) == 1 and cycles[0].id == "RK1"
    assert "RK1 ↔ RK2" in cycles[0].message


# -- the file that is not there ----------------------------------------------


def test_a_declared_file_that_is_absent_is_reported_not_crashed(tmp_path):
    report = lint(project(tmp_path, changelog=None))
    missing = next(f for f in report.findings if f.code == "file.missing")
    assert missing.file == "CHANGELOG.md" and missing.lineno is None
    assert report.lines == 2  # the roadmap was still read


def test_a_finding_about_a_file_the_report_never_read_sorts_last(tmp_path):
    """The rule `checked` doubles as, stated rather than left in a `dict.get` default (RK365).

    `checked` is what the gate judged *and* the order findings print in, so a finding about a
    file that is not in it has no place in that order — and the answer is the end, because the
    report is read against the list. An absent declared file is the live case: it is a finding
    with no document behind it, so nothing put it in `checked`.

    Right by accident until RK354 put `roadkeep.toml` in the list; held here now, so a check
    added tomorrow against a file nobody was told was read cannot land in the middle.
    """
    report = lint(project(tmp_path, changelog=None, roadmap=CLEAN.replace(
        "Because of another reason.", "Because of another reason. And a second sentence."
    )))
    assert "CHANGELOG.md" not in report.checked
    assert {f.file for f in report.findings} == {"ROADMAP.md", "CHANGELOG.md"}
    assert [f.file for f in report.findings][-1] == "CHANGELOG.md"


# -- the pointer, resolved in both directions (RK15) -------------------------


def test_a_pointer_to_a_section_that_does_not_exist_fails(tmp_path):
    # Worse than no pointer: it makes a reader stop looking.
    report = lint(project(tmp_path, improvements=PROSE.replace("§RK2", "§RK7")))
    unresolved = next(f for f in report.findings if f.code == "ref.unresolved")
    assert unresolved.id == "RK2" and "IMPROVEMENTS.md" in unresolved.message
    assert unresolved.file == "ROADMAP.md"  # where the broken pointer is written


def test_a_pointer_quoted_inside_a_sentence_is_not_scanned(tmp_path):
    # §RK15's own trap: the `why` quotes a pointer as an example of one, and a scan over
    # the raw line would report that quotation as the design that does not exist. The
    # rendered `ref` field is the only pointer, and here it resolves.
    quoting = CLEAN.replace(
        "Because of another reason.", "Because a `→ §RK9` in prose is not a pointer."
    )
    assert lint(project(tmp_path, roadmap=quoting)).clean


def test_a_section_whose_task_shipped_and_was_not_dropped_fails(tmp_path):
    # `ship` deletes the section as one of its three edits, so this is a hand edit.
    survived = PROSE + "\n### §RK5 The shipped design\n\nStill here after the ship.\n"
    report = lint(project(tmp_path, improvements=survived))
    stale = next(f for f in report.findings if f.code == "section.stale")
    assert stale.id == "RK5" and stale.file == "IMPROVEMENTS.md"


def test_a_section_no_line_points_at_is_an_orphan(tmp_path):
    orphaned = PROSE + "\n### §RK7 A design for nothing\n\nProse nothing points at.\n"
    report = lint(project(tmp_path, improvements=orphaned))
    assert [f.id for f in report.findings if f.code == "section.orphan"] == ["RK7"]


def test_a_subsection_of_a_live_task_belongs_to_it(tmp_path):
    # RK114: the anchor is derived from the id, so `§RK1.1` is RK1's — and RK1 is open.
    # Nothing points at a sub-anchor, so if it were owned by nobody it would also be
    # measured by nobody, which is the exemption the two assertions below close.
    nested = PROSE + "\n#### §RK1.1 A part of the first design\n\nMore reasoning.\n"
    assert lint(project(tmp_path, improvements=nested)).clean


def test_a_subsection_left_behind_by_a_renumber_is_an_orphan(tmp_path):
    # The measurement in §RK114: `renumber RK1 --to RK9` moves `§RK1` and leaves `§RK1.1`,
    # and the file came back clean — no pointer resolves to a sub-anchor, so `_pointers`
    # cannot see it, and matching the whole anchor against the id pattern exempted it here.
    stranded = PROSE + "\n#### §RK7.1 A part of a design for nothing\n\nProse.\n"
    report = lint(project(tmp_path, improvements=stranded))
    orphan = next(f for f in report.findings if f.code == "section.orphan")
    assert orphan.id == "RK7.1" and "RK7" in orphan.message


def test_a_subsection_of_a_shipped_task_is_stale(tmp_path):
    # `ship` deletes the section, and a section's subtree goes with it — so one that is
    # still here outlived the ship the same way its parent would have.
    survived = PROSE + "\n#### §RK5.1 A part of the shipped design\n\nStill here.\n"
    report = lint(project(tmp_path, improvements=survived))
    stale = next(f for f in report.findings if f.code == "section.stale")
    assert stale.id == "RK5.1" and "RK5" in stale.message


#: A project that numbers its rationale by hand, which is what both live corpora do (RK44).
#: The id is in the heading, not the anchor: `§XIV.15 A design (RK5)`.
OUTLINE_CONFIG = CONFIG.replace('prefix = "RK"', 'prefix = "RK"\nref_scheme = "outline"')
OUTLINE_CLEAN = CLEAN.replace("→ §RK1", "→ §I.1").replace("→ §RK2", "→ §I.2")
OUTLINE_PROSE = """# Design rationale

## Block A — The model

### §I.1 The first design (RK1)

The reasoning the first line has no room for.

### §I.2 The second design (RK2)

The reasoning the second line has no room for.
"""


def outline(tmp_path, improvements=OUTLINE_PROSE):
    return project(
        tmp_path, roadmap=OUTLINE_CLEAN, improvements=improvements, config=OUTLINE_CONFIG
    )


#: A project whose positioning prose lives where `[files]` declares it — Turing's shape,
#: and the outline scheme it numbers by: under `id` the pointer is derived from the id, so
#: a line addressing another file's section is `ref.mismatch` before RK172 is reached.
STRATEGY_CONFIG = OUTLINE_CONFIG + 'strategy = "STRATEGY.md"\n'
STRATEGY = """# Strategy

## X. Positioning

### §X.3 Content calendar

What the positioning prose the roadmap points at says.
"""
#: A line whose design is positioning and lives where positioning prose lives — added
#: rather than repointed, so the two sections `§I.1` and `§I.2` stay reachable (RK135).
POINTING_OUT = OUTLINE_CLEAN + (
    "- 📋 **RK4** (deps: —) **A fourth symptom** — Because of a fourth. → §X.3\n"
)


def strategic(tmp_path, roadmap=OUTLINE_CLEAN, strategy=STRATEGY, improvements=OUTLINE_PROSE):
    config = project(
        tmp_path, roadmap=roadmap, improvements=improvements, config=STRATEGY_CONFIG
    )
    (tmp_path / "STRATEGY.md").write_text(strategy, encoding="utf-8")
    return Config.discover(config.root)


def test_a_pointer_into_the_strategy_file_resolves(tmp_path):
    # RK172, measured adopting Turing: six open GEO lines carry `→ §X.3` and `→ §X.4`,
    # `docs/STRATEGY.md` declares both, and the gate called all six unresolved — clearable
    # only by repointing a line at an unrelated section or by moving positioning prose out
    # of the file the config declares for it.
    assert lint(strategic(tmp_path, roadmap=POINTING_OUT)).clean


def test_a_pointer_into_neither_prose_file_names_both(tmp_path):
    report = lint(strategic(tmp_path, roadmap=POINTING_OUT.replace("§X.3", "§X.9")))
    unresolved = next(f for f in report.findings if f.code == "ref.unresolved")
    assert "IMPROVEMENTS.md or STRATEGY.md" in unresolved.message


def test_an_anchor_two_prose_files_declare_is_named_and_not_read(tmp_path):
    # The seventh line's cost: T354 points at `§X.1`, an unrelated `§X.1` exists in the
    # improvements file, and reading the first billed it 365 words of somebody else's
    # subtree — so splitting that section into four moved the number *up* by five.
    both = OUTLINE_PROSE + "\n### §X.3 Why bypass the framework\n\nOther prose.\n"
    report = lint(strategic(tmp_path, roadmap=POINTING_OUT, improvements=both))
    ambiguous = next(f for f in report.findings if f.code == "ref.ambiguous")
    assert ambiguous.id == "RK4" and "IMPROVEMENTS.md and STRATEGY.md" in ambiguous.message
    # And never read as one of the two: the improvements `§X.3` is charged its own prose,
    # not the subtree a pointer would hand a reader.
    assert "section.too-long" not in codes(report)


def test_two_prose_files_declaring_one_anchor_fail_at_both_headings(tmp_path):
    # RK239, measured on Turing at `f08304fcb1`: thirteen anchors declared in both prose
    # files, one pointed at and reported, and the other twelve reported by nothing — while
    # `show`, `brief`, `ship` and `defer` all refuse to resolve them. The remedy is an edit
    # at each of the two, which is why it is one finding per heading and not one per anchor.
    both = OUTLINE_PROSE + "\n### §X.3 Why bypass the framework\n\nOther prose.\n"
    report = lint(strategic(tmp_path, improvements=both))
    doubled = [f for f in report.findings if f.code == "section.ambiguous"]
    assert [(f.file, f.id) for f in doubled] == [
        ("IMPROVEMENTS.md", "X.3"),
        ("STRATEGY.md", "X.3"),
    ]
    assert "STRATEGY.md" in doubled[0].message and "IMPROVEMENTS.md" in doubled[1].message
    # The roadmap here points at nothing doubled, which is the whole finding: before this,
    # the state was named only where a task line happened to reach it.
    assert "ref.ambiguous" not in codes(report)


def test_one_file_declaring_an_anchor_twice_is_not_two_files_disagreeing(tmp_path):
    # `_declared` dedupes a role, and this is the half that reads it: the second copy is
    # `section.duplicate` in that file, and a cross-file finding on top of it would report
    # one file's paste as three files disagreeing.
    twice = PROSE + "\n### §RK1 The first design again\n\nA pasted duplicate.\n"
    report = lint(project(tmp_path, improvements=twice))
    assert "section.ambiguous" not in codes(report)


def test_a_strategy_section_is_budgeted_like_any_other(tmp_path):
    # A strategy file is a prose file: a gate that read one of the two would leave the
    # other ungoverned in exactly the way the roadmap is not (RK30/RK50).
    long = STRATEGY.replace("What the positioning prose the roadmap points at says.", "word " * 40)
    config = project(
        tmp_path, roadmap=OUTLINE_CLEAN, improvements=OUTLINE_PROSE,
        config=STRATEGY_CONFIG + "[limits]\nsection = 10\n",
    )
    (tmp_path / "STRATEGY.md").write_text(long, encoding="utf-8")
    report = lint(Config.discover(config.root))
    over = next(f for f in report.findings if f.code == "section.too-long")
    assert over.file == "STRATEGY.md" and over.id == "X.3"


def test_an_outline_project_passes_when_every_section_names_a_live_task(tmp_path):
    assert lint(outline(tmp_path)).clean


def test_a_shipped_task_named_in_an_outline_heading_is_stale_too(tmp_path):
    # RK61: both checks were guarded by an id-shaped anchor, so under the scheme Shio and
    # Turing use they fired for nobody — 39 stale sections and 9 orphans in Shio, unseen.
    survived = OUTLINE_PROSE + "\n### §I.9 The shipped design (RK5)\n\nStill here.\n"
    report = lint(outline(tmp_path, improvements=survived))
    stale = next(f for f in report.findings if f.code == "section.stale")
    assert stale.id == "I.9" and "RK5" in stale.message


SHARED = OUTLINE_PROSE + "\n### §I.9 A shared design (RK5)\n\nProse two lines want.\n"
#: An earlier draft of `§I.1`, left behind under a heading that still names its task. Only
#: reachable under an outline: the id scheme derives the pointer from the id, so a line
#: pointing anywhere else is `ref.mismatch` before this check is reached (RK27).
DRAFTED = OUTLINE_PROSE + "\n### §I.0 The first design (RK1)\n\nAn earlier draft.\n"


def test_a_superseded_draft_whose_task_points_elsewhere_is_a_finding(tmp_path):
    # RK135, minimally: Shio carried `XV.21` and `XV.22` under one title, one an earlier
    # draft of the other, and SH265 points at `XV.22`. Twenty-three lines of superseded
    # design lint clean — `orphan` sees an open id, `duplicate` sees two anchors, and
    # `ref.unresolved` sees a pointer that resolves somewhere.
    report = lint(outline(tmp_path, improvements=DRAFTED))
    unreachable = next(f for f in report.findings if f.code == "section.unreachable")
    assert unreachable.id == "I.0" and "RK1 points at §I.1" in unreachable.message


def test_moving_the_pointer_moves_the_finding_to_the_other_draft(tmp_path):
    # The falsifying half, and the reason the remedy is not a deletion: which of the two
    # is the design is a reading, and the pointer is the whole of what states it.
    moved = OUTLINE_CLEAN.replace("→ §I.1", "→ §I.0")
    report = lint(
        project(tmp_path, roadmap=moved, improvements=DRAFTED, config=OUTLINE_CONFIG)
    )
    stranded = [f.id for f in report.findings if f.code == "section.unreachable"]
    assert stranded == ["I.1"]


def test_a_draft_some_other_open_line_points_at_is_reached(tmp_path):
    # Reachability is the pointer index and never the title (RK134), so any open line's
    # pointer is enough: a second task reading that design is what keeps it live.
    third = OUTLINE_CLEAN + (
        "- 📋 **RK4** (deps: —) **A fourth symptom** — Because of a fourth. → §I.0\n"
    )
    report = lint(
        project(tmp_path, roadmap=third, improvements=DRAFTED, config=OUTLINE_CONFIG)
    )
    assert "section.unreachable" not in codes(report)


def test_a_shared_design_whose_named_task_shipped_is_not_reported(tmp_path):
    # RK134, reproduced minimally and measured live in Shio's `VI.1`: SH22 shipped and
    # SH44-SH47 are still open against the same design. `_unowned` read the ids in the
    # heading and `section drop` reads the pointers, so the gate named a remedy the tool
    # refuses — and the state it named is the one RK64 makes `ship` write on purpose.
    both = OUTLINE_CLEAN.replace("→ §I.1", "→ §I.9").replace("→ §I.2", "→ §I.9")
    report = lint(outline(tmp_path, improvements=SHARED))
    (tmp_path / "ROADMAP.md").write_text(both, encoding="utf-8")
    assert "section.stale" in codes(report)  # nothing points at it yet
    assert "section.stale" not in codes(lint(Config.discover(tmp_path)))


def test_the_pointer_and_not_the_heading_is_what_buys_the_silence(tmp_path):
    # The falsifying half: one open line moved off the shared design is still enough, and
    # moving both back leaves the heading saying exactly what it said before.
    one = OUTLINE_CLEAN.replace("→ §I.1", "→ §I.9")
    report = lint(outline(tmp_path, improvements=SHARED))
    (tmp_path / "ROADMAP.md").write_text(one, encoding="utf-8")
    assert "section.stale" in codes(report)
    assert "section.stale" not in codes(lint(Config.discover(tmp_path)))


def test_an_outline_heading_naming_no_live_task_is_an_orphan(tmp_path):
    orphaned = OUTLINE_PROSE + "\n### §I.9 A design for nothing (RK7)\n\nProse.\n"
    report = lint(outline(tmp_path, improvements=orphaned))
    assert [f.id for f in report.findings if f.code == "section.orphan"] == ["I.9"]


def test_an_outline_subsection_still_owns_only_what_its_heading_names(tmp_path):
    # RK114 asks the anchor's *first segment*, so an outline sub-anchor reaches the heading
    # rule unchanged — `I` is no id, and prose belonging to no task is nobody's orphan.
    unowned = OUTLINE_PROSE + "\n#### §I.1.1 A shape of the file\n\nProse.\n"
    assert lint(outline(tmp_path, improvements=unowned)).clean


def test_an_outline_heading_that_names_no_task_owns_nothing(tmp_path):
    # Naming no id is how a section says it belongs to no task, under either scheme.
    unowned = OUTLINE_PROSE + "\n### §I.9 A shape of the file\n\nProse.\n"
    assert lint(outline(tmp_path, improvements=unowned)).clean


def test_naming_a_task_in_a_heading_is_the_claim_to_be_its_rationale(tmp_path):
    # No exemption for where the section sits. The first attempt made one — "a task's section
    # is under a `Block X` heading", read off this repository's own file — and it disabled the
    # check on the corpus it was for: Shio files rationale under `## VIII. … (Block H)`, so all
    # 146 of its sections looked unowned. This repository's own §0.4 lost `(RK20)` from its
    # heading instead, because citing the task that took a measurement is not owning it.
    outside = OUTLINE_PROSE.replace(
        "## Block A — The model",
        "### §0.9 A reading (RK5)\n\nProse.\n\n## Block A — The model",
    )
    report = lint(outline(tmp_path, improvements=outside))
    assert [f.code for f in report.findings] == ["section.stale"]


def test_prose_that_belongs_to_no_task_is_nobody_s_orphan(tmp_path):
    # `§0.1` is this repository's own preface: an anchor no line owns, which is legal —
    # the same rule `section add` applies to an anchor that is not id-shaped (RK9).
    preface = PROSE + "\n## §0 — Why this exists\n\n### §0.1 The measured problem\n\nProse.\n"
    assert lint(project(tmp_path, improvements=preface)).clean


def test_two_sections_with_one_anchor_fail(tmp_path):
    twice = PROSE + "\n### §RK1 The first design again\n\nA pasted duplicate.\n"
    report = lint(project(tmp_path, improvements=twice))
    duplicate = next(f for f in report.findings if f.code == "section.duplicate")
    assert duplicate.id == "RK1" and "resolves to neither" in duplicate.message


def test_a_section_over_its_word_budget_fails(tmp_path):
    tight = CONFIG + "\n[limits]\nsection = 5\n"
    report = lint(project(tmp_path, config=tight))
    over = [f for f in report.findings if f.code == "section.too-long"]
    assert len(over) == 2 and "limit is 5" in over[0].message


def test_a_section_a_line_points_at_is_charged_for_its_subsection(tmp_path):
    # RK9's rule, at the gate: prose that escapes the budget by gaining a heading is the
    # drift the budget exists to stop, and following §RK1 is what hands it to a reader.
    grown = PROSE.replace(
        "### §RK2 The second design",
        "#### §RK1.1 A subsection\n\nWhich doubles what the pointer hands a reader.\n"
        "\n### §RK2 The second design",
    )
    # 10 words clears every section's own prose here and not §RK1 plus its subsection.
    report = lint(project(tmp_path, improvements=grown, config=CONFIG + "\n[limits]\nsection = 10\n"))
    assert [f.id for f in report.findings if f.code == "section.too-long"] == ["RK1"]


def test_a_container_nothing_points_at_is_measured_on_its_own_prose(tmp_path):
    # The other half: §0 has no prose of its own and three anchored children that are each
    # inside the budget, so charging it their words would fail a file with no long
    # paragraph in it — and this repository's own file is the fixture.
    nested = """# Design rationale

## Block A — The model

### §RK1 The first design

Three words here.

### §RK2 The second design

Three words here.

## §0 — Why this exists

Short.

### §0.1 The measured problem

This subsection is comfortably over any budget of five words.
"""
    report = lint(project(tmp_path, improvements=nested, config=CONFIG + "\n[limits]\nsection = 5\n"))
    assert [f.id for f in report.findings if f.code == "section.too-long"] == ["0.1"]


def test_no_prose_file_means_no_pointer_to_resolve(tmp_path):
    # Shio declares no improvements file. That is not a pointer defect, and a gate that
    # said so would fail every project that keeps its rationale somewhere else.
    bare = 'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    assert lint(project(tmp_path, improvements=None, config=bare)).clean


# -- the paths a line claims (RK15, narrowed to the ledger by RK46) ----------


def test_a_path_a_shipped_line_names_and_the_repository_lacks_fails(tmp_path):
    claiming = LEDGER.replace(
        "Because it was done.", "Because `docs/specs/absent.md` says so."
    )
    # The directory and not the file: a claim is decidable where its directory exists, and
    # undecidable prose is what RK55 stopped reporting.
    (tmp_path / "docs" / "specs").mkdir(parents=True)
    report = lint(project(tmp_path, changelog=claiming))
    missing = next(f for f in report.findings if f.code == "path.missing")
    assert missing.id == "RK5" and "docs/specs/absent.md" in missing.message
    assert missing.file == "CHANGELOG.md"


def in_docs(tmp_path: Path, ledger: str) -> Config:
    """A project whose ledger sits one directory down, which is where `..` starts to mean
    something: at the root the two bases RK51 compares are the same directory."""
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "docs/CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir()
    for name, body in {"ROADMAP.md": CLEAN, "docs/CHANGELOG.md": ledger}.items():
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def test_a_link_relative_to_the_ledgers_own_directory_resolves(tmp_path):
    # 886 of Shio's ledger links are written the way Markdown reads them — from the file —
    # and every one of them was reported missing (RK51). The question is whether the
    # repository has the artefact, not whether the link renders from the root.
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "Service.java").write_text("//", encoding="utf-8")
    config = in_docs(
        tmp_path,
        LEDGER.replace("Because it was done.", "Because [S](../src/Service.java) does it."),
    )
    assert config.document("changelog").entries, "the fixture has to have a ledger to read"
    assert [f for f in lint(config).findings if f.code == "path.missing"] == []


def test_a_relative_link_that_resolves_under_no_base_is_still_reported(tmp_path):
    (tmp_path / "src").mkdir()  # the directory exists; the file it claims does not (RK55)
    config = in_docs(
        tmp_path,
        LEDGER.replace("Because it was done.", "Because [g](../src/Gone.java) did it."),
    )
    missing = next(f for f in lint(config).findings if f.code == "path.missing")
    assert "../src/Gone.java" in missing.message


def test_a_path_the_roadmap_names_is_the_file_the_task_will_write(tmp_path):
    # Shio: 8 findings, 8 false — every one an artefact its task exists to create. A
    # roadmap describes work that has not happened, so absence there is not a defect.
    claiming = CLEAN.replace(
        "Because of a reason.", "Because it will write `import/post-types.json`."
    )
    assert lint(project(tmp_path, roadmap=claiming)).clean


def test_a_slash_command_is_not_a_missing_path(tmp_path):
    # RK25's line names four of them; each is slash-shaped and none is a file here.
    commands = LEDGER.replace("Because it was done.", "Because `/roadkeep:add` exists.")
    assert lint(project(tmp_path, changelog=commands)).clean


@pytest.mark.parametrize(
    "token",
    [
        "blueprints/*/files/package.json",
        "monaco-editor/esm/vs/…",
        "template/widget/<name>.html",
        "@graphiql/react",
    ],
)
def test_a_token_naming_a_class_of_file_is_not_a_claim_even_when_shipped(tmp_path, token):
    # The ledger is the file where absence *is* a defect, and these still are not: no
    # state of the repository makes any of them resolve, so none of them is falsifiable.
    claiming = LEDGER.replace("Because it was done.", f"Because `{token}` says so.")
    assert lint(project(tmp_path, changelog=claiming)).clean


def test_a_section_may_name_a_file_that_does_not_exist_yet(tmp_path):
    # A design's whole job: §RK26 names `.claude-plugin/marketplace.json` before there is
    # one. Resolving a section's prose would fail every honest forward reference.
    forward = PROSE.replace(
        "The reasoning the first line has no room for.",
        "It will write `.claude-plugin/marketplace.json` and nothing else.",
    )
    assert lint(project(tmp_path, improvements=forward)).clean


# -- the dep that names more work than it looks like (RK35) -------------------

COLLECTIVE = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- 💭 **RK2** (deps: —) **A second symptom** — Because of another reason. → §RK2

## Block B — Authoring

- 📋 **RK3** (deps: Block A) **A third symptom** — Because of a third reason. → §RK3
"""

WITH_RK3 = PROSE + "\n### §RK3 The third design\n\nThe reasoning the third line lacks.\n"


#: Eight open tasks behind one token — the magnitude in a fixture that owns its numbers,
#: so no assertion about it depends on another repository still having a full backlog.
CROWDED = (
    "# Roadmap\n\n## Block A — The model\n"
    + "".join(
        f"- 📋 **RK{n}** (deps: —) **A symptom** — Because of a reason. → §RK{n}\n"
        for n in range(11, 19)
    )
    + "\n## Block B — Authoring\n\n"
    "- 📋 **RK19** (deps: Block A) **A ninth symptom** — Because of a reason. → §RK19\n"
)
CROWDED_PROSE = "# Design rationale\n\n## Block A — The model\n" + "".join(
    f"\n### §RK{n} The design\n\nThe reasoning the line has no room for.\n"
    for n in (*range(11, 19), 19)
)


def test_a_block_dep_says_what_it_expands_to_without_failing(tmp_path):
    # `Block P` resolved to forty-one open tasks in Shio and is one token on the page.
    # Legitimate (RK28), so the exit code cannot move — but a reader counting deps to
    # judge how blocked a line is has no way to see it from the line.
    report = lint(project(tmp_path, roadmap=COLLECTIVE, improvements=WITH_RK3))
    assert report.clean and report.problems == 0
    (note,) = report.notes
    assert note.code == "deps.collective" and note.id == "RK3"
    assert "Block A is one token naming 2 open tasks: RK1, RK2" in note.message
    assert str(note).startswith("ROADMAP.md:10  deps.collective  RK3:")


def test_the_note_does_not_move_the_exit_code(tmp_path, capsys):
    project(tmp_path, roadmap=COLLECTIVE, improvements=WITH_RK3)
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "deps.collective" in out and "clean" in out


# -- the door a markerless ledger keeps (RK214's note, RK125's answer) ---------

#: Shio's and Claude Code Tray's shape: a ledger reconstructed before this grammar, whose
#: entries carry no glyph because the file's heading is the marker.
MARKERLESS_CONFIG = CONFIG + "[ledger]\nmarker = false\n"
MARKERLESS_LEDGER = """# Shipped

## Block A — The model

- **RK5** **An earlier symptom** — Because it was done.
"""


def test_a_markerless_ledger_is_no_longer_told_a_verb_is_closed(tmp_path):
    # RK214 named the closed door at the gate rather than at the refusal; RK125 opened it,
    # so the note is gone. A gate that repeats a constraint the tool no longer has is worse
    # than silence: it is read with the same trust as the ones that are still true.
    report = lint(
        project(tmp_path, changelog=MARKERLESS_LEDGER, config=MARKERLESS_CONFIG)
    )
    assert report.clean and report.problems == 0
    assert not [n for n in report.notes if n.code == "ledger.no-marker"]


def test_the_verb_that_note_warned_about_now_writes(tmp_path):
    # The door, taken: the retirement carries the marker on its own line, which is what
    # keeps `Backlog.retired` from counting it as the shipment `ship` would have filed.
    from roadkeep.shipping import retire

    config = project(tmp_path, changelog=MARKERLESS_LEDGER, config=MARKERLESS_CONFIG)
    retire(config, "RK1", reason="The premise did not survive the measurement.").save()
    ledger = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "- 🗑 **RK1**" in ledger
    # And the gate reads that line back rather than reporting it: nothing about CHANGELOG.md,
    # which is the claim (L3). The roadmap's `deps.retired` is RK32 working — a line waiting
    # on work that left is the author's next edit.
    assert not [f for f in lint(config).findings if f.file == "CHANGELOG.md"]


def test_the_declaration_names_what_it_costs_where_the_choice_is_made(tmp_path):
    # RK214's mechanism outlives the door it named: `init` states the consequence of
    # `marker = false` in the file that declares it, and the consequence is now one line.
    from dataclasses import replace as replaced

    from roadkeep.adopting import render_config
    from roadkeep.schema import Schema

    rendered = render_config(
        replaced(Schema(), ledger_marker=False), {"roadmap": "docs/ROADMAP.md"}
    )
    assert "marker = false" in rendered and "a retirement still carries 🗑" in rendered


def test_a_range_dep_is_expanded_too(tmp_path):
    # Turing's `(deps: T451–T457)` is one token naming seven.
    ranged = COLLECTIVE.replace("(deps: Block A)", "(deps: RK1–RK2)")
    report = lint(project(tmp_path, roadmap=ranged, improvements=WITH_RK3))
    assert report.clean
    assert "RK1–RK2 is one token naming 2 open tasks" in report.notes[0].message


def test_the_listing_stops_at_six_and_the_count_still_names_them_all(tmp_path):
    # Where the count and the listing part company, which is the whole point of printing
    # the number: past six the reader is told how much the token hides, not which ids.
    report = lint(project(tmp_path, roadmap=CROWDED, improvements=CROWDED_PROSE))
    assert report.clean
    (note,) = report.notes
    assert "Block A is one token naming 8 open tasks: " in note.message
    assert note.message.endswith("RK11, RK12, RK13, RK14, RK15, RK16 …")


def test_a_collective_dep_naming_one_task_says_nothing(tmp_path):
    # There is no surprise at one, and at zero the annotation already reads ✅ because the
    # dep is satisfied (RK8). A note per token below that is output nobody reads.
    single = COLLECTIVE.replace(
        "- 💭 **RK2** (deps: —) **A second symptom** — Because of another reason. → §RK2\n",
        "",
    )
    # The section goes with the line, or §RK2 is an orphan and the file is not clean.
    prose = WITH_RK3.replace(
        "### §RK2 The second design\n\nThe reasoning the second line has no room for.\n", ""
    )
    report = lint(project(tmp_path, roadmap=single, improvements=prose))
    assert report.notes == () and report.clean


def test_quiet_drops_the_notes_with_everything_else(tmp_path, capsys):
    project(tmp_path, roadmap=COLLECTIVE, improvements=WITH_RK3)
    assert main(["-C", str(tmp_path), "lint", "--quiet"]) == EXIT_OK
    assert "deps.collective" not in capsys.readouterr().out


def test_json_carries_the_notes_beside_the_findings(tmp_path, capsys):
    project(tmp_path, roadmap=COLLECTIVE, improvements=WITH_RK3)
    assert main(["-C", str(tmp_path), "lint", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["clean"] is True and payload["findings"] == []
    (note,) = payload["notes"]
    assert note["code"] == "deps.collective" and note["id"] == "RK3"


def _open_in_shio_block(roadmap: Path, label: str) -> list[str]:
    """Block `label`'s open ids, read out of the raw text by nothing this suite tests.

    The point of the assertion below is that `expand` names *exactly* the set the file
    spells, so the expected side of it has to be counted independently — a second call
    into `Backlog` would only prove the parser agrees with itself.
    """
    ids: list[str] = []
    within = False
    for line in roadmap.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            within = line.startswith(f"## {label} ")
        elif within and (match := re.match(r"- \S+ \*\*(SH[1-9][0-9]*)\*\*", line)):
            ids.append(match.group(1))
    return ids


def test_a_live_backlog_shows_where_the_abbreviation_hides_work():
    roadmap = SHIO / "docs" / "ROADMAP.md"
    if not roadmap.is_file():
        pytest.skip(f"{roadmap} is not on this machine")
    config = Config.parse(
        {
            "prefix": "SH",
            "ref_scheme": "outline",
            "files": {"roadmap": "docs/ROADMAP.md", "changelog": "docs/CHANGELOG.md"},
        },
        root=SHIO,
    )
    # Not a floor: Shio empties Block P, and 48 when this was measured is 12 today. What
    # holds at every one of those is the note naming the count the file itself spells.
    expected = _open_in_shio_block(roadmap, "Block P")
    notes = [n for n in lint(config).notes if "Block P is one token" in n.message]
    if len(expected) < 2:
        # The block emptied to one: RK35 suppresses the note there, and that is the
        # assertion, not a reason to go red.
        assert notes == []
        return
    (note,) = notes
    assert f"naming {len(expected)} open tasks: {expected[0]}" in note.message


# -- the byte nobody can see (RK34) -------------------------------------------


def test_a_variation_selector_is_named_instead_of_its_consequence(tmp_path):
    # Measured against this parser: 📋 + U+FE0F is reported as `status.unknown`, which
    # prints as "'📋️' is not one of 📋" — correct, and unusable.
    report = lint(project(tmp_path, roadmap=CLEAN.replace("📋", "📋️", 1)))
    assert [f.code for f in report.findings] == ["char.invisible"]
    (finding,) = report.findings
    assert "U+FE0F" in finding.message and "variation selector-16" in finding.message
    # Column 4: "- " then the marker at 3, and the selector riding on it at 4.
    assert (finding.lineno, finding.column) == (5, 4)
    assert str(finding).startswith("ROADMAP.md:5:4  char.invisible  RK1:")


def test_a_no_break_space_is_named_instead_of_the_terminator_it_broke(tmp_path):
    # The other measured case: a NBSP before the pointer is reported as
    # `why.no-terminator`, naming the one thing the line does not lack.
    nbsp = CLEAN.replace("reason. → §RK1", "reason. → §RK1")
    report = lint(project(tmp_path, roadmap=nbsp))
    assert [f.code for f in report.findings] == ["char.space"]
    assert "U+00A0 no-break space" in report.findings[0].message


def test_the_codepoint_replaces_every_other_finding_on_that_line(tmp_path):
    # A line the author cannot read as written is not a line the format can judge, so the
    # rest is left for the run after the byte is gone — and the run after says so.
    tainted = CLEAN.replace("📋", "📋️", 1)
    config = project(tmp_path, roadmap=tainted)
    assert [f.code for f in lint(config).findings] == ["char.invisible"]
    (tmp_path / "ROADMAP.md").write_text(tainted.replace("️", ""), encoding="utf-8")
    assert lint(config).clean


def test_a_second_line_keeps_its_own_findings(tmp_path):
    # Suppression is per line, not per file: RK2's real problem still has to be reported.
    both = CLEAN.replace("📋", "📋️", 1).replace(
        "Because of another reason.", "Because of another reason. And a second."
    )
    report = lint(project(tmp_path, roadmap=both))
    assert [f.code for f in report.findings] == ["char.invisible", "why.sentences"]


def test_a_byte_order_mark_answers_for_itself(tmp_path):
    report = lint(project(tmp_path, roadmap="﻿" + CLEAN))
    assert [f.code for f in report.findings] == ["char.bom"]
    assert "not text" in report.findings[0].message


def test_a_tab_inside_a_line_says_what_is_wrong_with_a_tab(tmp_path):
    # RK146: it is `Cc`, so it was reported as "invisible in an editor", which of a tab is
    # untrue — and RK126 withheld it from `--fix` because the indentation of a nested line
    # is part of the model. Two correct decisions, one finding no command could clear.
    report = lint(project(tmp_path, roadmap=CLEAN.replace("A first symptom", "A first\tsymptom")))
    (tab,) = report.findings
    assert tab.code == "char.tab" and tab.column == 32
    assert "separates fields with a space" in tab.message


def test_a_tab_in_the_indentation_is_the_nesting_and_is_reported_by_nothing(tmp_path):
    # The other half of the same reading: there a tab is the text RK49 writes back verbatim,
    # so reporting it would be the standing finding that teaches a reader to stop reading.
    nested = CLEAN.replace("- 💭 **RK2**", "\t- 💭 **RK2**")
    assert lint(project(tmp_path, roadmap=nested)).clean


def test_two_kinds_of_line_ending_in_one_file_are_reported(tmp_path):
    mixed = CLEAN.replace("- 📋 **RK1**", "- 📋 **RK1**").replace("\n", "\r\n", 3)
    report = lint(project(tmp_path, roadmap=mixed))
    assert [f.code for f in report.findings] == ["char.mixed-endings"]
    assert "CRLF" in report.findings[0].message and "LF" in report.findings[0].message


def test_a_file_that_is_uniformly_crlf_is_not_a_defect(tmp_path):
    # It round-trips, and a repository that checks out CRLF is a configuration and not a
    # mistake (L6). Reporting it would fail every Windows clone of an adopting project.
    assert lint(project(tmp_path, roadmap=CLEAN.replace("\n", "\r\n"))).clean


def test_prose_is_not_scanned_for_invisible_characters(tmp_path):
    # §RK34 had to quote a variation selector to explain the defect. A scan over prose
    # would have reported that quotation as the defect — RK15's trap, one file over.
    quoting = PROSE.replace(
        "The reasoning the first line has no room for.",
        "Measured: `📋️` is refused as `status.unknown`, naming the wrong thing.",
    )
    assert lint(project(tmp_path, improvements=quoting)).clean


# -- the file that is loaded every turn (RK30) --------------------------------


def budgeted(tmp_path: Path, body: str, declaration: str) -> Config:
    (tmp_path / "agents.md").write_text(body, encoding="utf-8", newline="")
    return project(tmp_path, config=CONFIG + f"\n[budgets]\n{declaration}\n")


def test_a_file_over_its_line_budget_fails(tmp_path):
    # Shio's `agents.md` reached 186 KB while stating a 150-line rule about itself, which
    # is the whole argument: a budget nothing reads is a budget nothing enforces.
    report = lint(budgeted(tmp_path, "a\nb\nc\nd\n", '"agents.md" = { lines = 3 }'))
    over = next(f for f in report.findings if f.code == "budget.lines")
    assert "4 lines, budget is 3" in over.message and over.file == "agents.md"
    assert "every turn" in over.message


def test_a_file_inside_its_budget_passes(tmp_path):
    assert lint(budgeted(tmp_path, "a\nb\n", '"agents.md" = { lines = 2 }')).clean


def test_a_last_line_without_a_terminator_still_counts(tmp_path):
    # Otherwise a file could sit one line over the budget by not ending with a newline.
    report = lint(budgeted(tmp_path, "a\nb\nc", '"agents.md" = { lines = 2 }'))
    assert "3 lines" in next(f for f in report.findings if f.code == "budget.lines").message


def test_the_byte_budget_catches_what_the_line_budget_cannot(tmp_path):
    # A line budget alone is met by writing longer lines, which is why RK30 names both.
    long_lines = "x" * 400 + "\n" + "y" * 400 + "\n"
    report = lint(budgeted(tmp_path, long_lines, '"agents.md" = { lines = 9, bytes = 500 }'))
    assert [f.code for f in report.findings] == ["budget.bytes"]
    assert "802 bytes, budget is 500" in report.findings[0].message


def test_a_budgeted_file_that_is_absent_is_reported(tmp_path):
    report = lint(project(tmp_path, config=CONFIG + '\n[budgets]\n"gone.md" = { lines = 5 }\n'))
    absent = next(f for f in report.findings if f.code == "budget.absent")
    assert absent.file == "gone.md" and absent.lineno is None


def test_a_budget_is_read_from_the_configuration_and_not_from_the_file(tmp_path):
    # L6: the number is per project, and the file it governs is not one the tool writes —
    # so nothing here parses `agents.md`, it only measures what a loader pays for it.
    config = budgeted(tmp_path, "a\n" * 40, '"agents.md" = { lines = 40 }')
    assert lint(config).clean
    (tmp_path / "roadkeep.toml").write_text(
        CONFIG + '\n[budgets]\n"agents.md" = { lines = 39 }\n', encoding="utf-8"
    )
    assert not lint(Config.discover(tmp_path)).clean


# -- the one invariant a declaration adds (RK1068) -----------------------------


def test_a_grammar_that_cannot_read_back_what_it_writes_is_one_defect(tmp_path):
    # The cost RK1064 does not remove, caught at the end it is about: a grammar given as
    # data can be one that cannot reproduce its own file, and the round-trip guard then
    # refuses every line — a hundred findings for the one config line that broke them.
    config = project(tmp_path, config=CONFIG + '\n[grammar.roadmap]\ndrop = ["symptom"]\n')
    report = lint(config)
    grammar = [f for f in report.findings if f.code == "grammar.unreadable"]
    assert len(grammar) == 1, [str(f) for f in report.findings]
    # And the lines it explains are gone: the report is one defect at one rule, which is the
    # whole difference between blaming the corpus and naming what broke it.
    # And the lines it explains are gone, whichever way they failed: a declaration too loose
    # renders them back differently and one too narrow stops matching at all, and a wrong
    # `drop` produces the second — so the fold has to watch both or it misses its own case.
    assert not [
        f for f in report.findings if f.code in ("line.non-canonical", "line.unparsed")
    ]
    assert grammar[0].subject == "roadmap" and "not the lines" in grammar[0].message
    # Filed against the config, because that is where the declaration is and where the edit
    # goes — the pairing with RK1067 that makes the answer actionable rather than correct.
    assert grammar[0].file == "roadkeep.toml"
    assert "[grammar.roadmap]" in grammar[0].message


def test_one_edited_line_is_still_about_that_line(tmp_path):
    # The inference is about a population, and a population of one is a line: `line.non-
    # canonical` is exactly right for somebody who hand-edited a bullet, and folding it into
    # a claim about the rule would blame the config for an edit nobody made there.
    roadmap = CLEAN.replace(
        "**A second symptom** — Because of another reason.", "and then some prose"
    )
    report = lint(project(tmp_path, roadmap=roadmap))
    # The orphan is the section RK2 no longer points at, which is that line failing
    # and not a second defect: what matters is that neither is folded into a rule.
    assert [f.code for f in report.findings] == ["line.unparsed", "section.orphan"]
    assert not [f for f in report.findings if f.code == "grammar.unreadable"]


def test_a_file_written_under_another_format_says_so_rather_than_naming_a_grammar(tmp_path):
    # The other half of the answer, and the one an adopting project meets first: no
    # `[grammar]` is declared, so there is no config line to send anybody to and the finding
    # says which file it is about instead of citing a declaration that does not exist.
    roadmap = "# Roadmap\n\n## Block A — The model\n\n" + "".join(
        f"- 📋 **RK{n}** :: a symptom :: a reason\n" for n in (1, 2, 3)
    )
    report = lint(project(tmp_path, roadmap=roadmap))
    grammar = [f for f in report.findings if f.code == "grammar.unreadable"]
    assert len(grammar) == 1 and grammar[0].file == "ROADMAP.md"
    assert "no [grammar] is declared" in grammar[0].message


# -- the budget whose subject is not a file (RK1059) ---------------------------


def test_a_served_tool_over_its_budget_fails(tmp_path):
    # RK30's argument about a resident file, made about the schema: the tool list is sent
    # to every session that connects the server and nothing refused a number either way.
    report = lint(project(tmp_path, config=CONFIG + "\n[tools]\ncharacters = 300\n"))
    over = [f for f in report.findings if f.code == "budget.tool"]
    assert over, "no tool is under 300 characters, so the gate has to fire"
    # Filed against the config, which declared it and is the only address there is: the
    # cost is composed per session and no path a reader could open holds it.
    assert {f.file for f in over} == {"roadkeep.toml"}
    assert "connects the server" in over[0].message and "budget --tools" in over[0].message
    # Largest first, because the message sends the reader to that ranking and a report in a
    # different order would be two answers to one question. Read off the sizes the messages
    # carry rather than against a named tool, which is a figure that moves with every edit.
    sizes = [int(f.message.split(" is ")[1].split(" ")[0]) for f in over]
    assert sizes == sorted(sizes, reverse=True)


def test_a_project_declaring_no_tool_budget_is_silent(tmp_path):
    # A ceiling this tool chose would be a number nobody looked at, which is the guess
    # RK464 declined to make — so a project that has not looked is held to nothing.
    report = lint(project(tmp_path))
    assert not [f for f in report.findings if f.code == "budget.tool"]
    assert "roadkeep.toml" not in report.checked


def test_the_read_and_the_gate_answer_with_one_number(tmp_path, capsys):
    # RK345: a limit that reaches an author only as a refusal is the verdict-after-the-prose
    # this project replaces, so `budget --tools` prints the room the gate is about to refuse.
    root = project(tmp_path, config=CONFIG + "\n[tools]\ncharacters = 300\n").root
    assert main(["-C", str(root), "budget", "--tools", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["each"] == 300
    over = {f.subject for f in lint(Config.discover(root)).findings if f.code == "budget.tool"}
    assert set(payload["over"]) == over


# -- the block the tool writes outside a governed file (RK104) -----------------


def readme(tmp_path: Path, body: str, name: str = "README.md") -> Config:
    """A project whose README carries a projection — current, stale, or malformed."""
    config = project(tmp_path)
    (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
    with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
        handle.write(body)
    return config


def marked(inside: str) -> str:
    return f"# A project\n\nProse the author owns.\n\n{BEGIN}\n{inside}\n{END}\n"


def derived(config: Config, shape: str = "markdown") -> str:
    return exported(config).body(shape)


def test_a_file_with_no_markers_is_not_a_target(tmp_path):
    # The markers are the author's declaration (RK37): a README that restates nothing cannot
    # restate it wrongly, and inventing the container is the one thing a gate may not do.
    config = readme(tmp_path, "# A project\n\nNo projection here.\n")
    report = lint(config)
    assert report.clean and "README.md" not in report.checked


def test_a_current_block_is_silence(tmp_path):
    config = project(tmp_path)
    (tmp_path / "README.md").write_text(marked("stale"), encoding="utf-8", newline="")
    config = Config.discover(tmp_path)
    (tmp_path / "README.md").write_text(
        marked(derived(config)), encoding="utf-8", newline=""
    )
    report = lint(config)
    assert report.clean and "README.md" in report.checked


def test_a_stale_block_fails_and_names_the_command(tmp_path):
    # The symptom: a commit ships a task, forgets `export`, and the table now contradicts
    # the ledger it was derived from — which every gate passed before this check existed.
    config = readme(tmp_path, marked("| Block | Open | Shipped |\n| --- | --- | --- |\n"))
    report = lint(config)
    stale = next(f for f in report.findings if f.code == "export.stale")
    assert stale.file == "README.md" and "export --readme" in stale.message
    # On the begin marker, not on the file: the block has a place, and a reader sent to the
    # file is sent to look for it (RK34's reading of a column).
    assert stale.lineno == 5


def test_the_stale_block_is_reported_and_never_rewritten(tmp_path):
    config = readme(tmp_path, marked("nothing derived this"))
    before = (tmp_path / "README.md").read_bytes()
    assert not lint(config).clean
    assert (tmp_path / "README.md").read_bytes() == before


def test_a_begin_with_no_end_has_no_block_to_compare(tmp_path):
    config = readme(tmp_path, f"# A project\n\n{BEGIN}\nhalf a container\n")
    report = lint(config)
    unmarked = next(f for f in report.findings if f.code == "export.unmarked")
    assert "no end marker" in unmarked.message and BEGIN in unmarked.message


def test_the_page_shape_is_gated_where_the_page_is(tmp_path):
    # The same check for `--site`, addressed by the flag that writes it: HTML between the
    # same two markers is the other half of RK39, and a stale meter is a stale count.
    config = readme(tmp_path, marked("<p>nobody re-derived this</p>"), "docs/index.html")
    stale = next(f for f in lint(config).findings if f.code == "export.stale")
    assert stale.file == "docs/index.html" and "export --site" in stale.message


def test_a_page_carrying_its_own_derived_html_is_clean(tmp_path):
    config = project(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.html").write_text(
        marked(derived(config, "html")), encoding="utf-8", newline=""
    )
    assert lint(Config.discover(tmp_path)).clean


def test_the_gate_reads_the_same_bytes_the_write_produces(tmp_path):
    """`export` then `lint` is silence, which is the only property that makes this a gate.

    Asserted through the command rather than through the function: the two would agree on
    any pair of renderers, and what is being held is that they agree on *the* pair.
    """
    config = readme(tmp_path, marked("stale"))
    assert main(["-C", str(tmp_path), "export", "--readme"]) == EXIT_OK
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_OK


def test_a_claim_that_expires_moves_no_byte(tmp_path, monkeypatch):
    """The projection is claim-blind, so nothing outside the repository can make it stale.

    A claim is dated in a temp file and expires on a clock. A README derived through one
    would change bytes with no commit to explain the change, and a gate over those bytes
    would be red for a reason nobody can look up.
    """
    config = project(tmp_path, roadmap=CLEAN.replace("📋 **RK1**", "🛠 **RK1**"))
    (tmp_path / "README.md").write_text(
        marked(derived(config)), encoding="utf-8", newline=""
    )
    config = Config.discover(tmp_path)
    assert lint(config).clean
    take(config, None)  # RK1 is in progress, so tier 1 claims exactly that line
    assert lint(config).clean


# -- the id shape a project declares (RK106) ----------------------------------

PADDED = """# Roadmap

## Track A — Structured sources

- 📋 **D01** (deps: —) **A first symptom** — Because of a reason. → §D01
- 📋 **D09** (deps: D01) **A ninth symptom** — Because of another reason. → §D09
"""

PADDED_PROSE = """# Design rationale

## Track A — Structured sources

### §D01 The first design

The reasoning the first line has no room for.

### §D09 The ninth design

The reasoning the ninth line has no room for.
"""

PADDED_CONFIG = (
    'prefix = "D"\n[ids]\npad = 2\n[headings]\nword = "Track"\n'
    '[files]\nroadmap = "ROADMAP.md"\nimprovements = "IMPROVEMENTS.md"\n'
)


def test_a_backlog_that_pads_every_line_passes_once_it_declares_the_width(tmp_path):
    # The nine findings that were the whole of Dumont's lint output, and the reason a
    # fourth corpus could not wire the gate at all: one question about the id's spelling,
    # answered by the project rather than by the format.
    config = project(
        tmp_path,
        roadmap=PADDED,
        changelog=None,
        improvements=PADDED_PROSE,
        config=PADDED_CONFIG,
    )
    assert lint(config).clean, [str(f) for f in lint(config).findings]


def test_the_same_file_without_the_declaration_is_a_finding_per_line(tmp_path):
    config = project(
        tmp_path,
        roadmap=PADDED,
        changelog=None,
        improvements=PADDED_PROSE,
        config=PADDED_CONFIG.replace("[ids]\npad = 2\n", ""),
    )
    assert codes(lint(config)).count("id.format") == 2


# -- the contract -------------------------------------------------------------


def test_the_exit_code_is_the_report(tmp_path, capsys):
    project(tmp_path, roadmap=CLEAN.replace("Because of a reason.", "no terminator"))
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_GATE
    out = capsys.readouterr().out
    assert "why.no-terminator" in out and "1 problem(s)" in out


def test_quiet_keeps_the_summary_and_drops_the_lines(tmp_path, capsys):
    project(tmp_path, roadmap=CLEAN.replace("Because of a reason.", "no terminator"))
    assert main(["-C", str(tmp_path), "lint", "--quiet"]) == EXIT_GATE
    out = capsys.readouterr().out
    assert "ROADMAP.md:5" not in out and "why.no-terminator 1" in out


def test_json_carries_every_finding_and_still_exits_one(tmp_path, capsys):
    project(tmp_path, roadmap=CLEAN.replace("Because of a reason.", "no terminator"))
    assert main(["-C", str(tmp_path), "lint", "--json"]) == EXIT_GATE
    payload = json.loads(capsys.readouterr().out)
    assert payload["clean"] is False and payload["problems"] == 1
    assert payload["codes"] == {"why.no-terminator": 1}
    (finding,) = payload["findings"]
    assert finding["file"] == "ROADMAP.md" and finding["line"] == 5
    assert finding["id"] == "RK1"


# -- which tree the report is about (RK299) -----------------------------------


def test_a_clean_summary_names_the_tree_it_read(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_OK
    assert f"clean (in {tmp_path.as_posix()})" in capsys.readouterr().out


def test_a_failing_summary_names_it_too(tmp_path, capsys):
    # The exit that gets read, and the one a wrong directory makes expensive: 34 findings
    # about somebody else's repository are 34 findings an author starts editing.
    project(tmp_path, roadmap=CLEAN.replace("Because of a reason.", "no terminator"))
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_GATE
    out = capsys.readouterr().out
    assert "1 problem(s)" in out and f"(in {tmp_path.as_posix()})" in out


def test_the_tree_is_named_absolutely_and_not_relative_to_where_it_ran(tmp_path, capsys, monkeypatch):
    """The whole point: the defect being answered *is* a wrong working directory, so the
    spelling `invocation` uses for a launcher — relative where it is under the cwd (RK254) —
    is the one spelling that must not be reused here. Run from inside the project it would
    print `.`, and attribute the report to wherever it was misread from."""
    project(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert main(["lint"]) == EXIT_OK
    out = capsys.readouterr().out
    assert f"(in {tmp_path.as_posix()})" in out and "(in .)" not in out


def test_json_carries_the_root_every_path_in_it_is_relative_to(tmp_path, capsys):
    project(tmp_path, roadmap=CLEAN.replace("Because of a reason.", "no terminator"))
    assert main(["-C", str(tmp_path), "lint", "--json"]) == EXIT_GATE
    payload = json.loads(capsys.readouterr().out)
    assert payload["root"] == tmp_path.as_posix()
    # And the pair is what makes the payload filable: a relative path plus the root it is
    # relative to resolves to the file, which `findings` alone never did.
    (finding,) = payload["findings"]
    assert (Path(payload["root"]) / finding["file"]).is_file()


def test_the_same_key_and_spelling_the_other_json_root_uses(tmp_path, capsys):
    # `install --json` already answers "which tree" as `root` with `as_posix()`, and two
    # spellings of one fact is what a second tool reading both would have to special-case.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "lint", "--json"]) == EXIT_OK
    root = json.loads(capsys.readouterr().out)["root"]
    assert root == tmp_path.resolve().as_posix() and "\\" not in root


# -- the sweep before the walk (RK227) ----------------------------------------


def test_a_clean_file_is_cleared_without_asking_about_a_character(tmp_path):
    """The rule stays `suspect`'s and only the number of times it is asked changes.

    800215 calls over Turing's ledger, every answer no, for 148 ms of a 660 ms gate. Asking
    which codepoints *occur* first — one `set` in C — leaves the walk unentered on a clean
    file, and every file this gate passes is a clean file.
    """
    config = project(tmp_path)
    asked: list[str] = []
    real = linting.suspect

    def counted(char, *, indent=False):
        asked.append(char)
        return real(char, indent=indent)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(linting, "suspect", counted)
        assert lint(config).clean
    # One question per distinct codepoint of each scanned file, never one per character.
    scanned = [
        "".join(config.document(role).lines)
        for role in ("roadmap", "changelog")
        if config.has(role)
    ]
    assert len(asked) <= sum(len(set(text)) for text in scanned)
    assert len(asked) * 4 < sum(len(text) for text in scanned)


def test_the_line_ending_is_not_what_makes_every_file_dirty(tmp_path):
    """A line ending is `Cc`, so a sweep over the raw lines would have said "dirty" for
    every file ever written and been the walk with a longer preamble. `_endings` is what
    judges those, and the sweep reads the bodies."""
    config = project(tmp_path)
    asked: list[str] = []
    real = linting.suspect

    def counted(char, *, indent=False):
        asked.append(char)
        return real(char, indent=indent)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(linting, "suspect", counted)
        lint(config)
    assert "\n" not in asked and "\r" not in asked


# -- the file whose content did not reach the disk (RK451) --------------------


def voided(tmp_path: Path, size: int = 3301) -> Config:
    """A governed file a crash left entirely NUL — the shape this repository lost."""
    config = project(tmp_path)
    (tmp_path / "ROADMAP.md").write_bytes(b"\x00" * size)
    return config


def test_a_file_that_is_all_nul_is_one_finding_and_not_one_per_byte(tmp_path):
    """Measured on the file this repository lost: 3,301 findings for 3,301 bytes, each
    identical but for a column, each naming a `--fix` that strips characters which are not
    text. The rules below the check all ask what a *line* says, and this file has none."""
    report = linting.lint(voided(tmp_path))
    # Scoped to the file itself: the pointers in the *other* files now resolve to nothing,
    # and those are consequences of the loss rather than a second reading of it.
    mine = [f for f in report.findings if f.file == "ROADMAP.md"]
    assert [f.code for f in mine] == ["file.not-text"]
    assert "every byte is NUL" in mine[0].message
    # No line and no column: the finding is about the file, which is the whole point.
    assert mine[0].lineno is None


def test_the_remedy_names_the_store_and_never_a_verb_of_this_tools(tmp_path):
    """No verb here closes it — there is nothing left to render from — and the store is the
    repository (L2). So the command is git's, and nothing prefixes it with this engine."""
    from roadkeep.provenance import invocation
    from roadkeep.remedying import remedy

    report = linting.lint(voided(tmp_path))
    found = remedy(report.findings[0])
    assert found is not None and found.kind == "restore"
    door = found.doors[0]
    assert door.argv == ("git", "checkout", "--", "ROADMAP.md")
    assert door.command == "git checkout -- ROADMAP.md"
    assert not door.command.startswith(invocation())
    # And `repair` may not execute it: the tool runs its own verbs and nobody else's.
    assert not found.runnable


def test_the_fix_pass_never_empties_the_file_it_cannot_read(tmp_path):
    """`--fix` strips characters that are not text, so left to it this file would become an
    empty one and the tree would report clean — a recoverable state destroyed with the
    gate's blessing."""
    from roadkeep.fixing import fix

    config = voided(tmp_path)
    fix(config)
    assert (tmp_path / "ROADMAP.md").read_bytes() == b"\x00" * 3301


def test_the_other_governed_files_are_still_judged(tmp_path):
    """Not a refusal to run: a report that stopped at the first unreadable file would hide
    what is fine about the rest."""
    config = project(tmp_path)
    (tmp_path / "ROADMAP.md").write_bytes(b"\x00" * 40)
    report = linting.lint(config)
    assert "file.not-text" in codes(report)
    assert {f.file for f in report.findings} > {"ROADMAP.md"}


def test_a_partly_lost_file_is_one_finding_too(tmp_path):
    """RK454: the all-NUL file is what this repository lost, and a partly-lost one is the
    likelier shape on a large file where only some blocks were flushed. Measured before
    this: 400 findings for 400 NULs, and the `--fix` they named claimed all of them, wrote
    no byte, and returned the identical report on the next run."""
    config = project(tmp_path)
    path = tmp_path / "ROADMAP.md"
    kept = path.read_bytes()
    path.write_bytes(kept + b"\x00" * 400)
    mine = [f for f in linting.lint(config).findings if f.file == "ROADMAP.md"]
    assert [f.code for f in mine] == ["file.not-text"]
    assert "400 NUL byte(s)" in mine[0].message


def test_a_surviving_line_is_still_judged(tmp_path):
    """The question §RK454 left open, answered *beside* rather than *instead of*: a file that
    kept some of its lines has defects of its own in them, and hiding those would answer a
    question nobody asked. Only the all-NUL file has nothing left to read."""
    drifted = "- 📋 **RK9** (deps: RK99) **A symptom** — Because. → §RK9\n"
    config = project(tmp_path, roadmap=CLEAN + drifted)
    path = tmp_path / "ROADMAP.md"
    path.write_bytes(path.read_bytes() + b"\x00" * 40)
    codes_found = codes(linting.lint(config))
    assert "file.not-text" in codes_found and "deps.unknown" in codes_found


def test_a_nul_is_never_reported_as_a_character_defect(tmp_path):
    """RK118 wrote every byte of a governed file and none was ever one, so the diagnosis
    `char.invisible` gives is wrong in kind — and its `--fix` claims the finding and changes
    nothing, which is the loop this closes."""
    config = project(tmp_path)
    path = tmp_path / "ROADMAP.md"
    path.write_bytes(path.read_bytes() + b"\x00" * 40)
    assert "char.invisible" not in codes(linting.lint(config))
    assert not linting.suspect("\x00")


def test_the_fix_pass_claims_nothing_it_cannot_write(tmp_path):
    """The second half of the defect, and the worse one: nothing exits differently, so a
    caller that trusts `400 of them need no decision` runs it forever."""
    from roadkeep.fixing import fix

    config = project(tmp_path)
    path = tmp_path / "ROADMAP.md"
    path.write_bytes(path.read_bytes() + b"\x00" * 40)
    before = path.read_bytes()
    fix(config)
    assert path.read_bytes() == before
    assert codes(linting.lint(config)) == ["file.not-text"]


def test_an_empty_file_is_a_different_state(tmp_path):
    """A scaffold before its first line is not a lost write, and stays the gate's other
    business: the check asks whether every byte is NUL, not whether there are few of them."""
    config = project(tmp_path)
    (tmp_path / "ROADMAP.md").write_bytes(b"")
    assert "file.not-text" not in codes(linting.lint(config))


def test_a_reserved_id_written_as_a_line_is_the_two_statements_disagreeing(tmp_path):
    """The check that RK1031 is a fix and not a suppression. A reservation says the address
    is spoken for and never carried; a line that carries one means the deriver has been
    handing out numbers past it on the strength of a declaration the file contradicts."""
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "SH"\nreserved_ids = ["SH25"]\n[files]\nroadmap = "ROADMAP.md"\n'
        'changelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Block A — The model\n\n"
        "- 📋 **SH25** (deps: —) **A symptom** — Because of a reason.\n",
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## Block A — The model\n", encoding="utf-8"
    )
    found = [one for one in lint(Config.discover(tmp_path)).findings if one.code == "id.reserved"]
    assert [one.id for one in found] == ["SH25"]
    assert "reserved_ids" in found[0].message


def test_a_project_reserving_nothing_is_unchanged(tmp_path):
    """Silent where nothing is declared, which is every project until one is: a code that
    fired on a backlog with no `reserved_ids` would be a rule invented rather than read."""
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "SH"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Block A — The model\n\n"
        "- 📋 **SH25** (deps: —) **A symptom** — Because of a reason.\n",
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## Block A — The model\n", encoding="utf-8"
    )
    assert not [
        one for one in lint(Config.discover(tmp_path)).findings if one.code == "id.reserved"
    ]
