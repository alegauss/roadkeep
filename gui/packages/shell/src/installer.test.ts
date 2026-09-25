import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

/**
 * RK1700: the Windows installer places the app and then offers the Claude Code plugin.
 *
 * What electron-builder does with the macro is only proven by building an installer, which
 * this suite does not do; what it can hold is the promises the macro makes, each of which
 * fails silently. A macro nobody includes is an installer that never asks. One that runs
 * unasked turns a silent install into a network call nobody watching requested. One that
 * aborts on a failed command takes the app down with the plugin.
 */

const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const CONFIG = readFileSync(path.join(REPO, 'electron-builder.yml'), 'utf8')

function included(): string {
  const found = /^\s+include:\s*(\S+)\s*$/m.exec(CONFIG.slice(CONFIG.indexOf('\nnsis:')))
  return found?.[1] ?? ''
}

describe('RK1700: the plugin step the Windows installer runs', () => {
  it('is included by the NSIS target, from a file that is there', () => {
    const script = included()
    expect(script, 'nsis.include names no script').not.toBe('')
    expect(existsSync(path.join(REPO, script))).toBe(true)
  })

  const macro = readFileSync(path.join(REPO, included() || 'build/installer.nsh'), 'utf8')

  it('runs the two commands a person otherwise types, through the claude CLI', () => {
    expect(macro).toMatch(/!macro customInstall/)
    expect(macro).toContain('claude plugin marketplace add alegauss/roadkeep')
    expect(macro).toContain('claude plugin install roadkeep@alegauss')
  })

  it('asks first, and a silent install skips the step', () => {
    expect(macro).toMatch(/IfSilent roadkeep_plugin_done/)
    expect(macro).toMatch(/MessageBox MB_YESNO/)
    // Only where the CLI answers: offering a command that cannot run is a question with one
    // answer, and that answer is an error dialog.
    expect(macro).toMatch(/where claude/)
  })

  it('RK1701: checks Python 3.11 before offering, and names what is missing', () => {
    // The plugin's server is `python scripts/roadkeep.py mcp`, so a plugin installed without
    // one fails on its first call, far from the cause.
    expect(macro).toContain('sys.version_info >= (3, 11)')
    expect(macro.indexOf('sys.version_info')).toBeLessThan(macro.indexOf('MB_YESNO'))
    expect(macro).toContain('https://www.python.org/downloads/')
    expect(macro).toContain('https://docs.claude.com/en/docs/claude-code/setup')
  })

  it('never aborts the install over the plugin', () => {
    expect(macro).not.toMatch(/^\s*Abort\b/m)
    expect(macro).not.toMatch(/^\s*Quit\b/m)
  })
})
