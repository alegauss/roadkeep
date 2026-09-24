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

import { DEFAULT_SETTINGS, lineOf, listedTasks } from '@rk/core'

import { GATED_IMPACTS, outlivedFindings, unexcusedFindings } from './accessibility'
import { AGENT_VAR } from './agent-candidates'
import { refuseIfStale } from './built'
import { buildFixture } from './fixture'
import { liveEngine, liveHeld, read, REPO } from './live'
import { removeTree } from './scratch'
import { saveSettings } from './settings-file'
import { keepAnswers } from './shots-kept'
import { CAPTURED_GLOSS, scriptedAgent } from './scripted-agent'
import {
  buildOf,
  launchForShots,
  speakAndPaint,
  startSession,
  takeCapture,
  type Scan,
} from './shots-app'
import { capturesFor, isScanned, optionsFrom, SHOTS_DIRECTORY, type Capture } from './shots-plan'

/**
 * `npm run shots`: every surface the window serves, photographed (RG209).
 *
 * The tests render jsdom, which lays nothing out, so a chosen toggle at 1.27:1 against its
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

/**
 * Judge the scans and write what they found beside the pictures (RG211).
 *
 * @returns how many things fail the run: findings nobody excused, and — on a run over every
 *   surface, the only one that could have met them — exceptions nothing named any more.
 */
function judged(directory: string, scans: readonly Scanned[], narrowed: boolean): number {
  const findings = scans.flatMap((one) => one.findings)
  const unexcused = unexcusedFindings(findings)
  const outlived = narrowed ? [] : outlivedFindings(findings)
  writeFileSync(
    path.join(directory, 'a11y.json'),
    `${JSON.stringify({ gatedAt: GATED_IMPACTS, scans, unexcused, outlived }, null, 2)}\n`,
    'utf8',
  )
  for (const one of unexcused) {
    process.stderr.write(
      `a11y ${one.impact} ${one.rule} on ${one.surface} (${one.ground}): ${one.target} — ${one.help}\n`,
    )
  }
  for (const one of outlived) {
    process.stderr.write(`a11y exception no scan named: ${one.rule} ${one.target}\n`)
  }
  process.stdout.write(
    `${String(scans.length)} scans: ${String(findings.length)} findings, ` +
      `${String(unexcused.length)} unexcused, ${String(outlived.length)} outlived exceptions\n`,
  )
  return unexcused.length + outlived.length
}

interface Scanned extends Scan {
  readonly surface: string
  readonly state: string | null
  readonly ground: string
}

async function main(): Promise<number> {
  const { only, a11yOnly } = optionsFrom(process.argv.slice(2))
  refuseIfStale()

  const directory = path.join(REPO, SHOTS_DIRECTORY)
  mkdirSync(directory, { recursive: true })
  if (only.length === 0 && !a11yOnly) {
    for (const name of readdirSync(directory)) {
      if (name.endsWith('.png') || name === 'index.json') rmSync(path.join(directory, name))
    }
  }

  // Governed and committed since RG300, so one entry awaits a person: the validation tab has a
  // row to draw and the walkthrough dialog has something to open on.
  const fixture = await buildFixture(liveEngine, {
    open: 3,
    shipped: 1,
    deferred: 1,
    validating: true,
  })
  const userData = mkdtempSync(path.join(tmpdir(), 'rk-shots-'))
  // The session surface is photographed mid-run against an agent that replays one (RG210), and
  // the task surface's explanation against the gloss a real read wrote (RG285).
  const agent = scriptedAgent({ gloss: CAPTURED_GLOSS })
  let failed = 0
  try {
    const [first, second] = listedTasks(await read(fixture.root, 'list', {}))
    saveSettings(userData, { ...DEFAULT_SETTINGS, roots: [{ path: fixture.root, depth: 0 }] })

    // What this machine has kept (RG300): the two dialogs are photographed on an answer, which
    // is the state a fresh run can never be in. The entry is the one awaiting a person and the
    // commit is the one the engine placed it at — a walkthrough about another one reads as old.
    const awaits = (await read(fixture.root, 'unvalidated', {})).unvalidated[0]
    const shipped = await read(fixture.root, 'origin', { id: awaits?.id ?? '' })
    const briefed = lineOf(await read(fixture.root, 'brief', { id: first?.id ?? '' }))
    if (briefed === null) throw new Error('the fixture opened no line to keep a gloss for')
    keepAnswers(userData, fixture.root, briefed, awaits?.id ?? '', shipped.shippedIn?.sha ?? '')

    const shot = await launchForShots(userData, { [AGENT_VAR]: JSON.stringify(agent.command) })
    const taken: Taken[] = []
    const scans: Scanned[] = []
    try {
      const key = await startSession(shot, fixture.root, second?.id ?? '', agent.lines)
      const planned = capturesFor(
        { root: fixture.root, id: first?.id ?? '', sessionId: second?.id ?? '', key },
        only,
      )
      const captures = a11yOnly ? planned.filter(isScanned) : planned
      let painted = ''
      for (const capture of captures) {
        const look = `${capture.ground}.${capture.locale}`
        if (look !== painted) {
          await speakAndPaint(shot, capture.ground, capture.locale)
          painted = look
        }
        try {
          const done = await takeCapture(shot, capture, directory, {
            picture: !a11yOnly,
            scan: isScanned(capture),
          })
          if (done.scan !== null) {
            const { surface, state, ground } = capture
            scans.push({ surface, state, ground, ...done.scan })
          }
          if (!a11yOnly) {
            taken.push({ ...capture, settled: done.settled })
            process.stdout.write(`${done.settled ? 'settled  ' : 'unsettled'} ${capture.file}\n`)
          }
        } catch (cause) {
          failed += 1
          process.stderr.write(`not taken ${capture.file}: ${String(cause).split('\n')[0]}\n`)
        }
      }
      if (!a11yOnly) {
        const all = indexed(directory, await buildOf(shot), taken, only.length > 0)
        const unsettled = taken.filter((one) => !one.settled).length
        process.stdout.write(
          `${String(taken.length)} pictures in ${SHOTS_DIRECTORY}/ (${String(unsettled)} ` +
            `unsettled, ${String(failed)} not taken); the index lists ${String(all.length)}\n`,
        )
      }
      failed += judged(directory, scans, only.length > 0)
    } finally {
      await shot.close()
    }
  } finally {
    fixture.dispose()
    await liveHeld.close()
    removeTree(userData)
    agent.dispose()
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
