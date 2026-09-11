import { EVERY_SOURCE, folderName, type SessionRecord, type SessionState } from '@rk/core'
import { BentoEmptyState, BentoHero, BentoPanel } from '@viglet/viglet-design-system/bento'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { sessionPath } from './areas'
import { getBridge } from './bridge'
import { Pill } from './marks'
import { STATE_INTENT, STATE_TEXT } from './Session'
import { useWording } from './wording'

/**
 * Every session this window started (RG153), so one whose task screen was left is reachable
 * without remembering its route.
 *
 * **What is listed is what this process holds.** Sessions live with the window: the records are
 * main's, a session another launch started is not here, and nothing about them is stored — the
 * list is the answer to a question, asked when this screen opens.
 *
 * **And kept true by the topic, never by a timer** (RG178). Every line and every ending is
 * published already; what this screen could not do was name the sessions to listen to, since
 * one started after it asked has a key it never heard of. `EVERY_SOURCE` is the key that means
 * all of them, so this is one subscription that hears the next session as readily as the ones
 * the record answered with.
 */

/**
 * The record, re-asked whenever a session says anything.
 *
 * The read and not the event is what fills the list: what a row draws is the state, and the
 * record is where the state is. An event is only the news that it may have moved — which is
 * why a line and an ending are treated alike here, and why nothing has to be rebuilt from a
 * stream this screen does not follow.
 */
function useSessions(): readonly SessionRecord[] {
  const [held, setHeld] = useState<readonly SessionRecord[]>([])

  useEffect(() => {
    const bridge = getBridge()
    if (bridge === undefined) return undefined
    let live = true
    const stillHere = (): boolean => live
    const ask = (): void => {
      void bridge.sessions().then(
        (all) => {
          if (stillHere()) setHeld(all)
        },
        () => undefined,
      )
    }
    ask()
    const stop = bridge.subscribe('session', EVERY_SOURCE, ask)
    return () => {
      live = false
      stop()
    }
  }, [])

  return held
}

function stateOf(record: SessionRecord): SessionState {
  if (record.outcome !== null) return record.outcome.state
  return record.lines.length === 0 ? 'starting' : 'running'
}

export function Sessions() {
  const say = useWording()
  const held = useSessions()

  return (
    <>
      <BentoHero
        eyebrow={say('sessions.kicker')}
        title={
          held.length === 0
            ? say('sessions.title.none')
            : say('sessions.title', { count: held.length })
        }
        subtitle={say('sessions.footnote')}
      />
      {held.length === 0 ? (
        <BentoPanel contentClassName="p-6">
          <BentoEmptyState title={say('sessions.none')} description={say('sessions.none.hint')} />
        </BentoPanel>
      ) : (
        <BentoPanel className="overflow-hidden" contentClassName="p-0">
          {/* Three columns, each named: a grid whose columns are unlabelled is one a reader
              has to infer, and the catalogue already held the words (RG183). */}
          <div
            className="text-muted-foreground grid grid-cols-[8rem_minmax(0,1fr)_8rem] gap-4 px-5 py-2 text-[11px] font-semibold tracking-wider uppercase"
            data-testid="sessions-columns"
          >
            <span>{say('sessions.column.line')}</span>
            <span>{say('sessions.column.project')}</span>
            <span>{say('sessions.column.state')}</span>
          </div>
          <ul>
            {held.map((record) => {
              const state = stateOf(record)
              return (
                <li
                  key={record.key}
                  className="grid grid-cols-[8rem_minmax(0,1fr)_8rem] items-center gap-4 border-t px-5 py-3 first:border-t-0"
                  data-testid="session"
                  data-id={record.id}
                >
                  <Link
                    to={sessionPath(record.root, record.id, record.key)}
                    className="font-mono text-sm font-semibold hover:underline"
                    aria-label={say('sessions.open', { id: record.id })}
                  >
                    {record.id}
                  </Link>
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium">{folderName(record.root)}</div>
                    <div className="text-muted-foreground truncate text-xs">
                      {record.handed.symptom}
                    </div>
                  </div>
                  <Pill intent={STATE_INTENT[state]}>{say(STATE_TEXT[state])}</Pill>
                </li>
              )
            })}
          </ul>
        </BentoPanel>
      )}
    </>
  )
}
