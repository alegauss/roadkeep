<!--
  Assets in site/public/assets/ — the mark is task lines cut at a gate, with the refused
  remainder faded beyond it. The SVGs follow the reader's light/dark theme; a PNG
  cannot, so each carries a fixed dark palette.

    roadkeep-mark.svg     160x160   icon, the header below. Absolute and served by the
                                    site because this file is also the PyPI project page
                                    (RK19): a relative path resolves against pypi.org, and
                                    raw.githubusercontent serves an SVG as text/plain.
                                    Every link below is absolute for the same reason.
    roadkeep-logo.svg     520x160   mark + wordmark
    roadkeep-banner.svg  1200x300   banner source
    roadkeep-banner.png  1200x300   banner
    roadkeep-social.svg  1280x640   source for the link preview
    roadkeep-social.png  1280x640   upload at Settings > General > Social preview.
                                    This is what renders when the repo URL is pasted
                                    into LinkedIn, Slack or a link card anywhere else.
                                    Re-render either PNG after editing its SVG:
                                    msedge --headless=new --window-size=1200,300 \
                                      --screenshot=site/public/assets/roadkeep-banner.png \
                                      file:///.../site/public/assets/roadkeep-banner.svg
-->

<div align="center">

<img src="https://alegauss.github.io/roadkeep/assets/roadkeep-mark.svg" alt="roadkeep logo" width="120">

# roadkeep

**A Claude Code plugin that keeps your `ROADMAP.md`, `CHANGELOG.md` and `IMPROVEMENTS.md` to one format, by refusing the hand-edit and handing the agent the command that writes it properly.**

```sh
claude plugin marketplace add alegauss/roadkeep --scope project
claude plugin install roadkeep@alegauss --scope project
```

Python 3.11+ · zero runtime dependencies · nothing to add to `PATH` · your files stay plain Markdown

