import {
  DECLARES_NOTHING,
  BASE,
  bridgedRun,
  fill,
  openedFrom,
  openProject,
  type HandedOver,
  BASE_LOCALE,
  timeIn,
  EVERY_SOURCE,
  type SessionOutcome,
  folderName,
  PT_BR,
  PT_BR_LOCALE,
  translator,
  type EditedFile,
  type FileText,
} from '@rk/core'
import { act, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { projectPath, SESSIONS_ROUTE, sessionPath, taskPath } from './areas'
import i18next, { changeLanguage } from 'i18next'

import { linesIn } from './file-sheet'
import { drawWindow } from './harness'
import { holdSessionNotes } from './preferring'
import { at, CHANGED, engine, FILES, hear, KEY, RECORD, ROOT, SAID, USED } from './session-harness'
import { startSpeaking } from './speaking'
import { stubBridge } from './stub-bridge'

/**
 * RG153: a line handed to a session, and the session beside it.
 *
 * The bridge is stubbed the way a window sees it — a handover that answers, a record of what
 * is running, and the session topic to hear it on — over the same engine the task test builds.
 * What is held is that the stream is drawn as acts off the raw lines, that a line heard after
 * the record lands in its place, and that what moved comes from a reread and not from the
 * session's own account. The engine, the record and the bridge are `session-harness`'s, shared
 * with the browser project's file (RG213).
 */

afterEach(() => {
  Reflect.deleteProperty(window, 'roadkeep')
})

describe('RG153: handing a line to Claude Code', () => {
  it('takes the line and opens the session it started', async () => {
    const started: HandedOver = { kind: 'started', session: RECORD }
    // No session yet, which is the state a line is offered from: the handover is what puts
    // one there, and the far side holds it from that moment (RG175).
    const wired = await at(taskPath(ROOT, 'AL1'), { handOver: started })

    fireEvent.click(await screen.findByRole('button', { name: BASE['task.handOver'] }))

    expect(wired.handedOver).toEqual(['AL1'])
    // The session's own screen, which leads back to the line it was handed.
    expect(await screen.findByText(BASE['session.handed'])).toBeTruthy()
    expect(screen.getByRole('link', { name: 'AL1' }).getAttribute('href')).toBe(
      taskPath(ROOT, 'AL1'),
    )
  })

  it('names the holder of a held line and offers no session', async () => {
    // Block F's third criterion, held on the screen a person would click from.
    await at(taskPath(ROOT, 'AL2'))

    expect(
      await screen.findByText(
        fill(BASE['task.held.named'], { by: 'another session', since: 'an hour ago' }),
      ),
    ).toBeTruthy()
    expect(screen.queryByRole('button', { name: BASE['task.handOver'] })).toBeNull()
  })

  it('says why the line was not taken, in this app words for what came back', async () => {
    const wired = await at(taskPath(ROOT, 'AL1'), {
      handOver: { kind: 'unavailable', tried: [['claude'], ['/home/a/.local/bin/claude']] },
    })

    fireEvent.click(await screen.findByRole('button', { name: BASE['task.handOver'] }))

    expect(
      await screen.findByText(
        fill(BASE['task.handOver.unavailable'], {
          tried: 'claude, /home/a/.local/bin/claude',
        }),
      ),
    ).toBeTruthy()
    expect(wired.handedOver).toEqual(['AL1'])
  })

  it('leads back to a session this window already started for the line', async () => {
    await at(taskPath(ROOT, 'AL1'), { sessions: [RECORD] })

    const open = await screen.findByRole('link', { name: BASE['task.session.open'] })
    expect(open.getAttribute('href')).toBe(sessionPath(ROOT, 'AL1', KEY))
  })
})

describe('RG153: the session beside its task', () => {
  it('draws what was handed over, counted off the brief it was started from', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })

    expect(
      await screen.findByText(fill(BASE['session.claim'], { from: '📋', to: '🛠' })),
    ).toBeTruthy()
    expect(screen.getByText(fill(BASE['session.handed.design'], { count: 120 }))).toBeTruthy()
    // The singular keys, since the brief hands over one of each: a count of one says the
    // form the language has for it (RG216).
    expect(screen.getByText(fill(BASE['session.handed.deps.one'], { count: 1 }))).toBeTruthy()
    expect(screen.getByText(fill(BASE['session.handed.criteria.one'], { count: 1 }))).toBeTruthy()
    expect(
      screen.getByText(
        fill(BASE['session.handed.agent'], { command: 'claude', version: '2.1.263' }),
      ),
    ).toBeTruthy()
  })

  it('draws the stream as acts, a roadkeep call marked and a governed file named', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
    await screen.findByText(BASE['session.handed'])

    hear(wired, 'session', { session: KEY, index: 1, line: USED })

    const call = (await screen.findByText('Bash')).closest('li')
    if (call === null) throw new Error('no act')
    expect(within(call).getByText(BASE['session.act.roadkeep'])).toBeTruthy()
    // The raw line is one disclosure away from the act it was read into.
    expect(within(call).getByText(BASE['session.act.raw'])).toBeTruthy()

    const read = screen.getByText('Read').closest('li')
    if (read === null) throw new Error('no act')
    expect(
      within(read).getByText(fill(BASE['session.act.governed'], { files: 'docs/ROADMAP.md' })),
    ).toBeTruthy()
    expect(within(read).queryByText(BASE['session.act.roadkeep'])).toBeNull()
  })

  it('puts a line heard after the record in its own place in the stream', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
    await screen.findByText(BASE['session.handed'])

    hear(wired, 'session', { session: KEY, index: 2, line: USED })
    hear(wired, 'session', { session: KEY, index: 1, line: SAID })

    // The record's line, then what was heard, each in its place: the tool line carries two.
    await waitFor(() => {
      expect(screen.getAllByTestId('act').map((one) => one.dataset['kind'])).toEqual([
        'note',
        'said',
        'used',
        'used',
      ])
    })
  })

  it('says what the files moved, which is not what the session said it did', async () => {
    // The session's stream says it shipped; this column is the reread that settles it.
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD], shipped: true })

    const moved = within(await screen.findByTestId('moved'))
    expect(
      moved.getByText(fill(BASE['session.change.marker'], { from: '🛠', to: '✅' })),
    ).toBeTruthy()
    expect(moved.getByText(BASE['session.change.shipped'])).toBeTruthy()
    expect(moved.getByText(BASE['session.change.design.deleted'])).toBeTruthy()
  })

  it('says nothing moved while the line reads as it was handed over', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })

    expect(await screen.findByText(BASE['session.moved.none'])).toBeTruthy()
  })

  it('stops the session, and says how it ended when it does', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })

    fireEvent.click(await screen.findByRole('button', { name: BASE['session.stop'] }))
    expect(wired.stopped).toEqual([KEY])

    hear(wired, 'session', {
      session: KEY,
      outcome: { state: 'cancelled', sessionId: 'fake', code: null, said: '', result: '' },
    })

    expect(await screen.findByText(BASE['session.state.cancelled'])).toBeTruthy()
    expect(screen.queryByRole('button', { name: BASE['session.stop'] })).toBeNull()
  })

  it('names each governed file and when the disk last changed it', async () => {
    // The landing says which fields moved; this says which file the session actually wrote.
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })

    // The same wait as the claims below: this column stands before the disk has answered.
    await screen.findByText('docs/ROADMAP.md')
    const files = within(screen.getByTestId('files'))
    // In the window's language and not the desktop's, which RG177 separated.
    expect(files.getByText(timeIn(CHANGED, BASE_LOCALE))).toBeTruthy()
    // A role nothing has written yet is a state, drawn rather than dropped.
    expect(files.getByText('docs/DECISIONS.md')).toBeTruthy()
    expect(files.getByText(BASE['session.file.never'])).toBeTruthy()
  })

  it('names a claim held elsewhere, and neither its own line nor a lapsed one', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })

    // The panel draws before the registry answers, so the wait is for the entry and not for
    // the section — the container is there from the first frame, saying nothing is claimed.
    await screen.findByText('AL7')
    const elsewhere = within(screen.getByTestId('elsewhere'))
    expect(
      elsewhere.getByText(fill(BASE['session.claim.since'], { state: 'held', since: '15m' })),
    ).toBeTruthy()
    // The session's own claim is not somebody else, and an expired one is not somebody at all.
    expect(elsewhere.queryByText('AL1')).toBeNull()
    expect(elsewhere.queryByText('AL8')).toBeNull()
  })

  it('says so where this window holds no session by that name', async () => {
    await at(sessionPath(ROOT, 'AL1', 'nobody'))

    expect(await screen.findByText(BASE['session.missing'])).toBeTruthy()
  })
})

