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
  with that same trust, and the failure arrives in the shell an agent fell back to.
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
from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep.adopting import BlockedParent, blocking
from roadkeep.config import CONFIG_NAME, Config
from roadkeep.linting import lint
from roadkeep.merging import ATTRIBUTES, Registration, register
from roadkeep.provenance import Engine, Installed, engine, installed
from roadkeep.provenance import invocation

#: The server's name, which is also the prefix an agent reads on every tool it offers.
SERVER = "roadkeep"

#: What the plugin ships, relative to its root. Read, never rewritten: these four are the
#: source this command translates, and a fifth would be a decision this module invented.
LAUNCHER = "scripts/roadkeep.py"
PLUGIN_HOOKS = "hooks/hooks.json"
PLUGIN_MCP = ".claude-plugin/mcp.json"
PLUGIN_SKILL = "skills/roadkeep/SKILL.md"
PLUGIN_MANIFEST = ".claude-plugin/plugin.json"
#: The self-locating bridge, for the environment that installs no plugin and has no checkout
#: to point at (RK1108). Copied rather than translated: it is a program and not a declaration,
#: and the one fact `install` substitutes elsewhere — where the engine is — is the question
#: this file exists to answer at runtime.
PLUGIN_BRIDGE = "hooks/roadkeep-launch.py"

#: The five together, which is both what a tree must carry to be translated *from* and what
#: says a tree is the plugin rather than an adopter of it (RK235). One list, so the two
#: questions cannot come to disagree about what carrying the plugin means.
CARRIED = (LAUNCHER, PLUGIN_HOOKS, PLUGIN_MCP, PLUGIN_SKILL, PLUGIN_MANIFEST)

