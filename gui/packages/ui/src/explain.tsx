import { hasGloss, type BriefPayload, type GlossAnswer, type Translate } from '@rk/core'
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  Skeleton,
} from '@viglet/viglet-design-system'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { getBridge } from './bridge'
import { Explained } from './explained'
import { useSpokenLocale } from './speaking'
import { useWording } from './wording'

/**
 * A task said in plain words, on asking (RG285).
 *
 * The line and its design are written for whoever builds it, and a person new to the project
 * reads both and still asks what the task is. This is the other account: Claude Code's, over the
 * brief the far side reads (RG283, RG284), in the language the window speaks.
 *
 * **Shown and never written.** *No field this app composes* bounds it: what comes back is drawn
 * and nothing copies it into a symptom, a why or a section — which is also *no write to a
 * governed file*. Nothing here is kept between openings either: a gloss is a read.
 *
 * **Its author is named.** Two models explain one task two ways, so the footer says which
 * Claude Code and which model wrote it, in which language, from which line — the reason *no
 * engine the reader cannot name* gives for roadkeep's own copy holds for this one.
 *
 * **Every string is drawn as prose** (RG271), which is what the session's stream does with what
 * an agent writes: no Markdown is parsed, and the words are the answer's own.
 *
 * **A structured answer has one kind of progress** (RG288): the files the run reads on its way to
 * it. They arrive as events while the dialog waits, and none of them is kept — a reader who asks
 * again watches the next run read.
 */

type Explaining =
  | { readonly kind: 'closed' }
  | { readonly kind: 'asking' }
  | { readonly kind: 'said'; readonly answer: GlossAnswer }

const CLOSED: Explaining = { kind: 'closed' }

/**
 * Why there is no gloss, in this app's words for what the far side answered (RG284).
 *
 * One sentence per way of not answering, as a hand-over's refusals are: a machine with no Claude
 * Code, a run that failed and said why, one the reader gave up on, and a line the far side would
 * not read. An answer that came back empty is the fourth too — nothing was said about the task.
 */
function saidOfAnswer(answer: GlossAnswer, say: Translate): string {
  if (answer.kind === 'unavailable') {
    return say('explain.unavailable', {
      tried: answer.tried.map((command) => command.join(' ')).join(', '),
    })
  }
  if (answer.kind === 'failed') return say('explain.failed', { reason: answer.said })
  if (answer.kind === 'cancelled') return say('explain.cancelled')
  if (answer.kind === 'withheld') return say('explain.withheld', { reason: answer.reason })
  return say('explain.empty')
}

/** One call the run made while the answer was being written (RG288). */
interface Read {
  /** Its place in the run, which is what tells two reads of one file apart. */
  readonly at: number
  readonly tool: string
  readonly on: string
}

/**
 * How many reads are shown at once.
 *
 * The last few and not all of them: this is progress and not a log — what a reader wants is that
 * it is still going and what it is looking at now, and a run that reads thirty files would
 * otherwise push the answer off the screen before it arrived.
 */
const READS_SHOWN = 5

/**
 * The answer's shape while it is still being written, so the dialog does not jump when it lands —
 * and under it, the files the run is reading (RG288).
 */
