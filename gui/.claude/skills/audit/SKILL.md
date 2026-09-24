---
name: audit
description: Full audit of roadkeep-gui — runs the gates, scans eight partitions in parallel with the scanner agent, deduplicates, verifies with the verifier agent, then reconciles the roadkeep backlog against the code and the confirmed findings. Use when asked to audit, review the whole repository, hunt debt, look for defects outside a specific change, or check whether the roadmap still matches the code.
---

An audit of this repository, from the gates to the backlog. `/code-review` reads a diff;
this reads the project at rest. It fixes no code: the product is a reconciled backlog, not
a patch.

## 1. The gates first — the baseline

Note `git status --short` and `git rev-parse --short HEAD`: another session may share this
checkout, and its files are not the audit's. Then run, in this order, keeping every output:

```
node -v              # must be >= 26; below it the ui projects fail for a reason no output names
npm run typecheck
npm run lint
npm test
npm run build
npm run test:live    # needs the build above and python with roadkeep
roadkeep lint
```

What already fails is **baseline**, not a finding. Hand it to every agent below so nobody
re-reports it. Below Node 26, say once that every `ui` and `ui-live` result is inconclusive.

## 2. One `scanner` per partition, in parallel

Check coverage first: `Glob` `packages/*/src/**/*.{ts,tsx,css}` and make sure every file
lands in exactly one row. A file no row names goes to the row of its package whose subject
it shares; a shell `*-live.test.ts` with no unit beside it goes to row 8.

Then eight `scanner` calls in **one message**. Each prompt carries its partition's name, its
file list and the baseline — nothing about the other partitions.

| #   | Partition            | Scope — each name includes its tests                                                                                                                                                                                                                                                                                                                                                                                 |
| --- | -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | core/seam            | `packages/core/src/`: transport verbs writes payloads reading rows answers bridge client refusals gate boundaries                                                                                                                                                                                                                                                                                                    |
| 2   | core/rules           | acts backlog budgeting candidates correcting design detail families filters graph limiting limits markers marking policy repairing search sections                                                                                                                                                                                                                                                                   |
| 3   | core/session         | agent binding build cache capabilities cold-start engines engine-resolution handover memory pauses pool reloading session tools transcript updates watching                                                                                                                                                                                                                                                          |
| 4   | core/view            | catalogue contrast ground index landing leaving locales opening packages portfolio pt-br roots scanning settings wording writing                                                                                                                                                                                                                                                                                     |
| 5   | ui                   | all of `packages/ui/src/` (`.ts`, `.tsx`, `index.css`), plus `packages/ui/vite.config.ts`, `vitest.live.config.ts`, `components.json`                                                                                                                                                                                                                                                                                |
| 6   | shell/window+release | `packages/shell/src/`: main window preload posture menu menu-template navigation guard content-policy open-here machine locale launch dev start built built-setup updates advisories settings-file stamp stamp-build compiler audit icon publisher release suites; `packages/shell/vite.*.config.ts`, `electron-builder.yml`, `build/`, `.github/workflows/`, root `package.json`, `tsconfig.json`, `.oxlintrc.json` |
| 7   | shell/engines        | process-transport mcp-transport mcp http-transport bridge engine-handler engine-candidates engine-reading roadkeep-engine agent-candidates agent session-process session seam scan-fs root-paths source-watch governed-watch governed-stamp freshness git-worktree scratch probing catalogue bounded ceiling                                                                                                         |
| 8   | shell/live           | the harness — live live-setup fixture fixture-cache fake-claude running-app — and every other `packages/shell/src/*-live.test.ts` (the verb suites, `contract-live` among them); root `vitest.config.ts`, `packages/shell/vitest.config.ts`, `vitest.live.config.ts`                                                                                                                                                 |

Each row is 2.4k to 5.5k lines. Row 6 is the thinnest on purpose: it holds the window
posture, the preload and the content policy, which deserve the slowest read.

## 3. Deduplicate

The same defect in the same file from two scanners → one entry, both reproductions kept.
The same defect in several files → one entry listing every site: that is one backlog line,
not seven. Most severe first.

