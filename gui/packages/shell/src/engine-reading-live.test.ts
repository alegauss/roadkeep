import { createClient, type Transport } from '@rk/core'
import { describe, expect, it } from 'vitest'

import { ENGINE_VAR, engineReading, read, REPO, type EngineReading } from './live'

/**
 * RG84: what the run does when the engine it reads answered nothing.
 *
 * The resolved half is asserted where it belongs — `contract-live.test.ts` names the build
 * its green run is a claim about. This file is the other half, and it is the one that used
 * to be untestable: an engine mid-rebuild made thirty-one files each report a renamed key,
 * and no case anywhere said what that should look like instead.
 *
 * The reading is replaced through the environment variable it travels in, before anything
 * here asks for it. That is not a back door — it is the same crossing a worker uses, and a
 * file gets its own module instance, so what is set here is set here and nowhere else.
 */

const BROKEN: EngineReading = {
  named: '',
  unresolved: 'it refused `engines`: this configuration is not one this build accepts',
}

/**
 * What the run published, read before the line below overwrites it.
 *
 * The order matters and is the reason this is not inside a case. Replacing the reading is
 * what makes every case here possible, and it would also erase the one thing none of them
 * can check afterwards: that a reading crossed the fork at all. A worker arriving with an
 * empty environment asks the engine for itself and passes everything below, which is the
 * per-file resolution this task removed, silently back.
 */
const PUBLISHED = process.env[ENGINE_VAR] ?? ''

process.env[ENGINE_VAR] = JSON.stringify(BROKEN)

/**
 * A transport with no process behind it, answering something no verb's shape fits.
 *
 * Deliberately not a payload: what this file needs from it is that the read *reached* the
 * transport, and an unreadable answer proves that without this file having to hold a copy
 * of any verb's shape — which is the one thing the contract test exists so nobody does.
 */
const canned: Transport = {
  run: () => Promise.resolve({ code: 0, stdout: '{}', stderr: '', durationMs: 0 }),
}

/** What the read threw, as a sentence. A read that returned is a failure of this file. */
async function refusalOf(call: Promise<unknown>): Promise<string> {
  try {
    await call
  } catch (thrown) {
    return thrown instanceof Error ? thrown.message : String(thrown)
  }
  throw new Error('the read answered, and every case here is about one that cannot')
}

describe('RG84: one engine for the length of a run', () => {
  it('settles the reading before any worker starts, and hands it to each one', () => {
    expect(
      PUBLISHED,
      `\`globalSetup\` publishes the run's one reading as ${ENGINE_VAR}, and a worker that` +
        ' arrives without it resolves an engine of its own — which is the disagreement' +
        ' between files this task exists to remove',
    ).not.toBe('')
    expect((JSON.parse(PUBLISHED) as EngineReading).unresolved).toBe('')
  })

  it('spends the reading the run published, rather than asking again', async () => {
    expect(await engineReading()).toEqual(BROKEN)
  })

  it('says the engine answered nothing, once, instead of a key that moved', async () => {
    // No spawn: the reading already knows how this ends, and saying so is worth more than
    // thirty-one reports of a field that is missing because the build fell back.
    const said = await refusalOf(read(REPO, 'list', {}))

    expect(said).toContain('did not answer `engines`')
    expect(said).toContain('not one this build accepts')
  })

  it('leaves a file that brought its own transport to its own failure', async () => {
    // The shared reading is about the shared engine. A file testing a transport of its own
    // has asked a different question, and answering it with this repository's launcher
    // would be this seam overruling the thing the file was written to check.
    const said = await refusalOf(read(REPO, 'list', {}, { client: createClient(canned) }))

    expect(said).toContain('could not read')
    expect(said).not.toContain('did not answer `engines`')
  })
})
