"""What a task has left, from the query its own design declares (RK492).

`weight` answers what a comparable task cost, from the commits that shipped it. This is that
question's mirror and takes the same answer: derived on demand, landing on no line, and
therefore unable to go stale. §RK72's non-goal refuses a stored size and is not in the way —
what it refuses is a field, and this is a read.

What is worth testing about it is not the grep, which is `re` and `Path.glob`, but the three
decisions around it:

* **Where the declaration lives.** In the rationale section, so a `ship` deletes the query
  with the design that made the claim, and a reader who greps the pattern finds the paragraph
  saying what it is for. A `roadkeep.toml` entry would outlive the migration; a field on the
  line is what §RK72 refuses.
* **A query that declares nothing is answered, not refused.** *This design declares no query*
  is a fact about the task; a refusal there reads as evidence the id was wrong.
* **Nothing is counted in silence.** A glob that reached a file this cannot read as text is
  named, because a count over a set that quietly lost a member is the defect the whole verb
  is against.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.linting import lint
from roadkeep.remaining import FENCE, QueryError, count, declared

ROADMAP = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- 📋 **RK2** (deps: —) **A second symptom** — Because of another. → §RK2
"""

LEDGER = """# Shipped

## Block A — The model
"""

PROSE = f"""# Improvements

## Block A — The model

### §RK1 A migration with sites

The paragraph that says what the pattern is for.

```{FENCE}
src/*.py :: served
```

### §RK2 A design with no query

Prose and nothing else.
"""


def project(tmp_path: Path, prose: str = PROSE) -> Path:
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'improvements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    for name, body in (
        ("ROADMAP.md", ROADMAP),
        ("CHANGELOG.md", LEDGER),
        ("IMPROVEMENTS.md", prose),
    ):
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    (tmp_path / "src" / "one.py").write_text(
        "a = 1\nsaid = f'{served}lint'\nb = 2\nsaid = f'{served}show'\n", encoding="utf-8"
    )
    (tmp_path / "src" / "two.py").write_text("nothing here\n", encoding="utf-8")
    return tmp_path


# -- the grammar --------------------------------------------------------------


def test_a_section_with_no_fence_declares_nothing():
    assert declared("Just prose.\n") == ()


def test_a_clause_is_a_pathspec_and_a_pattern():
    found = declared(f"Prose.\n\n```{FENCE}\nsrc/*.py :: served\n```\n")
    assert len(found) == 1
    assert found[0].pathspec == "src/*.py"
    assert found[0].pattern == "served"


def test_a_comment_and_a_blank_line_are_not_clauses():
    found = declared(f"```{FENCE}\n# why this pattern\n\nsrc/*.py :: served\n```\n")
    assert [one.pathspec for one in found] == ["src/*.py"]


def test_several_clauses_in_one_block_are_one_query():
    found = declared(f"```{FENCE}\nsrc/*.py :: a\ntests/*.py :: b\n```\n")
    assert [one.pattern for one in found] == ["a", "b"]


def test_a_second_block_is_refused_rather_than_merged():
    """Two blocks are two claims about what is left, and the sum of them is a number
    neither paragraph states."""
    with pytest.raises(QueryError) as refused:
        declared(f"```{FENCE}\nsrc/*.py :: a\n```\n\n```{FENCE}\ntests/*.py :: b\n```\n")
    assert "the second" in str(refused.value)


@pytest.mark.parametrize(
    "clause, said",
    [
        ("src/*.py served", "no '::'"),
        (":: served", "both halves"),
        ("src/*.py ::", "both halves"),
        ("src/*.py :: (unclosed", "not a regex"),
    ],
)
def test_a_clause_this_grammar_cannot_read_names_the_line(clause, said):
    with pytest.raises(QueryError) as refused:
        declared(f"```{FENCE}\n{clause}\n```\n")
    assert said in str(refused.value)
    # The line inside the block, so a query of six clauses says which one (RK14's rule).
    assert refused.value.line == 2


# -- the count ----------------------------------------------------------------


def test_it_counts_the_sites_and_says_where_they_are(tmp_path):
    root = project(tmp_path)
    found = count(root, "RK1", declared(PROSE.split("### §RK2")[0]))
    assert found.total == 2
    assert found.files == 2
    assert [site.file for site in found.sites] == ["src/one.py", "src/one.py"]
    assert [site.lineno for site in found.sites] == [2, 4]


def test_a_glob_that_names_nothing_is_not_the_same_answer_as_a_pattern_that_matches_nothing(
    tmp_path,
):
    """Both count zero and they are opposite facts: the second is the work being done and
    the first is a typo in the pathspec, which is why the files read are reported too."""
    root = project(tmp_path)
    gone = count(root, "RK1", declared(f"```{FENCE}\nnowhere/*.py :: served\n```\n"))
    done = count(root, "RK1", declared(f"```{FENCE}\nsrc/*.py :: nothing-matches\n```\n"))
    assert gone.total == done.total == 0
    assert gone.files == 0
    assert done.files == 2


def test_a_file_it_cannot_read_as_text_is_named_and_never_dropped(tmp_path):
    root = project(tmp_path)
    (root / "src" / "three.py").write_bytes(b"\xff\xfe\x00binary")
    found = count(root, "RK1", declared(f"```{FENCE}\nsrc/*.py :: served\n```\n"))
    assert found.unread == ("src/three.py",)
    assert found.files == 2
    assert "not text this could search" in str(found)


# -- the verb -----------------------------------------------------------------


def test_the_command_answers_the_count_and_exits_zero(tmp_path, capsys):
    root = project(tmp_path)
    assert main(["-C", str(root), "remaining", "RK1"]) == EXIT_OK
    said = capsys.readouterr().out
    assert "RK1  2 site(s) left in 2 file(s)" in said
    assert "src/one.py:2" in said


