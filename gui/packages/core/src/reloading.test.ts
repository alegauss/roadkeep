import { describe, expect, it } from 'vitest'

import { AGAIN, createReloading, HELD, REBUILDING, RESTARTING } from './reloading'

/** A build whose result this test decides, and whose timing it drives. */
function buildOnDemand() {
  const finish: ((built: boolean) => void)[] = []
  let started = 0

  return {
    get started() {
      return started
    },
    build: () => {
      started += 1
      return new Promise<boolean>((resolve) => finish.push(resolve))
    },
    /** Let the oldest outstanding build finish. */
    async settle(built: boolean): Promise<void> {
      const next = finish.shift()
      if (next === undefined) throw new Error('no build was running')
      next(built)
      // Two turns: one for the build's own promise, one for the continuation it schedules.
      await Promise.resolve()
      await Promise.resolve()
    },
  }
}

function harness() {
  const builds = buildOnDemand()
  const said: string[] = []
  let restarts = 0

  const reloading = createReloading({
    build: builds.build,
    restart: () => {
      restarts += 1
    },
    report: (line) => said.push(line),
  })

  return {
    builds,
    reloading,
    said,
    get restarts() {
      return restarts
    },
  }
}

describe('RG57: one change, one rebuild, one restart', () => {
  it('starts idle and builds nothing until something moves', () => {
    const { reloading, builds } = harness()

    expect(reloading.state).toBe('idle')
    expect(builds.started).toBe(0)
  })

  it('builds and then restarts', async () => {
    const run = harness()

    run.reloading.changed()
    expect(run.reloading.state).toBe('building')
    expect(run.restarts).toBe(0)

    await run.builds.settle(true)

    expect(run.restarts).toBe(1)
    expect(run.reloading.state).toBe('idle')
    expect(run.reloading.restarts).toBe(1)
    expect(run.said).toEqual([REBUILDING, RESTARTING])
  })
})

describe('RG57: a build that failed', () => {
  it('leaves the running app alone', async () => {
    // The one outcome worse than waiting: a window that will not open, in place of an
    // error somebody could have read.
    const run = harness()

    run.reloading.changed()
    await run.builds.settle(false)

    expect(run.restarts).toBe(0)
    expect(run.reloading.state).toBe('idle')
    expect(run.said).toEqual([REBUILDING, HELD])
  })

  it('recovers on the next save rather than needing the run killed', async () => {
    const run = harness()

    run.reloading.changed()
    await run.builds.settle(false)
    run.reloading.changed()
    await run.builds.settle(true)

    expect(run.restarts).toBe(1)
  })

  it('treats a build that threw as a build that failed', async () => {
    let restarts = 0
    const said: string[] = []
    const reloading = createReloading({
      build: () => Promise.reject(new Error('tsc could not be spawned')),
      restart: () => {
        restarts += 1
      },
      report: (line) => said.push(line),
    })

    reloading.changed()
    await Promise.resolve()
    await Promise.resolve()
    await Promise.resolve()

    expect(restarts).toBe(0)
    expect(reloading.state).toBe('idle')
    expect(said).toContain(HELD)
  })
})

describe('RG57: a save while a build is running', () => {
  it('never runs two builds at once', async () => {
    // `tsc -b` writing while another reads is a build that fails for a reason nobody edited.
    const run = harness()

    run.reloading.changed()
    run.reloading.changed()
    run.reloading.changed()

    expect(run.builds.started).toBe(1)
    expect(run.reloading.state).toBe('queued')
  })

  it('goes round again, so the save that arrived mid-build is not lost', async () => {
    const run = harness()

    run.reloading.changed()
    run.reloading.changed()
    await run.builds.settle(true)

    expect(run.builds.started).toBe(2)
    expect(run.reloading.state).toBe('building')
    expect(run.said).toEqual([REBUILDING, RESTARTING, AGAIN, REBUILDING])

    await run.builds.settle(true)

    expect(run.restarts).toBe(2)
    expect(run.reloading.state).toBe('idle')
  })

  it('goes round again after a failure too, because the newer source may compile', async () => {
    const run = harness()

    run.reloading.changed()
    run.reloading.changed()
    await run.builds.settle(false)

    expect(run.reloading.state).toBe('building')
    await run.builds.settle(true)

    expect(run.restarts).toBe(1)
  })

  it('remembers one pending change and not a queue of them', async () => {
    // Two saves during one build are one thing to rebuild, and a counter would rebuild
    // twice for a state the first one already reached.
    const run = harness()

    run.reloading.changed()
    for (let save = 0; save < 5; save += 1) run.reloading.changed()
    await run.builds.settle(true)
    await run.builds.settle(true)

    expect(run.builds.started).toBe(2)
    expect(run.reloading.state).toBe('idle')
  })
})

describe('RG57: what it says', () => {
  it('says nothing to a caller that asked for no reporting', async () => {
    let restarts = 0
    const reloading = createReloading({
      build: () => Promise.resolve(true),
      restart: () => {
        restarts += 1
      },
    })

    reloading.changed()
    await Promise.resolve()
    await Promise.resolve()

    expect(restarts).toBe(1)
  })
})
