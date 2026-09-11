import { folderName, type SessionRecord, type SessionState } from '@rk/core'
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
 */

/** Asked once per opening. A session's own screen is where its stream is followed. */
function useSessions(): readonly SessionRecord[] {
  const [held, setHeld] = useState<readonly SessionRecord[]>([])

  useEffect(() => {
    const bridge = getBridge()
    if (bridge === undefined) return undefined
    let live = true
    const stillHere = (): boolean => live
    void bridge.sessions().then(
      (all) => {
        if (stillHere()) setHeld(all)
      },
      () => undefined,
    )
    return () => {
      live = false
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
