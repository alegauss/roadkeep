import {
  filterCounts,
  type KnownRoot,
  matchesFilter,
  ROW_FILTERS,
  tally,
  UNKNOWN_GATE,
  type GateVerdict,
  type MessageKey,
  type ProjectRow,
  type RowFilter,
  type RowStage,
} from '@rk/core'
import { IconFolder, IconInfoCircle, IconX } from '@tabler/icons-react'
import { Button } from '@viglet/viglet-design-system'
import {
  BENTO_TONES,
  BentoEmptyState,
  BentoHero,
  BentoPanel,
  bentoChipClass,
} from '@viglet/viglet-design-system/bento'
import { useCallback, useMemo, useState, type ReactNode } from 'react'

import { usePortfolio, type ReadingProgress, type Tried } from './usePortfolio'
import { useRoots, type RootsView } from './useRoots'
import { useWording } from './wording'

/**
 * The portfolio, at the root route (RG145) — the one screen this app exists for.
 *
 * `docs/design/Main.dc.html` is the drawing. Every column is a reader `core` already ships,
 * and this file decides only how they are arranged: the hero counts rows with `tally`, the
 * chips narrow what is loaded with `matchesFilter`, and each row is the `ProjectRow` a cold
 * start filled.
 *
 * **Rows and not tiles** (§RG63): a symptom is up to 120 characters and fits in no tile, so
 * the list is a table in a `BentoPanel`, in the record's order and never completion order.
 *
 * **A row still answering is pending, never zero** — block C's second criterion, drawn as
 * bars where the numbers will be. An unreadable row spans the counts and says why, with what
 * was tried behind a disclosure. A split engine is information and never an error, so its
 * verdict is drawn in the warning intent and the row stays a row.
 *
 * **The engine's verdict and the tier are the engine's words**, drawn as they came: they are
 * a payload's fields, and translating one would be this app rewording roadkeep. Everything
 * else a person reads is from the catalogue.
 *
 * Nothing opens when a row is clicked. The project surface is RG148's, and a row that led
 * nowhere would be a dead link.
 */

const FILTER_TEXT: Readonly<Record<RowFilter, MessageKey>> = {
  all: 'portfolio.filter.all',
  drifted: 'portfolio.filter.drifted',
  disagrees: 'portfolio.filter.disagrees',
  unreadable: 'portfolio.filter.unreadable',
}

const STAGE_TEXT: Readonly<Record<RowStage, MessageKey>> = {
  counting: 'portfolio.stage.counting',
  next: 'portfolio.stage.next',
}

const GATE_TEXT: Readonly<Record<GateVerdict, MessageKey>> = {
  unknown: 'portfolio.gate.unknown',
  clean: 'portfolio.gate.clean',
  drifted: 'portfolio.gate.drifted',
}

type Intent = 'on' | 'warn' | 'error' | null

const GATE_INTENT: Readonly<Record<GateVerdict, Intent>> = {
  unknown: null,
  clean: 'on',
  drifted: 'error',
}

/**
 * A tone for a project's chip, the same one every time for the same name. Decorative — the
 * chip is hidden from a screen reader and the name beside it says which project it is.
 */
function toneOf(name: string): (typeof BENTO_TONES)[number] {
  let sum = 0
  for (const character of name) sum = (sum * 31 + (character.codePointAt(0) ?? 0)) % 9973
  return BENTO_TONES[sum % BENTO_TONES.length] ?? 'slate'
}

/** A status pill in the design system's own intents. No intent is the neutral one. */
function Pill({ intent, children }: { readonly intent: Intent; readonly children: ReactNode }) {
  const tone = intent === null ? 'text-muted-foreground' : `bento-status bento-status-${intent}`
  const dot = intent === null ? 'bg-muted-foreground' : 'bento-status-dot'
  return (
    <span
      className={`inline-flex h-5 items-center gap-1.5 rounded-full border px-2 text-xs font-semibold ${tone}`}
    >
      <span aria-hidden="true" className={`size-1.5 rounded-full ${dot}`} />
      {children}
    </span>
  )
}

