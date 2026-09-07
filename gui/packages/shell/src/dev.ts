// The development run, in one process. It starts Vite over `packages/ui` through the
// Node API rather than a second terminal, waits for the URL it actually bound, and hands
// that URL to Electron in the environment. Two things follow from doing it this way: the
// port is never guessed, and closing the window shuts the dev server down instead of
// leaving one listening for the next run to collide with.
import path from 'node:path'

import { createServer } from 'vite'

import { shellRoot, spawnElectron } from './launch.js'

const uiRoot = path.resolve(shellRoot, '..', 'ui')

const server = await createServer({
  root: uiRoot,
  configFile: path.join(uiRoot, 'vite.config.ts'),
})
await server.listen()
server.printUrls()

const url = server.resolvedUrls?.local[0]
if (!url) {
  await server.close()
  throw new Error('Vite started but bound no local URL, so there is nothing to load')
}

const child = spawnElectron({ ROADKEEP_GUI_RENDERER_URL: url })

let closing = false
async function shutDown(code: number): Promise<never> {
  if (!closing) {
    closing = true
    await server.close()
  }
  process.exit(code)
}

child.on('close', (code) => {
  void shutDown(code ?? 0)
})

for (const signal of ['SIGINT', 'SIGTERM'] as const) {
  process.on(signal, () => {
    child.kill()
    void shutDown(0)
  })
}
