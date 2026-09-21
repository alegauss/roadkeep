import { mkdtempSync, readdirSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { GLOSS_SCHEMA, hasGloss, lanesOf, readGloss, type BriefPayload } from '@rk/core'
import { afterAll, describe, expect, it } from 'vitest'

import { askGloss, GLOSS_TOOLS } from './gloss-process'
import { removeTree } from './scratch'
import { scriptedAgent } from './scripted-agent'

/**
 * RG284: one read-only query, run for real.
 *
 * `captured/gloss-stream.jsonl` is what a real gloss run wrote, kept as it came back but for the
 * handshake the replay answers itself, the token accounting, the thinking, and what each read
 * returned — this repository's own source, cut to its first lines since the run's reads are what
 * is held here and not the files. The scripted agent replays it to
 * its end — a read answers once and exits, where a session's replay stays up — so what is held
 * here is the whole path: the SDK spawns the agent, reads its lines, and the `structured_output`
 * on the result comes back as a gloss.
 */

const CAPTURED = path.join(import.meta.dirname, 'captured', 'gloss-stream.jsonl')

const scratch: string[] = []

function where(): string {
  const made = mkdtempSync(path.join(tmpdir(), 'rk-gloss-run-'))
  scratch.push(made)
  return made
}

afterAll(() => {
  for (const one of scratch) removeTree(one)
})

/** The line the captured run was asked about, as much of it as reading the answer needs. */
const BRIEF = {
  id: 'RG282',
  deps: ['RG280'],
  depsResolved: [{ dep: 'RG280', kind: 'task', status: 'shipped', detail: 'in the changelog' }],
  unblocks: { count: 1, of: 7, direct: ['RG285'], transitive: ['RG285'], transitiveElided: 0 },
  nonGoals: ['No Markdown parsed in this app', 'No write to a governed file'],
} as unknown as BriefPayload

describe('RG284: a gloss run to its end', () => {
  it('answers with the structured output the run wrote, and the model that wrote it', async () => {
    const agent = scriptedAgent({ stream: CAPTURED, ends: true, intervalMs: 1 })
    const root = where()
    try {
      const said = await askGloss({
        command: agent.command[0] ?? '',
        prefix: agent.command.slice(1),
        cwd: root,
        prompt: 'what does this line mean',
        schema: GLOSS_SCHEMA,
      }).answered

      expect(said.kind).toBe('said')
      if (said.kind !== 'said') throw new Error(said.kind)
      // Named by the run's own `init` line, which is what a screen says answered.
      expect(said.model).not.toBe('')
      expect(said.version).not.toBe('')

      const gloss = readGloss(said.structured, BRIEF)
      expect(hasGloss(gloss)).toBe(true)
      expect(gloss.headline).not.toBe('')
      expect(Object.keys(gloss.deps)).toEqual(['RG280'])
    } finally {
      agent.dispose()
    }
  }, 30000)

  it('writes nothing into the project it ran in, having no tool to write with', async () => {
    const agent = scriptedAgent({ stream: CAPTURED, ends: true, intervalMs: 1 })
    const root = where()
    try {
      await askGloss({
        command: agent.command[0] ?? '',
        prefix: agent.command.slice(1),
        cwd: root,
        prompt: 'what does this line mean',
        schema: GLOSS_SCHEMA,
      }).answered

      expect(readdirSync(root)).toEqual([])
    } finally {
      agent.dispose()
    }
  }, 30000)

  it('answers cancelled and leaves no process behind when the reader gives up', async () => {
    // Slow enough that the run is still going when it is given up on.
    const agent = scriptedAgent({ stream: CAPTURED, ends: true, intervalMs: 400 })
    const root = where()
    try {
      const run = askGloss({
        command: agent.command[0] ?? '',
        prefix: agent.command.slice(1),
        cwd: root,
        prompt: 'what does this line mean',
        schema: GLOSS_SCHEMA,
      })
      await new Promise((settle) => setTimeout(settle, 500))
      run.cancel()

      expect((await run.answered).kind).toBe('cancelled')
    } finally {
      agent.dispose()
    }
  }, 30000)

  it('says the machine has none where nothing answers as Claude Code', async () => {
    const said = await askGloss({
      command: path.join(tmpdir(), 'rk-no-claude-here'),
      prefix: [],
      cwd: where(),
      prompt: 'what does this line mean',
      schema: GLOSS_SCHEMA,
    }).answered

    expect(said.kind).toBe('unavailable')
  }, 30000)

  it('keeps the fixture a real run wrote, result and all', () => {
    const lines = readFileSync(CAPTURED, 'utf8')
      .split('\n')
      .filter((line) => line.trim() !== '')
      .map((line): unknown => JSON.parse(line))

    expect(lines.length).toBeGreaterThan(3)
    // The two lines this reads: what named the run, and what it answered.
    expect(lines.some((line) => (line as { subtype?: string }).subtype === 'init')).toBe(true)
    expect(
      lines.some(
        (line) => (line as { structured_output?: unknown }).structured_output !== undefined,
      ),
    ).toBe(true)
  })
})

describe('RG288: a run that reads the files the design names', () => {
  it('tells the caller each read as it passes, and answers where the work lands', async () => {
    const agent = scriptedAgent({ stream: CAPTURED, ends: true, intervalMs: 1 })
    const root = where()
    const reads: [string, string][] = []
    try {
      const said = await askGloss({
        command: agent.command[0] ?? '',
        prefix: agent.command.slice(1),
        cwd: root,
        prompt: 'what does this line mean',
        schema: GLOSS_SCHEMA,
        reading: (tool, on) => {
          reads.push([tool, on])
        },
      }).answered

      if (said.kind !== 'said') throw new Error(said.kind)
      // The captured run read this repository: at least one file, by name, before it answered.
      expect(reads.some(([tool]) => tool === 'Read')).toBe(true)
      expect(reads.every(([, on]) => on !== '')).toBe(true)

      const gloss = readGloss(said.structured, BRIEF)
      expect(gloss.where.length).toBeGreaterThan(0)
      expect(gloss.where.every((place) => place.path !== '' && place.said !== '')).toBe(true)
      // And the lanes the screen draws are the folders of the paths it named.
      expect(lanesOf(gloss.where).length).toBeGreaterThan(0)
    } finally {
      agent.dispose()
    }
  }, 30000)

  it('is given three tools and all of them read', () => {
    expect(GLOSS_TOOLS).toEqual(['Read', 'Grep', 'Glob'])
  })
})
