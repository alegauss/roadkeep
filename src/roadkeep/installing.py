"""Wiring a project that runs this tool from a checkout instead of from the plugin (RK100).

`init` scaffolds the format — the config and the files it declares. What it does *not*
scaffold is the harness: the server that offers the tools, the hook that denies the
hand-edit, and the skill that says which command to call. Those ride with the plugin, and a
project can only install the plugin from a marketplace — which means the published ref, not
the sibling checkout an early adopter is developing against. Measured on the first one: five
hand-written surfaces against three scaffolded ones, and a copy of `SKILL.md` with a comment
saying where it came from, which nothing keeps in step with the file it was taken from.

**Every byte written here is a translation of what the plugin already ships**, never a second
statement of it. The hook events, their matcher and their timeouts are read out of
`hooks/hooks.json`; the server argv out of `.claude-plugin/mcp.json`; the skill is copied with
one sentence re-addressed; the workflow names the action this repository publishes. The one
thing substituted is where the launcher is — `${CLAUDE_PLUGIN_ROOT}` becomes the path from the
adopting project to the checkout that is answering, which is the only fact the plugin's own
files cannot hold, and the skill's own entry point is the fourth place it is written (RK137).
So a matcher added to the plugin reaches every installed project on its next `install`, and
this module has no opinion to disagree with.

Three surfaces, three different rules about re-running, because they are three different
kinds of file:

* **The skill is a copy, so it is refreshed** — always, unasked. It is the whole defect: a
  vendored authority that drifts is worse than none, because it is read with the same trust.
  Which is also why its entry-point sentence is re-addressed rather than copied (RK137): a
  copy that is faithful in every byte and names a command that does not exist here is read
  with that same trust, and the failure arrives in the shell an agent fell back to. **The
  skill is three files now** (RK1437) — an orientation and the two reference pages it points
  at — and they are one surface for every rule here: an orientation naming a page an adopter
  has not got fails by returning nothing, which is quieter than any drift.
* **`.mcp.json` and `.claude/settings.json` are declarations**, and other tools declare in
  them too. Only this project's entry is re-derived — the launcher path is the part that
  moves — and everything else in the file is carried through untouched. An existing file that
  is not a JSON object is refused rather than replaced: it is somebody's configuration.
* **The CI workflow is created once and then the adopter's.** It takes a `baseline:` and a
  `directory:` this command cannot know it wants, so refreshing it would overwrite the one
  thing an adopting repository actually tunes.

`--check` is what makes the first rule mean anything: it reports what `install` would change
and exits non-zero, so the copy is held in step by a gate rather than by whoever remembers.

**And there is a way out** (RK138). An early adopter develops against a checkout and switches
to the plugin once it is installable, and the second half of that had no verb: three surfaces
were removed with `rm`, safe only because `install` had created all three. `uninstall` is the
inverse under the same two rules — the declarations keep everything that is not this project's
entry, and a file that is not a JSON object is refused rather than rewritten — and it reads no
checkout, recognising the wiring by the server's name and the launcher a hook runs, because
the tree that was wired in is usually gone by then. The CI workflow is the one surface it
keeps: that gate calls the published action, not the checkout, so un-wiring the write path
does not un-gate the repository.

**The one tree that is not an adopter is this one** (RK235). Run at the plugin's own root the
two declarations still mean what they mean — point a session at this checkout's tools and its
guard, which this repository declares by hand (RK81) — and the two copies do not: a vendored
`SKILL.md` beside the `skills/` one it was read from is the drift this command exists to
remove, and a second workflow beside the one already gating the tree runs the same lint twice.
So they are named as unwritten instead, and `--check` at that root reports drift rather than a
category error. `uninstall` has no such narrowing and refuses outright, the entries there
being the tree's own rather than a copy of somebody's wiring.

Two more surfaces are named rather than written, which is not the same as being left out.
A line in `CONTRIBUTING.md` telling a contributor not to hand-edit the governed files is prose
about a project's own contribution policy, and this tool does not write prose (L4). The **merge
driver** (RK120) is configuration, so it stays opt-in — but being opt-in is no reason to be
unmentioned (RK148): it is named in the report, and `--register-merge` writes the
`.gitattributes` half for a caller that asks while the `git config` half is printed, that one
being a write outside the files this tool was given (L2).
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep.adopting import BlockedParent, blocking
from roadkeep.config import CONFIG_NAME, Config
from roadkeep.linting import lint
from roadkeep.merging import ATTRIBUTES, Registration, register
from roadkeep.provenance import Engine, Installed, engine, home, installed
from roadkeep.provenance import invocation, stated_at

#: The server's name, which is also the prefix an agent reads on every tool it offers.
SERVER = "roadkeep"

#: What the plugin ships, relative to its root. Read, never rewritten: these four are the
#: source this command translates, and a fifth would be a decision this module invented.
LAUNCHER = "scripts/roadkeep.py"
PLUGIN_HOOKS = "hooks/hooks.json"
PLUGIN_MCP = ".claude-plugin/mcp.json"
PLUGIN_SKILL = "skills/roadkeep/SKILL.md"
PLUGIN_MANIFEST = ".claude-plugin/plugin.json"
#: The two pages the skill points at instead of holding (RK1437). Named here rather than
#: globbed off the directory: what the plugin carries is a declaration, and a page somebody
#: dropped beside the skill is not a surface this command installs. They are copied verbatim
#: — the one substituted fact lives in the entry-point sentence, which is `SKILL.md`'s.
PLUGIN_PAGES = ("skills/roadkeep/writing.md", "skills/roadkeep/asking.md")
#: The self-locating bridge, for the environment that installs no plugin and has no checkout
#: to point at (RK1108). Copied rather than translated: it is a program and not a declaration,
#: and the one fact `install` substitutes elsewhere — where the engine is — is the question
#: this file exists to answer at runtime.
PLUGIN_BRIDGE = "hooks/roadkeep-launch.py"

#: The set together, which is both what a tree must carry to be translated *from* and what
#: says a tree is the plugin rather than an adopter of it (RK235). One list, so the two
#: questions cannot come to disagree about what carrying the plugin means — and the skill's
#: two pages are in it because a skill missing half of itself is a tree that cannot be
#: translated, not a tree with an optional extra (RK1437).
CARRIED = (LAUNCHER, PLUGIN_HOOKS, PLUGIN_MCP, PLUGIN_SKILL, *PLUGIN_PAGES, PLUGIN_MANIFEST)

#: Where each lands in the adopting project. The skill path is the loader's convention —
#: `.claude/skills/<name>/SKILL.md` — and the workflow is a file of its own rather than a job
#: spliced into an existing one: merging YAML would need a parser this tool does not have,
#: and a job appended to somebody's pipeline is an edit to a file they own.
PROJECT_MCP = ".mcp.json"
PROJECT_SETTINGS = ".claude/settings.json"
PROJECT_SKILL = ".claude/skills/roadkeep/SKILL.md"
#: The pages beside it, derived from :data:`PLUGIN_PAGES` so the two lists cannot drift into
#: naming different files: the loader reads a skill's directory, so a page lands where the
#: skill points at it and nowhere else.
PROJECT_PAGES = tuple(
    f"{PROJECT_SKILL.rsplit('/', 1)[0]}/{page.rsplit('/', 1)[1]}" for page in PLUGIN_PAGES
)
PROJECT_WORKFLOW = ".github/workflows/roadkeep.yml"
#: Where the bridge lands, beside the hooks that run it (RK1108). Inside the repository on
#: purpose: the environment it exists for reads what is committed and nothing else, so a path
#: pointing anywhere outside would be a path that resolves on one machine.
PROJECT_BRIDGE = ".claude/hooks/roadkeep-launch.py"

#: Where a **vendored** engine lands (RK1193). Inside the project so the path a declaration
#: names is stable across machines, and git-ignored so it stays an artefact: the tree is a
#: copy of somebody else's repository, and committing it would make every `/plugin update` a
#: diff in this one. The name is the `node_modules` shape both adopters converged on.
PROJECT_ENGINE = ".roadkeep"
#: The environment variable the launcher resolves first, which is how a vendored copy is
#: *pinned* rather than merely present: resolution order alone would still prefer it only
#: where nothing earlier answered, and pinning is the whole point.
ENGINE_HOME = "ROADKEEP_HOME"
#: The one way a **working checkout** becomes eligible to be vendored (RK1193). Named rather
#: than inferred, because the case that costs an hour is a checkout mid-refactor: it answers a
#: version, imports halfway, and is exactly what a pinned copy exists to stop being.
ENGINE_SOURCE = "ROADKEEP_SRC"

#: The directory whose presence decides whether the workflow is written. A repository with no
#: workflows has not asked for CI, and a scaffold that leaves a file nobody runs is litter.
WORKFLOWS = ".github/workflows"

#: The placeholder the harness defines for a plugin-provided config, and the two spellings of
#: the one it defines for a project's own. The `:-.` fallback is what the MCP declaration is
#: written with here and in the first adopting project; a hook always runs with the variable
#: set, so its command carries the bare form.
PLUGIN_ROOT = "${CLAUDE_PLUGIN_ROOT}"
PROJECT_DIR = "${CLAUDE_PROJECT_DIR}"
PROJECT_DIR_OR_CWD = "${CLAUDE_PROJECT_DIR:-.}"

#: The sentence in the shipped skill that names the entry point, matched rather than located
#: by line (RK137). Written as the two ends of it with anything between, so re-wrapping the
#: paragraph — which is prose somebody edits — does not silently stop the substitution: what
#: stops it is a refusal.
_ENTRY_RE = re.compile(
    r"`roadkeep` is the installed entry point.*?not on PATH\.", re.DOTALL
)

#: The ref the generated workflow calls the action at. `main` and not the version, because
#: the project reaching for this command is by definition running an unreleased checkout —
#: an adopter that has pinned a release edits one line, which is the file's own from then on.
ACTION_REF = "main"

#: The fifth surface: opt-in, and until RK148 unmentioned. RK120 shipped the merge driver as
#: configuration (L6) — right — but an adopter read a report naming four surfaces and a
#: `CONTRIBUTING.md` line and was never told a driver exists, so the failure landed later and
#: looked like the tool's: two branches spend one id, git writes conflict markers into the
#: roadmap, and the resolution is the hand edit the guard denies.
#: A template and not a string, because the invocation is a fact about the machine reading it
#: and this is a module constant (RK256): resolved at import, it would answer for whatever the
#: working directory was then rather than for the report being printed.
MERGE = (
    ".gitattributes: `{invocation} merge --register` wires the merge driver for the governed "
    "files, so two branches appending under one heading is two additions and not a conflict "
    "— opt-in configuration, and `install --register-merge` runs it here"
)

#: The same line where that file cannot be written at all (RK394). `not written` is the honest
#: half of the report and it names a remedy on every run; a remedy that exits 2 is a different
#: entry from one the caller simply has not chosen yet, so it says which this is and stops
#: advertising the flag.
MERGE_BLOCKED = (
    ".gitattributes: {blocker} is in the way, so the merge driver cannot be wired here at "
    "all — `install --register-merge` would refuse, and moving that is what comes first"
)

#: And the third state (RK1387), by :data:`MERGE_BLOCKED`'s own argument one step further: an
#: opt-in already taken is a different entry from one nobody has chosen yet, so it says which
#: and stops advertising a flag whose whole answer would be four lines already there.
#:
#: Read back rather than assumed, which is the defect: this row stated what `install` does not
#: write and never asked whether anything else had — so `merge --check` answered *4 of 4
#: governed files routed* while this one offered to wire them, two reads of one tree.
#:
#: The **attribute** half only. Whether git can run what it finds is per clone and is what
#: `merge --check` exists to say, so quoting it here would be the second answer this closes.
MERGE_WIRED = (
    ".gitattributes: the attribute half is written and the governed files route to the merge "
    "driver, so there is nothing here for `install --register-merge` to write — whether this "
    "clone holds the config to run them is `{invocation} merge --check`"
)

#: What the two *copies* become when the tree being wired is the tree answering (RK235). Not
#: a refusal: the declarations still mean what they mean at this root — this repository wires
#: itself to its own checkout by hand and a test holds that (RK81) — and what would be wrong
#: is vendoring a second copy of a file already in the tree, and a second workflow beside the
#: one already gating it. Named rather than silently absent, on the rule every skipped surface
#: here follows: an adopter discovers a silent absence by needing it.
_OWN_SKILL = (
    f"this tree ships {PLUGIN_SKILL}, so a copy of it here would be the drift `install` "
    f"exists to remove — a session in this checkout reads the original"
)
#: The same sentence about the pages the skill points at (RK1437). One row and not two,
#: because they are skipped for one reason and an adopter reading three near-identical
#: lines learns no more than from one that names both files.
_OWN_PAGES = (
    f"{' and '.join(PLUGIN_PAGES)} ship with it, and are read from the same original"
)
#: The third member of that set, and the one that was missing from it (RK402). A tree that
#: ships the guard as a **plugin** — `hooks/hooks.json`, declared by `.claude-plugin/plugin.json`
#: — already runs it, so writing the same hooks into `.claude/settings.json` would run the
#: guard twice on every turn. `install --check` reported `1 surface(s) differ` here
#: permanently, and a check that can never report clean is one nobody reads: the drift it
#: exists to catch arrives inside a report that already said the same thing yesterday.
_OWN_HOOKS = (
    f"this tree declares the guard as a plugin in {PLUGIN_MANIFEST} ({PLUGIN_HOOKS}), so "
    f"writing the same hooks here would run it twice on every turn"
)
_OWN_WORKFLOW = (
    "this tree *is* the action, and its own workflow already calls the gate — a second one "
    "would run the same lint twice"
)
#: The fourth of that set (RK1108). Same reasoning as the skill's, one file over: a tree that
#: ships the bridge does not vendor a copy of it beside the original.
_OWN_BRIDGE = (
    f"this tree ships {PLUGIN_BRIDGE}, and a session here reaches the engine directly — a "
    f"copy of the bridge beside the original is the drift `install` exists to remove"
)

#: The surface this command names and does not write (L4), and why. Printed by `install`.
CONTRIBUTING = (
    "CONTRIBUTING.md: one line telling a contributor the governed files are written by "
    "`roadkeep` and not by hand — prose about your project, so this command leaves it to you"
)


class NotShipped(ValueError):
    """The running copy of this package carries no plugin surfaces to translate.

    An installed wheel is `roadkeep/` alone: the hook declaration, the server declaration and
    the skill live beside `src/` in the repository, not inside the package. That is not worth
    fixing by shipping a second copy of them as package data — a copy is the defect this
    command exists to remove. The answer for a wheel is the plugin, which carries all three.
    """

    def __init__(self, root: Path, missing: tuple[str, ...]) -> None:
        self.root = root
        self.missing = missing
        super().__init__(
            f"{root} does not carry the surfaces the plugin ships and nothing was written "
            f"(missing: {', '.join(missing)}) — `install` translates a checkout of roadkeep "
            f"for a project beside it; an installed copy has none to translate, and "
            f"`/plugin install roadkeep@alegauss` is the route that carries them"
        )


class Unanchored(ValueError):
    """The shipped skill no longer spells the sentence the launcher is substituted into.

    A refusal and not a verbatim copy (RK137): the copy would then tell an adopting project
    to run a command that does not exist there, which is the whole defect `install` removes.
    Reached only by editing `SKILL.md`, and the repair is in that file — so it names it.
    """

    def __init__(self, path: Path, found: int) -> None:
        self.path = path
        self.found = found
        super().__init__(
            f"{path} states the entry point {found} time(s) and nothing was written: "
            f"`install` re-addresses that one sentence for a project wired to a checkout, "
            f"and a copy carrying `roadkeep` where the package is not installed names a "
            f"command that fails"
        )


class NotAnAdopter(ValueError):
    """The tree asked about is the plugin, and there is no installation of it to withdraw.

    `install` handles this root by *narrowing* what it writes (RK235) — the two declarations
    are this repository's own conformance (RK81) and stay. Un-wiring is the direction with no
    such reading: the entries here are not a copy of somebody else's wiring, they are the file
    the tree carries, and taking them out would un-wire the tool from itself.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        super().__init__(
            f"{root} ships the plugin rather than adopting it, and nothing was taken out: "
            f"the server and guard declared here point a session at this checkout on "
            f"purpose — `git checkout` is what reverts that, and `uninstall` is for a "
            f"project `install` wired"
        )


