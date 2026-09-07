import { spawn, type ChildProcess } from 'node:child_process'
import { createRequire } from 'node:module'
import path from 'node:path'

/** The directory Electron treats as the app: it holds the package.json naming `main`. */
export const shellRoot = path.resolve(import.meta.dirname, '..')

// The `electron` module means two different things depending on who loads it. Inside
// the app it is the Electron API, which is what its type declarations describe; loaded
// from Node it is a one-line module exporting the path of the binary, which is what a
// launcher needs and what no declaration covers. `createRequire` asks for the second
// one, and the cast is the price of a module that lies about itself in this direction.
const electronPath = createRequire(import.meta.url)('electron') as unknown as string

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
 */
export function spawnElectron(extraEnv: Record<string, string> = {}): ChildProcess {
  const env = { ...process.env, ...extraEnv }
  delete env['ELECTRON_RUN_AS_NODE']

  return spawn(electronPath, [shellRoot], { stdio: 'inherit', env })
}
