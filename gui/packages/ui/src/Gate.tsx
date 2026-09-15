import { counted, refusalOf, type GateHealth, type Gated, type LintPayload } from '@rk/core'
import { Button } from '@viglet/viglet-design-system'
import { BentoEmptyState, BentoPanel } from '@viglet/viglet-design-system/bento'
import { useCallback, useEffect, type ReactNode } from 'react'

import { DoorRow } from './Doors'
import { Caption } from './forms'
import { Pill } from './marks'
import { useExplained, type Explained, type Explaining } from './useExplained'
import { useGate, worthRunning } from './useGate'
import { useWhen, useWording } from './wording'

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

/**
 * What a code means, in the engine's own words, under the finding that carries it (RG258).
 *
 * The message on a row is about one line; the code is a class, and what `ref.unresolved` is —
 * whether it means different things in different places, what it waits on — is what `explain`
 * answers. Its doors are not drawn: the finding's own remedy already offers them filled in
 * for this line, while a class's carry a blank wherever this finding has a value.
 */
function Explains({ explained }: { readonly explained: Explained | undefined }) {
  const say = useWording()
  if (explained === undefined) return null
  if (explained.kind === 'asking') {
    return <span className="text-muted-foreground text-xs">{say('gate.explain.asking')}</span>
  }
  if (explained.kind === 'failed') {
    return <span className="text-muted-foreground text-xs">{say('gate.explain.failed')}</span>
  }

  const { explanation } = explained
  return (
    <span className="flex flex-col gap-1 text-xs" data-testid="explained">
      {explanation.cause === '' ? null : <span className="wrap-anywhere">{explanation.cause}</span>}
      {explanation.varies === null || explanation.varies === '' ? null : (
        <span className="text-muted-foreground wrap-anywhere">{explanation.varies}</span>
      )}
      {explanation.awaits === '' ? null : (
        <span className="text-muted-foreground wrap-anywhere">
          {say('gate.awaits', { awaits: explanation.awaits })}
        </span>
      )}
    </span>
  )
}

/** One finding, with what closes it under it. */
function Finding({
  gated,
  onTake,
  mark,
  explaining,
}: {
  readonly gated: Gated
  readonly onTake: Taking
  /** Which report this row is in: a note is not a finding, and neither is drawn as one. */
  readonly mark: string
  /**
   * What a code means, where this build can answer it (RG258). Null where `explain` is not
   * callable: a disclosure that opens on a refusal is a control that lies.
   */
  readonly explaining: Explaining | null
}) {
  const say = useWording()
  const { finding } = gated
  const code = finding.code
  const asking = useCallback(() => {
    explaining?.explain(code)
  }, [explaining, code])

  return (
    <li className="border-t first:border-t-0" data-testid={mark}>
      <div className="flex flex-col gap-1 px-4 py-3">
        <span className="flex flex-wrap items-center gap-2">
          {explaining === null ? (
            <Pill intent="error">{finding.code}</Pill>
          ) : (
            <details className="text-xs" data-testid="explain" onToggle={asking}>
              <summary className="cursor-pointer list-none">
                <Pill intent="error">{finding.code}</Pill>
              </summary>
              <span className="mt-1 block">
                <Explains explained={explaining.explained.get(finding.code)} />
              </span>
            </details>
          )}
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
  explaining,
}: {
  readonly title: ReactNode
  readonly rows: readonly Gated[]
  readonly onTake: Taking
  readonly mark: string
  readonly explaining: Explaining | null
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
            explaining={explaining}
          />
        ))}
      </ul>
    </BentoPanel>
  )
}

/**
 * The verdict on record, drawn where the files have not moved under it (RG185).
 *
 * The ledger holds what the gate said and when, never its findings — so this is a count and
 * a date, and the rows come from a run. `unknown` is the honest first state and says so.
 */
function Held({ health }: { readonly health: GateHealth }) {
  const say = useWording()
  const when = useWhen()

  return (
    <BentoPanel contentClassName="p-5">
      <p className="text-sm" data-testid="held">
        {health.verdict === 'unknown'
          ? say('gate.never')
          : say(health.verdict === 'clean' ? 'gate.held.clean' : 'gate.held.drifted', {
              count: health.problems,
            })}
      </p>
      {health.taken === null ? null : (
        <p className="text-muted-foreground mt-2 text-xs">
          {say('gate.taken', { taken: when(health.taken) })}
        </p>
      )}
      {health.stale ? (
        <p className="text-muted-foreground mt-2 text-xs" data-testid="stale">
          {say('gate.stale')}
        </p>
      ) : null}
    </BentoPanel>
  )
}