describe('RG208: system notes folded by choice', () => {
  const LIMIT = JSON.stringify({ type: 'rate_limit_event', rate_limit_info: { status: 'allowed' } })

  afterEach(() => {
    holdSessionNotes('shown')
  })

  it('folds each run of notes into one counted row, and leaves every other act drawn', async () => {
    holdSessionNotes('hidden')
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
    await screen.findByText(BASE['session.handed'])

    hear(wired, 'session', { session: KEY, index: 1, line: LIMIT })
    hear(wired, 'session', { session: KEY, index: 2, line: SAID })
    hear(wired, 'session', { session: KEY, index: 3, line: USED })

    // The record's init and the rate limit are one run; the text and both calls stand.
    const folded = await screen.findByTestId('folded')
    expect(folded.dataset['count']).toBe('2')
    expect(within(folded).getByText(fill(BASE['session.notes.folded'], { count: 2 }))).toBeTruthy()
    const stream = within(screen.getByTestId('stream'))
    expect(stream.getByText('Working it now.')).toBeTruthy()
    expect(stream.getByText('Bash')).toBeTruthy()
    // Folded and not dropped: each note is still there, one disclosure away.
    expect(
      within(folded)
        .getAllByTestId('act')
        .map((one) => one.dataset['kind']),
    ).toEqual(['note', 'note'])
  })

  it('draws every note as its own row by default, which is what it drew before the choice', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
    await screen.findByText(BASE['session.handed'])

    hear(wired, 'session', { session: KEY, index: 1, line: LIMIT })

    await waitFor(() => {
      expect(screen.getAllByTestId('act').map((one) => one.dataset['kind'])).toEqual([
        'note',
        'note',
      ])
    })
    expect(screen.queryByTestId('folded')).toBeNull()
  })
})