function Asking({ reads }: { readonly reads: readonly Read[] }) {
  const say = useWording()
  return (
    <div className="flex flex-col gap-3" data-testid="explain-asking">
      <Skeleton className="h-6 w-3/4" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <Skeleton className="h-4 w-2/3" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-1/2" />
      {reads.length === 0 ? null : (
        // Told as it happens, so a reader waiting on a long run sees it move.
        <div className="mt-1 flex flex-col gap-1" aria-live="polite" data-testid="explain-reading">
          <p className="text-muted-foreground text-xs">{say('explain.reading')}</p>
          <ul className="flex flex-col gap-0.5">
            {reads.map((read) => (
              <li key={read.at} className="flex min-w-0 items-baseline gap-2 text-xs">
                <span className="text-muted-foreground shrink-0 font-mono">{read.tool}</span>
                <span className="min-w-0 font-mono wrap-anywhere">{read.on}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export function Explain({
  root,
  payload,
}: {
  readonly root: string
  /** The line as the engine briefed it: what the chain is drawn from (RG286). */
  readonly payload: BriefPayload
}) {
  const id = payload.id
  const say = useWording()
  const spoken = useSpokenLocale()
  const [explaining, setExplaining] = useState<Explaining>(CLOSED)
  const [reads, setReads] = useState<readonly Read[]>([])
  // A reader who closed the dialog is not waiting on an answer, and one who left the screen is
  // not either: both give the run up rather than letting it finish into nothing.
  const onScreen = useRef(true)
  useEffect(() => {
    onScreen.current = true
    return () => {
      onScreen.current = false
      getBridge()
        ?.cancelGloss(root, id)
        .catch(() => undefined)
    }
  }, [root, id])

  const ask = useCallback(
    (again = false) => {
      const bridge = getBridge()
      if (bridge === undefined) return
      setReads([])
      setExplaining({ kind: 'asking' })
      void bridge.gloss(root, id, again).then(
        (answer) => {
          if (onScreen.current) setExplaining({ kind: 'said', answer })
        },
        (cause: unknown) => {
          const reason = cause instanceof Error ? cause.message : ''
          if (onScreen.current) {
            setExplaining({ kind: 'said', answer: { kind: 'withheld', reason } })
          }
        },
      )
    },
    [root, id],
  )
  /** Open it: what was kept answers at once, and nothing is asked of Claude Code (RG287). */
  const open = useCallback(() => {
    ask()
  }, [ask])
  /** Ask again, whatever is kept: a stale gloss, or another reading of a line that has not moved. */
  const again = useCallback(() => {
    ask(true)
  }, [ask])

  // What the run is reading, while it reads (RG288): its own events, keyed on the project and
  // named by the line, so a dialog open on another line hears them and keeps none.
  const asking = explaining.kind === 'asking'
  useEffect(() => {
    if (!asking) return undefined
    return getBridge()?.subscribe('gloss', root, (event) => {
      if (event.id !== id) return
      setReads((held) => [...held, { at: held.length, tool: event.tool, on: event.on }])
    })
  }, [asking, root, id])

  const close = useCallback(
    (showing: boolean) => {
      if (showing) return
      setExplaining(CLOSED)
      getBridge()
        ?.cancelGloss(root, id)
        .catch(() => undefined)
    },
    [root, id],
  )
  const stop = useCallback(() => {
    close(false)
  }, [close])
  // The last few, kept out of the render so the list is one array and not a new one each time.
  const shown = useMemo(() => reads.slice(-READS_SHOWN), [reads])

  const answer = explaining.kind === 'said' ? explaining.answer : null
  // A gloss that says nothing at all is not one: the answer came back and the reader is told so.
  const said = answer?.kind === 'said' && hasGloss(answer.gloss) ? answer.gloss : null

  return (
    // A column like the other actions on this hero (RG235), so its button is the first thing
    // in it and the row's tops meet.
    <div className="flex flex-col items-end gap-1">
      <Button variant="outline" size="sm" onClick={open} data-testid="explain">
        {say('explain.ask')}
      </Button>
      <Dialog open={explaining.kind !== 'closed'} onOpenChange={close}>
        <DialogContent
          className="max-h-[85dvh] w-full gap-0 overflow-auto sm:max-w-3xl"
          data-testid="explain-dialog"
        >
          <DialogHeader>
            <DialogTitle>{say('explain.title', { id })}</DialogTitle>
            <DialogDescription>{say('explain.about')}</DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            {explaining.kind === 'asking' ? <Asking reads={shown} /> : null}
            {/* Shown either way: it explained the line as it stood, and what moved since is
                what a reader decides about (RG287). */}
            {answer?.kind === 'said' && answer.stale ? (
              <p
                className="border-l-primary bg-muted/40 mb-4 rounded-r-lg border border-l-4 p-3 text-sm"
                data-testid="explain-stale"
              >
                {say('explain.stale')}
              </p>
            ) : null}
            {said === null ? null : <Explained payload={payload} gloss={said} />}
            {answer === null || said !== null ? null : (
              <div className="flex flex-col items-start gap-3" data-testid="explain-failed">
                <p className="text-sm">{saidOfAnswer(answer, say)}</p>
                <Button size="sm" onClick={again}>
                  {say('explain.again')}
                </Button>
              </div>
            )}
          </div>
          <footer className="text-muted-foreground mt-6 flex flex-col gap-2 border-t pt-3 text-xs">
            {explaining.kind === 'asking' ? (
              <span>
                <Button variant="outline" size="sm" onClick={stop}>
                  {say('explain.cancel')}
                </Button>
              </span>
            ) : null}
            {answer?.kind === 'said' ? (
              <span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={again}
                  data-testid="explain-regenerate"
                >
                  {say('explain.regenerate')}
                </Button>
              </span>
            ) : null}
            {answer?.kind === 'said' ? (
              <p data-testid="explain-by">
                {say('explain.by', {
                  version: answer.version,
                  model: answer.model,
                  language: spoken,
                  id,
                })}
              </p>
            ) : null}
            <p>{say('explain.not-backlog')}</p>
          </footer>
        </DialogContent>
      </Dialog>
    </div>
  )
}
