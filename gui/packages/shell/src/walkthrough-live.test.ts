import { mkdtempSync, readdirSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import {
  hasWalkthrough,
  promptForWalkthrough,
  readWalkthrough,
  WALKTHROUGH_SCHEMA,
  type OriginPayload,
} from '@rk/core'
import { afterAll, describe, expect, it } from 'vitest'

import { askQuestion, isGitRead, permitsGitRead, WALKTHROUGH_TOOLS } from './question'
import { read } from './live'
import { removeTree } from './scratch'
import { scriptedAgent } from './scripted-agent'

/**
 * RG291: how to check a shipped entry, asked of the commit that wrote it.
 *
 * Two captures, because the whole question is whether the run can tell them apart. Both were
 * real runs over real commits of this repository, kept as they came back but for the handshake
 * the replay answers itself, the thinking, the token accounting and what each read returned —
 * cut to its first lines, since the shape of the run is what is held here and not the diffs.
 *
 * `walkthrough-steps` is RG286, a screen change: a person can open the dialog and look, so the
 * answer is steps. `walkthrough-nothing` is RG289, two rows in a verb table: nothing is drawn,
 * nobody can open it, and the answer is `nothingToSee` with `steps` empty. An agent with no way
 * to say the second invents a procedure for it, which is the failure this slot exists to refuse.
 */

const STEPS = path.join(import.meta.dirname, 'captured', 'walkthrough-steps.jsonl')
const NOTHING = path.join(import.meta.dirname, 'captured', 'walkthrough-nothing.jsonl')
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')

const scratch: string[] = []

function where(): string {
  const made = mkdtempSync(path.join(tmpdir(), 'rk-walkthrough-'))
  scratch.push(made)
  return made
}

afterAll(() => {
  for (const one of scratch) removeTree(one)
})

/** Replay one capture to its end and read what it answered. */
async function replay(stream: string) {
  const agent = scriptedAgent({ stream, ends: true, intervalMs: 1 })
  const root = where()
  try {
    const said = await askQuestion({
      command: agent.command[0] ?? '',
      prefix: agent.command.slice(1),
      cwd: root,
      prompt: 'how would somebody check this',
      schema: WALKTHROUGH_SCHEMA,
      tools: WALKTHROUGH_TOOLS,
      permits: permitsGitRead,
    }).answered

    expect(said.kind, JSON.stringify(said)).toBe('said')
    if (said.kind !== 'said') throw new Error(said.kind)
    return { said, root, files: readdirSync(root) }
  } finally {
    agent.dispose()
  }
}

describe('RG291: a walkthrough over a real shipped commit', () => {
  it('answers steps a person can follow, each with what it should produce', async () => {
    const { said, files } = await replay(STEPS)
    const walkthrough = readWalkthrough(said.structured)

    expect(hasWalkthrough(walkthrough)).toBe(true)
    // A change somebody can open: steps, and no reason why they cannot.
    expect(walkthrough.nothingToSee).toBe('')
    expect(walkthrough.steps.length).toBeGreaterThan(0)
    expect(walkthrough.before.length).toBeGreaterThan(0)
    // Every step is a pair, which is what makes one checkable — a `does` alone is an
    // instruction nobody can tell the outcome of, and the reader drops it.
    for (const step of walkthrough.steps) {
      expect(step.does).not.toBe('')
      expect(step.sees).not.toBe('')
    }
    // Where the change landed, the gloss's own slot read by the gloss's own reader.
    expect(walkthrough.where.length).toBeGreaterThan(0)
    expect(walkthrough.where[0]?.path).not.toBe('')
    // Nothing was written into the project it ran in: every tool it had is a read.
    expect(files).toEqual([])
  }, 60000)

  it('says there is nothing to see where nobody can open the change, and invents no steps', async () => {
    const { said } = await replay(NOTHING)
    const walkthrough = readWalkthrough(said.structured)

    expect(hasWalkthrough(walkthrough)).toBe(true)
    expect(walkthrough.nothingToSee).not.toBe('')
    // The half that matters: a run that had to answer *something* would have written four
    // invented clicks here, and a person would have followed them.
    expect(walkthrough.steps).toEqual([])
  }, 60000)

  it('read the diff through git, and reached for a shell it was refused', () => {
    // The bound, held against what the runs actually did rather than against the list they were
    // given. The first attempt at this put `Bash(git show:*)` in `allowedTools` and the run came
    // back having called `ls`, `python` and `grep`: a specifier there grants the whole shell. So
    // the bound is `permits`, and the capture below is the proof — a `git show` that ran, and a
    // `vitest` the gate turned away.
    const shell = shellCalls(STEPS)

    expect(shell.filter((one) => isGitRead(one.command)).length).toBeGreaterThan(0)
    for (const call of shell) {
      expect(isGitRead(call.command) || call.refused, `${call.command} ran unbounded`).toBe(true)
    }
    // And the one that was not a git read was turned away, so this holds a refusal and not an
    // absence: a capture where the run never tried anything else proves nothing about the gate.
    expect(shell.some((one) => !isGitRead(one.command) && one.refused)).toBe(true)

    for (const call of shellCalls(NOTHING)) {
      expect(isGitRead(call.command) || call.refused).toBe(true)
    }
  })
})

/** Every shell call a capture made, with whether it came back refused. */
function shellCalls(capture: string): { command: string; refused: boolean }[] {
  const lines = readFileSync(capture, 'utf8').trim().split('\n')
  const blocks = lines.flatMap(
    (line): { type?: string; name?: string; [key: string]: unknown }[] => {
      const message = JSON.parse(line) as { message?: { content?: unknown } }
      return Array.isArray(message.message?.content) ? message.message.content : []
    },
  )
  const refused = new Set(
    blocks
      .filter((one) => one.type === 'tool_result' && one['is_error'] === true)
      .map((one) => String(one['tool_use_id'])),
  )
  return blocks
    .filter((one) => one.type === 'tool_use' && one.name === 'Bash')
    .map((one) => {
      const asked = (one['input'] as { command?: unknown } | undefined)?.command
      return {
        command: typeof asked === 'string' ? asked : '',
        refused: refused.has(String(one['id'])),
      }
    })
}

describe('RG291: the commit the run is anchored on', () => {
  it('reads origin for a shipped entry live, which is where the prompt gets its evidence', async () => {
    // This repository and not a fixture: a fixture in a temp directory has no history, and the
    // whole of this read is a history. The entry is this file's own capture subject.
    const payload: OriginPayload = await read(REPO, 'origin', { id: 'RG286' })

    expect(payload.id).toBe('RG286')
    expect(payload.shippedIn?.sha).toMatch(/^[0-9a-f]{40}$/)
    expect(payload.shippedIn?.short).not.toBe('')
    expect(payload.shippedIn?.subject).toContain('RG286')
    // The whole message, which is what `--why` prints — and the reason this app never sends
    // that flag: the payload already carries it, and the verb refuses the two together.
    expect(payload.shippedIn?.reasoning).toContain('RG286')
    expect(payload.proposedIn?.sha).toMatch(/^[0-9a-f]{40}$/)

    // And the prompt is built from it: the sha the agent is told to read is the one that shipped.
    const prompt = promptForWalkthrough(payload, 'The explanation is drawn as shapes.', 'en')
    expect(prompt).toContain(`git show ${payload.shippedIn?.sha ?? ''}`)
    expect(prompt).toContain('The explanation is drawn as shapes.')
  }, 30000)
})
