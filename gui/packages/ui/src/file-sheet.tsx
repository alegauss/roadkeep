import { FILE_REFUSAL_TEXT, type Edited, type FileText } from '@rk/core'
import {
  Button,
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@viglet/viglet-design-system'
import { useCallback, useEffect, useMemo, useState } from 'react'

import { getBridge } from './bridge'
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
 */

type Viewing =
  { readonly kind: 'reading' } | { readonly kind: 'answered'; readonly answer: FileText }

const READING: Viewing = { kind: 'reading' }

/** How many lines a text has, not counting the empty one after a final line break. */
export function linesIn(text: string): number {
  if (text === '') return 0
  return text.split('\n').length - (text.endsWith('\n') ? 1 : 0)
}

export function FileSheet({
  sessionKey,
  file,
  onClose,
}: {
  readonly sessionKey: string
  /** The edited file this opened on, as the stream has it now. */
  readonly file: Edited
  readonly onClose: () => void
}) {
  const say = useWording()
  const [viewing, setViewing] = useState<Viewing>(READING)
  const [reloads, setReloads] = useState(0)
  // Every reason to read again, as one value: which file, the last call on it and whether that
  // call has answered, and how many times the reader asked.
  const { path, last, answered } = file
  const request = useMemo(
    () => ({ path, last, answered, reloads }),
    [path, last, answered, reloads],
  )

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