class Unreadable(ValueError):
    """An existing declaration this command would have to merge into and cannot parse."""

    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        super().__init__(
            f"{path} is not a JSON object and nothing was written ({reason}): this command "
            f"merges its own entry into that file and never replaces one somebody wrote"
        )


@dataclass(frozen=True, slots=True)
class Surface:
    """One file this command owns a part of, and what running it would do to that file."""

    path: Path
    text: str
    #: False for the workflow, which is the adopter's after the first write. The distinction
    #: is the whole re-run contract, so it is a field rather than a check at the call site.
    refresh: bool
    existed: bool
    stale: bool

    @property
    def state(self) -> str:
        if not self.existed:
            return "created"
        if not self.stale:
            return "unchanged"
        return "updated" if self.refresh else "kept"

    @property
    def writes(self) -> bool:
        return self.state in ("created", "updated")


@dataclass(frozen=True, slots=True)
class Plan:
    """What `install` would write, computed before a byte reaches disk (all-or-nothing)."""

    root: Path
    #: The checkout being wired in — the tree whose `scripts/roadkeep.py` the hook will run.
    source: Path
    #: That launcher, exactly as the declarations spell it.
    launcher: str
    surfaces: tuple[Surface, ...]
    #: Paths not written, each with the reason — the report's other half. A surface that is
    #: silently absent is one the adopter discovers is absent by needing it.
    skipped: tuple[tuple[str, str], ...] = ()
    #: What this project's own gate reports today, or None where it could not be run (RK140).
    #: It decides which workflow is written, and it is on the plan because a decision taken
    #: from a measurement the report does not state is one the adopter cannot check.
    debt: int | None = None
    #: The version that wrote these surfaces where it is **newer** than the engine answering,
    #: or `""` (RK1462). On the plan and not decided at the write, because `--check` is the
    #: same computation and this is the half that says which way the write would go.
    ahead: str = ""
    #: Whether this project has **no** record of which engine wrote its surfaces (RK1485).
    #: The population RK1462 could not reach: the record arrives on the next `install`, and
    #: the next `install` is the write being guarded against — so on the tree that needs the
    #: guard most it is inert until somebody makes the very edit it exists to refuse. Not the
    #: complement of :attr:`ahead`: that field says *the surfaces are newer*, and this says
    #: *nothing here establishes a direction*, which is the honest state and a different one.
    #:
    #: False on a project with nothing wired at all — there is no surface whose provenance
    #: could be unknown, and a row about a record that would govern nothing is noise.
    unrecorded: bool = False
    #: Whether the write recorded `[install] wired` — a fifth file this command touches, so it
    #: is answered rather than assumed (RK298). False on every `--check`, which writes nothing.
    recorded: bool = False
    #: The merge driver, where `--register-merge` asked for it (RK148) — the attribute lines
    #: written and the `git config` line to run, exactly as `merge --register` reports them.
    registered: Registration | None = None
    #: Surfaces that would be written and cannot be, each with the ancestor standing in the
    #: way (RK393). RK392's question one command over: `exists` says whether a write would
    #: clobber, and this says whether it can happen — a `.claude` that is a file left the
    #: server declaration on disk with no hook and no skill beside it. On the plan and not
    #: raised here, because `--check` writes nothing and still has to report it: its whole
    #: job is naming the remedy, and `install` was the remedy it named and could not do.
    blocked: tuple[tuple[Path, Path], ...] = ()
    #: Which variant this plan is (RK1108), and whether the flag or the disk said so (RK1113).
    #: On the plan because the launcher alone does not say *why* it is that path, and a reader
    #: of a report that names no flag has to be able to tell a project wired to the bridge
    #: from one this run is about to move there.
    committed: bool = False
    #: True where :func:`_carrying` answered it rather than the caller (RK1113).
    carried: bool = False
    #: What is standing in the way of `.gitattributes`, where anything is (RK394). Its own
    #: field and not a row in :attr:`blocked`, because the driver is not one of the surfaces:
    #: it is written after the loop, by `--register-merge` alone, and the report names it on
    #: every run whether or not the flag was given — so this answers two questions, whether
    #: the write can happen and whether the sentence advertising it is true.
    driver: Path | None = None

    @property
    def changing(self) -> tuple[Surface, ...]:
        return tuple(surface for surface in self.surfaces if surface.writes)

    def stated(self, checked: bool) -> str:
        """Every surface and what this run did — or would do — to it (RK100, RK393).

        Beside :meth:`payload` since RK1170. `checked` is the caller's and not a field: the
        plan is the same computation either way, which is what makes `--check` a check of the
        thing that runs, and only the **tense** of the report differs.
        """
        # The **project** heads it, which is the reader's first question on a write: every row
        # under this one names a file in that tree, and the header used to name the engine's
        # instead (RK1359). Measured on a reader: running `install -C <elsewhere>` from a
        # neutral directory, the header read as *this is where it wrote*, and two commands went
        # by before listing the filesystem showed the files in the target and `-C` honoured.
        #
        # The engine only where it is a **different** tree, because the two collapse in the
        # checkout that ships this package and a second identical path is a line that says
        # nothing. They differ for an adopter, which is who `install` is for: the launcher a
        # hook runs months later lives in the engine's tree, so which one that is stays worth
        # a row — beside the project rather than in its place.
        rows = [f"{self.root.as_posix()}  →  {self.launcher}"]
        if self.source != self.root:
            rows.append(
                f"  engine         {self.source.as_posix()} — the checkout that launcher "
                f"runs from, which is not this project"
            )
        if self.carried:
            # Said because the header alone does not (RK1113): the launcher is a path, and a
            # reader who passed no flag has to be told the path came from their own project
            # rather than from a default that is about to overwrite it.
            rows.append(
                f"  committed      this project already runs {PROJECT_BRIDGE}, so the "
                f"wiring stays on it — `uninstall` then `install` moves it to a checkout"
            )
        if self.unrecorded:
            # Above the surfaces for `ahead`'s reason and before it, because it qualifies that
            # row's absence rather than the rows below: *not ahead* on a project that recorded
            # nothing is *not known to be ahead*, and the reader deciding whether to run this
            # is the one who has to be told which of the two they are looking at.
            rows.append(
                f"  record         none — nothing here says which engine wrote these "
                f"surfaces, so a refresh cannot be told from a downgrade; `install` writes "
                f"that record, and this report is what to read before it does"
            )
        if self.ahead:
            # Above the surfaces, because it changes what every `updated` under it means
            # (RK1462): the bytes on disk came from a newer engine, so the word is *downgrade*,
            # and the report says which way the write goes before it lists the files.
            rows.append(
                f"  ahead          written by {self.ahead} and the engine here is "
                f"{writing_from(self.source)}, so a rewrite is a downgrade — `install --vendor` moves "
                f"the engine, `uninstall` then `install` says it out loud"
            )
        for surface in self.surfaces:
            # `--check` writes nothing, so it reports in the conditional: the same three words
            # in the past tense would claim a file changed that did not.
            state = _WOULD[surface.state] if checked else surface.state
            rows.append(f"  {state:<14} {surface.path.relative_to(self.root).as_posix()}")
        if self.registered is not None:
            # The same lines `merge --register` prints, because it is the same write (RK148) —
            # and now literally the same rendering (RK276), so a field added to `Registration`
            # cannot reach one surface and miss the other. The `git config` half is still
            # printed and not run.
            from roadkeep.rendering import registration_report  # noqa: PLC0415 - RK260

            rows += registration_report(
                self.registered, self.registered.attributes.name, 14
            )
        if self.debt:
            # Beside the surfaces, because it is the reason one of them was written the way it
            # was (RK140): a decision taken from a measurement nobody is shown is one the
            # adopter cannot check.
            rows.append(
                f"  baselined      {self.debt} standing finding(s) here, so the workflow "
                f"fails on what a branch adds — drop the line once `lint` exits 0"
            )
        # One label for every surface this command does not write, because they are not one
        # kind: `CONTRIBUTING.md` is the author's, the driver is a flag away, and the two at
        # the plugin's own root are files the tree already ships (RK235). "by hand" said all
        # three, and on the last two it told the reader to write them.
        rows += [f"  not written    {why}" for _, why in self.skipped]
        # Beside the surfaces and before the verdict (RK393): this one is not a difference
        # `install` closes, and saying so is the whole repair. The remedy named is the blocker,
        # because that is the file somebody has to move.
        rows += [
            f"  blocked        {path.relative_to(self.root).as_posix()}: "
            f"{parent.relative_to(self.root).as_posix()} is a file, "
            f"so the directory cannot be made"
            for path, parent in self.blocked
        ]
        if self.recorded:
            # The fifth file (RK1462, RK298): a command whose contract is *every surface or
            # none* does not touch a sixth silently, and this row is what the next check reads.
            rows.append(
                f"  recorded       {CONFIG_NAME}: [install] wired = "
                f"{writing_from(self.source)} — which tells the next check which side is newer"
            )
        if not checked:
            rows += [f"  from here      {one}" for one in self.orientation()]
        return "\n".join(rows)

    def orientation(self) -> list[str]:
        """What the surfaces above now let a session do, on the write that wires them (RK1438).

        This report is an accurate account of **files** and says nothing about the tool they
        install. For an agent that output is often the first contact and the first refusal is
        the second; the skill is the third, arrives on a later turn, and is long enough to be
        skimmed — RK1424 measured it and RK1437 split it for that reason. So the two surfaces a
        session reliably reads were the two saying least about the shape of the thing.

        **Not more documentation** — the smallest useful part of it, where somebody is already
        looking. Five lines: which files stopped being hand-editable, the verbs a day actually
        uses, the gate, the two reads that save a refusal, and the check a CI job runs, which
        was discoverable from `--help` alone.

        **On the write and never on `--check`** (`checked` is the caller's, as everywhere in
        this report). An adopter runs the write once and reads it; the check runs in CI on
        every push, and an orientation printed there is five lines nobody reads, every time.

        **The sentences and not the rows** (RK1447). The label and its column are a terminal's,
        so they are :meth:`stated`'s to add; what is here is what both registers carry. The
        payload publishes these strings rather than facts behind them, which is this report's
        own idiom one key over — `skipped` publishes the reason a surface was not written as
        the sentence a reader gets — and a taxonomy invented to structure five lines would be a
        second grammar for something no caller asked to branch on.
        """
        say = invocation()
        return [
            "the files `roadkeep.toml` declares are the tool's now — the guard denies a hand "
            "edit and answers with the verb that makes it",
            f"`{say} brief` picks the next line and briefs it; `{say} add` files one, and "
            f"`{say} ship <id> --why \"…\"` closes it in all three files",
            f"`{say} lint` is the gate, and `{say} repair` spends a whole report of findings "
            f"in one call",
            f"`{say} budget` prices a field before the sentence exists and `{say} show <id>` "
            f"reads a line back, so the refusal is one you never meet",
            f"`{say} install --check` is what a CI job or a pre-commit hook runs to keep the "
            f"copies here in step with the checkout they came from",
        ]

    def verdict(self) -> list[str]:
        """What a `--check` has to say on **stderr**, where anything is (RK393).

        Two sentences and not one, because they are two states: a surface that differs is one
        `install` writes; a surface that is blocked is one it exits 2 on, and a gate whose
        named remedy is a red command sends a CI job round a loop.

        Its own method rather than the tail of :meth:`stated` (RK1170): these go to a different
        stream, and a register that mixed the two would put the verdict into the file a reader
        redirects stdout into.
        """
        if not self.changing:
            return []
        blocked = {path for path, _ in self.blocked}
        differing = [one for one in self.changing if one.path not in blocked]
        rows = []
        if differing:
            # And which way (RK1462). The sentence named one command in one direction, so a
            # project whose surfaces are newer than the engine answering was handed the write
            # that deletes them — in the vocabulary of an update, once a session, until
            # somebody took it. `install` refuses there, and this says so before they run it.
            rows.append(
                f"{len(differing)} surface(s) differ from what this checkout ships: "
                + (
                    f"they were written by {self.ahead} and this engine is "
                    f"{writing_from(self.source)}, so `{invocation()} install` refuses — `install "
                    f"--vendor` moves the engine forward"
                    if self.ahead
                    else f"`{invocation()} install` writes them"
                )
            )
        if self.blocked:
            rows.append(
                f"{len(self.blocked)} surface(s) cannot be written at all: "
                f"move what is standing in the directory first, and `{invocation()} "
                f"install` will not run until you do"
            )
        return rows

    def payload(self, checked: bool) -> dict[str, object]:
        """The same answer as data, with every state a reader might act on."""
        return {
            "root": self.root.as_posix(),
            "source": self.source.as_posix(),
            "launcher": self.launcher,
            # RK1113: which variant, and whether the project said so rather than the flag. Two
            # keys, because a reader deciding whether to pass `--committed` needs the second
            # one — with `carried` true, passing it changes nothing.
            "committed": self.committed,
            "carried": self.carried,
            "checked": checked,
            "debt": self.debt,
            # Which side is newer (RK1462): the version that wrote these surfaces where it is
            # ahead of the engine answering, and null where it is not — so a consumer tells a
            # refresh from a downgrade without reading the sentence. `recorded` is the fifth
            # file this write touches, said for the reason every staged path is (RK298).
            "ahead": self.ahead or None,
            # And whether a direction is established at all (RK1485). Beside `ahead` and not
            # folded into it: `null` there says *not ahead*, and on a project that recorded
            # nothing that is *not known to be ahead* — two states a consumer branching on one
            # key cannot tell apart, which is the guess this whole task is about.
            "unrecorded": self.unrecorded,
            "recorded": self.recorded,
            "surfaces": [
                {
                    "path": surface.path.relative_to(self.root).as_posix(),
                    "state": surface.state,
                    "writes": surface.writes,
                }
                for surface in self.surfaces
            ],
            "skipped": [{"path": path, "why": why} for path, why in self.skipped],
            # What the surfaces let a session do (RK1447), off the same method the report
            # prints from. RK1438 put those five lines on stdout and left the payload saying
            # only which files moved — and the caller most likely to run `install --json` is
            # the one wiring a project from a script or a session, which is exactly the reader
            # they were written for. Block C's rule, applied here: both registers come off one
            # record, because a printer and a payload builder agreeing by hand is how an agent
            # comes to be told less than the person at the terminal.
            #
            # **Empty under `--check` and never absent**, which is the `driver` key's rule for
            # its reason: the register split is deliberate — CI runs the check on every push —
            # and a reader has to tell "nothing was wired here" from "this payload predates
            # the field".
            "orientation": [] if checked else self.orientation(),
            "registered": None
            if self.registered is None
            else {
                "attributes": self.registered.attributes.as_posix(),
                "added": list(self.registered.added),
                "present": list(self.registered.present),
                "command": self.registered.command,
                "invalidated_by": self.registered.invalidated_by,
                "wiring": None
                if self.registered.wiring is None
                else {
                    "attributes": self.registered.wiring.attributes.state,
                    "driver": self.registered.wiring.driver.state,
                },
                # Keyed by the field names of `Registration`, and held to them by a test
                # (RK276): the reading most likely to be automated is the one a dropped field
                # is quietest in.
                "left_alone": [list(pair) for pair in self.registered.left_alone],
            },
            "changing": len(self.changing),
            # RK393: the surfaces `install` cannot write, each with the file standing in the
            # way. Its own key and not folded into `changing`, because a reader acting on that
            # number would run the command this one says will not run.
            "blocked": [
                {
                    "path": path.relative_to(self.root).as_posix(),
                    "blocked_by": parent.relative_to(self.root).as_posix(),
                }
                for path, parent in self.blocked
            ],
            # RK394: what stands in the way of the driver's own file, where anything does. Null
            # and not absent when nothing does, so a reader tells "checked and clear" from
            # "this payload predates the field".
            "driver": None
            if self.driver is None
            else self.driver.relative_to(self.root).as_posix(),
        }


