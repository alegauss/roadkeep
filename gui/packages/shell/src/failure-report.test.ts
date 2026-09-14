import { describe, expect, it } from 'vitest'

import {
  keptRun,
  reportName,
  worthKeeping,
  type ReadableCase,
  type ReadableModule,
} from './failure-report'

/**
 * RG232: what a run that went red keeps of itself.
 *
 * The reporter's own shape, asserted without starting a run that fails: `keptRun` takes the
 * modules, the clock and the arguments rather than reading any of them, so a case here is an
 * object literal that vitest's `TestCase` happens to satisfy.
 *
 * What is held is the pair the defect needed — a green run writes nothing, and a red one
 * writes a file no later run can overwrite — plus the two messages a terminal reporter
 * buries: the assertion's own diff, and an error belonging to no test at all.
 */

const AT = new Date('2026-01-02T03:04:05.678Z')

function failed(name: string, message: string): ReadableCase {
  return {
    fullName: name,
    project: { name: 'ui' },
    module: { relativeModuleId: 'src/task.test.tsx' },
    result: () => ({
      state: 'failed',
      errors: [{ name: 'AssertionError', message, stack: 'at src/task.test.tsx:12:5' }],
    }),
    diagnostic: () => ({ duration: 1042, retryCount: 1, repeatCount: 0, flaky: true }),
  }
}

function module_(
  tests: readonly ReadableCase[],
  errors: readonly { name: string; message: string }[] = [],
): ReadableModule {
  return {
    relativeModuleId: 'src/task.test.tsx',
    children: { allTests: () => tests },
    errors: () => errors,
  }
}

describe('RG232: a red run keeps its message', () => {
  it('keeps the failing test, its diagnostic and the assertion that threw', () => {
    const run = keptRun({
      modules: [module_([failed('a task opens > from Open', 'unable to find a heading')])],
      unhandled: [],
      reason: 'failed',
      at: AT,
      argv: ['run', '--project', 'ui'],
    })

    expect(worthKeeping(run)).toBe(true)
    expect(run.failures).toHaveLength(1)
    const [failure] = run.failures
    expect(failure?.project).toBe('ui')
    expect(failure?.module).toBe('src/task.test.tsx')
    expect(failure?.test).toBe('a task opens > from Open')
    // The three the defect needed: how long it waited, whether a retry saved it, and what
    // the assertion actually said.
    expect(failure?.durationMs).toBe(1042)
    expect(failure?.flaky).toBe(true)
    expect(failure?.errors[0]?.message).toBe('unable to find a heading')
    expect(failure?.errors[0]?.stack).toBe('at src/task.test.tsx:12:5')
    // The run's own context, so a report found later says which suite it came out of.
    expect(run.argv).toEqual(['run', '--project', 'ui'])
    expect(run.at).toBe('2026-01-02T03:04:05.678Z')
  })

  it('keeps an error no test carries, which is the one a terminal buries deepest', () => {
    const run = keptRun({
      modules: [module_([], [{ name: 'SyntaxError', message: 'Unexpected token' }])],
      unhandled: [{ name: 'Error', message: 'rejected after the run' }],
      reason: 'failed',
      at: AT,
      argv: [],
    })

    expect(run.failures).toHaveLength(0)
    expect(worthKeeping(run)).toBe(true)
    expect(run.outside.map((one) => [one.where, one.error.message])).toEqual([
      ['src/task.test.tsx', 'Unexpected token'],
      ['run', 'rejected after the run'],
    ])
  })

  it('writes nothing for a run with nothing to keep, so a loop leaves one file per red run', () => {
    const green = keptRun({
      modules: [module_([])],
      unhandled: [],
      reason: 'passed',
      at: AT,
      argv: [],
    })

    expect(worthKeeping(green)).toBe(false)
  })

  it('names a report for the instant and the process, so the next run cannot erase it', () => {
    // Colons are not a filename on Windows, which is the one substitution this makes.
    expect(reportName(AT, 4321)).toBe('2026-01-02T03-04-05.678Z-4321.json')
    expect(reportName(AT, 4322)).not.toBe(reportName(AT, 4321))
    expect(reportName(new Date('2026-01-02T03:04:05.679Z'), 4321)).not.toBe(reportName(AT, 4321))
  })
})