/**
 * The face a marker is drawn in, built once — `Marker`'s own, since a marker here is the
 * project's codepoint and nothing else. An object literal in the attribute would be a new
 * prop on every row.
 */
const MARKER_FACE = { fontFamily: 'var(--font-marker)' } as const

/** A marker's glyph, in the face every marker in this app is drawn in. */
function Glyph({ children }: { readonly children: string }) {
  return <span style={MARKER_FACE}>{children}</span>
}

/** Where a number will be, while it is still on its way. */
function Bar({ width }: { readonly width: string }) {
  return <span aria-hidden="true" className={`bg-muted block h-2 rounded-full ${width}`} />
}

function Chip({
  filter,
  count,
  active,
  onPick,
}: {
  readonly filter: RowFilter
  readonly count: number
  readonly active: boolean
  readonly onPick: (filter: RowFilter) => void
}) {
  const say = useWording()
  const choose = useCallback(() => {
    onPick(filter)
  }, [filter, onPick])

  return (
    <Button
      variant={active ? 'default' : 'outline'}
      size="sm"
      className="rounded-full"
      aria-pressed={active ? 'true' : 'false'}
      onClick={choose}
      data-testid={`filter-${filter}`}
    >
      {say(FILTER_TEXT[filter], { count })}
    </Button>
  )
}

function ProjectCell({ row, shared }: { readonly row: ProjectRow; readonly shared: boolean }) {
  const say = useWording()
  const unreadable = row.state === 'unreadable'
  const chip = unreadable
    ? 'text-muted-foreground border border-dashed'
    : `${bentoChipClass(toneOf(row.name))} text-white`

  return (
    <div className="flex min-w-0 items-center gap-3">
      <span
        aria-hidden="true"
        className={`flex size-8 shrink-0 items-center justify-center rounded-[10px] ${chip}`}
      >
        <IconFolder size={17} />
      </span>
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className={`truncate font-semibold ${unreadable ? 'text-muted-foreground' : ''}`}>
            {row.name}
          </span>
          {shared ? (
            <span className="bg-muted text-muted-foreground rounded px-1.5 text-[10.5px] font-semibold">
              {say('portfolio.worktree')}
            </span>
          ) : null}
        </div>
        <div className="text-muted-foreground truncate font-mono text-xs" title={row.path}>
          {row.path}
        </div>
      </div>
    </div>
  )
}

function BacklogCell({ row }: { readonly row: ProjectRow }) {
  const say = useWording()
  const counts = row.counts
  if (counts === null) {
    return (
      <div className="flex flex-col gap-1.5">
        <Bar width="w-20" />
        <Bar width="w-28" />
      </div>
    )
  }

  return (
    <div>
      <div className="font-semibold tabular-nums">
        {say('portfolio.open', { count: counts.total })}
      </div>
      <div className="text-muted-foreground mt-0.5 flex flex-wrap items-center gap-x-2 text-xs">
        {Object.entries(counts.markers).map(([marker, count]) => (
          <span key={marker} className="inline-flex items-center gap-1 tabular-nums">
            <Glyph>{marker}</Glyph>
            {count}
          </span>
        ))}
      </div>
      <div className="text-muted-foreground mt-0.5 text-xs">
        {say('portfolio.startable', { startable: counts.startable, waiting: counts.waiting })}
      </div>
      {counts.uncounted > 0 ? (
        <div className="text-muted-foreground text-xs">
          {say('portfolio.uncounted', { count: counts.uncounted })}
        </div>
      ) : null}
    </div>
  )
}