describe('RG153: every session this window started', () => {
  it('lists what is running, each leading to its own screen', async () => {
    await at(SESSIONS_ROUTE, { sessions: [RECORD] })

    const row = await screen.findByTestId('session')
    expect(row.dataset['id']).toBe('AL1')
    expect(within(row).getByText('a line ready to start')).toBeTruthy()
    expect(
      within(row)
        .getByRole('link', { name: fill(BASE['sessions.open'], { id: 'AL1' }) })
        .getAttribute('href'),
    ).toBe(sessionPath(ROOT, 'AL1', KEY))
    // One line written and no outcome: running, in the same words its own screen uses.
    expect(within(row).getByText(BASE['session.state.running'])).toBeTruthy()
  })

  it('says nothing has been started, which is what a window holds until one is', async () => {
    await at(SESSIONS_ROUTE)

    expect(await screen.findByText(BASE['sessions.none'])).toBeTruthy()
    expect(screen.getByText(BASE['sessions.none.hint'])).toBeTruthy()
  })
})

describe('RG177: a time in the window’s language', () => {
  afterEach(async () => {
    if (i18next.isInitialized) await changeLanguage(BASE_LOCALE)
  })

  it('writes a file’s stamp in the language the window speaks, not the desktop’s', async () => {
    await startSpeaking('pt-BR')
    await at(sessionPath(ROOT, 'AL1', RECORD.key), { sessions: [RECORD] })

    const files = await screen.findByTestId('files')
    expect(within(files).getByText(timeIn(CHANGED, 'pt-BR'))).toBeTruthy()
  })

  it('writes the same instant differently once the window speaks another language', async () => {
    await startSpeaking(BASE_LOCALE)
    await at(sessionPath(ROOT, 'AL1', RECORD.key), { sessions: [RECORD] })

    const files = await screen.findByTestId('files')
    // The same stamp, and not the string the other language writes for it.
    expect(within(files).queryByText(timeIn(CHANGED, 'pt-BR'))).toBeNull()
    expect(within(files).getByText(timeIn(CHANGED, BASE_LOCALE))).toBeTruthy()
  })
})

