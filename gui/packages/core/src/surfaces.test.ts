import { describe, expect, it } from 'vitest'

import {
  filledRoute,
  HOME_ROUTE,
  routeParams,
  SESSION_ROUTE,
  SURFACE_ROUTES,
  TASK_ROUTE,
} from './surfaces'

describe('RG209: the routes, in one list both halves read', () => {
  it('names each route once', () => {
    expect(new Set(SURFACE_ROUTES).size).toBe(SURFACE_ROUTES.length)
    expect(SURFACE_ROUTES).toContain(HOME_ROUTE)
  })

  it('reads the parameters a pattern names, in order', () => {
    expect(routeParams(SESSION_ROUTE)).toEqual(['root', 'id', 'key'])
    expect(routeParams(HOME_ROUTE)).toEqual([])
  })

  it('fills a pattern, encoding a root whole the way the path builders do', () => {
    expect(filledRoute(TASK_ROUTE, { root: 'D:\\code\\alpha', id: 'AL1' })).toBe(
      `/project/${encodeURIComponent('D:\\code\\alpha')}/task/AL1`,
    )
    expect(filledRoute(HOME_ROUTE, {})).toBe('/')
  })

  it('answers nothing for a pattern with a parameter left unfilled', () => {
    expect(filledRoute(TASK_ROUTE, { root: 'D:\\code\\alpha' })).toBeNull()
    expect(filledRoute(TASK_ROUTE, { root: 'D:\\code\\alpha', id: '' })).toBeNull()
  })
})
