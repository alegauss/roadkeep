import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

/**
 * RG138: the icon the packaged app wears, and the two things it needs to reach the .exe.
 *
 * Until then the taskbar, the title bar and the installer all showed Electron's atom:
 * `electron-builder.yml` named no icon, the repository held no raster of any size, and
 * `signAndEditExecutable` was off — which, it turns out, is also what writes an icon into
 * the executable at all. Measured after the change: the unpacked `roadkeep.exe` carries the
 * mark at 32px, `ProductName` is `roadkeep`, and `Get-AuthenticodeSignature` still reads
 * `NotSigned` on both it and the installer.
 *
 * Held here without packaging anything, because each half fails silently: a missing or
 * small PNG falls back to Electron's icon with a log line nobody reads, and the edit
 * switched off again takes the icon with it and says nothing.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const ICON = path.join(REPO, 'build', 'icon.png')

/** Width, height and colour type out of a PNG's header, which is all this needs of it. */
function pngHeader(file: string): { width: number; height: number; colourType: number } {
  const bytes = readFileSync(file)
  expect(bytes.subarray(0, 8).toString('hex'), `${file} is not a PNG`).toBe('89504e470d0a1a0a')
  return {
    width: bytes.readUInt32BE(16),
    height: bytes.readUInt32BE(20),
    colourType: bytes.readUInt8(25),
  }
}

describe('RG138: the icon electron-builder makes every other icon from', () => {
  it('is a 1024 PNG with an alpha channel, beside the SVG it is rendered from', () => {
    // 1024 because the .icns wants 512 at 2x and the .ico is cut down from it; RGBA because
    // the tile's corners are rounded, and a PNG without alpha fills them.
    expect(pngHeader(ICON)).toEqual({ width: 1024, height: 1024, colourType: 6 })
    expect(existsSync(path.join(REPO, 'build', 'icon.svg'))).toBe(true)
  })

  it('is found where electron-builder looks, and written into the executable', () => {
    const config = readFileSync(path.join(REPO, 'electron-builder.yml'), 'utf8')

    // `buildResources` is how `icon.png` is found without a line naming it, and the edit is
    // how it reaches the .exe. Either one lost puts Electron's atom back in the taskbar.
    expect(config).toMatch(/^\s+buildResources: build\s*$/m)
    expect(config).toMatch(/^\s+signAndEditExecutable: true\s*$/m)
  })
})
