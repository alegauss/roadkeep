"""A test about one rule may not assert over every rule the gate has (RK1448).

RK1440 gave the gate one more **note** — a wired project whose engine is a modified checkout
— and nineteen tests went red in one run. None of them was about engines. Six read
`(note,) = report.notes` or `report.notes == ()` while meaning *exactly one `deps.collective`
note*, one read `report.notes[0]`, and the rest were the same shape one file over.

The assertion is wrong in both directions. It fails on a note the test does not care about,
which is what happened; and it passes while a note it *should* have seen is absent, because a
list of one is a list of one whatever is in it. Neither failure names the rule under test, so
the repair is mechanical and the reader learns nothing. It also made the suite's verdict
depend on whether the checkout running it happened to be dirty.

**Notes and not findings**, which is the whole distinction. A finding moves the exit code: a
clean fixture that grows one is a regression, so `assert not lint(config).findings` is a claim
somebody meant. A note is advisory, does not move the verdict, and the set of them grows —
so the same sentence about notes is a claim about every advisory rule this tool will ever add.

What is refused is the **whole list used as a value**: unpacked, subscripted or compared.
Binding it to a name and filtering that name twice is the right shape and stays legal, which
is why this follows the binding rather than banning the attribute.

**And the exemption is a receiver, not a file** (RK1653). Five classes answer to this name and
one of them is a gate report, so RK1603 and RK1611 each added a module to a list — three rows,
each turning the rule off for every assertion in that file, and `test_installing` alone reads a
gate report thirty times. :data:`RECEIVERS` is that list re-keyed by *which object* the read is
of, held total against the suite: a receiver nobody classified is a red with one question in it
rather than a silence. Two of the six reads it removed were not lists at all — `remedying.
notes()` and `describing.notes()` are functions, and an attribute being **called** is now told
apart from one being read.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from surface import suite

HERE = Path(__file__).resolve().parent

#: What a row says when the receiver **is** a gate report, and so the rule applies to it.
#: A sentinel rather than a second table, because the population is one and the two answers
#: are what a reader is looking for on the same row.
REPORT = "a gate report"

#: Every `notes` read in the suite, by the receiver it is a read *of* — `(module, the head
#: symbol of the receiver)` — and either :data:`REPORT` or the reason it is not one.
#:
#: **Keyed by the receiver and no longer by the file** (RK1653). Duck typing means several
#: objects answer to this name, and the exemption for one of them was a whole module: three
#: rows, and no assertion anywhere in `test_blocking`, `test_describing` or `test_installing`
#: was swept — where `test_installing` alone reads a gate report thirty times. The rule is
#: about a name reached from a `Report`, and a file was never the shape of that.
#:
#: Held **total** against the suite below, which is what the narrowing costs and buys: a
#: receiver nobody classified is a red here with one question in it, where a file-keyed
#: exemption turned the rule off for everything else in the file that answered it.
#:
#: Two modules spell one local name for two things — `found` is a `cost --notes` payload in
#: `test_budgeting` and a `describing.Shape` in `test_describing` — which is why the key is a
#: pair and not the symbol alone.
RECEIVERS: dict[tuple[str, str], str] = {
    ("test_baseline.py", "lint"): REPORT,
    ("test_baseline.py", "report"): REPORT,
    # `blocking.Closed.notes` is a mapping of role to line count, not a gate report.
    ("test_blocking.py", "closed"): "a mapping of role to the lines a close removed",
    # `cost --notes` prices what a clean gate says beside its verdict, so its payload carries
    # the notes as **rows of a measurement** — the population, not this run's findings.
    ("test_budgeting.py", "found"): "the `cost --notes` payload, whose notes are priced rows",
    ("test_budgeting.py", "lint"): REPORT,
    ("test_budgeting.py", "report"): REPORT,
    ("test_composing.py", "lint"): REPORT,
    # RK1603 moved the harvested sentence off every key row of `config --json` and onto a
    # mapping of table to sentence. `config` reports no findings at all.
    ("test_describing.py", "found"): "a `describing.Shape`, mapping a table to its sentence",
    ("test_installing.py", "_linted"): REPORT,
    # RK1611's, and the third object to answer to this name: what a withdrawal does to
    # something the un-wiring keeps. Two receivers, one per spelling the module uses.
    ("test_installing.py", "intent"): "an `installing.Removal`, bound before it is read",
    ("test_installing.py", "removal"): "an `installing.Removal` read straight off the call",
    ("test_installing.py", "lint"): REPORT,
    ("test_installing.py", "report"): REPORT,
    ("test_linting.py", "lint"): REPORT,
    ("test_linting.py", "linting"): REPORT,
    ("test_linting.py", "payload"): REPORT,
    ("test_linting.py", "report"): REPORT,
    ("test_queueing.py", "report"): REPORT,
    ("test_remedying.py", "lint"): REPORT,
    ("test_scoping.py", "lint"): REPORT,
    ("test_scoping.py", "report"): REPORT,
    # The same report one register over: `lint --json` parsed back out of stdout.
    ("test_turning.py", "json"): REPORT,
    ("test_turning.py", "report"): REPORT,
    ("test_unpaired.py", "payload"): REPORT,
    ("test_unpaired.py", "report"): REPORT,
}


def _bound(body: ast.AST, path: Path) -> set[str]:
    """Names a function binds to a **report's** notes, following one step of dataflow.

    `said = lint(config).notes` and then two filters over `said` is the shape a test *should*
    have, and a rule that stopped at the attribute would refuse it.

    A read of something else that answers to the name binds nothing here (RK1653): `said =
    found.notes` in `test_describing` is a mapping, and following it would carry the rule onto
    every later use of a local variable the rule is not about.
    """
    found = set()
    for node in ast.walk(body):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and _is_notes(node.value) and _reports(path, node.value):
            found.add(target.id)
    return found


def _is_notes(node: ast.AST) -> bool:
    """A gate report's notes, however this file spells the read: attribute or payload key."""
    if isinstance(node, ast.Attribute) and node.attr == "notes":
        return True
    return (
        isinstance(node, ast.Subscript)
        and isinstance(node.slice, ast.Constant)
        and node.slice.value == "notes"
    )