#: Where each lands in the adopting project. The skill path is the loader's convention —
#: `.claude/skills/<name>/SKILL.md` — and the workflow is a file of its own rather than a job
#: spliced into an existing one: merging YAML would need a parser this tool does not have,
#: and a job appended to somebody's pipeline is an edit to a file they own.
PROJECT_MCP = ".mcp.json"
PROJECT_SETTINGS = ".claude/settings.json"
PROJECT_SKILL = ".claude/skills/roadkeep/SKILL.md"
PROJECT_WORKFLOW = ".github/workflows/roadkeep.yml"
#: Where the bridge lands, beside the hooks that run it (RK1108). Inside the repository on
#: purpose: the environment it exists for reads what is committed and nothing else, so a path
#: pointing anywhere outside would be a path that resolves on one machine.
PROJECT_BRIDGE = ".claude/hooks/roadkeep-launch.py"

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
        rows = [f"{self.source.as_posix()}  →  {self.launcher}"]
        if self.carried:
            # Said because the header alone does not (RK1113): the launcher is a path, and a
            # reader who passed no flag has to be told the path came from their own project
            # rather than from a default that is about to overwrite it.
            rows.append(
                f"  committed      this project already runs {PROJECT_BRIDGE}, so the "
                f"wiring stays on it — `uninstall` then `install` moves it to a checkout"
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
        return "\n".join(rows)

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
            rows.append(
                f"{len(differing)} surface(s) differ from what this checkout ships: "
                f"`{invocation()} install` writes them"
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
            "surfaces": [
                {
                    "path": surface.path.relative_to(self.root).as_posix(),
                    "state": surface.state,
                    "writes": surface.writes,
                }
                for surface in self.surfaces
            ],
            "skipped": [{"path": path, "why": why} for path, why in self.skipped],
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
    origin = Path(source).resolve() if source is not None else _source()
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
        described = (
            MERGE.format(invocation=invocation())
            if driver is None
            else MERGE_BLOCKED.format(blocker=driver.name)
        )
        skipped.insert(0, (described.split(":")[0], described))
    debt = _standing(base) if gauging else None
    if own:
        skipped.insert(0, (PROJECT_SKILL, f"{PROJECT_SKILL}: {_OWN_SKILL}"))
    else:
        surfaces.append(
            _copy(base / PROJECT_SKILL, _skill(origin, launcher, committed=committed))
        )
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
    if governed is not None:
        intent = replace(intent, registered=register(governed))
    return intent


def stale(root: str | Path = ".") -> tuple[str, ...]:
    """The vendored surfaces that have drifted from the checkout answering here (RK234).

    `--check` is what RK100 named as holding the copy in step, and nothing in an adopting
    project ran it: Turing's `SKILL.md` was 78 lines behind and its `PreToolUse` matcher was
    missing `Bash` — a guard narrower than the one the plugin ships, in the file that decides
    whether the guard fires. So the question is asked where it is cheap to ask and useful to
    answer: the session start, in the process that is already the wired checkout.

    **What a project that is not wired pays is one `is_file`.** The vendored copy is the
    discriminator, and a plugin-served project has none — there is nothing to drift, and the
    plugin's own surfaces are whatever the session loaded. A wired one pays four small reads
    and two JSON parses, and never the gate: ``gauging=False``, the workflow being written
    once and then the adopter's, so it is excluded here by the same field that says so.

    Measured against RK176's 43ms floor, which is the budget this spends from: **0.07ms**
    unwired and **0.86ms** on Dumont, wired. The gate would have been 40ms of that floor on
    its own, which is why declining it is a parameter rather than a comment.

    Every failure is silence, exactly as the notice this feeds is (RK82): a session that
    cannot start because a checkout moved is worse than one told nothing, and `install
    --check` still answers on demand.
    """
    base = Path(root).resolve()
    if not (base / PROJECT_SKILL).is_file():
        return ()
    try:
        intent = plan(base, gauging=False)
    except (ValueError, OSError):
        return ()
    return tuple(
        surface.path.relative_to(base).as_posix()
        for surface in intent.changing
        if surface.refresh
    )


#: What :attr:`Engines.verdict` answers (RK418). Three and not two, because a checkout with
#: uncommitted work is at no commit the plugin could match — so `agreed` would be the defect
#: and `behind` a direction nothing measured.
AGREED = "agreed"
BEHIND = "behind"
UNPINNABLE = "unpinnable"


@dataclass(frozen=True, slots=True)
class Engines:
    """The three copies of this tool one project runs, read back together (RK415).

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
    #: `(file, ref)` per workflow step calling the action, in file order.
    gates: tuple[tuple[str, str], ...] = ()

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
    def agree(self) -> bool:
        """Whether the two engines that state a version are the same copy of this tool.

        The gate is deliberately not in this: `main` and `v0.2.1` and `./` are refs, and a
        ref is not a number to compare — what CI runs is decided when CI runs. It is reported
        beside the two because a reader comparing them needs to know a third exists.

        `unpinnable` is **not** agreement (RK418): a boolean has to fall one way, and the
        state this exists to stop being silent about is exactly the one where the numbers
        match and the files do not.
        """
        return self.verdict == AGREED

    def stated(self) -> str:
        """The three copies, and where they differ (RK415, RK418).

        Beside :meth:`payload` since RK1170. Every absence is **said** rather than left as a
        missing row: "no plugin" and "a plugin this could not read" look the same to a reader,
        and only one of them means the writes are unjudged by a second copy.
        """
        running, plugin = self.running, self.plugin
        rows = [
            f"writing  {running.version:<10}{running.revision}  {running.home.as_posix()}"
        ]
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
        if self.verdict == UNPINNABLE:
            # The state that used to read as agreement, and the one a machine developing this
            # tool is in every day (RK418): the numbers match, the checkout has uncommitted
            # work, and the files the two copies hold are not the same files.
            rows.append(
                f"differ   both state {running.version} and this checkout is modified at "
                f"{running.revision}, so the two cannot be compared: commit, or read a hook's "
                f"refusal as that copy's rule rather than this one's"
            )
        elif not self.agree:
            rows.append(
                f"differ   the pen is {running.version} at {running.revision} and the judge "
                f"is {plugin.version if plugin else '—'} at "
                f"{plugin.revision if plugin else '—'}: `/plugin update` moves the judge, and "
                f"until then a hook's refusal is that copy's rule and not this one's"
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
            "gates": [{"file": where, "ref": ref} for where, ref in self.gates],
            "agree": self.agree,
            # Which of the three, because the boolean above cannot carry the state RK418
            # added: a checkout with uncommitted work is at no commit the plugin could match,
            # and `agreed` there was the defect being fixed.
            "verdict": self.verdict,
        }


def engines(root: str | Path = ".") -> Engines:
    """The three, for one project. Reads four small files and asks git nothing new."""
    base = Path(root).resolve()
    return Engines(running=engine(), plugin=installed(base), gates=gated_at(base))


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
    """
    try:
        config = Config.discover(base)
        if config.source is None:
            return None
        return lint(config).problems
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
