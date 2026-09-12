import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { afterEach, describe, expect, it } from 'vitest'

import { LOGO_CEILING, logoOf } from './project-logo'
import { removeTree } from './scratch'

/**
 * RG204: the mark a project declares, and what this refuses to read.
 *
 * The path is a repository's word, not this app's, so what is held here is the refusing:
 * a climb out of the project, an absolute path, a file that is not the image it claims to
 * be, and one too large for a thirty-two pixel row. Each answers empty, and the row falls
 * back to the emoji — a broken logo is cosmetic rather than an empty cell.
 *
 * Files are written here rather than kept as fixtures: what is under test is bytes on a
 * disk being resolved against a root, and a checked-in PNG would be a fixture this test
 * reads rather than a file a repository declared.
 */

const PNG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x01])

const made: string[] = []

function project(): string {
  const root = mkdtempSync(path.join(tmpdir(), 'rk-logo-'))
  made.push(root)
  return root
}

afterEach(() => {
  for (const one of made.splice(0)) removeTree(one)
})

describe('RG204: a picture from a repository this app does not own', () => {
  it('reads a declared file and answers it as a data URL', async () => {
    const root = project()
    mkdirSync(path.join(root, 'docs'))
    writeFileSync(path.join(root, 'docs', 'mark.png'), PNG)

    const said = await logoOf(root, 'docs/mark.png')

    // A data URL and never a path: the renderer receives a picture or it receives nothing.
    expect(said.startsWith('data:image/png;base64,')).toBe(true)
    expect(said).not.toContain(root)
  })

  it('recognises an SVG, which is text and carries no magic number', async () => {
    const root = project()
    writeFileSync(path.join(root, 'mark.svg'), '<svg xmlns="http://www.w3.org/2000/svg"/>')

    expect((await logoOf(root, 'mark.svg')).startsWith('data:image/svg+xml;base64,')).toBe(true)
  })

  it('refuses a path that climbs out, once the dot segments are resolved', async () => {
    // The one that a string test would pass: it starts with nothing suspicious and lands in
    // another repository. Block G's criterion — a location is parsed, never matched.
    const root = project()
    const outside = path.join(root, 'outside.png')
    writeFileSync(outside, PNG)
    const inner = path.join(root, 'inner')
    mkdirSync(inner)

    expect(await logoOf(inner, '../outside.png')).toBe('')
    expect(await logoOf(inner, 'docs/../../outside.png')).toBe('')
  })

  it('refuses an absolute path, which is not a path inside the project at all', async () => {
    const root = project()
    const mark = path.join(root, 'mark.png')
    writeFileSync(mark, PNG)

    expect(await logoOf(root, mark)).toBe('')
  })

  it('refuses a file that is not the image it claims to be', async () => {
    // Sniffed rather than trusted to the extension: a `.png` holding something else is a
    // file this app would otherwise hand a renderer as an image.
    const root = project()
    writeFileSync(path.join(root, 'mark.png'), 'not a picture at all')

    expect(await logoOf(root, 'mark.png')).toBe('')
  })

  it('refuses one too large for a row, on the bytes and not on a declaration', async () => {
    const root = project()
    writeFileSync(path.join(root, 'huge.png'), Buffer.concat([PNG, Buffer.alloc(LOGO_CEILING)]))

    expect(await logoOf(root, 'huge.png')).toBe('')
  })

  it('answers empty for a file that is not there, and for a declaration that is not one', async () => {
    const root = project()

    expect(await logoOf(root, 'docs/missing.png')).toBe('')
    expect(await logoOf(root, '')).toBe('')
    // A directory is not a file, and reading one would throw rather than answer.
    expect(await logoOf(root, '.')).toBe('')
  })
})