#: `install --check` reports the same four states as a run, in the tense of a run that has not
#: happened. `kept` and `unchanged` are already that tense: neither describes a write. Beside
#: the plan since RK1170, the report having moved onto it.
_WOULD = {
    "created": "would create",
    "updated": "would update",
    "unchanged": "unchanged",
    "kept": "kept, yours",
}


def plan(
    root: str | Path = ".",
    *,
    source: str | Path | None = None,
    registering: bool = False,
    gauging: bool = True,
    committed: bool = False,
) -> Plan:
    """Read the plugin's surfaces and the project's, and answer what would change.

    Writes nothing, which is what lets `install` and `install --check` be the same
    computation — a check that ran a different code path would be checking something else.

    ``registering`` only moves the merge driver out of the *unwritten* list (RK148): the
    driver is written by :func:`install`, and a `--check` that registered one would be a
    check that changed the repository.

    ``gauging`` is the one part a caller may decline: :func:`_standing` runs this project's
    whole gate to choose the workflow's default (RK140), and :func:`stale` asks this question
    on every session start (RK234) where the workflow is not in play at all. Declining it
    reports ``debt`` as None, which is the same answer a project that declares nothing gets.

    ``committed`` wires the bridge instead of the checkout (RK1108) — a fourth surface, and the
    launcher every declaration then names. Opt-in and never the default, because it answers a
    different question: the default points at the tree this command is running from, which is
    exact and is what an early adopter developing against a checkout wants; the bridge searches
    at runtime, which is the only thing that can work in an environment holding neither a
    plugin nor a checkout. A project that has both is better served by the exact path.

    Opt-in **for a project that has not chosen yet**, which is the correction RK1113 makes: a
    project already wired to the bridge has chosen, on disk, and the flag is not where that
    answer lives. Without the flag this reads :func:`_carrying` and keeps the variant it finds,
    so `--check` on a `--committed` project reports what actually drifted and the plain
    `install` it names no longer downgrades the wiring. Moving *back* to a checkout path is
    `uninstall` and then `install`, which is the same two commands as any other change of mind
    about a variant — and unlike a flag, it cannot happen by running the repair a check named.
    """
    base = Path(root).resolve()
    # A project that vendored an engine has **chosen** one, on disk, and a plan that read the
    # running checkout instead would offer to re-point every declaration at it — undoing the
    # pin, in the vocabulary of a refresh. `_carrying`'s rule one variant over (RK1113), and
    # the half RK1464 leaves without it: the run that vendors is clean and the `--check` that
    # follows is not. The caller's `--source` still wins, being an answer they gave.
    origin = (
        Path(source).resolve()
        if source is not None
        else (_pinned_engine(base) or _source())
    )
    carried = not committed and _carrying(base)
    committed = committed or carried
    _carried(origin, committed=committed)

    # Addressed from the project and not from the checkout, which is the whole point: the file
    # is committed, so the path resolves on every machine that clones the repository (RK1108).
    launcher = PROJECT_BRIDGE if committed else _launcher(base, origin)
    hooks = _hooks(origin, launcher)
    server = _server(origin, launcher)

    # The tree being wired *is* the tree answering (RK235): the two declarations still mean
    # what they mean — point a session at this checkout's tools and its guard, which is what
    # this repository declares by hand (RK81) — and the two copies do not, both being copies
    # of files already in the tree.
    own = base == origin
    surfaces = [
        _declaration(base / PROJECT_MCP, lambda current: _merged_mcp(current, server)),
    ]
    # Conditioned on the tree *providing* the plugin and never on which repository this is
    # (RK402): a fork, a vendored copy and this checkout are the same situation, and a name
    # test would answer for one of them. The `.mcp.json` declaration stays either way — a
    # plugin's server and a project's are two entries the harness reads separately, and only
    # the hooks would fire twice.
    skipped: list[tuple[str, str]] = [(CONTRIBUTING.split(":")[0], CONTRIBUTING)]
    if _provides_plugin(base):
        skipped.insert(0, (PROJECT_SETTINGS, f"{PROJECT_SETTINGS}: {_OWN_HOOKS}"))
    else:
        surfaces.append(
            _declaration(
                base / PROJECT_SETTINGS, lambda current: _merged_settings(current, hooks)
            )
        )
    # A copy and refreshed like the skill, for the skill's reason (RK1108): a vendored program
    # that drifts from the one the plugin ships is read with the same trust and answers with an
    # older rule. Skipped at the plugin's own root, where it would sit beside the file it came
    # from — the narrowing RK235 already makes for the other two copies.
    if committed:
        if own:
            skipped.insert(0, (PROJECT_BRIDGE, f"{PROJECT_BRIDGE}: {_OWN_BRIDGE}"))
        else:
            surfaces.append(_copy(base / PROJECT_BRIDGE, _read(origin / PLUGIN_BRIDGE)))
    driver = blocking(base / ATTRIBUTES)
    if not registering:
        # Three states and no longer two (RK1387). `blocking` answers whether another driver
        # holds the path; `_routed` answers whether ours already does, which is the question
        # this row never asked and `merge --check` has always answered.
        described = (
            MERGE_BLOCKED.format(blocker=driver.name)
            if driver is not None
            else MERGE_WIRED.format(invocation=invocation())
            if _routed(base)
            else MERGE.format(invocation=invocation())
        )
        skipped.insert(0, (described.split(":")[0], described))
    debt = _standing(base) if gauging else None
    if own:
        skipped.insert(0, (PROJECT_SKILL, f"{PROJECT_SKILL}: {_OWN_SKILL}"))
        skipped.insert(1, (PROJECT_PAGES[0], f"{PROJECT_PAGES[0]}: {_OWN_PAGES}"))
    else:
        surfaces.append(
            _copy(base / PROJECT_SKILL, _skill(origin, launcher, committed=committed))
        )
        # The pages the skill points at, copied with it and never separately (RK1437): a
        # vendored orientation naming two files an adopter has not got is worse than one
        # that held the reference, because the miss is a read that silently returns nothing.
        surfaces += [
            _copy(base / landed, _read(origin / page))
            for page, landed in zip(PLUGIN_PAGES, PROJECT_PAGES, strict=True)
        ]
    if own:
        skipped.insert(0, (PROJECT_WORKFLOW, f"{PROJECT_WORKFLOW}: {_OWN_WORKFLOW}"))
    elif (base / WORKFLOWS).is_dir():
        surfaces.append(_once(base / PROJECT_WORKFLOW, _workflow(origin, debt)))
    else:
        skipped.insert(0, (PROJECT_WORKFLOW, f"no {WORKFLOWS}/ — this project has no CI to gate"))
    return Plan(
        root=base,
        source=origin,
        launcher=launcher,
        surfaces=tuple(surfaces),
        skipped=tuple(skipped),
        debt=debt,
        # Read here so `--check` and the write answer from one computation (RK1462): which
        # side is newer is a fact about the project, and a check that did not ask it is the
        # check that offered a downgrade.
        ahead=ahead_of(base, origin),
        # And whether anything establishes a direction at all (RK1485). Asked beside it for
        # the reason above it is: `--check` and the write answer from one computation, and a
        # check that reported *behind* about a project that recorded nothing was stating a
        # direction it had not established.
        unrecorded=not wired_by(base) and any(one.existed for one in surfaces),
        # Over what would be written and never every surface: a directory nobody needs to
        # create is not in anybody's way (RK393).
        blocked=tuple(
            (surface.path, parent)
            for surface in surfaces
            if surface.writes and (parent := blocking(surface.path))
        ),
        # Always, and not only under `--register-merge` (RK394): the report names the flag on
        # every run, so whether running it could work is part of every run's answer.
        driver=driver,
        committed=committed,
        carried=carried,
    )


def install(
    root: str | Path = ".",
    *,
    source: str | Path | None = None,
    register_merge: bool = False,
    committed: bool = False,
) -> Plan:
    """Write every surface that would change, or write nothing.

    The order is `init`'s and for `init`'s reason: everything that can refuse has refused by
    the time the first file is opened, because a project wired for the tools but not for the
    hook is a project that looks governed and is not.

    ``register_merge`` adds the fifth (RK148): the `.gitattributes` half of `merge --register`,
    for a caller that asked. A flag and never a default, because the other half is a line in
    somebody's `git config` — which this command prints and does not run (L2) — and the
    project's own config is resolved *before* the first write, so a project with nothing to
    register refuses instead of leaving four surfaces written and a flag unhonoured.
    """
    intent = plan(root, source=source, registering=register_merge, committed=committed)
    # First of the refusals (RK1462): the surfaces on disk came from an engine this one is
    # behind, so *refresh* means *downgrade* — and the caller asked for it because a check and
    # a finding spoke in one direction. Only where something would actually be rewritten: a
    # project whose files already match is not being downgraded by a run that writes nothing.
    if intent.ahead and any(one.existed for one in intent.changing):
        raise SurfacesAhead(intent.root, intent.ahead, writing_from(intent.source))
    # With the rest of the refusals and above the first write (RK393), which is what the
    # paragraph above claims and the `mkdir` below used to break.
    if intent.blocked:
        raise BlockedParent(intent.blocked, intent.root)
    if register_merge and intent.driver is not None:
        # The config was already resolved up here and the file was not (RK394), so the flag
        # was honoured or not by a write three modules along and after the loop below — four
        # surfaces on disk, the driver unwired, and `--check` green over it.
        raise BlockedParent([(intent.root / ATTRIBUTES, intent.driver)], intent.root)
    governed = _governed(intent.root) if register_merge else None
    for surface in intent.changing:
        surface.path.parent.mkdir(parents=True, exist_ok=True)
        surface.path.write_text(surface.text, encoding="utf-8", newline="")
    # And the record that makes the refusal above possible next time (RK1462), after the
    # writes rather than before them: it says *these surfaces came from this engine*, which is
    # a claim about files that are now on disk.
    # The version that **wrote** them (RK1464), which under `--vendor` is the tree copied in
    # and not this process: a record naming the retiring engine would make the next check
    # refuse the surfaces this run just installed correctly.
    written_down = _recorded(intent.root, writing_from(intent.source))
    if governed is not None:
        intent = replace(intent, registered=register(governed))
    return replace(intent, recorded=written_down)


def declared_launcher(root: Path) -> str:
    """The command this project's own `.mcp.json` runs for the roadkeep server, or `""`.

    **Read and never re-derived** (RK1469). `Engines.invoke` answers *which copy to call*, and
    it did so by restating a resolution order the launcher already holds: `$ROADKEEP_HOME`,
    then `.roadkeep/`, then a sibling checkout, then the cache clone, each probed. It knew the
    middle of that list and neither end, so a project pinning `ROADKEEP_HOME` to a tree outside
    itself was handed a copy that is not the pen — RK1230's own failure, one wiring along.

    The order does not need restating, because the answer is on disk: whatever `install` wrote
    into this file **is** what the harness runs, and where that is the committed bridge the
    order is resolved at the moment it is used, by the file that owns it. So a second statement
    of `_candidates` never appears here, and no subprocess is spent on a read `lint` reaches.

    `""` on a project served by a plugin alone, whose `.mcp.json` declares no such server —
    and on anything unreadable, which is the direction every reader in this module takes.
    """
    try:
        declared = json.loads(_read(root / PROJECT_MCP))["mcpServers"][SERVER]
        argv = [str(declared["command"]), *(str(one) for one in declared["args"])]
    except (OSError, ValueError, KeyError, TypeError):
        return ""
    # Up to the program and no further: the declaration ends in `mcp`, which is the mode the
    # harness wants and the one thing a shell caller is about to replace with a verb. The
    # program is the last argument that is a Python file, which is the one shape every
    # spelling of this declaration has — a launcher, a bridge, or an engine's own script.
    ends = max(
        (n for n, one in enumerate(argv) if one.endswith(".py")), default=len(argv) - 1
    )
    # The two spellings `install` writes, resolved against the tree they address (RK1200's
    # rule, one file over): a command carrying a placeholder is one nobody can paste.
    where = root.as_posix()
    return " ".join(
        one.replace(PROJECT_DIR_OR_CWD, where).replace(PROJECT_DIR, where)
        for one in argv[: ends + 1]
    ).strip()


