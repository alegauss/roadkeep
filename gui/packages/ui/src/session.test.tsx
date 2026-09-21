import {
  DECLARES_NOTHING,
  BASE,
  bridgedRun,
  CHANGE_LETTER,
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
  type MovedPath,
} from '@rk/core'
import { act, cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { projectPath, SESSIONS_ROUTE, sessionPath, taskPath } from './areas'
import i18next, { changeLanguage } from 'i18next'

import { linesIn } from './file-sheet'
import { drawWindow } from './harness'
import { holdSessionNotes } from './preferring'
import {
  ASKED,
  at,
  CHANGED,
  engine,
  FILES,
  hear,
  KEY,
  RECORD,
  ROOT,
  SAID,
  STARTED,
  USED,
} from './session-harness'
import { startSpeaking } from './speaking'
import { scrolledIntoView } from './scroll-record'
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

/** Every file row either list draws, whichever tree or list it sits in. */
const FILE_ROWS = /^(edited|moved)-file$/

/**
 * Open a file the way a reader does (RG265): by its row. A file in a tree is a row of the tree
 * and the row is the control; one outside the project is a row of its own with its button.
 * Found by the path the session named it by, which is what the viewer is asked for.
 */
async function openFile(path: string) {
  const row = await waitFor(() => {
    const found = screen.getAllByTestId(FILE_ROWS).find((one) => one.dataset['path'] === path)
    if (found === undefined) throw new Error(`no row for ${path}`)
    return found
  })
  fireEvent.click(row.closest('[role="treeitem"]') ?? within(row).getByRole('button'))
  return screen.findByTestId('file-sheet')
}

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
      outcome: {
        state: 'cancelled',
        sessionId: 'fake',
        code: null,
        said: '',
        result: '',
        denials: [],
      },
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
      outcome: { state: 'done', sessionId: KEY, code: 0, said: '', result: 'shipped', denials: [] },
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

  it('lists each file the stream edited, counted, marked and failed', async () => {
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
    // A card of its own since RG265, and no longer a section of what moved in the backlog.
    expect(screen.getByTestId('edited').closest('[data-region="session-files"]')).not.toBeNull()
    expect(screen.getByTestId('edited').closest('[data-region="session-moved"]')).toBeNull()
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
    // Drawn under the folder the shell's shortening puts it in, and matched on the path the call
    // spelled (RG265): the row carries its own name, and `src` is the tree's.
    expect(alpha.getByText('alpha.ts')).toBeTruthy()
    expect(row(ALPHA).closest('[role="treeitem"]')?.getAttribute('aria-level')).toBe('2')
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
      outcome: { state: 'done', sessionId: 'fake', code: 0, said: '', result: 'done', denials: [] },
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

describe('RG265: the files it touched, as a tree of their own', () => {
  const editing = (id: string, path: string) =>
    JSON.stringify({
      type: 'assistant',
      message: { content: [{ type: 'tool_use', id, name: 'Edit', input: { file_path: path } }] },
    })

  /** The row a folder or a file is drawn as, found by the name the tree gives it. */
  const treeRow = (name: string) => {
    const found = screen
      .getAllByRole('treeitem')
      .find((one) => one.querySelector('span')?.textContent === name || one.textContent === name)
    if (found === undefined) throw new Error(`no tree row named ${name}`)
    return found
  }

  it('draws the edited files as folders holding them, not as full paths', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
    await screen.findByTestId('edited')

    hear(wired, 'session', { session: KEY, index: 1, line: editing('t1', 'src/alpha.ts') })
    hear(wired, 'session', { session: KEY, index: 2, line: editing('t2', 'src/beta.ts') })

    const tree = await screen.findByRole('tree', { name: BASE['session.edited'] })
    // One `src`, holding both — the prefix said once instead of on every row.
    await waitFor(() => {
      expect(within(tree).getAllByRole('treeitem')).toHaveLength(3)
    })
    expect(treeRow('src').getAttribute('aria-level')).toBe('1')
    expect(treeRow('src').getAttribute('aria-expanded')).toBe('true')
    expect(within(tree).queryByText('src/alpha.ts')).toBeNull()
  })

  it('keeps a folder the reader closed closed, and opens the one a new file arrives in', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
    await screen.findByTestId('edited')
    hear(wired, 'session', { session: KEY, index: 1, line: editing('t1', 'src/alpha.ts') })
    hear(wired, 'session', { session: KEY, index: 2, line: editing('t2', 'src/beta.ts') })
    await screen.findByRole('tree', { name: BASE['session.edited'] })
    await waitFor(() => {
      expect(treeRow('src').getAttribute('aria-expanded')).toBe('true')
    })

    fireEvent.click(treeRow('src'))
    await waitFor(() => {
      expect(treeRow('src').getAttribute('aria-expanded')).toBe('false')
    })

    // A file lands in a folder nobody has seen yet, while the session runs. It turns up open,
    // since a closed one would hide the file that just moved; the folder the reader shut stays
    // shut, since that was theirs.
    hear(wired, 'session', { session: KEY, index: 3, line: editing('t3', 'lib/gamma.ts') })
    await waitFor(() => {
      expect(treeRow('lib').getAttribute('aria-expanded')).toBe('true')
    })
    expect(treeRow('src').getAttribute('aria-expanded')).toBe('false')
    expect(screen.getAllByTestId('edited-file').map((one) => one.dataset['path'])).toEqual([
      'lib/gamma.ts',
    ])
  })

  it('draws what moved on disk as a tree too, in the same card', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
    await screen.findByTestId('moved-disk')

    hear(wired, 'session', {
      session: KEY,
      moved: [
        { path: 'dist/bundle.js', first: STARTED, last: STARTED, moves: 1 },
        { path: 'dist/bundle.css', first: STARTED, last: STARTED, moves: 1 },
      ],
      beyond: 0,
    })

    const tree = await screen.findByRole('tree', { name: BASE['session.disk'] })
    await waitFor(() => {
      expect(within(tree).getAllByRole('treeitem')).toHaveLength(3)
    })
    expect(screen.getByTestId('moved-disk').closest('[data-region="session-files"]')).not.toBeNull()
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

  const openRow = openFile

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

describe('RG246: what the session changed inside the file', () => {
  const EDITS = JSON.stringify({
    type: 'assistant',
    message: {
      content: [
        {
          type: 'tool_use',
          id: 'k1',
          name: 'Edit',
          input: {
            file_path: 'src/alpha.ts',
            old_string: 'const a = 0',
            new_string: 'const a = 1',
          },
        },
        {
          type: 'tool_use',
          id: 'k2',
          name: 'Edit',
          input: {
            file_path: 'src/alpha.ts',
            old_string: 'const b = 0',
            new_string: 'const b = 2',
          },
        },
      ],
    },
  })
  const ANSWERS = JSON.stringify({
    type: 'user',
    message: {
      content: [
        { tool_use_id: 'k1', type: 'tool_result', content: 'updated' },
        { tool_use_id: 'k2', type: 'tool_result', content: 'no match', is_error: true },
      ],
    },
  })
  /** The file as the disk holds it: the first edit landed, the second did not. */
  const TEXT: FileText = {
    kind: 'read',
    path: 'src/alpha.ts',
    shown: 'src/alpha.ts',
    text: 'const a = 1\nconst b = 0\n',
    bytes: 24,
  }

  const openAlpha = () => openFile('src/alpha.ts')

  it('draws each edit above the file, checked against the text that was read', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD], texts: [TEXT] })
    hear(wired, 'session', { session: KEY, index: 1, line: EDITS })
    hear(wired, 'session', { session: KEY, index: 2, line: ANSWERS })

    const sheet = within(await openAlpha())
    await waitFor(() => {
      expect(sheet.getAllByTestId('file-edit')).toHaveLength(2)
    })

    const [landed, missing] = sheet.getAllByTestId('file-edit')
    if (landed === undefined || missing === undefined) throw new Error('no edits')
    // What it put there is in the file, so it is there; the other's is not.
    expect(landed.dataset['standing']).toBe('in-the-file')
    expect(within(landed).getByText(BASE['session.file.edit.found'])).toBeTruthy()
    expect(within(landed).getByText('const a = 0')).toBeTruthy()
    expect(within(landed).getByText('const a = 1')).toBeTruthy()
    expect(missing.dataset['standing']).toBe('not-in-the-file')
    expect(within(missing).getByText(BASE['session.file.edit.gone'])).toBeTruthy()
    // And the call that failed says so beside its own blocks.
    expect(within(missing).getByText(BASE['session.act.failed'])).toBeTruthy()
  })

  it('leads from an edit back to the act that made it, in the stream', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD], texts: [TEXT] })
    hear(wired, 'session', { session: KEY, index: 1, line: EDITS })
    const sheet = within(await openAlpha())
    const [first] = await sheet.findAllByTestId('file-edit')
    const seq = first?.dataset['seq'] ?? ''

    fireEvent.click(
      within(first ?? document.body).getByText(fill(BASE['session.file.edit.act'], { seq })),
    )

    // The viewer closes, since the stream is under it, and the act it named is on the screen.
    await waitFor(() => {
      expect(screen.queryByTestId('file-sheet')).toBeNull()
    })
    const named = document.getElementById(`act-${seq}`)
    expect(named).not.toBeNull()
    // And brought into view, on the frame after the viewer closed (RG266) — the half of the lead
    // nothing checked while jsdom threw on it after the test had ended.
    await waitFor(() => {
      expect(scrolledIntoView).toEqual([named])
    })
  })
})

