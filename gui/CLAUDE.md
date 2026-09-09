# roadkeep-gui

A desktop app that reads roadkeep-governed backlogs across many local repositories. Electron
main process, React renderer, and a pure core between them.

This file is loaded on every turn, so it is an index. The long form lives in the
[`roadkeep-gui-roadmap-docs`](.claude/skills/roadkeep-gui-roadmap-docs/SKILL.md) skill,
which triggers on the tasks that need it.

## Which package may know what

The split is the design, not a folder convention — `core` is the half a web service would
keep, `ui` the half it would serve to a browser, `shell` the half it would throw away. Each
is its own `tsc` project with its own types in scope, so putting code in the wrong one is a
compile error rather than a debate.

| Package     | Knows                                                                              | Never                                              |
| ----------- | ---------------------------------------------------------------------------------- | -------------------------------------------------- |
| `@rk/core`  | The transport interface, the verb table, the payload readers, and every pure rule. | Node. The DOM. Any timer, path or process type.    |
| `@rk/ui`    | React, the design system, the DOM.                                                 | Node. A path, a process, or how a call is carried. |
| `@rk/shell` | Electron main, spawning, the filesystem, settings.                                 | The DOM.                                           |

Cross-package imports go through the workspace name — `@rk/core`, never a relative path out
of a package.

## Five files belong to roadkeep

`docs/ROADMAP.md`, `CHANGELOG.md`, `IMPROVEMENTS.md`, `DECISIONS.md`, `DEFERRED.md` are
written by the tool and **never by hand** — a hook denies the edit. Start a task with
`brief`, not by reading them. Reach for the `mcp__roadkeep__*` tools first; the shell
fallback is `python .claude/hooks/roadkeep-launch.py`.

## One task, one commit

`run-commit.cmd -m "<conventional-commits title, ASCII>"` from the repo root — never
`git commit` by hand, and never two tasks in one commit. The doc sync rides in the same
commit as the code.

## The gates, before that commit

| Command             | When                                                               |
| ------------------- | ------------------------------------------------------------------ |
| `npm run typecheck` | Any `.ts` or `.tsx` change.                                        |
| `npm test`          | Any change to behaviour something asserts. Fast: starts nothing.   |
| `npm run test:live` | Anything that spawns or reads the build. Needs python and a build. |
| `roadkeep lint`     | Every task, without exception.                                     |
| `npm run lint`      | Any file this repo owns. `npm run format` is the writer.           |
| `npm run build`     | Anything the packaged app loads: a Vite config, an asset path.     |

`npm run dev` opens the window with hot reload; `npm start` runs it against the bundle on
disk. Neither is a gate.

**Node 26 or newer**, declared in `package.json` and `.nvmrc` (RG97). On Node 20 none of
the above reports a version problem: every jsdom file dies with a `TypeError` out of the
undici jsdom bundles, and the window test with `WebSocket is not defined`. Two symptoms
that look unrelated and neither names the cause.

## Two habits that are not obvious

**Check what is already there before building a mechanism.** The design system ships a
`ThemeProvider` and i18next; a second one is two systems writing the same state, not a
duplicate. Read `node_modules/@viglet/viglet-design-system/dist/components/` first.

**A 💭 line's design is still to write, and a 📋 line's is not.** Read the design before
building against it — it may already have decided the thing you are about to choose.
