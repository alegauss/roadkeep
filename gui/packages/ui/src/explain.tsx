import { hasGloss, type Gloss, type GlossAnswer, type Translate } from '@rk/core'
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
import { PanelTitle } from './forms'
import { Prose } from './prose'
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

/** One part of the answer that is a list: drawn only where the answer filled it. */
function Listed({ title, items }: { readonly title: string; readonly items: readonly string[] }) {
  if (items.length === 0) return null
  return (
    <section className="mt-4">
      <PanelTitle>{title}</PanelTitle>
      <ul className="ml-5 flex list-outside list-disc flex-col gap-1.5 text-sm">
        {items.map((item) => (
          <li key={item}>
            <Prose text={item} />
          </li>
        ))}
      </ul>
    </section>
  )
}

/** What the gloss says, as a reader reads it: the headline first, then the rest in order. */
function Said({ gloss }: { readonly gloss: Gloss }) {
  const say = useWording()
  const terms = gloss.terms
  const keyed = [
    { title: say('explain.deps'), rows: Object.entries(gloss.deps) },
    { title: say('explain.unblocks'), rows: Object.entries(gloss.unblocks) },
    { title: say('explain.binds'), rows: Object.entries(gloss.binds) },
  ]

  return (
    <div data-testid="explain-said">
      <p className="text-lg font-semibold wrap-anywhere">
        <Prose text={gloss.headline} />
      </p>
      {gloss.today === '' ? null : (
        <section className="mt-4">
          <PanelTitle>{say('explain.today')}</PanelTitle>
          <Prose text={gloss.today} />
        </section>
      )}
      {gloss.after === '' ? null : (
        <section className="mt-4">
          <PanelTitle>{say('explain.after')}</PanelTitle>
          <Prose text={gloss.after} />
        </section>
      )}
      {gloss.steps.length === 0 ? null : (
        <section className="mt-4">
          <PanelTitle>{say('explain.steps')}</PanelTitle>
          <ol className="ml-5 flex list-outside list-decimal flex-col gap-1.5 text-sm">
            {gloss.steps.map((step) => (
              <li key={step}>
                <Prose text={step} />
              </li>
            ))}
          </ol>
        </section>
      )}
      {terms.length === 0 ? null : (
        <section className="mt-4">
          <PanelTitle>{say('explain.terms')}</PanelTitle>
          <dl className="flex flex-col gap-1.5 text-sm">
            {terms.map((term) => (
              <div key={term.term} className="flex flex-col">
                <dt className="font-mono text-xs font-semibold wrap-anywhere">{term.term}</dt>
                <dd className="text-muted-foreground">
                  <Prose text={term.said} />
                </dd>
              </div>
            ))}
          </dl>
        </section>
      )}
      <Listed title={say('explain.risks')} items={gloss.risks} />
      <Listed title={say('explain.done')} items={gloss.done} />
      {keyed.map(({ title, rows }) =>
        rows.length === 0 ? null : (
          <section className="mt-4" key={title}>
            <PanelTitle>{title}</PanelTitle>
            <dl className="flex flex-col gap-1.5 text-sm">
              {rows.map(([key, said]) => (
                <div key={key} className="flex flex-col">
                  <dt className="font-mono text-xs font-semibold wrap-anywhere">{key}</dt>
                  <dd className="text-muted-foreground">
                    <Prose text={said} />
                  </dd>
                </div>
              ))}
            </dl>
          </section>
        ),
      )}
    </div>
  )
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

export function Explain({ root, id }: { readonly root: string; readonly id: string }) {
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
            {said === null ? null : <Said gloss={said} />}
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
