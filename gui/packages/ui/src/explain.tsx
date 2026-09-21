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
import { useCallback, useEffect, useRef, useState } from 'react'

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

/** The answer's shape while it is still being written, so the dialog does not jump when it lands. */
function Asking() {
  return (
    <div className="flex flex-col gap-3" data-testid="explain-asking">
      <Skeleton className="h-6 w-3/4" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <Skeleton className="h-4 w-2/3" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-1/2" />
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

  const ask = useCallback(() => {
    const bridge = getBridge()
    if (bridge === undefined) return
    setExplaining({ kind: 'asking' })
    void bridge.gloss(root, id).then(
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
  }, [root, id])

  const close = useCallback(
    (open: boolean) => {
      if (open) return
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

  const answer = explaining.kind === 'said' ? explaining.answer : null
  // A gloss that says nothing at all is not one: the answer came back and the reader is told so.
  const said = answer?.kind === 'said' && hasGloss(answer.gloss) ? answer.gloss : null

  return (
    // A column like the other actions on this hero (RG235), so its button is the first thing
    // in it and the row's tops meet.
    <div className="flex flex-col items-end gap-1">
      <Button variant="outline" size="sm" onClick={ask} data-testid="explain">
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
            {explaining.kind === 'asking' ? <Asking /> : null}
            {said === null ? null : <Explained payload={payload} gloss={said} />}
            {answer === null || said !== null ? null : (
              <div className="flex flex-col items-start gap-3" data-testid="explain-failed">
                <p className="text-sm">{saidOfAnswer(answer, say)}</p>
                <Button size="sm" onClick={ask}>
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
