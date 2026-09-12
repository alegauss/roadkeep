import { LOCALE_TAGS, SURFACE_ROUTES } from '@rk/core'
import { describe, expect, it } from 'vitest'

import {
  capturesFor,
  onlyFrom,
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

const VALUES = { root: 'C:\\Temp\\rk-fixture-abc', id: 'FX1', key: 'no-session' }

describe('RG209: every surface the router serves', () => {
  it('is filled from the fixture, so a surface routed without a shot fails here', () => {
    const surfaces = new Set(capturesFor(VALUES).map((one) => one.pattern))

    expect([...surfaces].sort()).toEqual([...SURFACE_ROUTES].sort())
  })

  it('is taken in both grounds, every language and both widths', () => {
    const captures = capturesFor(VALUES)

    expect(captures).toHaveLength(
      SURFACE_ROUTES.length * SHOT_GROUNDS.length * LOCALE_TAGS.length * SHOT_SIZES.length,
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

describe('RG209: narrowing a run', () => {
  it('keeps the surfaces --only names, however they are spelled on the line', () => {
    expect(onlyFrom(['--only', 'settings', '--only', 'sessions,home'])).toEqual([
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
    expect(() => onlyFrom(['--all'])).toThrow(/--only/)
    expect(() => onlyFrom(['--only'])).toThrow(/names a surface/)
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
