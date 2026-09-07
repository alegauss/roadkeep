import { describe, expect, it } from 'vitest'

import { readEnginesPayload, splitCommandLine } from './engines'

const REAL = JSON.stringify({
  writing: {
    version: '0.2.356',
    home: 'D:/Git/alegauss/roadkeep/src/roadkeep',
    revision: '2404ae02',
    on_disk: '0.2.356',
  },
  plugin: null,
  vendored: null,
  gates: [],
  driver: '',
  declaration: 'python D:/proj/.claude/hooks/roadkeep-launch.py mcp',
  readable: true,
  invoke: 'python D:/proj/.claude/hooks/roadkeep-launch.py',
  agree: true,
  verdict: 'agreed',
  split: false,
  swapped: false,
})

describe('RG2: reading what engines answered', () => {
  it('takes the fields this app uses out of a real payload', () => {
    const payload = readEnginesPayload(REAL)

    expect(payload?.writing.version).toBe('0.2.356')
    expect(payload?.writing.onDisk).toBe('0.2.356')
    expect(payload?.verdict).toBe('agreed')
    expect(payload?.agree).toBe(true)
    expect(payload?.invoke).toBe('python D:/proj/.claude/hooks/roadkeep-launch.py')
  })

  it.each([
    ['not JSON at all', 'roadkeep: command not found'],
    ['JSON that is not an object', '["engines"]'],
    ['an object with no writing', '{"invoke":"roadkeep"}'],
    ['a writing with no version', '{"writing":{"home":"/x"}}'],
    ['nothing', ''],
  ])('answers null for %s, because a candidate may not be roadkeep', (_case, stdout) => {
    // The first call is made against something that might be any program on the machine.
    // "did not answer with an engines payload" has to be a value, not an exception.
    expect(readEnginesPayload(stdout)).toBeNull()
  })

  it('treats a missing flag as false rather than as unknown', () => {
    const payload = readEnginesPayload('{"writing":{"version":"1.0"}}')

    expect(payload?.agree).toBe(false)
    expect(payload?.readable).toBe(false)
    expect(payload?.verdict).toBe('')
  })
})

describe('RG2: turning a command line into argv', () => {
  it('splits on whitespace', () => {
    expect(splitCommandLine('python /a/launcher.py')).toEqual(['python', '/a/launcher.py'])
  })

  it('keeps a backslash, because on Windows it is a path and not an escape', () => {
    // A splitter that consumed backslashes turns this into C:UsersaAppDataroadkeep.exe
    // and then reports an engine that could not be started.
    expect(splitCommandLine('C:\\Users\\a\\AppData\\roadkeep.exe')).toEqual([
      'C:\\Users\\a\\AppData\\roadkeep.exe',
    ])
  })

  it('groups a quoted path with spaces into one argument', () => {
    expect(splitCommandLine('python "C:\\Program Files\\rk\\launch.py"')).toEqual([
      'python',
      'C:\\Program Files\\rk\\launch.py',
    ])
    expect(splitCommandLine("python 'C:\\Program Files\\rk\\launch.py'")).toEqual([
      'python',
      'C:\\Program Files\\rk\\launch.py',
    ])
  })

  it('collapses runs of whitespace instead of emitting empty arguments', () => {
    expect(splitCommandLine('  python   /a/b.py  ')).toEqual(['python', '/a/b.py'])
  })

  it('answers nothing for an empty line', () => {
    expect(splitCommandLine('   ')).toEqual([])
  })

  it('refuses an unterminated quote rather than guessing', () => {
    // The one case where a best guess reaches a different copy of roadkeep, which is the
    // whole failure this file exists to prevent.
    expect(splitCommandLine('python "C:\\Program Files\\rk')).toBeNull()
  })

  it('keeps an empty quoted argument, which is not the same as no argument', () => {
    expect(splitCommandLine('rk ""')).toEqual(['rk', ''])
  })
})