def test_a_migration_with_work_left_is_never_a_failing_exit(tmp_path):
    """A read says the call was answered and never what the answer was: `lint` is what
    refuses, and a `remaining` that exited 1 while work was outstanding is a verb nobody
    could put in a loop."""
    root = project(tmp_path)
    assert main(["-C", str(root), "remaining", "RK1"]) == EXIT_OK


def test_a_design_that_declares_no_query_is_answered_and_not_refused(tmp_path, capsys):
    root = project(tmp_path)
    assert main(["-C", str(root), "remaining", "RK2"]) == EXIT_OK
    said = capsys.readouterr().out
    assert "declares no query" in said
    # And the grammar is named, because the next thing a caller wants is to write one.
    assert FENCE in said and "<pathspec> :: <regex>" in said


def test_a_task_with_no_section_is_refused_in_the_words_show_already_composed(tmp_path, capsys):
    root = project(tmp_path, prose="# Improvements\n\n## Block A — The model\n")
    assert main(["-C", str(root), "remaining", "RK1"]) == EXIT_USAGE
    assert "has no section" in capsys.readouterr().err


def test_an_id_no_file_carries_is_refused(tmp_path, capsys):
    root = project(tmp_path)
    assert main(["-C", str(root), "remaining", "RK99"]) == EXIT_USAGE


def test_the_json_carries_every_site_and_the_query_that_found_them(tmp_path, capsys):
    root = project(tmp_path)
    assert main(["-C", str(root), "remaining", "RK1", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "RK1"
    assert payload["total"] == 2
    assert payload["query"] == [{"pathspec": "src/*.py", "pattern": "served", "files": 2}]
    # Every site and not the printed ten: a consumer acting per address needs them all.
    assert len(payload["sites"]) == 2


def test_the_json_says_none_rather_than_zero_where_no_query_is_declared(tmp_path, capsys):
    """Zero is *the query found nothing*, which is a different fact from there being no
    query — and a consumer branching on the number would read the second as the first."""
    root = project(tmp_path)
    assert main(["-C", str(root), "remaining", "RK2", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["total"] is None and payload["query"] == []


# -- the gate -----------------------------------------------------------------


def test_the_gate_reports_a_block_it_cannot_read(tmp_path):
    """L1's backstop half for a fence: `remaining` refuses one it cannot read, and that verb
    is asked by whoever is continuing the migration — so a query nobody has run since it was
    typed is exactly the one that is wrong."""
    broken = PROSE.replace("src/*.py :: served", "src/*.py has no separator")
    root = project(tmp_path, prose=broken)
    report = lint(Config.discover(root))
    assert [one.code for one in report.findings] == ["remaining.format"]
    assert "cannot read" in report.findings[0].message


def test_a_section_declaring_no_query_is_silent(tmp_path):
    root = project(tmp_path)
    report = lint(Config.discover(root))
    assert not [one for one in report.findings if one.code.startswith("remaining")]


def test_sites_left_are_work_and_never_a_finding(tmp_path):
    """The count is `remaining`'s and never the gate's: a migration with sites left is not a
    defect in a file, and a gate that refused one would be a gate that fails until the work
    it is about is finished."""
    root = project(tmp_path)
    report = lint(Config.discover(root))
    assert report.clean


# -- a query that never ran, told apart from work that is done (RK1216) --------


def test_a_pathspec_that_reached_no_file_is_said_and_not_left_to_a_second_number(
    tmp_path, capsys
):
    """The defect, measured in pportal: `lib/src :: <regex>` names a directory, which
    `Path.glob` matches as one entry that is not a file, so the whole query answered `0
    site(s) left in 0 file(s)` over a tree holding 420. The regex was right and only the glob
    was wrong — and `0` is documented to mean the pattern stopped matching, so the reading an
    author gets is that the migration is finished."""
    prose = PROSE.replace("src/*.py :: served", "src :: served")
    root = project(tmp_path, prose=prose)
    assert main(["-C", str(root), "remaining", "RK1"]) == EXIT_OK
    printed = capsys.readouterr().out
    # On the headline, because the headline is the number being misread: a note under the
    # clauses is the `in 0 file(s)` problem again one line further down.
    first = printed.splitlines()[0]
    assert "matched no file" in first and "did not run" in first
    assert "← matched no file" in printed


def test_the_clause_that_reached_nothing_is_named_among_ones_that_did(tmp_path, capsys):
    """A three-clause query short by one is the worse case: the total still looks like a
    total, and the zero is one number among several rather than the whole answer."""
    prose = PROSE.replace(
        "src/*.py :: served", "src/*.py :: served\nlib :: served\nsrc/*.py :: nothing"
    )
    root = project(tmp_path, prose=prose)
    assert main(["-C", str(root), "remaining", "RK1", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["total"] > 0
    # Its own key: a consumer deciding whether a migration is finished reads `total`, and the
    # one state where `total` means nothing has to be answerable without hunting for a zero.
    assert payload["unmatched"] == ["lib"]
    # A pattern that matched nothing in files it *did* read is the other zero, and it is not
    # this one — that clause is the honest "no sites left".
    assert [one["files"] for one in payload["query"]] == [2, 0, 2]


def test_a_query_that_ran_says_nothing_about_matching_no_file(tmp_path, capsys):
    """The sentence is an exception and has to read as one: a clean count is unchanged."""
    root = project(tmp_path)
    assert main(["-C", str(root), "remaining", "RK1"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "matched no file" not in printed

    assert main(["-C", str(root), "remaining", "RK1", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["unmatched"] == []
