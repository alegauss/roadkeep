import { folderName, type Gated, type LintPayload } from '@rk/core'
import { Button } from '@viglet/viglet-design-system'
import { BentoEmptyState, BentoHero, BentoPanel } from '@viglet/viglet-design-system/bento'
import { useEffect, useMemo, type ReactNode } from 'react'
import { useParams } from 'react-router-dom'

import { projectPath } from './areas'
import { DoorRow } from './Doors'
import { Caption } from './forms'
import { Pill } from './marks'
import { useGate } from './useGate'
import { useWording } from './wording'

/**
 * The gate as a surface and not a report (RG152), which is block E's third criterion.
 *
 * **A finding is a row**: its code, where it is, and the sentence the gate wrote — then the
 * doors that close it, drawn by the same component the write path draws a refusal's with
 * (RG151). Nothing here works out what a fix should be; every command shown is the engine's,
 * and taking one is naming which door the carrier kept.
 *
 * **The rows go when the findings do.** A door that ran means the report is old, so the gate
 * runs again and the answer is what says whether the finding is closed — never this screen.
 *
 * **Notes are drawn apart from findings.** The gate says things it does not fail for, and a
 * screen that mixed the two would report a clean project as having eleven problems.
 */

/** One finding, with what closes it under it. */
function Finding({
  gated,
  onTake,
  mark,
}: {
  readonly gated: Gated
  readonly onTake: Taking
  /** Which report this row is in: a note is not a finding, and neither is drawn as one. */
  readonly mark: string
}) {
  const say = useWording()
  const { finding } = gated

  return (
    <li className="border-t first:border-t-0" data-testid={mark}>
      <div className="flex flex-col gap-1 px-4 py-3">
        <span className="flex flex-wrap items-center gap-2">
          <Pill intent="error">{finding.code}</Pill>
          {finding.where === '' ? null : (
            <span className="text-muted-foreground font-mono text-xs">{finding.where}</span>
          )}
          {finding.id === '' ? null : <span className="font-mono text-xs">{finding.id}</span>}
        </span>
        <span className="text-sm wrap-anywhere">{finding.message}</span>
        {finding.decision === '' ? null : (
          <span className="text-xs font-medium" data-testid="decision">
            {say('gate.decision', { decision: finding.decision })}
          </span>
        )}
        {finding.awaits === '' ? null : (
          <span className="text-muted-foreground text-xs">
            {say('gate.awaits', { awaits: finding.awaits })}
          </span>
        )}
        {finding.sequence ? (
          <span className="text-muted-foreground text-xs">{say('gate.sequence')}</span>
        ) : null}
      </div>
      {gated.doors.length === 0 ? (
        <p className="text-muted-foreground px-4 pb-3 text-xs">{say('gate.doors.none')}</p>
      ) : (
        <div className="px-0 pb-1">
          <span className="block px-4 pb-1">
            <Caption>{say('gate.doors')}</Caption>
          </span>
          <ul>
            {gated.doors.map(({ offer, which }) => (
              <DoorRow key={which} door={offer.door} which={which} onTake={onTake} />
            ))}
          </ul>
        </div>
      )}
    </li>
  )
}

type Taking = (which: number, words: readonly string[]) => void

function Report({
  title,
  rows,
  onTake,
  mark,
}: {
  readonly title: ReactNode
  readonly rows: readonly Gated[]
  readonly onTake: Taking
  readonly mark: string
}) {
  if (rows.length === 0) return null
  return (
    <BentoPanel className="overflow-hidden" contentClassName="p-0">
      <span className="block px-4 pt-3">
        <Caption>{title}</Caption>
      </span>
      <ul className="mt-2">
        {rows.map((gated) => (
          <Finding
            key={`${gated.finding.code}:${gated.finding.where}`}
            gated={gated}
            onTake={onTake}
            mark={mark}
          />
        ))}
      </ul>
    </BentoPanel>
  )
}

/** What the run counted, which is the engine's sentence about its own read. */
function Counted({ payload }: { readonly payload: LintPayload }) {
  const say = useWording()
  return (
    <BentoPanel contentClassName="p-5">
      <p className="text-sm" data-testid="counted">
        {payload.clean
          ? say('gate.clean', { lines: payload.lines, sections: payload.sections })
          : say('gate.problems', {
              problems: payload.problems,
              lines: payload.lines,
              sections: payload.sections,
            })}
      </p>
      {payload.checked.length === 0 ? null : (
        <p className="text-muted-foreground mt-2 font-mono text-xs wrap-anywhere">
          {say('gate.checked', { checked: payload.checked.join(', ') })}
        </p>
      )}
    </BentoPanel>
  )
}

export function Gate() {
  const say = useWording()
  const params = useParams()
  const root = decodeURIComponent(params['root'] ?? '')
  const gating = useGate(root)
  const { gate, project, run, takeDoor } = gating

  // Run as the screen opens: somebody who asked for the gate asked for it to run, and a
  // surface that showed nothing until a second press would be a report with an extra step.
  const opened = project !== null
  useEffect(() => {
    if (opened) run()
  }, [opened, run])

  const trailing = useMemo(
    () => (
      <Button size="sm" onClick={run} disabled={gate.kind === 'running'}>
        {say('gate.run')}
      </Button>
    ),
    [run, gate.kind, say],
  )

  return (
    <>
      <BentoHero
        backTo={projectPath(root)}
        backLabel={folderName(root)}
        title={say('gate.title')}
        subtitle={say('gate.about')}
        trailing={trailing}
      />
      <div className="flex flex-col gap-3">
        {gate.kind === 'running' ? (
          <p className="text-muted-foreground text-xs" data-testid="running">
            {say('gate.running')}
          </p>
        ) : null}
        {gate.kind === 'failed' ? (
          <BentoPanel contentClassName="p-6">
            <BentoEmptyState title={say('gate.failed', { reason: gate.reason })} />
          </BentoPanel>
        ) : null}
        {gate.kind === 'unreadable' ? (
          <BentoPanel contentClassName="p-6">
            <BentoEmptyState title={say('gate.unreadable', { reason: gate.reason })} />
          </BentoPanel>
        ) : null}
        {gate.kind === 'read' ? (
          <>
            <Counted payload={gate.payload} />
            <Report
              title={say('gate.title')}
              rows={gate.findings}
              onTake={takeDoor}
              mark="finding"
            />
            <Report title={say('gate.notes')} rows={gate.notes} onTake={takeDoor} mark="note" />
          </>
        ) : null}
      </div>
    </>
  )
}
