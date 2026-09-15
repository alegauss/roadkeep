import {
  editsOf,
  editStanding,
  FILE_REFUSAL_TEXT,
  type Act,
  type FileEdit,
  type FileText,
} from '@rk/core'
import {
  Button,
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@viglet/viglet-design-system'
import { useCallback, useEffect, useMemo, useState, type MouseEvent } from 'react'

import { getBridge } from './bridge'
import { Pill } from './marks'
import { useWording } from './wording'

/**
 * One file a session edited, as the disk holds it now, over the session (RG245).
 *
 * **The design system's `Sheet`, and nothing routes.** It opens over the screen so the stream
 * keeps running under it, and it is drawn only while open, so closing it forgets the text:
 * nothing here is kept, which is `No store of its own`.
 *
 * **Drawn as the file stores it.** The text face, its line numbers beside it, its own line
 * breaks and no wrapping of this app's. A Markdown file is its characters (`No Markdown parsed
 * in this app`) and nothing is highlighted: the question a reviewer brings is what changed, and
 * a grammar per language would be a second parser answering another one.
 *
 * **Current, never remembered.** Read as it opens, again from its own button, and again when
 * the stream edits the same path while it is open — as the call is made and as its answer
 * lands, since the second is when the disk has moved.
 *
 * **What the session changed is above the file** (RG246), read off its own calls and checked
 * against the text below it rather than believed.
 */

type Viewing =
  { readonly kind: 'reading' } | { readonly kind: 'answered'; readonly answer: FileText }

const READING: Viewing = { kind: 'reading' }

/** How many lines a text has, not counting the empty one after a final line break. */
export function linesIn(text: string): number {
  if (text === '') return 0
  return text.split('\n').length - (text.endsWith('\n') ? 1 : 0)
}

/** Past this many lines a block folds, and opens where it stands (RG246). */
const FOLD_OVER = 12

/** One side of an edit: what it replaced, or what it put there. Folded where it is long. */
function Block({ label, text }: { readonly label: string; readonly text: string }) {
  const say = useWording()
  const body = (
    <pre className="bg-muted mt-1 max-h-80 overflow-auto rounded p-2 text-[11px] whitespace-pre-wrap">
      {text}
    </pre>
  )
  const count = linesIn(text)
  if (count <= FOLD_OVER) {
    return (
      <div className="mt-2">
        <span className="text-muted-foreground text-[11px]">{label}</span>
        {body}
      </div>
    )
  }
  return (
    <details className="mt-2">
      <summary className="text-muted-foreground cursor-pointer text-[11px]">
        {label} · {say('session.file.edit.folded', { count })}
      </summary>
      {body}
    </details>
  )
}

/**
 * What the session changed in this file, above the file itself (RG246).
 *
 * Each call's own two halves, in stream order, with its seq leading back to the act in the
 * stream. Checked against the text that was read rather than believed: found means what the
 * edit put there is in the file now, and gone means it is not — whether a later edit overwrote
 * it, something reverted it, or it never applied.
 */
function Edits({
  edits,
  text,
  onAct,
}: {
  readonly edits: readonly FileEdit[]
  /** The file as it was read, or null while nothing has been read. */
  readonly text: string | null
  readonly onAct: (seq: number) => void
}) {
  const say = useWording()
  const acted = useCallback(
    (event: MouseEvent<HTMLButtonElement>) => {
      onAct(Number(event.currentTarget.dataset['seq'] ?? '0'))
    },
    [onAct],
  )
  if (edits.length === 0) return null

  return (
    <section className="border-b" data-testid="file-edits">
      <h3 className="text-muted-foreground px-4 pt-3 text-[11px] font-semibold tracking-wide uppercase">
        {say('session.file.edits')}
      </h3>
      <ul>
        {edits.map((edit, at) => {
          const standing = editStanding(edit, text)
          return (
            <li
              key={`${String(edit.seq)}-${String(at)}`}
              className="px-4 py-3"
              data-testid="file-edit"
              data-seq={edit.seq}
              data-standing={standing}
            >
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <button
                  type="button"
                  className="font-mono font-semibold hover:underline"
                  data-seq={edit.seq}
                  onClick={acted}
                >
                  {say('session.file.edit.act', { seq: edit.seq })}
                </button>
                <span className="text-muted-foreground font-mono">{edit.tool}</span>
                {edit.failed ? <Pill intent="error">{say('session.act.failed')}</Pill> : null}
                {standing === 'in-the-file' ? (
                  <Pill intent="on">{say('session.file.edit.found')}</Pill>
                ) : null}
                {standing === 'not-in-the-file' ? (
                  <Pill intent="warn">{say('session.file.edit.gone')}</Pill>
                ) : null}
              </div>
              {edit.before === '' ? null : (
                <Block label={say('session.file.edit.replaced')} text={edit.before} />
              )}
              <Block
                label={
                  edit.before === '' ? say('session.file.edit.wrote') : say('session.file.edit.put')
                }
                text={edit.after}
              />
            </li>
          )
        })}
      </ul>
    </section>
  )
}

export function FileSheet({
  sessionKey,
  path,
  version,
  acts,
  onAct,
  onClose,
}: {
  readonly sessionKey: string
  /** The file to read, as the call or the watch spelled its path. */
  readonly path: string
  /**
   * What makes this file worth reading again: an edited file's last call and whether it has
   * answered, a moved one's last move. A changed value is a reread.
   */
  readonly version: string
  /** The stream, which is where what the session changed in this file is read from (RG246). */
  readonly acts: readonly Act[]
  /** Show one act in the stream, by its seq. */
  readonly onAct: (seq: number) => void
  readonly onClose: () => void
}) {
  const say = useWording()
  const [viewing, setViewing] = useState<Viewing>(READING)
  const [reloads, setReloads] = useState(0)
  // Every reason to read again, as one value: which file, what makes it worth rereading, and
  // how many times the reader asked for it.
  const request = useMemo(() => ({ path, version, reloads }), [path, version, reloads])

  useEffect(() => {
    const bridge = getBridge()
    if (bridge === undefined) return undefined
    let live = true
    void bridge.fileText(sessionKey, request.path).then(
      (answer) => {
        if (live) setViewing({ kind: 'answered', answer })
      },
      () => undefined,
    )
    return () => {
      live = false
    }
  }, [sessionKey, request])

  const reload = useCallback(() => {
    setReloads((was) => was + 1)
  }, [])
  const changed = useCallback(
    (open: boolean) => {
      if (!open) onClose()
    },
    [onClose],
  )

  const answer = viewing.kind === 'answered' ? viewing.answer : null
  const read = answer?.kind === 'read' ? answer : null
  const lines = read === null ? 0 : linesIn(read.text)
  const numbers = useMemo(
    () => Array.from({ length: Math.max(lines, 1) }, (_, at) => String(at + 1)).join('\n'),
    [lines],
  )
  const edits = useMemo(() => editsOf(acts, path), [acts, path])
  // What the file is, in one sentence: still being read, how long it is, or why it was not read.
  let described = say('session.file.reading')
  if (read !== null) described = say('session.file.lines', { count: lines })
  if (answer?.kind === 'refused') described = say(FILE_REFUSAL_TEXT[answer.code], answer.fields)

  return (
    <Sheet open onOpenChange={changed}>
      <SheetContent side="right" className="w-full gap-0 sm:max-w-3xl" data-testid="file-sheet">
        <SheetHeader className="border-b pr-12">
          <SheetTitle className="font-mono text-sm wrap-anywhere">{read?.shown ?? path}</SheetTitle>
          <SheetDescription
            data-testid="file-described"
            data-code={answer?.kind === 'refused' ? answer.code : undefined}
          >
            {described}
          </SheetDescription>
          <span>
            <Button variant="outline" size="sm" onClick={reload}>
              {say('session.file.reload')}
            </Button>
          </span>
        </SheetHeader>
        {/* Reachable by keyboard, because it scrolls: a region a mouse can scroll and a Tab
            cannot reach is the finding the accessibility pass names (RG211), and a file long
            enough to scroll is the ordinary case here. Named by the file, as a group. */}
        <section
          className="min-h-0 flex-1 overflow-auto"
          data-testid="file-body"
          tabIndex={0}
          aria-label={read?.shown ?? path}
        >
          <Edits edits={edits} text={read?.text ?? null} onAct={onAct} />
          {read === null ? null : (
            <div className="flex font-mono text-xs leading-5">
              <pre
                aria-hidden="true"
                className="text-muted-foreground bg-background sticky left-0 border-r px-3 py-3 text-right select-none"
              >
                {numbers}
              </pre>
              <pre className="px-3 py-3" data-testid="file-text">
                {read.text}
              </pre>
            </div>
          )}
        </section>
      </SheetContent>
    </Sheet>
  )
}