describe('RG178: a list that hears what it lists', () => {
  it('takes one subscription that means every session, not one per row', async () => {
    const wired = await at(SESSIONS_ROUTE, { sessions: [RECORD] })

    await screen.findByTestId('session')
    const heard = wired.listeners.filter((one) => one.topic === 'session')
    expect(heard.map((one) => one.key)).toEqual([EVERY_SOURCE])
  })

  it('reads again when a session says something, so an ending stops reading as running', async () => {
    const wired = await at(SESSIONS_ROUTE, { sessions: [RECORD] })

    expect(
      within(await screen.findByTestId('session')).getByText(BASE['session.state.running']),
    ).toBeTruthy()

    // Main's own record moves, and then main says so on the topic.
    wired.holds[0] = {
      ...RECORD,
      outcome: { state: 'done', sessionId: KEY, code: 0, said: '', result: 'shipped' },
    }
    hear(wired, 'session', { session: KEY, outcome: wired.holds[0].outcome as SessionOutcome })

    await waitFor(() => {
      expect(
        within(screen.getByTestId('session')).getByText(BASE['session.state.done']),
      ).toBeTruthy()
    })
  })

  it('hears a session it never listed, since the key it listens to is all of them', async () => {
    const wired = await at(SESSIONS_ROUTE)

    expect(await screen.findByText(BASE['sessions.none'])).toBeTruthy()

    // Started from another screen: a key this list had never heard of when it asked.
    wired.holds.push(RECORD)
    hear(wired, 'session', { session: KEY, index: 0, line: '{}' })

    await waitFor(() => {
      expect(screen.getByTestId('session').dataset['id']).toBe('AL1')
    })
  })
})

describe('RG190: the screen a handover moves after it is gone', () => {
  it('leaves a reader who went back where they went, when the handover lands', async () => {
    let landing: ((handed: HandedOver) => void) | null = null
    const alpha = openedFrom(
      await openProject(ROOT, [['roadkeep']], () => engine({ shipped: false })),
    )
    Object.defineProperty(window, 'roadkeep', {
      value: stubBridge({
        projects: () =>
          Promise.resolve({
            version: 1,
            roots: [],
            projects: [
              {
                path: ROOT,
                aliases: [],
                commonDir: null,
                root: '/code',
                confirmed: '',
                presence: 'present' as const,
                branch: '',
                declared: DECLARES_NOTHING,
              },
            ],
          }),
        open: () => Promise.resolve(alpha),
        run: (root, request) =>
          bridgedRun(() => engine({ shipped: false }).run({ ...request, root })),
        sessions: () => Promise.resolve([]),
        governedAt: () => Promise.resolve(FILES),
        // Held open, so the press and the answer are two moments a test can stand between.
        handOver: () =>
          new Promise<HandedOver>((answer) => {
            landing = answer
          }),
      }),
      configurable: true,
    })
    drawWindow({ at: taskPath(ROOT, 'AL1') })

    fireEvent.click(await screen.findByRole('button', { name: BASE['task.handOver'] }))
    await waitFor(() => {
      expect(landing).not.toBeNull()
    })

    // Back to the project, which is the screen this window is on when the answer arrives.
    fireEvent.click(screen.getByRole('link', { name: folderName(ROOT) }))
    await screen.findByText(BASE['project.blocks'])

    await act(async () => {
      landing?.({ kind: 'started', session: RECORD })
      await Promise.resolve()
    })

    // Still where the reader put themselves: the session started and is on the list, and
    // nothing moved the window to it.
    expect(screen.queryByText(BASE['session.handed'])).toBeNull()
    expect(screen.getByText(BASE['project.blocks'])).toBeTruthy()
  })
})

