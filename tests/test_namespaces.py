"""Two prose files, two outlines, and the address that says which one (RK340).

`ref_scheme` is read once per project and applied to every role, and every outline starts
at `I`. Measured in an adopting project: `IMPROVEMENTS.md` opens at `§I — House constraints`
and `STRATEGY.md` at `§I — What this is`, both declare a `§III`, `lint` reports four
`section.ambiguous` on every run it has ever made, and ten pointers at the roadmap's own
non-goals resolve to nothing. The only fix available was hand-picking ranges that do not
overlap — numbering one file from `L` because the other reached `XLIX` — which is one
sequence wearing two headings and nothing keeps it true as either grows.

So `[refs] <role> = "<prefix>"` gives a file its own namespace, and what is asserted here is
that the namespace is a *namespace* rather than a spelling:

* the two files may both declare `I`, and the gate is clean about it;
* a prefixed role answers **only** prefixed addresses, and an unprefixed one only bare ones,
  because a role answering both would put the collision back one file over;
* the prefix rides on the **pointer** and never on the heading — the file is the answer to
  "which file", so writing it inside would be the answer stored in its own subject;
* nothing changes for a project that declares no `[refs]`, which is every project that has
  one prose file or two that never collided.
"""

from __future__ import annotations

import json

import pytest

from roadkeep.adopting import adopt
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config, ConfigError
from roadkeep.linting import lint
from roadkeep.schema import split_ref
from roadkeep.sections import SectionError, add, anchored, find, local, qualified

ROADMAP = "docs/ROADMAP.md"
IMPROVEMENTS = "docs/IMPROVEMENTS.md"
STRATEGY = "docs/STRATEGY.md"

BACKLOG = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §I.1
- 📋 **RK2** (deps: —) **A second symptom** — Because of another reason. → §S:I.1
"""

IMPROVEMENTS_BODY = """# Improvements

## I. House constraints

What this file is for.

### I.1 A first design

The reasoning the line has no room for.
"""

STRATEGY_BODY = """# Strategy

## I. What this is

What that file is for.

### I.1 A positioning note

