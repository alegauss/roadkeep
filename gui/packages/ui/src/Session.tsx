import {
  actsIn,
  arrivedSince,
  drawnState,
  editedIn,
  foldedNotes,
  FOLLOWING,
  landingBetween,
  onDisk,
  scrolledTo,
  type Act,
  type Actionable,
  type BriefPayload,
  type Change,
  type ClaimsPayload,
  type DiskStanding,
  type DrawnState,
  type Handed,
  type HandedOver,
  type Follow,
  type Edited,
  type EditedFile,
  type GovernedFile,
  type MessageKey,
  type MovedPath,
  type Reading,
  type SessionOutcome,
  type SessionRecord,
  type SessionState,
} from '@rk/core'
import { Button, Textarea, Tree, treeFromPaths, type TreeNode } from '@viglet/viglet-design-system'
import { BentoEmptyState, BentoHero, BentoPanel } from '@viglet/viglet-design-system/bento'
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type MouseEvent,
  type ReactNode,
} from 'react'
import { useParams } from 'react-router-dom'

import { getBridge } from './bridge'
import { FileSheet } from './file-sheet'
import { PanelTitle } from './forms'
import { HeroActions } from './hero'
import { Glyph, Pill, type Intent } from './marks'
import { useSessionNotes } from './preferring'
import { ProjectTrail } from './trail'
import { useEditedAt } from './useEditedAt'
import { useRegionHeight } from './useRegionHeight'
import { useSession } from './useSession'
import { useWhen, useWording } from './wording'

/**
 * One session beside the line it was handed (RG153). `docs/design/Sessao.dc.html` is the
 * drawing, reached from Hand to Claude Code on the task.
 *
 * **Three columns, and the middle one is the session's own words.** What was handed over is
 * the brief it was started from, counted and never rewritten. The stream is `actsIn` over the
 * raw lines: text, then each tool on what it was called on, a roadkeep call marked and an act
 * that touched a governed file edged — both by what the project said its own look like — and
 * every raw line stays one disclosure away.
 *
 * **What moved is read off the files, not off the stream.** A session can report shipping a
 * line it did not ship, so the line is briefed again on every move and `landingBetween`
 * compares that with what the session was handed. Where the two disagree, this column is the
 * one that is true. The files it edited are listed off the stream (RG243) and each is then
 * asked of the disk (RG244), so that list is held to the same rule.
 *
 * Stopping kills the process and leaves the claim to the registry's expiry — the session may
 * have moved the line, and releasing it here would undo a state nobody reviewed.
 */

/**
 * Where the session stands, in this app's words for the engine's states. Exported because the
 * list of what is running says the same thing about each one, and two tables would drift.
 */
export const STATE_TEXT: Readonly<Record<DrawnState, MessageKey>> = {
  starting: 'session.state.starting',
  running: 'session.state.running',
  done: 'session.state.done',
  waiting: 'session.state.waiting',
  unshipped: 'session.state.unshipped',
  failed: 'session.state.failed',
  cancelled: 'session.state.cancelled',
  unavailable: 'session.state.unavailable',
}

/**
 * Waiting and stopped short are the warning intent (RG268): the one a reader already reads as
 * their move, which both are — a refused call to grant, a line the turn did not finish.
 */
export const STATE_INTENT: Readonly<Record<DrawnState, Intent>> = {
  starting: null,
  running: null,
  done: 'on',
  waiting: 'warn',
  unshipped: 'warn',
  failed: 'error',
  cancelled: 'warn',
  unavailable: 'error',
}

/** The raw line, one disclosure away from every act it was read into. */
function Raw({ line }: { readonly line: string }) {
  const say = useWording()
  return (
    <details className="mt-1 text-[11px]">
      <summary className="text-muted-foreground cursor-pointer">{say('session.act.raw')}</summary>
      <pre className="bg-muted mt-1 max-h-40 overflow-auto rounded p-2 text-[11px] whitespace-pre-wrap">
        {line}
      </pre>
    </details>
  )
}

function Spoken({ act }: { readonly act: Act }) {
  const say = useWording()

  if (act.kind === 'said') {
    return <p className="text-[13px] leading-relaxed whitespace-pre-wrap">{act.text}</p>
  }
  if (act.kind === 'used') {
    return (
      <div className="flex flex-col gap-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-xs font-semibold">{act.tool}</span>
          {act.on === '' ? null : (
            <span className="text-muted-foreground min-w-0 font-mono text-xs wrap-anywhere">
              {act.on}
            </span>
          )}
          {act.roadkeep ? <Pill intent="on">{say('session.act.roadkeep')}</Pill> : null}
        </div>
        {act.governed.length === 0 ? null : (
          <span className="text-xs font-medium">
            {say('session.act.governed', { files: act.governed.join(', ') })}
          </span>
        )}
      </div>
    )
  }
  if (act.kind === 'returned') {
    return (
      <div className="flex flex-col gap-1">
        {act.ok ? null : <Pill intent="error">{say('session.act.failed')}</Pill>}
        <pre className="text-muted-foreground max-h-32 overflow-auto text-[12px] whitespace-pre-wrap">
          {act.text}
        </pre>
      </div>
    )
  }
  return <span className="text-muted-foreground font-mono text-xs">{act.about}</span>
}