describe('RG247: files that moved on disk while the session ran', () => {
  const EDIT = JSON.stringify({
    type: 'assistant',
    message: {
      content: [{ type: 'tool_use', id: 'm1', name: 'Edit', input: { file_path: 'src/alpha.ts' } }],
    },
  })
  const MOVED: MovedPath[] = [
    { path: 'src/alpha.ts', first: STARTED, last: CHANGED, moves: 1 },
    { path: 'dist/bundle.js', first: STARTED, last: CHANGED, moves: 4 },
  ]

  it('lists what no edit call named, unattributed, and leaves the edited list its own', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), {
      sessions: [RECORD],
      edited: [
        {
          path: 'src/alpha.ts',
          shown: 'src/alpha.ts',
          inside: true,
          present: true,
          changed: CHANGED,
        },
      ],
    })
    hear(wired, 'session', { session: KEY, index: 1, line: EDIT })
    hear(wired, 'session', { session: KEY, moved: MOVED, beyond: 3 })

    const disk = within(await screen.findByTestId('moved-disk'))
    await waitFor(() => {
      expect(disk.getAllByTestId('moved-file').map((one) => one.dataset['path'])).toEqual([
        'dist/bundle.js',
      ])
    })
    // Counted, dated, and said to be nobody's account in particular.
    expect(
      disk.getByText(fill(BASE['session.disk.moves'], { count: 4 }), { exact: false }),
    ).toBeTruthy()
    expect(disk.getByText(BASE['session.disk.about'])).toBeTruthy()
    expect(disk.getByText(fill(BASE['session.disk.beyond'], { count: 3 }))).toBeTruthy()
  })

  it('says nothing else moved before anything has, and opens a moved file in the viewer', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), {
      sessions: [RECORD],
      texts: [
        {
          kind: 'read',
          path: 'dist/bundle.js',
          shown: 'dist/bundle.js',
          text: 'built\n',
          bytes: 6,
        },
      ],
    })
    const disk = within(await screen.findByTestId('moved-disk'))
    expect(disk.getByText(BASE['session.disk.none'])).toBeTruthy()

    hear(wired, 'session', { session: KEY, moved: MOVED, beyond: 0 })

    const sheet = within(await openFile('dist/bundle.js'))
    await waitFor(() => {
      expect(sheet.getByTestId('file-text').textContent).toBe('built\n')
    })
    expect(wired.fileAsked).toEqual([{ key: KEY, path: 'dist/bundle.js' }])
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

