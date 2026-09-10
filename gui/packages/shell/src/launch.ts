import { spawn, type ChildProcess } from 'node:child_process'
import { createRequire } from 'node:module'
import path from 'node:path'

/** The directory Electron treats as the app: it holds the package.json naming `main`. */
export const shellRoot = path.resolve(import.meta.dirname, '..')

// The `electron` module means two different things depending on who loads it. Inside
// the app it is the Electron API, which is what its type declarations describe; loaded
// from Node it is a one-line module exporting the path of the binary, which is what a
// launcher needs and what no declaration covers. `createRequire` asks for the second one.
//
// Checked rather than asserted (RG121). The declarations describe the other module, so
// there is nothing here to trust: if this ever stops being a path, every launch fails on
// a spawn with an object for a command, and the sentence below is the one worth reading
// instead.
const required: unknown = createRequire(import.meta.url)('electron')
if (typeof required !== 'string') {
  throw new TypeError(
    `the electron module resolved to ${typeof required} and not the path of the binary`,
  )
}
const electronPath = required

/**
 * Spawn the app and hand back the child.
 *
 * `ELECTRON_RUN_AS_NODE=1` tells the Electron binary to behave as a plain Node runtime:
 * no builtin `electron` module, so `app` is undefined and the main process dies on its
 * first line. Editors export it — VS Code sets it for its extension host, and every
 * terminal and agent that inherits from one carries it — so a developer who runs the app
 * from inside their editor hits a crash that says nothing about the cause. Inheriting it
 * is never what a launch wants, so it is dropped here rather than diagnosed again.
 *
 * @param extraEnv variables this run adds, such as the dev server's URL.
 * @param extraArgs switches for the binary itself, before the app path — a debugging port
 *   and a throwaway profile, which is how a test gets to ask the running window anything.
 * @param stdio how the child's streams are wired. Inherited by default, because a person
 *   running the app wants its output; a test that reads the renderer's console pipes them.
 */
export function spawnElectron(
  extraEnv: Record<string, string> = {},
  extraArgs: readonly string[] = [],
  stdio: 'inherit' | 'pipe' = 'inherit',
): ChildProcess {
  const env = { ...process.env, ...extraEnv }
  delete env['ELECTRON_RUN_AS_NODE']

  // The switches come first: Chromium reads its own before the positional path, and one
  // after it is an argument to the app rather than to the browser.
  return spawn(electronPath, [...extraArgs, shellRoot], { stdio, env })
}
