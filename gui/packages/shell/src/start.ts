// Run the app the way a packaged build runs it: no dev server, the renderer loaded off
// disk out of `packages/ui/dist`. `npm start` builds first, so what opens is what the
// last build produced.
import { spawnElectron } from './launch'

const child = spawnElectron()
child.on('close', (code) => {
  process.exit(code ?? 0)
})
