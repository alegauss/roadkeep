# roadkeep — Design rationale

> Rationale for **unshipped** sections only. Status markers live in
> [ROADMAP.md](ROADMAP.md); shipped work is described in
> [CHANGELOG.md](CHANGELOG.md) and `git log`. When a section ships, delete it here.

## §0 — Why this exists

### §0.1 The measured problem

Three files in the Viglet Shio repository declare a format and none enforces it:

| Artefact | Rule | Reading |
|---|---|---|
| `docs/ROADMAP.md` | one sentence per task | 92 active lines, **142 words** average, worst **1406 characters** (7× the best) |
| `agents.md` | index only, resident every turn | grew to **186 KB (~46k tokens)** before it was split |
| `docs/IMPROVEMENTS.md` | rationale for *unshipped* work | accreted shipped implementation reports; the sibling project's reached **539 KB** |

The pattern is identical in all three: an author with the whole design in working
memory writes it where the reader will be, and the reader is a file that gets loaded
every turn. Shio measured this in SH341 and found **six of the eight worst lines were
written in the session that then diagnosed the problem** — so this is a drift the
process invites, not a lapse of attention. An instruction to be terse does not survive
the moment its author knows more than the line allows.

### §0.2 Why the fix is a write path, not a linter

A linter reports after the prose exists, and by then the cost is already paid: the
tokens were spent generating it, and the author is being asked to delete work. A field
with `maxLength: 200` refuses at the point of insertion, before a sentence is composed
to fill it. Same rule, two orders of magnitude cheaper — and it converts an analytical
act ("is this line too long, and what would I cut?") into a procedural one ("call
`add`"). **The saving is the analysis, not the characters.**

### §0.3 The six laws

| # | Law |
|---|---|
| L1 | **The format is a schema, enforced where the text is created** — `add` refuses; `lint` is the backstop for what bypassed it. |
| L2 | **The store is the repository** — Markdown, greppable, diffable, no database and no service. |
| L3 | **Round-trip or don't write** — parse → render → byte-identical, or the tool may not own the file. |
| L4 | **The tool never writes prose** — it validates and renders. A generator would reintroduce the drift. |
| L5 | **Query instead of read** — every question a maintainer asks the file is a command, so answering it costs no context. |
| L6 | **Configuration, not convention** — prefix, paths, markers and limits are declared per project. |

L5 is the one that pays for the rest. `pick` replaces loading 558 lines to find one
task; `stats` replaces a grep whose misses are silent; `show` replaces joining two
files by hand. Those three are most of what an agent currently spends a roadmap
session doing.

### §0.4 The limits, measured against a live corpus

§0.1 asked whether the limits are right or the lines are. Shio's 78 active lines answer
it, and the answer is split in a way that only a real backlog could have produced — the
reading RK20 took:

| Field | Limit | p50 | p90 | max | Over |
|---|---|---|---|---|---|
| `symptom` | 120 | 58 | 86 | 111 | **0 of 78** |
| `why` | 200 | 481 | 900 | 1251 | **70 of 78** |

The same authors, in the same lines, met one limit every single time and missed the
other 89% of the time. So 89% is not evidence that 200 is too small — `symptom` is the
control, and it shows compliance is available. The difference is that "what does not
work" is one clause by construction and a `why` has no natural end, which is L1 stated
as a measurement: the field whose scope is unbounded is the one that needs the bound at
the write path.

And the migration is smaller than that task assumed. **74 of the 78 pointers resolve,
and none dangle**; 67 of the 70 over-length lines point at a section that already exists
and makes the same argument — compared line-against-section on SH295 and SH309, the
`why` is a recompression of the paragraph, same examples and all. The rationale is not
homeless. The line is a second copy of it, so the edit is compression against a text
already written, not authorship.

## Block A — The model

## Block B — Authoring

## Block C — Query

## Block D — The gate

## Block E — Adoption

### §RK1740 install --vendor deletes the capture inbox it shares a folder with

Measured on 2026-11-12, refreshing seventeen vendored projects under `D:\Git` with
`install --vendor --committed`: multi-agent, japode/ads and japode/schools each held a
`.roadkeep/reports/` and no engine, and after the run each held the engine and no
reports. `vendor` replaces `.roadkeep/` whole with `shutil.rmtree`, which is right for
the engine (a half-old tree is the state RK1193 exists to prevent) and wrong for the one
directory under it the engine does not own.

`capturing.REPORTS` puts the capture inbox at `.roadkeep/reports` (RK89), and the same
run that writes a capture adds `.roadkeep/` to `.gitignore`. So the reports are in no
history: a refresh that deletes them deletes the only copy, and nothing in the report
said a file outside the engine went with it.

The replacement should own what it copied and nothing else: move `reports/` (or anything
the engine did not ship) aside before the removal and back after it, or remove only the
engine's own directories. Either way the report names what it kept.

Done when `install --vendor` over a `.roadkeep/` holding captures leaves every capture
byte-identical, and a test holds it.

### §RK1741 A vendored copy is a cache that never refreshes

Measured on 2026-11-12 across the 57 projects under `D:\Git` that declare a
`roadkeep.toml`: thirteen vendored copies stood between 0.2.473 and 0.2.511 while the
checkout on the same machine stood at 0.2.576, and four projects whose settings pin
`ROADKEEP_HOME` to `${CLAUDE_PROJECT_DIR}/.roadkeep` held no engine there, so the
launcher refused every command (RK1678). Bringing them level took a hand-run sweep.

The copy exists for Claude Code on the web, where no plugin installs, and `.roadkeep/`
is gitignored, so it is not a pin a commit carries: it is a per-machine cache. A cache
that never refreshes is the drift this tool's L1 argument was written against, one level
down. It also outranks the checkout locally: the launcher reads `.roadkeep/` before the
sibling, and a project's `env` pin outranks a user-level `ROADKEEP_HOME`.

The guard already compares versions at `SessionStart` for `install.stale`. Where the
running engine is newer than the vendored copy, or the pinned tree holds no engine, it
can run the refresh `install --vendor` does and say so, rather than leave the next
session to meet a refusal about a format its copy predates (RK1739). A sweep over
sibling projects, `install --vendor --all` or similar, covers the projects no session
opens.

Done when a session opening a project whose vendored copy is older than the reachable
engine finishes `SessionStart` running the newer one, and names the versions it moved.

## Block F — The plugin

### §RK1739 A wholesale grammar failure blames the file when the engine is the stale one

Measured on 2026-11-12 in winwright: the roadmap's four open lines all carry the `(from:
…)` clause RK1723 introduced, and a served tool answered that the grammar fails on 4 of
4 bullets, that no `[grammar]` is declared, and that the file was written under another
format. `lint` from the current engine reads the same file clean. The server had started
before RK1723's commit, so the format it lacked was newer than itself.

The refusal reasons only about the file. It already holds the fact that would have
answered: `roadkeep.toml` records `[install] wired`, the version that wired the project,
and the running engine knows its own. When every bullet fails and the running engine is
older than the wired one, the likelier cause is the engine, and the remedy is restarting
the server or refreshing the copy, not rewriting the file.

Two smaller defects ride along. An empty `[grammar]` table is reported as undeclared,
which contradicts a file the reader can open. And the message gives no version at all,
so telling a stale process from a foreign format takes a second session.

Done when a wholesale grammar failure under an engine older than `wired` names both
versions and the restart, and an empty `[grammar]` is reported as declared but empty.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)

## Block J — Validation (whether a person ever tried it)

## Block K — The desktop app (one installer for the reader and the plugin)

## Block L — Product sites on the package

### §RK1729 Both sites on the package's build

The pitch prerenders through the design system's `prerenderSite` (VDS215), keeping only
its `markdown.mjs` converter and a `robots.txt` naming the docs sitemap; its output was
byte-identical.

**The gui landing** (`gui/site/scripts/prerender.mjs`) cannot follow yet: its head
carries `<link rel="alternate" type="text/markdown">` per route, and `prerenderSite` has
no hook for it. Patching the HTML afterwards would leave the manifest's byte counts
stale. The hook landed as VDS243 (`headTags`, committed locally in viglet-design-system,
not yet published); once a release carries it, the gui moves the same way, and its
social card can take `renderOgCard` from `./vite` in place of `scripts/og-image.mjs`.

**The registry** is done, committed locally there (2026-11-05): the design system's
`consumers.json` gains both sites (`chrome: "product-site"`, `tone: "cool"`, accent
amber, entries `./site`, `./site.css`, `./tokens.css`, `./vite`), and the hub's
`projects.json` changes roadkeep from slate `148,163,184` to the amber the pitch uses,
`245,158,11`.

Done when the gui has no prerender of its own beyond what `prerenderSite` cannot do,
both sites' tests pass on the built output, and both registries name both sites.

## Block M — Codex integration (one engine, host-specific adapters)

### §RK1731 Codex shell and lifecycle decisions

Evidence: Refusal.decision returns ask for Bash, and the executable guard emits
permissionDecision=ask. The Codex hook documentation states this result is unsupported
in PreToolUse and the tool call continues after the hook failure. This is a
compatibility defect, not a request to weaken Claude behavior.

Scope: define the Codex policy for shell mentions of governed paths and serialize only
supported outcomes. Block confirmed prohibited writes with an actionable Roadkeep
command. Preserve the existing exemptions for legitimate Roadkeep invocations and safe
Git staging/history operations. For ambiguous commands, choose and document a deliberate
supported refusal policy; do not emulate an approval by returning allow or relying on
PermissionRequest to run when no approval is needed. Keep host-independent ownership
checks shared.

Acceptance: executable payload tests demonstrate no unsupported ask output, rejection of
prohibited redirection/script writes, and successful approved Roadkeep mutations and Git
add/commit workflows. Cover quoting, spaces, Windows shells, newline-separated commands
and command operators. Verify SessionStart context and Stop lint results use supported
Codex outputs, including recursion protection and timeouts.

Limits: do not introduce a general shell interpreter or promise complete prevention of
computed-path writes. Keep the existing attestation, lint and CI backstops, and preserve
Claude ask semantics in its own adapter.

Official references to recheck when implementing: https://learn.chatgpt.com/docs/hooks

### §RK1732 Codex workspace binding for the existing MCP server

Evidence: the existing Python MCP server passed initialize and tools/list with 67 tools
when started explicitly in the site repository. Its default directory is the process
working directory; that smoke test did not establish Codex plugin startup behavior. A
plugin-root cwd copied from an example would target the package instead of the user's
project.

Scope: establish the workspace binding contract for Codex local stdio startup, tools and
diagnostics, using supported client context or an explicit configured project directory.
Reuse serving.py and the CLI dispatch. Preserve dynamic schemas, readOnlyHint
annotations and configuration refresh behavior. Keep each worktree and simultaneous
project isolated, and refuse missing or ambiguous project identity with a usable
configuration remedy. Likely seams: serving.py, launcher arguments and Codex MCP
configuration.

Acceptance: initialize, tools/list and representative read/write calls run against
temporary repositories with distinct prefixes and configs. Starting from a plugin cache,
a subdirectory or another project cannot silently select that backlog. Verify two
concurrent workspaces, paths containing spaces, Windows launch behavior and schema
changes within a session. Standard output remains JSON-RPC only; startup diagnostics use
stderr.

Limits: no hosted service, database, duplicate engine or supported Python API. Require
the existing Python runtime and use the same repository-backed transactions.

Official references to recheck when implementing:
https://learn.chatgpt.com/docs/extend/mcp

### §RK1733 Host-aware installation and engine provenance

Evidence: provenance.py resolves installed plugins through CLAUDE_CONFIG_DIR and the
Claude registry; installing.py names Claude manifests and project settings. Existing
duplicate-hook suppression must not interpret a cached Codex directory as evidence that
a plugin is active.

Scope: introduce host-aware installation and engine discovery, covering native plugin
activation and repository wiring. Adapt invocation hints, served tool naming, engines
output and stale-surface diagnostics to the selected host. Derive names from the actual
connection rather than assuming Claude-prefixed MCP tool names. Preserve ROADKEEP_HOME
selection, vendored-engine precedence and the no-network launcher contract. Likely
seams: provenance.py, installing.py, launcher discovery and diagnostics tests.

Acceptance: test enabled, disabled, absent and outdated Codex installations; multiple
user config roots; stale caches; native plus committed wiring; and simultaneous
Claude/Codex use. A cached but inactive plugin must not suppress a live project guard.
Hook execution is not duplicated when both supported declarations are active. Missing
engines or untrusted hooks must be reported honestly rather than presented as enforced.

Limits: no broad scan of unrelated credentials or user files, no automatic trust grants
and no background download. Preserve current Claude engine-selection behavior. Pin
fixtures to observed supported configuration contracts and record the tested Codex
versions.

Official references to recheck when implementing:
https://learn.chatgpt.com/docs/config-file/config-basic

### §RK1734 Shared skills and Codex workflow entry points

Evidence: plugin/skills/roadkeep already uses SKILL.md, while plugin/commands/add.md and
its siblings contain Claude-specific allowed-tools, slash-command arguments and
CLAUDE_PLUGIN_ROOT references. The domain workflow is reusable; those invocation
contracts are not automatically portable.

Scope: keep one authoritative Roadkeep skill and shared reference pages, adapting
host-specific launch and tool hints at packaging or installation time. Provide Codex
equivalents for add, ship, pick and lint through supported skill invocation, preserving
each command's behavior. Consider agents/openai.yaml only for useful UI metadata or tool
dependencies. Handle both a connected MCP server and the documented CLI fallback. Likely
seams: plugin/skills, plugin/commands and generated installation surfaces.

Acceptance: every referenced file and command exists in a clean package; the Codex skill
discovers session tools without hardcoded Claude names; fallback execution reaches the
selected engine. Preserve the add command's exact-user-words rule, missing-field
behavior, claims, non-goals and one-task-per-commit guidance where applicable. Compare
generated instructions to their shared source so fixes cannot drift between hosts.

Limits: no model-based prose generator, duplicate authored manuals or assumed parity of
Claude frontmatter. Keep Codex workflow files discoverable without copying an every-turn
manual into AGENTS.md.

Official references to recheck when implementing:
https://learn.chatgpt.com/docs/build-skills

### §RK1735 Codex project installation lifecycle

Evidence: installing.py currently writes .claude/settings.json, .claude/skills/roadkeep
and .claude/hooks/roadkeep-launch.py. Codex uses different configuration and skill
discovery locations; copying those files does not activate equivalent behavior.

Scope: add an explicit host selector, such as install --host codex, after confirming the
final CLI spelling. Support project-scoped .codex/config.toml, .agents/skills and
supported hook declarations, plus a committed launcher where required. Reuse
installation planning and ownership rules. Extend check, refresh and uninstall to the
selected host. Respect trusted-project configuration and explicit hook trust; report the
required review without enabling bypass flags or silently trusting code.

Acceptance: dry-run/check performs no writes; first install, repeat install, refresh and
uninstall have deterministic results. Existing TOML settings, unrelated MCP servers,
skills, comments where supported, and Claude wiring survive. Malformed configuration is
refused without overwriting it. Test paths with spaces, Windows and POSIX launchers,
native-plugin coexistence and an engine unavailable in the target environment. Removal
deletes only Roadkeep-owned wiring and preserves the adopter's CI policy.

Limits: do not change the default host for existing users without an explicit
compatibility decision. No credentials, machine-wide permission changes, network
bootstrap or automatic trust approval.

Official references to recheck when implementing:
https://learn.chatgpt.com/docs/config-file/config-basic
https://learn.chatgpt.com/docs/hooks

### §RK1736 Portable Codex package and local marketplace

Evidence: plugin/.claude-plugin/plugin.json declares the current package, whose MCP
configuration uses CLAUDE_PLUGIN_ROOT. The local Codex CLI exposes plugin management,
and official packaging supports a portable root manifest plus OpenAI-specific extension
fields. Native Codex loading has not yet been tested for Roadkeep.

Scope: add the portable plugin.json and root mcp.json, using a supported stdio
declaration and PLUGIN_ROOT where required. Retain the Claude manifest and entry point.
Bundle the shared engine, skills, host hook declarations and any required listing
assets. Add a local marketplace entry for development installation, with paths relative
to the catalog. Extend version-stamping and packaging tests so all manifests derive from
the existing single version authority.

Acceptance: validate schemas, package contents, executable paths and root-relative
references. Install from a clean local package or marketplace, outside the development
checkout, and verify the selected workspace and hook trust flow. Test upgrade, disable
and removal; preserve Claude discovery and avoid loading one hook definition twice.
Document Python >=3.11 as the local runtime requirement.

Limits: no API key, hosted MCP endpoint, remote publication or duplicate engine. Public
directory eligibility is handled as a documented distribution constraint, not inferred
from a successful local installation.

Official references to recheck when implementing:
https://developers.openai.com/plugins/build/plugins

### §RK1737 Native Codex enforcement and compatibility evidence

Scope: add a repeatable integration harness over disposable repositories and the
packaged plugin. Test the actual Codex runtime in addition to unit payload fixtures;
record client versions, operating system, configuration and hook trust state. Begin with
local Codex desktop/CLI surfaces that can be exercised. Test the IDE and remote surfaces
separately before claiming parity.

Acceptance: in a fresh trusted session, SessionStart identifies the selected engine;
apply_patch attempts on each governed role are denied; the equivalent Roadkeep
transaction succeeds; normal source edits and permitted Git operations work; Stop
reports actionable lint findings without a loop. Verify unsupported hook outputs cannot
silently authorize a write. Exercise multiple files, nested repositories, two worktrees,
blocked startup, missing Python, disabled/untrusted hooks, update and uninstall. Confirm
MCP initialization, schema refresh and representative read/write tools.

Run the Python suite and existing plugin/launcher tests to protect Claude behavior;
inspect CI corpus skips rather than treating skipped real-file coverage as proof. Keep
generated runs and credentials out of the repository, retaining only reproducible
fixtures and a concise compatibility report.

Limits: acceptance is observed behavior for named versions and surfaces. Hooks are a
workflow guardrail with known coverage limits; the tests must not claim an
operating-system security boundary or install plugins in the user's personal environment
without an explicit test choice.

Official references to recheck when implementing: https://learn.chatgpt.com/docs/hooks

### §RK1738 Codex adoption and distribution documentation

Scope: document the tested Codex installation paths in the product README and
documentation area, updating shared copy sources rather than duplicating divergent
prose. Explain the native local plugin, project-scoped fallback, Python requirement,
workspace binding, hook trust, MCP tools, skills, check/update/uninstall and
troubleshooting. Include exact commands tested by the integration task and a versioned
surface matrix for desktop, CLI, IDE and remote execution.

Explain what changes compared with Claude, which engine and Markdown contracts stay
shared, and how to recover when hooks are disabled, untrusted or unavailable. Retain
CI/pre-commit guidance as backstops and distinguish workflow enforcement from a security
boundary.

Distribution: recheck official OpenAI rules at implementation time. Record whether
bundled hooks are eligible for the public directory and whether local stdio submission
needs publisher approval. Present manual/local installation as a separate verified path.
If public submission remains unavailable, document that limitation without claiming an
upcoming approval or creating a hosted service. Provide a concrete maintainer checklist
for identity, assets, package validation and eligibility if submission is later
authorized.

Acceptance: a clean-room adoption follows the guide successfully; all links and commands
resolve; marketing claims match the compatibility report. No directory submission,
account registration, launch campaign or public publication belongs to this task.

Official references to recheck when implementing:
https://developers.openai.com/plugins/deploy/desktop-only
https://developers.openai.com/plugins/build/plugins
