import { createRequire } from 'node:module'
import path from 'node:path'

/**
 * Where TypeScript keeps its launcher, which is a path into somebody else's package.
 *
 * The dev loop has to run `tsc -b`, and it runs it with this process's own Node rather than
 * through `npx`: PATH is not something a rebuild should depend on, and a shell in the middle
 * is a quoting question nobody needs to have. That means naming the file.
 *
 * **The file is not nameable through the package.** TypeScript 7's `exports` publishes
 * `./package.json`, `.` as a version module and the unstable API, and nothing else — asking
 * for `typescript/bin/tsc` throws `ERR_PACKAGE_PATH_NOT_EXPORTED` at load, which is how this
 * was found: the dev run died before opening a window. So the path is assembled from the
 * directory `typescript/package.json` resolves in, plus where that version happens to keep
 * the launcher.
 *
 * **Its own module because it is unowned** (RG93). Assembled inline in the dev loop it was
 * a reach into a layout nobody publishes, held by somebody happening to run `npm run dev`
 * after an upgrade. Here it is a function two callers can name, and the second caller is a
 * test: `compiler-live.test.ts` resolves this same path and starts it, so a TypeScript
 * release that moves the file fails a suite rather than a morning.
 */

/** Under the package directory, where the launcher lives. */
const LAUNCHER = ['lib', 'tsc.js'] as const

/**
 * The launcher's absolute path.
 *
 * @param from the module resolving it, so a caller in another package finds the same
 *   TypeScript this one would. Defaults to this file, which is what the dev loop wants.
 */
export function compilerLauncher(from: string = import.meta.url): string {
  const manifest = createRequire(from).resolve('typescript/package.json')
  return path.join(path.dirname(manifest), ...LAUNCHER)
}
