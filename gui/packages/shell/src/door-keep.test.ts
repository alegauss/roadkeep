import { describe, expect, it } from 'vitest'

import { createDoorKeep } from './door-keep'

/**
 * RG165: what the side that received a door keeps, and when it stops holding it.
 *
 * The stamp is a function here, so what this holds is the rule and not the filesystem: a name
 * belongs to one project, it is worth nothing once that project's files have moved, and a name
 * nobody offered names nothing.
 */

const ANSWER = {
  doors: [
    { argv: ['criterion', 'add', '--task', 'RG9', '--lead', '<lead>'], complete: false },
    { argv: ['engines'], complete: true },
  ],
}

function keeping(stamps: string[] = ['one']) {
  let at = 0
  let names = 0
  const keep = createDoorKeep({
    stampOf: () => Promise.resolve(stamps[Math.min(at++, stamps.length - 1)] ?? ''),
    name: () => `token-${String((names += 1))}`,
  })
  return keep
}

describe('RG165: the doors an answer carried', () => {
  it('keeps them under a name, and hands back the one a caller points at', async () => {
    const keep = keeping()

    const token = await keep.keep('/proj', ANSWER)
    expect(token).toBe('token-1')
    if (token === null) throw new Error('unreachable')

    expect((await keep.taken('/proj', token, 0))?.argv[0]).toBe('criterion')
    expect((await keep.taken('/proj', token, 1))?.argv).toEqual(['engines'])
    expect(keep.held).toBe(1)
  })

  it('names nothing for an answer that carried no door', async () => {
    const keep = keeping()

    expect(await keep.keep('/proj', { file: 'docs/ROADMAP.md', tasks: [] })).toBeNull()
    expect(keep.held).toBe(0)
  })

  it('answers nothing for a door index the batch does not have', async () => {
    const keep = keeping()
    const token = (await keep.keep('/proj', ANSWER)) ?? ''

    expect(await keep.taken('/proj', token, 7)).toBeNull()
    expect(await keep.taken('/proj', token, -1)).toBeNull()
  })

  it('answers nothing for a name nobody offered', async () => {
    const keep = keeping()
    await keep.keep('/proj', ANSWER)

    expect(await keep.taken('/proj', 'made-up', 0)).toBeNull()
  })

  it('answers nothing for another project, even one the same caller has open', async () => {
    // The root is part of the name: a door is about the files of the project it came from.
    const keep = keeping()
    const token = (await keep.keep('/proj', ANSWER)) ?? ''

    expect(await keep.taken('/elsewhere', token, 0)).toBeNull()
  })

  it('drops the batch once the project files have moved', async () => {
    // A door offered against a state that has gone may no longer close anything, and every
    // door in that batch is about the same gone state.
    const keep = keeping(['one', 'two'])
    const token = (await keep.keep('/proj', ANSWER)) ?? ''

    expect(await keep.taken('/proj', token, 0)).toBeNull()
    expect(keep.held).toBe(0)
    // And it stays dropped, rather than coming back when the stamp settles.
    expect(await keep.taken('/proj', token, 0)).toBeNull()
  })
})

describe('RG181: a keep with a bound', () => {
  it('holds one batch per project, whatever a window reads', async () => {
    const keep = keeping()

    await keep.keep('/a', ANSWER)
    await keep.keep('/a', ANSWER)
    await keep.keep('/a', ANSWER)

    expect(keep.held).toBe(1)
  })

  it('drops the batch it replaces, since no page has a button for it any more', async () => {
    const keep = keeping()
    const first = await keep.keep('/a', ANSWER)
    if (first === null) throw new Error('nothing was offered')

    await keep.keep('/a', ANSWER)

    expect(await keep.taken('/a', first, 1)).toBeNull()
  })

  it('keeps the one it just took, which is the answer a screen is showing', async () => {
    const keep = keeping()
    await keep.keep('/a', ANSWER)
    const second = await keep.keep('/a', ANSWER)
    if (second === null) throw new Error('nothing was offered')

    expect(await keep.taken('/a', second, 1)).toMatchObject({
      argv: ['engines'],
      complete: true,
    })
  })

  it('bounds by project and not overall, so one open project does not blind another', async () => {
    const keep = keeping()

    await keep.keep('/a', ANSWER)
    await keep.keep('/b', ANSWER)
    const second = await keep.keep('/a', ANSWER)

    expect(keep.held).toBe(2)
    expect(second).not.toBeNull()
  })
})
