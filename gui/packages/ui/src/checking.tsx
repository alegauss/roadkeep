import { hasWalkthrough, type Translate, type Walkthrough, type WalkthroughAnswer } from '@rk/core'
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@viglet/viglet-design-system'
import { useCallback, useEffect, useRef, useState } from 'react'

import { getBridge } from './bridge'
import { useWording } from './wording'

/**
 * How to check one shipped entry, on asking (RG293).
 *
 * `explain.tsx`'s shape and its rules, about a different question: shown and never written, its
 * author named, every string drawn as prose with no Markdown parsed, and nothing kept here — what
 * is kept is kept by the far side (RG292) and comes back marked `kept`.
 *
 * **Asked when a row is opened and never before.** A list being scrolled past costs nothing,
 * which is the whole reason this is a dialog and not a column in the table.
 *
 * **`nothingToSee` is an answer and not an empty state.** A refactor, a test or an internal rule
 * has nothing a person can open, and the run saying so is the useful answer — drawn as its own
 * paragraph, with no steps beside it.
 */

type Checking =
  | { readonly kind: 'closed' }
  | { readonly kind: 'asking' }
  | { readonly kind: 'said'; readonly answer: WalkthroughAnswer }

const CLOSED: Checking = { kind: 'closed' }

/** Why there is no walkthrough, in this app's words for what the far side answered. */
function saidOfAnswer(answer: WalkthroughAnswer, say: Translate): string {
  switch (answer.kind) {
    case 'unavailable':
      return say('project.validation.unavailable', {
        tried: answer.tried.map((command) => command.join(' ')).join(', '),
      })
    case 'failed':
      return say('project.validation.failed', { reason: answer.said })
    case 'cancelled':
      return say('project.validation.cancelled')
    case 'withheld':
      return say('project.validation.withheld', { reason: answer.reason })
    default:
      // A run that answered with every slot empty said nothing about the entry either.
      return say('project.validation.failed', { reason: '' })
  }
}

/** One heading over a region, absent where the answer filled nothing under it. */
function Region({
  title,
  children,
}: {
  readonly title: string
  readonly children: React.ReactNode
}) {
  return (
    <section className="mt-5 first:mt-0">
      <h3 className="text-muted-foreground mb-2 text-xs font-semibold tracking-wide uppercase">
        {title}
      </h3>
      {children}
    </section>
  )
}

/** The steps, each a pair: what somebody does, and what they should see if it worked. */
function Steps({ steps }: { readonly steps: Walkthrough['steps'] }) {
  const say = useWording()
  return (
    <ol className="flex flex-col gap-3" data-testid="check-steps">
      {steps.map((step, at) => (
        <li
          key={`${String(at)}-${step.does}`}
          className="grid grid-cols-[1.5rem_minmax(0,1fr)] gap-x-3 rounded-lg border p-3"
        >
          <span className="text-muted-foreground pt-0.5 text-right font-mono text-xs">
            {at + 1}
          </span>
          <div className="min-w-0">
            <p className="text-sm font-medium [overflow-wrap:anywhere]">{step.does}</p>
            <p className="text-muted-foreground mt-1 text-[13px] [overflow-wrap:anywhere]">
              <span className="font-semibold">{say('project.validation.sees')}: </span>
              {step.sees}
            </p>
          </div>
        </li>
      ))}
    </ol>
  )
}

/** The answer as regions, each drawn only where the run filled it. */
function Walked({ walkthrough }: { readonly walkthrough: Walkthrough }) {
  const say = useWording()
  return (
    <div data-testid="check-said">
      {walkthrough.nothingToSee === '' ? null : (
        <Region title={say('project.validation.nothing')}>
          <p
            className="text-sm leading-relaxed [overflow-wrap:anywhere]"
            data-testid="check-nothing"
          >
            {walkthrough.nothingToSee}
          </p>
        </Region>
      )}
      {walkthrough.before.length === 0 ? null : (
        <Region title={say('project.validation.before')}>
          <ul className="flex flex-col gap-1.5" data-testid="check-before">
            {walkthrough.before.map((one) => (
              <li key={one} className="text-sm [overflow-wrap:anywhere]">
                {one}
              </li>
            ))}
          </ul>
        </Region>
      )}
      {walkthrough.steps.length === 0 ? null : (
        <Region title={say('project.validation.steps')}>
          <Steps steps={walkthrough.steps} />
        </Region>
      )}
      {walkthrough.where.length === 0 ? null : (
        <Region title={say('project.validation.where')}>
          <ul className="flex flex-col gap-1.5" data-testid="check-where">
            {walkthrough.where.map((place) => (
              <li key={place.path} className="text-sm [overflow-wrap:anywhere]">
                <span className="font-mono text-xs font-semibold">{place.path}</span>
                <span className="text-muted-foreground ml-2 text-[13px]">{place.said}</span>
              </li>
            ))}
          </ul>
        </Region>
      )}
    </div>
  )
}

