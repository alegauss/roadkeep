import { spawn, type ChildProcess } from 'node:child_process'
import { createRequire } from 'node:module'
import path from 'node:path'

/** The directory Electron treats as the app: it holds the package.json naming `main`. */
export const shellRoot = path.resolve(import.meta.dirname, '..')

/**
 * The debugging port `npm run dev:inspect` opens, which `.mcp.json` points Playwright MCP at
 * (RG212).
 *
 * Fixed, because the MCP server is configured before the window exists and cannot ask it for
 * a port. Not Chrome's customary 9222, which a browser somebody left open would already hold.
 */
export const INSPECT_PORT = 9333

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
/** The Electron binary, which the screenshot run hands to Playwright as well (RG209). */
export const electronPath = required

/**
 * The environment a launch runs in: this process's, plus what the run adds, minus
 * `ELECTRON_RUN_AS_NODE` — see `spawnElectron` for why that one never survives.
 */
export function launchEnv(extraEnv: Record<string, string> = {}): Record<string, string> {
  const env: Record<string, string> = {}
  for (const [name, value] of Object.entries({ ...process.env, ...extraEnv })) {
    if (value !== undefined && name !== 'ELECTRON_RUN_AS_NODE') env[name] = value
  }
  return env
}

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
  // The switches come first: Chromium reads its own before the positional path, and one
  // after it is an argument to the app rather than to the browser.
  return spawn(electronPath, [...extraArgs, shellRoot], { stdio, env: launchEnv(extraEnv) })
}
