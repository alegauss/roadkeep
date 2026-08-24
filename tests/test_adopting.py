"""The two doors into a project the tool does not own yet (RK18).

`init` and `adopt` are tested against opposite failure modes, because they have opposite
risks. A scaffold's risk is that it writes: the assertions here are that it writes nothing
when anything is in the way, and that what it does write is a project the *rest* of the
tool then works on — `add`, `section add`, `ship` and `lint` are run over the output,
because a scaffold proven only by its own file listing is a scaffold proven by nothing.

An estimate's risk is the opposite: that it reports a number nobody can act on. So the
claims are that it never fails (exit 0 on a file with eighty defects — an estimate with a
gate's exit code is a gate), that a prefix it guessed is *labelled* as guessed, and that
the counts move for the reason the reader would assume they moved.

And the corpus that decides §RK20: Shio's roadmap, read where it lives and never written
to, skipped on any machine but the author's.
"""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import fields, replace
from pathlib import Path

import pytest

import corpora
from roadkeep.adopting import (
    AlreadyConfigured,
    BlockedParent,
    Estimate,
    NotACorpus,
    RepeatedBlock,
    Unreadable,
    UnreadableBlock,
    WouldOverwrite,
    blocking,
    adopt,
    init,
    render_config,
)
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config, Scope
from roadkeep.kernel.schema import CODE_POINTS, UTF16_UNITS, WORDS, Schema
from roadkeep.kernel.document import Document, ledger_slots
from roadkeep.linting import lint
from roadkeep.sections import unanchored, words

SHIO = Path("D:/Git/viglet/shio/latest/docs/ROADMAP.md")

CONFORMING = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- 💭 **RK2** (deps: RK1) **A second symptom** — Because of another reason. → §RK2
"""

FOREIGN = """# Roadmap

## Block A — The model

- 📋 **SH1** (deps: —) **A symptom from another backlog** — Because of a reason. → §SH1
- 📋 **SH2** (deps: SH1) **A second one** — Because of another reason. → §SH2
- ✨ **SH3** (deps: —) **A marker nobody declared** — Because of a third reason. → §SH3
"""


def scaffolded(tmp_path: Path, **kwargs) -> Config:
    init(tmp_path, **kwargs)
    return Config.discover(tmp_path)


def written(tmp_path: Path) -> set[str]:
    return {
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }


# -- init writes a project the rest of the tool works on ---------------------


def test_scaffold_is_a_project_lint_passes(tmp_path: Path, capsys) -> None:
    assert main(["-C", str(tmp_path), "init"]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_OK
    assert "clean" in capsys.readouterr().out



def test_the_strategy_file_is_scaffolded_only_where_it_is_asked_for(tmp_path: Path) -> None:
    """RK1186's two halves, and neither works alone.

    A bare `init` writes three files and declares three keys — the strategy role is opt-in
    because the two prose roles answer different questions, and a project with no
    specification above its backlog would get a file it never opens. With `--strategy` it
    writes four and declares four, which is the second half: the file and the key are one
    transaction, and `_verify` refuses the scaffold whole where they disagree.
    """
    from roadkeep.adopting import SCAFFOLD_ROLES, STRATEGY_ROLE, init

    bare = init(tmp_path / "plain", blocks=("A",))
    assert [one.name for one in bare.files] == ["ROADMAP.md", "CHANGELOG.md", "IMPROVEMENTS.md"]
    assert "strategy" not in bare.config.read_text(encoding="utf-8")

    asked = init(
        tmp_path / "split", blocks=("A",), roles=(*SCAFFOLD_ROLES, STRATEGY_ROLE)
    )
    assert [one.name for one in asked.files] == [
        "ROADMAP.md",
        "CHANGELOG.md",
        "IMPROVEMENTS.md",
        "STRATEGY.md",
    ]
    # The key as well as the file: a scaffold that wrote one without the other is the
    # half-configured project `_verify` exists to refuse.
    assert 'strategy = "docs/STRATEGY.md"' in asked.config.read_text(encoding="utf-8")


def test_the_deferred_store_is_scaffolded_only_where_it_is_asked_for(tmp_path: Path) -> None:
    """RK1259, and the same two halves one role over.

    Opt-in for the reason the strategy file is, plus one of its own: a project that never
    pauses anything has no store rather than an empty one. What it closes is the other side —
    `defer` refuses where no store is declared and will not scaffold one on the way past, so
    the remedy was a toml key and a skeleton no verb offered to write.
    """
    from roadkeep.adopting import DEFERRED_ROLE, SCAFFOLD_ROLES, init

    bare = init(tmp_path / "plain", blocks=("A",))
    assert "deferred" not in bare.config.read_text(encoding="utf-8")

    asked = init(
        tmp_path / "pausing", blocks=("A — The model",), roles=(*SCAFFOLD_ROLES, DEFERRED_ROLE)
    )
    assert [one.name for one in asked.files] == [
        "ROADMAP.md",
        "CHANGELOG.md",
        "IMPROVEMENTS.md",
        "DEFERRED.md",
    ]
    assert 'deferred = "docs/DEFERRED.md"' in asked.config.read_text(encoding="utf-8")
    # The block headings, mirrored as they are into every other file this writes: a line is
    # set aside under the heading it was open under, and no write invents one (RK37).
    store = (tmp_path / "pausing" / "docs" / "DEFERRED.md").read_text(encoding="utf-8")
    assert store.startswith("# Set aside\n") and "## Block A — The model" in store


def test_the_pause_door_the_scaffold_opened_is_one_defer_can_walk_through(
    tmp_path: Path, capsys
) -> None:
    """The claim the file listing cannot make, and the whole point of the task: the verb that
    was refused now runs on a project this command created."""
    from roadkeep.adopting import DEFERRED_ROLE, SCAFFOLD_ROLES, init

    init(tmp_path, blocks=("A",), roles=(*SCAFFOLD_ROLES, DEFERRED_ROLE))
    assert main([
        "-C", str(tmp_path), "add", "--block", "A", "--symptom", "A symptom",
        "--why", "Because of a reason.", "--section", "A design",
        "--section-body", "Prose the author wrote.",
    ]) == EXIT_OK
    capsys.readouterr()
    assert main([
        "-C", str(tmp_path), "defer", "RK1", "--reason", "It waits on traffic nothing produces.",
    ]) == EXIT_OK
    assert "RK1" in (tmp_path / "docs" / "DEFERRED.md").read_text(encoding="utf-8")
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_OK


# -- declare: the role a configured project turns out to want (RK1264) --------


def test_a_configured_project_can_declare_the_role_the_scaffold_declined(tmp_path: Path) -> None:
    """RK1264. `[files]` is written once, by the command that refuses to run twice, so a role
    declined at scaffold time was retrofitted by hand-editing configuration this tool otherwise
    owns — and `init --deferred` on a configured tree answers `AlreadyConfigured`."""
    from roadkeep.adopting import AlreadyConfigured, DEFERRED_ROLE, SCAFFOLD_ROLES, declare, init

    init(tmp_path, blocks=("A — The model", "B — Authoring"))
    config = Config.discover(tmp_path)
    assert not config.has("deferred")
    # The door that was closed, still closed: this is the state the task is about.
    with pytest.raises(AlreadyConfigured):
        init(tmp_path, roles=(*SCAFFOLD_ROLES, DEFERRED_ROLE))

    written = declare(config, "deferred")
    assert written.role == "deferred"
    assert 'deferred = "docs/DEFERRED.md"' in (tmp_path / "roadkeep.toml").read_text(
        encoding="utf-8"
    )
    # The block headings the roadmap carries, spelled as that file spells one — a governed file
    # with none is one every write then refuses with "no heading declares".
    store = (tmp_path / "docs" / "DEFERRED.md").read_text(encoding="utf-8")
    assert store.startswith("# Set aside\n")
    assert "## Block A — The model" in store
    assert "## Block B — Authoring" in store
    assert written.blocks == ("A", "B")


def test_the_role_it_declared_is_one_the_refused_verb_can_now_reach(tmp_path: Path, capsys) -> None:
    """The claim the file listing cannot make, and the whole point: the verb whose refusal sent
    the caller here runs on the project this command changed, and the gate still passes."""
    from roadkeep.adopting import declare

    init(tmp_path, blocks=("A",))
    assert main([
        "-C", str(tmp_path), "add", "--block", "A", "--symptom", "A symptom",
        "--why", "Because of a reason.", "--section", "A design",
        "--section-body", "Prose the author wrote.",
    ]) == EXIT_OK
    capsys.readouterr()
    # Refused, and the refusal is what this task is the remedy for.
    assert main([
        "-C", str(tmp_path), "defer", "RK1", "--reason", "It waits on nothing that happens.",
    ]) != EXIT_OK
    capsys.readouterr()

    declare(Config.discover(tmp_path), "deferred")
    assert main([
        "-C", str(tmp_path), "defer", "RK1", "--reason", "It waits on nothing that happens.",
    ]) == EXIT_OK
    assert "RK1" in (tmp_path / "docs" / "DEFERRED.md").read_text(encoding="utf-8")
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_OK


def test_the_config_keeps_every_byte_it_did_not_come_to_change(tmp_path: Path) -> None:
    """A targeted insertion and never a serialiser, which is `_with_namespace`'s rule and
    `bump_version`'s before it: a `tomllib` round-trip drops the comments a scaffolded config is
    mostly made of. Placed after the table's last key, never under whatever table follows."""
    from roadkeep.adopting import declare

    init(tmp_path, blocks=("A",))
    source = tmp_path / "roadkeep.toml"
    before = source.read_text(encoding="utf-8")
    declare(Config.discover(tmp_path), "strategy")
    after = source.read_text(encoding="utf-8")

    assert after.replace('strategy = "docs/STRATEGY.md"\n', "", 1) == before
    files = after[after.index("[files]") :]
    # Inside `[files]` and after its last key: the next table heading comes later.
    assert files.index("strategy =") < files.index("\n[")


def test_a_role_already_declared_is_refused_and_so_is_one_nothing_governs(tmp_path: Path) -> None:
    from roadkeep.adopting import NoSuchRole, RoleDeclared, declare

    init(tmp_path, blocks=("A",))
    config = Config.discover(tmp_path)
    with pytest.raises(RoleDeclared) as held:
        declare(config, "roadmap")
    # It names what it found, which is also the answer to "why did nothing happen".
    assert 'roadmap = "docs/ROADMAP.md"' in str(held.value)

    with pytest.raises(NoSuchRole) as absent:
        declare(config, "notes")
    assert "is not a role this format governs" in str(absent.value)
    # Nothing written by either: the tree is the scaffold and no more.
    assert not (tmp_path / "docs" / "DEFERRED.md").exists()


def test_a_file_already_there_is_never_overwritten(tmp_path: Path) -> None:
    """`init`'s own rule at this door: the role is undeclared and the path is taken, which is a
    project that made the file by hand and never got the key — so the write refuses and the
    file it would have clobbered is the reason."""
    from roadkeep.adopting import WouldOverwrite, declare

    init(tmp_path, blocks=("A",))
    standing = tmp_path / "docs" / "DEFERRED.md"
    standing.write_text("# Set aside\n\nprose somebody wrote\n", encoding="utf-8")
    with pytest.raises(WouldOverwrite):
        declare(Config.discover(tmp_path), "deferred")
    assert "prose somebody wrote" in standing.read_text(encoding="utf-8")
    assert "deferred" not in (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")


def test_the_path_is_the_callers_where_they_name_one(tmp_path: Path) -> None:
    from roadkeep.adopting import declare

    init(tmp_path, blocks=("A",))
    written = declare(Config.discover(tmp_path), "deferred", "docs/paused/LATER.md")
    assert written.path == tmp_path / "docs" / "paused" / "LATER.md"
    assert 'deferred = "docs/paused/LATER.md"' in (tmp_path / "roadkeep.toml").read_text(
        encoding="utf-8"
    )
    assert Config.discover(tmp_path).has("deferred")


def test_the_command_reports_the_verb_the_role_opens(tmp_path: Path, capsys) -> None:
    init(tmp_path, blocks=("A",))
    assert main(["-C", str(tmp_path), "declare", "deferred"]) == EXIT_OK
    out = capsys.readouterr().out
    assert 'declared deferred = "docs/DEFERRED.md"' in out
    # The question a caller has next, which is the one the refusal that sent them here was about.
    assert "defer <id> --reason" in out
    assert "stage    git add --" in out


def test_the_flag_reaches_the_scaffold_from_the_command_line(tmp_path: Path, capsys) -> None:
    assert main(["-C", str(tmp_path), "init", "--deferred"]) == EXIT_OK
    capsys.readouterr()
    assert 'deferred = "docs/DEFERRED.md"' in (
        tmp_path / "roadkeep.toml"
    ).read_text(encoding="utf-8")


def test_an_unconfigured_project_is_not_missing_a_deferred_file(tmp_path: Path) -> None:
    """The measurement `STRATEGY_PATH` was moved for, asked of the constant beside it: this
    says where `init --deferred` would put a store, never what a project already has."""
    from roadkeep.config import Config

    config = Config.discover(tmp_path)
    assert config.source is None
    assert "deferred" not in config.missing()


def test_an_unconfigured_project_is_not_missing_a_strategy_file(tmp_path: Path) -> None:
    """The measurement that moved `STRATEGY_PATH` out of `DEFAULT_PATHS` (RK1186).

    That table declares the layout a project **has** when it declares none, so a row in it
    is a file the project is expected to have — and a strategy row made `missing()` name one
    on every unconfigured tree. Where the constant lives is the fix, and this is what says so.
    """
    from roadkeep.config import Config

    config = Config.discover(tmp_path)
    assert config.source is None
    assert "strategy" not in config.missing()


def test_scaffold_takes_the_whole_lifecycle(tmp_path: Path, capsys, monkeypatch) -> None:
    """The claim the file listing cannot make: `add`, `section`, `ship` and `lint` all run.

    A scaffold is only correct if the block headings it wrote are the ones every write
    files under — the failure this catches is a heading that reads as prose to the parser
    and refuses every task with `UnknownBlock` on the project's first day.
    """
    where = ["-C", str(tmp_path)]
    assert main([*where, "init", "--block", "A — The model"]) == EXIT_OK
    assert (
        main(
            [
                *where,
                "add",
                "--block",
                "A",
                "--symptom",
                "The scaffold is never written to",
                "--why",
                "A file nothing writes to is a file whose shape was never tested.",
            ]
        )
        == EXIT_OK
    )
    monkeypatch.setattr("sys.stdin", _Stdin("The reasoning the line has no room for."))
    assert main([*where, "section", "add", "RK1", "--title", "The first"]) == EXIT_OK
    assert main([*where, "ship", "RK1", "--why", "It works now."]) == EXIT_OK
    capsys.readouterr()
    assert main([*where, "lint"]) == EXIT_OK
    assert "clean" in capsys.readouterr().out


def test_config_reads_back_as_the_schema_it_was_rendered_from(tmp_path: Path) -> None:
    """The scaffold cannot declare a format the tool does not implement.

    Less `origins`, which is not part of the format: the scaffold writes every limit out
    explicitly, so a schema read back from it cites those lines where a bare `Schema()`
    cites nothing (RK1067) — a difference in provenance and not in what is enforced.
    """
    init(tmp_path)
    written = Config.load(tmp_path / "roadkeep.toml").schema
    assert replace(written, origins=()) == Schema()
    # And the citations really are the file it was just written to, which is the whole
    # affordance: an author refused over one of these numbers is one line from it.
    assert dict(written.origins)["why_max"].startswith("roadkeep.toml:")


def test_config_follows_the_schema_and_not_a_template() -> None:
    """A default that moves moves the scaffold, because the value is read off the object."""
    rendered = render_config(
        Schema(prefixes=("SH",), symptom_max=99), {"roadmap": "docs/ROADMAP.md"}
    )
    assert 'prefix = "SH"' in rendered
    assert "symptom = 99" in rendered
    assert 'roadmap = "docs/ROADMAP.md"' in rendered
    assert "changelog" not in rendered


def test_only_the_ledger_slots_a_file_lacks_are_written_out() -> None:
    # A key is emitted only when it is false (RK43, RK48): a default written out reads as a
    # decision somebody made about a slot the file carries anyway.
    paths = {"roadmap": "docs/ROADMAP.md"}
    assert "ledger" not in render_config(Schema(), paths)
    for field, key in (("ledger_marker", "marker"), ("ledger_symptom", "symptom")):
        rendered = render_config(replace(Schema(), **{field: False}), paths)
        assert "[ledger]" in rendered and f"{key} = false" in rendered
        parsed = Config.parse(tomllib.loads(rendered), root=".").schema
        assert getattr(parsed, field) is False
        # And only that one: the other slot is still the default the file has.
        other = "ledger_symptom" if field == "ledger_marker" else "ledger_marker"
        assert getattr(parsed, other) is True


def test_only_a_declared_id_shape_is_written_out() -> None:
    # RK106, and the same rule as the two above: `pad = 1` reads as a width somebody chose
    # rather than as the unpadded id nobody had to.
    paths = {"roadmap": "docs/ROADMAP.md"}
    assert "[ids]" not in render_config(Schema(), paths)
    rendered = render_config(Schema(prefixes=("D",), id_pad=2, id_suffix=True), paths)
    assert "[ids]" in rendered and "pad = 2" in rendered and "suffix = true" in rendered
    parsed = Config.parse(tomllib.loads(rendered), root=".").schema
    assert (parsed.id_pad, parsed.id_suffix) == (2, True)


def test_prefix_is_carried_into_the_first_id(tmp_path: Path, capsys) -> None:
    assert main(["-C", str(tmp_path), "init", "--prefix", "SH"]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "next-id"]) == EXIT_OK
    assert capsys.readouterr().out.strip() == "SH1"


