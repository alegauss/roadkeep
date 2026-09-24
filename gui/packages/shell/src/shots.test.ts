import { LOCALE_TAGS, SURFACE_ROUTES } from '@rk/core'
import { describe, expect, it } from 'vitest'

import {
  capturesFor,
  isScanned,
  optionsFrom,
  PROJECT_SHOTS,
  SESSION_SHOTS,
  TASK_SHOTS,
  settleScript,
  SHOT_GROUNDS,
  SHOT_SIZES,
  surfaceName,
} from './shots-plan'

/**
 * RG209: what the screenshot run photographs, before anything starts.
 *
 * The half a fast test can hold: every routed surface is filled from the fixture and
 * photographed in each ground, language and width, under a name no two captures share.
 */

const VALUES = { root: 'C:\\Temp\\rk-fixture-abc', id: 'FX1', sessionId: 'FX2', key: 'session-1' }

describe('RG209: every surface the router serves', () => {
  it('is filled from the fixture, so a surface routed without a shot fails here', () => {
    const surfaces = new Set(capturesFor(VALUES).map((one) => one.pattern))

    expect([...surfaces].sort()).toEqual([...SURFACE_ROUTES].sort())
  })

  it('is taken in both grounds, every language and both widths', () => {
    const captures = capturesFor(VALUES)

    // The session surface once per state it is put in (RG210), the task surface once per
    // state of its own (RG285) and the project surface once per tab it is shown on (RG293);
    // every other surface once.
    const pictured =
      SURFACE_ROUTES.length - 3 + SESSION_SHOTS.length + TASK_SHOTS.length + PROJECT_SHOTS.length
    expect(captures).toHaveLength(
      pictured * SHOT_GROUNDS.length * LOCALE_TAGS.length * SHOT_SIZES.length,
    )
    expect(new Set(captures.map((one) => one.ground))).toEqual(new Set(['light', 'dark']))
    expect(new Set(captures.map((one) => one.width))).toEqual(new Set([1280, 400]))
  })

  it('names each picture once, by surface, ground, language and width', () => {
    const files = capturesFor(VALUES).map((one) => one.file)

    expect(new Set(files).size).toBe(files.length)
    expect(files).toContain('project-task.dark.pt-BR.400.png')
    expect(files).toContain('home.light.en.1280.png')
  })

  it('goes to the route the window serves, encoded the way the path builders encode it', () => {
    const task = capturesFor(VALUES).find((one) => one.surface === 'project-task')

    expect(task?.route).toBe(`/project/${encodeURIComponent(VALUES.root)}/task/FX1`)
  })

  it('takes a ground at a time, so a run reloads per ground and language and not per picture', () => {
    const grounds = capturesFor(VALUES).map((one) => `${one.ground}.${one.locale}`)
    const runs = grounds.filter((one, at) => at === 0 || grounds[at - 1] !== one)

    expect(runs).toHaveLength(SHOT_GROUNDS.length * LOCALE_TAGS.length)
  })
})

describe('RG210: the session, photographed in the states a reader puts it in', () => {
  it('takes it following, scrolled up, folded and with a file open, each under a name of its own', () => {
    const session = capturesFor(VALUES, ['project-task-session'])

    expect(new Set(session.map((one) => one.state))).toEqual(new Set(SESSION_SHOTS))
    expect(session.map((one) => one.file)).toContain(
      'project-task-session.scrolled.dark.pt-BR.400.png',
    )
    // The viewer over the session (RG245).
    expect(session.map((one) => one.file)).toContain('project-task-session.file.light.en.1280.png')
    // Every other surface has no state to be put in.
    expect(capturesFor(VALUES, ['settings']).every((one) => one.state === null)).toBe(true)
  })

  it('RG293: takes the project surface on its validation tab as well as at rest', () => {
    const project = capturesFor(VALUES, ['project'])

    expect(new Set(project.map((one) => one.state))).toEqual(new Set(PROJECT_SHOTS))
    expect(project.map((one) => one.file)).toContain('project.validation.dark.pt-BR.400.png')
    // And the walkthrough over one of its rows (RG300).
    expect(project.map((one) => one.file)).toContain('project.checking.light.en.1280.png')
  })

  it('RG300: takes the explanation on a kept answer the reader is told is old', () => {
    const task = capturesFor(VALUES, ['project-task'])

    expect(task.map((one) => one.file)).toContain('project-task.explain-old.dark.pt-BR.400.png')
  })

  it('goes to the line that was handed over, and leaves the task surface on a line nobody holds', () => {
    const [session] = capturesFor(VALUES, ['project-task-session'])
    const [task] = capturesFor(VALUES, ['project-task'])

    expect(session?.route).toBe(
      `/project/${encodeURIComponent(VALUES.root)}/task/FX2/session/session-1`,
    )
    expect(task?.route).toBe(`/project/${encodeURIComponent(VALUES.root)}/task/FX1`)
  })
})

describe('RG211: which pictures are scanned for accessibility', () => {
  it('scans each surface, state and ground once, at the desktop width in the base language', () => {
    const scanned = capturesFor(VALUES).filter(isScanned)
    const pictured =
      SURFACE_ROUTES.length - 3 + SESSION_SHOTS.length + TASK_SHOTS.length + PROJECT_SHOTS.length

    expect(scanned).toHaveLength(pictured * SHOT_GROUNDS.length)
    expect(scanned.every((one) => one.width === 1280 && one.locale === LOCALE_TAGS[0])).toBe(true)
    expect(new Set(scanned.map((one) => one.ground))).toEqual(new Set(SHOT_GROUNDS))
  })
})

describe('RG209: narrowing a run', () => {
  it('keeps the surfaces --only names, however they are spelled on the line', () => {
    expect(optionsFrom(['--only', 'settings', '--only', 'sessions,home']).only).toEqual([
      'settings',
      'sessions',
      'home',
    ])
    const narrowed = capturesFor(VALUES, ['settings'])
    expect(new Set(narrowed.map((one) => one.surface))).toEqual(new Set(['settings']))
  })

  it('refuses a surface nobody is called, naming the ones there are', () => {
    // A typo narrowed to nothing would be a run that says it succeeded.
    expect(() => capturesFor(VALUES, ['setings'])).toThrow(/setings.*settings/)
  })

  it('refuses anything on the line it does not take', () => {
    expect(() => optionsFrom(['--all'])).toThrow(/--only/)
    expect(() => optionsFrom(['--only'])).toThrow(/names a surface/)
  })

  it('reads --a11y-only beside --only, and neither by default (RG211)', () => {
    expect(optionsFrom([])).toEqual({ only: [], a11yOnly: false })
    expect(optionsFrom(['--a11y-only', '--only', 'settings'])).toEqual({
      only: ['settings'],
      a11yOnly: true,
    })
  })

  it('refuses a fixture that cannot fill a route, rather than skipping the surface', () => {
    expect(() => capturesFor({ ...VALUES, id: '' })).toThrow(/cannot fill/)
  })
})

describe('RG209: the names', () => {
  it('reads a surface off its fixed segments', () => {
    expect(surfaceName('/')).toBe('home')
    expect(surfaceName('/project/:root/task/:id/session/:key')).toBe('project-task-session')
  })

  it('waits on the document and never on a clock alone', () => {
    const script = settleScript(400, 10000)

    expect(script).toContain('MutationObserver')
    expect(script).toContain('aria-busy')
    expect(script).toContain('>= 400')
    expect(script).toContain('>= 10000')
  })
})