describe('RG268: an ended turn, drawn as what the files and the refusals say', () => {
  const ENDED: SessionOutcome = {
    state: 'done',
    sessionId: 'fake',
    code: 0,
    said: '',
    result: 'I stopped to ask which remedy you want.',
    denials: [],
  }
  const REFUSED: SessionOutcome = {
    ...ENDED,
    state: 'waiting',
    denials: [{ tool: 'Edit', callId: 'toolu_01', input: { file_path: 'docs/IMPROVEMENTS.md' } }],
  }

  /** The hero's own pill, which is where a reader looks for how the session stands. */
  const pill = async (text: string) => {
    const hero = await screen.findByText(text)
    return hero
  }

  it('draws a clean end that left the line unshipped as a stop, not as done', async () => {
    // commitclerk's T65 ended its turn asking for a choice, with the line still in progress
    // and nothing written, and the window drew it as done.
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [{ ...RECORD, outcome: ENDED }] })

    expect(await pill(BASE['session.state.unshipped'])).toBeTruthy()
    expect(screen.queryByText(BASE['session.state.done'])).toBeNull()
  })

  it('draws it as the turn ending where the files say the line shipped', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), {
      sessions: [{ ...RECORD, outcome: ENDED }],
      shipped: true,
    })

    expect(await pill(BASE['session.state.done'])).toBeTruthy()
    expect(screen.queryByText(BASE['session.state.unshipped'])).toBeNull()
  })

  it('says a session refused a call is waiting on the reader, on the screen and on the list', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [{ ...RECORD, outcome: REFUSED }] })
    expect(await pill(BASE['session.state.waiting'])).toBeTruthy()
    cleanup()

    // The list has no landing to read, so it says what the engine did: waiting, never done.
    await at(SESSIONS_ROUTE, { sessions: [{ ...RECORD, outcome: REFUSED }] })
    const row = await screen.findByTestId('session')
    expect(within(row).getByText(BASE['session.state.waiting'])).toBeTruthy()
  })
})