def wired_by(root: Path) -> str:
    """The engine version that last wrote this project's surfaces, or `""` (RK1462).

    `[install] wired`, read through `Config` so the key is parsed once and refused once — and
    silent on an unreadable project, which is every reader in this module's rule: a record that
    cannot be read is one nobody wrote, and the check then behaves as it did before it existed.
    """
    from roadkeep.config import Config  # noqa: PLC0415 - RK260

    try:
        return Config.discover(root).install_wired
    except Exception:  # noqa: BLE001 - an unreadable tree recorded nothing, to this reader
        return ""


def writing_from(origin: Path) -> str:
    """The version of the tree these surfaces are generated **from** (RK1462, RK1464).

    Read off the tree and not off this process, because the two come apart at exactly the door
    that matters: `install --vendor` copies a newer engine in and then wires the project from
    it, so the copy that writes the bytes is a directory rather than the running package.
    Through :func:`~roadkeep.provenance.stated_at`, which is this package's one reader for
    *what does this directory say it is*.

    Falls back to the running engine, which is every ordinary `install`: the source is the
    checkout answering, and its literal is that version anyway.
    """
    return stated_at(origin / "src" / "roadkeep") or engine().version


def ahead_of(root: Path, origin: Path | None = None) -> str:
    """The version this project's surfaces were written by, where it is **newer** than the
    tree about to write them — or `""` where it is not, or where nothing recorded one (RK1462).

    The comparison `install --check` never made. That one asks whether the bytes differ and
    speaks in one direction — stale, behind, refresh — so a project whose engine is older than
    its surfaces is offered a downgrade in the vocabulary of an update, once a session, until
    somebody takes it. Measured here: the vendored 0.2.4 answered, the committed launcher
    carried RK1446's Windows branch, `install.stale` called it behind, and the repair the
    finding named wrote the pre-fix version back over it.

    Ordered by :func:`_numbered`, which is `install --vendor`'s own comparison and for the same
    reason (RK1193): `0.1.10` sorts under `0.1.9` as text, and two adopting projects got that
    right only by never having a two-digit patch.
    """
    recorded = wired_by(root)
    if not recorded:
        return ""
    # Against the tree that would **write**, not against this process (RK1464): `--vendor`
    # copies a newer engine in and wires the project from it, so comparing with the running
    # copy would call that upgrade a downgrade and refuse the one run that is moving forward.
    writing = engine().version if origin is None else writing_from(origin)
    return recorded if _numbered(recorded) > _numbered(writing) else ""


class SurfacesAhead(ValueError):
    """`install` asked to write a surface a **newer** engine wrote (RK1462).

    A refusal and not a warning, because what the write does is delete a fix: the bytes on disk
    came from an engine this one is behind, so *refresh* means *downgrade* and the caller asked
    for it in the vocabulary of an update.

    Two doors, and neither is a flag on this verb. `install --vendor` moves the **engine**
    forward, which is the direction a project in this state usually wants and the reason that
    command exists. `uninstall` then `install` is the deliberate downgrade, which is already
    how a project changes its mind about a variant (see :func:`plan`) — and unlike a flag, it
    cannot happen by running the repair a check named.
    """

    def __init__(self, root: Path, recorded: str, running: str) -> None:
        self.recorded = recorded
        self.running = running
        super().__init__(
            f"{root.as_posix()} was wired by {recorded} and the engine here is {running}: "
            f"rewriting these surfaces would put an older copy over a newer one — `install "
            f"--vendor` moves the engine forward, and `uninstall` then `install` is the "
            f"downgrade said out loud"
        )


def record_wired(config_source: Path, version: str) -> bool:
    """Write `[install] wired = "<version>"` into this project's config (RK1462).

    A targeted insertion and never a serialiser, which is `adopting._with_role`'s rule: a
    `tomllib` round-trip drops the comments a scaffolded config is mostly made of. The key is
    replaced where it stands, appended under an existing `[install]`, and the table is opened
    at the end where the project has none — the three states a config can be in about it.

    Answers whether it wrote, so the report can say so: a fifth file touched by a command whose
    contract is *every surface or none* is not a write to leave unmentioned (RK298).
    """
    text = config_source.read_text(encoding="utf-8")
    line, row = chr(10), f'wired = "{version}"'
    lines = text.split(line)
    at = next((n for n, one in enumerate(lines) if one.strip() == "[install]"), None)
    if at is None:
        blank = line * 2
        tail = "" if text.endswith(blank) else (line if text.endswith(line) else blank)
        config_source.write_text(
            f"{text}{tail}[install]{line}{row}{line}", encoding="utf-8", newline=""
        )
        return True
    end = next(
        (n for n in range(at + 1, len(lines)) if lines[n].lstrip().startswith("[")),
        len(lines),
    )
    held = next(
        (n for n in range(at + 1, end) if lines[n].split("=")[0].strip() == "wired"), None
    )
    if held is not None:
        if lines[held] == row:
            return False
        lines[held] = row
    else:
        lines.insert(at + 1, row)
    config_source.write_text(line.join(lines), encoding="utf-8", newline="")
    return True


def _recorded(root: Path, version: str) -> bool:
    """Write the version down where this project has a config to write it into (RK1462).

    Silent on a project with none, which is one `install` is wiring before `init` ran: the
    record is a convenience for the next check and never a reason to fail a write that
    otherwise landed whole.
    """
    from roadkeep.config import Config  # noqa: PLC0415 - RK260

    try:
        source = Config.discover(root).source
        return False if source is None else record_wired(source, version)
    except Exception:  # noqa: BLE001 - a config this cannot write is one nobody will read
        return False


@dataclass(frozen=True, slots=True)
class Drifted:
    """One wired surface behind this engine, and whether the project has it at all (RK1482).

    The distinction the path alone could not carry, and it is the measured one: in the project
    RK1482 was filed from, `asking.md` and `writing.md` were not stale — they **did not
    exist**, so the session never learnt that `budget --anchor` measures a section before it is
    sent, and one design took five refusals against the word limit for want of a page one
    command away. *Behind* and *absent* wear the same shape and cost different things.
    """

    path: str
    #: False where this project has no copy at all. A surface that never existed is not drift
    #: between two versions of a text; it is a page the reader has never been able to open.
    existed: bool


def staleness(root: str | Path = ".") -> tuple[Drifted, ...]:
    """:func:`stale`, with the two states told apart (RK1482)."""
    base = Path(root).resolve()
    if not (base / PROJECT_SKILL).is_file():
        return ()
    try:
        intent = plan(base, gauging=False)
    except (ValueError, OSError):
        return ()
    if intent.ahead:
        return ()
    return tuple(
        Drifted(surface.path.relative_to(base).as_posix(), surface.existed)
        for surface in intent.changing
        if surface.refresh
    )


def stale(root: str | Path = ".") -> tuple[str, ...]:
    """The vendored surfaces that have drifted from the checkout answering here (RK234).

    `--check` is what RK100 named as holding the copy in step, and nothing in an adopting
    project ran it: Turing's `SKILL.md` was 78 lines behind and its `PreToolUse` matcher was
    missing `Bash` — a guard narrower than the one the plugin ships, in the file that decides
    whether the guard fires. So the question is asked where it is cheap to ask and useful to
    answer: the session start, in the process that is already the wired checkout.

    **What a project that is not wired pays is one `is_file`.** The vendored copy is the
    discriminator, and a plugin-served project has none — there is nothing to drift, and the
    plugin's own surfaces are whatever the session loaded. A wired one pays one small read per
    vendored surface and two JSON parses, and never the gate: ``gauging=False``, the workflow being written
    once and then the adopter's, so it is excluded here by the same field that says so.

    Measured against RK176's 43ms floor, which is the budget this spends from: **0.07ms**
    unwired and **0.86ms** on Dumont, wired. The gate would have been 40ms of that floor on
    its own, which is why declining it is a parameter rather than a comment.

    Every failure is silence, exactly as the notice this feeds is (RK82): a session that
    cannot start because a checkout moved is worse than one told nothing, and `install
    --check` still answers on demand.
    """
    # The paths alone, which is what the session-start notice names (RK1482): that message is
    # one sentence about the wiring and the two states read the same in it. `staleness` is the
    # reader that tells them apart, and this is it with the distinction dropped — one plan,
    # one answer, so the two cannot come to disagree about what has drifted.
    #
    # The one direction neither can report (RK1462): where the surfaces are **ahead**, every
    # word here is *behind*, *stale*, *refresh*, and the remedy names the write that would
    # delete the newer copy — so `install --check` is where that state is reported in words
    # that fit it, and both of these say nothing.
    return tuple(one.path for one in staleness(root))


@dataclass(frozen=True, slots=True)
class Vendor:
    """The copy of this tool a project holds **inside itself**, at `.roadkeep/` (RK1451).

    The fifth engine and the second that writes. `install --vendor` puts it there and the
    launcher resolves it above every clone and cache, so where no plugin is registered it is
    what the guard and the served tools run — while a shell reaching `roadkeep` gets whatever
    the path answers. Measured in Japode/cloud: the launcher at 0.1.1269 and the shell at
    0.2.58, two minor versions apart, both exiting 0 and neither naming the other.
    """

    version: str
    #: The package directory inside the vendored tree — `<root>/.roadkeep/src/roadkeep`, so it
    #: is the same fact as :attr:`Engine.home` and the two rows compare directly.
    home: Path


def vendored_at(root: Path) -> Vendor | None:
    """The engine vendored into this project, or None where it holds none (RK1451).

    **Read and never run**, which is the opposite of :func:`candidates`' rule and for a reason
    that reverses with the question. Ranking engines to pin one has to prove importability — a
    checkout mid-refactor states a version and then raises — so that reader spends a subprocess
    per candidate under a 30-second timeout. This one is not choosing anything: it names a copy
    already in place, and it sits on the path `lint` takes through :func:`engines`, where a
    probe of that shape is a gate that hangs.

    So the literal is the answer, through :func:`~roadkeep.provenance.stated_at`, which is the
    one reader this package has for *what a directory says it is* — and the same one
    :attr:`Engine.on_disk` asks about the running copy (RK1452). Where the tree states nothing
    there is no row: a `.roadkeep/` with no package in it is not a second engine, it is a
    directory.
    """
    # Resolved, because the row beside it is :attr:`Engine.home` and that one is: a copy
    # answering out of `.roadkeep/` has to compare equal to itself, and on this platform two
    # spellings of one directory are what would stop it.
    home = (root / PROJECT_ENGINE / "src" / "roadkeep").resolve()
    found = stated_at(home)
    return Vendor(version=found, home=home) if found else None


#: What :attr:`Engines.verdict` answers (RK418). Three and not two, because a checkout with
#: uncommitted work is at no commit the plugin could match — so `agreed` would be the defect
#: and `behind` a direction nothing measured.
AGREED = "agreed"
BEHIND = "behind"
UNPINNABLE = "unpinnable"


