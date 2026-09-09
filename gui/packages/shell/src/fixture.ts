import { appendFileSync, cpSync, existsSync, mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import type { Transport } from '@rk/core'

import { cacheDirectory } from './fixture-cache'

import { removeTree } from './scratch'

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
  /**
   * `[reads] list`, in characters, for a project that declares one.
   *
   * The one shape this app could not read off a real payload until something declared it
   * (RG67): a listing past this bound comes back as blocks and counts with the lines
   * withdrawn, and no repository here sets one. Written into `roadkeep.toml` after `init`
   * rather than passed to it, because `init` takes no flag for it — and a small number is
   * the point, since the bound has to be one four short lines exceed.
   */
  readonly listRead?: number
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
 * **Built once per shape per run, and copied after that** (RG68). Twenty-six of these are
 * asked for across the live suite and twelve distinct shapes answer all of them, so the
 * first ask pays the ten interpreter starts and the rest pay a directory copy. Each caller
 * still gets a project of its own — several of these files ship, defer and amend what they
 * were handed, and a shared one would make a test depend on which file ran first.
 *
 * The copy is a copy of the *built* project and never of a template kept between runs:
 * `fixture-cache.ts` says why that line is where it is.
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
    removeTree(root)
  }

  const held = builtEarlier(shape)
  if (held !== '') {
    cpSync(held, root, { recursive: true })
    return { root, dispose }
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

    // Last, so every write above runs against a project with no ceiling on a read. The
    // table is appended rather than templated: what the file already holds is `init`'s,
    // and this adds the one line that makes the listing bounded.
    if (shape.listRead !== undefined) {
      appendFileSync(
        path.join(root, 'roadkeep.toml'),
        `\n[reads]\nlist = ${String(shape.listRead)}\n`,
        'utf8',
      )
    }

    keepForLater(shape, root)
    return { root, dispose }
  } catch (cause) {
    dispose()
    throw cause
  }
}

/**
 * The name this shape's built project is kept under.
 *
 * Every field, so a shape that differs in one number is a different project — which it is:
 * the ids run to a different count and half these tests name one.
 */
function nameOf(shape: FixtureShape): string {
  return [
    `open-${String(shape.open)}`,
    `shipped-${String(shape.shipped)}`,
    `deferred-${String(shape.deferred)}`,
    `read-${String(shape.listRead ?? 0)}`,
  ].join('-')
}

/** A project of this shape already built this run, or the empty string. */
function builtEarlier(shape: FixtureShape): string {
  const cache = cacheDirectory()
  if (cache === '') return ''
  const held = path.join(cache, nameOf(shape))
  return existsSync(held) ? held : ''
}

/**
 * Keep this project so the next ask for the same shape copies it.
 *
 * A failure to keep it is not a failure to build it: the caller has a working fixture in
 * hand, and the only thing lost is the saving on whoever asks next.
 */
function keepForLater(shape: FixtureShape, root: string): void {
  const cache = cacheDirectory()
  if (cache === '') return
  try {
    cpSync(root, path.join(cache, nameOf(shape)), { recursive: true, force: false })
  } catch {
    // Two workers reaching here at once, or a disk that said no. Either way the suite has
    // what it asked for and the next build is simply not free.
  }
}
