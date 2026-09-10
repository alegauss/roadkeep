import { applyWrite, composeWrite, readAddedPayload } from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { CEILING, liveEngine as transport, read } from './live'

/**
 * RG9: a person's words, in and back out unchanged.
 *
 * The line filed this worried that prose composed into argv reaches the engine as different
 * bytes, and planned to move each field onto stdin as the verbs grew a dash for it. Two things
 * were measured before building that. The engine takes one field per call from stdin — a
 * second dash is refused as a pipe clash — so an `add` with a symptom, a why and a body could
 * never have sent all three that way. And this app spawns with no shell: on Windows the
 * elements go to `CreateProcessW` as UTF-16 and the interpreter reads them back as such, so
 * there is no layer left to reinterpret a byte.
 *
 * So the claim is held here as a round trip rather than a routing rule: every character a
 * shell or a code page would touch goes in through each prose field, and `show` must hand the
 * same string back.
 */

/**
 * What a shell reads as syntax and a code page can re-encode, in the three prose fields of one
 * line. The engine's own rules still apply to each — a symptom is a phrase, a why is one
 * sentence with its stop — so the words are awkward in content and ordinary in form.
 */
const WORDS = {
  symptom: `ação — "aspas", it's \`crase\` & $(nada) | %PATH% ^caret \\barra ✓ 日本`,
  why: `Cada campo leva ç, ã, é, o travessão — e "aspas", o apóstrofo de it's e \`crase\` intactos.`,
  body:
    `Um parágrafo com acentos (ação, coração, pé), um travessão — e aspas "duplas" e 'simples'. ` +
    `Também \`crase\`, $(subshell), %VARIÁVEL%, ^circunflexo, & e | soltos, \\barra\\ e ✓ 日本語.`,
}

let fixture: Fixture
let id = ''

beforeAll(async () => {
  fixture = await buildFixture(transport, { open: 1, shipped: 0, deferred: 0 })
  const outcome = await applyWrite(
    transport,
    composeWrite(fixture.root, 'add', {
      block: 'A',
      symptom: WORDS.symptom,
      why: WORDS.why,
      section: 'Palavras que atravessam',
      sectionBody: WORDS.body,
    }),
    readAddedPayload,
    { timeoutMs: CEILING },
  )
  if (outcome.kind !== 'applied') {
    throw new Error(`the add did not apply: ${JSON.stringify(outcome)}`)
  }
  id = outcome.value.id
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG9: prose in through argv, back through show', () => {
  it('keeps the symptom byte for byte', async () => {
    const shown = await read(fixture.root, 'show', { id })

    expect(Buffer.from(shown.symptom, 'utf8')).toEqual(Buffer.from(WORDS.symptom, 'utf8'))
  })

  it('keeps the why byte for byte', async () => {
    const shown = await read(fixture.root, 'show', { id })

    expect(shown.why).toBe(WORDS.why)
  })

  it('keeps the section body word for word, wrapped the way the file wraps', async () => {
    // The engine writes a paragraph at the file's width, so a space may come back as a line
    // break — which is the file's wrapping and not the author's bytes. Every run of characters
    // between them has to be the one that went in.
    const shown = await read(fixture.root, 'show', { id })
    const body = shown.section?.body ?? ''

    expect(body).toContain('\n')
    expect(body.trim().split(/\s+/)).toEqual(WORDS.body.split(' '))
  })
})