def test_every_named_block_is_declared_in_all_three_files(tmp_path: Path) -> None:
    """The ledger and the rationale file are filed under the same headings (RK37)."""
    config = scaffolded(tmp_path, blocks=("A", "B — Authoring"))
    for role in ("roadmap", "changelog", "improvements"):
        document = config.document(role)
        assert [h.label for h in document.headings if h.label] == ["A", "B"]


def test_non_goals_heading_exists_from_the_start(tmp_path: Path) -> None:
    config = scaffolded(tmp_path)
    texts = [h.text for h in config.document("roadmap").headings]
    assert "Non-goals" in texts


# -- init refuses, and refusing means nothing was written --------------------


def test_a_configured_project_is_adopt_s_problem(tmp_path: Path) -> None:
    (tmp_path / "roadkeep.toml").write_text('prefix = "RK"\n', encoding="utf-8")
    with pytest.raises(AlreadyConfigured):
        init(tmp_path)
    assert written(tmp_path) == {"roadkeep.toml"}


def test_pyproject_that_declares_roadkeep_counts_as_configured(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.roadkeep]\nprefix = "RK"\n', encoding="utf-8"
    )
    with pytest.raises(AlreadyConfigured):
        init(tmp_path)


def test_an_ancestor_s_config_is_shadowed_not_clobbered(tmp_path: Path) -> None:
    """A subproject may declare its own format; the walk finds the nearest (RK3)."""
    (tmp_path / "roadkeep.toml").write_text('prefix = "RK"\n', encoding="utf-8")
    inner = tmp_path / "packages" / "inner"
    inner.mkdir(parents=True)
    init(inner, prefix="IN")
    assert Config.discover(inner).schema.prefix == "IN"


def test_one_existing_file_refuses_all_of_them(tmp_path: Path) -> None:
    """All-or-nothing: a half-scaffolded project reads as configured and is neither."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "CHANGELOG.md").write_text("# Mine\n", encoding="utf-8")
    with pytest.raises(WouldOverwrite):
        init(tmp_path)
    assert written(tmp_path) == {"docs/CHANGELOG.md"}


def test_the_refusal_names_the_door_for_the_backlog_it_found(tmp_path: Path) -> None:
    # RK282: `AlreadyConfigured` always named `adopt`, and this is the branch that needed it
    # more — a repository with a backlog and no declaration has never met this tool, while the
    # refusal that named the door is reached by a project that already adopted.
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ROADMAP.md").write_text("# Mine\n", encoding="utf-8")
    with pytest.raises(WouldOverwrite) as raised:
        init(tmp_path)
    message = str(raised.value)
    # Relative, for the reason `invocation` gives: an absolute path is about one machine.
    assert "`adopt docs/ROADMAP.md` reports" in message
    assert str(tmp_path) not in message.split("—")[1]


def test_the_configuration_is_not_a_file_an_estimate_is_taken_over(tmp_path: Path) -> None:
    """`adopt` reads a backlog; pointing it at `roadkeep.toml` is a different refusal one
    command later, so the door names documents and never the declaration.

    Built directly rather than through `init`: a project that has a `roadkeep.toml` raises
    `AlreadyConfigured` before the clash list is ever assembled, so this is the one shape of
    the exception that door cannot reach — and the filter is still what keeps it right if it
    ever does."""
    refusal = WouldOverwrite([tmp_path / "roadkeep.toml"], tmp_path)
    assert refusal.adoptable == ()
    assert "adopt" not in str(refusal)


def test_more_than_one_backlog_names_one_door_and_counts_the_rest(tmp_path: Path) -> None:
    """Every path is already listed above; repeating them as doors doubled a message that is
    mostly pathname."""
    (tmp_path / "docs").mkdir()
    for name in ("ROADMAP.md", "CHANGELOG.md"):
        (tmp_path / "docs" / name).write_text("# Mine\n", encoding="utf-8")
    with pytest.raises(WouldOverwrite) as raised:
        init(tmp_path)
    assert len(raised.value.adoptable) == 2
    assert "(and 1 more) reports" in str(raised.value)


def test_a_block_no_heading_could_declare_is_refused(tmp_path: Path) -> None:
    with pytest.raises(UnreadableBlock):
        init(tmp_path, blocks=("— The model",))
    assert written(tmp_path) == set()


def test_a_directory_a_file_is_standing_in_is_refused_before_anything_lands(
    tmp_path: Path,
) -> None:
    """RK392: `exists` answers whether a write would clobber, not whether it can happen — so
    a `docs` that is a file left `roadkeep.toml` on disk and every file it declares unwritten,
    which is the half-scaffolded project `init` says out loud it exists to prevent."""
    (tmp_path / "docs").write_text("not a directory\n", encoding="utf-8")
    with pytest.raises(BlockedParent) as caught:
        init(tmp_path)
    # The `docs` handed in is all that survives: the config is what made the old state look
    # configured, and it is the one file whose absence says nothing happened.
    assert written(tmp_path) == {"docs"}
    # Per file and per blocker, because they are different paths and the second is the one to
    # act on — deleting the roadmap they were never given would be the wrong move.
    assert [blocker.name for _, blocker in caught.value.blocked] == ["docs"] * 3
    assert "blocked by docs" in str(caught.value)


def test_the_blocker_is_the_ancestor_and_not_only_the_parent(tmp_path: Path) -> None:
    # The whole chain, because `mkdir(parents=True)` is what would have walked it: a nested
    # target is stopped just as dead by a `docs` two levels up.
    (tmp_path / "docs").write_text("not a directory\n", encoding="utf-8")
    assert blocking(tmp_path / "docs" / "deep" / "ROADMAP.md") == tmp_path / "docs"
    assert blocking(tmp_path / "elsewhere" / "ROADMAP.md") is None


def test_a_block_that_names_one_and_then_more_is_refused(tmp_path: Path) -> None:
    """RK390: the check read the first heading and returned, so `A\\nB` was a block by that
    reading — and the scaffold wrote the `B` out as prose under a heading that did parse."""
    with pytest.raises(UnreadableBlock) as caught:
        init(tmp_path, blocks=("A\nB",))
    assert written(tmp_path) == set()
    # The message says which of the two problems it is, so a caller is not sent at the other
    # (RK370): this value *does* name a block, and that is the confusing part of it.
    assert caught.value.beyond and "and then more" in str(caught.value)


def test_one_label_given_twice_is_refused_and_not_folded(tmp_path: Path) -> None:
    # The check of the set, which per-value validation cannot make. Refused rather than folded,
    # which §RK390 left open: folding makes this and `blocks=("A",)` produce identical files,
    # so the author never learns the command was wrong.
    with pytest.raises(RepeatedBlock):
        init(tmp_path, blocks=("A", "A"))
    assert written(tmp_path) == set()


def test_one_label_spelled_two_ways_is_still_one_label(tmp_path: Path) -> None:
    # Read off the labels and never the values: `A` and `A — The model` are one block written
    # twice, and it is the heading the label lands in that a verb has to find exactly once.
    with pytest.raises(RepeatedBlock) as caught:
        init(tmp_path, blocks=("A", "A — The model"))
    assert caught.value.label == "A"
    assert written(tmp_path) == set()


def test_a_prefix_the_format_cannot_carry_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        init(tmp_path, prefix="rk-1")
    assert written(tmp_path) == set()


# -- adopt measures and writes nothing ---------------------------------------


def test_a_conforming_file_costs_nothing(tmp_path: Path) -> None:
    config = scaffolded(tmp_path)
    (tmp_path / "docs" / "ROADMAP.md").write_text(CONFORMING, encoding="utf-8")
    estimate = adopt(config, tmp_path / "docs" / "ROADMAP.md")
    assert (estimate.parsed, estimate.conforming, estimate.changing) == (2, 2, 0)
    assert estimate.inferred is False
    assert estimate.non_canonical == 0


def test_the_prefix_is_inferred_only_when_nothing_declares_one(tmp_path: Path) -> None:
    """And it is labelled, because a count under a guessed prefix is a different count."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(FOREIGN, encoding="utf-8")
    guessed = adopt(Config.default(tmp_path), target)
    assert (guessed.prefix, guessed.inferred) == ("SH", True)
    assert ("SH", 2) in guessed.prefixes

    declared = adopt(Config.default(tmp_path), target, prefix="RK")
    assert (declared.prefix, declared.inferred) == ("RK", False)
    assert dict(declared.codes)["id.format"] == 2


def test_a_prefix_nothing_declared_and_nothing_produced_is_neither_of_those(tmp_path: Path) -> None:
    """RK485. `inferred` was `declared is None`, so a file where *no id parsed at all* fell
    through to the schema default and reported it as a reading.

    Measured on an ungoverned copy of Shio's docs: the roadmap infers `SH` correctly, and the
    changelog — whose every id is also `SH`, in a shape no grammar here reads — answered
    *prefix RK (inferred from the ids)*. A one-line file with no id said the same.

    Three states, and the third is the one worth saying loudest: the counts under it were
    taken against a prefix the file never mentions, which is the reading `adopt`'s own
    docstring calls useless."""
    target = tmp_path / "NOTHING.md"
    target.write_text("# Nothing here\n", encoding="utf-8")

    estimate = adopt(Config.default(tmp_path), target)

    assert estimate.prefix == "RK"
    assert estimate.inferred is False and estimate.defaulted is True
    # And the two that were already right stay right: read off the ids, and declared.
    other = tmp_path / "ROADMAP.md"
    other.write_text(FOREIGN, encoding="utf-8")
    read = adopt(Config.default(tmp_path), other)
    assert (read.inferred, read.defaulted) == (True, False)
    told = adopt(Config.default(tmp_path), other, prefix="RK")
    assert (told.inferred, told.defaulted) == (False, False)