def _receiver(node: ast.AST) -> str:
    """The head symbol of what this read is a read **of** — `lint(config).notes` is `lint`.

    Structural and not a spelling (RK1653): a receiver keyed by its source text would be a new
    row for every fixture a call happens to take, and what the rule is about is *which object*
    answers to the name. Walked down through calls, attributes and subscripts to the name at
    the bottom, which is the one part a reader recognises.
    """
    head = getattr(node, "value", node)
    while isinstance(head, (ast.Call, ast.Attribute, ast.Subscript)):
        head = head.func if isinstance(head, ast.Call) else head.value
    return head.id if isinstance(head, ast.Name) else ast.unparse(head)


def _read(tree: ast.AST) -> list[ast.AST]:
    """Every `notes` read in this module — and never the function of the same name (RK1653).

    `remedying.notes()` and `describing.notes()` are *functions* returning a population, and
    the sweep read each as a list it was about: six reads across two modules, one of which was
    a whole module's exemption on its own. An attribute being **called** is not a list, which
    is the one structural fact that tells them apart.
    """
    called = {id(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    return [
        node for node in ast.walk(tree) if _is_notes(node) and id(node) not in called
    ]


def _whole(function: ast.AST, bound: set[str], path: Path) -> list[int]:
    """Line numbers where a **report's** list is used as a value rather than filtered.

    ``path`` decides which reads are a report's, per receiver (RK1653): the same name reaches
    a mapping in three modules, and the rule is about the object rather than about the word.
    """
    over: list[int] = []

    def names_it(node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id in bound
        return _is_notes(node) and _reports(path, node)

    for node in ast.walk(function):
        # Unpacked: `(note,) = report.notes`, which claims the gate said exactly this one.
        if isinstance(node, ast.Assign) and names_it(node.value):
            if any(isinstance(one, (ast.Tuple, ast.List)) for one in node.targets):
                over.append(node.lineno)
        # Compared: `report.notes == ()`, the same claim spelled as equality.
        elif isinstance(node, ast.Compare) and (
            names_it(node.left) or any(names_it(one) for one in node.comparators)
        ):
            over.append(node.lineno)
        # Indexed: `report.notes[0]`, which is the first of a list nobody ordered.
        elif isinstance(node, ast.Subscript) and names_it(node.value):
            over.append(node.lineno)
    return over


def _reports(path: Path, node: ast.AST) -> bool:
    """Whether this read is a read of a gate report, off :data:`RECEIVERS`."""
    return RECEIVERS.get((path.name, _receiver(node))) == REPORT


def test_no_test_asserts_over_the_whole_list_of_notes():
    """The sweep that would have caught all seven the first time, and costs nothing on the
    ones that filter. Over `surface.suite`, which is where the set of test modules is
    declared: a sweep deriving its own view of the directory is RK496's failure one directory
    across, and this is the second sweep that wanted it.

    Per **receiver** since RK1653, so a module reading a report and something else that
    answers to the same name is swept for the first and exempt for the second — which is three
    modules, one of them the heaviest reader of gate reports in the suite."""
    guilty: dict[str, list[int]] = {}
    for path in suite():
        if path.name == Path(__file__).name:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            bound = _bound(node, path)
            for at in _whole(node, bound, path):
                guilty.setdefault(path.name, []).append(at)
    assert not guilty, (
        f"these assert over every note the gate has, not the one they are about: {guilty}"
    )


def test_every_notes_read_in_the_suite_is_classified():
    """The total the narrowing rests on. A receiver nobody classified is a read this sweep
    cannot decide about, and the answer it would give — *not a report, so exempt* — is the
    silence a file-keyed exemption already was.

    Both directions: a row naming a receiver the suite no longer spells is a reason nobody
    will read, and it leaves the rule looking stricter than it is."""
    found = {
        (path.name, _receiver(node))
        for path in suite()
        if path.name != Path(__file__).name
        for node in _read(ast.parse(path.read_text(encoding="utf-8")))
    }
    assert found == set(RECEIVERS), {
        "read and unclassified": sorted(found - set(RECEIVERS)),
        "classified and not read": sorted(set(RECEIVERS) - found),
    }
    for (name, _symbol), because in RECEIVERS.items():
        assert (HERE / name).is_file(), name
        assert because.strip(), name
    # And the majority are reports, which the shape alone would not say: a register where
    # every row is an exemption passes the total above and sweeps nothing.
    swept = [one for one in RECEIVERS.values() if one == REPORT]
    assert len(swept) > len(RECEIVERS) / 2, RECEIVERS


def test_the_function_of_the_same_name_is_not_a_list_of_notes():
    """RK1653's other half, and the cheaper one: `remedying.notes()` returns the population of
    notes this build can say, and `describing.notes()` the sentences a config's source carries.
    Both are calls, both were read as lists, and one of them was a module's whole exemption."""
    tree = ast.parse("said = remedying.notes()\nother = report.notes\n")
    assert [_receiver(one) for one in _read(tree)] == ["report"]


# -- a test may not read this backlog as though it could not empty (RK1671) ---

#: What names this checkout's root, in every spelling the suite uses. Nine modules bind `HERE`
#: and three spell `Path(__file__).resolve().parents[1]` inline, so the pattern and not a name.
_LIVE = re.compile(
    r"\bHERE\b|\bROOT\b|\bCHECKOUT\b|Path\.cwd\(\)|Path\(__file__\)\.resolve\(\)\.parent"
)

#: What names the backlog rather than the ledger, the configuration or the wiring.
_BACKLOG = re.compile(r"'roadmap'|\"roadmap\"|\bBacklog\b|\bentries\b|\bopen_lines\b")

#: The fixture that answers this whole question (RK1098): this repository whenever its backlog
#: has an open line, and a three-line stand-in when it does not.
STANDS_IN = "populated"

#: What a row says a drain does to it. Five words, and each is a property of *what the claim is
#: over* rather than a judgement about the test — which is what makes a row something a reader
#: can check against the body in front of them.
SURVIVES = {
    STANDS_IN: (
        "takes `populated`, so an emptied roadmap changes which files are read and never "
        "whether the contract is asserted"
    ),
    "guarded": (
        "names the empty state — a skip, or the `or role == roadmap` clause the assertion "
        "itself carries — so nothing is claimed where there is nothing"
    ),
    "pinned": (
        "the claim is carried by a pinned corpus (RK1630) and the local read is a second "
        "reading of it, which a drain leaves standing"
    ),
    "vacuous": (
        "holds over an empty backlog by construction: a loop over the entries, or the claim "
        "that nothing among them is wrong"
    ),
    "grows": (
        "what the claim is over is not the open backlog — the ledger, the non-goals, the "
        "configuration — and a departure adds to each of those"
    ),
}

#: Every test that reads this checkout's live backlog, and what a drain does to it (RK1671).
#:
#: Three tests went red in one sitting of shipping, none of them about the code that shipped:
#: `test_ranking` asserted a ratio over a backlog that had reached one differing line, and two
#: note-cost reads asserted this project's gate says a note. RK1098 met the same thing once and
#: built :data:`STANDS_IN`; RK1630 met it again and moved a claim to a pinned corpus. Neither
#: was a rule, so each red was repaired by whoever met it.
#:
#: **Measured rather than classified.** The suite was run against a drained copy of this
#: checkout in a throwaway worktree: of the thirty-one rows here two went red — `test_ranking`'s
#: `assert total`, and the `engines.gates` row of `test_payloads`, which takes `populated` and
#: broke *because* it does, that fixture's stand-in shipping no `.github/workflows`. Both are
#: fixed. The other twenty-nine survive, and this table says why each one does.
#:
#: Held total against :func:`_live_reads`, so a thirty-second is a red here with one question in
#: it: what does this do when the backlog empties.
DRAINED: dict[tuple[str, str], str] = {
    # `adopt` over the governed snapshot, asserting nothing is loose and nothing is a finding:
    # an empty backlog is a file with nothing loose in it.
    ("test_adopting.py", "test_a_conforming_backlog_lists_nothing"): "vacuous",
    ("test_adopting.py", "test_a_conforming_file_gains_no_finding_from_the_wider_pass"): "vacuous",
    # Every dep resolves, every open task briefs, every open task shows its section: three
    # claims quantified over the entries, and true of none of them.
    ("test_backlog.py", "test_this_repository_resolves_every_dep"): "vacuous",
    ("test_briefing.py", "test_every_open_task_here_briefs"): "vacuous",
    ("test_showing.py", "test_every_open_task_here_shows_its_own_section"): "vacuous",
    # The denial's own width, measured on a temp project: the live spelling here is a role name
    # inside a path the refusal quotes, and this checkout's backlog is not read at all.
    ("test_budgeting.py", "test_the_denial_is_measured_off_the_refusal_and_not_a_fixture"): "grows",
    # `near_cost` ranks a block's **ledger** entries beside its open ones, and this ledger
    # holds nine hundred: the dearest block is still a block when nothing is open.
    ("test_budgeting.py", "test_the_rows_an_add_volunteers_are_priced"): "grows",
    ("test_budgeting.py", "test_the_rows_are_priced_off_the_composer_and_not_a_fixture"): "grows",
    ("test_budgeting.py", "test_the_dearest_block_is_the_figure_and_not_a_mean"): "grows",
    # The configuration: the prefix, the roles, the ledger's own grammar. Nothing a ship moves.
    ("test_config.py", "test_the_tool_configures_itself"): "grows",
    ("test_config.py", "test_the_changelog_is_the_same_format_in_its_ledger_configuration"): "grows",
    ("test_packaging.py", "test_no_py_typed_ships_and_the_reason_is_declared"): "grows",
    # The two that already carried the clause this rule generalises, spelled in the assertion
    # itself: `assert document.entries or role == "roadmap"`, and the census's `total > 0 or
    # role == "roadmap"` beside it. RK1671 is that sentence made a rule instead of a habit.
    ("test_config.py", "test_its_own_documents_validate_under_its_own_config"): "guarded",
    ("test_counting.py", "test_this_repositorys_own_files_have_nothing_uncounted"): "guarded",
    # The projection is compared against the read it is derived from, so both answer 0.
    ("test_exporting.py", "test_this_repositorys_projection_matches_its_own_files"): "vacuous",
    # Every payload row `docs/` stopped producing the day a block shipped its last line, which
    # is what RK1098 built the fixture for.
    ("test_editor.py", "test_the_tree_groups_by_block_and_separates_what_is_blocked"): STANDS_IN,
    ("test_payloads.py", "test_the_top_level_keys_a_client_is_promised_are_there"): STANDS_IN,
    ("test_payloads.py", "test_every_payload_says_which_project_and_which_build"): STANDS_IN,
    ("test_payloads.py", "test_a_governed_path_says_so_and_names_the_roles_it_declares"): STANDS_IN,
    ("test_payloads.py", "test_a_list_payload_is_handed_back_as_the_list_it_is"): STANDS_IN,
    ("test_payloads.py", "test_the_keys_inside_a_row_are_there_too"): STANDS_IN,
    (
        "test_payloads.py",
        "test_every_list_of_objects_a_promised_payload_carries_has_a_row",
    ): STANDS_IN,
    ("test_payloads.py", "test_a_payload_is_the_whole_of_stdout_and_parses_as_one_object"): STANDS_IN,
    # The retirement pairs, which are entries of the **ledger**: a supersession is written at
    # the departure and stays there, so the population these read only ever grows.
    (
        "test_ranking.py",
        "test_every_pair_this_ledger_knows_the_answer_to_lands_inside_the_count",
    ): "grows",
    (
        "test_ranking.py",
        "test_the_pair_out_of_reach_is_the_one_whose_sentences_are_not_the_pair",
    ): "grows",
    ("test_ranking.py", "test_joining_the_query_scores_the_bookkeeping_and_looks_like_a_gain"): "grows",
    ("test_ranking.py", "test_widening_the_window_reaches_no_pair_three_does_not"): "grows",
    # RK1630's answer, and the row that is the reason it was chosen.
    ("test_ranking.py", "test_the_two_corpora_do_not_compete_for_the_volunteered_rows"): "pinned",
    ("test_ranking.py", "test_the_same_holds_here_wherever_there_is_anything_to_observe"): "guarded",
    # The non-goals, which are bullets of the roadmap that no departure removes — the same
    # false positive RK1098's first predicate made, from the other side.
    ("test_scoping.py", "test_this_repository_declares_its_own_list_governed_and_passes"): "grows",
    # The decisions file, whose every entry names an id the ledger holds: both only grow, and
    # the read is skipped where the role is undeclared.
    (
        "test_shipping.py",
        "test_every_decision_this_project_records_was_filed_by_a_departure",
    ): "grows",
}


def _live(node: ast.AST) -> bool:
    """Whether this function discovers a config at **this checkout's** root.

    The argument of the call and never the body around it: `test_budgeting` builds a temp
    project and then quotes a role name in a path a refusal composes, which is not a read of
    this repository at all.
    """
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        name = (
            child.func.attr
            if isinstance(child.func, ast.Attribute)
            else getattr(child.func, "id", "")
        )
        if name in ("discover", "default") and any(
            _LIVE.search(ast.unparse(one)) for one in child.args
        ):
            return True
    return False


def _live_reads(path: Path) -> list[tuple[str, str]]:
    """Every test in one module that reads this checkout's live backlog, by name (RK1671).

    Two ways in, and both are the population: a test that **takes** `populated` is asking for
    this repository's backlog by name, and one that discovers a config at the checkout and
    names the roadmap is asking for it by hand. The second needs the narrowing, because most
    live reads here are of the configuration, which a ship does not touch.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test_"):
            continue
        args = {one.arg for one in node.args.args}
        stands = STANDS_IN in args
        reads = ("governed" in args or _live(node)) and bool(
            _BACKLOG.search(ast.unparse(node))
        )
        if stands or reads:
            found.append((path.name, node.name))
    return found


def test_every_test_that_reads_this_backlog_says_what_a_drain_does_to_it():
    """RK1671. The rule the three reds were the absence of: a backlog with nothing open is what
    `ship` announces as finished, and a suite that reads it as a broken build is one whose
    verdict depends on how much work is left.

    Total, so this is a census and not a sample. A thirty-second row arrives as a red with one
    question in it — what does this do when the backlog empties — which is the question RK1098
    answered once, RK1630 answered again, and nothing asked of the next one."""
    found = [
        one for path in suite() if path.name != Path(__file__).name for one in _live_reads(path)
    ]
    assert len(found) == len(set(found)), found
    assert set(found) == set(DRAINED), {
        "reads the backlog, unclassified": sorted(set(found) - set(DRAINED)),
        "classified, no longer reads it": sorted(set(DRAINED) - set(found)),
    }


def test_every_row_is_one_of_the_five_and_each_word_says_what_it_covers():
    """A row is a reading, so the vocabulary is closed and each word means something stated —
    :data:`RECEIVERS`' own arrangement one rule over. And the shape the total alone would not
    say: a census where every row read `grows` would be a table of reasons this never applies."""
    assert set(DRAINED.values()) <= set(SURVIVES)
    assert set(SURVIVES) == set(DRAINED.values()), sorted(set(SURVIVES) - set(DRAINED.values()))
    for word, because in SURVIVES.items():
        assert len(because.split()) >= 12, word
    for name, _test in DRAINED:
        assert (HERE / name).is_file(), name
    # The three answers somebody built on purpose — the fixture, the pin, the named absence —
    # reach a quarter of the census, which is what makes the other two readings and not excuses.
    deliberate = [one for one in DRAINED.values() if one in (STANDS_IN, "pinned", "guarded")]
    assert len(deliberate) >= len(DRAINED) / 4, DRAINED
