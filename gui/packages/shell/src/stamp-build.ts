import path from 'node:path'

import { posturesLost, RENDERER_POSTURE } from './posture'
import { writeStamp } from './stamp'

/**
 * The build step: stamp what this build is, and refuse to package one that lost its
 * posture.
 *
 * **Packaging is where the posture stops being configuration.** The renderer's
 * `webPreferences` are one exported constant, so this asserts the value the window is
 * actually constructed with rather than a second copy of it. What that catches is a power
 * gained during development: the package fails here rather than shipping.
 *
 * Asking the *running* page whether isolation holds is RG60's, and it stays separate: this
 * runs anywhere, and that one needs a window and a debugging port.
 */

const root = path.resolve(import.meta.dirname, '..', '..', '..')

const lost = posturesLost({ ...RENDERER_POSTURE })
if (lost.length > 0) {
  process.stderr.write(
    `roadkeep-gui: this build lost the posture it claims, so it is not packaged:\n  ${lost.join(
      '\n  ',
    )}\n`,
  )
  process.exit(1)
}

const stamp = writeStamp(root)
process.stdout.write(
  `roadkeep-gui ${stamp.version || 'unstamped'} (${stamp.commit || 'unstamped'}, ${stamp.signed})\n`,
)
