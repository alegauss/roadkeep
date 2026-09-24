import { describe, expect, it } from 'vitest'

/**
 * RG1: `core` is the half a web service keeps, and this is what keeps it that.
 *
 * `tsconfig.json` already gives this package neither Node's types nor the DOM's, so a
 * `document` or a `process` is a compile error. What that cannot catch is an *import*:
 * `react` and `electron` are hoisted into the workspace's `node_modules`, so either one
 * would resolve and typecheck here perfectly well, and the first time anybody noticed
 * would be when the service that was supposed to be a transport swap needed a renderer.
 */
const sources = import.meta.glob('./**/*.ts', { query: '?raw', eager: true }) as Record<
  string,
  { default: string }
>

describe('RG1: what the client is allowed to import', () => {
  it('reads its own source, so the assertions below are about something', () => {
    expect(Object.keys(sources).length).toBeGreaterThan(4)
  })

  it.each(['node:', 'electron', 'react'])('imports nothing from %s', (forbidden) => {
    const offenders = Object.entries(sources)
      .filter(([, module]) => new RegExp(`from ['"]${forbidden}`).test(module.default))
      .map(([file]) => file)

    expect(
      offenders,
      `a file in core imports ${forbidden}. This package has to run behind an HTTP handler` +
        ' with no Electron and no React, which is what makes the later service a transport' +
        ' swap rather than a rewrite.',
    ).toEqual([])
  })
})

/**
 * RG98: the quiet way past the rule above.
 *
 * An import is the loud way in. RG65 found the other one: a rule about what a path *means*
 * needs no import at all. `left.replace(/\\/g, '/') === right.replace(/\\/g, '/')` is nine
 * tokens, has no dependency, typechecks under a config with no Node types, and would have
 * shipped the bug RG65 rejected — two different files on Linux reported as one, in the
 * branch that claims the declared engine was reached.
 *
 * **A backslash is not the tell; a separator fold is.** Scanning for a backslash finds
 * hundreds of them here and almost all are `\n`, a regex, or a Windows path a test states
 * on purpose — a gate that noisy is one somebody switches off. What is narrow enough to
 * hold is the shape: a quoted lone backslash, or a character class that contains one, in
 * code rather than in prose.
 *
 * **Two sites answer it today and both are named below.** Neither decides whether two paths
 * are the same file, which is the thing RG65 put on the other side of the seam. A third one
 * fails this, and so does an entry here that no longer matches — the exception list stays a
 * record of what is true rather than of what somebody once wrote down.
 */
const FOLDS_SEPARATORS = /['"`/]\\\\['"`/]|\[[^\]\n]{0,4}\\\\[^\]\n]{0,4}\]/

/**
 * Prose out, so what is left is what runs.
 *
 * Most backslashes in this package are in a docstring explaining one, and a gate that read
 * its own explanation would be the exception list the design warned about.
 */
function code(source: string): string {
  return source.replaceAll(/\/\*[\s\S]*?\*\//g, '').replaceAll(/(^|\s)\/\/.*$/gm, '$1')
}

/**
 * Where `core` folds a separator on purpose, and why each is not a path comparison.
 *
 * A test is not here and is not scanned: stating `D:\Git\app` is how a test says what a
 * Windows caller passes, and it is the fixture rather than the rule.
 */
const ANSWERED: Readonly<Record<string, string>> = {
  './acts.ts':
    '`governedIn` searches an agent`s tool-call text for a filename the project declared.' +
    ' A substring search over prose, so the worst a fold can do is label an act wrongly —' +
    ' it never decides that two paths are one file.',
  './portfolio.ts':
    'splitting a path into parts to derive the name shown for a project. It reads a path' +
    ' rather than comparing two, and a wrong answer is a label and not an identity.',
}

describe('RG98: what core is allowed to know about a path', () => {
  it('folds a separator only where somebody wrote down why', () => {
    const folding = Object.entries(sources)
      .filter(([file]) => !file.includes('.test.'))
      .filter(([, module]) => FOLDS_SEPARATORS.test(code(module.default)))
      .map(([file]) => file)

    expect(
      folding.filter((file) => !(file in ANSWERED)),
      'a file in core folds a path separator. RG65 put what a path means on the side of the' +
        ' seam that has a filesystem — so either hand the comparison in, or add the file to' +
        ' ANSWERED with why it is not deciding that two paths are the same file.',
    ).toEqual([])
  })

  it('keeps no answer to a question nobody is asking', () => {
    const gone = Object.keys(ANSWERED).filter(
      (file) => !FOLDS_SEPARATORS.test(code(sources[file]?.default ?? '')),
    )

    expect(
      gone,
      'this file no longer folds a separator, so its entry in ANSWERED is a note about code' +
        ' that has moved. Delete it: a list nobody removes from stops being read.',
    ).toEqual([])
  })

  it('is looking at something, which a clean list would not prove', () => {
    // The control. A pattern that matched nothing would pass the first assertion for the
    // wrong reason, and this repository has two real sites to find.
    expect(Object.keys(ANSWERED).length).toBeGreaterThan(0)
    for (const file of Object.keys(ANSWERED)) expect(sources[file]).toBeDefined()
  })
})
