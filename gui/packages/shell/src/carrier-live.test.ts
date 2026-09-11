import { buildArgv, buildCall, DEFAULT_SETTINGS } from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { liveEngine, REPO } from './live'
import { startApp, type RunningApp } from './running-app'
import { saveSettings } from './settings-file'

/**
 * RG143: a project read by the window, over IPC, from the built app.
 *
 * Everything below `window.roadkeep` is real: the preload's three new methods, the handlers
 * main registered, the carrier's walk of the one root the profile names, `openHere` holding
 * an engine for it, and the guard in front of all of it. The unit tests hold each of those
 * against a machine; this holds that they are wired to each other.
 *
 * The profile is a throwaway one naming a fixture as its only root, at depth zero, so the
 * walk is one directory and the project is one nobody else is reading. The app is asked to
 * quit rather than killed, which is how the engine it holds in the fixture is given back
 * before the fixture is removed.
 */

let fixture: Fixture
let app: RunningApp

beforeAll(async () => {
  fixture = await buildFixture(liveEngine, { open: 2, shipped: 0, deferred: 0 })
  app = await startApp({}, (userData) => {
    saveSettings(userData, { ...DEFAULT_SETTINGS, roots: [{ path: fixture.root, depth: 0 }] })
  })
}, 180000)

afterAll(async () => {
  await app.close()
  fixture.dispose()
})

/** One bridge call, its arguments carried into the page as JSON. */
function asked<T>(method: string, ...args: unknown[]): Promise<T> {
  const spelled = args.map((one) => JSON.stringify(one)).join(', ')
  return app.evaluate<T>(`window['roadkeep'].${method}(${spelled})`)
}

describe('RG143: the window asks, and main answers from an engine', () => {
  it('lists the project under the one root the profile names', async () => {
    const catalogue = await asked<{ projects: { path: string; presence: string }[] }>('projects')

    expect(catalogue.projects).toHaveLength(1)
    expect(catalogue.projects[0]?.presence).toBe('present')
  })

  it('opens it where the engine can be held, and answers with the engine it resolved', async () => {
    const opened = await asked<{
      kind: string
      engine?: { payload: { writing: { version: string } } }
    }>('open', fixture.root)

    expect(opened.kind).toBe('open')
    expect(opened.engine?.payload.writing.version).toMatch(/^\d+\.\d+\.\d+/)
  })

  it('runs one read over IPC and hands back what the engine printed', async () => {
    const answer = await asked<{ kind: string; result?: { code: number; stdout: string } }>(
      'run',
      fixture.root,
      { argv: buildArgv(fixture.root, 'list', {}), call: buildCall('list', {}) },
    )

    expect(answer.kind).toBe('ran')
    expect(answer.result?.code).toBe(0)
    const listed = JSON.parse(answer.result?.stdout ?? '{}') as { tasks?: { id: string }[] }
    expect(listed.tasks?.map((task) => task.id)).toEqual(['FX1', 'FX2'])
  })

  it('withholds a governed folder the profile never named, before anything starts', async () => {
    // This repository is governed and has an engine, and no root the person named holds it.
    const opened = await asked<{ kind: string }>('open', REPO)
    const answer = await asked<{ kind: string; reason?: string }>('run', REPO, {
      argv: buildArgv(REPO, 'list', {}),
    })

    expect(opened.kind).toBe('withheld')
    expect(answer).toMatchObject({ kind: 'failed', reason: 'withheld' })
  })

  it('withholds a command line that names a file, though the project is its own', async () => {
    const answer = await asked<{ kind: string; reason?: string; message?: string }>(
      'run',
      fixture.root,
      {
        argv: [
          '-C',
          fixture.root,
          'section',
          'add',
          'FX1',
          '--title',
          'T',
          '--body-file',
          REPO,
          '--json',
        ],
      },
    )

    expect(answer).toMatchObject({ kind: 'failed', reason: 'withheld' })
    expect(answer.message).toContain('--body-file')
  })
})