@dataclass(frozen=True, slots=True)
class Engines:
    """Every copy of this tool one project runs, read back together (RK415).

    **Five are read and three state a version** (RK1392, RK1451). RK1385 added the merge driver,
    which git runs when nobody is watching, and it is deliberately outside the comparison:
    `agreed`, `behind` and `unpinnable` compare versions, and this tool refuses to execute a
    recorded driver to ask for one — the gate states a ref, which is not a number either. So a
    count says which of the two questions a sentence is about, and the copies below are the ones
    that *wrote, judged or gated* something already.

    An adopting project wires three: the plugin its `PreToolUse` hook and skill run, the
    action its workflow gates on, and whatever `roadkeep` the caller invokes — which on a
    machine that also develops this tool is a checkout. Measured live, all three at once: the
    checkout at 0.1.418 doing every write, the plugin at 0.1.285 denying the hand edits, and
    `@main` in CI. Every write was fine; what nothing said is that the pen and the judge were
    133 versions apart, in a project whose own backlog reasoned about *the plugin this
    repository runs* while a newer one held the pen.

    Read and never reconciled, which is :mod:`roadkeep.provenance`'s rule one level up: a
    cache is allowed to lag a checkout, and what is not survivable is being unable to say
    which of them answered.
    """

    #: The copy this process is, always known.
    running: Engine
    #: The copy the harness wired to this project, or None where none is registered — which
    #: is every project served by a checkout alone, and is not a defect.
    plugin: Installed | None = None
    #: The copy the project vendored into itself, or None where it holds none (RK1451). Read
    #: like the plugin and judged like it, because it writes for the same reason: with no
    #: plugin registered the launcher resolves `.roadkeep/` first, so the guard and every
    #: served tool go through it while a shell reaches whatever is on the path.
    vendored: Vendor | None = None
    #: `(file, ref)` per workflow step calling the action, in file order.
    gates: tuple[tuple[str, str], ...] = ()
    #: The command this project's own `.mcp.json` declares for the roadkeep server, resolved,
    #: or `""` where it declares none (RK1469). Read and never derived: it is literally what
    #: the harness runs, so :meth:`invoke` answers it rather than restating the launcher's
    #: resolution order — which it knew two of four entries of.
    declared: str = ""
    #: The command git would run to merge a governed file, or `""` where nothing is wired
    #: (RK1385). The **fourth** copy, and the one that runs when nobody is watching: git
    #: invokes it mid-merge, on the files whose whole claim is that their merge is decidable,
    #: and until this row neither `engines` nor `merge --check` said which copy it is —
    #: `--check` answers whether git can run it, which is a different question (RK266).
    #:
    #: The command and never its version: reading that would mean *running* somebody's
    #: recorded driver, which `merging._resolves` refuses on its own argument. What a reader
    #: gets is the path beside the tree above, which is the comparison they came for.
    driver: str = ""

    @property
    def verdict(self) -> str:
        """`agreed`, `behind` or `unpinnable` — three states, because two are not enough (RK418).

        The comparison used to be the release string alone, which is the one fact an earlier
        task proved insufficient: two `src/roadkeep/` trees fourteen files apart answered the
        same number, and that is why the running engine carries its directory and its commit
        at all. Both copies have a revision — the running one from git, the installed one from
        the marketplace row that records the sha it was built at — and both were read, both
        printed, and neither compared.

        The case that got through is the one a machine developing this tool is in every day: a
        checkout at the plugin's own version, with uncommitted work, writing; the plugin
        judging; the numbers matching and the verb saying they agree. The files do not.

        So the third state is its own, and collapsing it would be wrong either way. A checkout
        whose files are **modified** is at no commit the plugin could match — calling that
        `behind` asserts a direction nothing measured, and calling it `agreed` is the defect
        this fixes. `unpinnable` says the only true thing: these two cannot be compared, and
        the reason is on the running engine's own `revision`.

        Where a commit is missing on either side the version is still the best fact available,
        so it decides — a marketplace row that recorded no sha is not evidence of a difference.
        """
        if self.plugin is None:
            return AGREED
        if self.plugin.version != self.running.version:
            return BEHIND
        if self.running.modified:
            return UNPINNABLE
        if self.plugin.commit and self.running.commit:
            # Both known and both at one version: the sha is what tells the trees apart, and
            # it is compared on the prefix because the marketplace records a short one.
            short = min(len(self.plugin.commit), len(self.running.commit), 7)
            if self.plugin.commit[:short] != self.running.commit[:short]:
                return BEHIND
        return AGREED

    @property
    def swapped(self) -> bool:
        """Whether the copy answering is no longer the copy its own directory holds (RK1452).

        The third way this report can be wrong about who wrote, and the only one where the
        wrong answer is about the engine *asking*. `install --vendor` replaces `.roadkeep/` in
        place; a server that imported the old modules keeps answering their version for a path
        that has not held it since, and every row here is then a comparison against a number
        nothing on disk states.

        So it is asked at answer time, off :attr:`Engine.on_disk`, and it outranks every other
        reading: a verdict composed from a stale `running` is a verdict about copies that are
        not the ones in play.
        """
        return bool(self.running.on_disk) and self.running.on_disk != self.running.version

    @property
    def split(self) -> bool:
        """Whether a copy **inside this project** states a version other than the one answering.

        Separate from :attr:`verdict` on purpose, and the separation is what keeps the write
        guard honest: `behind` is a decision about the pin a project declared with `[install]
        enforced`, and :func:`behind` refuses a write on it. A vendored copy is not that pin —
        it is a second engine in play — so it belongs in the report and the exit code without
        acquiring the standing to refuse anything.

        Trivially False where the copy answering *is* the vendored one, the two reading one
        `__init__.py`. That is the launcher's own case, and the row it prints is still the whole
        of what a reader there was missing: which of the copies on this machine answered.
        """
        return self.vendored is not None and self.vendored.version != self.running.version

    @property
    def agree(self) -> bool:
        """Whether every copy of this tool that states a version states the same one.

        The gate is deliberately not in this: `main` and `v0.2.1` and `./` are refs, and a
        ref is not a number to compare — what CI runs is decided when CI runs. It is reported
        beside the rest because a reader comparing them needs to know another exists.

        `unpinnable` is **not** agreement (RK418): a boolean has to fall one way, and the
        state this exists to stop being silent about is exactly the one where the numbers
        match and the files do not. Nor is a vendored copy at another version (RK1451), which
        is the same silence one copy further in — the difference being that nothing there is
        even claiming to be the other. Nor is a home swapped under the running process
        (RK1452), where the copy that would answer *this* row is already gone.
        """
        return self.verdict == AGREED and not self.split and not self.swapped

    def invoke(self) -> str:
        """The shell command that reaches the copy **wired to this project** (RK1230).

        The MCP tools always reach the right copy; the shell does not, and a session that
        needs the shell has to know which one to invoke — `lint --fix` is withheld from the
        tool surface, so any repair goes there. Nothing said which.

        Observed across one long session: commands were run against a copy found by *listing*
        a plugins cache directory, while the engine the project writes with lived under a
        different plugins root entirely. The stale copy did not fail. It agreed with a rule
        that had moved, and answered plausibly, which is the part that matters.

        One line and nothing else, so it can be read into a shell variable rather than
        recognised inside a report. :meth:`stated` already prints the same paths in a table,
        and a table is the thing a caller was reduced to grepping.

        The **plugin's** where one is registered, because that is what "wired to this project"
        means — the copy the hook and the skill run.

        Then **what this project declares** (RK1469), which is read and never derived: RK1451
        taught this to name the vendored copy, and both rules were restatements of a resolution
        order the launcher owns — `$ROADKEEP_HOME`, `.roadkeep/`, a sibling, the cache clone —
        of which this knew the middle and neither end. A project pinning `ROADKEEP_HOME` outside
        itself was handed a copy that is not the pen, which is RK1230's failure one wiring along.
        The declaration is what the harness runs, and where it names the committed bridge the
        order is resolved at the moment it is used, by the file that owns it.

        Only where a project declares neither is the running engine's own invocation the honest
        answer: the copy the caller reaches *is* the one that answers, and naming a second would
        be inventing a disagreement.
        """
        if self.plugin is not None and self.plugin.home is not None:
            return f"python {(self.plugin.home / LAUNCHER).as_posix()}"
        if self.declared:
            return self.declared
        return invocation()

    def stated(self) -> str:
        """Every copy this project runs, and where the three that state a version differ.

        Four rows and three compared (RK415, RK418, RK1392): the driver is read and never
        judged, which is why it carries a command rather than a number.

        Beside :meth:`payload` since RK1170. Every absence is **said** rather than left as a
        missing row: "no plugin" and "a plugin this could not read" look the same to a reader,
        and only one of them means the writes are unjudged by a second copy.
        """
        running, plugin, held = self.running, self.plugin, self.vendored
        rows = [
            f"writing  {running.version:<10}{running.revision}  {running.home.as_posix()}"
        ]
        # Directly under the row it contradicts (RK1452), because it is a correction to that
        # row and not a sixth copy: one directory, and the version this process holds for it is
        # not the version it holds. Said before anything is compared, every other row here
        # being a comparison against the number above.
        if self.swapped:
            rows.append(
                f"swapped  {running.on_disk:<10}that directory states {running.on_disk} now — "
                f"this process loaded {running.version} from it and kept the modules, so "
                f"nothing on disk is what answered: restart the session"
            )
        # The fifth (RK1451), beside the copy that answered because it is the same kind of fact:
        # a package directory and the version its own `__init__.py` states. Said only where the
        # project holds one — an absent `.roadkeep/` is not an absence a reader can act on, it
        # is every project that never ran `install --vendor`.
        if held is not None:
            whose = (
                "  this is the copy answering"
                if held.home == running.home
                else "  the copy the launcher runs, so the guard and the served tools write here"
            )
            rows.append(f"vendored {held.version:<10}{held.home.as_posix()}{whose}")
        if plugin is None:
            rows.append("plugin   —         no plugin is registered for this project")
        else:
            home = "" if plugin.home is None else f"  {plugin.home.as_posix()}"
            rows.append(
                f"plugin   {plugin.version:<10}{plugin.revision}  {plugin.scope} scope{home}"
            )
        rows += [f"gate     {ref:<10}{where}" for where, ref in self.gates or ()]
        if not self.gates:
            rows.append("gate     —         no workflow here calls the action")
        # The fourth (RK1385). Said either way, for the reason every absence here is: a driver
        # nothing wired and a driver this could not read look the same to a reader, and only
        # one of them means a conflict falls back to git's own markers.
        #
        # **And it says which half it read** (RK1388). This wiring has two — the attribute
        # lines a repository commits, and the config this clone holds — and the row reads the
        # second. Written flat, it answered *no driver is wired* about a tree whose files
        # `install --check` reports as routed, so the two read as contradicting each other and
        # reconciling them meant already knowing which half each had inherited. The word is
        # `merge --check`'s own, that verb being the one which labels both.
        if not self.driver:
            rows.append(
                "merge    —         nothing in this clone's git config, so a conflict falls "
                "back to git's markers: `merge --check` reads the attribute half too"
            )
        else:
            here = self.running.home.parent.parent.as_posix()
            whose = (
                "  this tree"
                if self.driver.startswith(here)
                else "  another copy — `merge --check` names the line that re-wires it"
            )
            rows.append(f"merge    {self.driver}{whose}")
        if self.verdict == UNPINNABLE:
            # The state that used to read as agreement, and the one a machine developing this
            # tool is in every day (RK418): the numbers match, the checkout has uncommitted
            # work, and the files the two copies hold are not the same files.
            rows.append(
                f"differ   both state {running.version} and this checkout is modified at "
                f"{running.revision}, so the two cannot be compared: commit, or read a hook's "
                f"refusal as that copy's rule rather than this one's"
            )
        elif self.verdict != AGREED:
            rows.append(
                f"differ   the pen is {running.version} at {running.revision} and the judge "
                f"is {plugin.version if plugin else '—'} at "
                f"{plugin.revision if plugin else '—'}: `/plugin update` moves the judge, and "
                f"until then a hook's refusal is that copy's rule and not this one's"
            )
        # Its own sentence and never the one above (RK1451): that pair is a pen and a judge and
        # `/plugin update` is what moves it, while these two are both pens — the remedy is to
        # re-vendor or to stop reaching past the launcher, and printing "the judge is —" about a
        # project with no plugin is how the wrong pair got read for a whole session.
        if self.split and held is not None:
            rows.append(
                f"differ   the launcher runs the vendored {held.version} and this shell "
                f"reached {running.version} at {running.revision}: both write, so re-vendor "
                f"with `install --vendor` or run what `engines --invoke` prints"
            )
        return chr(10).join(rows)

    def payload(self) -> dict[str, object]:
        running, plugin = self.running, self.plugin
        return {
            # `writing`, which is what this copy *does* and not what it is: the reader is
            # deciding whose rule a refusal was, so the key names the role and the plugin
            # below names the other one.
            "writing": {
                "version": running.version,
                "home": running.home.as_posix(),
                "revision": running.revision,
                # What that home states **now** (RK1452), or null where it states nothing.
                # Beside the version and not instead of it: the two being different is the
                # answer, and a consumer that saw only one of them could not tell.
                "on_disk": running.on_disk or None,
            },
            # Null where no plugin is registered for this project, which is every tree served
            # by a checkout alone and is not a defect (RK415).
            "plugin": None
            if plugin is None
            else {
                "version": plugin.version,
                "home": None if plugin.home is None else plugin.home.as_posix(),
                "revision": plugin.revision,
                "scope": plugin.scope,
            },
            # Null where the project vendored none, which is the common case and not a defect
            # (RK1451). No `revision`: `install --vendor` excludes `.git` on purpose, so the
            # copy is at no commit anything could name.
            "vendored": None
            if self.vendored is None
            else {"version": self.vendored.version, "home": self.vendored.home.as_posix()},
            "gates": [{"file": where, "ref": ref} for where, ref in self.gates],
            # The fourth copy (RK1385), as the command and never as a version: reading that
            # would mean running it. `""` and never omitted, so a consumer tells "nothing
            # wired" from "this build predates the row".
            "driver": self.driver,
            # The command a shell caller runs (RK1230), on the ordinary payload as well as
            # behind its own flag: a consumer already reading this answer should not have to
            # make a second call for the one field it acts on.
            "invoke": self.invoke(),
            "agree": self.agree,
            # Which of the three, because the boolean above cannot carry the state RK418
            # added: a checkout with uncommitted work is at no commit the plugin could match,
            # and `agreed` there was the defect being fixed.
            "verdict": self.verdict,
            # The other two ways `agree` can be False, stated separately because each is a
            # different pair: `split` is pen against pen (RK1451) and `swapped` is the pen
            # against its own directory (RK1452). `verdict` stays the decision about the pin,
            # and only that decision refuses a write.
            "split": self.split,
            "swapped": self.swapped,
        }


def _routed(root: Path) -> bool:
    """Whether the governed files already route to this driver (RK1387).

    Off `merging.attributed`, which is `register`'s own read: two computations of *the line
    this role wants* is how a check and a write come to disagree, and that function was written
    to be the one both ask. What it answers here is the **attribute** half — a fact about a
    committed file, and this report's business — while whether this clone can run what they
    route to is per checkout and is what `merge --check` exists to say.

    False on a tree this cannot read, which is the same direction every other absence in this
    report takes: an unreadable project is one nothing is wired in as far as a reader can tell,
    and offering the command there is the honest half.
    """
    from roadkeep.config import Config  # noqa: PLC0415 - RK260
    from roadkeep.merging import attributed  # noqa: PLC0415 - RK260

    try:
        found = attributed(Config.discover(root))
    except Exception:  # noqa: BLE001 - an unreadable tree is an unwired one to this reader
        return False
    return bool(found.wanted) and not set(found.wanted) - set(found.present)


def engines(root: str | Path = ".") -> Engines:
    """The five, for one project. Reads five small files and asks git nothing new."""
    base = Path(root).resolve()
    return Engines(
        running=engine(),
        plugin=installed(base),
        # The fifth (RK1451), read out of the project's own tree: one `read_text` where a copy
        # is vendored and one failed open where none is.
        vendored=vendored_at(base),
        # What this project runs, as it wrote it down (RK1469) — one small JSON read, and the
        # answer `--invoke` prints rather than an order restated here.
        declared=declared_launcher(base),
        gates=gated_at(base),
        # The fourth copy (RK1385), read out of git config and never run. Swallowed the way
        # every other absence here is: a tree git cannot be asked about answers "nothing
        # wired", which is what a reader of an unwired project sees anyway.
        driver=_driver(base),
    )


def _driver(root: Path) -> str:
    """The command git would run to merge a governed file, or `""` (RK1385).

    Off `merging.registered`, which is the reader that already owns this question — a second
    `git config --get` here would be the two coming to disagree about which key is the driver.

    A read of the *config* and never of the command: whether the thing it names still exists
    is `merge --check`'s answer, and whether it is this tree is the comparison the row states.
    """
    from roadkeep.config import Config  # noqa: PLC0415 - RK260
    from roadkeep.merging import registered  # noqa: PLC0415 - RK260

    try:
        return registered(Config.discover(root)).stored
    except Exception:  # noqa: BLE001 - an unreadable tree is an unwired one to this reader
        return ""