## 4. One `verifier` in FINDINGS mode

One call, its prompt starting `MODE: FINDINGS`, with the whole deduplicated list and the
baseline. It needs the full list to close findings in batches by command; eight verifiers
would run `npm test` eight times.

## 5. One `verifier` in ROADMAP mode

Read the open backlog through roadkeep, never by opening `docs/ROADMAP.md`:

```
roadkeep list        # every open line, verbatim
roadkeep unclosed    # open lines whose work the history already names
```

One call, its prompt starting `MODE: ROADMAP`, with both outputs and the CONFIRMED
findings, so it can spot overlaps. It returns one line per task —
`task-id | status | evidence | text` — and a `COVERED` line for each finding an open task
already holds.

## 6. Reconcile, through roadkeep only

The five governed files are written by the tool, and a hook refuses a hand-edit. The
`mcp__roadkeep__*` tool of the same name is the first choice; the CLI below is the same
engine, and `python .claude/hooks/roadkeep-launch.py` is the fallback. Run
`roadkeep show <id>` before touching a line.

| Verifier said   | Command                                                                                                                                                                                 |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ALREADY DONE    | `roadkeep ship <id> --why "<outcome>"`. If a paragraph of its design is a rule that must outlive it, carry it with `--decides` — the `roadkeep-gui-roadmap-docs` table says which flag. |
| OUTDATED        | `roadkeep retire <id> --reason "<reason>"`, adding `--superseded-by <id>` or `--folds-into <id>` when another line takes the work.                                                      |
| NEEDS REWORDING | `roadkeep restate <id> --symptom "…"` for the claim, `roadkeep amend <id> --why "…"` for the why. A line too broad is restated narrower and the rest filed as a new line.               |
| STILL VALID     | Nothing.                                                                                                                                                                                |

Then file each CONFIRMED finding no `COVERED` line claims — one line per finding, or per
pattern:

1. `roadkeep delivered <block> --near "<symptom>" --open` — the duplicate check, before an
   id is spent. An open line that says the same thing takes the finding into its design
   (`roadkeep section amend`), not a new line; a shipped one means a regression — file it
   and name the shipped id in the why.
2. Pick the block by subject from `roadkeep block list`. Today: A payloads and transport,
   B discovery, C the portfolio, D one backlog read, E the write path, F the agent, G the
   shell and its tests, H the look (paused).
3. Write the design to a scratchpad file, then:
   `roadkeep add --block <X> --symptom "<what does not work>" --why "<one sentence.>" --status 📋 --section "<title>" --section-body-file <path>`.
   The symptom says what does not work, never the fix. 📋 when the section names the
   mechanism; 💭 only when a question no code can answer blocks the start — 💭 is
   `undesigned` here and hides the line from `pick --designed`.

Close with `roadkeep lint`; each finding it reports names its own door, and
`roadkeep repair` applies the one-command ones. Then
`Select-String docs\*.md -Pattern '</section_body>|</invoke>'` must count 0: an inline MCP
body once leaked its closing markup, and lint stays green over it.

FALSE POSITIVE and UNVERIFIABLE findings are not filed. If roadkeep is unreachable — no MCP,
no CLI, no launcher — stop here and write the same reconciliation to `docs/AUDIT.md` as a
dated section instead.

Do not commit. An audit is not a task: the reconciliation stays in the tree for the user to
read in `git diff docs/`, and another session's files may share the tree. Offer a commit
of `docs/` alone: `git add -- docs/`, then `git commit -F <message file>` titled
`docs: reconcile the backlog with the <date> audit`, with no Claude attribution and no push.

## 7. Report counts only

```
findings: raw N · after dedupe N · CONFIRMED N · FALSE POSITIVE N · UNVERIFIABLE N
tasks: kept N · closed N · removed N · rewritten N · added N
baseline: <gates already red, or "clean"> · uncommitted: git diff docs/
```

Do not repeat the findings; they are in the backlog now. If a CONFIRMED finding is small and
obvious, offer to fix it as the next task. Do not fix it inside the audit.