describe('RG269: answering a session that stopped, from the window', () => {
  const STOPPED: SessionOutcome = {
    state: 'done',
    sessionId: 's-42',
    code: 0,
    said: '',
    result: 'Which of the two remedies do you want?',
    denials: [],
  }

  it('offers a reply under the stream once the session stopped, beside its last words', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [{ ...RECORD, outcome: STOPPED }] })

    const reply = await screen.findByTestId('reply')
    const lastWord = within(reply).getByTestId('last-word')
    expect(within(lastWord).getByText(BASE['session.result'])).toBeTruthy()
    expect(within(lastWord).getByText(STOPPED.result)).toBeTruthy()
    expect(within(reply).getByLabelText(BASE['session.reply'])).toBeTruthy()
    // Said once, beside the box, and no longer repeated in the side panel.
    expect(screen.getAllByText(BASE['session.result'])).toHaveLength(1)
    // Under the stream, in its panel: the reply is to what the stream says.
    expect(reply.closest('[data-region="session-stream"]')).not.toBeNull()
  })

  it('offers none while the session runs, or where it never named itself', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
    await screen.findByText(BASE['session.handed'])
    expect(screen.queryByTestId('reply')).toBeNull()
    cleanup()

    await at(sessionPath(ROOT, 'AL1', KEY), {
      sessions: [{ ...RECORD, outcome: { ...STOPPED, sessionId: '' } }],
    })
    await screen.findByText(BASE['session.handed'])
    expect(screen.queryByTestId('reply')).toBeNull()
  })

  it('sends the words to that session, and empties the box when it resumed', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), {
      sessions: [{ ...RECORD, outcome: STOPPED }],
    })
    const box = await screen.findByLabelText(BASE['session.reply'])
    const send = screen.getByRole('button', { name: BASE['session.reply.send'] })
    // Nothing to send before anything is written.
    expect(send.hasAttribute('disabled')).toBe(true)

    fireEvent.change(box, { target: { value: 'The first one.' } })
    fireEvent.click(send)

    await waitFor(() => {
      expect(wired.replied).toEqual([{ key: KEY, text: 'The first one.', allowed: [] }])
    })
    await waitFor(() => {
      expect((box as HTMLTextAreaElement).value).toBe('')
    })
  })

  it('says why a reply resumed nothing, in its own words and not a handover’s', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), {
      sessions: [{ ...RECORD, outcome: STOPPED }],
      reply: {
        kind: 'held',
        held: [{ by: 'another session', since: 'an hour ago', state: 'held', paths: [] }],
      },
    })
    fireEvent.change(await screen.findByLabelText(BASE['session.reply']), {
      target: { value: 'The first one.' },
    })
    fireEvent.click(screen.getByRole('button', { name: BASE['session.reply.send'] }))

    expect(
      await screen.findByText(
        fill(BASE['session.reply.held'], { by: 'another session', since: 'an hour ago' }),
      ),
    ).toBeTruthy()
  })

  it('opens with the box focused where the session is waiting on the reader', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), {
      sessions: [
        {
          ...RECORD,
          outcome: {
            ...STOPPED,
            state: 'waiting',
            denials: [{ tool: 'Edit', callId: 't1', input: {} }],
          },
        },
      ],
    })

    const box = await screen.findByLabelText(BASE['session.reply'])
    await waitFor(() => {
      expect(document.activeElement).toBe(box)
    })
  })

  it('runs again when the far side says it resumed, with no ended pill or reply left over', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), {
      sessions: [{ ...RECORD, outcome: STOPPED }],
    })
    await screen.findByTestId('reply')

    hear(wired, 'session', { session: KEY, resumed: true })

    await waitFor(() => {
      expect(screen.queryByTestId('reply')).toBeNull()
    })
    expect(screen.getByText(BASE['session.state.running'])).toBeTruthy()
  })
})

