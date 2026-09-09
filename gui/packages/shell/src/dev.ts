// The development run, in one process. It starts Vite over `packages/ui` through the
// Node API rather than a second terminal, waits for the URL it actually bound, and hands
// that URL to Electron in the environment. Two things follow from doing it this way: the
// port is never guessed, and closing the window shuts the dev server down instead of
// leaving one listening for the next run to collide with.
//
// RG57: and it watches the half that does not hot-reload. `shell` and `core` are compiled
// and the Electron child is replaced; Vite is left alone, because restarting the server
// throws away the renderer state that made the change worth looking at. What decides when
// to build and when not to is `createReloading` in `core`, and the burst is held by the
// same `createWatching` the governed files use.
import { spawn, type ChildProcess } from 'node:child_process'
import path from 'node:path'

import { createReloading, createWatching } from '@rk/core'
import { createServer } from 'vite'

import { compilerLauncher } from './compiler'
import { REAL_CLOCK } from './governed-watch'
import { shellRoot, spawnElectron } from './launch'
import { createSourceWatcher, REBUILD_QUIET_MS } from './source-watch'

const uiRoot = path.resolve(shellRoot, '..', 'ui')
const repoRoot = path.resolve(shellRoot, '..', '..')

/** The trees `tsc -b` reads for the main process. `ui` is absent: Vite already has it. */
const WATCHED = ['packages/shell/src', 'packages/core/src']

const server = await createServer({
  root: uiRoot,
  configFile: path.join(uiRoot, 'vite.config.ts'),
})
await server.listen()
server.printUrls()

const bound = server.resolvedUrls?.local[0]
if (!bound) {
  await server.close()
  throw new Error('Vite started but bound no local URL, so there is nothing to load')
}
// Narrowed into a name of its own: `start` is a hoisted declaration, so it does not
// inherit the check above and would otherwise hand Electron a possibly-absent URL.
const url: string = bound

const watching = createWatching(createSourceWatcher(), REAL_CLOCK, REBUILD_QUIET_MS)
const watched = watching.hold(repoRoot, WATCHED)

let closing = false
let child: ChildProcess = start()

function start(): ChildProcess {
  const started = spawnElectron({ ROADKEEP_GUI_RENDERER_URL: url })
  started.on('close', (code) => {
    // A child replaced by a restart is not the run ending. Only the one that is current
    // when it closes takes the run with it, which is the window being closed by hand.
    if (started === child && !closing) void shutDown(code ?? 0)
  })
  return started
}

async function shutDown(code: number): Promise<never> {
  if (!closing) {
    closing = true
    watched.release()
    await server.close()
  }
  process.exit(code)
}

/**
 * `tsc -b` over the three packages, as `npm run typecheck` runs it.
 *
 * The compiler is resolved and run with this process's own Node rather than reached through
 * `npx` and a shell: PATH is not something a dev loop should depend on, and a shell in the
 * middle is a quoting question nobody needs to have.
 *
 * Why the path is assembled rather than imported is `compiler.ts`, which is also where a
 * test resolves the same one and starts it (RG93).
 */
const tsc = compilerLauncher()

function compile(): Promise<boolean> {
  return new Promise((resolve) => {
    const build = spawn(process.execPath, [tsc, '-b'], { cwd: repoRoot, stdio: 'inherit' })
    build.on('close', (code) => resolve(code === 0))
    // Unspawnable is a failed build, which is the answer that leaves the app running.
    build.on('error', () => resolve(false))
  })
}

const reloading = createReloading({
  build: compile,
  restart: () => {
    const previous = child
    child = start()
    previous.kill()
  },
  report: (said) => {
    // `console` rather than the Vite logger: this is the main process half, and mixing it
    // into the renderer's output is how somebody reads a rebuild as a hot update.
    console.log(`[dev] ${said}`)
  },
})

watching.onChanged(() => {
  reloading.changed()
})

for (const signal of ['SIGINT', 'SIGTERM'] as const) {
  process.on(signal, () => {
    child.kill()
    void shutDown(0)
  })
}
