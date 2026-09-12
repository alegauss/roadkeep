import { describe, expect, it } from 'vitest'

import { bashFor } from './git-bash'

/**
 * RG218: the bash a workflow step runs under, on a machine where WSL's comes first.
 */

const WINDOWS_APPS = 'C:\\Users\\a\\AppData\\Local\\Microsoft\\WindowsApps'
const GIT_CMD = 'C:\\Program Files\\Git\\cmd'

function machine(...files: string[]) {
  const held = new Set(files.map((file) => file.toLowerCase()))
  return (file: string) => held.has(file.toLowerCase())
}

describe('RG218: Git bash, found beside git', () => {
  it("takes Git's bash even where WSL's bash.exe is earlier on PATH", () => {
    const exists = machine(
      `${WINDOWS_APPS}\\bash.exe`,
      `${GIT_CMD}\\git.exe`,
      'C:\\Program Files\\Git\\bin\\bash.exe',
    )

    expect(bashFor('win32', `${WINDOWS_APPS};${GIT_CMD}`, exists)).toEqual({
      kind: 'found',
      command: 'C:\\Program Files\\Git\\bin\\bash.exe',
    })
  })

  it('finds it from the mingw64 directory a Git shell puts on PATH', () => {
    const exists = machine(
      'C:\\Program Files\\Git\\mingw64\\bin\\git.exe',
      'C:\\Program Files\\Git\\bin\\bash.exe',
    )

    expect(bashFor('win32', 'C:\\Program Files\\Git\\mingw64\\bin', exists)).toEqual({
      kind: 'found',
      command: 'C:\\Program Files\\Git\\bin\\bash.exe',
    })
  })

  it('says what it looked for where there is no Git bash, rather than running WSL', () => {
    const nothing = bashFor('win32', WINDOWS_APPS, machine(`${WINDOWS_APPS}\\bash.exe`))
    expect(nothing.kind).toBe('missing')
    expect(nothing.kind === 'missing' && nothing.said).toMatch(/no directory on PATH holds git/)

    const noBash = bashFor('win32', GIT_CMD, machine(`${GIT_CMD}\\git.exe`))
    expect(noBash.kind === 'missing' && noBash.said).toContain(
      'C:\\Program Files\\Git\\bin\\bash.exe',
    )
  })

  it('leaves bash on PATH alone anywhere but Windows', () => {
    expect(bashFor('linux', '/usr/bin', machine())).toEqual({ kind: 'found', command: 'bash' })
    expect(bashFor('darwin', '/bin', machine())).toEqual({ kind: 'found', command: 'bash' })
  })
})