describe('RG270: a refused call, shown and allowed for one turn', () => {
  /** A session whose Edit was refused, with the call in its stream so the link has somewhere to go. */
  const EDIT_CALL = JSON.stringify({
    type: 'assistant',
    message: {
      content: [
        { type: 'tool_use', id: 'toolu_01', name: 'Edit', input: { file_path: 'docs/ROADMAP.md' } },
      ],
    },
  })
  const WAITING: SessionOutcome = {
    state: 'waiting',
    sessionId: 's-42',
    code: 0,
    said: '',
    result: 'I need to edit the roadmap.',
    denials: [{ tool: 'Edit', callId: 'toolu_01', input: { file_path: 'docs/ROADMAP.md' } }],
  }
  const WAITING_RECORD = { ...RECORD, lines: [...RECORD.lines, EDIT_CALL], outcome: WAITING }

  it('lists each refusal with its tool, what it would have touched and its call', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [WAITING_RECORD] })

    const refusal = await screen.findByTestId('refusal')
    expect(within(refusal).getByText('Edit')).toBeTruthy()
    expect(within(refusal).getByText('docs/ROADMAP.md')).toBeTruthy()
    expect(
      within(refusal).getByRole('checkbox', {
        name: fill(BASE['session.grant.allow'], { tool: 'Edit' }),
      }),
    ).toBeTruthy()

    fireEvent.click(within(refusal).getByRole('button', { name: BASE['session.grant.call'] }))
    // The link leads to the act that made the call.
    const called = document.querySelector('[data-kind="used"]')
    expect(scrolledIntoView).toContain(called)
  })

  it('places the grant’s sentence in an empty box, still the reader’s to change', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [WAITING_RECORD] })
    const refusal = await screen.findByTestId('refusal')

    fireEvent.click(within(refusal).getByRole('checkbox'))

    const box = screen.getByLabelText(BASE['session.reply']) as HTMLTextAreaElement
    await waitFor(() => {
      expect(box.value).toBe(fill(BASE['session.grant.reply'], { tools: 'Edit' }))
    })
  })

  it('sends the checked tool with the reply, and nothing where nothing was checked', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [WAITING_RECORD] })
    const refusal = await screen.findByTestId('refusal')
    const box = screen.getByLabelText(BASE['session.reply'])

    fireEvent.change(box, { target: { value: 'Not yet.' } })
    fireEvent.click(screen.getByRole('button', { name: BASE['session.reply.send'] }))
    await waitFor(() => {
      expect(wired.replied).toEqual([{ key: KEY, text: 'Not yet.', allowed: [] }])
    })

    fireEvent.click(within(refusal).getByRole('checkbox'))
    fireEvent.change(box, { target: { value: 'Go on.' } })
    fireEvent.click(screen.getByRole('button', { name: BASE['session.reply.send'] }))
    await waitFor(() => {
      expect(wired.replied.at(-1)).toEqual({ key: KEY, text: 'Go on.', allowed: ['Edit'] })
    })
  })
})

