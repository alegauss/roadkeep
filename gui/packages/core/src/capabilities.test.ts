import { describe, expect, it } from 'vitest'

import { CALLED_NAMES, flagsFor, publishedName, readCapabilities, withheld } from './capabilities'

/** Shaped like a real `commands --json` entry, trimmed to the keys this app reads. */
function command(name: string, flags: string[][], writes = false, runs = true) {
  return {
    command: name,
    family: 'reading',
    help: `what ${name} does`,
    writes,
    runs,
    // Deliberately false: twenty-three real verbs run without being on the MCP tool
    // surface, so a fixture that set this true everywhere would hide the distinction the
    // live contract test failed on.
    published: false,
    needs: '',
    arguments: flags.map((spelling) => ({
      spelling,
      primary: spelling[0],
      positional: false,
      takes: '',
      repeatable: false,
      required: false,
      help: '',
    })),
  }
}

/** A build that publishes everything this app calls, with every flag it sends. */
function completeBuild(version = '0.2.360'): string {
  return JSON.stringify({
    version,
    source: { home: '/engines/one' },
    commands: CALLED_NAMES.map((verb) =>
      command(
        // The name a real build publishes, which for a two-word verb is not its key.
        publishedName(verb),
        flagsFor(verb).map((flag) => [flag]),
      ),
    ),
  })
}

describe('RG69: a verb that is two words', () => {
  it('is looked up under the name commands publishes, not under its key', () => {
    // The failure this read exists to prevent, arriving through the read itself: looked
    // up by key, `nonGoalList` is a name no build ever printed, so it reports as one this
    // engine cannot run and its door is withheld.
    expect(publishedName('nonGoalList')).toBe('non-goal list')
    expect(publishedName('criterionList')).toBe('criterion list')

    const report = readCapabilities(completeBuild(), '0.2.360')

    expect(report.kind === 'known' && report.complete).toBe(true)
    if (report.kind !== 'known') throw new Error('unreachable')
    expect(report.byVerb.nonGoalList.callable).toBe(true)
    expect(report.byVerb.criterionList.callable).toBe(true)
  })

  it('is spelled by its own key where the key is the whole name', () => {
    expect(publishedName('list')).toBe('list')
    expect(publishedName('add')).toBe('add')
  })

  it('withholds a two-word verb this build does not publish, by that name', () => {
    const build = JSON.stringify({
      version: '0.2.360',
      source: {},
      commands: CALLED_NAMES.filter((verb) => verb !== 'nonGoalList').map((verb) =>
        command(
          publishedName(verb),
          flagsFor(verb).map((flag) => [flag]),
        ),
      ),
    })

    const report = readCapabilities(build, '0.2.360')

    expect(report.kind === 'known' && report.complete).toBe(false)
    expect(withheld(report).join(' ')).toContain('nonGoalList')
  })
})

describe('RG6: the flags this app would send', () => {
  it('derives them by running the builder, so they cannot drift from it', () => {
    // `--marker` is only ever emitted by `list`'s builder. A list maintained beside the
    // builders would keep approving it after somebody removed it.
    expect(flagsFor('list')).toContain('--marker')
    expect(flagsFor('list')).toContain('--block')
    expect(flagsFor('show')).not.toContain('--block')
  })

  it('includes --json, which the client appends to every call', () => {
    for (const verb of CALLED_NAMES) {
      expect(flagsFor(verb)).toContain('--json')
    }
  })

  it('lists nothing twice for a repeatable flag', () => {
    const flags = flagsFor('brief')
    expect(flags.length).toBe(new Set(flags).size)
  })
})

