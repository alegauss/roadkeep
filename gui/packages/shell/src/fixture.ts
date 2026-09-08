import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import type { Transport } from '@rk/core'

/**
 * A governed project, built by the real engine, for the contract test to read.
 *
 * It is scaffolded by `init` and populated by the write verbs rather than by writing
 * Markdown here. That is the whole point: a fixture assembled by hand would be this app's
 * idea of what a governed file looks like, and the contract would then be checked against
 * that idea instead of against what roadkeep produces.
 *
 * Nothing in this file reads a payload. It only makes the project the reads run against.
 */

export interface Fixture {
  readonly root: string
  /** Remove it. Safe to call twice. */
  dispose(): void
}

export interface FixtureShape {
  /** How many open lines to add. */
  readonly open: number
  /** How many of those to ship, so the ledger is not empty. */
  readonly shipped: number
  /**
   * How many to set aside. `init` scaffolds the store either way, so 0 is the useful
   * shape for asserting that a project pausing nothing reads as empty and not as missing.
   */
  readonly deferred: number
}

const DEFAULT_SHAPE: FixtureShape = { open: 3, shipped: 1, deferred: 1 }

/** Run one engine command and refuse to continue quietly if it did not work. */
async function must(
  transport: Transport,
  root: string,
  argv: readonly string[],
  timeoutMs: number,
): Promise<string> {
  const result = await transport.run({ root, argv: ['-C', root, ...argv], timeoutMs })
  if (result.code !== 0) {
    throw new Error(
      `building the fixture failed at \`${argv.join(' ')}\` (exit ${String(result.code)})\n` +
        `${result.stdout}\n${result.stderr}`,
    )
  }
  return result.stdout
}

/**
 * Scaffold and populate a fixture project.
 *
 * @param transport the engine to build it with — the same one the reads will use, so a
 *   contract proven here is a contract about that build and no other.
 */
export async function buildFixture(
  transport: Transport,
  shape: FixtureShape = DEFAULT_SHAPE,
  timeoutMs = 30000,
): Promise<Fixture> {
  const root = mkdtempSync(path.join(tmpdir(), 'rk-fixture-'))
  const dispose = () => {
    rmSync(root, { recursive: true, force: true })
  }

  try {
    await must(
      transport,
      root,
      [
        'init',
        '--prefix',
        'FX',
        '--block',
        'A — The model',
        '--block',
        'B — The surface',
        '--deferred',
      ],
      timeoutMs,
    )

    await must(
      transport,
      root,
      [
        'non-goal',
        'add',
        '--lead',
        'No second store',
        '--why',
        'The files are the store, and a cache beside them is a second answer.',
      ],
      timeoutMs,
    )
    await must(
      transport,
      root,
      [
        'criterion',
        'add',
        '--block',
        'A',
        '--lead',
        'Every read is answered by the engine',
        '--why',
        'Nothing here restates a rule the tool already holds.',
      ],
      timeoutMs,
    )

    const total = shape.open + shape.shipped + shape.deferred
    const ids: string[] = []
    for (let index = 0; index < total; index += 1) {
      const stdout = await must(
        transport,
        root,
        [
          'add',
          '--block',
          index % 2 === 0 ? 'A' : 'B',
          '--symptom',
          `nothing answers question ${String(index)} yet`,
          '--why',
          `The ${String(index)}th read has no call path, so the screen has nothing to draw.`,
          '--section',
          `Why question ${String(index)} needs answering`,
          '--section-body',
          'A rationale long enough to be prose and short enough to stay inside the budget the project declares for a section.',
          '--json',
        ],
        timeoutMs,
      )
      ids.push((JSON.parse(stdout) as { id: string }).id)
    }

    for (const id of ids.slice(0, shape.shipped)) {
      await must(
        transport,
        root,
        ['ship', id, '--why', 'The read now answers, and a test holds it.'],
        timeoutMs,
      )
    }
    for (const id of ids.slice(shape.shipped, shape.shipped + shape.deferred)) {
      await must(
        transport,
        root,
        ['defer', id, '--reason', 'Waiting on a decision that is not this project.'],
        timeoutMs,
      )
    }

    return { root, dispose }
  } catch (cause) {
    dispose()
    throw cause
  }
}