function NextCell({ row, settled }: { readonly row: ProjectRow; readonly settled: boolean }) {
  const say = useWording()
  const next = row.next
  if (next === null) {
    return settled ? (
      <span className="text-muted-foreground text-xs">{say('portfolio.next.missing')}</span>
    ) : (
      <Bar width="w-48" />
    )
  }
  if (next.id === null) {
    return (
      <span className="text-muted-foreground text-xs">
        {say('portfolio.next.none', { blocked: next.blocked })}
      </span>
    )
  }

  return (
    <div className="min-w-0">
      <div className="flex items-center gap-2">
        <span className="font-mono text-xs font-semibold">{next.id}</span>
        <Glyph>{next.status}</Glyph>
        <span className="bg-muted text-muted-foreground rounded px-1.5 text-[11px] font-semibold">
          {next.block}
        </span>
        {next.tier === '' ? null : (
          <span className="text-muted-foreground text-xs">
            {say('portfolio.tier', { tier: next.tier })}
          </span>
        )}
      </div>
      <div className="mt-0.5 line-clamp-2 text-[13px] [overflow-wrap:anywhere]">{next.symptom}</div>
    </div>
  )
}

function GateCell({ row }: { readonly row: ProjectRow }) {
  const say = useWording()
  const gate = row.gate ?? UNKNOWN_GATE
  const known = gate.verdict !== 'unknown'

  return (
    <div>
      <Pill intent={GATE_INTENT[gate.verdict]}>{say(GATE_TEXT[gate.verdict])}</Pill>
      <div className="text-muted-foreground mt-1 text-xs">
        {known
          ? say('portfolio.gate.findings', { count: gate.problems })
          : say('portfolio.gate.never')}
        {known && gate.stale ? ` · ${say('portfolio.gate.stale')}` : null}
      </div>
    </div>
  )
}

function EngineCell({ row }: { readonly row: ProjectRow }) {
  const say = useWording()
  const engine = row.engine
  if (engine === null) return <Bar width="w-24" />

  return (
    <div className="min-w-0">
      <div className="font-mono text-xs font-semibold">{engine.version}</div>
      <div className="mt-1 flex flex-wrap gap-1">
        <Pill intent={engine.agree ? 'on' : 'warn'}>{engine.verdict}</Pill>
        {engine.modified ? <Pill intent="warn">{say('portfolio.engine.modified')}</Pill> : null}
      </div>
      <div
        className="text-muted-foreground mt-1 truncate font-mono text-[11px]"
        title={engine.home}
      >
        {engine.home}
      </div>
    </div>
  )
}

