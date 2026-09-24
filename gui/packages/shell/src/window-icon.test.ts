import { readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { windowIcon } from './window-icon'

/**
 * RG236: the icon an unpackaged window names, and the packaged one does not.
 *
 * Held without starting Electron, since both halves fail silently: a path that names nothing
 * falls back to the atom with no error, and a packaged window naming a file `buildResources`
 * never copied would do the same.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')

describe('RG236: the window names roadkeep`s mark when it is not packaged', () => {
  it('names the PNG RG138 renders from the SVG, three steps above the main process', () => {
    // From this directory, which is `shell/src`: the compiled main process runs from `shell/dist`,
    // at the same depth, so the answer from either is the same file.
    const icon = windowIcon(import.meta.dirname, false)

    expect(icon).toBe(path.join(REPO, 'build', 'icon.png'))
    // The bytes and not only the name: a PNG header is what Electron's native image reads, and
    // an SVG renamed would be a path that exists and an icon that is not drawn.
    const bytes = readFileSync(icon ?? '')
    expect(bytes.subarray(0, 8).toString('hex')).toBe('89504e470d0a1a0a')
  })

  it('names nothing packaged, where the executable already carries the icon', () => {
    expect(windowIcon(import.meta.dirname, true)).toBeUndefined()
  })
})
