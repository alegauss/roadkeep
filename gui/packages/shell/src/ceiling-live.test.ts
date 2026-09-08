import { availableParallelism, tmpdir } from 'node:os'

import { attemptRead, createPooledTransport, readListPayload, withLimits } from '@rk/core'
import { describe, expect, it } from 'vitest'

import { machineWidth } from './machine'
import { createProcessTransport } from './process-transport'

/**
 * RG8 against real processes. The pool and the deadline are only worth anything if they
 * hold when the thing on the other end is an actual program that will not come back — so
 * the engine here is Node told to sleep for half a minute.
 */
const node = createProcessTransport({ command: process.execPath })

const hangs = (root = tmpdir()) => ({
  root,
  argv: ['-e', 'setTimeout(() => {}, 30000)'],
  timeoutMs: 400,
})

describe('RG8: a project whose engine never comes back', () => {
  it('becomes an unreadable state rather than a call that never settles', async () => {
    const read = await attemptRead(node, hangs(), readListPayload)

    expect(read.ok).toBe(false)
    if (read.ok) return
    expect(read.unreadable.reason).toBe('timeout')
    expect(read.unreadable.elapsedMs).toBeGreaterThanOrEqual(300)
    expect(read.unreadable.argv).toContain('-e')
  })

  it('does not stop the projects beside it', async () => {
    const pool = createPooledTransport(node, { width: 2 })
    const working = {
      root: tmpdir(),
      argv: [
        '-e',
        'process.stdout.write(JSON.stringify({file:"docs/ROADMAP.md",total:0,uncounted:[],standing:null,startable:null,over:null,tasks:[]}))',
      ],
      timeoutMs: 20000,
    }

    const [broken, fine] = await Promise.all([
      attemptRead(pool, { ...hangs(), timeoutMs: 400 }, readListPayload),
      attemptRead(pool, working, readListPayload),
    ])

    // Nineteen of twenty projects still drawing is the whole point of the state.
    expect(broken.ok).toBe(false)
    expect(fine.ok).toBe(true)
  })
})

describe('RG8: the width this machine should use', () => {
  it('is derived from the machine and stays inside the clamp', () => {
    const width = machineWidth()

    expect(width).toBeGreaterThanOrEqual(1)
    expect(width).toBeLessThanOrEqual(32)
    expect(withLimits({ width }).width).toBe(width)
  })

  it('never asks for more than the machine has cores', () => {
    // A laptop with four cores running twenty Pythons is not fast, it is unresponsive.
    expect(machineWidth()).toBeLessThanOrEqual(availableParallelism())
  })
})
