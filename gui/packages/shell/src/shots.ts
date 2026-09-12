import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { DEFAULT_SETTINGS, listedTasks } from '@rk/core'

import { refuseIfStale } from './built'
import { buildFixture } from './fixture'
import { liveEngine, liveHeld, read, REPO } from './live'
import { removeTree } from './scratch'
import { saveSettings } from './settings-file'
import { buildOf, launchForShots, speakAndPaint, takeCapture } from './shots-app'
import { capturesFor, onlyFrom, SHOTS_DIRECTORY, type Capture } from './shots-plan'

/**
 * `npm run shots`: every surface the window serves, photographed (RG209).
 *
 * The tests render jsdom, which lays nothing out, so a chosen toggle at 1.35:1 against its
 * panel passed every one of them and was found by a screenshot somebody improvised. This is
 * that screenshot, made a command: a fixture project, a throwaway profile naming it, the built
 * app, and a PNG per surface, ground, language and width in `.shots/` — which an agent reads
 * the way a person looks.
 *
 * **Refuses a stale build**, as the live suite does: a picture of a bundle older than the tree
 * is a picture of code nobody is looking at. The fixture needs python and the wired launcher,
 * for the same reason the live suite does.
 *
 * `--only <surface>` narrows a run to what a change touched, and the index keeps the pictures
 * an earlier run took of the rest.
 */

interface Taken extends Capture {
  readonly settled: boolean
}

/** Whether an entry an earlier index held still reads as a capture: its file, at least. */
function isTaken(value: unknown): value is Taken {
  return (
    typeof value === 'object' &&
    value !== null &&
    'file' in value &&
    typeof value.file === 'string' &&
    'settled' in value &&
    typeof value.settled === 'boolean'
  )
}

/** The captures an earlier run indexed, or none where there is no index it can read. */
function earlierCaptures(file: string): Taken[] {
  try {
    const parsed: unknown = JSON.parse(readFileSync(file, 'utf8'))
    const captures =
      typeof parsed === 'object' && parsed !== null && 'captures' in parsed ? parsed.captures : []
    return Array.isArray(captures) ? captures.filter(isTaken) : []
  } catch {
    return []
  }
}

/**
 * Write the index. A narrowed run keeps what an earlier one took of the other surfaces, where
 * the picture is still on disk, so the index always describes the directory.
 */
function indexed(directory: string, build: unknown, taken: readonly Taken[], narrowed: boolean) {
  const file = path.join(directory, 'index.json')
  const retaken = new Set(taken.map((one) => one.file))
  const kept = narrowed
    ? earlierCaptures(file).filter(
        (one) => !retaken.has(one.file) && existsSync(path.join(directory, one.file)),
      )
    : []
  const captures = [...kept, ...taken]
  writeFileSync(file, `${JSON.stringify({ build, captures }, null, 2)}\n`, 'utf8')
  return captures
}

async function main(): Promise<number> {
  const only = onlyFrom(process.argv.slice(2))
  refuseIfStale()

  const directory = path.join(REPO, SHOTS_DIRECTORY)
  mkdirSync(directory, { recursive: true })
  if (only.length === 0) {
    for (const name of readdirSync(directory)) {
      if (name.endsWith('.png') || name === 'index.json') rmSync(path.join(directory, name))
    }
  }

  const fixture = await buildFixture(liveEngine, { open: 3, shipped: 1, deferred: 1 })
  const userData = mkdtempSync(path.join(tmpdir(), 'rk-shots-'))
  let failed = 0
  try {
    const id = listedTasks(await read(fixture.root, 'list', {}))[0]?.id ?? ''
    const captures = capturesFor({ root: fixture.root, id, key: 'no-session' }, only)
    saveSettings(userData, { ...DEFAULT_SETTINGS, roots: [{ path: fixture.root, depth: 0 }] })

    const shot = await launchForShots(userData)
    const taken: Taken[] = []
    try {
      let painted = ''
      for (const capture of captures) {
        const look = `${capture.ground}.${capture.locale}`
        if (look !== painted) {
          await speakAndPaint(shot, capture.ground, capture.locale)
          painted = look
        }
        try {
          const settled = await takeCapture(shot, capture, directory)
          taken.push({ ...capture, settled })
          process.stdout.write(`${settled ? 'settled  ' : 'unsettled'} ${capture.file}\n`)
        } catch (cause) {
          failed += 1
          process.stderr.write(`not taken ${capture.file}: ${String(cause).split('\n')[0]}\n`)
        }
      }
      const all = indexed(directory, await buildOf(shot), taken, only.length > 0)
      const unsettled = taken.filter((one) => !one.settled).length
      process.stdout.write(
        `${String(taken.length)} pictures in ${SHOTS_DIRECTORY}/ (${String(unsettled)} unsettled, ` +
          `${String(failed)} not taken); the index lists ${String(all.length)}\n`,
      )
    } finally {
      await shot.close()
    }
  } finally {
    fixture.dispose()
    await liveHeld.close()
    removeTree(userData)
  }
  return failed === 0 ? 0 : 1
}

main().then(
  (code) => {
    process.exitCode = code
  },
  (cause: unknown) => {
    process.stderr.write(
      `roadkeep-gui shots: ${cause instanceof Error ? cause.message : String(cause)}\n`,
    )
    process.exitCode = 1
  },
)
