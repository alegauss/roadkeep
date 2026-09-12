import { mkdtempSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { DEFAULT_SETTINGS, listedTasks } from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { CHOSEN_SCRIPT, chosenFindings, judgeChosen, readingsFrom } from './accessibility'
import { AGENT_VAR } from './agent-candidates'
import { buildFixture, type Fixture } from './fixture'
import { liveEngine, read } from './live'
import { removeTree } from './scratch'
import { scriptedAgent, type ScriptedAgent } from './scripted-agent'
import { saveSettings } from './settings-file'
import { launchForShots, speakAndPaint, startSession, takeCapture, type ShotApp } from './shots-app'
import { capturesFor } from './shots-plan'

/**
 * RG209: Playwright drives this app, on every machine the live suite runs on.
 *
 * Its Electron support is marked experimental, so what the screenshot run stands on is held
 * here rather than trusted: the built app launches through `_electron`, takes a ground and a
 * language, is read at phone width, and closes — on Windows where it was measured, and under
 * `xvfb` on the Linux runner, where the live suite already starts the app.
 *
 * No fixture: the settings surface is about no project, so an empty profile is enough to prove
 * the launch and the capture.
 */

const directories: string[] = []
let shot: ShotApp

/** A PNG's width and height, off its header. */
function sizeOf(file: string): { width: number; height: number; png: boolean } {
  const bytes = readFileSync(file)
  return {
    png: bytes.subarray(1, 4).toString('ascii') === 'PNG',
    width: bytes.readUInt32BE(16),
    height: bytes.readUInt32BE(20),
  }
}

beforeAll(async () => {
  const userData = mkdtempSync(path.join(tmpdir(), 'rk-shots-live-'))
  directories.push(userData)
  saveSettings(userData, DEFAULT_SETTINGS)
  shot = await launchForShots(userData)
}, 60000)

afterAll(async () => {
  // Absent where the launch itself failed, which is the failure to read and not this one.
  if (typeof shot !== 'undefined') await shot.close()
  for (const directory of directories) removeTree(directory)
})

describe('RG209: a surface photographed through Playwright', () => {
  it('takes the settings surface at phone width, in the dark ground and Portuguese', async () => {
    const out = mkdtempSync(path.join(tmpdir(), 'rk-shots-out-'))
    directories.push(out)
    const unused = { root: 'unused', id: 'unused', sessionId: 'unused', key: 'unused' }
    const capture = capturesFor(unused, ['settings']).find(
      (one) => one.ground === 'dark' && one.locale === 'pt-BR' && one.width === 400,
    )
    if (capture === undefined) throw new Error('the plan has no dark Portuguese phone capture')

    await speakAndPaint(shot, capture.ground, capture.locale)
    const { settled } = await takeCapture(shot, capture, out)

    expect(settled).toBe(true)
    // The emulated width, not the window's: the window stops at its minimum well above 400.
    expect(sizeOf(path.join(out, capture.file))).toEqual({ png: true, width: 400, height: 800 })
    // And the page is the one it was asked for, in the language it was put in.
    expect(await shot.page.evaluate('document.documentElement.classList.contains("dark")')).toBe(
      true,
    )
    expect(await shot.page.evaluate('location.hash')).toBe('#/settings')
  }, 60000)

  it('scans a surface with axe and reads every chosen option beside a sibling (RG211)', async () => {
    const capture = capturesFor(
      { root: 'unused', id: 'unused', sessionId: 'unused', key: 'unused' },
      ['settings'],
    ).find((one) => one.ground === 'dark' && one.locale === 'en' && one.width === 1280)
    if (capture === undefined) throw new Error('the plan has no dark English desktop capture')

    await speakAndPaint(shot, capture.ground, capture.locale)
    const { scan } = await takeCapture(shot, capture, directories[0] ?? '', {
      picture: false,
      scan: true,
    })
    if (scan === null) throw new Error('a capture asked to scan returned no scan')

    // The ground, the language and the notes, each a group with one option chosen — RG207's
    // toggle, drawn in the dark ground where its accent alone was 1.27:1, and marked since.
    expect(scan.chosen.length).toBeGreaterThanOrEqual(3)
    expect(scan.chosen.every((one) => one.marked)).toBe(true)
    expect(scan.findings.filter((one) => one.rule === 'chosen-state-told-by-shade')).toEqual([])
  }, 60000)

  it('fails a chosen option told apart by a shade alone, as the window paints it (RG211)', async () => {
    // RG207's toggle before its mark, rebuilt in the page: the dark accent on the dark panel,
    // chosen and not, nothing else between them. Styled through the CSSOM, which the content
    // policy allows, and removed after.
    const readings = await shot.page.evaluate(`(() => {
      const group = document.createElement('div')
      group.setAttribute('role', 'radiogroup')
      group.id = 'rg211-shade-only'
      for (const [label, checked, colour] of [['Before', 'true', '#333333'], ['After', 'false', '#212121']]) {
        const option = document.createElement('button')
        option.setAttribute('role', 'radio')
        option.setAttribute('aria-checked', checked)
        option.textContent = label
        option.style.backgroundColor = colour
        option.style.border = 'none'
        group.append(option)
      }
      document.body.append(group)
      const read = ${CHOSEN_SCRIPT}
      group.remove()
      return read.filter((one) => one.target === 'radio "Before"')
    })()`)
    const [verdict] = readingsFrom(readings).map((one) => judgeChosen(one))

    expect(verdict?.readable).toBe(false)
    expect(chosenFindings(verdict === undefined ? [] : [verdict], 'settings', 'dark')).toHaveLength(
      1,
    )
  }, 30000)

  it('closes without waiting on a quit the app defers', async () => {
    const started = Date.now()
    await shot.close()

    expect(shot.exited()).toBe(true)
    expect(Date.now() - started).toBeLessThan(10000)
  }, 20000)
})

describe('RG210: a session photographed mid-run, against a scripted agent', () => {
  let fixture: Fixture
  let agent: ScriptedAgent
  let running: ShotApp
  let key = ''
  let sessionId = ''
  let out = ''

  beforeAll(async () => {
    fixture = await buildFixture(liveEngine, { open: 2, shipped: 0, deferred: 0 })
    agent = scriptedAgent({ tail: 60, intervalMs: 5 })
    const userData = mkdtempSync(path.join(tmpdir(), 'rk-shots-session-'))
    out = mkdtempSync(path.join(tmpdir(), 'rk-shots-session-out-'))
    directories.push(userData, out)
    saveSettings(userData, { ...DEFAULT_SETTINGS, roots: [{ path: fixture.root, depth: 0 }] })
    sessionId = listedTasks(await read(fixture.root, 'list', {}))[1]?.id ?? ''

    running = await launchForShots(userData, { [AGENT_VAR]: JSON.stringify(agent.command) })
    // English and light whatever the desktop speaks: the assertions below read the words.
    await speakAndPaint(running, 'light', 'en')
    key = await startSession(running, fixture.root, sessionId, agent.lines)
  }, 180000)

  afterAll(async () => {
    if (typeof running !== 'undefined') await running.close()
    agent.dispose()
    fixture.dispose()
  })

  function sessionCapture(state: string) {
    const found = capturesFor({ root: fixture.root, id: sessionId, sessionId, key }, [
      'project-task-session',
    ]).find((one) => one.state === state && one.width === 1280 && one.ground === 'light')
    if (found === undefined) throw new Error(`the plan has no ${state} session capture`)
    return found
  }

  it('starts the session on the scripted agent, which the screen names', async () => {
    const capture = sessionCapture('following')
    expect((await takeCapture(running, capture, out)).settled).toBe(true)

    expect(await running.page.evaluate('document.body.innerText')).toContain('2.1.263')
  })

  it('shows the way back to the end once the stream is scrolled up', async () => {
    const capture = sessionCapture('scrolled')
    await takeCapture(running, capture, out)

    // The region overflows and was left at its top, so following stopped (RG206).
    expect(
      await running.page.evaluate('document.querySelector(\'[data-testid="stream"]\').scrollTop'),
    ).toBe(0)
    expect(await running.page.evaluate('document.body.innerText')).toMatch(/Jump to latest/)
  })

  it('folds the notes for its picture, and puts the preference back after it', async () => {
    const capture = sessionCapture('folded')
    await takeCapture(running, capture, out)

    expect(
      await running.page.evaluate(
        'window.roadkeep.settings().then((s) => s.settings.sessionNotes)',
      ),
    ).toBe('shown')
    expect(sizeOf(path.join(out, capture.file))).toEqual({ png: true, width: 1280, height: 800 })
  })
})