**[alegauss.github.io/roadkeep](https://alegauss.github.io/roadkeep/)**: the site, and the
[docs](https://alegauss.github.io/roadkeep/docs/).

</div>

- **Refused before the prose exists.** A task line is fields with limits: `symptom` and `why`
  have a `maxLength`, markers are an `enum`, ids have a pattern. A line that does not fit is
  refused when it is written, not reported by a linter after the tokens are spent.
- **A hand-edit is denied, with the command to call instead.** The hook names the exact
  `add`, `status` or `ship` that does the job, so the right path is also the cheapest one.
- **Ask instead of read.** `pick`, `brief`, `list` and `deps` answer what is next, what blocks
  what and why a task exists, so an agent never reads a whole backlog to find one line.
- **It governs the file you already have.** One line per task in your existing `ROADMAP.md`,
  not a new store to migrate into, and a write that would not round-trip byte for byte is
  refused.
- **The same gate everywhere.** `roadkeep lint` runs as the hook at the end of a turn, as a
  pre-commit hook and as a GitHub Action, and every finding names the command that fixes it.

---

> **Unofficial / community project.** Not affiliated with, endorsed by, or sponsored by
> Anthropic. "Claude" and "Claude Code" are trademarks of Anthropic.

## Install

Run the two commands above in the repository you want governed. You need a **Python 3.11+**
interpreter as `python`; the plugin carries the package itself, so there is nothing to
`pip install`.

`--scope project` writes both declarations into that repository's `.claude/settings.json`:

```jsonc
"extraKnownMarketplaces": { "alegauss": { "source": { "source": "github", "repo": "alegauss/roadkeep" } } },
"enabledPlugins": { "roadkeep@alegauss": true }
```

Commit that file and **every clone is wired**, with no step per machine. What arrives:

- the **hook** that denies a hand-edit of a governed file and names the command, and runs
  `lint` before the turn ends;
- the **MCP tools** (`mcp__roadkeep__*`), whose input schema is *your* project's: its limits,
  its markers, its id shape;
- four **slash commands**, `/roadkeep:add`, `/roadkeep:ship`, `/roadkeep:pick` and
  `/roadkeep:lint`;
- the **skill**, loaded only when a governed file is in play.

Inside an interactive session, `/plugin marketplace add alegauss/roadkeep` and
`/plugin install roadkeep@alegauss` do the same for your user alone.

## First session

The format is declared once per repository, in `roadkeep.toml`. Ask for it:

> Adopt docs/ROADMAP.md under roadkeep, with the prefix SH.

For a backlog you already have, that runs `adopt` first, which measures your file and reports
what a limit would refuse before anything changes. Then it runs `init --existing`, which
declares your roadmap untouched: the prefix comes off the ids it already carries and the
blocks off its own headings. On a new project, a bare `init` writes the config and the empty
files. Years of lines written before the rules can be forgiven by name with `--baseline`, so
the gate goes into CI on the first day. The whole run, with every refusal it printed, is in
[Adopting a backlog you already have](https://alegauss.github.io/roadkeep/docs/adopting/).

From then on, ask in plain words:

> Add a task to block B: the export drops the last line when the file has no trailing newline.

> What should I work on next?

> Ship RK12: export keeps the last line.

Claude calls `add`, `pick` and `ship`. If the symptom is too long, the refusal says by how
much, and `ship` moves the line to the changelog and drops its rationale section in one write.
If Claude reaches for `Edit` on the roadmap out of habit, the hook stops it and names the call.
[In a session](https://alegauss.github.io/roadkeep/docs/session/) covers everything the agent
receives.

## Run it as a gate

`roadkeep lint` exits **1** on a file that drifted and **0** on one that did not. That exit
code is the whole contract, so every surface calls the same command:

```yaml
# .github/workflows/gate.yml — the action this repository ships
steps:
  - uses: actions/checkout@v4
  - uses: alegauss/roadkeep@v0.2.0      # with: {directory: .}

# .pre-commit-config.yaml — the same command, one step earlier
repos:
  - repo: https://github.com/alegauss/roadkeep
    rev: v0.2.0                        # a release tag; `main` tracks unreleased
    hooks:
      - id: roadkeep-lint              # or roadkeep-lint-fix, which normalizes first
```

`--fix` repairs only what the format *derives* — the dep annotation, the pointer, dep order,
an invisible codepoint, whitespace around a field, a queue entry whose task has left, a
criteria heading addressed to nothing — and
leaves every editorial finding to a human, which is what keeps a first run on a real backlog
down to a report somebody reads.

Every finding names the command that closes it. `roadkeep repair` runs the ones that need no
decision, `repair --dry-run` prints them without running, and `roadkeep explain <code>` says
what a finding code means.

## Without Claude Code

```sh
uvx roadkeep lint                  # no install, no checkout
pip install roadkeep               # or into an environment you keep

# A fix that is on main and not yet released: the same run, resolved by URL
uvx --from git+https://github.com/alegauss/roadkeep roadkeep lint
```

Every command takes `--json`, which also says which file and line the answer came from.

### On Claude Code on the web

[Claude Code on the web](https://code.claude.com/docs/en/claude-code-on-the-web) never
installs a marketplace plugin. It reads only what the repository commits, so the plugin
commands above wire nothing there, and an agent with no guard falls back to hand-editing the
governed files. The fix is a small launcher committed to the repository, which the hook and
the MCP server point at instead of the plugin root. It finds an engine at run time, and its
guard stands down where the plugin is installed. [Viglet Shio](https://github.com/openviglet/shio) carries
the reference copy at
[`.claude/hooks/roadkeep-launch.py`](https://github.com/openviglet/shio/blob/main/.claude/hooks/roadkeep-launch.py),
and [In a session](https://alegauss.github.io/roadkeep/docs/session/) explains the wiring.

### From a checkout beside it

A project adopting an unreleased version runs a sibling checkout, and `install` writes the
hook, the MCP server and the skill into that project itself:

```sh
python ../roadkeep/plugin/scripts/roadkeep.py -C . install
python ../roadkeep/plugin/scripts/roadkeep.py -C . install --check   # in CI: still in step?
```

## Why it exists

It started as three readings from a real production repository, where all three files
declared a format and none enforced it:

| Artefact | Declared rule | Actual reading |
|---|---|---|
| `docs/ROADMAP.md` | one sentence per task | 92 lines, **142 words** average, worst **1406 characters** |
| `agents.md` | index only, loaded every turn | grew to **186 KB (~46k tokens)** |
| `docs/IMPROVEMENTS.md` | rationale for *unshipped* work | a sibling project's reached **539 KB** |

Six of the eight worst lines were written in the session that then diagnosed the problem. An
author, human or model, who has the whole design in mind writes it where the reader is, and an
instruction to be terse does not survive that. A linter reports after the prose exists, when
the author is asked to delete work just done. A field with `maxLength: 200` refuses before the
sentence is composed.

Six laws bind the design, and a change that breaks one is wrong even if requested
([§0.3](https://github.com/alegauss/roadkeep/blob/main/docs/IMPROVEMENTS.md)):

| # | Law |
|---|---|
| L1 | The format is a schema, **enforced where the text is created**; `lint` is the backstop. |
| L2 | **The store is the repository**: Markdown, greppable, diffable. No database, no service. |
| L3 | **Round-trip or don't write**: parse → render → byte-identical. |
| L4 | **The tool never writes prose**: it validates and renders. |
| L5 | **Query instead of read**: every question is a command. |
| L6 | **Configuration, not convention**: prefix, paths, markers and limits are per project. |

The non-goals: no web UI and no server, no issue-tracker sync, no model and no prompts inside
the tool, and no dates, quarters or estimates.

## Status

The table below is **not written by hand**: `roadkeep export --readme` derives it from
`docs/`, so it cannot restate a backlog it no longer matches.

<!-- roadkeep:begin -->
<!-- generated by `roadkeep export --readme`; edit the governed files instead -->

| Block | Open | Shipped | Retired |
| --- | --- | --- | --- |
| A — The model (a task is data before it is a line) | 1 | 43 | 2 |
| B — Authoring (insert, never hand-edit) | 1 | 237 | 2 |
| C — Query (consult without reading the file) | 0 | 204 | 7 |
| D — The gate | 0 | 319 | 7 |
| E — Adoption | 0 | 123 | 1 |
| F — The Claude Code plugin (the guardrail at the agent boundary) | 0 | 167 | 4 |
| G — The editor surface (the backlog where the file is open) | 0 | 15 | 0 |
| H — The tool's own shape (what one verb costs to change) | 0 | 45 | 1 |
| I — The documentation area (what an adopter reads before there is a session to ask) | 1 | 20 | 0 |
| J — Validation (whether a person ever tried it) | 0 | 5 | 0 |
| K — The desktop app (one installer for the reader and the plugin) | 0 | 9 | 0 |
| L — Product sites on the package | 1 | 0 | 0 |
| **Total** | 4 | 1187 | 24 |

**Next ready:**

- 📋 **RK1715** (deps: —) **block add opens a label the ledger already declares under another title** — It writes the new heading where the label is missing and exits 0, so one label carries two titles across the governed files. → §RK1715
<!-- roadkeep:end -->

Open work is in
[docs/ROADMAP.md](https://github.com/alegauss/roadkeep/blob/main/docs/ROADMAP.md). Four
projects are governed by it today: this one, Shio, Turing and Dumont. This repository is its
own conformance fixture: `roadkeep lint` must pass on `docs/` here, and the suite asserts it.

## More tools by alegauss

For Claude Code:

- **[Claude Code Tray](https://alegauss.github.io/claude-tray/)**: your rate-limit usage as a Windows tray icon that turns red before you run out.
- **[commitclerk](https://alegauss.github.io/commitclerk/)**: Conventional Commits messages from your staged diff, in a single-file Python CLI.
- **[polyweave](https://alegauss.github.io/polyweave/)**: a Claude Code plugin that makes a game's 3D assets, sounds and names by declaring what each has to satisfy.

For Windows developers:

- **[winwright](https://alegauss.github.io/winwright/)**: drives a Windows desktop app from a test and reports what was actually observed.
- **[FreeWilly](https://alegauss.github.io/freewilly/)**: Docker on Windows without Docker Desktop, with no admin prompt and no telemetry.
- **[Quickshell](https://alegauss.github.io/quickshell/)**: an SSH client for Windows with sessions, keys, SFTP and tunnels, and without the rest of the suite.

All of them: [alegauss.github.io](https://alegauss.github.io/)