/** What the run counted, which is the engine's sentence about its own read. */
function Counted({ payload }: { readonly payload: LintPayload }) {
  const say = useWording()
  // What was read, as a row of fragments each agreeing with its own number (RG216): one
  // sentence carrying both said `1 linhas e 1 seções`.
  const read = counted(say, [
    ['counts.lines', payload.lines],
    ['counts.sections', payload.sections],
  ])
  return (
    <BentoPanel contentClassName="p-5">
      <p className="text-sm" data-testid="counted">
        {payload.clean
          ? say('gate.clean', { counted: read })
          : say('gate.problems', { count: payload.problems, counted: read })}
      </p>
      {payload.checked.length === 0 ? null : (
        <p className="text-muted-foreground mt-2 font-mono text-xs wrap-anywhere">
          {say('gate.checked', { checked: payload.checked.join(', ') })}
        </p>
      )}
    </BentoPanel>
  )
}

/**
 * The gate, as a tab of the project it is about (RG255).
 *
 * **What those files say about themselves is part of the project**, not a screen beside it: a
 * reader who saw six findings on a portfolio row looks along the tabs for them, and a verb in
 * the hero read as a run to start rather than as the place the findings already are.
 *
 * The button moves in here, above the report, for the same reason: it belongs to what it
 * runs. Everything below it is what this screen has always drawn.
 */
export function GateTab({ root }: { readonly root: string }) {
  const say = useWording()
  const gating = useGate(root)
  const { gate, project, refused, run, takeDoor } = gating
  // What a code means is offered only where this build answers `explain` (RG258): a
  // disclosure that opens on a refusal is a control that lies.
  const explaining = useExplained(root, project)
  const callable =
    project !== null &&
    project.capabilities.kind === 'known' &&
    project.capabilities.byVerb.explain.callable

  // Run as the screen opens only where a run would say something new (RG185, RG254), which
  // `worthRunning` decides. A person pressing Run the gate is a person saying they want it
  // run whatever the ledger holds.
  const opened = project !== null
  const running = worthRunning(gate)
  useEffect(() => {
    if (opened && running) run()
  }, [opened, running, run])

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <Button size="sm" onClick={run} disabled={gate.kind === 'running'}>
          {say('gate.run')}
        </Button>
        <span className="text-muted-foreground text-xs">{say('gate.about')}</span>
      </div>
      {gate.kind === 'running' ? (
        <p className="text-muted-foreground text-xs" data-testid="running">
          {say('gate.running')}
        </p>
      ) : null}
      {gate.kind === 'failed' ? (
        <BentoPanel contentClassName="p-6">
          <BentoEmptyState title={say('gate.failed', { reason: refusalOf(gate.reason, say) })} />
        </BentoPanel>
      ) : null}
      {gate.kind === 'unreadable' ? (
        <BentoPanel contentClassName="p-6">
          <BentoEmptyState title={say('gate.unreadable', { reason: gate.reason })} />
        </BentoPanel>
      ) : null}
      {/*
        Above the report and not inside it (RG260): the door that failed belongs to a finding
        the run below may or may not still hold, and what a reader needs first is that the
        report they are about to read is unchanged because nothing ran.
      */}
      {refused === null ? null : (
        <p className="text-sm font-medium" data-testid="door-failed">
          {say('door.failed', { reason: refusalOf(refused, say) })}
        </p>
      )}
      {gate.kind === 'held' ? <Held health={gate.health} /> : null}
      {gate.kind === 'read' ? (
        <>
          <Counted payload={gate.payload} />
          <Report
            title={say('gate.title')}
            rows={gate.findings}
            onTake={takeDoor}
            mark="finding"
            explaining={callable ? explaining : null}
          />
          <Report
            title={say('gate.notes')}
            rows={gate.notes}
            onTake={takeDoor}
            mark="note"
            explaining={callable ? explaining : null}
          />
        </>
      ) : null}
    </div>
  )
}