describe('RG271: what an agent wrote for a person, rendered', () => {
  /** A said line, as the stream carries one. */
  function saying(text: string) {
    return JSON.stringify({ type: 'assistant', message: { content: [{ type: 'text', text }] } })
  }

  async function heard(text: string) {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
    await screen.findByText(BASE['session.handed'])
    hear(wired, 'session', { session: KEY, index: 1, line: saying(text) })
    return waitFor(() => {
      const said = screen.getAllByTestId('act').find((one) => one.dataset['kind'] === 'said')
      if (said === undefined) throw new Error('no said act')
      return said
    })
  }

  it('draws its bold, its code and its choices as elements, not as characters', async () => {
    const said = await heard(
      'Two **remedies** for `lint`:\n\n1. Retire the row\n2. Flip the row\n\n```sh\nnpm run lint\n```',
    )

    expect(within(said).getByText('remedies').tagName).toBe('STRONG')
    expect(within(said).getByText('lint').tagName).toBe('CODE')
    expect(
      within(said)
        .getAllByRole('listitem')
        .map((one) => one.textContent),
    ).toEqual(['Retire the row', 'Flip the row'])
    expect(within(said).getByText('npm run lint').closest('pre')).not.toBeNull()
    // Scrolled inside the stream, and reachable by a keyboard, which is what reads its end.
    const wide = within(said).getByRole('region', { name: BASE['session.prose.wide'] })
    expect(wide.tabIndex).toBe(0)
    expect(within(wide).getByText('npm run lint')).toBeTruthy()
    // The asterisks are gone from what is read, and still in the raw line under it.
    expect(within(within(said).getByTestId('prose')).queryByText(/\*\*/)).toBeNull()
    expect(
      within(said)
        .getByText(/\*\*remedies\*\*/)
        .closest('details'),
    ).not.toBeNull()
  })

  it('renders no raw HTML and fetches no image, and opens a link in its own window', async () => {
    const said = await heard(
      'Look <b>here</b> ![the chart](https://example.com/chart.png) and [the docs](https://example.com/docs)',
    )

    expect(said.querySelector('b')).toBeNull()
    expect(said.querySelector('img')).toBeNull()
    expect(within(said).getByText('the chart').tagName).toBe('SPAN')
    const link = within(said).getByRole('link', { name: 'the docs' })
    // A link with a target is a window the shell's guard sends to the desktop's browser.
    expect(link.getAttribute('target')).toBe('_blank')
    expect(link.getAttribute('rel')).toBe('noreferrer noopener')
  })

  it('draws an agent heading as emphasis, never as a heading of this screen', async () => {
    const said = await heard('# Plan\n\nShip it.')

    expect(within(said).queryByRole('heading')).toBeNull()
    expect(within(said).getByText('Plan').tagName).toBe('P')
  })

  it('labels a task list mark with whether it is done', async () => {
    const said = await heard('- [x] typecheck\n- [ ] shots')

    expect(within(said).queryByRole('checkbox')).toBeNull()
    const items = within(said)
      .getAllByRole('listitem')
      .map((one) => one.textContent)
    expect(items).toEqual([
      `${BASE['session.prose.task.done']} typecheck`,
      `${BASE['session.prose.task.open']} shots`,
    ])
  })

  it('renders its last word too, and keeps a tool call and what it gave back raw', async () => {
    const outcome: SessionOutcome = {
      state: 'done',
      sessionId: 's-42',
      code: 0,
      said: '',
      result: 'Pick **one**.',
      denials: [],
    }
    const returned = JSON.stringify({
      type: 'user',
      message: { content: [{ type: 'tool_result', tool_use_id: 't1', content: '**raw** out' }] },
    })
    await at(sessionPath(ROOT, 'AL1', KEY), {
      sessions: [{ ...RECORD, lines: [...RECORD.lines, USED, returned], outcome }],
    })

    const lastWord = await screen.findByTestId('last-word')
    expect(within(lastWord).getByText('one').tagName).toBe('STRONG')
    expect(await screen.findByText('**raw** out')).toBeTruthy()
  })
})