def behind(root: str | Path = ".") -> bool:
    """Whether the copy running is older than the one registered here, paying for git only
    where the cheap facts cannot decide (RK1237).

    RK1235 put :func:`engines` in front of every governed write on a pinned project and never
    measured it. It is **45 ms** — three git subprocesses, 14 for `ls-files`, 14 for
    `rev-parse` and 16 for `status --porcelain` — against RK176's 43 ms floor for a whole
    command, and cached per *process*, which is once per write on a CLI and never twice.

    The narrowing RK1237 filed was to drop `status --porcelain`, and that reading was wrong:
    `modified` is exactly what separates `unpinnable` from `behind`, and this guard has to
    make that separation — a developer's checkout with uncommitted work at the plugin's
    version but on another commit is `unpinnable`, and refusing it is the failure the whole
    design exists to avoid.

    What is actually free is the **version**, which is a module attribute. :attr:`Engines.
    verdict` already decides on it first and reaches for a sha only where the two match, so
    the fix is not a second rule but a cheaper *reading* handed to the same one: ask with the
    commit unknown, which is the state a marketplace row with no sha already produces, and
    escalate only where that answer was `agreed` and a plugin exists to disagree. A project
    running a copy at another version — the case this guard is for — pays nothing.

    Measured after: **2 ms** where no plugin is registered or the versions differ, against 45
    for the reading it replaces — the registry is a JSON file and the version is an attribute.
    Only two copies claiming one version pay for git, and that is the one case where nothing
    cheaper could tell them apart.

    One verdict and never two, which is :meth:`~roadkeep.kernel.document.Document.holds`'
    rule (RK300): what changes between the two calls is the facts, never the judgement.
    """
    base = Path(root).resolve()
    cheap = Engines(running=engine(placed=False), plugin=installed(base))
    if cheap.plugin is None or cheap.verdict == BEHIND:
        return cheap.verdict == BEHIND
    return engines(base).verdict == BEHIND


#: A workflow step calling this action, in either of the two spellings a repository writes:
#: `<owner>/roadkeep@<ref>` in an adopting project, and `./` in the tree that *is* the action.
#: The owner is not matched, because a fork publishes the same action under another name and
#: the question is which ref gates this project rather than whose copy does.
_GATE_RE = re.compile(
    r"^\s*-?\s*uses:\s*(?P<action>\./|[^\s#]*?/roadkeep)(?:@(?P<ref>[^\s#]+))?\s*(?:#.*)?$",
    re.MULTILINE,
)


def _provides_plugin(base: Path) -> bool:
    """Whether this tree already runs the guard as a plugin of its own (RK402).

    Asked of the two files that make it true rather than of the root's name: the manifest
    that declares the plugin, and the hooks file it points at. A fork, a vendored copy and
    this checkout are the same situation, and a name test would answer for exactly one.

    Both, because either alone is a different state: a manifest with no hooks file declares
    nothing that runs, and a hooks file no manifest names is a file the harness never loads —
    and in both of those the project settings are still the only place the guard could live.
    """
    return (base / PLUGIN_MANIFEST).is_file() and (base / PLUGIN_HOOKS).is_file()


def gated_at(root: str | Path = ".") -> tuple[tuple[str, str], ...]:
    """Which ref of this action every workflow calls, as `(file, ref)` in file order (RK415).

    The third engine, and the only one stated in a file the project owns: the checkout
    answers for itself and the plugin is a row in the harness's registry, while CI runs
    whatever a `uses:` line names — `main` as `install` writes it, a tag where an adopter
    pinned one, and `./` in this tree, which gates on its own working copy.

    Every workflow and not the one this command writes, because an adopter is free to call
    the gate from a pipeline of their own and a reader that only knew `roadkeep.yml` would
    report *no gate* about a repository that has one. The file rides with the ref and
    duplicates are kept: two workflows calling two refs is the disagreement this exists to
    show, not a set to fold, and folding it would lose the one thing that locates the fix.

    Empty where the directory is absent or unreadable — a repository with no workflows has
    not asked for CI, which is a different answer from one whose ref cannot be read, and
    neither is worth failing over.
    """
    base = Path(root).resolve()
    directory = base / WORKFLOWS
    refs: list[tuple[str, str]] = []
    try:
        files = sorted(
            path
            for path in directory.iterdir()
            if path.suffix in (".yml", ".yaml") and path.is_file()
        )
    except OSError:
        return ()
    for path in files:
        try:
            body = path.read_text(encoding="utf-8")
        except (OSError, ValueError):
            continue
        refs.extend(
            # A local `uses: ./` carries no ref and is the tree itself, said as the caller
            # spelled it rather than resolved to a revision this function has no business
            # asking git for.
            (path.relative_to(base).as_posix(), found.group("ref") or found.group("action"))
            for found in _GATE_RE.finditer(body)
        )
    return tuple(refs)


def _governed(base: Path) -> Config:
    """This project's own configuration, or a refusal naming what a driver would be for.

    A driver is registered per *governed file*, so a project that declares none has nothing to
    register: writing `.gitattributes` lines for the paths a default config happens to name
    would wire a driver for files nobody declared (L6).
    """
    config = Config.discover(base)
    if config.source is None:
        raise ValueError(
            f"{base} declares no {CONFIG_NAME} and nothing was registered: a merge driver is "
            f"wired per governed file, so `{invocation()} init` (or a config) comes first — the "
            f"four surfaces above do not depend on it"
        )
    return config


# -- where the surfaces are read from ----------------------------------------


def _source() -> Path:
    """The tree that is answering, as a plugin root: the parent of the package's `src/`.

    Taken from :func:`~roadkeep.provenance.engine`, which already resolves *which copy of
    this package is running* — the same question, and the one thing a plugin cache and a
    checkout disagree about (RK79). Deriving it a second way here would be a second answer.
    """
    return engine().home.parent.parent


def _pinned_engine(base: Path) -> Path | None:
    """The engine this project vendored, where it is one this command could wire from (RK1464).

    `_carrying`'s question about the other variant: which engine a project runs is a fact on
    its disk, and reading the checkout answering instead makes every `--check` after an
    `install --vendor` report drift and offer the write that un-pins it.

    Asked as *does it carry what this command translates* and never as *is the directory
    there*: a half-copied `.roadkeep/` is not a source, and falling through to the running
    engine there is the same answer a project with no pin gets.
    """
    home = base / PROJECT_ENGINE
    if not home.is_dir():
        return None
    return home if all((home / part).is_file() for part in CARRIED) else None


def _carried(root: Path, *, committed: bool = False) -> None:
    """Refuse a tree that is not carrying what this run has to translate, naming what it lacks.

    The bridge is asked for only under `--committed` (RK1108) and is deliberately not in
    :data:`CARRIED`: that list also decides whether a tree *is* the plugin, so adding a sixth
    file would make an older checkout stop being recognised as one. Asked here instead, so a
    source that predates the bridge is refused by name rather than by an errno from the copy.
    """
    wanted = (*CARRIED, PLUGIN_BRIDGE) if committed else CARRIED
    missing = tuple(part for part in wanted if not (root / part).is_file())
    if missing:
        raise NotShipped(root, missing)


def _ships_the_plugin(root: Path) -> bool:
    """Whether this tree *is* the plugin rather than a project that adopted it (RK235).

    Asked of the files rather than of a source, because :func:`removal` is given no checkout
    to compare against — it recognises a wiring by this project's own entries, which is what
    lets it run after the tree it pointed at is gone. Where a source *is* known,
    :func:`plan` compares the two roots instead, that being the exact statement.
    """
    return all((root / part).is_file() for part in CARRIED)


def _standing(base: Path) -> int | None:
    """What this project's own gate reports today, or None where it cannot be asked (RK140).

    Run while the workflow is being written, because that is the one moment the difference
    between a strict gate and a baselined one is knowable without being told: the projects
    that most need the gate are the ones carrying the most debt, and a workflow that is red on
    its first push is a gate an adopter switches off rather than reads.

    None for a project that declares nothing — there is no governed file to be in debt about,
    so the strict workflow is the honest one — and None again where the gate itself refused,
    because `install` writes four surfaces and a lint that raised is not a reason to write
    none of them.

    **`install.stale` is not debt and is subtracted** (RK1192). The gate now reports a wired
    surface behind the engine answering, and its remedy is this very command — so counting one
    here would bake the work `install` is running *in order to do* into the baseline it writes,
    and the number would go down by itself on the next push. Every other finding is the
    project's own backlog and is exactly what a baseline is for; this one is the state that
    ends the moment these surfaces are written.
    """
    try:
        config = Config.discover(base)
        if config.source is None:
            return None
        return sum(
            1 for one in lint(config).findings if one.code != "install.stale"
        )
    except (ValueError, OSError):
        return None


def _carrying(base: Path) -> bool:
    """Whether this project's own declarations run the committed launcher (RK1113).

    The variant is a property of the project and `--check` read it off the **flag**, so a tree
    adopted `--committed` was told every one of its surfaces had drifted and handed the plain
    `install` as the repair — which rewrites them to a checkout path, the one change the bridge
    exists to prevent: the file stays on disk, nothing references it, and a web session loses
    its hook. Measured on dockerdesk at acc7fc1, a tree with no local edits: "3 surface(s)
    differ", and `install --committed` restored all three to exactly HEAD.

    Read the way :func:`removal` reads (RK284, RK1108) — **this project's own entry** and no
    checkout — and both halves of it, because either alone is a different state. A bridge
    nothing references is what a downgrade leaves behind; a declaration naming a bridge that is
    not there is a project whose launcher was deleted. Neither is wired to it, so both are drift
    against the default, where the repair is the `install --committed` that puts it back.

    A substring and not a parse: what is being asked is whether the path this command writes
    appears where this command writes it, and the two declarations spell it under different
    placeholders (:data:`PROJECT_DIR` and :data:`PROJECT_DIR_OR_CWD`) — so matching the launcher
    itself is the one test that does not need to know which of them a surface used.
    """
    if not (base / PROJECT_BRIDGE).is_file():
        return False
    for name in (PROJECT_SETTINGS, PROJECT_MCP):
        try:
            if PROJECT_BRIDGE in _read(base / name):
                return True
        except OSError:
            # A declaration that is not there says nothing about the variant, and an
            # unreadable one is not this command's refusal to make: `_declaration` reads the
            # same file one step on and reports it as the surface it is.
            continue
    return False


def _launcher(base: Path, origin: Path) -> str:
    """The launcher, addressed from the adopting project — the one substituted fact.

    Relative wherever a relative path exists, so a pair of sibling checkouts wires up the
    same on every machine that has them; absolute only when there is none to write, which on
    Windows means the two trees are on different drives.
    """
    try:
        relative = os.path.relpath(origin, base).replace(os.sep, "/")
    except ValueError:
        return (origin / LAUNCHER).as_posix()
    return LAUNCHER if relative == "." else f"{relative}/{LAUNCHER}"


def _rooted(command: str, launcher: str, placeholder: str) -> str:
    """One plugin-rooted path, re-addressed to the project. Absolute paths lose the prefix."""
    target = launcher if launcher.startswith("/") or ":" in launcher.split("/")[0] else None
    if target is not None:
        return command.replace(f"{PLUGIN_ROOT}/{LAUNCHER}", target)
    return command.replace(f"{PLUGIN_ROOT}/{LAUNCHER}", f"{placeholder}/{launcher}")


def _hooks(origin: Path, launcher: str) -> dict:
    """The plugin's hook declaration with the launcher re-addressed, and nothing else moved.

    The events, the matcher and the timeouts arrive from the file — so the matcher that
    `tests/test_plugin.py` holds against :data:`~roadkeep.guarding.WRITE_TOOLS` is the matcher
    every adopting project gets, and a fourth event reaches them all by being declared once.
    """
    declared = json.loads(_read(origin / PLUGIN_HOOKS))["hooks"]
    return {
        event: [
            {
                **group,
                "hooks": [
                    {**hook, "command": _rooted(hook["command"], launcher, PROJECT_DIR)}
                    for hook in group["hooks"]
                ],
            }
            for group in groups
        ]
        for event, groups in declared.items()
    }


def _server(origin: Path, launcher: str) -> dict:
    """The plugin's server declaration, addressed the way a project's own `.mcp.json` is."""
    server = json.loads(_read(origin / PLUGIN_MCP))["mcpServers"][SERVER]
    return {
        **server,
        "args": [_rooted(arg, launcher, PROJECT_DIR_OR_CWD) for arg in server["args"]],
    }


def _workflow(origin: Path, debt: int | None) -> str:
    """The gate as CI calls it: the action this repository publishes, at one line.

    The repository is read out of the plugin manifest rather than written here, because the
    manifest is what an install already trusts to say where this tool comes from.

    ``debt`` is what this project's own gate reports **today** (RK140), which is what decides
    between the two honest defaults. A backlog with standing findings gets the baseline, so
    the gate fails on what a branch adds and forgives what nobody was going to redo — and the
    count is named in the comment, because a baseline nobody remembers to remove is the other
    failure mode. A project already clean gets the strict gate and no comment to act on.
    """
    repository = json.loads(_read(origin / PLUGIN_MANIFEST))["repository"]
    action = repository.removeprefix("https://github.com/").removesuffix(".git").strip("/")
    head = [
        "# The gate the write path already runs locally, called in CI through the action",
        "# roadkeep publishes rather than a copied `run:` block, which drifts per",
        "# repository. `roadkeep lint` exits 1 on a governed file that drifted, and that",
        "# exit code is the whole contract.",
        "#",
    ]
    if not debt:
        head.append(
            "# Yours from here: `with: {directory: .}` where roadkeep.toml is not at the root,"
        )
        head.append(
            "# and `with: {baseline: origin/main}` to fail on what a branch added rather than"
        )
        head.append("# on a backlog's standing debt.")
    else:
        head += [
            f"# Baselined, because `roadkeep lint` reported {debt} finding(s) here when this",
            "# was written: the gate fails on what a branch adds and forgives the standing",
            "# debt by name, which is the only setting a late gate can be switched on under.",
            "# Drop the `baseline:` line — and the fetch-depth above it — the day `lint`",
            "# exits 0 on the default branch, and the gate is absolute.",
            "#",
            "# Yours from here: `with: {directory: .}` where roadkeep.toml is not at the root.",
        ]
    checkout = ["      - uses: actions/checkout@v4"]
    step = [f"      - uses: {action}@{ACTION_REF}"]
    if debt:
        # A baseline is a rev, so the diff needs the history to take it against.
        checkout += ["        with:", "          fetch-depth: 0"]
        step += [
            "        with:",
            "          # `base_ref` on a pull request, the default branch on a push — where",
            "          # the two coincide the diff is empty and the gate passes on the debt.",
            "          baseline: origin/${{ github.base_ref || "
            "github.event.repository.default_branch }}",
        ]
    return "\n".join(
        (
            *head,
            "name: roadkeep",
            "",
            "on: [push, pull_request]",
            "",
            "jobs:",
            "  lint:",
            "    name: roadkeep lint",
            "    runs-on: ubuntu-latest",
            "    steps:",
            *checkout,
            *step,
            "",
        )
    )


# -- what each kind of surface does to the file it lands in -------------------