/** One act, edged where it touched a file this project governs. */
function ActRow({ act }: { readonly act: Act }) {
  const touched = act.kind === 'used' && act.governed.length > 0
  return (
    <li
      // Named by its seq, so an edit in the file viewer leads back to the act that made it
      // (RG246).
      id={`act-${String(act.seq)}`}
      className={`border-t px-4 py-2.5 first:border-t-0 ${touched ? 'border-l-primary border-l-2' : ''}`}
      data-testid="act"
      data-kind={act.kind}
    >
      <Spoken act={act} />
      <Raw line={act.line} />
    </li>
  )
}

/**
 * A run of notes folded into one quiet row (RG208), counted so the stream is still accounted
 * for, and each note with its raw line one disclosure away.
 */
function FoldedRow({ notes }: { readonly notes: readonly Act[] }) {
  const say = useWording()
  return (
    <li
      className="border-t px-4 py-2 first:border-t-0"
      data-testid="folded"
      data-count={notes.length}
    >
      <details className="text-[11px]">
        <summary className="text-muted-foreground cursor-pointer">
          {say('session.notes.folded', { count: notes.length })}
        </summary>
        <ul className="mt-1.5 flex flex-col gap-1.5">
          {notes.map((note) => (
            <li key={note.seq} data-testid="act" data-kind={note.kind}>
              <Spoken act={note} />
              <Raw line={note.line} />
            </li>
          ))}
        </ul>
      </details>
    </li>
  )
}

/**
 * The one sentence a session is known by, whichever it was handed (RG263).
 *
 * A line's symptom and a finding's message are the same thing at two moments: what is wrong,
 * in the engine's own words. Drawn where a reader looks for the name of what is running.
 */
export function saidOf(handed: Handed): string {
  return handed.kind === 'line' ? handed.brief.symptom : handed.finding.message
}

/** A line's brief, counted: what the session was told, and none of it rewritten. */
function HandedLine({ brief }: { readonly brief: BriefPayload }) {
  const say = useWording()
  const claimed = brief.claimed

  return (
    <ul className="flex flex-col gap-1.5 text-[13px]">
      {claimed === null ? null : (
        <li className="flex items-center gap-1.5">
          <Glyph>{claimed.from}</Glyph>
          <span>{say('session.claim', { from: claimed.from, to: claimed.to })}</span>
        </li>
      )}
      <li>
        {brief.section === null
          ? say('session.handed.nodesign')
          : say('session.handed.design', { count: brief.section.words })}
      </li>
      <li>{say('session.handed.deps', { count: brief.deps.length })}</li>
      <li>{say('session.handed.criteria', { count: brief.doneWhen.length })}</li>
      <li>{say('session.handed.bounds', { count: brief.nonGoals.length })}</li>
    </ul>
  )
}

/**
 * A gate finding and the command it was told to run (RG263).
 *
 * The counts above are a line's facts and a finding has none of them, so this says what it
 * does have: the code, where it is, and the door — the argv as the engine wrote it, blanks
 * and all, which is what makes it readable as a command somebody could have run by hand.
 */
function HandedFinding({
  finding,
  argv,
}: {
  readonly finding: Actionable
  readonly argv: readonly string[]
}) {
  return (
    <ul className="flex flex-col gap-1.5 text-[13px]">
      <li className="flex flex-wrap items-center gap-1.5">
        <Pill intent="warn">{finding.code}</Pill>
        {finding.where === '' ? null : (
          <span className="text-muted-foreground font-mono text-xs">{finding.where}</span>
        )}
      </li>
      <li className="wrap-anywhere">{finding.message}</li>
      {/* The engine's own command line, drawn as the door row draws it: a payload's words,
          untranslated, with no sentence of this app's around them. */}
      <li className="text-muted-foreground font-mono text-xs wrap-anywhere">{argv.join(' ')}</li>
    </ul>
  )
}

/** What was handed over: a line's brief or a gate finding, counted and not rewritten. */
function Handed({ record }: { readonly record: SessionRecord }) {
  const say = useWording()
  const handed = record.handed

  return (
    <BentoPanel contentClassName="p-5">
      <PanelTitle>
        {say(handed.kind === 'line' ? 'session.handed' : 'session.handed.finding')}
      </PanelTitle>
      {handed.kind === 'line' ? (
        <HandedLine brief={handed.brief} />
      ) : (
        <HandedFinding finding={handed.finding} argv={handed.argv} />
      )}
      <p className="text-muted-foreground mt-3 text-xs wrap-anywhere">
        {say('session.handed.agent', {
          command: record.agent.command.join(' '),
          version: record.agent.version,
        })}
      </p>
    </BentoPanel>
  )
}

/** One change to the line, in the engine's own values. */
function ChangeSaid({ change }: { readonly change: Change }) {
  const say = useWording()
  switch (change.kind) {
    case 'marker':
      return <>{say('session.change.marker', { from: change.from, to: change.to })}</>
    case 'design':
      return (
        <>
          {say(
            change.to === 'written'
              ? 'session.change.design.written'
              : 'session.change.design.deleted',
          )}
        </>
      )
    case 'shipped':
      return <>{say('session.change.shipped')}</>
    case 'symptom':
      return <>{say('session.change.symptom')}</>
    case 'why':
      return <>{say('session.change.why')}</>
    case 'deps':
      return (
        <>
          {change.added.length === 0
            ? null
            : say('session.change.depsAdded', { ids: change.added.join(', ') })}
          {change.dropped.length === 0
            ? null
            : say('session.change.depsDropped', { ids: change.dropped.join(', ') })}
        </>
      )
    default:
      return <>{say('session.change.left', { said: change.said })}</>
  }
}