describe('RG272: a question the running session asks, answered from the window', () => {
  const ASKING_RECORD = { ...RECORD, lines: [...RECORD.lines, ASKED] }
  const pill = (text: string) => screen.findByText(text)

  it('draws the question in the stream and the session as asking, on its screen and the list', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [ASKING_RECORD] })

    expect(await pill(BASE['session.state.asking'])).toBeTruthy()
    const asked = screen.getAllByTestId('act').find((one) => one.dataset['kind'] === 'asked')
    if (asked === undefined) throw new Error('no question in the stream')
    expect(within(asked).getByText('Write')).toBeTruthy()
    expect(within(asked).getByText('src/notes.md')).toBeTruthy()
    expect(within(asked).getByTestId('ask-standing').dataset['standing']).toBe('open')
    cleanup()

    await at(SESSIONS_ROUTE, { sessions: [ASKING_RECORD] })
    const row = await screen.findByTestId('session')
    expect(within(row).getByText(BASE['session.state.asking'])).toBeTruthy()
  })

  it('offers the three answers under the stream, and what allowing for the session grants', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [ASKING_RECORD] })

    const asking = await screen.findByTestId('asking')
    expect(asking.closest('[data-region="session-stream"]')).not.toBeNull()
    const ask = within(asking).getByTestId('ask')
    for (const key of ['session.ask.once', 'session.ask.session', 'session.ask.decline'] as const) {
      expect(within(ask).getByRole('button', { name: BASE[key] })).toBeTruthy()
    }
    expect(
      within(ask).getByText(fill(BASE['session.ask.grants'], { grants: 'acceptEdits' })),
    ).toBeTruthy()
    // No reply box while it runs: a reply is for a session that stopped.
    expect(screen.queryByTestId('reply')).toBeNull()
  })

  it('sends the answer by the question, and draws it answered once the line arrives', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [ASKING_RECORD] })
    const ask = await screen.findByTestId('ask')

    fireEvent.click(within(ask).getByRole('button', { name: BASE['session.ask.session'] }))
    await waitFor(() => {
      expect(wired.answered).toEqual([{ key: KEY, requestId: 'ask-1', answer: 'session' }])
    })

    // The far side keeps the answer as a line, and every window hears it as one.
    const line = JSON.stringify({
      type: 'control_response',
      response: {
        subtype: 'success',
        request_id: 'ask-1',
        response: { behavior: 'allow', updatedInput: {}, updatedPermissions: [] },
      },
    })
    hear(wired, 'session', { session: KEY, index: ASKING_RECORD.lines.length, line })

    await waitFor(() => {
      expect(screen.queryByTestId('asking')).toBeNull()
    })
    expect(screen.getByTestId('ask-standing').dataset['standing']).toBe('session')
    expect(await pill(BASE['session.state.running'])).toBeTruthy()
  })

  it('says why an answer was not sent, and keeps the question open', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), {
      sessions: [ASKING_RECORD],
      answer: { kind: 'withheld', reason: 'that question is no longer open' },
    })
    const ask = await screen.findByTestId('ask')

    fireEvent.click(within(ask).getByRole('button', { name: BASE['session.ask.decline'] }))

    expect(
      await within(ask).findByText(
        fill(BASE['session.ask.withheld'], { reason: 'that question is no longer open' }),
      ),
    ).toBeTruthy()
    expect(screen.getByTestId('asking')).toBeTruthy()
  })

  it('draws a question left open by a session that ended as unanswered, with nothing to press', async () => {
    const ended: SessionOutcome = {
      state: 'cancelled',
      sessionId: '',
      code: null,
      said: '',
      result: '',
      denials: [],
    }
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [{ ...ASKING_RECORD, outcome: ended }] })

    expect(await screen.findByText(BASE['session.ask.unanswered'])).toBeTruthy()
    expect(screen.queryByTestId('asking')).toBeNull()
    expect(screen.queryByText(BASE['session.state.asking'])).toBeNull()
  })
})

