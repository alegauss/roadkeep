import { describe, expect, it } from 'vitest'

import { GLOSS_TOOLS, isGitRead, permitsGitRead, WALKTHROUGH_TOOLS } from './gloss-process'

/**
 * RG291: the one shell call a walkthrough may make.
 *
 * The bound is here and not in the tool list, and that is the whole of what these hold: a
 * `Bash(git show:*)` entry in `allowedTools` grants the entire shell, which a captured run
 * proved by reaching for `ls`, `python` and `grep` under it. So the list grants no `Bash` at
 * all and every shell call arrives at this gate instead.
 */

describe('RG291: what a walkthrough may run', () => {
  it('allows the read it is for', () => {
    expect(isGitRead('git show 216066b')).toBe(true)
    expect(isGitRead('git show 216066b --stat')).toBe(true)
    expect(isGitRead('git show 216066b -- packages/core/src/verbs.ts')).toBe(true)
    expect(isGitRead('git show 216066b:package.json')).toBe(true)
    // Leading space is somebody's spacing and not a second command.
    expect(isGitRead('  git show 216066b  ')).toBe(true)
  })

  it('refuses another command chained or redirected onto the end of it', () => {
    // The whole reason a prefix check is not enough: every one of these starts with the read.
    expect(isGitRead('git show 216066b && rm -rf .')).toBe(false)
    expect(isGitRead('git show 216066b; git push')).toBe(false)
    expect(isGitRead('git show 216066b | tee out.txt')).toBe(false)
    expect(isGitRead('git show 216066b > out.txt')).toBe(false)
    expect(isGitRead('git show 216066b `git commit -am x`')).toBe(false)
    expect(isGitRead('git show 216066b $(git push)')).toBe(false)
    expect(isGitRead('git show 216066b\ngit push')).toBe(false)
  })

  it('refuses every other git command, reads included', () => {
    // One read and not a family: `git log` and `git diff` are reads too, and a gate that let
    // them in would be a gate deciding which git commands are safe rather than naming the one.
    expect(isGitRead('git log')).toBe(false)
    expect(isGitRead('git diff HEAD')).toBe(false)
    expect(isGitRead('git commit -am x')).toBe(false)
    expect(isGitRead('git showman')).toBe(false)
    // Bare, with nothing to show: not the call, and not a prefix of one either.
    expect(isGitRead('git show')).toBe(false)
  })

  it('answers for Bash alone, and defers every other tool to the list', () => {
    expect(permitsGitRead('Bash', { command: 'git show 216066b' })).toBe('allow')
    expect(permitsGitRead('Bash', { command: 'ls' })).toBe('deny')
    expect(permitsGitRead('Bash', {})).toBe('deny')
    expect(permitsGitRead('Bash', { command: 42 })).toBe('deny')
    // Deferred and not denied, which is what the first gate here got wrong: it answered for
    // `StructuredOutput` too, and the run came back with no answer at all.
    expect(permitsGitRead('Read', { file_path: 'a.ts' })).toBe('defer')
    expect(permitsGitRead('StructuredOutput', {})).toBe('defer')
    expect(permitsGitRead('Write', { command: 'git show 216066b' })).toBe('defer')
  })

  it('grants no shell in the list a walkthrough is given', () => {
    // The failure this file exists to hold: a `Bash` entry here is a whole shell, whatever
    // specifier follows it.
    expect(WALKTHROUGH_TOOLS).toEqual(GLOSS_TOOLS)
    expect(WALKTHROUGH_TOOLS.some((tool) => tool.startsWith('Bash'))).toBe(false)
  })
})