/** When each governed file last changed, written in the language the window speaks. */
function Files({ files }: { readonly files: readonly GovernedFile[] }) {
  const say = useWording()
  const when = useWhen()
  if (files.length === 0) return null

  return (
    <section className="mt-4" data-testid="files">
      <PanelTitle>{say('session.files')}</PanelTitle>
      <ul className="flex flex-col gap-1 text-xs">
        {files.map((file) => (
          <li key={file.path} className="flex flex-col">
            <span className="font-mono wrap-anywhere">{file.path}</span>
            <span className="text-muted-foreground">
              {file.changed === '' ? say('session.file.never') : when(file.changed)}
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}

/** What the disk says about an edited file, for each place it can stand (RG244). */
const STANDING_TEXT: Readonly<Record<Exclude<DiskStanding, 'unasked' | 'changed'>, MessageKey>> = {
  outside: 'session.edited.outside',
  missing: 'session.edited.missing',
  unchanged: 'session.edited.unchanged',
}

/** One edited file's standing on disk, or nothing before the disk has answered for it. */
function DiskSaid({
  standing,
  changed,
}: {
  readonly standing: DiskStanding
  readonly changed: string
}) {
  const say = useWording()
  const when = useWhen()
  if (standing === 'unasked') return null
  if (standing === 'changed') return <>{say('session.edited.changed', { when: when(changed) })}</>
  return <>{say(STANDING_TEXT[standing])}</>
}

/**
 * The key `Tree` addresses a path by: its segments, empty ones dropped, joined with `/` (RG265).
 *
 * Not a second reading of what a path is. Both lists arrive spelled by the shell with forward
 * slashes, and this is `treeFromPaths`'s own rule said once more so a leaf can be found again
 * by the key the tree hands back — a path with a leading slash would otherwise miss its row.
 */
function treeKey(path: string): string {
  return path
    .split('/')
    .filter((segment) => segment !== '')
    .join('/')
}

/** Every folder in a built tree, by its key: what is held open unless the reader closed it. */
function foldersIn(nodes: readonly TreeNode[], parent = ''): string[] {
  return nodes.flatMap((node) => {
    const key = parent === '' ? node.id : `${parent}/${node.id}`
    const under = node.children ?? []
    return under.length === 0 ? [] : [key, ...foldersIn(under, key)]
  })
}

/** One file a tree holds: where it sits, what opening it asks for, and what its row says. */
interface Leaf {
  /** Where it is drawn, spelled with forward slashes. */
  readonly at: string
  /** What the viewer asks the disk for, which is the path as it was first named. */
  readonly path: string
  /** Which list it is a row of, so a row is found by what it is and not where it sits. */
  readonly list: 'edited-file' | 'moved-file'
  /** Where the disk has it, for an edited file; a moved file has only moved. */
  readonly standing?: string
  /** What the row says under its name. */
  readonly facts: ReactNode
}

/** A file's row in the tree: its own name, what the list says of it, and what it is. */
function LeafLabel({ name, leaf }: { readonly name: string; readonly leaf: Leaf }) {
  return (
    <span
      className="flex min-w-0 flex-col gap-0.5 py-0.5 whitespace-normal"
      data-testid={leaf.list}
      data-path={leaf.path}
      data-standing={leaf.standing}
    >
      <span className="wrap-anywhere">{name}</span>
      <span className="flex flex-col gap-0.5 font-sans">{leaf.facts}</span>
    </span>
  )
}

/** The same tree with each file drawn as its list draws it, under the name its segment gives. */
function labelled(
  nodes: readonly TreeNode[],
  leaves: ReadonlyMap<string, Leaf>,
  parent = '',
): TreeNode[] {
  return nodes.map((node) => {
    const key = parent === '' ? node.id : `${parent}/${node.id}`
    const under = node.children ?? []
    if (under.length > 0) return { ...node, children: labelled(under, leaves, key) }
    const leaf = leaves.get(key)
    return leaf === undefined ? node : { ...node, label: <LeafLabel name={node.id} leaf={leaf} /> }
  })
}

/** Nothing closed, so every folder a session touches turns up open. */
const NONE_CLOSED: ReadonlySet<string> = new Set()

/**
 * A list of files as a tree of folders, from the design system (RG265, VDS167).
 *
 * **The branching and the keyboard are the package's**: roles, levels, one tab stop and the arrow
 * keys, owned there once for every product that draws a hierarchy. What stays here is the row.
 *
 * **Open unless the reader closed it.** A folder is held by what the reader shut rather than by
 * what they opened, because files arrive while the session runs — a folder that turned up closed
 * would hide the file that just moved in it, which is the one somebody is watching for.
 */
function FileTree({
  label,
  leaves,
  onOpen,
}: {
  readonly label: string
  readonly leaves: readonly Leaf[]
  readonly onOpen: (path: string) => void
}) {
  const [closed, setClosed] = useState<ReadonlySet<string>>(NONE_CLOSED)
  const byKey = useMemo(() => new Map(leaves.map((leaf) => [treeKey(leaf.at), leaf])), [leaves])
  const built = useMemo(() => treeFromPaths(leaves.map((leaf) => leaf.at)), [leaves])
  const nodes = useMemo(() => labelled(built, byKey), [built, byKey])
  const folders = useMemo(() => foldersIn(built), [built])
  const expanded = useMemo(() => folders.filter((key) => !closed.has(key)), [folders, closed])
  const changed = useCallback(
    (next: readonly string[]) => {
      const open = new Set(next)
      setClosed(new Set(folders.filter((key) => !open.has(key))))
    },
    [folders],
  )
  // A folder is chosen too, and opens and closes by itself; only a file has anything to show.
  const chosen = useCallback(
    (key: string) => {
      const leaf = byKey.get(key)
      if (leaf !== undefined) onOpen(leaf.path)
    },
    [byKey, onOpen],
  )

  return (
    <Tree
      // Folders and files are both segments of a path, which this app draws monospaced wherever
      // it draws one; a folder in the package's default face read as a heading over its files.
      className="-mx-1.5 font-mono text-xs"
      label={label}
      nodes={nodes}
      expanded={expanded}
      onExpandedChange={changed}
      onSelect={chosen}
    />
  )
}

/** What a file's row says under its name: the calls, the marks, and where the disk has it. */
function EditedFacts({
  file,
  read,
  changed,
}: {
  readonly file: Edited
  readonly read: ReturnType<typeof onDisk>
  readonly changed: string
}) {
  const say = useWording()
  return (
    <>
      <span className="text-muted-foreground flex flex-wrap items-center gap-1.5 text-xs">
        {say('session.edited.calls', { count: file.calls })}
        {file.governed ? <Pill intent="on">{say('session.edited.governed')}</Pill> : null}
        {file.failed ? <Pill intent="error">{say('session.edited.failed')}</Pill> : null}
      </span>
      {read.standing === 'unasked' ? null : (
        <span className="text-muted-foreground flex flex-wrap items-center gap-1.5 text-xs">
          <DiskSaid standing={read.standing} changed={changed} />
          {read.disagrees ? <Pill intent="warn">{say('session.edited.disagrees')}</Pill> : null}
        </span>
      )}
    </>
  )
}

/**
 * The files the session edited, off its own calls and then asked of the disk (RG243, RG244).
 *
 * Every edit call names its path, so the code a session changed is listed rather than found by
 * reading the stream. **The list is the session's word and each row's standing is the disk's**,
 * the rule this column keeps for the backlog: a call that reported success on a file the disk
 * has not changed since the session started is drawn as the disagreement it is. Each row opens
 * the file as the disk holds it now (RG245).
 *
 * Drawn as a tree since RG265, but a file the shell calls outside the project is not in it: it
 * has no root to sit under, so it stays a row of its own below, spelled the way it was named.
 */
function EditedFiles({
  edited,
  disk,
  started,
  onOpen,
}: {
  readonly edited: readonly Edited[]
  readonly disk: ReadonlyMap<string, EditedFile>
  readonly started: string
  readonly onOpen: (path: string) => void
}) {
  const say = useWording()
  // Inside unless the shell said otherwise. A file the disk has not answered for is drawn where
  // its own name puts it, and moves into place when the answer shortens it.
  const inside = useMemo(
    () => edited.filter((file) => disk.get(file.path)?.inside !== false),
    [edited, disk],
  )
  const outside = edited.filter((file) => disk.get(file.path)?.inside === false)
  const leaves = useMemo(
    () =>
      inside.map((file): Leaf => {
        const at = disk.get(file.path)
        const read = onDisk(file, at, started)
        return {
          at: at?.shown ?? file.path,
          path: file.path,
          list: 'edited-file',
          standing: read.standing,
          facts: <EditedFacts file={file} read={read} changed={at?.changed ?? ''} />,
        }
      }),
    [inside, disk, started],
  )
  // One handler for every row outside the project, reading which file off the button pressed.
  const openOutside = useCallback(
    (event: MouseEvent<HTMLButtonElement>) => {
      onOpen(event.currentTarget.dataset['path'] ?? '')
    },
    [onOpen],
  )

  return (
    <section data-testid="edited">
      <PanelTitle>{say('session.edited')}</PanelTitle>
      {edited.length === 0 ? (
        <p className="text-muted-foreground text-xs">{say('session.edited.none')}</p>
      ) : (
        <>
          <p className="text-muted-foreground mb-1.5 text-xs">{say('session.edited.about')}</p>
          {leaves.length === 0 ? null : (
            <FileTree label={say('session.edited')} leaves={leaves} onOpen={onOpen} />
          )}
          {outside.length === 0 ? null : (
            <ul className="mt-1.5 flex flex-col gap-1.5 text-xs">
              {outside.map((file) => {
                const at = disk.get(file.path)
                const read = onDisk(file, at, started)
                const shown = at?.shown ?? file.path
                return (
                  <li
                    key={file.path}
                    className="flex flex-col gap-0.5"
                    data-testid="edited-file"
                    data-path={file.path}
                    data-standing={read.standing}
                  >
                    <button
                      type="button"
                      className="text-left font-mono wrap-anywhere hover:underline"
                      data-path={file.path}
                      aria-label={say('session.edited.open', { path: shown })}
                      onClick={openOutside}
                    >
                      {shown}
                    </button>
                    <EditedFacts file={file} read={read} changed={at?.changed ?? ''} />
                  </li>
                )
              })}
            </ul>
          )}
        </>
      )}
    </section>
  )
}

/**
 * What moved on disk under the project while the session ran, that no edit call named (RG247).
 *
 * **Unattributed, and said so.** A formatter or a generator run through Bash writes files the
 * stream never mentions, and git is not this app's to ask — so the shell watches the root and
 * this lists what moved. Anything else writing under the project in that time is in here too,
 * which the caption does not pretend otherwise about. Every path is under the root, which is
 * what the watch is of, so all of it is the tree (RG265).
 */
function MovedOnDisk({
  moved,
  beyond,
  edited,
  onOpen,
}: {
  readonly moved: readonly MovedPath[]
  readonly beyond: number
  /** The paths the edited list already names, which this one does not repeat. */
  readonly edited: readonly string[]
  readonly onOpen: (path: string) => void
}) {
  const say = useWording()
  const when = useWhen()
  // What the edited list already named is not news: a path it holds is drawn there, with its
  // calls beside it. Compared on the spelling the shell answers with, which is what both carry.
  const rest = useMemo(() => moved.filter((one) => !edited.includes(one.path)), [moved, edited])
  const leaves = useMemo(
    () =>
      rest.map((one): Leaf => ({
        at: one.path,
        path: one.path,
        list: 'moved-file',
        facts: (
          <span className="text-muted-foreground text-xs">
            {say('session.disk.moves', { count: one.moves })} · {when(one.last)}
          </span>
        ),
      })),
    [rest, say, when],
  )

  return (
    <section className="mt-4" data-testid="moved-disk">
      <PanelTitle>{say('session.disk')}</PanelTitle>
      {rest.length === 0 ? (
        <p className="text-muted-foreground text-xs">{say('session.disk.none')}</p>
      ) : (
        <>
          <p className="text-muted-foreground mb-1.5 text-xs">{say('session.disk.about')}</p>
          <FileTree label={say('session.disk')} leaves={leaves} onOpen={onOpen} />
          {beyond === 0 ? null : (
            <p className="text-muted-foreground mt-1.5 text-xs">
              {say('session.disk.beyond', { count: beyond })}
            </p>
          )}
        </>
      )}
    </section>
  )
}

/** Who else is on a line of this project, off the engine's own registry. */
function Elsewhere({ claims, id }: { readonly claims: ClaimsPayload | null; readonly id: string }) {
  const say = useWording()
  // Held, and not this session's own line: an expired entry was stepped over and a stale one
  // is a marker that moved out from under it, and neither is somebody working.
  const others = (claims?.claims ?? []).filter((claim) => claim.id !== id && claim.state === 'held')

  return (
    <section className="mt-4" data-testid="elsewhere">
      <PanelTitle>{say('session.claims')}</PanelTitle>
      {others.length === 0 ? (
        <p className="text-muted-foreground text-xs">{say('session.claims.none')}</p>
      ) : (
        <ul className="flex flex-col gap-1 text-xs">
          {others.map((claim) => (
            <li key={claim.id} className="flex flex-wrap items-center gap-1.5">
              <Glyph>{claim.marker}</Glyph>
              <span className="font-mono font-semibold">{claim.id}</span>
              <span className="text-muted-foreground">
                {say('session.claim.since', { state: claim.state, since: claim.since })}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

/** What moved in the backlog: the files' answer, never the session's account of it. */
function Moved({
  record,
  now,
  outcome,
  files,
  claims,
}: {
  readonly record: SessionRecord
  readonly now: Reading | null
  readonly outcome: SessionOutcome | null
  readonly files: readonly GovernedFile[]
  readonly claims: ClaimsPayload | null
}) {
  const say = useWording()
  // A landing is a line's brief before against after (RG263). A session handed a finding has
  // no before, so there is nothing to compare and nothing honest to draw — what it did is in
  // its stream and in the files that moved, both of which are beside this.
  const landing =
    now === null || record.handed.kind !== 'line'
      ? null
      : landingBetween({ kind: 'read', payload: record.handed.brief }, now)

  return (
    <BentoPanel contentClassName="p-5">
      <PanelTitle>{say('session.moved')}</PanelTitle>
      {landing === null || !landing.moved ? (
        <p className="text-muted-foreground text-xs">{say('session.moved.none')}</p>
      ) : (
        <ul className="flex flex-col gap-1.5 text-[13px]" data-testid="moved">
          {landing.changes.map((change) => (
            <li key={change.kind} className="wrap-anywhere">
              <ChangeSaid change={change} />
            </li>
          ))}
        </ul>
      )}
      {outcome === null || outcome.said === '' ? null : (
        <pre className="text-muted-foreground mt-2 max-h-32 overflow-auto text-[11px] whitespace-pre-wrap">
          {outcome.said}
        </pre>
      )}
      <Files files={files} />
      <Elsewhere claims={claims} id={record.id} />
    </BentoPanel>
  )
}

/**
 * The files the session touched, as a card of their own (RG265).
 *
 * They shared a panel with what moved in the backlog, which made that column three answers deep
 * before the first file — and were two flat lists of full paths, each repeating its prefix, so a
 * reader asking what changed under one folder read every row to find out. Here they are two
 * trees, the edited and the moved, since they are two accounts of the same folders.
 */
function Touched({
  record,
  outcome,
  acts,
  moved,
  movedBeyond,
}: {
  readonly record: SessionRecord
  readonly outcome: SessionOutcome | null
  readonly acts: readonly Act[]
  /** What moved on disk while it ran, as last told (RG247). */
  readonly moved: readonly MovedPath[]
  readonly movedBeyond: number
}) {
  const ended = outcome !== null
  const edited = useMemo(() => editedIn(acts), [acts])
  const disk = useEditedAt(record.key, edited, ended)
  // Which file is open in the viewer, and what makes it worth rereading (RG245, RG247). One
  // state for both lists, since a file opens the same way whichever named it.
  const [open, setOpen] = useState<string | null>(null)
  const opening = useCallback((path: string) => {
    setOpen(path)
  }, [])
  const closing = useCallback(() => {
    setOpen(null)
  }, [])
  // An edit's seq leads back to the act that made it (RG246): the viewer closes, since the
  // stream is under it, and the act is brought into view in its own region.
  const showing = useCallback((seq: number) => {
    setOpen(null)
    requestAnimationFrame(() => {
      document.getElementById(`act-${String(seq)}`)?.scrollIntoView({ block: 'center' })
    })
  }, [])
  // Built once per read: the paths the edited list draws, which the moved list does not repeat.
  const drawn = useMemo(
    () => edited.map((file) => disk.get(file.path)?.shown ?? file.path),
    [edited, disk],
  )
  const viewedEdit = edited.find((file) => file.path === open)
  const viewedMove = moved.find((one) => one.path === open)
  // An edited file is read again as its last call answers; a moved one, each time it moves.
  const version =
    viewedEdit === undefined
      ? (viewedMove?.last ?? '')
      : `${String(viewedEdit.last)}:${String(viewedEdit.answered)}`

  return (
    <BentoPanel contentClassName="p-5">
      <EditedFiles edited={edited} disk={disk} started={record.started} onOpen={opening} />
      <MovedOnDisk moved={moved} beyond={movedBeyond} edited={drawn} onOpen={opening} />
      {open === null ? null : (
        <FileSheet
          sessionKey={record.key}
          path={open}
          version={version}
          acts={acts}
          onAct={showing}
          onClose={closing}
        />
      )}
    </BentoPanel>
  )
}

/**
 * Why a reply resumed nothing, in this window's words (RG269).
 *
 * Its own sentences and not the handover's: a reply takes no line and hands nothing over, so
 * "the line was not handed over" would say a thing that never happened.
 */
function saidOfReply(
  replied: Exclude<HandedOver, { readonly kind: 'started' }>,
  say: ReturnType<typeof useWording>,
): string {
  if (replied.kind === 'held') {
    const holder = replied.held[0]
    return say('session.reply.held', { by: holder?.by ?? '', since: holder?.since ?? '' })
  }
  if (replied.kind === 'refused') return say('session.reply.refused', { reason: replied.said })
  if (replied.kind === 'unavailable') {
    return say('session.reply.unavailable', {
      tried: replied.tried.map((command) => command.join(' ')).join(', '),
    })
  }
  const reason = replied.kind === 'withheld' ? replied.reason : replied.readiness
  return say('session.reply.withheld', { reason })
}

type Replying =
  | { readonly kind: 'idle' }
  | { readonly kind: 'sending' }
  | { readonly kind: 'said'; readonly replied: Exclude<HandedOver, { readonly kind: 'started' }> }

const NOT_REPLYING: Replying = { kind: 'idle' }

/**
 * Where a session stopped, and the box that answers it (RG269).
 *
 * **Answering is resuming.** A headless session ends its turn at its first question, and the only
 * way to answer it was a terminal, the project's folder and a session id this window never
 * showed. The reply goes to the far side as it was typed, and the session continues under the
 * same key — the stream above grows where it left off.
 *
 * **Beside its last words**, since those are what is being answered; the side panel no longer
 * repeats them. Focused when the session ended waiting on a refused call (RG268), which is the
 * one case where the reader's move is the whole reason the screen is open.
 */
function Reply({
  sessionKey,
  outcome,
}: {
  readonly sessionKey: string
  readonly outcome: SessionOutcome
}) {
  const say = useWording()
  const [text, setText] = useState('')
  const [replying, setReplying] = useState<Replying>(NOT_REPLYING)
  const box = useRef<HTMLTextAreaElement>(null)
  const waiting = outcome.state === 'waiting'

  useEffect(() => {
    if (waiting) box.current?.focus()
  }, [waiting])

  const typed = useCallback((event: ChangeEvent<HTMLTextAreaElement>) => {
    setText(event.target.value)
  }, [])
  const send = useCallback(() => {
    const bridge = getBridge()
    if (bridge === undefined) return
    setReplying({ kind: 'sending' })
    void bridge.replySession(sessionKey, text).then(
      (replied) => {
        if (replied.kind === 'started') {
          setText('')
          setReplying(NOT_REPLYING)
          return
        }
        setReplying({ kind: 'said', replied })
      },
      (cause: unknown) => {
        setReplying({
          kind: 'said',
          replied: { kind: 'withheld', reason: cause instanceof Error ? cause.message : '' },
        })
      },
    )
  }, [sessionKey, text])

  return (
    <section className="border-t px-5 py-4" data-testid="reply">
      {outcome.result === '' ? null : (
        <p className="text-[13px] leading-relaxed whitespace-pre-wrap wrap-anywhere">
          {say('session.result', { result: outcome.result })}
        </p>
      )}
      <Textarea
        ref={box}
        className="mt-3 w-full"
        rows={3}
        aria-label={say('session.reply')}
        value={text}
        onChange={typed}
      />
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <Button
          size="sm"
          onClick={send}
          disabled={text.trim() === '' || replying.kind === 'sending'}
        >
          {say('session.reply.send')}
        </Button>
        {replying.kind === 'sending' ? (
          <span className="text-muted-foreground text-xs">{say('session.reply.sending')}</span>
        ) : null}
        {replying.kind === 'said' ? (
          <span className="text-xs font-medium" data-testid="reply-failed">
            {saidOfReply(replying.replied, say)}
          </span>
        ) : null}
      </div>
    </section>
  )
}

/**
 * The session's own words, in a region that scrolls by itself and follows its end (RG206).
 *
 * The drawing gives the stream a height of its own; drawn as a list the page grows around, a
 * new act landed below the fold and a running session was read by scrolling the window. The
 * region is bounded by the viewport at every width, so there is one scroller and one rule —
 * `scrolledTo` — rather than a window below `lg` and a region above it.
 *
 * **The bound is measured** (RG217). It was `calc(100dvh - 12rem)`, a guess at what the header
 * and the hero take, and they take about 290 pixels rather than 192 — so the region ran past
 * the bottom of the window and its end, the one thing following exists to keep in view, was
 * below the fold. `useRegionHeight` reads the room under the region's own top instead.
 *
 * Following moves with the reader's own scroll: away from the end it stops and offers the way
 * back with what arrived since, and at the end it follows again. The jump is instant, because
 * a smooth scroll chasing several lines a second never arrives.
 */
function Stream({
  acts,
  after,
}: {
  readonly acts: readonly Act[]
  /** What sits under the region inside the panel, which its height leaves room for (RG269). */
  readonly after?: ReactNode
}) {
  const say = useWording()
  // Folded where the reader chose it, and applied here rather than in `actsIn`: the acts stay
  // whole, and following still counts every one of them (RG208).
  const notes = useSessionNotes()
  const rows = useMemo(
    () =>
      notes === 'hidden' ? foldedNotes(acts) : acts.map((act) => ({ kind: 'act' as const, act })),
    [acts, notes],
  )
  const region = useRef<HTMLDivElement>(null)
  const tail = useRef<HTMLDivElement>(null)
  // The reply box under the region is kept in view (RG269): the region's room is measured to the
  // bottom of the window, and a box under it would otherwise open below the fold at the very
  // moment the session is asking for it.
  const room = useRegionHeight(region, tail, after !== undefined)
  // Built once per measurement: a fresh object every render is a prop the region redraws for,
  // which `react-perf` refuses and a stream redrawn several times a second cannot afford.
  const bound = useMemo(() => (room === null ? undefined : { maxHeight: room }), [room])
  const [follow, setFollow] = useState<Follow>(FOLLOWING)
  const count = acts.length
  // What the region was last put at the end for, so only a change moves it: a redraw for
  // anything else — a reread of the line, a raw line opened — leaves it be.
  //
  // The room as well as the count, since RG217. The bound arrives after the first paint —
  // it is measured off the page — so a stream that was placed while it was still unbounded
  // had nowhere to scroll to, and stayed at its top with the newest act out of sight. A
  // window the reader resizes is the same moment: while following, the end stays in view.
  const placed = useRef({ count: 0, room: null as number | null })

  // Before paint, so an act that lands while following is never seen below the fold first.
  useLayoutEffect(() => {
    const element = region.current
    if (element === null || follow.leftAt !== null) return
    if (placed.current.count === count && placed.current.room === room) return
    placed.current = { count, room }
    element.scrollTop = element.scrollHeight
  }, [count, follow, room])

  const scrolled = useCallback(() => {
    const element = region.current
    if (element === null) return
    const where = {
      top: element.scrollTop,
      height: element.scrollHeight,
      visible: element.clientHeight,
    }
    setFollow((was) => scrolledTo(was, where, count))
  }, [count])

  const jump = useCallback(() => {
    const element = region.current
    if (element !== null) element.scrollTop = element.scrollHeight
    setFollow(FOLLOWING)
  }, [])

  if (count === 0) {
    return (
      <BentoPanel className="min-w-0" contentClassName="p-6">
        <BentoEmptyState title={say('session.stream.empty')} />
      </BentoPanel>
    )
  }
  const arrived = arrivedSince(follow, count)
  return (
    <BentoPanel className="min-w-0" contentClassName="relative p-0">
      <span className="block px-5 pt-4">
        <PanelTitle>{say('session.stream')}</PanelTitle>
      </span>
      <div
        ref={region}
        onScroll={scrolled}
        className="mt-2 overflow-y-auto overscroll-contain"
        style={bound}
        data-testid="stream"
      >
        <ul>
          {rows.map((row) =>
            row.kind === 'act' ? (
              <ActRow key={row.act.seq} act={row.act} />
            ) : (
              <FoldedRow key={`folded-${String(row.notes[0]?.seq ?? 0)}`} notes={row.notes} />
            ),
          )}
        </ul>
      </div>
      <div ref={tail}>{after}</div>
      {follow.leftAt === null ? null : (
        <div className="pointer-events-none absolute inset-x-0 bottom-3 flex justify-center">
          <Button size="sm" className="pointer-events-auto shadow-md" onClick={jump}>
            {arrived === 0
              ? say('session.follow')
              : say('session.follow.since', { count: arrived })}
          </Button>
        </div>
      )}
    </BentoPanel>
  )
}

export function Session() {
  const say = useWording()
  const params = useParams()
  const root = decodeURIComponent(params['root'] ?? '')
  const id = decodeURIComponent(params['id'] ?? '')
  const key = decodeURIComponent(params['key'] ?? '')
  const view = useSession(root, id, key)
  const session = view.kind === 'open' ? view : null

  const stop = useCallback(() => {
    void getBridge()?.stopSession(key)
  }, [key])

  const outcome: SessionState =
    session === null
      ? 'starting'
      : (session.outcome?.state ?? (session.lines.length === 0 ? 'starting' : 'running'))
  // Drawn off the files where they have something to say (RG268): a session handed a line has a
  // landing, and a turn that ended without it shipping is a stop and not a done.
  const landing =
    session === null || session.now === null || session.record.handed.kind !== 'line'
      ? null
      : landingBetween({ kind: 'read', payload: session.record.handed.brief }, session.now)
  const state = drawnState(outcome, landing)
  const running = session !== null && session.outcome === null

  let subtitle: ReactNode = say('session.opening')
  if (view.kind === 'absent') subtitle = say('transport.absent')
  if (view.kind === 'missing') subtitle = say('session.missing')
  if (session !== null) {
    subtitle = (
      <span className="flex flex-col gap-1">
        <span className="wrap-anywhere">{saidOf(session.record.handed)}</span>
        <span>
          <Pill intent={STATE_INTENT[state]}>{say(STATE_TEXT[state])}</Pill>
        </span>
      </span>
    )
  }
  const trailing = useMemo(
    () =>
      running ? (
        <HeroActions>
          <Button variant="outline" size="sm" onClick={stop}>
            {say('session.stop')}
          </Button>
        </HeroActions>
      ) : undefined,
    [running, stop, say],
  )

  // Which project and which line this session is on (RG242): the task was the only crumb, so a
  // session reached from the sessions list or a handover never said which project it was in.
  const face = session === null ? null : session.face
  const trail = useMemo(() => <ProjectTrail root={root} face={face} task={id} />, [root, face, id])
  // Once it has stopped and named itself, which is when there is something to answer and a
  // session to resume (RG269). Built once per outcome, since the stream redraws for every act.
  const ended = session?.outcome ?? null
  const reply = useMemo(
    () =>
      ended === null || ended.sessionId === '' ? undefined : (
        <Reply sessionKey={key} outcome={ended} />
      ),
    [ended, key],
  )

  // Read once for both columns that need them: the stream draws the acts, and what moved lists
  // the files they edited (RG243).
  const lines = session?.lines
  const marks = session?.marks
  const acts = useMemo(
    () => (lines === undefined || marks === undefined ? [] : actsIn(lines, marks)),
    [lines, marks],
  )

  return (
    <>
      <BentoHero eyebrow={trail} title={id} subtitle={subtitle} trailing={trailing} />
      {session === null ? null : (
        // The stream is written first and placed in the middle (RG225). Stacked below `lg`,
        // the columns fall in the order they are written, and what was handed over and what
        // moved used to come first — so at 400 wide the session's own words, which a reader
        // opened this screen for, started below the fold whatever the region's height did.
        // First in the document is also first for a screen reader, at every width.
        //
        // Laid out as an editor is, across the window's whole width (RG237): from `xl` what was
        // handed over is a side bar on the left, what moved one on the right, and the stream
        // takes the middle. Between `lg` and `xl` the two side panels share the left column —
        // what moved under what was handed, the stream spanning both rows — since three columns
        // at 1024 would leave the stream where the reading column had it. The second row is
        // `1fr` so a stream taller than the two panels grows that row and not the gap between them.
        <div className="grid items-start gap-5 lg:grid-cols-[18rem_minmax(0,1fr)] lg:grid-rows-[auto_1fr] xl:grid-cols-[18rem_minmax(0,1fr)_18rem] xl:grid-rows-none">
          <div
            className="min-w-0 lg:col-start-2 lg:row-span-2 lg:row-start-1 xl:row-span-1"
            data-region="session-stream"
          >
            <Stream acts={acts} after={reply} />
          </div>
          <div className="min-w-0 lg:col-start-1 lg:row-start-1" data-region="session-handed">
            <Handed record={session.record} />
          </div>
          {/* What moved in the backlog, and under it the files it touched as a card of their
              own (RG265): one grid cell holding both, so neither layout above it moves. */}
          <div className="flex min-w-0 flex-col gap-5 lg:col-start-1 lg:row-start-2 xl:col-start-3 xl:row-start-1">
            <div className="min-w-0" data-region="session-moved">
              <Moved
                record={session.record}
                now={session.now}
                outcome={session.outcome}
                files={session.files}
                claims={session.claims}
              />
            </div>
            <div className="min-w-0" data-region="session-files">
              <Touched
                record={session.record}
                outcome={session.outcome}
                acts={acts}
                moved={session.moved}
                movedBeyond={session.movedBeyond}
              />
            </div>
          </div>
        </div>
      )}
    </>
  )
}
