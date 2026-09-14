import { mkdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'

import type { Reporter, SerializedError, TestModule, TestRunEndReason, Vitest } from 'vitest/node'

/**
 * What a run that went red leaves behind (RG232).
 *
 * A terminal reporter prints a failure and keeps nothing. That is fine while a test fails
 * every time — you run it again and read it — and useless for the one that fails once in a
 * hundred runs: RG232 exists because `task.test.tsx` went red inside a full suite, was green
 * on every run since, and nobody can say what it waited on, the message being gone.
 *
 * So the suite writes its own evidence. **Only a run with something to keep writes a file**,
 * and every file is named for the moment it was written — which is the pair that makes this
 * usable under the loop that reproduces a flake: a hundred runs in a row leave one file per
 * red one, a green run neither writes nor overwrites, and the next run cannot erase the
 * message the last one caught.
 *
 * It is the whole run's reporter and not the fast suite's: `npm test`, `npm run test:live`
 * and `npm run test:all` go through the same root config, and a flake in a live test is the
 * harder one to catch twice.
 *
 * The directory is `.vitest/`, already ignored by git and by Prettier, beside the
 * screenshots Browser Mode leaves there for the same reason.
 */

/** Where a report lands, under the repository root. */
export const REPORT_DIR = path.join('.vitest', 'failures')

/** One error, flattened: what was thrown, what was expected, and where it was thrown from. */
export interface KeptError {
  readonly name: string
  readonly message: string
  readonly diff: string
  readonly expected: string
  readonly actual: string
  readonly stack: string
}

/** One test that went red, named the way a `-t` filter would take it. */
export interface KeptFailure {
  readonly project: string
  readonly module: string
  readonly test: string
  readonly durationMs: number
  readonly retries: number
  readonly repeats: number
  /** True where it failed and then passed on a retry, which is this defect's own shape. */
  readonly flaky: boolean
  readonly errors: readonly KeptError[]
}

/** An error that belongs to no test: a module that would not collect, or an unhandled one. */
export interface KeptOutside {
  /** The module it came from, or `run` for one nothing collected. */
  readonly where: string
  readonly error: KeptError
}

/** One run's evidence, as the file stores it. */
export interface KeptRun {
  readonly version: 1
  readonly at: string
  readonly reason: TestRunEndReason
  /** The arguments the run was started with, which say which projects were in it. */
  readonly argv: readonly string[]
  readonly failures: readonly KeptFailure[]
  readonly outside: readonly KeptOutside[]
}

/**
 * The little of vitest's `TestCase` this reads.
 *
 * Structural on purpose: vitest's own class satisfies it, and a test can hand this one a
 * case it built out of an object literal — which is what lets the report's shape be asserted
 * without starting a run that fails.
 */
export interface ReadableCase {
  readonly fullName: string
  readonly project: { readonly name: string }
  readonly module: { readonly relativeModuleId: string }
  result: () => { readonly state: string; readonly errors: readonly SerializedError[] | undefined }
  diagnostic: () =>
    | {
        readonly duration: number
        readonly retryCount: number
        readonly repeatCount: number
        readonly flaky: boolean
      }
    | undefined
}

/** The little of `TestModule` this reads, structural for the same reason. */
export interface ReadableModule {
  readonly relativeModuleId: string
  readonly children: { allTests: (state?: 'failed') => Iterable<ReadableCase> }
  errors: () => readonly SerializedError[]
}

/**
 * A `SerializedError` as the file keeps it: every field a string, and absent means empty.
 *
 * `diff`, `expected` and `actual` are `TestError`'s and reached through `SerializedError`'s
 * own index signature, which is what an assertion here would be adding nothing to: a module
 * error carries none of the three, and a missing one is the empty string either way.
 */
export function keptError(error: SerializedError): KeptError {
  return {
    name: text(error.name),
    message: text(error.message),
    diff: text(error.diff),
    expected: text(error.expected),
    actual: text(error.actual),
    stack: text(error.stack),
  }
}

function text(value: unknown): string {
  if (typeof value === 'string') return value
  if (value === undefined || value === null) return ''
  try {
    // An `expected` that is an object arrives as one. Serialised rather than coerced: `String`
    // of an object is `[object Object]`, which is the evidence thrown away.
    //
    // Read back as `unknown` because the signature is not quite true: `JSON.stringify` is
    // declared to return a string and answers `undefined` for a function, a symbol, or
    // anything whose `toJSON` does. The `catch` is the other half of the same care — a cycle
    // or a BigInt throws, and a reporter that threw on the way out would take the run's own
    // exit code with it.
    const said: unknown = JSON.stringify(value)
    return typeof said === 'string' ? said : ''
  } catch {
    return ''
  }
}

/** One failed case, flattened. */
export function keptFailure(test: ReadableCase): KeptFailure {
  const result = test.result()
  const diagnostic = test.diagnostic()
  return {
    project: test.project.name,
    module: test.module.relativeModuleId,
    test: test.fullName,
    durationMs: diagnostic?.duration ?? 0,
    retries: diagnostic?.retryCount ?? 0,
    repeats: diagnostic?.repeatCount ?? 0,
    flaky: diagnostic?.flaky ?? false,
    errors: (result.errors ?? []).map((error) => keptError(error)),
  }
}

/**
 * The whole run, as the file stores it.
 *
 * Pure, and every argument is passed rather than read off the process: the clock, the
 * arguments and the modules are all things a test hands over.
 */
export function keptRun(run: {
  readonly modules: Iterable<ReadableModule>
  readonly unhandled: readonly SerializedError[]
  readonly reason: TestRunEndReason
  readonly at: Date
  readonly argv: readonly string[]
}): KeptRun {
  const failures: KeptFailure[] = []
  const outside: KeptOutside[] = []

  for (const module of run.modules) {
    for (const test of module.children.allTests('failed')) failures.push(keptFailure(test))
    // A module that would not collect — a syntax error, an import that threw — has no failed
    // test to carry its message, and is the case a terminal reporter buries deepest.
    for (const error of module.errors())
      outside.push({ where: module.relativeModuleId, error: keptError(error) })
  }
  for (const error of run.unhandled) outside.push({ where: 'run', error: keptError(error) })

  return {
    version: 1,
    at: run.at.toISOString(),
    reason: run.reason,
    argv: [...run.argv],
    failures,
    outside,
  }
}

/** Whether this run left anything worth a file. A green run writes nothing. */
export function worthKeeping(run: KeptRun): boolean {
  return run.failures.length > 0 || run.outside.length > 0
}

/**
 * The file one run writes, under `REPORT_DIR`.
 *
 * Named for the instant and the process: the loop that reproduces a flake runs the suite
 * again and again, and a fixed name would mean the run after the red one erased it.
 */
export function reportName(at: Date, pid: number): string {
  const stamp = at.toISOString().replaceAll(':', '-')
  return `${stamp}-${pid}.json`
}

/** Write one run's evidence and answer where it went. */
export function writeReport(root: string, run: KeptRun, pid: number): string {
  const into = path.join(root, REPORT_DIR)
  mkdirSync(into, { recursive: true })
  const where = path.join(into, reportName(new Date(run.at), pid))
  writeFileSync(where, `${JSON.stringify(run, null, 2)}\n`, 'utf8')
  return where
}

/**
 * The reporter itself, named in the root `vitest.config.ts` beside `default`.
 *
 * It prints one line and only when it wrote something: a reporter that announces itself on
 * every green run is noise on the run nobody is debugging.
 */
export default class FailureReport implements Reporter {
  #root = process.cwd()

  onInit(vitest: Vitest): void {
    this.#root = vitest.config.root
  }

  onTestRunEnd(
    modules: readonly TestModule[],
    unhandled: readonly SerializedError[],
    reason: TestRunEndReason,
  ): void {
    const run = keptRun({
      modules,
      unhandled,
      reason,
      at: new Date(),
      argv: process.argv.slice(2),
    })
    if (!worthKeeping(run)) return

    const where = writeReport(this.#root, run, process.pid)
    console.log(`\n  ${run.failures.length} failed, kept in ${path.relative(this.#root, where)}`)
  }
}
