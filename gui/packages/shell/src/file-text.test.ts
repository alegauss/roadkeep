import path from 'node:path'

import { FILE_TEXT_CEILING } from '@rk/core'
import { describe, expect, it } from 'vitest'

import { fileText, TEXT_PROBE, type Disk } from './file-text'

/**
 * RG245: one edited file read for the viewer, with the disk faked.
 *
 * What is held is each refusal and what was asked of the disk on the way to it: a path outside
 * the root asks nothing, and a file past the ceiling is never read.
 */

const ROOT = path.resolve('/proj')

interface Planted {
  readonly bytes?: Uint8Array
  readonly size?: number
  readonly file?: boolean
  readonly unreadable?: boolean
}

function disk(files: Readonly<Record<string, Planted>>): Disk & { readonly asked: string[] } {
  const asked: string[] = []
  const at = (file: string): Planted | undefined =>
    files[path.relative(ROOT, file).replaceAll('\\', '/')]
  return {
    asked,
    stat: (file) => {
      asked.push(`stat ${file}`)
      const found = at(file)
      if (found === undefined) return Promise.resolve(null)
      return Promise.resolve({
        size: found.size ?? found.bytes?.length ?? 0,
        file: found.file ?? true,
      })
    },
    read: (file) => {
      asked.push(`read ${file}`)
      const found = at(file)
      if (found?.unreadable === true || found?.bytes === undefined) {
        return Promise.reject(new Error('EACCES'))
      }
      return Promise.resolve(found.bytes)
    },
  }
}

const text = (said: string): Uint8Array => new TextEncoder().encode(said)

describe('RG245: an edited file, read for the viewer', () => {
  it('reads a text file under the root as its characters, shortened for the screen', async () => {
    const source = 'const a = 1\nconst ç = 2\n'
    const fake = disk({ 'src/a.ts': { bytes: text(source) } })

    expect(await fileText(ROOT, path.join(ROOT, 'src', 'a.ts'), fake)).toEqual({
      kind: 'read',
      path: path.join(ROOT, 'src', 'a.ts'),
      shown: 'src/a.ts',
      text: source,
      // Bytes and not characters: the ç is two of them.
      bytes: source.length + 1,
    })
  })

  it('refuses a path outside the root and asks the disk nothing', async () => {
    const fake = disk({})

    const answer = await fileText(ROOT, '../sibling/a.ts', fake)

    expect(answer).toEqual({
      kind: 'refused',
      path: '../sibling/a.ts',
      code: 'outside',
      fields: {},
    })
    expect(fake.asked).toEqual([])
  })

  it('refuses what is not there, and what is there and is not a file', async () => {
    const fake = disk({ src: { file: false } })

    expect(await fileText(ROOT, 'src/gone.ts', fake)).toMatchObject({ code: 'missing' })
    expect(await fileText(ROOT, 'src', fake)).toMatchObject({ code: 'unreadable' })
  })

  it('refuses a file it may not read, rather than throwing', async () => {
    const fake = disk({ 'src/locked.ts': { size: 10, unreadable: true } })

    expect(await fileText(ROOT, 'src/locked.ts', fake)).toMatchObject({ code: 'unreadable' })
  })

  it('refuses a file past the ceiling with both numbers, and never reads it', async () => {
    const fake = disk({ 'big.log': { size: FILE_TEXT_CEILING + 1 } })

    const answer = await fileText(ROOT, 'big.log', fake)

    expect(answer).toEqual({
      kind: 'refused',
      path: 'big.log',
      code: 'too-large',
      fields: { bytes: String(FILE_TEXT_CEILING + 1), ceiling: String(FILE_TEXT_CEILING) },
    })
    expect(fake.asked.some((one) => one.startsWith('read'))).toBe(false)
  })

  it('refuses a file with a NUL in its first block as not text', async () => {
    const binary = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x00, 0x0a])
    const late = new Uint8Array(TEXT_PROBE + 10).fill(0x61)
    late[TEXT_PROBE + 5] = 0

    expect(await fileText(ROOT, 'logo.png', disk({ 'logo.png': { bytes: binary } }))).toMatchObject(
      { code: 'not-text' },
    )
    // Past the first block is not looked at, which is the bound on what judging text costs.
    expect(await fileText(ROOT, 'late.txt', disk({ 'late.txt': { bytes: late } }))).toMatchObject({
      kind: 'read',
    })
  })
})