def test_the_line_and_the_payload_agree_about_which_of_the_three_it_was(tmp_path, capsys) -> None:
    """The `--json` half had the same two-words-for-three: a consumer meeting `inferred:
    false` on a defaulted prefix reads it as *declared*, which is the state it is furthest
    from."""
    target = tmp_path / "NOTHING.md"
    target.write_text("# Nothing here\n", encoding="utf-8")

    assert main(["-C", str(tmp_path), "adopt", str(target)]) == EXIT_OK
    said = capsys.readouterr().out
    assert "inferred from the ids" not in said
    assert "no id here was read" in said

    assert main(["-C", str(tmp_path), "adopt", str(target), "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["inferred"] is False and payload["defaulted"] is True


def test_a_configured_project_never_guesses(tmp_path: Path) -> None:
    config = scaffolded(tmp_path)
    target = tmp_path / "OTHER.md"
    target.write_text(FOREIGN, encoding="utf-8")
    estimate = adopt(config, target)
    assert (estimate.prefix, estimate.inferred) == ("RK", False)


def test_an_undeclared_marker_is_named_as_the_markers_delta(tmp_path: Path) -> None:
    target = tmp_path / "ROADMAP.md"
    target.write_text(FOREIGN, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target)
    assert estimate.undeclared == (("✨", 1),)
    # The line is unread rather than invalid, so it counts as changing and not as parsed.
    assert estimate.parsed == 2
    assert estimate.changing == 1
    assert [count for _, count in estimate.rejects] == [1]


def test_a_checkbox_backlog_is_counted_and_never_offered_as_a_marker(tmp_path: Path) -> None:
    """cursarei's shape (RK103): 0 entries, and until now 0 rejects — so nothing to change.

    The `[markers]` delta is where this could go wrong twice: the token is `[`, which
    carries no alphanumeric, so an estimate that read the slot alone would tell the adopting
    project to declare a bracket.
    """
    target = tmp_path / "ROADMAP.md"
    boxes = "\n".join(f"- [ ] **C{n}** · a task in another convention" for n in (1, 2, 3))
    target.write_text(f"# Roadmap\n\n## Block A\n\n{boxes}\n", encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, prefix="C")
    assert estimate.parsed == 0
    assert [count for _, count in estimate.rejects] == [3]
    assert estimate.changing == 3  # the answer an empty file may not share
    assert estimate.undeclared == ()


#: Dumont's shape and Turing's in one file (RK110): two widths of leading zero, and the one
#: lowercase letter a split kept. Under a default config all four are `id.format`.
SHAPED = (
    "# Roadmap\n\n## Block A\n\n"
    "- 📋 **D01** (deps: —) **A symptom** — Because of a reason. → §D01\n"
    "- 📋 **D02** (deps: —) **A symptom** — Because of a reason. → §D02\n"
    "- 📋 **D003** (deps: —) **A symptom** — Because of a reason. → §D003\n"
    "- 📋 **D4b** (deps: —) **A symptom** — Because of a reason. → §D4b\n"
)


def test_the_id_findings_are_named_as_the_ids_delta(tmp_path: Path) -> None:
    """Four `id.format` findings are two unwritten keys, and the estimate says which (RK110).

    Per width and not as one padding fact: a corpus that pads to two *and* to three is one
    whose width nobody has chosen, and a single line would hide that.
    """
    target = tmp_path / "ROADMAP.md"
    target.write_text(SHAPED, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, prefix="D")
    assert dict(estimate.codes)["id.format"] == 4
    assert [(s.declaration, s.count) for s in estimate.id_shape] == [
        ("pad = 2", 2),
        ("pad = 3", 1),
        ("suffix = true", 1),
    ]


def test_a_declared_id_shape_is_not_reported_as_a_delta(tmp_path: Path) -> None:
    """The same rule the prefix line has: only what the schema does not already hold."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(SHAPED, encoding="utf-8")
    config = Config.default(tmp_path)
    declared = replace(config, schema=replace(config.schema, id_pad=2, id_suffix=True))
    estimate = adopt(declared, target, prefix="D")
    assert [s.declaration for s in estimate.id_shape] == ["pad = 3"]  # the one still unread


def test_the_ids_delta_names_the_key_and_never_proposes_it(tmp_path: Path, capsys) -> None:
    """Measuring `pad = 2` against nine findings took a throwaway script; now it is a line."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(SHAPED, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target), "--prefix", "D"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "2 id(s) carry a leading zero, refused here: [ids] pad = 2" in out
    assert "1 id(s) end in a lowercase letter, refused here: [ids] suffix = true" in out
    # The condition is the whole discipline: what the ids spell, never what to declare (L4).
    assert "if that width is this backlog's spelling" in out

    assert main(["-C", str(tmp_path), "adopt", str(target), "--prefix", "D", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["id_shape"][0] == {
        "key": "pad",
        "value": "2",
        "count": 2,
        "declaration": "pad = 2",
    }


def test_a_length_is_reported_as_a_distance_and_not_a_verdict(tmp_path: Path) -> None:
    """`longest` beside `over`: how many lines change, and whether the limit is close."""
    target = tmp_path / "ROADMAP.md"
    why = "Because of a reason that runs on. " * 12
    target.write_text(
        f"# Roadmap\n\n## Block A\n\n- 📋 **RK1** (deps: —) **A symptom** — {why}\n",
        encoding="utf-8",
    )
    estimate = adopt(Config.default(tmp_path), target)
    measures = {m.field: m for m in estimate.measures}
    assert measures["symptom"].over == 0
    assert measures["why"].over == 1
    assert measures["why"].longest > measures["why"].limit
    assert measures["line"].limit == 320


#: Claude Code Tray's shape (RK139): a lead over the limit, a reason far over it, and a bullet
#: with no bold head at all — the three findings that arrived after that adoption was decided.
SCOPED = (
    "# Roadmap\n\n## Block A\n\n"
    "- 📋 **RK1** (deps: —) **A symptom** — Because of a reason. → §RK1\n\n"
    "## Non-goals\n\n"
    "- **No web UI and no server.** Files and a CLI.\n"
    f"- **{'No ' + 'very ' * 30}long a lead** Because of a reason.\n"
    f"- **No second one** {'Because of a reason that runs on. ' * 12}\n"
    "- A bullet with no bold head at all, which is a shape nothing can address.\n"
)


def test_the_non_goals_are_measured_beside_the_task_lines(tmp_path: Path) -> None:
    """The half of the roadmap the estimate did not read (RK139)."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(SCOPED, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target)
    scoped = estimate.non_goals
    assert (scoped.parsed, scoped.unparsed, scoped.over) == (3, 1, 2)
    measures = {m.field: m for m in scoped.measures}
    assert measures["lead"].over == 1 and measures["lead"].longest > measures["lead"].limit
    assert measures["why"].over == 1
    # Measured at the defaults, and said so: the number an adopter needs is what the rule
    # would cost, and until this the only way to get it was to declare the table and lint.
    assert scoped.governed is False


def test_a_rule_nobody_adopted_is_reported_beside_the_headline_and_not_inside_it(
    tmp_path: Path,
) -> None:
    """`changing` is what the gate would fail on, and the gate reports nothing where
    `[non_goals]` is undeclared — so opting in is what moves those bullets into the total."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(SCOPED, encoding="utf-8")
    ungoverned = adopt(Config.default(tmp_path), target)
    assert ungoverned.changing == 0  # one task line, conforming
    assert ungoverned.non_goals.changing == 3

    config = Config.default(tmp_path)
    governed = adopt(replace(config, non_goals=Scope()), target)
    assert governed.non_goals.governed is True
    assert governed.changing == 3


def test_a_ledger_has_no_such_list_to_measure(tmp_path: Path) -> None:
    """A heading matched there would be an answer about the wrong file."""
    target = tmp_path / "CHANGELOG.md"
    target.write_text(
        "# Shipped\n\n## Block A\n\n- ✅ **RK1** **A symptom** — because it was done.\n",
        encoding="utf-8",
    )
    assert adopt(Config.default(tmp_path), target, ledger=True).non_goals is None


def test_the_non_goals_report_names_the_two_limits(tmp_path: Path, capsys) -> None:
    target = tmp_path / "ROADMAP.md"
    target.write_text(SCOPED, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target)]) == EXIT_OK
    out = capsys.readouterr().out
    assert "non-goals 3 bullet(s), 1 unread, 2 over" in out
    assert "[non_goals] not governed, so measured at the defaults" in out
    assert "lead     longest" in out

    assert main(["-C", str(tmp_path), "adopt", str(target), "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["non_goals"]["changing"] == 3
    assert payload["non_goals"]["measures"][0]["field"] == "lead"


def test_the_ledger_is_measured_as_the_ledger(tmp_path: Path) -> None:
    """✅ with no deps is a defect in a roadmap and the format of a changelog (L6)."""
    target = tmp_path / "CHANGELOG.md"
    target.write_text(
        "# Shipped\n\n## Block A\n\n- ✅ **RK1** **A symptom** — because it was done.\n",
        encoding="utf-8",
    )
    assert adopt(Config.default(tmp_path), target, ledger=True).conforming == 1
    assert adopt(Config.default(tmp_path), target).conforming == 0


def test_the_ref_scheme_is_an_override_and_never_a_guess(tmp_path: Path) -> None:
    """Two real questions: adopt the tool, or adopt it and renumber the outline (RK27)."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(
        "# Roadmap\n\n## Block A\n\n"
        "- 📋 **RK1** (deps: —) **A symptom** — Because of a reason. → §2.3\n",
        encoding="utf-8",
    )
    assert adopt(Config.default(tmp_path), target).conforming == 0
    assert adopt(Config.default(tmp_path), target, ref_scheme="outline").conforming == 1


TABULAR = """# Roadmap

Legend, and not a backlog — it is above every block heading:

| Marker | Means |
| --- | --- |
| 📋 | designed |

## Block A — The model

| ID | Status | Task | Depends on |
| --- | --- | --- | --- |
| T1 | 📋 | A first symptom | — |
| T2 | 📋 | A second symptom | T1 |

Prose that uses a pipe | like this is not a row.

## Block B — Authoring

| ID | Status | Task | Depends on |
|---|---|---|---|
| T3 | 💭 | A third symptom | — |
"""


def test_a_table_is_not_an_empty_file(tmp_path: Path) -> None:
    """The zero RK98 is about: 0 parsed and 0 rejected is what a file with no tasks gets."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(TABULAR, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, prefix="T")
    assert (estimate.parsed, estimate.rejects) == (0, ())
    # Three task rows: the two under Block A and the one under Block B. Neither header row
    # nor rule row is one, the legend is above every block, and the prose is prose.
    assert estimate.tabular == 3
    assert estimate.changing == 3


def test_counting_the_rows_is_not_reading_them(tmp_path: Path) -> None:
    """Deliberately not a table parser (RK98): the shape is measured, the cells are not."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(TABULAR, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, prefix="T")
    # No id was read out of a cell, so nothing about the ids is claimed — `prefixes` is what
    # the *entries* spell, and a table contributes none.
    assert estimate.prefixes == ()
    assert estimate.conforming == 0
    assert all(measure.longest == 0 for measure in estimate.measures)


#: The shape almost every unadopted roadmap is actually in (RK279), with the frame around it:
#: a preamble that is bullets, a non-goals list that is bullets, and a nested detail bullet.
#: Only the four under a block heading are where a task would be.
LISTED = """# Roadmap

- a preamble bullet, above every heading

## Block A — The model

- [ ] make the thing faster
- [x] fix login
- an ordinary bullet
  - a nested detail of the one above

## Block B — Authoring

1. a numbered task
2) and its sibling

Prose under a block is not a bullet.

## Non-goals

- **No web UI.** Files and a CLI.
"""


def test_a_list_is_not_an_empty_file_either(tmp_path: Path) -> None:
    """RK279: RK98's zero, in the shape that reaches it most often — a Markdown checklist."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(LISTED, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, prefix="T")
    assert (estimate.parsed, estimate.rejects, estimate.tabular) == (0, (), 0)
    # Five: three under Block A and two under Block B. Not the preamble bullet, not the
    # non-goal, not the nested detail, not the prose — the frame is not the work.
    assert estimate.listed == 5
    assert estimate.changing == 5


def test_the_frame_is_not_priced_as_the_backlog(tmp_path: Path) -> None:
    """The reason this was not done with the tables: a roadmap's bullets are not all tasks."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(LISTED, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, prefix="T")
    # The non-goals are counted by their own half, as they were before, and once only.
    assert estimate.non_goals is not None and estimate.non_goals.parsed == 1
    assert estimate.listed + estimate.non_goals.parsed < len(LISTED.splitlines())


def test_counting_the_bullets_is_not_reading_them(tmp_path: Path) -> None:
    """The line `Row` draws, drawn the same way: the shape is measured, the text is not."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(LISTED, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, prefix="T")
    assert estimate.prefixes == () and estimate.conforming == 0
    assert all(measure.longest == 0 for measure in estimate.measures)


#: A rationale file anchored the way Shio's is: `0.1`, no sigil, because `anchor_text` writes
#: one only under the id scheme. Under `id` every one of these reads as carrying no anchor.
OUTLINE_PROSE = """# Design notes

## 0 — Why this exists

### 0.1 The goals, restated

Prose under the first anchor, enough of it to be a section.

### 0.2 What this is today

More prose, under the second.
"""


def test_a_prose_file_can_say_which_scheme_its_headings_are_in(tmp_path: Path) -> None:
    # RK288: `_schemes` reads pointers on task lines and a rationale file has none, so the one
    # sentence that would say "read this the other way" was absent on the command where the
    # misreading is total — Shio read 0 conform under the default and 93 under `outline`.
    target = tmp_path / "DESIGN.md"
    target.write_text(OUTLINE_PROSE, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, sections=True)
    assert dict(estimate.schemes)["outline"] >= 2
    assert estimate.parsed == 0, "under `id` these anchors are invisible, which is the defect"


def test_the_scheme_line_fires_where_the_reading_is_the_minority(tmp_path: Path, capsys) -> None:
    target = tmp_path / "DESIGN.md"
    target.write_text(OUTLINE_PROSE, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target), "--sections"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "heading(s) anchored outline" in printed
    assert "--ref-scheme outline" in printed


def test_a_file_that_mixes_anchors_is_not_told_to_switch(governed: Path, capsys) -> None:
    """This repository's own rationale file anchors its preamble `§0.1` and its task sections
    `§RK200`, so a bare "some headings are outline-shaped" fired on a file that conforms."""
    config = Config.discover(governed)
    estimate = adopt(config, config.path("improvements"), sections=True)
    assert estimate.conforming == estimate.parsed and estimate.changing == 0
    # Both shapes are present and the ratio is not what decides (RK305): the id-anchored
    # sections are this backlog's open designs and are deleted at every ship, so a majority
    # is a fact about how much work is left rather than about the file's shape.
    assert dict(estimate.schemes).get("outline")
    assert main(
        ["-C", str(governed), "adopt", str(config.path("improvements")), "--sections"]
    ) == EXIT_OK
    assert "also" not in capsys.readouterr().out


#: The same file's shape with the ratio the other way up: every heading carries the sigil, so
#: the declared `id` scheme reads all four, and three of them are outline-shaped (RK305).
MIXED_PROSE = """# Design notes

## §0.1 The goals, restated

Prose under the first anchor, enough of it to be a section.

## §0.2 What this is today

More prose, under the second.

## §0.3 What it is not

More prose, under the third.

## §T9 One open design

The only id-anchored section, and the kind a ship deletes.
"""


def test_a_conforming_file_is_not_told_to_switch_by_a_majority(tmp_path: Path, capsys) -> None:
    """RK305: what a ship erodes is the ratio, so the ratio cannot be what decides. Every
    heading here is read by the declared scheme and outline-shaped ones outnumber id-shaped
    ones three to one — the state this repository's rationale file reaches by delivering."""
    target = tmp_path / "DESIGN.md"
    target.write_text(MIXED_PROSE, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, sections=True)
    counts = dict(estimate.schemes)
    assert counts["outline"] > counts["id"], "the majority RK288 would have fired on"
    assert estimate.listed == 0, "and nothing is unread, which is what makes it a false alarm"
    assert main(["-C", str(tmp_path), "adopt", str(target), "--sections"]) == EXIT_OK
    assert "--ref-scheme" not in capsys.readouterr().out


def test_unanchored_still_asks_the_declared_scheme(tmp_path: Path) -> None:
    """What must not happen (RK288): a count that quietly repaired itself would leave the
    reader the right number under a reading the report still claims is right."""
    target = tmp_path / "DESIGN.md"
    target.write_text(OUTLINE_PROSE, encoding="utf-8")
    schema = Config.default(tmp_path).schema_for("improvements")
    document = Document.load(target, schema)
    assert len(unanchored(document)) == 2, "read under `id`, these carry no anchor it knows"


def test_a_fenced_list_is_an_example(tmp_path: Path) -> None:
    """A rationale file quotes the shape it argues about, and a fence is what says so."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(
        "# Roadmap\n\n## Block A\n\n```\n- [ ] quoted, not counted\n```\n", encoding="utf-8"
    )
    assert adopt(Config.default(tmp_path), target, prefix="T").listed == 0


def test_a_conforming_backlog_lists_nothing(governed: Path) -> None:
    """The count has to be zero on a file already in the format, or every adopted project
    would read as having work it does not have — this repo's own docs are the fixture."""
    config = Config.discover(governed)
    estimate = adopt(config, config.path("roadmap"))
    assert estimate.listed == 0 and estimate.changing == 0


#: A rationale file as somebody who never met this tool writes one (RK281): no sigil anywhere,
#: a title, a container heading whose children carry the prose, and one section that is prose.
UNSIGILLED = """# Design notes

## Storage

### The store is the repository

Markdown, greppable, no database. The argument is that a backlog living in a service
is one an agent cannot grep.

### Round-trip or refuse

Parse, render, compare bytes.

## Open questions

Whether the width should be configurable at all.
"""


def test_a_rationale_file_without_the_sigil_is_not_an_empty_one(tmp_path: Path) -> None:
    """RK281: the sigil is this tool's convention, so `adopt --sections` used to read a file
    correctly exactly when it had already adopted the format — the one case needing no
    estimate."""
    target = tmp_path / "DESIGN.md"
    target.write_text(UNSIGILLED, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, sections=True)
    assert estimate.parsed == 0  # nothing is anchored, which is true and is not the answer
    # Three: the two `###` with prose, and `## Open questions` which carries prose of its own.
    # Not `# Design notes`, which is the document, and not `## Storage`, which is a container.
    assert estimate.listed == 3
    assert estimate.changing == 3


def test_the_frame_of_a_rationale_file_is_not_a_section(tmp_path: Path) -> None:
    """The two exclusions, asserted apart from the count so a change to either is visible."""
    target = tmp_path / "DESIGN.md"
    target.write_text(UNSIGILLED, encoding="utf-8")
    document = Document.load(target, Config.default(tmp_path).schema_for("improvements"))
    titles = [h.text for h in unanchored(document)]
    assert "Design notes" not in titles  # level 1 is the document
    assert "Storage" not in titles  # a container: its children hold the prose
    assert titles == ["The store is the repository", "Round-trip or refuse", "Open questions"]


def test_an_unanchored_section_is_measured_like_an_anchored_one(tmp_path: Path) -> None:
    """The word count is what an adopter is being asked to declare, and a span has one
    whether or not this tool has an address for it."""
    target = tmp_path / "DESIGN.md"
    target.write_text(UNSIGILLED, encoding="utf-8")
    tight = replace(Config.default(tmp_path).schema_for("improvements"), section_max=5)
    estimate = adopt(
        replace(Config.default(tmp_path), schema=tight), target, sections=True
    )
    measure = next(m for m in estimate.measures if m.field == "section")
    assert measure.longest > 5 and measure.over >= 1


def test_an_adopted_rationale_file_has_nothing_loose(governed: Path) -> None:
    """This repo's own file is the fixture: every section is anchored, so the count is zero
    and an adopted project cannot read as having work it does not have."""
    config = Config.discover(governed)
    estimate = adopt(config, config.path("improvements"), sections=True)
    assert estimate.listed == 0 and estimate.changing == 0


#: A backlog that points by outline, as Shio's does: the ids are its own, the pointers are
#: `<x.y>` anchors chosen by hand. Under the `id` scheme every line is `ref.mismatch`.
OUTLINED = """# Roadmap

## Block A — The model

- 📋 **SH1** (deps: —) **A first symptom** — Because of a reason. → §XVI.1
- 📋 **SH2** (deps: —) **A second symptom** — Because of another. → §XVI.2
"""


def test_the_scheme_the_pointers_spell_is_named_like_the_prefix_is(tmp_path: Path) -> None:
    # RK285: Shio read `0 conform, 65 would change` under the default and `63 conform, 2 would
    # change` under `--ref-scheme outline`, with `ref.mismatch` on every line as the only
    # signal — while the prefix half of the same misreading already named its flag.
    target = tmp_path / "ROADMAP.md"
    target.write_text(OUTLINED, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, prefix="SH")
    assert estimate.schemes == (("outline", 2),)
    assert estimate.ref_scheme == "id" and dict(estimate.codes)["ref.mismatch"] == 2


def test_the_scheme_that_is_already_being_read_under_is_not_advice(tmp_path: Path) -> None:
    """A measurement and not a choice: read under `outline`, the same pointers are the answer
    rather than a suggestion, and the file conforms."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(OUTLINED, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, prefix="SH", ref_scheme="outline")
    assert estimate.schemes == (("outline", 2),) and estimate.ref_scheme == "outline"
    assert estimate.conforming == 2 and estimate.changing == 0


#: A backlog that points by id on two lines and by hand on the third — the minority RK288's
#: majority silenced, and the two lines the declared scheme genuinely cannot read (RK305).
MOSTLY_DERIVED = """# Roadmap

## Block A — The model

- 📋 **SH1** (deps: —) **A first symptom** — Because of a reason. → §SH1
- 📋 **SH2** (deps: —) **A second symptom** — Because of another. → §SH2
- 📋 **SH3** (deps: —) **A third symptom** — Because of a third. → §XVI.3
"""


def test_a_minority_of_unread_pointers_is_still_reported(tmp_path: Path, capsys) -> None:
    """RK305: what decides is whether the declared scheme left an address unread, and one
    hand-chosen pointer among two derived ones is unread however small a share it is."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(MOSTLY_DERIVED, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, prefix="SH")
    assert dict(estimate.schemes)["id"] > dict(estimate.schemes)["outline"]
    assert main(["-C", str(tmp_path), "adopt", str(target), "--prefix", "SH"]) == EXIT_OK
    assert "1 pointer(s) spell outline" in capsys.readouterr().out


def test_the_scheme_half_is_named_where_the_prefix_was_inferred(tmp_path: Path, capsys) -> None:
    """Nothing declares a prefix here, so `adopt` infers SH off the ids and only the scheme is
    misread — the half that had no sentence before."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(OUTLINED, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target)]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "--ref-scheme outline if that is how" in printed
    assert "--ref-scheme outline changes it" in printed


def test_the_report_names_both_halves_of_one_misreading(tmp_path: Path, capsys) -> None:
    """Shio's own shape: a declared prefix that is not the file's, *and* the other scheme. Both
    flags, and the round-trip line saying which reading produced its number."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(OUTLINED, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target), "--prefix", "RK"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "--prefix SH if it is a track" in printed
    assert "--ref-scheme outline if that is how" in printed
    assert "--prefix SH, --ref-scheme outline changes it" in printed


def test_the_payload_carries_the_door_the_printed_report_names(tmp_path: Path, capsys) -> None:
    """RK1147: the same run, both surfaces, and the flag on each.

    The report has named `--ref-scheme outline` since RK285 and the payload published
    `{"scheme": "outline", "count": 20}` beside `line.non-canonical`, so what an agent got was
    two counts and the inference between them — the asymmetry `lint` has not had since RK15.
    Asserted against the *rendered* report and not against the fields, because reading the
    object is what filed this task against a report that already said the right thing.
    """
    target = tmp_path / "ROADMAP.md"
    target.write_text(OUTLINED, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target), "--prefix", "RK"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert main(["-C", str(tmp_path), "adopt", str(target), "--prefix", "RK", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    doors = {
        tuple(row["doors"][0]["argv"][-2:])
        for key in ("prefixes", "schemes")
        for row in payload[key]
        if "doors" in row
    }
    assert doors == {("--prefix", "SH"), ("--ref-scheme", "outline")}
    # Every flag the text names is a door, and every door is a flag the text names: one list
    # decides both (`_readings`), and the point of the closure is that it stays one.
    for flag, value in doors:
        assert f"{flag} {value}" in printed
        (row,) = [
            r
            for r in payload["prefixes" if flag == "--prefix" else "schemes"]
            if r.get(flag.strip("-").replace("ref-scheme", "scheme")) == value
        ]
        # The door is a read, and says so — `adopt` writes nothing (RK18), which the parser
        # now declares rather than a test comment claiming it.
        assert row["doors"][0]["writes"] is False and row["doors"][0]["complete"] is True
    # And a row the report says nothing about carries no door: a family already covered is not
    # an unread reading, so the key is absent rather than null.
    assert main(["-C", str(tmp_path), "adopt", str(target), "--prefix", "SH", "--json"]) == EXIT_OK
    covered = json.loads(capsys.readouterr().out)
    assert [row for row in covered["prefixes"] if "doors" in row] == []


def test_a_door_carries_the_flag_that_decided_the_measurement(tmp_path: Path, capsys) -> None:
    """A ledger read as a backlog is a different measurement of the same bytes (RK76), so a door
    that dropped `--ledger` would answer about a reading nobody asked for."""
    target = tmp_path / "CHANGELOG.md"
    target.write_text(UNSLOTTED, encoding="utf-8")
    # Declared the way a ledger of these lines has to be (RK286), so the entries parse at all:
    # under the default slots every line is a reject and the run has no reading to be unread.
    ledgered(tmp_path, marker=False, symptom=False)
    argv = ["-C", str(tmp_path), "adopt", str(target), "--ledger", "--prefix", "RK", "--json"]
    assert main(argv) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["ledger"] is True
    (row,) = [r for r in payload["prefixes"] if "doors" in r]
    assert "--ledger" in row["doors"][0]["argv"]


def test_a_reading_nothing_disputes_qualifies_nothing(tmp_path: Path, capsys) -> None:
    """The qualifier is a conjunction and not a hedge: read correctly, there is no `also` line
    and the round-trip sentence — if it fires at all — names no alternative."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(OUTLINED, encoding="utf-8")
    argv = ["-C", str(tmp_path), "adopt", str(target), "--prefix", "SH", "--ref-scheme", "outline"]
    assert main(argv) == EXIT_OK
    printed = capsys.readouterr().out
    assert "also" not in printed and "changes it" not in printed


#: A ledger in Turing's shape: every entry shipped, so no marker, and no `**symptom**` slot
#: either — plus one line that carries a marker and still has no symptom.
UNSLOTTED = """# Shipped Ledger

## Block A — The model

- **T1** — because of the first reason.
- **T2** — because of the second reason.
- ✅ **T3** — because it kept its marker.
"""


def ledgered(tmp_path: Path, **ledger) -> Config:
    """A project whose changelog is the file under test, with `[ledger]` as given."""
    body = "".join(f"{key} = {str(value).lower()}\n" for key, value in ledger.items())
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "T"\n[files]\nchangelog = "docs/CHANGELOG.md"\n'
        + (f"[ledger]\n{body}" if body else ""),
        encoding="utf-8",
    )
    return Config.discover(tmp_path)


def test_the_reason_names_every_slot_the_line_needs(tmp_path: Path) -> None:
    # RK286: Turing was told `marker = false` alone, and declaring exactly that left `827
    # would change` where it was, because its lines carry no symptom slot either.
    target = tmp_path / "CHANGELOG.md"
    target.write_text(UNSLOTTED, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, prefix="T", ledger=True)
    reasons = " ".join(reason for reason, _ in estimate.rejects)
    assert "marker = false, symptom = false" in reasons


def test_the_fewest_slots_that_read_the_line_are_the_ones_named(tmp_path: Path) -> None:
    """A line that kept its marker wants one declaration, not two — the smallest that works."""
    # A ledger line in full shape needs nothing declared.
    assert ledger_slots("- ✅ **T1** **A symptom** — Because of a reason.") == ()
    # No marker, symptom still delimited: one slot.
    assert ledger_slots("- **T1** **A symptom** — Because of a reason.") == ("marker = false",)
    # Marker kept, no symptom slot: the other one, and only it.
    assert ledger_slots("- ✅ **T1** — Because of a reason.") == ("symptom = false",)
    # Neither, which is Turing's shape.
    assert ledger_slots("- **T1** — Because.") == ("marker = false", "symptom = false")
    # A line no declaration reaches is not evidence about one.
    assert ledger_slots("- nonsense") == ()


def test_the_count_is_what_declaring_it_actually_recovers(tmp_path: Path) -> None:
    """The number RK18 says is only worth having *before* the commitment. Asserted against the
    truth rather than against itself: what the report promises is what declaring it reads."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "CHANGELOG.md").write_text(UNSLOTTED, encoding="utf-8")
    target = docs / "CHANGELOG.md"

    before = adopt(ledgered(tmp_path), target, ledger=True)
    promised = {declaration: count for declaration, count in before.ledger_shape}
    assert before.parsed == 0 and promised

    # Each row on its own, never their sum: the rows are alternatives. `- ✅ **T3** — why` is
    # read by `symptom = false` and stopped by `marker = false`, because with no marker slot
    # the ✅ sits where the id goes — so a total would promise what no one config delivers.
    for declaration, count in promised.items():
        slots = {key.strip(): False for key in declaration.split(",")}
        under = adopt(ledgered(tmp_path, **{k.split(" =")[0]: v for k, v in slots.items()}),
                      target, ledger=True)
        assert under.parsed == count, declaration
    assert sum(promised.values()) > max(promised.values()), "the rows really do differ"


def test_a_roadmap_has_no_ledger_slots_to_report(tmp_path: Path) -> None:
    """`[ledger]` is a fact about the ledger, so a backlog is owed no line about it."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(CONFORMING, encoding="utf-8")
    assert adopt(Config.default(tmp_path), target).ledger_shape == ()


#: Where the payload deliberately names a field differently from the dataclass (RK289).
#: Declared rather than derived: the boundary is where a field gets a name a reader outside
#: this package can use — `path` is *which file*, and `file` says so — and a payload generated
#: from the dataclass would be correct with no place left to say that.
#: `surface` travels as `serves`, and as an object rather than an integer: the cadence has to
#: reach a client with the number, or it is added to a per-turn figure (RK1100).
ESTIMATE_RENAMES = {"path": "file", "surface": "serves"}


def test_the_payload_carries_every_field_of_the_estimate(tmp_path: Path, capsys) -> None:
    # RK289, and RK276 is why it exists rather than being trusted: a field was added to
    # `Registration`, reached one surface, and was absent from the payload — under a comment
    # asserting the two said the same. Three fields reached `Estimate` in one week, each
    # carried across by hand, so this is the fourth one failing here instead of going quiet.
    target = tmp_path / "ROADMAP.md"
    target.write_text(CONFORMING, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target), "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    named = {ESTIMATE_RENAMES.get(field.name, field.name) for field in fields(Estimate)}
    # Containment and not equality: the payload also carries derived answers — `changing` is a
    # property, and it is the number the whole report exists to give. What must not happen is a
    # *field* going missing, which is the direction RK276 measured.
    assert named <= set(payload)


#: One id on two lines — a defect that needs *two* lines to see, and is decidable from the one
#: file both the estimate and the gate were handed.
DOUBLED = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- 📋 **RK1** (deps: —) **A second line with one id** — Because of another. → §RK1
"""


def test_the_estimate_sees_what_needs_more_than_one_line(tmp_path: Path) -> None:
    # RK290: `adopt` validated each task on its own — the per-line half of the rules — so a
    # duplicated id read `2 conform, 0 would change` while `lint` over that same file refused
    # it. The estimate was not slightly low on that class; it could not see it.
    target = tmp_path / "ROADMAP.md"
    target.write_text(DOUBLED, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target)
    assert dict(estimate.codes)["id.duplicate"] == 1
    assert estimate.conforming == 1 and estimate.changing == 1


def test_the_estimate_and_the_gate_agree_over_one_file(tmp_path: Path, capsys) -> None:
    """The claim RK18 rests on, asserted as an equality rather than described: what the
    estimate reports and what the gate reports about the same file are the same codes."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "ROADMAP.md").write_text(DOUBLED, encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "docs/ROADMAP.md"\n', encoding="utf-8"
    )
    config = Config.discover(tmp_path)
    estimated = dict(adopt(config, docs / "ROADMAP.md").codes)

    gated: dict[str, int] = {}
    for finding in lint(config).findings:
        gated[finding.code] = gated.get(finding.code, 0) + 1
    # Only the half one file decides: the gate also resolves deps and pointers across the
    # files a project declares, and an estimate is handed one file that may be declared by
    # nothing (RK290).
    assert estimated == {code: n for code, n in gated.items() if code == "id.duplicate"}


def test_a_conforming_file_gains_no_finding_from_the_wider_pass(governed: Path) -> None:
    """The direction that would matter most if it broke: this repository's own backlog, and
    two live corpora, must not acquire work because the estimate started looking wider."""
    config = Config.discover(governed)
    estimate = adopt(config, config.path("roadmap"))
    assert estimate.changing == 0 and estimate.conforming == estimate.parsed


def test_the_files_it_did_not_open_are_named(tmp_path: Path) -> None:
    # RK291: RK290 made the estimate and the gate agree on everything one file decides, so the
    # checks that resolve *across* files became the whole difference — and no line said so.
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "ROADMAP.md").write_text(CONFORMING, encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "docs/ROADMAP.md"\n'
        'changelog = "docs/CHANGELOG.md"\nimprovements = "docs/IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    config = Config.discover(tmp_path)
    estimate = adopt(config, docs / "ROADMAP.md")
    # The target is excluded by resolved path, and the siblings are named as the project
    # spells them — a filename is what an adopter can act on, unlike a finding code.
    assert estimate.unopened == ("docs/CHANGELOG.md", "docs/IMPROVEMENTS.md")


def test_the_limit_is_stated_even_where_it_did_not_bite(tmp_path: Path, capsys) -> None:
    """A limit named only when it happened to matter is one the reader cannot rely on — the
    same reason `[non_goals] not governed` prints on a file with no non-goals."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(CONFORMING, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target)]) == EXIT_OK
    printed = capsys.readouterr().out
    # Printed on a file with nothing wrong with it, which is the point.
    assert "0 would change" in printed
    assert "deps and pointers resolve across files" in printed


def test_the_sentence_holds_where_there_is_no_sibling_to_name(tmp_path: Path, capsys) -> None:
    """A project declaring one file has no changelog to hand over, and the limit is still real:
    a dep is resolved against the roadmap *and* the ledger, so one file cannot settle it."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "ROADMAP.md").write_text(CONFORMING, encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "docs/ROADMAP.md"\n', encoding="utf-8"
    )
    config = Config.discover(tmp_path)
    assert adopt(config, docs / "ROADMAP.md").unopened == ()
    assert main(["-C", str(tmp_path), "adopt", str(docs / "ROADMAP.md")]) == EXIT_OK
    assert "no other governed file not read" in capsys.readouterr().out


def test_the_estimate_never_resolves_what_it_could_not_read(tmp_path: Path) -> None:
    """The direction that must not happen (RK291): pointed at Shio's roadmap without its
    changelog, a deps pass reports 82 unresolved deps on a backlog whose deps all resolve."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(
        "# Roadmap\n\n## Block A — The model\n\n"
        "- 📋 **RK1** (deps: RK99) **A first symptom** — Because of a reason. → §RK1\n",
        encoding="utf-8",
    )
    estimate = adopt(Config.default(tmp_path), target)
    assert "deps.unknown" not in dict(estimate.codes)
    assert estimate.changing == 0, "a dep it cannot resolve is not work it may price"


def test_a_target_no_project_here_declares_names_no_siblings(tmp_path: Path, capsys) -> None:
    # RK292: adopting Turing's `docs/IMPROVEMENTS.md` from this checkout named *this* repo's
    # three files as unread, one of them same-named — so the report said it had not read the
    # file it read, and offered siblings nobody could hand over.
    foreign = tmp_path / "elsewhere" / "ROADMAP.md"
    foreign.parent.mkdir()
    foreign.write_text(CONFORMING, encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "ROADMAP.md").write_text(CONFORMING, encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "docs/ROADMAP.md"\n'
        'changelog = "docs/CHANGELOG.md"\n',
        encoding="utf-8",
    )
    config = Config.discover(tmp_path)

    outside = adopt(config, foreign)
    assert outside.declared is False and outside.unopened == ()
    inside = adopt(config, docs / "ROADMAP.md")
    assert inside.declared is True and inside.unopened == ("docs/CHANGELOG.md",)

    assert main(["-C", str(tmp_path), "adopt", str(foreign)]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "declared by no project here" in printed
    # The whole defect: this project's own files are not named as unread.
    assert "docs/CHANGELOG.md" not in printed


def test_the_limit_is_still_stated_for_a_file_no_project_owns(tmp_path: Path, capsys) -> None:
    """Narrower, never absent (RK291 holds): one file was read, and deps and pointers need
    more than one whichever project they belong to."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(CONFORMING, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target)]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "deps and pointers resolve across files" in printed


def test_a_fenced_table_is_an_example(tmp_path: Path) -> None:
    """A rationale file quotes the shape it is arguing about; a fence is what says so."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(
        "# Roadmap\n\n## Block A\n\n```\n| ID | Task |\n| --- | --- |\n| T1 | one |\n```\n",
        encoding="utf-8",
    )
    assert adopt(Config.default(tmp_path), target, prefix="T").tabular == 0


def test_the_table_row_is_named_in_the_report(tmp_path: Path, capsys) -> None:
    target = tmp_path / "ROADMAP.md"
    target.write_text(TABULAR, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target), "--prefix", "T"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "3 would change" in out
    assert "3 line(s) in a table this format does not read" in out


SENTENCE = "One two three four five six seven eight nine ten eleven twelve thirteen four."
WIDE_ROW = (
    "| A table row that nobody would ever wrap a paragraph to, and that is wider "
    "than every line of prose in this file |"
)

RATIONALE = f"""# Improvements

A preamble above every anchor, wrapped the way the rest of this file is.

## Block A — The model

### §RK1 The first design

{SENTENCE}

{WIDE_ROW}
| --- |
| one |

### §RK2 The second design

Short.
"""

#: §RK1's own prose, as `anchored` reads it: everything up to the next heading. The table
#: under it is **not** charged (RK136) — the limit budgets an argument, and a row of data is
#: not asking for an agent's attention — so the number an adopter is shown is 14 and not 45.
FIRST_BODY = RATIONALE.partition("### §RK1 The first design\n")[2].partition("### §RK2")[0]
FIRST_ARGUMENT = words(FIRST_BODY)


def test_the_other_half_of_the_corpus_is_measured(tmp_path: Path) -> None:
    """`section` and `prose` are two of the limits an adopter declares, and until RK99
    the estimate reported neither — so they were set by a script or copied from here."""
    target = tmp_path / "IMPROVEMENTS.md"
    target.write_text(RATIONALE, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, sections=True)
    assert (estimate.unit, estimate.parsed, estimate.conforming) == ("section", 2, 2)
    measures = {m.field: m for m in estimate.measures}
    assert measures["section"].limit == 250
    assert measures["section"].longest == FIRST_ARGUMENT == 14  # the longer body
    assert len(FIRST_BODY.split()) == 45  # what the table would have cost it (RK136)
    assert measures["prose"].limit == 88


def test_the_width_measured_is_the_width_that_would_be_written(tmp_path: Path) -> None:
    """A table row is the widest line in a rationale file and the tool never wraps one,
    so an adopter reading `prose` off it would declare a width nothing produces."""
    target = tmp_path / "IMPROVEMENTS.md"
    target.write_text(RATIONALE, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, sections=True)
    prose = {m.field: m for m in estimate.measures}["prose"]
    assert max(len(line) for line in RATIONALE.splitlines()) == len(WIDE_ROW) > 88
    # The widest line the tool would have written is the sentence, not the row above it.
    assert prose.longest == len(SENTENCE)


def test_a_section_over_budget_is_what_would_change(tmp_path: Path) -> None:
    target = tmp_path / "IMPROVEMENTS.md"
    body = "word " * 300
    target.write_text(f"# Improvements\n\n### §RK1 A design\n\n{body}\n", encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, sections=True)
    assert (estimate.parsed, estimate.conforming, estimate.changing) == (1, 0, 1)
    assert {m.field: m.over for m in estimate.measures}["section"] == 1


def test_the_scheme_decides_whether_there_is_a_count_at_all(tmp_path: Path) -> None:
    """RK44's measurement, from the estimate's side: 151 headings read as 0 sections."""
    target = tmp_path / "IMPROVEMENTS.md"
    target.write_text(
        "# Improvements\n\n### VIII.1 A design\n\nProse.\n\n### VIII.2 Another\n\nProse.\n",
        encoding="utf-8",
    )
    config = Config.default(tmp_path)
    assert adopt(config, target, sections=True).parsed == 0
    outlined = adopt(config, target, sections=True, ref_scheme="outline")
    assert (outlined.parsed, outlined.ref_scheme) == (2, "outline")


def test_a_rationale_file_claims_no_prefix(tmp_path: Path) -> None:
    """A section is addressed by its §, not by a family — so none is named or guessed."""
    target = tmp_path / "IMPROVEMENTS.md"
    target.write_text(RATIONALE, encoding="utf-8")
    estimate = adopt(Config.default(tmp_path), target, sections=True)
    assert (estimate.families, estimate.prefix, estimate.inferred) == ((), "", False)


def test_two_units_are_two_runs(tmp_path: Path) -> None:
    target = tmp_path / "IMPROVEMENTS.md"
    target.write_text(RATIONALE, encoding="utf-8")
    with pytest.raises(ValueError, match="its own run"):
        adopt(Config.default(tmp_path), target, ledger=True, sections=True)


def test_the_longest_prints_even_when_nothing_is_over(tmp_path: Path, capsys) -> None:
    """The number an adopter is here for is the longest: a measure that appears only once
    it is exceeded is one nobody can set a limit from."""
    target = tmp_path / "IMPROVEMENTS.md"
    target.write_text(RATIONALE, encoding="utf-8")
    argv = ["-C", str(tmp_path), "adopt", str(target), "--sections"]
    assert main(argv) == EXIT_OK
    out = capsys.readouterr().out
    assert "2 section(s), 2 conform, 0 would change" in out
    assert f"section  longest {FIRST_ARGUMENT} of 250 words, 0 over" in out
    assert "prefix" not in out

    assert main([*argv, "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert (payload["unit"], payload["ref_scheme"]) == ("section", "id")


def test_every_measure_names_the_unit_its_two_figures_are_in(tmp_path: Path, capsys) -> None:
    """RK437: `[limits]` is one table in three units — UTF-16 code units for the five figures
    that refuse, words for `section`, code points for `prose`, which is a fill width and not a
    gate. An adopter reads this report to decide what to declare, and unnamed every row read
    as the same kind of number."""
    target = tmp_path / "IMPROVEMENTS.md"
    target.write_text(RATIONALE, encoding="utf-8")
    argv = ["-C", str(tmp_path), "adopt", str(target), "--sections"]
    assert main(argv) == EXIT_OK
    out = capsys.readouterr().out
    assert "section  longest" in out and f"of 250 {WORDS}" in out
    assert "prose    longest" in out and f"of 88 {CODE_POINTS}" in out

    assert main([*argv, "--json"]) == EXIT_OK
    units = {m["field"]: m["unit"] for m in json.loads(capsys.readouterr().out)["measures"]}
    assert units == {"section": WORDS, "prose": CODE_POINTS}


def test_the_lines_and_the_bullets_are_measured_in_the_unit_they_are_refused_in(
    tmp_path: Path, capsys
) -> None:
    """The five that refuse are counted the way the gate counts (RK430), and say so. The two
    `[non_goals]` rows were the ones still on `len`, which is the report telling an adopter a
    bullet fits that `scoping` then refuses — one astral character is the whole difference."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(
        FOREIGN + "\n## Non-goals\n\n- **📋 A lead**  Because of a reason.\n",
        encoding="utf-8",
    )
    assert main(["-C", str(tmp_path), "adopt", str(target), "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert {m["unit"] for m in payload["measures"]} == {UTF16_UNITS}
    goals = {m["field"]: m for m in payload["non_goals"]["measures"]}
    assert {m["unit"] for m in goals.values()} == {UTF16_UNITS}
    # `📋 A lead` is 8 code points and 9 UTF-16 units, which is the figure the gate reads.
    assert goals["lead"]["longest"] == 9


def test_adopt_writes_nothing(tmp_path: Path) -> None:
    target = tmp_path / "ROADMAP.md"
    target.write_text(FOREIGN, encoding="utf-8")
    before = target.read_bytes()
    adopt(Config.default(tmp_path), target)
    assert target.read_bytes() == before
    assert written(tmp_path) == {"ROADMAP.md"}


# -- the command surface -----------------------------------------------------


def test_an_estimate_is_not_a_gate(tmp_path: Path, capsys) -> None:
    """Exit 0 on a file with nothing but defects: an estimate with a gate's exit code
    is a gate, and the point is to take it *before* the commitment."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(FOREIGN, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target)]) == EXIT_OK
    out = capsys.readouterr().out
    assert "inferred from the ids" in out
    assert "declared by nothing in [markers]" in out


def test_a_file_that_is_not_there_is_a_usage_error(tmp_path: Path, capsys) -> None:
    assert main(["-C", str(tmp_path), "adopt", str(tmp_path / "nope.md")]) == EXIT_USAGE
    said = capsys.readouterr().err
    # RK370: the argument, and the path spelled from the project root — neither of which
    # `pathlib`'s own sentence carries, and a run takes several paths now.
    assert "nope.md (the file to measure)" in said
    assert "No such file or directory" not in said


NOT_A_BACKLOG = """# My project

A paragraph about the project, several lines long.

## Install

    pip install myproject
"""


#: Every pair of `adopt` arguments that names no measurement, with the words its refusal
#: turns on (RK386). A table rather than one test each: they are a family, and written one
#: test at a time the family was invisible — the oldest of the three had no test at all,
#: because it shipped before the two whose task *was* the refusal. A fourth arrives here with
#: its row empty, which is the whole reason for the shape.
REFUSED_PAIRS = (
    ("--ledger with --sections", {"ledger": True, "sections": True}, "measure different units"),
    (
        "--with without --sections",
        {"alongside": ["STRATEGY.md"]},
        "a backlog holds lines and not headings",
    ),
    ("--prefix with --sections", {"sections": True, "prefix": "SH"}, "for a prefix to choose"),
)


@pytest.mark.parametrize(
    ("arguments", "says"),
    [(arguments, says) for _, arguments, says in REFUSED_PAIRS],
    ids=[named for named, _, _ in REFUSED_PAIRS],
)
def test_an_argument_pair_that_names_no_measurement_is_refused(
    tmp_path: Path, arguments: dict, says: str
) -> None:
    """RK386: an untested refusal here is not an internal invariant — these are the sentences
    an adopter reads while deciding whether to adopt, on the one command that runs before a
    project has a gate of its own."""
    with pytest.raises(ValueError) as caught:
        # No file is written, and that is an assertion too: all three are refused before
        # anything is opened, so the reason reaches a caller whose path was wrong as well.
        adopt(Config.discover(tmp_path), tmp_path / "ROADMAP.md", **arguments)
    assert says in str(caught.value)


def test_the_halves_of_a_refused_pair_each_still_stand_alone(tmp_path: Path) -> None:
    """RK384, which the table above cannot say: the refusal is about the combination, so
    neither flag may be the one that stopped working."""
    target = tmp_path / "IMPROVEMENTS.md"
    target.write_text("# Improvements\n\n## §I A design\n\nProse.\n", encoding="utf-8")
    config = Config.discover(tmp_path)
    assert adopt(config, target, sections=True).parsed == 1
    assert adopt(config, target, prefix="SH").prefix == "SH"


def test_a_file_that_is_no_backlog_is_told_apart_from_an_empty_one(tmp_path: Path) -> None:
    """RK376: RK98's rule at the far end of itself. `tabular` and `listed` stop a backlog in a
    shape nothing reads from answering an empty file's number, and a file that is not a backlog
    in any shape walked past both — on the run a typo puts the caller least able to check."""
    target = tmp_path / "README.md"
    target.write_text(NOT_A_BACKLOG, encoding="utf-8")
    config = Config.discover(tmp_path)
    foreign = adopt(config, target)
    assert (foreign.parsed, foreign.recognised) == (0, 0) and foreign.lines > 0

    # The roadmap that really is empty answers the same headline and is a different fact: its
    # block heading was read, so the zero above it means what it says.
    empty = tmp_path / "ROADMAP.md"
    empty.write_text("# Roadmap\n\n## Block A\n", encoding="utf-8")
    assert adopt(config, empty).recognised == 1

    # And a file with nothing in it at all needs no sentence: there the zero is simply true.
    blank = tmp_path / "BLANK.md"
    blank.write_text("", encoding="utf-8")
    assert (adopt(config, blank).lines, adopt(config, blank).recognised) == (0, 0)


JUST_PROSE = """Just prose, no headings at all.

A second paragraph, also prose, nothing this format reads.

A third one for bulk.
"""


def test_both_runs_say_a_file_was_read_in_no_shape(tmp_path: Path) -> None:
    """RK387: RK376 landed where the estimate is assembled for entries, and the rationale run
    assembles its own — so `--sections` went on answering a blank file's words over prose. The
    third field to arrive in one path and not the other, which is why this asserts the pair."""
    target = tmp_path / "NOTES.md"
    target.write_text(JUST_PROSE, encoding="utf-8")
    config = Config.discover(tmp_path)
    backlog, prose = adopt(config, target), adopt(config, target, sections=True)
    # The shapes each run reads differ — entries and bullets against headings — and what may
    # not differ is whether the run says nothing was read.
    assert (backlog.lines, backlog.recognised) == (prose.lines, prose.recognised)
    assert backlog.lines > 0 and backlog.recognised == 0


def test_a_heading_a_rationale_run_does_read_is_not_called_unread(tmp_path: Path) -> None:
    # The other side of it, so the parity above is not satisfied by both paths answering zero
    # to everything: a heading with prose and no anchor is a shape this run reads (RK281), and
    # a run that found one has not read nothing.
    target = tmp_path / "NOTES.md"
    target.write_text("# Notes\n\n## A design\n\nProse with no anchor.\n", encoding="utf-8")
    assert adopt(Config.discover(tmp_path), target, sections=True).recognised == 1


def test_a_heading_the_format_cannot_read_as_structure_is_not_read(tmp_path: Path) -> None:
    # The qualifier that is the measurement rather than a detail of it: counting every heading
    # put this back where it started, a `README.md` answering two for `# My project` and
    # `## Install` — the same headings `blocks` already looks at and finds no label in.
    target = tmp_path / "README.md"
    target.write_text(NOT_A_BACKLOG, encoding="utf-8")
    assert adopt(Config.discover(tmp_path), target).blocks == ()


#: A ledger grouping its entries under sub-headings of the block's own label — Shio's shape,
#: where eight of them sit under one `## Block K` and 91 entries hang off them.
NESTED_LEDGER = """# Shipped

## Block B — Authoring

### Block B follow-ups

- ✅ **RK6** **A sixth thing fails** — because it held.

### Block B follow-ups

- ✅ **RK4** **A fourth thing fails** — because it held.
"""

#: The state RK439 keeps refusing: two regions neither of which is inside the other.
DOUBLED_LEDGER = """# Shipped

## Block B — Authoring

- ✅ **RK6** **A sixth thing fails** — because it held.

## Block B — Authoring, again

- ✅ **RK4** **A fourth thing fails** — because it held.
"""


def _ledger(tmp_path: Path, body: str) -> Path:
    target = tmp_path / "CHANGELOG.md"
    target.write_text(body, encoding="utf-8")
    return target


def test_a_block_grouped_by_sub_headings_is_counted_once(tmp_path: Path, capsys) -> None:
    """RK445: the estimate read every heading naming a label, which RK439 stopped being a
    declaration of one. Shio's ledger nests eight `### Block K follow-ups` under their own
    `## Block K`, so the first line an adopting project reads about its own corpus reported
    Block K nine times — and that line is what a `[files]` declaration and a first `lint`
    are decided from."""
    target = _ledger(tmp_path, NESTED_LEDGER)
    assert adopt(Config.discover(tmp_path), target, ledger=True).blocks == ("B",)
    assert main(["-C", str(tmp_path), "adopt", str(target), "--ledger"]) == EXIT_OK
    assert "blocks   B\n" in capsys.readouterr().out


def test_two_regions_neither_inside_the_other_are_still_counted_twice(tmp_path: Path) -> None:
    """The repeat that survives, and has to: that is `block.repeated`, and an adopter
    counting labels is exactly the reader who needs to see it before committing."""
    target = _ledger(tmp_path, DOUBLED_LEDGER)
    assert adopt(Config.discover(tmp_path), target, ledger=True).blocks == ("B", "B")


def test_the_list_keeps_the_files_own_order(tmp_path: Path) -> None:
    """It is read as the shape of the plan, so it is not reordered by first mention."""
    target = _ledger(
        tmp_path,
        "# Shipped\n\n## Block C — Query\n\n### Block C notes\n\n"
        "## Block A — The model\n\n## Block B — Authoring\n",
    )
    assert adopt(Config.discover(tmp_path), target, ledger=True).blocks == ("C", "A", "B")


def test_the_command_says_which_zero_this_is(tmp_path: Path, capsys) -> None:
    target = tmp_path / "README.md"
    target.write_text(NOT_A_BACKLOG, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target)]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "nothing in 7 line(s) was read in any shape" in printed
    # A measurement and not a verdict: the count of lines that would have to change is an
    # answer about a backlog becoming conforming, and this file may be no backlog at all.
    assert "0 conform, 0 would change" in printed


def test_the_configuration_is_refused_rather_than_measured_as_an_empty_backlog(
    tmp_path: Path,
) -> None:
    """RK374: it opens, so every reader below found no line in it and the estimate answered
    `0 lines, 0 would change` — what an empty roadmap reports, and the one answer RK98 says
    an estimate may not give."""
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n', encoding="utf-8"
    )
    (tmp_path / "ROADMAP.md").write_text(CONFORMING, encoding="utf-8")
    config = Config.discover(tmp_path)
    with pytest.raises(NotACorpus) as caught:
        adopt(config, tmp_path / "roadkeep.toml")
    # The door, said precisely: this *is* the configuration this run loaded, so what it
    # declares is what the caller almost certainly meant.
    assert "measure ROADMAP.md" in str(caught.value)


def test_a_pyproject_that_declares_this_tool_is_the_same_refusal(tmp_path: Path) -> None:
    """RK375: RK374's guard was by filename, so the newer of the two doors into this format
    reached one of the two files it is declared in — and the other went on measuring as the
    empty backlog that refusal exists to stop."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "whatever"\n\n[tool.roadkeep]\nprefix = "SH"\n', encoding="utf-8"
    )
    with pytest.raises(NotACorpus):
        adopt(Config.discover(tmp_path), tmp_path / "pyproject.toml")


def test_a_pyproject_declaring_nothing_here_is_measured_and_not_refused(tmp_path: Path) -> None:
    # The reason the guard could not simply take the filename: most repositories have one of
    # these and this format only sometimes lives in it, so the table is what decides — the
    # same question `init` asks, and now the same reader asking it.
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "plain"\n', encoding="utf-8")
    assert adopt(Config.discover(tmp_path), tmp_path / "pyproject.toml").parsed == 0
    # Unparseable is not a declaration either: refusing a file because its TOML is broken
    # would be refusing it on a hunch about what somebody meant to put in it.
    (tmp_path / "pyproject.toml").write_text("not toml [[[\n", encoding="utf-8")
    assert adopt(Config.discover(tmp_path), tmp_path / "pyproject.toml").parsed == 0


def test_a_configuration_belonging_to_another_tree_is_refused_without_a_door(
    tmp_path: Path,
) -> None:
    # Offering this project's paths for somebody else's `roadkeep.toml` would send the caller
    # at the wrong tree — the RK292 care, one refusal over.
    (tmp_path / "roadkeep.toml").write_text('prefix = "RK"\n', encoding="utf-8")
    elsewhere = tmp_path / "vendor"
    elsewhere.mkdir()
    (elsewhere / "roadkeep.toml").write_text('prefix = "SH"\n', encoding="utf-8")
    said = str(NotACorpus("the file to measure", elsewhere / "roadkeep.toml",
                          Config.discover(tmp_path)))
    assert "is not a corpus" in said and "measure " not in said


def test_the_configuration_is_refused_through_the_second_argument_too(tmp_path: Path) -> None:
    # `--with` takes paths as well, and there the silence was worse: a config file contributes
    # no anchors, so it neither collided nor was reported, and the caller who meant a sibling
    # prose file got a clean run.
    (tmp_path / "roadkeep.toml").write_text('prefix = "RK"\n', encoding="utf-8")
    target = tmp_path / "IMPROVEMENTS.md"
    target.write_text("# Improvements\n\n## §I A design\n\nProse.\n", encoding="utf-8")
    with pytest.raises(NotACorpus) as caught:
        adopt(
            Config.discover(tmp_path),
            target,
            sections=True,
            alongside=[str(tmp_path / "roadkeep.toml")],
        )
    assert caught.value.named == "--with"


def test_the_refusal_names_the_argument_that_carried_each_path(tmp_path: Path) -> None:
    target = tmp_path / "IMPROVEMENTS.md"
    target.write_text("# Improvements\n\n## §I A design\n\nProse.\n", encoding="utf-8")
    with pytest.raises(Unreadable) as caught:
        adopt(
            Config.discover(tmp_path),
            target,
            sections=True,
            alongside=[str(tmp_path / "gone.md"), str(tmp_path / "also-gone.md")],
        )
    assert [named for named, _ in caught.value.missing] == ["--with", "--with"]
    assert "gone.md (--with), also-gone.md (--with)" in str(caught.value)


def test_no_file_is_opened_when_one_of_the_set_cannot_be(tmp_path: Path) -> None:
    # The reason the check runs before the first read and not inside the loop: a report that
    # measured two of three files stops looking like a partial answer and starts looking
    # like a complete one — `init`'s all-or-nothing order, one command over.
    target = tmp_path / "IMPROVEMENTS.md"
    target.write_text("# Improvements\n\n## §I A design\n\nProse.\n", encoding="utf-8")
    sibling = tmp_path / "STRATEGY.md"
    sibling.write_text("# Strategy\n\n## §I A bet\n\nProse.\n", encoding="utf-8")
    config = Config.discover(tmp_path)
    # The two that exist would collide at `I`, so a run that read them and then stopped would
    # have a finding to report — and reporting it is exactly what must not happen.
    with pytest.raises(Unreadable):
        adopt(
            config, target, sections=True, alongside=[str(sibling), str(tmp_path / "gone.md")]
        )
    assert adopt(config, target, sections=True, alongside=[str(sibling)]).ambiguous


def test_json_carries_every_number_the_report_prints(tmp_path: Path, capsys) -> None:
    target = tmp_path / "ROADMAP.md"
    target.write_text(FOREIGN, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target), "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["prefix"] == "SH"
    assert payload["inferred"] is True
    assert payload["parsed"] == 2
    assert payload["undeclared"] == [{"marker": "✨", "count": 1}]
    assert payload["tabular"] == 0
    assert {m["field"] for m in payload["measures"]} == {"symptom", "why", "line"}


def test_init_json_names_what_it_created(tmp_path: Path, capsys) -> None:
    assert main(["-C", str(tmp_path), "init", "--json", "--block", "A"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["blocks"] == ["A"]
    assert len(payload["created"]) == 4
    assert all(Path(name).is_file() for name in payload["created"])


def test_init_refusal_is_a_usage_error(tmp_path: Path, capsys) -> None:
    (tmp_path / "roadkeep.toml").write_text('prefix = "RK"\n', encoding="utf-8")
    assert main(["-C", str(tmp_path), "init"]) == EXIT_USAGE
    assert "adopt" in capsys.readouterr().err


# -- the corpus that decides §RK20 -------------------------------------------


@pytest.mark.parametrize("scheme", ["outline", "id"])
def test_shio_is_readable_before_it_is_conforming(tmp_path: Path, scheme: str) -> None:
    """The measurement RK20 turns on: the lines parse, and it is the *prose* that does not.

    If a meaningful fraction could not be read at all, the grammar would be wrong. What
    this asserts is the opposite finding — under Shio's own outline scheme the lines round
    -trip, so adoption is an editing cost and not a reformatting one.

    Read at the pin (RK105), which is why the count below is exact: the estimate shrinks
    every time Shio ships, and a bound set at today's live reading is a count whatever the
    comment beside it claims (RK102) — which is how the one in `test_document.py` was
    crossed. What a moving corpus cannot be allowed to decide is whether this suite is red.

    **Both schemes, because an estimate means nothing until one is named** (RK1146). The
    editing-cost half used to rest on which codes appeared, and Shio's prose has since come
    inside even this repository's narrower limits — so that half stopped asserting and
    skipped, on a corpus that had simply improved. Pointing the same bytes at the wrong
    scheme is what still separates the two costs: every line that is canonical under their
    numbering is non-canonical under ours, and no editing of theirs can make that go away.
    """
    corpora.require(corpora.SHIO)
    source = corpora.materialise(corpora.SHIO, "roadmap", tmp_path)
    estimate = adopt(Config.default(tmp_path), source, ref_scheme=scheme)
    assert estimate.prefix == "SH"
    # Re-measured with the pin (RK1144): 48 at `b9302e8e`, and the roadmap turned over.
    assert estimate.parsed == 20
    codes = dict(estimate.codes)
    if scheme == "outline":
        assert estimate.non_canonical == 0
        # The finding is which *kind* of code appears: none about the id, the deps, the marker
        # or the block, so what adoption asks for is editing and not reformatting.
        assert [c for c in codes if not c.startswith(("why.", "line.", "ref."))] == []
    else:
        assert estimate.non_canonical == estimate.parsed
        assert {"line.non-canonical", "ref.mismatch"} <= set(codes)


class _Stdin:
    """A stdin the section writer can read prose from, with nothing to reconfigure."""

    def __init__(self, text: str) -> None:
        self._text = text

    def read(self) -> str:
        return self._text


def test_the_estimate_is_taken_under_the_numbers_the_gate_applies(tmp_path: Path) -> None:
    """RK76: `adopt` was the one caller reaching past `Config.schema_for(role)`.

    So `[limits.changelog]` and `[rules.changelog]` — the two tables a project writes
    *because* its ledger is history — were invisible to the estimate, and the number it
    printed measured a commitment nobody was being asked to make. Measured on Dumont:
    34 `why.no-terminator` from `adopt` against none from `lint`, on one file.
    """
    (tmp_path / "roadkeep.toml").write_text(
        '[files]\nchangelog = "CHANGELOG.md"\n\n'
        "[limits.changelog]\nwhy = 4000\nline = 4200\n\n"
        "[rules.changelog]\none_sentence = false\nterminator = false\n",
        encoding="utf-8",
    )
    history = "Two sentences. And no terminating stop, at " + "x" * 400
    target = tmp_path / "CHANGELOG.md"
    target.write_text(
        f"# Shipped\n\n## Block A\n\n- ✅ **RK1** **A symptom** — {history}\n",
        encoding="utf-8",
    )
    assert adopt(Config.discover(tmp_path), target, ledger=True).conforming == 1

    # And it is those two tables doing it, not the ledger shape: the same file, the same
    # `--ledger`, with the role's own numbers withdrawn, is the estimate as it read before.
    (tmp_path / "roadkeep.toml").write_text(
        '[files]\nchangelog = "CHANGELOG.md"\n', encoding="utf-8"
    )
    bare = adopt(Config.discover(tmp_path), target, ledger=True)
    assert bare.conforming == 0
    assert {code for code, _ in bare.codes} >= {
        "why.too-long",
        "why.sentences",
        "why.no-terminator",
    }


# -- the list init left ungoverned (RK1040) ----------------------------------


def test_the_scaffold_governs_the_list_it_wrote_a_heading_for(tmp_path: Path, capsys) -> None:
    """The defect. `init` wrote `## Non-goals` into the roadmap and no `[non_goals]` into
    `roadkeep.toml`, so the one verb that fills that heading refused on a project the
    scaffold had just created — with a reason that is `adopt`'s: prose predating the
    grammar, which cannot be true of a heading `init` emptied."""
    where = ["-C", str(tmp_path)]
    assert main([*where, "init"]) == EXIT_OK
    capsys.readouterr()
    assert Config.discover(tmp_path).non_goals is not None
    assert main([*where, "non-goal", "add", "--lead", "No web UI", "--why", "A second store."]) == EXIT_OK
    capsys.readouterr()
    assert main([*where, "non-goal", "list"]) == EXIT_OK
    assert "No web UI" in capsys.readouterr().out
    assert main([*where, "lint"]) == EXIT_OK


def test_the_table_is_written_empty_so_the_numbers_stay_the_defaults(tmp_path: Path) -> None:
    """`_scope` documents an empty table as the shortest way to opt in: what a project says
    by writing it is *that* the list is a schema. Numbers here would read as limits somebody
    chose, which is the argument `[ids] pad` and the `[ledger]` absences already make."""
    assert main(["-C", str(tmp_path), "init"]) == EXIT_OK
    text = (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")
    # Nothing follows either table but a comment, which is what they declare: nothing. Two of
    # them since RK1313 — the positive twin arrived after RK1040 settled this shape, so a fresh
    # tree could not call the one verb that fills it.
    for table in ("[non_goals]", "[criteria]"):
        after = text.split(table, 1)[1].lstrip()
        assert not after or after.startswith("#"), f"{table} declares something"
    assert "lead =" not in text
    for scope in (Config.discover(tmp_path).non_goals, Config.discover(tmp_path).criteria):
        assert scope is not None
        assert (scope.lead, scope.why) == (Scope().lead, Scope().why)


def test_adopt_still_writes_no_config_at_all(tmp_path: Path, capsys) -> None:
    """The bound, and the reason RK70 made the list opt-in: an adopting project's bullets
    were written years before this grammar, and a gate reporting fifteen findings on the
    first run is one that gets bypassed rather than adopted."""
    (tmp_path / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Block A — The model\n\n## Non-goals\n\n- **Something long** that "
        "somebody wrote as prose long before any of this existed.\n",
        encoding="utf-8",
    )
    assert main(["-C", str(tmp_path), "adopt", str(tmp_path / "ROADMAP.md")]) == EXIT_OK
    assert not (tmp_path / "roadkeep.toml").exists()
    assert "not governed" in capsys.readouterr().out


def test_the_estimate_names_the_door_this_project_has_not_got(tmp_path: Path) -> None:
    """RK1087. Measuring for RK1084 found that **neither adopting corpus declares a store**,
    and neither carries a single retired entry either — so a pause spelled another way is not
    there to find, and the feature's only user is this tool's own suite.

    An adopter reading an estimate is asking what the format costs, and *there is no door for
    "not now"* is part of the answer. Without this it arrives as a refusal from the first
    `defer`, at the moment somebody wanted to set a line aside.
    """
    (tmp_path / "R.md").write_text(
        "# R\n\n## Block A — x\n\n- 📋 **RK1** (deps: —) **A symptom** — Because of it.\n",
        encoding="utf-8",
    )
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "R.md"\n', encoding="utf-8"
    )
    named = {gain.name: gain.because for gain in adopt(
        Config.discover(tmp_path), str(tmp_path / "R.md")
    ).gains}
    # The category RK1089 named: the store, a prose file to point at, the roadmap's other
    # bullet, the queue, and the decisions file (RK1269). Each says what the project has
    # *instead*.
    assert set(named) == {"pause", "design", "non-goals", "queue", "decisions"}
    assert "no deferred store" in named["pause"] and "terminal" in named["pause"]


def test_a_project_with_every_door_reports_no_gains(tmp_path: Path) -> None:
    # Said only where the answer is *nothing*, which is the shape every other absence in an
    # estimate takes: a limit stated where it does not bite is noise.
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "R.md"\ndeferred = "D.md"\n'
        'improvements = "I.md"\ndecisions = "K.md"\n[non_goals]\nlead = 60\nwhy = 200\n',
        encoding="utf-8",
    )
    (tmp_path / "R.md").write_text(
        "# R\n\n## Priority\n\n## Block A — x\n\n"
        "- 📋 **RK1** (deps: —) **A symptom** — Because of it.\n",
        encoding="utf-8",
    )
    (tmp_path / "D.md").write_text("# D\n\n## Block A — x\n", encoding="utf-8")
    (tmp_path / "I.md").write_text("# I\n", encoding="utf-8")
    (tmp_path / "K.md").write_text("# K\n\n## Block A — x\n", encoding="utf-8")
    assert adopt(Config.discover(tmp_path), str(tmp_path / "R.md")).gains == ()


def test_the_queue_is_the_fourth_door_and_is_read_off_the_section(tmp_path: Path) -> None:
    """RK1090. RK1089 named a queue among the category's members and wrote three, which is
    the shape that task exists to prevent, one iteration later.

    Read off the `## Priority` **heading** and not off what is under it: RK325 moved the
    queue into the roadmap, and a project whose queue is empty today has the door and is
    using it. Counting entries reported this repository as missing one on any day nothing
    outranked the id order — which is most days.
    """
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "R.md"\n', encoding="utf-8"
    )
    line = "- 📋 **RK1** (deps: —) **A symptom** — Because of it.\n"
    (tmp_path / "R.md").write_text(
        "# R\n\n## Block A — x\n\n" + line, encoding="utf-8"
    )
    named = {g.name for g in adopt(Config.discover(tmp_path), str(tmp_path / "R.md")).gains}
    assert "queue" in named

    # The section, empty, is the door — so the gain goes even though nothing is queued.
    (tmp_path / "R.md").write_text(
        "# R\n\n## Priority\n\n## Block A — x\n\n" + line, encoding="utf-8"
    )
    opened = {g.name for g in adopt(Config.discover(tmp_path), str(tmp_path / "R.md")).gains}
    assert "queue" not in opened


def test_the_queue_gain_names_the_section_and_never_the_retired_config_key(tmp_path: Path) -> None:
    # RK325 moved the queue out of `[priority]`, and the gate reports that key as
    # `priority.config` — so a gain naming the old home would be advice the gate refuses.
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "R.md"\n', encoding="utf-8"
    )
    (tmp_path / "R.md").write_text(
        "# R\n\n## Block A — x\n\n- 📋 **RK1** (deps: —) **A symptom** — Because of it.\n",
        encoding="utf-8",
    )
    (queue,) = [
        g for g in adopt(Config.discover(tmp_path), str(tmp_path / "R.md")).gains
        if g.name == "queue"
    ]
    assert "## Priority" in queue.because and "[priority]" not in queue.because
    # And it says what the project does *instead*, which is a real answer rather than a gap.
    assert "lowest ready id" in queue.because


def test_every_door_the_format_opens_is_named_among_the_gains() -> None:
    """RK1093, and the question a function body could not be asked. RK1089 built the category
    so a fourth member had somewhere to land; RK1090 landed it by adding a fifth `if` to a
    block that was already four, which is the failure RK1089 was filed about arriving one
    iteration later.

    The closure is over what the *format* has: a governed role a project may declare, plus
    the two shapes that are not roles — the non-goals table and the priority section. A fifth
    door added to the tool is red here until somebody says whether an estimate mentions it.
    """
    from roadkeep.adopting import GAINS
    from roadkeep.config import ROLES

    named = {name for name, _opens, _because in GAINS}
    # The roles an estimate can be about: the roadmap is the file being estimated and the
    # changelog is where its lines go, so neither is a door a project would *gain*.
    optional = set(ROLES) - {"roadmap", "changelog"}
    assert {"pause", "queue", "decisions"} <= named
    # `design` stands for the prose roles together: one file answers a pointer, and which of
    # the two it is is the project's business (RK196).
    assert len(optional - {"improvements", "strategy", "deferred", "decisions"}) == 0
    assert named == {"pause", "design", "non-goals", "queue", "decisions"}


def test_every_gain_says_what_the_project_does_instead(tmp_path: Path) -> None:
    # A row that only names an absence is a gap; one that says what happens instead is a
    # cost, which is what an adopter is asking about. Held over the table rather than over
    # one sentence, so a fifth row cannot be the first that only says no.
    from roadkeep.adopting import GAINS

    for name, _opens, because in GAINS:
        assert len(because.split()) >= 20, name
        assert "no " in because or "not " in because, name


def _project(tmp_path: Path) -> Path:
    """A conforming backlog under a config of its own — what the reads below need."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n', encoding="utf-8"
    )
    (tmp_path / "ROADMAP.md").write_text(CONFORMING, encoding="utf-8")
    return tmp_path


def test_the_estimate_prices_the_surface_it_arrives_with(tmp_path, capsys):
    """The other side of the transaction (RK1100).

    `GAINS` names four doors the format opens and the report named no cost at all, which is a
    decision asked for on half its terms. RK1097 made the missing half knowable: the served
    surface is a fact about the package — three projects, the same 52 tools, 1.4% apart — so
    it is the same figure for an adopter as for this repository.
    """
    from roadkeep.serving import surface

    root = _project(tmp_path)
    estimate = adopt(Config.discover(root), root / "ROADMAP.md")
    assert estimate.surface == surface(Config.discover(root)).characters

    main(["-C", str(root), "adopt", str(root / "ROADMAP.md")])
    printed = capsys.readouterr().out
    line = next(one for one in printed.splitlines() if one.strip().startswith("serves"))
    # The cadence travels with the number, or the reader adds it to a per-turn figure — which
    # is the arithmetic RK1095 refused to print and this row would reintroduce.
    assert "once at connect" in line and str(estimate.surface) in line
    assert "[tools]" in line, "a cost with no door to hold it is a number and not a reading"


def test_the_cost_is_reported_and_never_weighed_against_the_gains(tmp_path, capsys):
    # L4. The estimate states both and concludes nothing: a sentence recommending adoption, or
    # against it, is the tool making somebody's decision from two numbers it does not own.
    root = _project(tmp_path)
    main(["-C", str(root), "adopt", str(root / "ROADMAP.md")])
    printed = capsys.readouterr().out.lower()
    for verdict in ("worth", "recommend", "should", "cheap", "expensive"):
        assert verdict not in printed, f"the estimate reached a conclusion: {verdict}"


def test_the_json_carries_the_cadence_with_the_number(tmp_path, capsys):
    root = _project(tmp_path)
    main(["-C", str(root), "adopt", str(root / "ROADMAP.md"), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["serves"]["cadence"] == "once, at connect"
    assert payload["serves"]["characters"] > 0


# -- which directory a path argument is relative to (RK1101) ------------------


def test_a_relative_target_is_read_from_the_project_and_not_from_the_caller(tmp_path, monkeypatch):
    """The silent half, which is the one worth a test (RK1101).

    `-C` names the project, and a relative path resolved against the *process's* directory
    read a file the caller never chose. Loud where that file is absent; here both trees hold a
    `ROADMAP.md`, and the old rule measured the caller's backlog under the project's config
    with nothing in the report naming the tree it read.
    """
    project, elsewhere = _project(tmp_path / "project"), tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Block A — The model\n\n"
        "- 📋 **RK9** (deps: —) **Another project's line** — Because it is not this one's. → §RK9\n",
        encoding="utf-8",
        newline="",
    )
    monkeypatch.chdir(elsewhere)

    estimate = adopt(Config.discover(project), "ROADMAP.md")
    assert estimate.parsed == 2, "the caller's one-line file was measured, not the project's"
    # And the report spells it from the project root, which is the answer to *which tree*: an
    # absolute path here is the message `provenance.invocation` refuses.
    assert estimate.path.as_posix() == "ROADMAP.md"


def test_an_absolute_target_is_still_exactly_the_file_named(tmp_path, monkeypatch):
    # The rule is about resolving a *relative* path, and an absolute one was never ambiguous.
    project = _project(tmp_path / "project")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "OTHER.md").write_text(CONFORMING, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    estimate = adopt(Config.discover(project), outside / "OTHER.md")
    assert estimate.parsed == 2
    # Not under the root, so the whole path is the only true answer — `_relative`'s own rule.
    assert estimate.path.is_absolute()


def test_the_refusal_names_the_file_beside_the_caller(tmp_path, monkeypatch):
    """The cost of the change, paid where it lands (RK1101).

    `cd docs && adopt ROADMAP.md` used to work and now refuses, and the one thing that refusal
    must not do is read as the file having gone missing. So where the same relative path *is*
    a file next to the caller, the message says so and says which spelling to pass.
    """
    project = _project(tmp_path / "project")
    beside = tmp_path / "beside"
    beside.mkdir()
    (beside / "NOTES.md").write_text(CONFORMING, encoding="utf-8")
    monkeypatch.chdir(beside)
    with pytest.raises(Unreadable) as raised:
        adopt(Config.discover(project), "NOTES.md")
    said = str(raised.value)
    assert "NOTES.md is a file where this was run" in said
    assert "read from the project root" in said
    # Named and never opened: two bases is the ambiguity the rule removes, and a fallback here
    # would put it back one layer down — which is why this is a refusal and not a second look.


def test_a_body_file_stays_relative_to_the_caller(tmp_path, monkeypatch):
    """The other half of the rule, and the reason it is not "every path" (RK1101).

    `--section-body-file` names a file to *read from*, the way `cat` does — the caller's own,
    not one this project has. Resolving it against the root would be a rule about somebody
    else's shell.
    """
    project = _project(tmp_path / "project")
    (project / "IMPROVEMENTS.md").write_text(
        "# Improvements\n\n## Block A — The model\n", encoding="utf-8", newline=""
    )
    (project / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nimprovements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    beside = tmp_path / "beside"
    beside.mkdir()
    (beside / "body.md").write_text(
        "A rationale written somewhere else entirely, which is where a caller keeps one.\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(beside)
    assert main([
        "-C", str(project), "section", "add", "RK1",
        "--title", "A title for it", "--body-file", "body.md",
    ]) == EXIT_OK
    assert "somewhere else entirely" in (project / "IMPROVEMENTS.md").read_text(encoding="utf-8")


def test_the_two_verbs_that_arrived_last_work_on_a_fresh_project(tmp_path: Path, capsys) -> None:
    """RK1313, observed on a tree `roadkeep init` had just created, 2026-08-23. `criterion add
    --block A` refused with *roadkeep.toml declares no [criteria]*, and `add --requires
    hardware` refused with `requires.unknown`, naming a table the file does not carry.

    RK1040 settled the shape: a section the scaffold just emptied has no prose to report on,
    and leaving it ungoverned refuses the one verb that fills it. RK1265 added the positive
    twin and RK1297 the requirement vocabulary, and neither reached the render — so the two
    verbs that arrived last were the two a fresh project could not call, and the remedy each
    refusal names is a hand edit to configuration this tool owns.
    """
    where = ["-C", str(tmp_path)]
    assert main([*where, "init"]) == EXIT_OK
    capsys.readouterr()
    assert main([
        *where, "criterion", "add", "--block", "A",
        "--lead", "Every write has a door",
        "--why", "the schema refuses at, and not a lint that reports after.",
    ]) == EXIT_OK
    assert main([*where, "lint"]) == EXIT_OK


def test_the_vocabulary_is_commented_because_an_empty_one_governs_nothing(tmp_path: Path) -> None:
    """The half that is *not* the same fix. `[criteria]` is an opt-in, so the empty table is
    the whole of it; this is a list of words, and `declared = []` changes only which refusal
    the author reads. So it takes the shape `[ids]`, `[headings]` and `[ledger]` are written in
    — named where a project departs from what every project starts with. What was missing was
    never the table but the fact that the axis exists."""
    assert main(["-C", str(tmp_path), "init"]) == EXIT_OK
    text = (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")
    assert "# [requirements]" in text
    # Commented, so the parser sees nothing and `--requires` still refuses by name until a
    # project names its own words — which is the state that made the axis discoverable.
    assert Config.discover(tmp_path).schema.requirements == ()

    commented = '# [requirements]\n# declared = ["hardware"]'
    (tmp_path / "roadkeep.toml").write_text(
        text.replace(commented, commented.replace("# ", "")), encoding="utf-8"
    )
    assert Config.discover(tmp_path).schema.requirements == ("hardware",)


# -- the other axis one argument carries (RK1328) ------------------------------

#: The table `init` writes since RK1313, taken back out to make the project that predates
#: that scaffold — which is every project already past `init`, and most of them.
OPENED = "[criteria]" + chr(10)


def test_an_opt_in_table_opens_on_a_project_past_init(tmp_path: Path, capsys) -> None:
    """Measured on this repository, declaring `[criteria]` for RK1323: the table went in by
    hand, because no verb opened one. RK1313 closed it for a project being *scaffolded* and
    named the half it left open — every project already past `init`, which is most of them.

    `declare <role>` retrofits a file and `govern <address> <n>` writes a number against a
    reading; an opt-in table carries no number at all — declared at all means governed — so it
    fell between them, and the remedy each refusal named was an edit to configuration this tool
    owns the writes to, which over MCP is not an edit at all.
    """
    from roadkeep.config import Config

    where = ["-C", str(tmp_path)]
    assert main([*where, "init"]) == EXIT_OK
    capsys.readouterr()
    # `init` writes it, so take it back out: this is the project that predates that scaffold.
    written = (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(
        written.replace(OPENED, "", 1), encoding="utf-8"
    )
    assert Config.discover(tmp_path).criteria is None

    assert main([*where, "declare", "criteria"]) == EXIT_OK
    said = capsys.readouterr().out
    assert "declared [criteria]" in said
    # The verb it gates, which is what a caller came here to run — `declare`'s own rule.
    assert "criterion add --block" in said
    assert Config.discover(tmp_path).criteria is not None
    assert main([*where, "lint"]) == EXIT_OK


def test_the_table_arrives_empty_so_the_numbers_stay_the_defaults(tmp_path: Path, capsys) -> None:
    # What a project says by writing the table is *that* the list is a schema; `lead` and `why`
    # are what it may then tune, and `govern` is the verb for that. A number written here would
    # read as a limit somebody chose, which is `[ids] pad`'s argument and `init`'s for this one.
    from roadkeep.config import Config, Scope

    where = ["-C", str(tmp_path)]
    assert main([*where, "init"]) == EXIT_OK
    written = (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(
        written.replace(OPENED, "", 1), encoding="utf-8"
    )
    capsys.readouterr()
    assert main([*where, "declare", "criteria"]) == EXIT_OK
    text = (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")
    assert text.rstrip().endswith("[criteria]")
    scope = Config.discover(tmp_path).criteria
    assert (scope.lead, scope.why) == (Scope().lead, Scope().why)


def test_a_table_already_open_is_refused_and_not_written_twice(tmp_path: Path, capsys) -> None:
    # `RoleDeclared`'s twin: a table already there governs its list, and writing it again would
    # either replace the numbers a project tuned or leave two of it.
    where = ["-C", str(tmp_path)]
    assert main([*where, "init"]) == EXIT_OK
    capsys.readouterr()
    assert main([*where, "declare", "criteria"]) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "already declares [criteria]" in said
    # And it names the verb that *does* change what is in it.
    assert "govern criteria.lead" in said


def test_the_refusal_that_sent_a_caller_here_names_the_command(tmp_path: Path, capsys) -> None:
    """The half this task is measured by: the refusal named a hand edit to configuration this
    tool owns the writes to, and over MCP that is not an edit at all — which is exactly what
    RK1264 built `declare` to remove, one table over."""
    where = ["-C", str(tmp_path)]
    assert main([*where, "init"]) == EXIT_OK
    written = (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(
        written.replace(OPENED, "", 1), encoding="utf-8"
    )
    capsys.readouterr()
    assert main([
        *where, "criterion", "add", "--block", "A", "--lead", "A lead", "--why", "and why.",
    ]) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "`declare criteria` opens the table" in said
    assert "add the table to roadkeep.toml" not in said


def test_a_word_that_is_neither_names_both_vocabularies(tmp_path: Path, capsys) -> None:
    # One argument now carries two, and a caller who typed into the wrong one learns nothing
    # from a refusal about the other.
    where = ["-C", str(tmp_path)]
    assert main([*where, "init"]) == EXIT_OK
    capsys.readouterr()
    assert main([*where, "declare", "nonsense"]) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "roadmap" in said and "criteria" in said


def test_every_gain_is_separated_from_its_sentence_whatever_its_label(tmp_path, capsys) -> None:
    """RK1344. The row padded with `{name:<9}` and two of the five labels are exactly nine —
    `decisions` and `non-goals` — so the pad added nothing and the line printed
    `decisionsno decisions file`. Found by running `adopt` on an ungoverned repository, which
    is the only way to see it: this project declares all five, so its own gains are none.

    Asserted as the rule and never as the width, because a constant is what failed: nine was a
    guess about the longest label that stopped being true the day one reached it. `offered`
    states the same rule one module over — the width is per rendering."""
    target = tmp_path / "ROADMAP.md"
    target.write_text(OUTLINED, encoding="utf-8")
    # The two roles a project needs and nothing else, so the rest are gains: an estimate
    # against no config at all reports none, and would assert nothing.
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text("# Shipped\n\n## Block A\n", encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target), "--prefix", "RK"]) == EXIT_OK
    rows = [
        line for line in capsys.readouterr().out.splitlines() if line.startswith("    ")
    ]
    assert main(["-C", str(tmp_path), "adopt", str(target), "--prefix", "RK", "--json"]) == EXIT_OK
    names = [gain["name"] for gain in json.loads(capsys.readouterr().out)["gains"]]
    assert names, "a project declaring everything would assert nothing here"

    printed = [row for row in rows if row.split()[0] in names]
    assert len(printed) == len(names), (printed, names)
    for row, name in zip(printed, names, strict=False):
        # The label, then a gap, then prose — never the label running into its first word.
        assert row.startswith(f"    {name} "), row
    # And one column for all of them, which is what padding is for: the widest sets it, so a
    # longer label added tomorrow moves every row rather than closing this one's gap.
    # Where the prose starts, measured as the end of *indent, label, gap* rather than by
    # searching for the sentence: its first word appears again further along the line.
    columns = {re.match(r"\s*\S+\s+", row).end() for row in printed}
    assert len(columns) == 1, (columns, printed)


def test_a_field_nothing_parsed_is_unread_and_not_a_fitting_zero(tmp_path, capsys) -> None:
    """RK1345. Measured on an ungoverned `CHANGELOG.md`: 717 lines, 398 recognised, `parsed:
    0`, `changing: 361` — and three rows reading `longest 0 of 120, 0 over`. Nothing was
    measured, and what an adopter reads is that their fields fit.

    `0 over` is the half that misleads: a count of violations over an empty population is
    vacuously true and sits in the column a real one does. The same report tells the two apart
    a row above — `unread nothing in 837 line(s) was read in any shape` — and `govern` answers
    `reading none — <why>` rather than `0`. The gap was the middle case: lines recognised,
    none parsed, so no `unread` row fires and the measures are of an empty set."""
    target = tmp_path / "ROADMAP.md"
    # Recognised as a bullet and refused as an entry — a `why` that is blank does not parse,
    # which is the state that produced this on a real file.
    target.write_text(
        "# Roadmap\n\n## Block A\n\n"
        "- 📋 **RK1** (deps: —) **A symptom plainly long enough to read** — \n",
        encoding="utf-8",
    )
    assert main(["-C", str(tmp_path), "adopt", str(target), "--prefix", "RK"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "nothing parsed as an entry" in printed
    # Every field it did not read is named, and none of them claims a number.
    for field in ("symptom", "why", "line"):
        assert field in printed
        assert f"{field}  longest" not in printed
    # No row claims a length over a population that is empty. The non-goals *header* keeps its
    # `0 over`, and rightly: it says `0 bullet(s)` in the same clause, so the count the verdict
    # is over is named before the verdict — which is the whole difference this task is about.
    assert "longest 0 of" not in printed
    assert "0 bullet(s), 0 unread, 0 over" in printed

    assert main(["-C", str(tmp_path), "adopt", str(target), "--prefix", "RK", "--json"]) == EXIT_OK
    measures = json.loads(capsys.readouterr().out)["measures"]
    assert measures, "the limits stay, being what an adopter came to see"
    for one in measures:
        assert one["longest"] is None and one["over"] is None, one
        assert one["limit"], one

    # And where a line does parse, the numbers are back — this narrows a claim, it does not
    # withdraw one.
    target.write_text(
        "# Roadmap\n\n## Block A\n\n"
        "- 📋 **RK1** (deps: —) **A symptom plainly long enough to read** — A reason.\n",
        encoding="utf-8",
    )
    assert main(["-C", str(tmp_path), "adopt", str(target), "--prefix", "RK"]) == EXIT_OK
    assert "longest" in capsys.readouterr().out


LEDGER_LINES = """# Shipped

## Block A — The model

- ✅ **RK1** **A first symptom that is plainly long enough to read** — it landed.
- ✅ **RK2** **A second symptom that is plainly long enough to read** — it landed too.
"""


def test_a_file_that_parses_as_a_ledger_is_read_as_one(tmp_path, capsys) -> None:
    """RK1346. Measured on an ungoverned `CHANGELOG.md`: the backlog grammar reported 0 parsed
    and *361 would change*; `--ledger` reported 361 conform and none changing. The file was
    already conforming, the report priced adopting it at 361 lines of work, and the word
    `ledger` appeared nowhere in it.

    Not a guess — the grammars separate by an order of magnitude. On this repository
    `docs/CHANGELOG.md` reads 843 conform as a ledger and 0 as a backlog, and `docs/ROADMAP.md`
    reads 1 and 0 the other way, so the better reading is a measurement."""
    target = tmp_path / "CHANGELOG.md"
    target.write_text(LEDGER_LINES, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target), "--prefix", "RK"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "read as a ledger" in printed
    assert "2 line(s), 2 conform, 0 would change" in printed

    # A backlog keeps the grammar it is in, so this narrows nothing it should not: the second
    # reading is taken only where the first parsed nothing, and preferred only where it wins.
    roadmap = tmp_path / "ROADMAP.md"
    roadmap.write_text(OUTLINED, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(roadmap), "--prefix", "RK"]) == EXIT_OK
    assert "read as a backlog" in capsys.readouterr().out

    # And the flag is honoured as typed, for the reason `--prefix` is: an override the tool
    # second-guesses is not an override. Read as a backlog because that is what was asked.
    assert main(["-C", str(tmp_path), "adopt", str(roadmap), "--prefix", "RK", "--ledger"]) == EXIT_OK
    assert "read as a ledger" in capsys.readouterr().out


def test_the_reread_covers_the_third_role_and_names_it(tmp_path, capsys) -> None:
    """RK1347. RK1346 re-read only as a ledger, so a rationale file kept the verdict a
    changelog had shed: `adopt IMPROVEMENTS.md` on an ungoverned repository reported *nothing
    in 837 line(s) was read in any shape*, where `--sections` read 51 conforming sections and
    19 paragraphs over a limit. And the header named two roles where there are three, printing
    `read as a backlog` on a run that counted sections.

    Discriminating and not a guess, which is what the retry rests on: measured on that
    repository, `--sections` parses 51 of the rationale file and **0** of the roadmap, the
    changelog and the README."""
    target = tmp_path / "IMPROVEMENTS.md"
    target.write_text(RATIONALE, encoding="utf-8")
    assert main(["-C", str(tmp_path), "adopt", str(target)]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "read as prose" in printed
    assert "section(s)" in printed
    # The verdict the backlog grammar gave, gone: it read nothing and said so.
    assert "was read in any shape" not in printed