describe('RG243: the files a session edited', () => {
  /** Two edits of one file, a write to a governed one that failed, and a read that is no edit. */
  const EDITS = JSON.stringify({
    type: 'assistant',
    message: {
      content: [
        { type: 'tool_use', id: 'e1', name: 'Edit', input: { file_path: 'src/alpha.ts' } },
        { type: 'tool_use', id: 'e2', name: 'Write', input: { file_path: 'docs/ROADMAP.md' } },
        { type: 'tool_use', id: 'e3', name: 'Read', input: { file_path: 'src/beta.ts' } },
        { type: 'tool_use', id: 'e4', name: 'Edit', input: { file_path: 'src/alpha.ts' } },
      ],
    },
  })
  const ANSWERS = JSON.stringify({
    type: 'user',
    message: {
      content: [
        { tool_use_id: 'e1', type: 'tool_result', content: 'updated', is_error: false },
        { tool_use_id: 'e2', type: 'tool_result', content: 'denied by a hook', is_error: true },
        { tool_use_id: 'e4', type: 'tool_result', content: 'updated', is_error: false },
      ],
    },
  })

  afterEach(async () => {
    if (i18next.isInitialized) await changeLanguage(BASE_LOCALE)
  })

  it('lists each file the stream edited under what moved, counted, marked and failed', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
    const edited = await screen.findByTestId('edited')
    // Nothing edited is a state of its own, drawn before the first call.
    expect(within(edited).getByText(BASE['session.edited.none'])).toBeTruthy()

    hear(wired, 'session', { session: KEY, index: 1, line: EDITS })
    hear(wired, 'session', { session: KEY, index: 2, line: ANSWERS })

    await waitFor(() => {
      expect(screen.getAllByTestId('edited-file').map((row) => row.dataset['path'])).toEqual([
        'src/alpha.ts',
        'docs/ROADMAP.md',
      ])
    })
    const [alpha, roadmap] = screen.getAllByTestId('edited-file')
    if (alpha === undefined || roadmap === undefined) throw new Error('no rows')
    expect(within(alpha).getByText(fill(BASE['session.edited.calls'], { count: 2 }))).toBeTruthy()
    expect(within(alpha).queryByText(BASE['session.edited.failed'])).toBeNull()
    expect(within(alpha).queryByText(BASE['session.edited.governed'])).toBeNull()
    expect(
      within(roadmap).getByText(fill(BASE['session.edited.calls.one'], { count: 1 })),
    ).toBeTruthy()
    expect(within(roadmap).getByText(BASE['session.edited.governed'])).toBeTruthy()
    expect(within(roadmap).getByText(BASE['session.edited.failed'])).toBeTruthy()
    // Whose account this is, since the disk has not been asked.
    expect(
      within(screen.getByTestId('edited')).getByText(BASE['session.edited.about']),
    ).toBeTruthy()
    expect(screen.getByTestId('edited').closest('[data-region="session-moved"]')).not.toBeNull()
  })

  it('says it in the language the window speaks', async () => {
    await startSpeaking('pt-BR')
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
    await screen.findByTestId('edited')

    hear(wired, 'session', { session: KEY, index: 1, line: EDITS })

    const say = translator(PT_BR, PT_BR_LOCALE)
    const alpha = await screen.findByText(say('session.edited.calls', { count: 2 }))
    expect(alpha.closest('[data-testid="edited-file"]')?.getAttribute('data-path')).toBe(
      'src/alpha.ts',
    )
    expect(screen.getByText(say('session.edited.about'))).toBeTruthy()
  })
})