/**
 * The button on a row, and the dialog it opens.
 *
 * Its own component per row so the ask belongs to the row somebody pressed: the state, the
 * cancel and the run are one entry's, and a second row opened while the first is out is a
 * second question the far side joins or starts on its own.
 */
export function Checking({ root, id }: { readonly root: string; readonly id: string }) {
  const say = useWording()
  const [checking, setChecking] = useState<Checking>(CLOSED)
  const onScreen = useRef(true)

  useEffect(() => {
    onScreen.current = true
    return () => {
      onScreen.current = false
    }
  }, [])

  const ask = useCallback(
    (again = false) => {
      setChecking({ kind: 'asking' })
      const bridge = getBridge()
      if (bridge === undefined) {
        setChecking({
          kind: 'said',
          answer: { kind: 'withheld', reason: say('transport.absent') },
        })
        return
      }
      bridge.walkthrough(root, id, again).then(
        (answer) => {
          if (onScreen.current) setChecking({ kind: 'said', answer })
        },
        (cause: unknown) => {
          const reason = cause instanceof Error ? cause.message : ''
          if (onScreen.current) {
            setChecking({ kind: 'said', answer: { kind: 'withheld', reason } })
          }
        },
      )
    },
    [root, id, say],
  )
  /** Open it: what was kept answers at once, and nothing is asked of Claude Code (RG292). */
  const open = useCallback(() => {
    ask()
  }, [ask])
  const again = useCallback(() => {
    ask(true)
  }, [ask])

  const close = useCallback(
    (showing: boolean) => {
      if (showing) return
      setChecking(CLOSED)
      getBridge()
        ?.cancelWalkthrough(root, id)
        .catch(() => undefined)
    },
    [root, id],
  )
  const stop = useCallback(() => {
    close(false)
  }, [close])

  const answer = checking.kind === 'said' ? checking.answer : null
  const said =
    answer?.kind === 'said' && hasWalkthrough(answer.walkthrough) ? answer.walkthrough : null

  return (
    <>
      <Button variant="outline" size="sm" onClick={open} data-testid="check">
        {say('project.validation.open')}
      </Button>
      <Dialog open={checking.kind !== 'closed'} onOpenChange={close}>
        <DialogContent
          className="max-h-[85dvh] w-full gap-0 overflow-auto sm:max-w-2xl"
          data-testid="check-dialog"
        >
          <DialogHeader>
            <DialogTitle>{say('project.validation.title', { id })}</DialogTitle>
            <DialogDescription>{say('project.validation.about')}</DialogDescription>
          </DialogHeader>
          <div className="mt-4 min-w-0">
            {checking.kind === 'asking' ? (
              <p className="text-muted-foreground text-sm" data-testid="check-asking">
                {say('project.validation.asking')}
              </p>
            ) : null}
            {/* Shown either way: it was true of the commit it was written about, and what moved
                since is what a reader decides about (RG292). */}
            {answer?.kind === 'said' && answer.stale ? (
              <p
                className="border-l-primary bg-muted/40 mb-4 rounded-r-lg border border-l-4 p-3 text-sm"
                data-testid="check-stale"
              >
                {say('project.validation.stale')}
              </p>
            ) : null}
            {said === null ? null : <Walked walkthrough={said} />}
            {answer === null || said !== null ? null : (
              <p className="text-sm" data-testid="check-failed">
                {saidOfAnswer(answer, say)}
              </p>
            )}
          </div>
          <footer className="text-muted-foreground mt-6 flex flex-wrap items-center gap-3 border-t pt-3 text-xs">
            {checking.kind === 'asking' ? (
              <Button variant="outline" size="sm" onClick={stop} data-testid="check-cancel">
                {say('project.validation.cancel')}
              </Button>
            ) : (
              <Button variant="outline" size="sm" onClick={again} data-testid="check-again">
                {say('project.validation.again')}
              </Button>
            )}
            {answer?.kind === 'said' && answer.commit !== '' ? (
              <span data-testid="check-commit">
                {say('project.validation.shipped.in', { commit: answer.commit.slice(0, 8) })}
              </span>
            ) : null}
            {answer?.kind === 'said' && answer.model !== '' ? (
              <span>{`${answer.model} · ${answer.version}`}</span>
            ) : null}
          </footer>
        </DialogContent>
      </Dialog>
    </>
  )
}
