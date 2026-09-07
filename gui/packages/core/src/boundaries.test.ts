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