describe('RG244: the edited files against the disk', () => {
  const ALPHA = 'D:\\code\\alpha\\src\\alpha.ts'
  const OUTSIDE = 'C:\\Users\\a\\.claude\\memory\\notes.md'
  const EDITS = JSON.stringify({
    type: 'assistant',
    message: {
      content: [
        { type: 'tool_use', id: 'd1', name: 'Edit', input: { file_path: ALPHA } },
        { type: 'tool_use', id: 'd2', name: 'Edit', input: { file_path: 'src/beta.ts' } },
        { type: 'tool_use', id: 'd3', name: 'Write', input: { file_path: OUTSIDE } },
        { type: 'tool_use', id: 'd4', name: 'Edit', input: { file_path: 'src/gone.ts' } },
      ],
    },
  })
  const ANSWERS = JSON.stringify({
    type: 'user',
    message: {
      content: ['d1', 'd2', 'd3', 'd4'].map((id) => ({
        tool_use_id: id,
        type: 'tool_result',
        content: 'updated',
      })),
    },
  })
  /** Changed after the session started, before it, outside the root, and not there. */
  const DISK: EditedFile[] = [
    { path: ALPHA, shown: 'src/alpha.ts', inside: true, present: true, changed: CHANGED },
    {
      path: 'src/beta.ts',
      shown: 'src/beta.ts',
      inside: true,
      present: true,
      changed: '2026-09-10T08:00:00.000Z',
    },
    { path: OUTSIDE, shown: OUTSIDE, inside: false, present: false, changed: '' },
    { path: 'src/gone.ts', shown: 'src/gone.ts', inside: true, present: false, changed: '' },
  ]

  const row = (path: string) => {
    const found = screen.getAllByTestId('edited-file').find((one) => one.dataset['path'] === path)
    if (found === undefined) throw new Error(`no row for ${path}`)
    return found
  }

  it('says where each edited file stands on disk, and where the disk disagrees', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD], edited: DISK })
    await screen.findByTestId('edited')

    hear(wired, 'session', { session: KEY, index: 1, line: EDITS })
    hear(wired, 'session', { session: KEY, index: 2, line: ANSWERS })

    await waitFor(() => {
      expect(row('src/gone.ts').dataset['standing']).toBe('missing')
    })
    // Changed since the session started: the time, in the window's language, and no dispute.
    const alpha = within(row(ALPHA))
    expect(row(ALPHA).dataset['standing']).toBe('changed')
    // Drawn as the shell shortened it, and matched on the path the call spelled.
    expect(alpha.getByText('src/alpha.ts')).toBeTruthy()
    expect(
      alpha.getByText(fill(BASE['session.edited.changed'], { when: timeIn(CHANGED, BASE_LOCALE) })),
    ).toBeTruthy()
    expect(alpha.queryByText(BASE['session.edited.disagrees'])).toBeNull()
    // A call reported success and the disk has not changed the file since: the disagreement.
    const beta = within(row('src/beta.ts'))
    expect(beta.getByText(BASE['session.edited.unchanged'])).toBeTruthy()
    expect(beta.getByText(BASE['session.edited.disagrees'])).toBeTruthy()
    // Outside the project: named, never checked, and nothing to disagree with.
    const outside = within(row(OUTSIDE))
    expect(outside.getByText(BASE['session.edited.outside'])).toBeTruthy()
    expect(outside.queryByText(BASE['session.edited.disagrees'])).toBeNull()
    const gone = within(row('src/gone.ts'))
    expect(gone.getByText(BASE['session.edited.missing'])).toBeTruthy()
    expect(gone.getByText(BASE['session.edited.disagrees'])).toBeTruthy()
  })

  it('asks by the session and the paths its calls named, once calls land and when it ends', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD], edited: DISK })
    await screen.findByTestId('edited')

    // Calls still running have not moved the disk, so nothing is asked until one answers.
    hear(wired, 'session', { session: KEY, index: 1, line: EDITS })
    await screen.findAllByTestId('edited-file')
    expect(wired.editedAsked).toEqual([])

    hear(wired, 'session', { session: KEY, index: 2, line: ANSWERS })
    await waitFor(() => {
      expect(wired.editedAsked).toHaveLength(1)
    })
    expect(wired.editedAsked[0]).toEqual({
      key: KEY,
      paths: [ALPHA, 'src/beta.ts', OUTSIDE, 'src/gone.ts'],
    })

    hear(wired, 'session', {
      session: KEY,
      outcome: { state: 'done', sessionId: 'fake', code: 0, said: '', result: 'done' },
    })
    await waitFor(() => {
      expect(wired.editedAsked).toHaveLength(2)
    })
  })

  it('draws a row before the disk answers, with no standing claimed for it', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
    await screen.findByTestId('edited')

    hear(wired, 'session', { session: KEY, index: 1, line: EDITS })

    await waitFor(() => {
      expect(row('src/beta.ts').dataset['standing']).toBe('unasked')
    })
    expect(within(row('src/beta.ts')).queryByText(BASE['session.edited.disagrees'])).toBeNull()
  })
})

describe('RG245: counting a file’s lines', () => {
  it('counts the lines a file has, and not the empty one after its last break', () => {
    expect(linesIn('')).toBe(0)
    expect(linesIn('one')).toBe(1)
    expect(linesIn('one\n')).toBe(1)
    expect(linesIn('one\ntwo')).toBe(2)
    expect(linesIn('one\n\n')).toBe(2)
  })
})