describe('RG280: what the session did to each file', () => {
  /** One call per line, each answered on its own line, which is how a real run arrives. */
  const CALL = (id: string, tool: string, path: string) =>
    JSON.stringify({
      type: 'assistant',
      message: { content: [{ type: 'tool_use', id, name: tool, input: { file_path: path } }] },
    })
  /** The answer, carrying the `tool_use_result` Claude Code writes beside the result. */
  const ANSWER = (id: string, result: Record<string, unknown>) =>
    JSON.stringify({
      type: 'user',
      message: {
        content: [{ tool_use_id: id, type: 'tool_result', content: 'ok', is_error: false }],
      },
      tool_use_result: result,
    })

  const MADE = 'src/made.ts'
  const ALPHA = 'src/alpha.ts'
  const GONE = 'src/gone.ts'
  const LOST = 'src/lost.ts'

  /** Made and still there, changed and still there, changed and gone, made and gone. */
  const DISK: EditedFile[] = [
    { path: MADE, shown: MADE, inside: true, present: true, changed: CHANGED },
    { path: ALPHA, shown: ALPHA, inside: true, present: true, changed: CHANGED },
    { path: GONE, shown: GONE, inside: true, present: false, changed: '' },
    { path: LOST, shown: LOST, inside: true, present: false, changed: '' },
  ]

  const LINES = [
    CALL('k1', 'Write', MADE),
    ANSWER('k1', { type: 'create', filePath: MADE, originalFile: null }),
    CALL('k2', 'Edit', ALPHA),
    ANSWER('k2', { filePath: ALPHA, originalFile: 'what it said before' }),
    CALL('k3', 'Edit', GONE),
    ANSWER('k3', { filePath: GONE, originalFile: 'what it said before' }),
    CALL('k4', 'Write', LOST),
    ANSWER('k4', { type: 'create', filePath: LOST, originalFile: null }),
  ]

  const row = (path: string) => {
    const found = screen.getAllByTestId('edited-file').find((one) => one.dataset['path'] === path)
    if (found === undefined) throw new Error(`no row for ${path}`)
    return found
  }

  afterEach(async () => {
    if (i18next.isInitialized) await changeLanguage(BASE_LOCALE)
  })

  async function drawn() {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD], edited: DISK })
    await screen.findByTestId('edited')
    LINES.forEach((line, index) => {
      hear(wired, 'session', { session: KEY, index: index + 1, line })
    })
    await waitFor(() => {
      expect(row(LOST).dataset['kind']).toBeDefined()
    })
  }

  it('marks each file with the letter and the word for what the session did to it', async () => {
    await drawn()

    expect(row(MADE).dataset['kind']).toBe('created')
    expect(row(MADE).textContent).toContain(
      `${CHANGE_LETTER.created} ${BASE['session.kind.created']}`,
    )
    expect(row(ALPHA).dataset['kind']).toBe('changed')
    expect(row(ALPHA).textContent).toContain(
      `${CHANGE_LETTER.changed} ${BASE['session.kind.changed']}`,
    )
  })

  it('reads a file that is gone as deleted, and one it made and lost as its own word', async () => {
    await drawn()

    // The session's answer says the file was there; the disk says it is not.
    expect(row(GONE).dataset['kind']).toBe('deleted')
    expect(row(GONE).textContent).toContain(
      `${CHANGE_LETTER.deleted} ${BASE['session.kind.deleted']}`,
    )
    // And one it created that nothing holds now is not a file it deleted.
    expect(row(LOST).dataset['kind']).toBe('undone')
    expect(row(LOST).textContent).toContain(
      `${CHANGE_LETTER.undone} ${BASE['session.kind.undone']}`,
    )
  })

  it('strikes the name of a file that is not there any more', async () => {
    await drawn()

    expect(within(row(GONE)).getByText('gone.ts').className).toContain('line-through')
    expect(within(row(MADE)).getByText('made.ts').className).not.toContain('line-through')
  })

  it('marks nothing until the call is answered, since a mark before it is a guess', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD], edited: DISK })
    await screen.findByTestId('edited')

    hear(wired, 'session', { session: KEY, index: 1, line: CALL('k9', 'Write', MADE) })

    await waitFor(() => {
      expect(row(MADE)).toBeTruthy()
    })
    expect(row(MADE).dataset['kind']).toBeUndefined()
    expect(row(MADE).textContent).not.toContain(BASE['session.kind.created'])
  })

  it('says the word in the language the window speaks', async () => {
    await startSpeaking('pt-BR')
    await drawn()

    const say = translator(PT_BR, PT_BR_LOCALE)
    expect(row(MADE).textContent).toContain(say('session.kind.created'))
  })
})