The reasoning that line has no room for.
"""


def project(tmp_path, *, refs: str = '[refs]\nstrategy = "S"\n') -> Config:
    """Two prose files whose outlines both start at `I`, and what the project says about it."""
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\nref_scheme = "outline"\n{refs}'
        f'[files]\nroadmap = "{ROADMAP}"\nimprovements = "{IMPROVEMENTS}"\n'
        f'strategy = "{STRATEGY}"\n',
        encoding="utf-8",
    )
    for name, body in {
        ROADMAP: BACKLOG,
        IMPROVEMENTS: IMPROVEMENTS_BODY,
        STRATEGY: STRATEGY_BODY,
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


# -- the collision, and the configuration out of it --------------------------


def test_two_files_declaring_one_address_is_clean_once_one_has_a_namespace(tmp_path):
    # The whole task in one assertion: this is the exact shape that reported four
    # `section.ambiguous` and ten unresolved pointers, and no edit to either file fixed it.
    report = lint(project(tmp_path))
    assert [f.code for f in report.findings] == []


def test_without_the_namespace_the_same_files_are_the_defect(tmp_path):
    # Held so the test above is a demonstration and not a tautology about a clean fixture.
    config = project(tmp_path, refs="")
    rules = {f.code for f in lint(config).findings}
    assert "section.ambiguous" in rules
    # And the roadmap line that points into the prefixed file now points at nothing, which
    # is what a project without `[refs]` has instead: one namespace and one of each address.
    assert "ref.unresolved" in rules


# -- the estimate taken before the gate speaks (RK347) -----------------------


def test_the_estimate_names_the_address_two_files_declare(tmp_path):
    """RK347: every other limit `--sections` reports is a property of the file in front of it,
    so a doubling — which only exists across two — was the one finding it could not reach."""
    config = project(tmp_path, refs="")
    estimate = adopt(config, config.path("improvements"), sections=True)
    # Conforming on its own, which is the whole defect: this is the number an adopter priced
    # the commitment from, and the gate then filed a finding per collision against it.
    assert estimate.conforming == estimate.parsed and estimate.changing == 0
    assert estimate.ambiguous == (
        ("I", ("improvements", "strategy")),
        ("I.1", ("improvements", "strategy")),
    )


def test_the_declaration_the_estimate_names_is_the_one_that_closes_it(tmp_path):
    # The same run against the same files, with the line of configuration written: an estimate
    # naming a repair that leaves the number where it was would be worth nothing.
    config = project(tmp_path)
    assert adopt(config, config.path("improvements"), sections=True).ambiguous == ()


def test_the_command_names_both_files_and_the_declaration(tmp_path, capsys):
    project(tmp_path, refs="")
    target = str(tmp_path / IMPROVEMENTS)
    assert main(["-C", str(tmp_path), "adopt", target, "--sections"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "2 address(es) declared by both improvements and strategy (I, I.1)" in printed
    # Once, not once per address: the repair is one line of configuration for both of them.
    assert printed.count("[refs]") == 1
    # And the sibling it opened to answer that is not also reported as out of reach (RK291).
    assert STRATEGY not in printed.split("scope")[1]


def test_a_file_this_project_does_not_govern_is_measured_alone(tmp_path):
    """RK292's rule, one check further on: pointed at somebody else's file, `[files]` names
    siblings that belong to another project, and a collision between two of them is not a
    fact about the file the caller asked about."""
    config = project(tmp_path, refs="")
    outside = tmp_path / "NOTES.md"
    outside.write_text(IMPROVEMENTS_BODY, encoding="utf-8")
    assert adopt(config, outside, sections=True).ambiguous == ()


# -- the set the caller names, where no project declares one (RK359) ---------


def unadopted(tmp_path) -> tuple[Config, str, str]:
    """Two prose files under no declaration at all — the case `adopt` exists for."""
    config = project(tmp_path, refs="")
    notes, plans = tmp_path / "NOTES.md", tmp_path / "PLANS.md"
    notes.write_text(IMPROVEMENTS_BODY, encoding="utf-8")
    plans.write_text(STRATEGY_BODY, encoding="utf-8")
    return config, str(notes), str(plans)


def test_the_doubling_is_reachable_over_files_the_caller_names(tmp_path):
    """RK359: the collision an adopter meets first is between two files no `roadkeep.toml`
    declares, and until this the estimate could only see it after the commitment."""
    config, notes, plans = unadopted(tmp_path)
    # Alone it is the RK292 answer, and the same two files are conforming apart.
    assert adopt(config, notes, sections=True).ambiguous == ()
    estimate = adopt(config, notes, sections=True, alongside=[plans])
    # By path and not by role: these files hold none here, and labelling them with this
    # project's would name a set the caller never handed over.
    assert estimate.ambiguous == (
        ("I", ("NOTES.md", "PLANS.md")),
        ("I.1", ("NOTES.md", "PLANS.md")),
    )
    # Every other number stays about the target alone — one file's sections, one file's width.
    assert estimate.path.name == "NOTES.md" and estimate.parsed == 2


def test_a_file_named_twice_does_not_double_against_itself(tmp_path):
    # The one way a report of this shape can be false: read once per name, `NOTES.md` declares
    # every one of its own addresses twice and the answer is a collision with nobody.
    config, notes, _ = unadopted(tmp_path)
    assert adopt(config, notes, sections=True, alongside=[notes]).ambiguous == ()


def test_the_sibling_is_never_inferred_from_the_directory(tmp_path):
    # `PLANS.md` sits beside `NOTES.md` and is not read: which files are one outline is a fact
    # about somebody's layout, and a report that guessed it would measure an unnamed set.
    config, notes, _ = unadopted(tmp_path)
    assert adopt(config, notes, sections=True).ambiguous == ()


def test_the_set_is_a_sections_measurement_and_a_backlog_refuses_it(tmp_path):
    config, _, plans = unadopted(tmp_path)
    with pytest.raises(ValueError) as caught:
        adopt(config, config.path("roadmap"), alongside=[plans])
    assert "a backlog holds lines and not headings" in str(caught.value)


def test_the_command_takes_the_second_file_and_names_both(tmp_path, capsys):
    config, notes, plans = unadopted(tmp_path)
    assert main(
        ["-C", str(tmp_path), "adopt", notes, "--sections", "--with", plans]
    ) == EXIT_OK
    printed = capsys.readouterr().out
    assert "2 address(es) declared by both NOTES.md and PLANS.md (I, I.1)" in printed


def test_a_named_file_keeps_the_namespace_its_project_declared(tmp_path):
    """RK369: the prefix rides on the document's schema, so a path loaded directly carries
    none — and the estimate reported a collision the configuration had already resolved."""
    config = project(tmp_path)  # `[refs] strategy = "S"` is written
    named = adopt(
        config,
        config.path("improvements"),
        sections=True,
        alongside=[str(config.path("strategy"))],
    )
    # The same answer the roles give over the same two files, which is the whole claim: how a
    # file was reached may not change what the run says about it.
    assert named.ambiguous == adopt(config, config.path("improvements"), sections=True).ambiguous
    assert named.ambiguous == ()


def test_a_governed_file_is_labelled_by_its_role_and_a_foreign_one_by_its_path(tmp_path):
    # Each file named the truest way this project can name it: `[files]` gives one a role, and
    # a file it does not govern has none to be called by.
    config = project(tmp_path, refs="")
    outside = tmp_path / "NOTES.md"
    outside.write_text(STRATEGY_BODY, encoding="utf-8")
    estimate = adopt(
        config, config.path("improvements"), sections=True, alongside=[str(outside)]
    )
    assert estimate.ambiguous == (
        ("I", ("improvements", "NOTES.md")),
        ("I.1", ("improvements", "NOTES.md")),
    )
    # RK371: and which of the two is which is recorded, not left to the sentence around it.
    assert estimate.by_path == ("NOTES.md",)


def test_which_files_were_outside_the_project_is_answered_without_a_collision(tmp_path):
    # Over the set that was read and not over the doubling: a run whose files agree is the run
    # an adopter most wants the scope of, and a field derived from the collisions would be
    # empty exactly then.
    config = project(tmp_path, refs="")
    outside = tmp_path / "NOTES.md"
    outside.write_text("# Notes\n\n## XL. A design\n\nProse.\n", encoding="utf-8")
    estimate = adopt(
        config, config.path("improvements"), sections=True, alongside=[str(outside)]
    )
    assert estimate.ambiguous == () and estimate.by_path == ("NOTES.md",)


def test_a_prose_file_the_set_left_out_is_named_unread(tmp_path):
    """RK373: `--with` replaces the declared set, and the sentence naming what went unread was
    handed every prose role — so the one line whose job is to say which cross-file checks were
    not made said a collision had been looked for in a file nobody opened."""
    config = project(tmp_path, refs="")
    outside = tmp_path / "NOTES.md"
    outside.write_text(STRATEGY_BODY, encoding="utf-8")
    narrowed = adopt(
        config, config.path("improvements"), sections=True, alongside=[str(outside)]
    )
    assert narrowed.unopened == (ROADMAP, STRATEGY)
    # And the run that reads every prose file still says so: the answer follows what was
    # opened, so neither case is a rule the other has to be an exception to.
    assert adopt(config, config.path("improvements"), sections=True).unopened == (ROADMAP,)


def test_a_declared_file_read_by_path_is_not_therefore_called_ungoverned(tmp_path, capsys):
    """RK372: the report said `unopened: ()` about a file and, in the same payload, that this
    project had no role for it. Both were printed and one of them was wrong."""
    config = project(tmp_path, refs="")
    argv = ["-C", str(tmp_path), "adopt", str(config.path("improvements")), "--sections"]
    assert main([*argv, "--with", str(config.path("roadmap")), "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    # It was read, so it is not out of reach — the RK359 rule, unchanged.
    assert ROADMAP not in payload["unopened"]
    # And the field beside it says only how the file was named: a backlog has no outline to
    # collide in, so it is read by path, which is a fact about this run and not about who
    # owns the file.
    assert payload["by_path"] == [ROADMAP]


def test_the_payload_files_each_name_under_the_key_that_says_what_it_is(tmp_path, capsys):
    """RK371: `--json` is taken by the caller who took it *not* to open a file, and a `roles`
    list holding filenames sent it to look up something `[files]` was never going to answer."""
    config = project(tmp_path, refs="")
    outside = tmp_path / "NOTES.md"
    outside.write_text(STRATEGY_BODY, encoding="utf-8")
    argv = ["-C", str(tmp_path), "adopt", str(config.path("improvements")), "--sections"]
    assert main([*argv, "--with", str(outside), "--json"]) == EXIT_OK
    mixed = json.loads(capsys.readouterr().out)["ambiguous"]
    assert mixed[0] == {
        "anchor": "I",
        "declared_by": [{"role": "improvements"}, {"path": "NOTES.md"}],
    }
    # And a run that named nothing is all roles, which is every project that has not used
    # `--with`: the key is a fact about each name and not a mode the flag switches on.
    assert main([*argv, "--json"]) == EXIT_OK
    roles = json.loads(capsys.readouterr().out)["ambiguous"]
    assert roles[0]["declared_by"] == [{"role": "improvements"}, {"role": "strategy"}]


def test_a_named_file_this_project_governs_is_not_then_called_unread(tmp_path):
    # `opened`'s rule, applied to the second way a sibling gets read (RK347): a report may not
    # measure a file and say in the same breath that it was out of reach.
    config = project(tmp_path, refs="")
    estimate = adopt(
        config,
        config.path("improvements"),
        sections=True,
        alongside=[str(config.path("roadmap"))],
    )
    assert "roadmap" not in estimate.unopened and ROADMAP not in estimate.unopened


def test_the_gate_names_the_configuration_rather_than_an_edit(tmp_path):
    # The remedy is not "rename one of them": both files number their own outline from I, so
    # the edit the finding would be asking for is a renumbering of somebody's whole document.
    findings = lint(project(tmp_path, refs="")).findings
    said = next(f for f in findings if f.code == "section.ambiguous")
    assert "[refs]" in said.message and "§<prefix>:<x.y>" in said.message


def test_declaring_a_namespace_moves_every_pointer_into_it(tmp_path):
    # The cost of the declaration, stated: a role that answers only prefixed addresses is one
    # whose old bare pointers now resolve to nothing — reported per line, by the gate, rather
    # than silently re-resolved to the file that happens to still answer.
    config = project(tmp_path, refs='[refs]\nstrategy = "S"\nimprovements = "D"\n')
    assert [f.code for f in lint(config).findings] == ["ref.unresolved"]
    (tmp_path / ROADMAP).write_text(
        BACKLOG.replace("§I.1", "§D:I.1"), encoding="utf-8"
    )
    # Repointed, and the remedy sentence is gone with the collision: `[refs]` has nothing
    # left to offer a project that has already declared both.
    assert [f.code for f in lint(Config.discover(tmp_path)).findings] == []


# -- an address in one namespace is not an address in the other --------------


def test_a_prefixed_role_answers_only_prefixed_addresses(tmp_path):
    config = project(tmp_path)
    strategy = config.document("strategy")
    assert find(strategy, "S:I.1") is not None
    # The bare address is the *other* file's, and a role that answered both would be the
    # collision one file over rather than the fix.
    assert find(strategy, "I.1") is None


def test_an_unprefixed_role_answers_only_bare_addresses(tmp_path):
    config = project(tmp_path)
    improvements = config.document("improvements")
    assert find(improvements, "I.1") is not None
    assert find(improvements, "S:I.1") is None


def test_the_sections_of_a_prefixed_file_carry_the_project_address(tmp_path):
    # `anchored` is what the gate reads both files into one index with, so the qualification
    # happens there — once — and every reader downstream compares comparable addresses.
    config = project(tmp_path)
    assert [s.anchor for s in anchored(config.document("strategy"))] == ["S:I", "S:I.1"]
    assert [s.anchor for s in anchored(config.document("improvements"))] == ["I", "I.1"]


def test_the_namespace_is_on_the_pointer_and_never_in_the_heading(tmp_path):
    config = project(tmp_path)
    schema = config.schema_for("strategy")
    assert qualified(schema, "I.1") == "S:I.1" and local(schema, "S:I.1") == "I.1"
    # And the file says so: the heading a reader sees is the one the author wrote.
    assert "## I. What this is" in (tmp_path / STRATEGY).read_text(encoding="utf-8")
    assert "S:" not in (tmp_path / STRATEGY).read_text(encoding="utf-8")


def test_a_section_written_into_the_wrong_namespace_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SectionError) as raised:
        add(config, "improvements", "S:I.2", "A design", "The prose it carries.")
    assert [v.code for v in raised.value.violations] == ["anchor.namespace"]


def test_a_section_add_writes_the_bare_heading_under_the_named_role(tmp_path):
    config = project(tmp_path)
    document, section = add(config, "strategy", "S:I.2", "A second note", "The prose.")
    assert section.anchor == "S:I.2"
    assert "### I.2 A second note" in "".join(document.lines)
    assert "S:I.2" not in "".join(document.lines)


# -- what the reads say ------------------------------------------------------


def test_the_free_address_is_derived_per_namespace(tmp_path, capsys):
    # A maximum taken across both files would hand the shorter one the taller one's number,
    # and reading the mixed set as one sequence answers "none derives" — which is the useful
    # answer withheld from exactly the projects that configured their way out of the mess.
    config = project(tmp_path)
    assert main(["-C", str(config.root), "anchors", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    spaces = {row["namespace"]: row["next"] for row in payload["next_families"]}
    assert spaces == {None: "II", "S": "S:II"}


def test_the_listing_names_a_free_family_in_each_namespace(tmp_path, capsys):
    config = project(tmp_path)
    assert main(["-C", str(config.root), "anchors"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "§II — no family ever used it" in out
    assert "§S:II — no family in S ever used it" in out


def test_show_resolves_a_prefixed_pointer_to_one_file(tmp_path, capsys):
    config = project(tmp_path)
    assert main(["-C", str(config.root), "show", "RK2"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "A positioning note" in out and "A first design" not in out


# -- the declaration itself --------------------------------------------------


def test_a_namespace_for_a_role_that_holds_no_headings_is_refused(tmp_path):
    with pytest.raises(ConfigError) as raised:
        project(tmp_path, refs='[refs]\nroadmap = "R"\n')
    assert "not a prose role" in str(raised.value)


def test_a_namespace_under_the_id_scheme_is_refused(tmp_path):
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[refs]\nstrategy = "S"\n[files]\nroadmap = "{ROADMAP}"\n'
        f'strategy = "{STRATEGY}"\n',
        encoding="utf-8",
    )
    with pytest.raises(ConfigError) as raised:
        Config.discover(tmp_path)
    assert "already unique" in str(raised.value)


def test_two_roles_may_not_share_one_namespace(tmp_path):
    with pytest.raises(ConfigError) as raised:
        project(tmp_path, refs='[refs]\nstrategy = "S"\nimprovements = "S"\n')
    assert "already" in str(raised.value)


def test_a_namespace_is_one_word_and_never_a_dotted_one(tmp_path):
    # A dot is what an outline segments by, so `S.I` would be a child of something called S
    # to every reader that splits one — which is why the separator is a colon.
    with pytest.raises(ConfigError) as raised:
        project(tmp_path, refs='[refs]\nstrategy = "S.x"\n')
    assert "letters and digits" in str(raised.value)


def test_a_namespace_for_a_file_the_project_does_not_declare_is_refused(tmp_path):
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\nref_scheme = "outline"\n[refs]\nstrategy = "S"\n'
        f'[files]\nroadmap = "{ROADMAP}"\nimprovements = "{IMPROVEMENTS}"\n',
        encoding="utf-8",
    )
    with pytest.raises(ConfigError) as raised:
        Config.discover(tmp_path)
    assert "declares no 'strategy' file" in str(raised.value)


def test_a_line_may_carry_a_prefix_the_format_reads_but_no_file_answers(tmp_path, capsys):
    # Shape is the schema's and membership is the gate's: a pointer at a namespace nothing
    # declares is `ref.unresolved` against the files, not a violation about a legal spelling.
    config = project(tmp_path)
    (tmp_path / ROADMAP).write_text(
        BACKLOG.replace("§S:I.1", "§Q:I.1"), encoding="utf-8"
    )
    rules = [f.code for f in lint(Config.discover(tmp_path)).findings]
    assert rules == ["ref.unresolved"]
    assert config.schema.validate  # the schema had nothing to say about it


def test_an_address_is_split_once_and_kept_verbatim():
    assert split_ref("S:I.1") == ("S", "I.1")
    assert split_ref("I.1") == ("", "I.1")
    # Two colons is one prefix and a tail that fails the anchor check with the text typed,
    # rather than a silent re-cut into something that parses.
    assert split_ref("S:x:1") == ("S", "x:1")


def test_a_line_whose_prefix_is_not_a_word_is_a_format_violation(tmp_path):
    config = project(tmp_path)
    schema = config.schema
    task = config.document("roadmap").entries[0].task
    bad = [v.code for v in schema.validate(_reffed(task, "1S:I.1"))]
    assert bad == ["ref.format"]


def _reffed(task, ref):
    from dataclasses import replace

    return replace(task, ref=ref)


def test_nothing_changes_for_a_project_that_declares_no_namespace(tmp_path):
    # The default is what every project had: one flat set of addresses across both files,
    # which is right where they never collide and is what `[refs]` is opt-in about.
    config = project(tmp_path, refs="")
    assert config.refs == {}
    assert config.schema_for("strategy").ref_prefix == ""
    assert [s.anchor for s in anchored(config.document("strategy"))] == ["I", "I.1"]


def test_the_usage_exit_is_the_one_a_bad_declaration_gets(tmp_path, capsys):
    project(tmp_path, refs='[refs]\nstrategy = "S"\n')
    (tmp_path / "roadkeep.toml").write_text(
        (tmp_path / "roadkeep.toml").read_text(encoding="utf-8").replace('"S"', '"S.x"'),
        encoding="utf-8",
    )
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_USAGE
