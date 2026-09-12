import { mkdtempSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { DEFAULT_SETTINGS } from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { removeTree } from './scratch'
import { saveSettings } from './settings-file'
import { launchForShots, speakAndPaint, takeCapture, type ShotApp } from './shots-app'
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
    const capture = capturesFor({ root: 'unused', id: 'unused', key: 'unused' }, ['settings']).find(
      (one) => one.ground === 'dark' && one.locale === 'pt-BR' && one.width === 400,
    )
    if (capture === undefined) throw new Error('the plan has no dark Portuguese phone capture')

    await speakAndPaint(shot, capture.ground, capture.locale)
    const settled = await takeCapture(shot, capture, out)

    expect(settled).toBe(true)
    // The emulated width, not the window's: the window stops at its minimum well above 400.
    expect(sizeOf(path.join(out, capture.file))).toEqual({ png: true, width: 400, height: 800 })
    // And the page is the one it was asked for, in the language it was put in.
    expect(await shot.page.evaluate('document.documentElement.classList.contains("dark")')).toBe(
      true,
    )
    expect(await shot.page.evaluate('location.hash')).toBe('#/settings')
  }, 60000)

  it('closes without waiting on a quit the app defers', async () => {
    const started = Date.now()
    await shot.close()

    expect(shot.exited()).toBe(true)
    expect(Date.now() - started).toBeLessThan(10000)
  }, 20000)
})