describe('RG245: an edited file opened from the window', () => {
  const EDIT = (id: string) =>
    JSON.stringify({
      type: 'assistant',
      message: {
        content: [{ type: 'tool_use', id, name: 'Edit', input: { file_path: 'src/alpha.ts' } }],
      },
    })
  const ANSWER = (id: string) =>
    JSON.stringify({
      type: 'user',
      message: { content: [{ tool_use_id: id, type: 'tool_result', content: 'updated' }] },
    })
  const LOG = JSON.stringify({
    type: 'assistant',
    message: {
      content: [{ type: 'tool_use', id: 'w1', name: 'Write', input: { file_path: 'big.log' } }],
    },
  })
  const read = (text: string): FileText => ({
    kind: 'read',
    path: 'src/alpha.ts',
    shown: 'src/alpha.ts',
    text,
    bytes: text.length,
  })

  const openRow = async (path: string) => {
    fireEvent.click(
      await screen.findByRole('button', { name: fill(BASE['session.edited.open'], { path }) }),
    )
    return screen.findByTestId('file-sheet')
  }

  it('opens a row as the disk holds the file now, numbered, and forgets it when closed', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), {
      sessions: [RECORD],
      texts: [read('const a = 1\nconst b = 2\n')],
    })
    hear(wired, 'session', { session: KEY, index: 1, line: EDIT('e1') })

    const sheet = within(await openRow('src/alpha.ts'))

    await waitFor(() => {
      expect(sheet.getByTestId('file-text').textContent).toBe('const a = 1\nconst b = 2\n')
    })
    expect(sheet.getByText(fill(BASE['session.file.lines'], { count: 2 }))).toBeTruthy()
    expect(wired.fileAsked).toEqual([{ key: KEY, path: 'src/alpha.ts' }])

    fireEvent.keyDown(document.activeElement ?? document.body, { key: 'Escape' })
    await waitFor(() => {
      expect(screen.queryByTestId('file-sheet')).toBeNull()
    })
  })

  it('says why a file was not read, in this app words with the numbers it carried', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), {
      sessions: [RECORD],
      texts: [
        {
          kind: 'refused',
          path: 'big.log',
          code: 'too-large',
          fields: { bytes: '2000000', ceiling: '1048576' },
        },
      ],
    })
    hear(wired, 'session', { session: KEY, index: 1, line: LOG })

    const sheet = within(await openRow('big.log'))

    expect(
      await sheet.findByText(
        fill(BASE['file.refused.too-large'], { bytes: '2000000', ceiling: '1048576' }),
      ),
    ).toBeTruthy()
    expect(sheet.queryByTestId('file-text')).toBeNull()
  })

  it('reads again when the stream edits the open file, and when asked to', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), {
      sessions: [RECORD],
      texts: [read('before\n')],
    })
    hear(wired, 'session', { session: KEY, index: 1, line: EDIT('e1') })
    hear(wired, 'session', { session: KEY, index: 2, line: ANSWER('e1') })
    const sheet = within(await openRow('src/alpha.ts'))
    await waitFor(() => {
      expect(sheet.getByTestId('file-text').textContent).toBe('before\n')
    })
    const asked = wired.fileAsked.length

    // The session edits the same file while it is open: read as the answer lands.
    wired.texts.set('src/alpha.ts', read('after\n'))
    hear(wired, 'session', { session: KEY, index: 3, line: EDIT('e2') })
    hear(wired, 'session', { session: KEY, index: 4, line: ANSWER('e2') })
    await waitFor(() => {
      expect(sheet.getByTestId('file-text').textContent).toBe('after\n')
    })
    expect(wired.fileAsked.length).toBeGreaterThan(asked)

    const before = wired.fileAsked.length
    fireEvent.click(sheet.getByRole('button', { name: BASE['session.file.reload'] }))
    await waitFor(() => {
      expect(wired.fileAsked).toHaveLength(before + 1)
    })
  })
})

describe('RG242: which project a session is in', () => {
  it('names the project and the line above the session, each a link to its own screen', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
    await screen.findByText(BASE['session.handed'])

    const trail = screen.getByTestId('trail')
    // The task was the only crumb, so a session opened from the list never said its project.
    expect(
      within(trail)
        .getByRole('link', { name: folderName(ROOT) })
        .getAttribute('href'),
    ).toBe(projectPath(ROOT))
    expect(within(trail).getByRole('link', { name: 'AL1' }).getAttribute('href')).toBe(
      taskPath(ROOT, 'AL1'),
    )
    const chip = await within(trail).findByTestId('project-chip')
    expect(chip.getAttribute('aria-hidden')).toBe('true')
  })
})
