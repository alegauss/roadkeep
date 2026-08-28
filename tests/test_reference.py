"""The generated reference, held against the parser it is generated from (RK1402).

One page per verb family, each a **generated table under prose written once**. The split is
the point: regenerating never edits an argument, and editing an argument never touches a
table — so the half that goes stale cannot be the half nobody is looking at.

What makes that worth doing is the check. A build that quietly published a reference nobody
could see was wrong would be worse than no reference, because a stale page reads exactly like
a current one. So four joins are held here, and each of them has already failed once:

* **Every family has a page, and every page a family.** A module added under `verbs/` is a
  section of the surface with nothing documenting it, and a page whose family was renamed is
  one the build throws on.
* **The component reads keys the payload carries.** This is not hypothetical: the first
  version read `one.path` and `one.turns_on`, which are the *dataclass* field names —
  `payload()` publishes them as `command` and `writes_when`, and the build died on the first
  page it rendered. A component and a payload agreeing is not something either one states.
* **No page retypes a flag into a table.** A hand-written table is a second declaration of the
  schema, which is the whole thing this task removed.
* **The generator runs before both entry points.** A `build` that regenerates and a `dev` that
  does not is a preview showing something no deploy will.

Nothing here runs the build: that is CI's job and `site.yml`'s. These read the declarations,
which is why they are green on a checkout with no `node_modules` in it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from generated import read_by

from roadkeep import commanding, describing
from roadkeep.config import Config

HERE = Path(__file__).resolve().parent.parent
SITE = HERE / "site" / "docs"
PAGES = SITE / "src" / "content" / "docs" / "reference"
COMPONENT = SITE / "src" / "components" / "VerbTable.astro"
GENERATOR = SITE / "scripts" / "commands.mjs"

CONFIG_PAGE = SITE / "src" / "content" / "docs" / "configuration.mdx"
CONFIG_COMPONENT = SITE / "src" / "components" / "ConfigTable.astro"
CONFIG_GENERATOR = SITE / "scripts" / "config.mjs"

#: Where the generator writes, as the component imports it. One string, because a rename that
#: moved only one of the two is a build that reads a file nothing writes.
GENERATED = "commands.generated.json"


def _listing() -> commanding.Listing:
    """The surface this checkout declares — the same call the generator makes over the CLI."""
    return commanding.commands(Config.discover(HERE))


def _families() -> tuple[str, ...]:
    """Every family, in the order the parser declares them, which is dispatch order."""
    return tuple(dict.fromkeys(one.family for one in _listing().commands))


def _page_families() -> dict[str, Path]:
    return {path.stem: path for path in sorted(PAGES.glob("*.mdx"))}


# -- the census: a family with no page, and a page with no family --------------


def test_every_verb_family_has_a_page_and_every_page_a_family():
    """Total both ways. A module added under `verbs/` is a whole section of the command
    surface with nothing documenting it, and a page naming a family the parser no longer has
    is one the component throws on at build time — found by CI, but only after a push."""
    assert _families(), "the walk found no families, so this asserts nothing"
    assert set(_families()) == set(_page_families()), {
        "a family with no page": sorted(set(_families()) - set(_page_families())),
        "a page with no family": sorted(set(_page_families()) - set(_families())),
    }


def test_no_page_declares_an_order_of_its_own():
    """`sidebar.order` was the one fact about a generated page that was typed (RK1414): six
    numbers restating what `build_parser` already declares, each chosen by reading the other
    five, and a gap nobody notices when a family is removed. A number here again is that
    second statement back, and Starlight would take it — silently and in preference."""
    carried = [
        path.name
        for path in _page_families().values()
        if re.search(r"^\s+order:\s*\d+$", path.read_text(encoding="utf-8"), re.M)
    ]
    assert not carried, {"declares its own sidebar order": carried}


def test_the_sidebar_takes_the_reference_order_from_the_payload():
    """The order a reader meets the families in is the order dispatch calls them — writing
    before the gate, adoption last — and it is now read off the same generated file the tables
    come off, so the two cannot be different answers.

    Asserted as the config's own reading rather than by running Astro: this file is green on a
    checkout with no `node_modules`, and what it holds is that the config asks the payload and
    refuses to guess when the payload is not there.
    """
    config = (SITE / "astro.config.mjs").read_text(encoding="utf-8")
    assert GENERATED in config, "the config does not read what the generator wrote"
    assert "autogenerate: { directory: \"reference\"" not in config
    assert re.search(r"slug:\s*`reference/\$\{family\}`", config)
    # Loud where the generated file is missing, for the generator's own reason: an order
    # falling back to alphabetical would read exactly like the derived one.
    assert "throw new Error" in config


# -- the join that already broke: the component and the payload ---------------


def test_the_component_reads_only_keys_the_payload_publishes():
    """The failure this exists for, met once already: the component was written against the
    dataclass field names — `one.path`, `one.turns_on` — and the payload publishes `command`
    and `writes_when`. Two names for one fact, and the build died on the first page.

    The payload is the contract, because it is what crosses out of Python. So a key the
    component reads and `payload()` does not carry is a red here rather than a stack trace in
    a build log.
    """
    published = commanding.payload(_listing())
    one = published["commands"][0]
    component = COMPONENT.read_text(encoding="utf-8")
    assert read_by(component, "one") <= set(one), {
        "the component reads it, the payload has no such key": sorted(
            read_by(component, "one") - set(one)
        )
    }
    argument = one["arguments"][0]
    assert read_by(component, "argument") <= set(argument), {
        "read off an argument, not published": sorted(
            read_by(component, "argument") - set(argument)
        )
    }


def test_the_component_groups_by_the_field_the_payload_carries():
    """`family` is what makes one page one family. It was added to the payload for this, so
    a component filtering on anything else would be grouping by a fact nothing derives."""
    assert "family" in commanding.payload(_listing())["commands"][0]
    assert re.search(r"\.family\s*===\s*family", COMPONENT.read_text(encoding="utf-8"))


# -- nothing is retyped, and nothing can be fallen back to --------------------


def test_no_page_carries_a_table_of_its_own():
    """A hand-written table is a second declaration of the schema — wrong at the first renamed
    flag and silent about it. The tables come off the parser or they are not there."""
    written = {
        path.name: [line for line in path.read_text(encoding="utf-8").splitlines()
                    if line.strip().startswith("|")]
        for path in _page_families().values()
    }
    assert not {name: rows for name, rows in written.items() if rows}


def test_every_page_renders_the_generated_table():
    """Prose alone is a page about a family that never says what it takes, which is the state
    this task started from."""
    for name, path in _page_families().items():
        text = path.read_text(encoding="utf-8")
        assert "VerbTable" in text, name
        assert f'family="{name}"' in text, name


def test_the_generated_file_is_never_committed():
    """A committed copy is what a build quietly falls back to, and the reference it publishes
    is stale in exactly the way nobody can see."""
    ignored = [
        line.strip()
        for line in (SITE / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    # By what generated it and never by directory: `src/data/` also holds the hand-written
    # half of a finding page (RK1403), which ignoring the directory would have left out of
    # the repository entirely.
    assert "src/data/*.generated.json" in ignored
    assert not [one for one in ignored if one.rstrip("/") == "src/data"]


def test_the_generator_runs_before_both_entry_points():
    """A `build` that regenerates and a `dev` that does not is a preview of something no
    deploy will ever show — which is the class of defect a person only finds in production."""
    scripts = json.loads((SITE / "package.json").read_text(encoding="utf-8"))["scripts"]
    assert "node scripts/commands.mjs" in scripts["prebuild"]
    # npm runs `prebuild` before `build` on its own; `dev` is not a lifecycle name npm hooks,
    # so that one has to say so.
    assert "prebuild" in scripts["dev"]


def test_the_generator_asks_the_tool_and_refuses_to_guess():
    """It has one job and one failure mode. Asked and answered, it writes; unable to ask, it
    must stop — because a page rendered from whatever was there before reads exactly like a
    page rendered from the truth."""
    source = GENERATOR.read_text(encoding="utf-8")
    assert "roadkeep.cli" in source
    assert "commands" in source and "--json" in source
    assert GENERATED in source
    assert GENERATED in COMPONENT.read_text(encoding="utf-8")
    # It throws rather than falling back, which is the whole of why it may be trusted.
    assert "throw" in source


@pytest.mark.parametrize("family", sorted(_page_families()))
def test_each_page_says_why_the_family_exists(family):
    """The half generation cannot supply, and most of what a reader came for. A page that was
    only a table would be `--help` with a stylesheet."""
    text = PAGES.joinpath(f"{family}.mdx").read_text(encoding="utf-8")
    prose = text.split("---", 2)[2].replace("import VerbTable", "")
    prose = prose.split("<VerbTable")[0]
    assert len(prose.split()) >= 80, family


# -- the configuration reference, rendered from the read that owns it (RK1404) --


def test_the_config_component_reads_only_keys_that_payload_publishes():
    """`VerbTable`'s failure, one surface over, and the reason this is a second assertion
    rather than a second reading of the first: two components read two payloads, and a name
    that agrees with neither is caught only by asking each of them."""
    published = describing.payload(describing.shape(Config.discover(HERE)))
    component = CONFIG_COMPONENT.read_text(encoding="utf-8")
    assert read_by(component, "key") <= set(published["keys"][0]), {
        "the component reads it, the payload has no such key": sorted(
            read_by(component, "key") - set(published["keys"][0])
        )
    }
    assert read_by(component, "surface") <= set(published), {
        "read off the payload root, not published": sorted(
            read_by(component, "surface") - set(published)
        )
    }
    assert published["fixed"], "nothing is fixed, so the boundary section renders empty"
    # Its own receiver name, because a name that means two payloads is one nothing can hold
    # against either — which is what `one` was doing across both loops here.
    assert read_by(component, "figure") <= set(published["fixed"][0]), {
        "read off a fixed figure, not published": sorted(
            read_by(component, "figure") - set(published["fixed"][0])
        )
    }
    assert read_by(component, "one") <= set(published["keys"][0])


def test_the_page_renders_the_table_rather_than_carrying_one():
    """The keys are what `config` publishes. A page that listed them would be the third copy
    of a set the parser already refuses by — which is what this task exists to not write."""
    text = CONFIG_PAGE.read_text(encoding="utf-8")
    assert "<ConfigTable" in text
    assert not [line for line in text.splitlines() if line.strip().startswith("|")]


def test_the_page_does_not_transcribe_the_configuration_it_points_at():
    """The worked example is this repository's own file, which is provably valid because its
    `docs/` are the conformance fixture. Transcribed here it would be a copy that goes stale;
    linked, it cannot."""
    text = CONFIG_PAGE.read_text(encoding="utf-8")
    assert "blob/main/roadkeep.toml" in text
    # No TOML assignments outside a shell block: a `key = "value"` on this page is the file
    # being copied into it one line at a time.
    fenced = re.sub(r"```.*?```", "", text, flags=re.S)
    assert not re.findall(r'^\s*\w+ = ["\[]', fenced, re.M)


def test_the_page_says_a_number_is_measured_and_recommends_none():
    """`[limits]` and `[budgets]` hold judgements measured against a corpus, and `govern`
    refuses one this corpus already breaks. A page that printed a suggested value would be the
    thing somebody copies instead of measuring — which is the whole failure mode."""
    text = CONFIG_PAGE.read_text(encoding="utf-8")
    assert "adopt" in text and "govern" in text
    assert "does not recommend a value" in text


def test_the_config_generator_refuses_a_tree_with_no_configuration():
    """Answered against an unconfigured tree every row reads as undeclared, and the worked
    example silently becomes a list of defaults — a page that is wrong in the one way nothing
    on it would show."""
    source = CONFIG_GENERATOR.read_text(encoding="utf-8")
    assert "no roadkeep.toml" in source
    assert "throw new Error" in source


def test_the_configuration_page_is_reachable_before_the_reference():
    """It is the read an adopter needs first: what the file they are about to write may say,
    which comes before what any verb takes."""
    config = (SITE / "astro.config.mjs").read_text(encoding="utf-8")
    at_config = config.index('label: "Configuration"')
    at_reference = config.index('label: "Reference"')
    assert at_config < at_reference
    assert 'link: "/configuration/"' in config


def test_all_three_generators_run_before_the_build():
    scripts = json.loads((SITE / "package.json").read_text(encoding="utf-8"))["scripts"]
    for name in ("commands", "findings", "config"):
        assert f"scripts/{name}.mjs" in scripts["prebuild"], name