def _skill(origin: Path, launcher: str, *, committed: bool = False) -> str:
    """The plugin's skill with its entry point re-addressed — the fourth substitution (RK137).

    `install` states that the launcher's path is the only substituted fact, and the skill was
    the one surface where it was not: the shipped sentence says `roadkeep` is the installed
    entry point, and for a project wired to a checkout the package is *not* installed, so
    every shell example in the copy names a command that resolves to nothing. Verified on a
    real adoption. Nothing breaks until an agent falls back from the MCP tools to the shell —
    which is exactly the moment the skill is being read.

    The sentence is matched rather than the line number, and a match that is not exactly one
    is a refusal: a copy written with the wrong entry point is the defect this module exists
    to remove, and silently shipping it would be worse than the hand-written copy it replaced.
    """
    text = _read(origin / PLUGIN_SKILL)
    # A function and not a replacement string: a launcher is a path, and `re.sub` would read
    # a backslash in one as a group reference.
    replaced, count = _ENTRY_RE.subn(lambda _: _entry(launcher, committed=committed), text)
    if count != 1:
        raise Unanchored(origin / PLUGIN_SKILL, count)
    return replaced


def _entry(launcher: str, *, committed: bool = False) -> str:
    """What the entry-point sentence becomes, per variant (RK1119).

    Quoted, for the reason the hook command is: a checkout on a path with a space in it is
    otherwise two arguments.

    **Two sentences and not one with a clause swapped**, because the clause is the difference:
    under `--committed` nothing was wired to a checkout — the launcher is a file in the
    repository that *resolves* one at runtime, and the environment the flag exists for has
    none until something provides one. So the sentence a session read before running anything
    named the wrong place to look for its engine, in the file it reads instead of asking, and
    an agent that believed it went looking for the checkout the launcher exists to not need.
    Since RK1113 a plain `install` writes this variant too, so the flag is not the only path.
    """
    if committed:
        return (
            f"`python \"{launcher}\"` is this project's entry point — the package is not "
            f"installed here and `roadkeep` is on no PATH, and that launcher is committed to "
            f"this repository so it finds an engine wherever this environment has one."
        )
    return (
        f"`python \"{launcher}\"` is this project's entry point — `install` wired it to a "
        f"checkout, so the package is not installed here and `roadkeep` is on no PATH."
    )


def _copy(path: Path, text: str) -> Surface:
    """A verbatim copy, refreshed on every run: the drift RK100 is about."""
    existed = path.is_file()
    return Surface(
        path=path,
        text=text,
        refresh=True,
        existed=existed,
        stale=not existed or _read(path) != text,
    )


def _once(path: Path, text: str) -> Surface:
    """Written when absent, then left alone — the adopter tunes it and this does not."""
    existed = path.is_file()
    return Surface(
        path=path,
        text=text,
        refresh=False,
        existed=existed,
        stale=not existed or _read(path) != text,
    )


def _declaration(path: Path, merge) -> Surface:
    """This project's entry re-derived inside a file other tools also declare in.

    Compared as parsed JSON and not as bytes: an adopter's own indentation is not staleness,
    and a `--check` that failed on whitespace is a check nobody leaves switched on.
    """
    current: dict = {}
    existed = path.is_file()
    if existed:
        try:
            loaded = json.loads(_read(path))
        except json.JSONDecodeError as error:
            raise Unreadable(path, str(error)) from error
        if not isinstance(loaded, dict):
            raise Unreadable(path, f"read as {type(loaded).__name__}")
        current = loaded
    merged = merge(current)
    return Surface(
        path=path,
        text=json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
        refresh=True,
        existed=existed,
        stale=merged != current,
    )


# -- vendoring an engine into the project (RK1193) ----------------------------


class NoEngine(ValueError):
    """Nothing on this machine is a roadkeep this command could copy (RK1193).

    A refusal and never a silent skip: `--vendor` is asked for, so a run that copied nothing
    and exited 0 would leave a project believing it is pinned. The candidates it looked at are
    named, because the commonest cause is a plugin root under a `CLAUDE_CONFIG_DIR` this
    process does not see.
    """

    def __init__(self, looked: Sequence[str]) -> None:
        self.looked = tuple(looked)
        where = ", ".join(self.looked) or "nowhere this process can see"
        super().__init__(
            f"no engine to vendor: looked in {where} — set {ENGINE_SOURCE} to a roadkeep "
            f"checkout to use one, which is also the only way a working tree is eligible"
        )


class NotVerified(ValueError):
    """The copy landed and does not answer the version it was chosen for (RK1193).

    The last of the four rules, and the one the other three exist to make meaningful: picking
    by version is worth nothing if what arrives is a different tree. Raised **after** the copy,
    because the evidence is the copy running — so the directory is left on disk for a reader
    to look at rather than removed to make the failure tidy.
    """

    def __init__(self, wanted: str, answered: str, where: Path) -> None:
        self.wanted = wanted
        self.answered = answered
        super().__init__(
            f"vendored {where} answers {answered or 'nothing'} and {wanted} was chosen: the "
            f"copy is left where it is, because what is wrong with it is what it just said"
        )


@dataclass(frozen=True, slots=True)
class Candidate:
    """One roadkeep this machine can reach, and what it answered when asked (RK1193)."""

    #: The plugin root — the directory holding `scripts/roadkeep.py`.
    home: Path
    #: What `--version` printed. Compared as a **tuple of integers**, never as text: `0.1.9`
    #: sorts above `0.1.10` as a string, and the two adopters this generalises both got that
    #: right by accident of never having a two-digit patch.
    version: str
    #: Where it was found, for a report that has to say why this one and not another.
    why: str
    #: Whether it is a working tree — skipped unless `ROADKEEP_SRC` named it, which is the
    #: rule the measured hour paid for: a checkout mid-refactor answers a version and then
    #: raises `ImportError` out of a half-edited module.
    working: bool = False

    @property
    def ordered(self) -> tuple[int, ...]:
        return _numbered(self.version)


