import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { samePathPart } from './engine-candidates'

/**
 * RG65: the comparison handed to `resolveEngine`, which `core` cannot make for itself.
 *
 * Nothing here starts a process — this is the pure half of a rule that only a platform can
 * state, so it belongs in the fast suite beside `root-paths`.
 */

const WINDOWS = process.platform === 'win32'

describe('RG65: two spellings of one command line part', () => {
  it('sees an identical part as identical everywhere', () => {
    expect(samePathPart('python', 'python')).toBe(true)
    expect(samePathPart('/a/b/launch.py', '/a/b/launch.py')).toBe(true)
  })

  it('does not confuse two different commands', () => {
    expect(samePathPart('python', 'python3')).toBe(false)
    expect(samePathPart('roadkeep', 'rk')).toBe(false)
    expect(samePathPart('/a/b/launch.py', '/a/c/launch.py')).toBe(false)
  })

  it('does not read an empty part as any part at all', () => {
    // `path.normalize('')` is `.`, which would make a blank equal to a directory.
    expect(samePathPart('', '.')).toBe(false)
    expect(samePathPart('', '')).toBe(true)
  })

  it('leaves a bare name a name rather than resolving it somewhere', () => {
    // `roadkeep` is a PATH lookup and not a file in whatever directory this process is in,
    // so it must never compare equal to that directory's `roadkeep`.
    expect(samePathPart('roadkeep', path.resolve('roadkeep'))).toBe(false)
  })

  it('collapses the detour a path took to get there', () => {
    expect(samePathPart(path.join('a', 'b', '..', 'launch.py'), path.join('a', 'launch.py'))).toBe(
      true,
    )
  })

  it.runIf(WINDOWS)('reads the posix spelling of a Windows path as the same file', () => {
    // The whole of RG65: `invoke` says one, the candidate holds the other, and a literal
    // comparison started a second interpreter on every resolution to find out.
    expect(
      samePathPart(
        'D:/proj/.claude/hooks/roadkeep-launch.py',
        'D:\\proj\\.claude\\hooks\\roadkeep-launch.py',
      ),
    ).toBe(true)
    expect(samePathPart('D:\\Proj\\Launch.py', 'd:\\proj\\launch.py')).toBe(true)
  })

  it.runIf(!WINDOWS && process.platform !== 'darwin')(
    'keeps a backslash an ordinary character where it is one',
    () => {
      // Folding separators here would report two different files as one, and resolution
      // would then claim to have reached a copy it never ran.
      expect(samePathPart('/proj/a\\b.py', '/proj/a/b.py')).toBe(false)
      expect(samePathPart('/proj/Launch.py', '/proj/launch.py')).toBe(false)
    },
  )
})