describe('RG6: what a build can do', () => {
  it('reports a complete build as complete, with its own version', () => {
    const report = readCapabilities(completeBuild('0.2.360'), '0.2.360')

    expect(report.kind).toBe('known')
    if (report.kind !== 'known') return
    expect(report.version).toBe('0.2.360')
    expect(report.complete).toBe(true)
    expect(withheld(report)).toEqual([])
  })

  it('withholds a verb this build does not carry at all', () => {
    const payload = JSON.parse(completeBuild()) as { commands: { command: string }[] }
    const build = JSON.stringify({
      ...payload,
      commands: payload.commands.filter((entry) => entry.command !== 'explain'),
    })

    const report = readCapabilities(build, '0.2.100')

    expect(report.kind).toBe('known')
    if (report.kind !== 'known') return
    expect(report.byVerb.explain.callable).toBe(false)
    expect(report.complete).toBe(false)
    expect(withheld(report)).toContain('explain: this build cannot run it')
  })

  it('offers a verb that runs but is not on the MCP tool surface', () => {
    // `stats`, `commands`, `init`, `section` and eighteen others are exactly this. Gating
    // a door on `published` would withhold a third of the verbs that work perfectly well.
    const report = readCapabilities(completeBuild(), '0.2.360')

    expect(report.kind).toBe('known')
    if (report.kind !== 'known') return
    expect(report.byVerb.stats.onToolSurface).toBe(false)
    expect(report.byVerb.stats.callable).toBe(true)
    expect(withheld(report)).toEqual([])
  })

  it('withholds a verb this build carries but cannot run', () => {
    const build = JSON.stringify({
      version: '0.2.360',
      source: null,
      commands: CALLED_NAMES.map((verb) =>
        command(
          verb,
          flagsFor(verb).map((flag) => [flag]),
          false,
          verb !== 'lint',
        ),
      ),
    })

    const report = readCapabilities(build, '0.2.360')
    expect(report.kind === 'known' && report.byVerb.lint.callable).toBe(false)
    expect(withheld(report)).toContain('lint: this build cannot run it')
  })

  it('names the flag an older build does not take', () => {
    // The failure this read exists to prevent: without it, the first sign is a refusal
    // arriving after somebody filled in a form.
    const build = JSON.stringify({
      version: '0.1.0',
      source: null,
      commands: CALLED_NAMES.map((verb) =>
        command(
          verb,
          flagsFor(verb)
            .filter((flag) => flag !== '--have')
            .map((flag) => [flag]),
        ),
      ),
    })

    const report = readCapabilities(build, '0.1.0')

    expect(report.kind).toBe('known')
    if (report.kind !== 'known') return
    expect(report.byVerb.list.missingFlags).toEqual(['--have'])
    expect(withheld(report)).toContain('list: this build does not take --have')
  })

  it('accepts a flag under any of its spellings', () => {
    // `--marker` and `--status` are one argument. A check that only compared the primary
    // would report a flag missing that the build takes perfectly well.
    const build = JSON.stringify({
      version: '0.2.360',
      source: null,
      commands: CALLED_NAMES.map((verb) => command(publishedName(verb), [flagsFor(verb)])),
    })

    const report = readCapabilities(build, '0.2.360')
    expect(report.kind === 'known' && report.complete).toBe(true)
  })
})

describe('RG6: a build too old to answer at all', () => {
  it('is unsupported with its version, which is a state and not a failure', () => {
    const report = readCapabilities('roadkeep: unrecognised command `commands`', '0.1.0')

    expect(report.kind).toBe('unsupported')
    if (report.kind !== 'unsupported') return
    // The version comes from `engines`, which older builds do answer.
    expect(report.version).toBe('0.1.0')
    expect(report.reason).toContain('not a payload')
    expect(withheld(report)[0]).toContain('roadkeep 0.1.0')
  })

  it('is unsupported when the payload is there but the shape is not', () => {
    const report = readCapabilities('{"version":"0.1.0"}', '0.1.0')

    expect(report.kind).toBe('unsupported')
    if (report.kind !== 'unsupported') return
    expect(report.reason).toContain('commands')
  })

  it('still names a version it was never told', () => {
    const report = readCapabilities('not json', '')
    expect(report.kind === 'unsupported' && withheld(report)[0]).toContain('unknown version')
  })
})