def _numbered(version: str) -> tuple[int, ...]:
    """A version as integers, so `0.1.10` outranks `0.1.9` (RK1193).

    Anything unparsable sorts lowest rather than raising: a candidate that answered something
    this cannot read is still a candidate, and it loses to every one that answered a number.
    """
    parts: list[int] = []
    for piece in version.strip().split("."):
        digits = "".join(one for one in piece if one.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


@dataclass(frozen=True, slots=True)
class Vendored:
    """What `install --vendor` copied, from where, and what the copy then answered."""

    #: Where it landed, absolute.
    into: Path
    chosen: Candidate
    #: Every candidate this looked at, highest version first — the report's evidence that the
    #: choice was by version and not by position.
    considered: tuple[Candidate, ...] = ()
    #: What the copy answered when asked after the write. Equal to `chosen.version` or this
    #: is a :class:`NotVerified` rather than a result.
    verified: str = ""
    files: int = 0
    #: Whether the project should be told to ignore the copy — False where a `.gitignore`
    #: already names it, so a project that did this once is not advised about it every run.
    ignore: bool = False

    def stated(self, checked: bool) -> str:
        """The choice, the evidence for it, and what the copy answered (RK1193)."""
        would = "would vendor" if checked else "vendored"
        rows = [
            f"  {would:<14} {self.chosen.version} from {self.chosen.why}",
            f"  {'into':<14} {self.into.as_posix()}  ({self.files} file(s))",
        ]
        rows += [
            f"  {'also saw':<14} {one.version} at {one.why}"
            + ("  (a working tree, skipped)" if one.working else "")
            for one in self.considered
            if one.home != self.chosen.home
        ]
        if self.verified:
            # The fourth rule, said out loud: picking by version is worth nothing unless what
            # landed is asked what it is.
            rows.append(f"  {'answers':<14} {self.verified}, as chosen")
        if self.ignore:
            # Printed and never written, which is `merge --register`'s rule about the `git
            # config` half (RK148): `.gitignore` is the project's file, and a copy of somebody
            # else's repository appearing in `git status` is what the line prevents. Said only
            # where nothing already covers it, so a project that did this once is not nagged.
            rows.append(
                f"  {'to ignore':<14} add `{PROJECT_ENGINE}/` to .gitignore — the copy is an "
                f"artefact, and committing it makes every upgrade a diff in this repository"
            )
        return "\n".join(rows)

    def stranded(self) -> str:
        """What is on disk after a run that copied this engine and then refused (RK1487).

        RK1464 moved the vendor in front of the surfaces and accepted the hazard RK1193 had
        put it behind them for: a run that copies an engine and then fails to wire it leaves a
        copy nothing points at. The trade is right — a downgrade somebody commits is worse
        than a directory one more `install` clears — and it was **silent**, so the caller read
        what stopped the surfaces and nothing about what landed.

        :class:`NotVerified`'s own shape, one failure over: that one leaves the tree on disk
        deliberately and says why, and this says the same about a copy the refusal above it
        never mentioned. Not an offer to delete it — the bytes are the evidence, and the next
        `install` is what points at them.
        """
        return (
            f"roadkeep: {self.chosen.version} landed in {self.into.as_posix()} and nothing "
            f"is wired to it: the copy is left where it is, because the write that points at "
            f"it is the one that just refused — `{invocation()} install --check` says what is "
            f"still to write, and a second `install` writes it"
        )

    def payload(self) -> dict[str, object]:
        return {
            "into": self.into.as_posix(),
            "version": self.chosen.version,
            "from": self.chosen.why,
            "files": self.files,
            "verified": self.verified or None,
            "ignore": self.ignore,
            "considered": [
                {"version": one.version, "from": one.why, "working": one.working}
                for one in self.considered
            ],
        }


#: What is never copied into the vendored tree (RK1193). `.git` above all: with it the copy is
#: a second repository inside the project — `git status` walks it, tooling finds two roots, and
#: an artefact stops being one. The rest is build litter that costs megabytes and answers
#: nothing.
_UNVENDORED = (".git", "__pycache__", ".pytest_cache", ".venv", "node_modules")


def candidates(root: Path) -> tuple[Candidate, ...]:
    """Every roadkeep this machine can reach, highest version first (RK1193).

    **Asked rather than read.** Each candidate is run as `<home>/scripts/roadkeep.py
    --version`, which is the one question that proves the tree is not merely present but
    *importable* — and importability is the whole failure being designed around: a checkout
    mid-refactor is on disk, states a version in `__init__.py`, and raises `ImportError` out of
    a half-edited module the moment anything uses it. Reading the literal would rank exactly
    that tree first.

    Measured on one machine: **six** engines resolvable — 0.1.841 and 0.1.820 under
    `~/.claude`, 0.1.678 and 0.1.645 under `~/.claude-pessoal`, and two marketplace clones.
    Picking by position gives whichever the search order happened to reach; picking by version
    gives the same answer on every machine, which is what makes a pin reproducible.

    A **working tree is excluded** unless `ROADKEEP_SRC` names it. Deliberately not a
    heuristic about how modified it is: a clean checkout is one `git pull` from being a dirty
    one, and a project that pinned an engine did so to stop tracking somebody's editor.
    """
    named = os.environ.get(ENGINE_SOURCE)
    found: list[Candidate] = []
    seen: set[Path] = set()
    for home, why, working in _places(root, named):
        resolved = home.resolve()
        if resolved in seen or not (resolved / LAUNCHER).is_file():
            continue
        seen.add(resolved)
        version = _asked(resolved)
        if version:
            found.append(Candidate(resolved, version, why, working=working))
    return tuple(sorted(found, key=lambda one: one.ordered, reverse=True))


def _places(root: Path, named: str | None) -> list[tuple[Path, str, bool]]:
    """Where to look, with what to call each — the launcher's own order plus the caches.

    Not the launcher's *resolution*, which stops at the first hit: this collects, because the
    choice here is by version and a search that returned early would be picking by position
    under another name.
    """
    out: list[tuple[Path, str, bool]] = []
    if named:
        # The one door a working tree comes through, and it is unconditional: a caller who
        # named it has said which tree they mean.
        out.append((Path(named), f"{ENGINE_SOURCE}={named}", False))
    wired = installed(root)
    if wired is not None and wired.home is not None:
        out.append((wired.home, f"the plugin wired to this project ({wired.version})", False))
    for base in _plugin_roots():
        out += [(one, f"a plugin root at {one.as_posix()}", False) for one in _under(base)]
    sibling = root.resolve().parent / "roadkeep"
    if sibling.is_dir():
        # A sibling checkout is the case `ROADKEEP_SRC` exists for, so it is offered and
        # marked rather than silently dropped: the report says it was seen and why it lost.
        out.append((sibling, f"a sibling checkout at {sibling.as_posix()}", True))
    stated = os.environ.get("XDG_CACHE_HOME")
    found = home()
    if stated or found is not None:
        cache = Path(stated) if stated else found / ".cache"  # type: ignore[operator]
        out.append((cache / "roadkeep-src" / "roadkeep", "the launcher's cache clone", False))
    return out


def _plugin_roots() -> tuple[Path, ...]:
    """The harness config directories a plugin can be unpacked under.

    Both spellings, because a machine can have more than one: `CLAUDE_CONFIG_DIR` and the
    default `~/.claude` are what the harness itself resolves, and the measurement that
    motivated this found engines under two of them at once.
    """
    stated = os.environ.get("CLAUDE_CONFIG_DIR")
    homes = [Path(stated)] if stated else []
    if (found := home()) is not None:
        homes.append(found / ".claude")
    return tuple(dict.fromkeys(one / "plugins" for one in homes))


def _under(base: Path) -> list[Path]:
    """Every directory under a plugins root that carries a launcher, at any depth up to two.

    Shallow on purpose: a marketplace unpacks to `<root>/<marketplace>/<plugin>` and a cache
    to `<root>/<name>`, and a full walk of a config directory is a scan of somebody's whole
    plugin collection for a command that should cost milliseconds.
    """
    out: list[Path] = []
    try:
        for one in sorted(base.iterdir()):
            if not one.is_dir():
                continue
            out.append(one)
            out += [two for two in sorted(one.iterdir()) if two.is_dir()]
    except OSError:
        return []
    return out


def _asked(home: Path) -> str:
    """What this tree answers to `--version`, or `""` where it cannot be run at all.

    The subprocess is the point (see :func:`candidates`), and every failure is `""`: a tree
    that raises, hangs past the timeout or is not Python is not a candidate, and none of that
    is worth failing the command over while another copy may be fine.
    """
    import subprocess  # noqa: PLC0415 - RK260

    try:
        done = subprocess.run(
            [sys.executable, str(home / LAUNCHER), "--version"],
            capture_output=True,
            text=True,
            timeout=_ASKED_TIMEOUT,
            check=False,
        )
    except (OSError, ValueError, subprocess.SubprocessError):
        return ""
    if done.returncode != 0:
        return ""
    return _version_in(done.stdout)


#: The number inside a `--version` line, wherever it sits in it. `argparse` prints `roadkeep
#: 0.1.963 (479d7266 modified, D:\…\src\roadkeep)` — the provenance RK79 added — so taking the
#: last token reads the *path* as the version and every candidate ties at nothing. Anchored on
#: a dotted run of digits, which is the one shape a version has and no path fragment does.
_VERSION_RE = re.compile(r"\b(\d+(?:\.\d+)+)\b")


def _version_in(said: str) -> str:
    """The version a `--version` line states, or `""` where it states none.

    Read out of the line rather than assumed to *be* it, because the line carries more than
    the number by design: this tool's own `--version` names the commit, whether the tree is
    modified, and where the package is — the facts RK79 added so two copies could be told
    apart, and exactly the ones that break a positional read.
    """
    found = _VERSION_RE.search(said)
    return found.group(1) if found else ""


#: Seconds one candidate may take to say what it is. Generous for a cold import and short
#: enough that six of them do not make `install` feel hung.
_ASKED_TIMEOUT = 30


def vendor(root: str | Path = ".", *, checked: bool = False) -> Vendored:
    """Copy the highest-versioned engine this machine can reach into the project (RK1193).

    The command two adopting repositories each wrote for themselves. Shio and freewilly carry
    a 147-line `install_roadkeep.py` and a `.cmd` wrapper, byte-identical apart from one
    comment — the same code in two repositories, which is the drift this tool spends its
    backlog refusing everywhere else. `install --vendor` is that, once.

    Four rules, and each is a measurement rather than a preference:

    * **Pick by version, not by position.** Six engines were resolvable on the machine this
      was written on. A search order answers differently per machine; the highest version
      answers the same everywhere, which is what a pin is for.
    * **Skip a working checkout unless `ROADKEEP_SRC` names it.** A tree mid-refactor answers
      a version and then raises out of a half-edited module — an hour, measured.
    * **Exclude `.git`.** With it the copy is a second repository inside the project rather
      than an artefact.
    * **Verify what landed.** The copy is asked its version, and a disagreement is
      :class:`NotVerified` — picking by version proves nothing about a tree that arrived
      different.

    ``checked`` computes and copies nothing, which is `--check`'s contract one command over:
    the choice and the evidence for it are the whole answer, and reporting them costs the same
    walk either way.
    """
    import shutil  # noqa: PLC0415 - RK260

    base = Path(root).resolve()
    found = candidates(base)
    usable = [one for one in found if not one.working or _named(one)]
    if not usable:
        raise NoEngine([one.why for one in found] or _looked(base))
    chosen = usable[0]
    into = base / PROJECT_ENGINE
    unignored = not _ignored(base)
    if checked:
        return Vendored(into=into, chosen=chosen, considered=found, ignore=unignored)

    if into.exists():
        # Replaced whole rather than merged: a half-old tree is the state every rule above is
        # about, and `shutil.copytree` onto a populated directory is how one is made.
        shutil.rmtree(into)
    shutil.copytree(chosen.home, into, ignore=shutil.ignore_patterns(*_UNVENDORED))
    answered = _asked(into)
    if answered != chosen.version:
        raise NotVerified(chosen.version, answered, into)
    return Vendored(
        into=into,
        chosen=chosen,
        considered=found,
        verified=answered,
        files=sum(1 for one in into.rglob("*") if one.is_file()),
        ignore=unignored,
    )


def _ignored(root: Path) -> bool:
    """Whether a `.gitignore` here already covers the vendored tree (RK1193).

    Read as **text and not through git**, which is the honest bound: this is deciding whether
    to print one line of advice, and shelling out to `check-ignore` would make a report depend
    on a subprocess for a sentence. A project whose rule lives in `.git/info/exclude` or a
    parent's `.gitignore` gets the advice anyway, which is a redundant line and not a wrong one.
    """
    try:
        written = (root / ".gitignore").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return any(
        one.strip().rstrip("/") == PROJECT_ENGINE for one in written.splitlines()
    )


def _named(candidate: Candidate) -> bool:
    """Whether `ROADKEEP_SRC` is what put this working tree on the list."""
    return candidate.why.startswith(f"{ENGINE_SOURCE}=")


def _looked(root: Path) -> list[str]:
    """Where a refusal says it looked, when nothing answered at all."""
    return [one.as_posix() for one in _plugin_roots()] + [
        (root.resolve().parent / "roadkeep").as_posix()
    ]


# -- un-wiring ---------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Withdrawal:
    """One file un-wiring touches, and what it would do to that file (RK138)."""

    path: Path
    #: What the file keeps. ``None`` where nothing of it survives this project's entry, which
    #: is the state `install` created it in and therefore the one to return it to.
    text: str | None
    existed: bool
    #: Whether the file still holds something this command wrote.
    held: bool

    @property
    def state(self) -> str:
        if not self.existed:
            return "absent"
        if not self.held:
            return "untouched"
        return "deleted" if self.text is None else "reduced"

    @property
    def writes(self) -> bool:
        return self.state in ("deleted", "reduced")


@dataclass(frozen=True, slots=True)
class Removal:
    """What `uninstall` would take out, computed before a byte is touched (all-or-nothing)."""

    root: Path
    withdrawals: tuple[Withdrawal, ...]
    #: Paths deliberately left, each with the reason — the other half of the report, for the
    #: reason `install` names what it does not write: a surface silently kept reads as missed.
    kept: tuple[tuple[str, str], ...] = ()

    @property
    def changing(self) -> tuple[Withdrawal, ...]:
        return tuple(withdrawal for withdrawal in self.withdrawals if withdrawal.writes)

    def stated(self, checked: bool) -> str:
        """Every file the un-wiring touches, and what it did — or would do — to it (RK138).

        Beside :meth:`payload` and :meth:`verdict` since RK1170, in :class:`Plan`'s shape and
        for its reason: this is the same command pointed the other way.
        """
        rows = [f"{self.root.as_posix()}  ←  this project's own entries"]
        for withdrawal in self.withdrawals:
            state = _WOULD_REMOVE[withdrawal.state] if checked else withdrawal.state
            rows.append(f"  {state:<14} {withdrawal.path.relative_to(self.root).as_posix()}")
        rows += [f"  kept           {why}" for _, why in self.kept]
        return "\n".join(rows)

    def verdict(self) -> list[str]:
        """What a `--check` has to say on **stderr**, where anything is left wired."""
        if not self.changing:
            return []
        return [
            f"{len(self.changing)} surface(s) still wire this project to a checkout: "
            f"`{invocation()} uninstall` takes them out"
        ]

    def payload(self, checked: bool) -> dict[str, object]:
        return {
            "root": self.root.as_posix(),
            "checked": checked,
            "surfaces": [
                {
                    "path": withdrawal.path.relative_to(self.root).as_posix(),
                    "state": withdrawal.state,
                    "writes": withdrawal.writes,
                }
                for withdrawal in self.withdrawals
            ],
            "kept": [{"path": path, "why": why} for path, why in self.kept],
            "changing": len(self.changing),
        }


#: The same rule as :data:`_WOULD` for the other direction (RK138). `absent` and `untouched`
#: describe no write either, so only the two states that take something out are conditional.
_WOULD_REMOVE = {
    "deleted": "would delete",
    "reduced": "would reduce",
    "absent": "absent",
    "untouched": "untouched",
}


def removal(root: str | Path = ".") -> Removal:
    """Read the project's own surfaces and answer what un-wiring would take out.

    Reads no checkout, unlike :func:`plan`: the wiring is recognised by *this project's own
    entry* — the server's name, and the launcher a hook command runs — so a project can be
    un-wired after the checkout it pointed at is gone, which is the case that produced RK138.

    What is reported as kept is read off the disk (RK284). It used to be a constant, so a
    project `install` had just told "no `.github/workflows/` — this project has no CI to gate"
    was told at `uninstall` that CI stays wired and to delete a path that was not there. A
    surface never present was not kept, and naming it does the thing this field exists to
    prevent — "a surface silently kept reads as missed" — from the other side.
    """
    base = Path(root).resolve()
    if _ships_the_plugin(base):
        raise NotAnAdopter(base)
    kept: list[tuple[str, str]] = []
    if (base / PROJECT_WORKFLOW).is_file():
        # Absence gets no line of its own. `install` says why it wrote nothing, because an
        # adopter has to know CI was considered; here there is nothing to have kept, and a
        # sentence about a file that does not exist is the report this task is about.
        kept.append(
            (
                PROJECT_WORKFLOW,
                f"{PROJECT_WORKFLOW}: the gate calls the published action and not this "
                f"checkout, so CI stays wired — delete it to stop gating",
            )
        )
    return Removal(
        root=base,
        withdrawals=(
            _withdrawn(base / PROJECT_MCP, _without_server),
            _withdrawn(base / PROJECT_SETTINGS, _without_guard),
            _dropped(base / PROJECT_SKILL),
            # And the pages it points at, for the reason the skill itself is dropped (RK1437):
            # a reference left behind is a copy of this tool's rules that nothing refreshes.
            *(_dropped(base / page) for page in PROJECT_PAGES),
            # Unconditionally, and `_dropped` answers `held=False` where it is not there
            # (RK1108): `removal` reads no checkout and cannot know whether the wiring it is
            # taking out was written with `--committed`, so asking the disk is the only reading
            # available — which is the rule RK284 already established for what is *kept*.
            _dropped(base / PROJECT_BRIDGE),
        ),
        kept=tuple(kept),
    )


def uninstall(root: str | Path = ".") -> Removal:
    """Take this project's entries out of the four surfaces, or take nothing out.

    The inverse of :func:`install` and held to its two rules: the declarations keep everything
    that is not this project's entry, and a file that is not a JSON object is refused rather
    than rewritten. A file left holding nothing but what this command wrote is *deleted*,
    because `install` created it and an empty declaration reads as a project that declares
    something.
    """
    intent = removal(root)
    for withdrawal in intent.changing:
        if withdrawal.text is None:
            withdrawal.path.unlink()
            _prune(withdrawal.path.parent, intent.root)
        else:
            withdrawal.path.write_text(withdrawal.text, encoding="utf-8", newline="")
    return intent


def _withdrawn(path: Path, without) -> Withdrawal:
    """One declaration with this project's entry taken out, as a :class:`Withdrawal`.

    Compared as parsed JSON for the reason :func:`_declaration` is: an adopter's indentation
    is not a wiring, and a command that reported one would report every project as wired.
    """
    if not path.is_file():
        return Withdrawal(path=path, text=None, existed=False, held=False)
    try:
        loaded = json.loads(_read(path))
    except json.JSONDecodeError as error:
        raise Unreadable(path, str(error)) from error
    if not isinstance(loaded, dict):
        raise Unreadable(path, f"read as {type(loaded).__name__}")
    left = without(loaded)
    return Withdrawal(
        path=path,
        text=None if not left else json.dumps(left, indent=2, ensure_ascii=False) + "\n",
        existed=True,
        held=left != loaded,
    )


def _dropped(path: Path) -> Withdrawal:
    """The copied skill: a file this command owns whole, so there is nothing to reduce."""
    existed = path.is_file()
    return Withdrawal(path=path, text=None, existed=existed, held=existed)


def _without_server(current: dict) -> dict:
    """`.mcp.json` without this project's server, every other key in its own place."""
    servers = {name: entry for name, entry in current.get("mcpServers", {}).items() if name != SERVER}
    left = {}
    for key, value in current.items():
        if key != "mcpServers":
            left[key] = value
        elif servers:
            left[key] = servers
    return left


def _without_guard(current: dict) -> dict:
    """`.claude/settings.json` without the guard's three events and the server's approval.

    An event left with no groups is dropped rather than emptied, and so is `hooks` itself: a
    declaration that holds an empty list is a project that declares a hook, which is exactly
    the reading un-wiring exists to end.
    """
    left: dict = {}
    for key, value in current.items():
        if key == "enabledMcpjsonServers":
            approved = [name for name in value if name != SERVER]
            if approved:
                left[key] = approved
        elif key == "hooks":
            events = {
                event: kept
                for event, groups in value.items()
                if (kept := [group for group in groups if not _ours(group)])
            }
            if events:
                left[key] = events
        else:
            left[key] = value
    return left


def _prune(directory: Path, root: Path) -> None:
    """Remove the directories the deleted copy was alone in, and stop at the project root.

    `install` created `.claude/skills/roadkeep/`, so leaving it behind empty leaves a project
    that looks as though it vendors a skill. Anything else in there is somebody's, and an
    empty parent that this command did not create — `.claude/` on a project whose settings
    were only ever this tool's — is the same fact one level up.
    """
    while directory != root and directory.is_dir() and not any(directory.iterdir()):
        directory.rmdir()
        directory = directory.parent


def _merged_mcp(current: dict, server: dict) -> dict:
    merged = dict(current)
    servers = dict(merged.get("mcpServers", {}))
    servers[SERVER] = server
    merged["mcpServers"] = servers
    return merged


def _merged_settings(current: dict, hooks: dict) -> dict:
    """Approve the server and wire the guard, leaving every other setting where it is.

    A project `.mcp.json` waits for approval, and a server awaiting approval is one that
    never ran — indistinguishable, from the session's side, from one never declared.
    """
    merged = dict(current)
    enabled = list(merged.get("enabledMcpjsonServers", []))
    if SERVER not in enabled:
        enabled.append(SERVER)
    merged["enabledMcpjsonServers"] = enabled

    events = dict(merged.get("hooks", {}))
    for event, groups in hooks.items():
        # Ours dropped and re-added rather than edited in place: the launcher path is what
        # moves between runs, and a match on it is the one thing that would stop matching.
        kept = [group for group in events.get(event, []) if not _ours(group)]
        events[event] = kept + groups
    merged["hooks"] = events
    return merged


#: Every launcher spelling this command writes into a hook, which is what recognising its own
#: entry means (RK1108). Two since the bridge: a match on the checkout's `scripts/roadkeep.py`
#: alone did not see a `--committed` wiring — so a re-run appended a second identical group to
#: all three events instead of replacing its own, and `uninstall` left the guard in place. The
#: comment beside `_merged_settings` had named this exact failure ("a match on it is the one
#: thing that would stop matching") one flag before it happened.
_LAUNCHERS = (LAUNCHER, PROJECT_BRIDGE)


def _ours(group: dict) -> bool:
    """A hook group this command wrote, recognised by the launcher it runs."""
    return any(
        any(spelling in hook.get("command", "") for spelling in _LAUNCHERS)
        for hook in group.get("hooks", [])
    )


def _read(path: Path) -> str:
    """Every file this module compares, read one way: UTF-8, newlines normalised.

    A checkout on Windows can hold the skill with CRLF endings; a copy that differed from its
    source only in those would be reported stale forever and rewritten on every run.
    """
    return path.read_text(encoding="utf-8")