/** What was tried, for a row that did not open: the command lines, and anything the engine said. */
function WhatWasTried({ row, tried }: { readonly row: ProjectRow; readonly tried: Tried }) {
  const say = useWording()
  const lines = (tried[row.path] ?? []).map((argv) => argv.join(' '))
  const argv = row.unreadable?.argv ?? []
  if (argv.length > 0) lines.push(argv.join(' '))
  const said = row.unreadable?.said ?? ''
  if (lines.length === 0 && said === '') return null

  return (
    <details className="text-xs">
      <summary className="text-primary cursor-pointer font-medium">
        {say('portfolio.tried')}
      </summary>
      <ul className="text-muted-foreground mt-1 flex flex-col gap-0.5 font-mono [overflow-wrap:anywhere]">
        {lines.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
      {said === '' ? null : (
        <pre className="text-muted-foreground mt-1 font-mono whitespace-pre-wrap [overflow-wrap:anywhere]">
          {said}
        </pre>
      )}
    </details>
  )
}

function Row({
  row,
  settled,
  shared,
  tried,
}: {
  readonly row: ProjectRow
  readonly settled: boolean
  /** Another row shares this one's git directory, which is what makes it one worktree of several. */
  readonly shared: boolean
  readonly tried: Tried
}) {
  const say = useWording()
  const cell = 'px-5 py-3 align-middle'

  if (row.state === 'unreadable') {
    return (
      <tr data-state={row.state} data-testid="portfolio-row" className="border-t">
        <td className={cell}>
          <ProjectCell row={row} shared={shared} />
        </td>
        <td className={cell} colSpan={3}>
          <div className="flex flex-col gap-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <Pill intent="error">{say('portfolio.unreadable')}</Pill>
              <span className="line-clamp-3 text-[13px] [overflow-wrap:anywhere]">
                {row.unreadable?.message}
              </span>
            </div>
            <WhatWasTried row={row} tried={tried} />
          </div>
        </td>
        <td className={`${cell} text-muted-foreground text-xs`}>{say('portfolio.kept')}</td>
      </tr>
    )
  }

  if (row.state === 'pending') {
    return (
      <tr data-state={row.state} data-testid="portfolio-row" className="border-t">
        <td className={cell}>
          <ProjectCell row={row} shared={shared} />
        </td>
        <td className={cell}>
          <BacklogCell row={row} />
        </td>
        <td className={cell}>
          <span className="text-muted-foreground flex items-center gap-2 text-[13px]">
            <span aria-hidden="true" className="bg-primary size-1.5 rounded-full" />
            {say('portfolio.pending')}
          </span>
        </td>
        <td className={cell}>
          <Bar width="w-16" />
        </td>
        <td className={cell}>
          <Bar width="w-20" />
        </td>
      </tr>
    )
  }

  return (
    <tr data-state={row.state} data-testid="portfolio-row" className="border-t">
      <td className={cell}>
        <ProjectCell row={row} shared={shared} />
      </td>
      <td className={cell}>
        <BacklogCell row={row} />
      </td>
      <td className={cell}>
        <NextCell row={row} settled={settled} />
      </td>
      <td className={cell}>
        <GateCell row={row} />
      </td>
      <td className={cell}>
        <EngineCell row={row} />
      </td>
    </tr>
  )
}

function Subtitle({
  rows,
  progress,
}: {
  readonly rows: readonly ProjectRow[]
  readonly progress: ReadingProgress | null
}) {
  const say = useWording()
  const counted = tally(rows)
  return (
    <span className="flex flex-col gap-0.5">
      <span>
        {say('portfolio.tally', {
          read: counted.read,
          pending: counted.pending,
          unreadable: counted.unreadable,
        })}
      </span>
      {progress === null ? null : (
        <span data-testid="portfolio-progress">
          {say('portfolio.progress', {
            stage: say(STAGE_TEXT[progress.stage]),
            done: progress.done,
            total: progress.total,
          })}
        </span>
      )}
    </span>
  )
}

function RootChip({
  root,
  onRemove,
}: {
  readonly root: KnownRoot
  readonly onRemove: (path: string) => void
}) {
  const say = useWording()
  const remove = useCallback(() => {
    onRemove(root.path)
  }, [root.path, onRemove])

  return (
    <li
      className="bg-muted/60 flex items-center gap-2 rounded-full py-0.5 pr-1 pl-3 text-xs"
      data-testid="root"
      data-presence={root.presence}
    >
      <span className="font-mono">{root.path}</span>
      <span className="text-muted-foreground">{say('roots.depth', { depth: root.depth })}</span>
      {root.presence === 'missing' ? <Pill intent="warn">{say('roots.missing')}</Pill> : null}
      <Button
        variant="ghost"
        size="icon"
        className="size-6 rounded-full"
        aria-label={say('roots.remove', { path: root.path })}
        onClick={remove}
      >
        <IconX aria-hidden="true" size={14} />
      </Button>
    </li>
  )
}

/**
 * Where the window looks, named (RG146): each root with its depth, a missing one marked and
 * kept, and the way to stop looking under one. Nothing while the list is still being asked.
 */
function RootStrip({
  view,
  onRemove,
}: {
  readonly view: RootsView
  readonly onRemove: (path: string) => void
}) {
  const say = useWording()
  if (view.kind !== 'known' || view.roots.length === 0) return null

  return (
    <ul aria-label={say('roots.label')} className="flex flex-wrap items-center gap-2">
      {view.roots.map((root) => (
        <RootChip key={root.path} root={root} onRemove={onRemove} />
      ))}
    </ul>
  )
}

export function Portfolio() {
  const say = useWording()
  const { view, rescan } = usePortfolio()
  const roots = useRoots(rescan)
  const unnamed = roots.view.kind === 'known' && roots.view.roots.length === 0
  const [filter, setFilter] = useState<RowFilter>('all')
  const pick = useCallback((next: RowFilter) => {
    setFilter(next)
  }, [])

  const rows = view.kind === 'listed' ? view.rows : null
  const counts = useMemo(() => (rows === null ? null : filterCounts(rows)), [rows])
  const families = useMemo(() => {
    const sizes = new Map<string, number>()
    for (const row of rows ?? []) {
      if (row.commonDir !== null) sizes.set(row.commonDir, (sizes.get(row.commonDir) ?? 0) + 1)
    }
    return sizes
  }, [rows])
  const shown = useMemo(
    () => (rows === null ? [] : rows.filter((row) => matchesFilter(row, filter))),
    [rows, filter],
  )

  // Built once per change and not in the attribute: the hero is handed an element, and one
  // made in the prop is a new one every render. Nothing to offer a page with no bridge.
  const bridged = view.kind !== 'absent'
  const add = roots.add
  const actions = useMemo(
    () =>
      bridged ? (
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={rescan} data-testid="rescan">
            {say('roots.rescan')}
          </Button>
          <Button onClick={add} data-testid="add-root">
            {say('roots.add')}
          </Button>
        </div>
      ) : null,
    [bridged, rescan, add, say],
  )

  let title = say('portfolio.title.unknown')
  let subtitle: ReactNode = say('portfolio.asking')
  if (view.kind === 'listed') {
    title = say('portfolio.title', { count: view.rows.length })
    subtitle = <Subtitle rows={view.rows} progress={view.progress} />
  } else if (view.kind === 'absent') {
    subtitle = say('transport.absent')
  } else if (view.kind === 'failed') {
    subtitle = say('portfolio.failed', { reason: view.reason })
  }

  return (
    <>
      <BentoHero
        eyebrow={say('portfolio.kicker')}
        title={title}
        subtitle={subtitle}
        trailing={actions}
      />

      <RootStrip view={roots.view} onRemove={roots.remove} />

      {unnamed ? (
        <BentoEmptyState title={say('roots.none')} description={say('roots.none.hint')} />
      ) : null}

      {!unnamed && view.kind === 'listed' && view.rows.length === 0 ? (
        <BentoEmptyState title={say('portfolio.none')} description={say('portfolio.none.hint')} />
      ) : null}

      {view.kind === 'listed' && counts !== null && view.rows.length > 0 ? (
        <>
          <div className="flex flex-wrap items-center gap-2">
            <fieldset className="m-0 flex flex-wrap items-center gap-2 border-0 p-0">
              <legend className="sr-only">{say('portfolio.filter.label')}</legend>
              {ROW_FILTERS.map((one) => (
                <Chip
                  key={one}
                  filter={one}
                  count={counts[one]}
                  active={one === filter}
                  onPick={pick}
                />
              ))}
            </fieldset>
            <span className="text-muted-foreground ml-auto text-xs">{say('portfolio.order')}</span>
          </div>

          <BentoPanel className="overflow-hidden" contentClassName="p-0 overflow-x-auto">
            <table className="w-full min-w-[56rem] table-fixed border-collapse text-left text-sm">
              <thead>
                <tr className="text-muted-foreground text-[11px] font-semibold tracking-wide uppercase">
                  <th scope="col" className="w-[26%] px-5 py-3 font-semibold">
                    {say('portfolio.column.project')}
                  </th>
                  <th scope="col" className="w-[16%] px-5 py-3 font-semibold">
                    {say('portfolio.column.backlog')}
                  </th>
                  <th scope="col" className="px-5 py-3 font-semibold">
                    {say('portfolio.column.next')}
                  </th>
                  <th scope="col" className="w-[13%] px-5 py-3 font-semibold">
                    {say('portfolio.column.gate')}
                  </th>
                  <th scope="col" className="w-[15%] px-5 py-3 font-semibold">
                    {say('portfolio.column.engine')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {shown.map((row) => (
                  <Row
                    key={row.path}
                    row={row}
                    settled={view.progress === null}
                    shared={row.commonDir !== null && (families.get(row.commonDir) ?? 0) > 1}
                    tried={view.tried}
                  />
                ))}
              </tbody>
            </table>
          </BentoPanel>
        </>
      ) : null}

      <p className="text-muted-foreground flex items-center gap-2 text-xs">
        <IconInfoCircle aria-hidden="true" size={14} />
        {say('portfolio.footnote')}
      </p>
    </>
  )
}
