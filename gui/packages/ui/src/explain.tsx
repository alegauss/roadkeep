import { actsIn, hasGloss, type BriefPayload, type GlossAnswer, type Translate } from '@rk/core'
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@viglet/viglet-design-system'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { getBridge } from './bridge'
import { Explained } from './explained'
import { useSpokenLocale } from './speaking'
import { NO_STANDINGS, Stream } from './stream'
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
 * **A structured answer has one kind of progress** (RG297): the run's own stream on its way to
 * it — the files it reads (RG288), what it says, the notes of it thinking. The lines arrive as
 * events while the dialog waits and are drawn with the session's rows, beside a clock of how long
 * it has been asked. None of them is kept: a reader who asks again watches the next run.
 *
 * **Nothing in it can ask the reader anything.** The run is given three reads under `dontAsk`, so
 * a call outside them is refused where it stands and shows in the stream as a failed result.
 */

type Explaining =
  | { readonly kind: 'closed' }
  /** Since when, as the clock reads it: what the dialog counts up from (RG297). */
  | { readonly kind: 'asking'; readonly started: number }
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

/**
 * How long it has been asking, as a clock: minutes and seconds, which read the same in every
 * language this build ships and need no sentence of their own per unit.
 */
export function clockOf(ms: number): string {
  const seconds = Math.max(0, Math.floor(ms / 1000))
  return `${String(Math.floor(seconds / 60))}:${String(seconds % 60).padStart(2, '0')}`
}

/** A clock that moves once a second from when the asking started, for as long as it is drawn. */
function useSince(started: number): string {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const tick = setInterval(() => {
      setNow(Date.now())
    }, 1000)
    return () => {
      clearInterval(tick)
    }
  }, [])
  return clockOf(now - started)
}

/** The region's height inside the dialog: most of it, leaving the title and the footer in view. */
const STREAM_BOUND = 'max-h-[55dvh]'

/**
 * The run as it goes (RG297): a clock of how long it has been asked, and its stream drawn with
 * the session's own rows.
 *
 * The clock is what tells a run thinking for a minute from a run that stopped: the stream says
 * what it did, and the clock says it is still being waited on. The stream folds its notes by the
 * reader's own setting, as the session screen does.
 */
function Asking({
  lines,
  started,
}: {
  readonly lines: readonly string[]
  readonly started: number
}) {
  const say = useWording()
  const acts = useMemo(() => actsIn(lines), [lines])
  const since = useSince(started)
  return (
    <div className="flex flex-col gap-3" data-testid="explain-asking">
      <p
        className="text-muted-foreground flex items-center gap-2 text-xs"
        data-testid="explain-since"
      >
        <span
          className="bg-primary size-2 shrink-0 animate-pulse rounded-full"
          aria-hidden="true"
        />
        {say('explain.since', { elapsed: since })}
      </p>
      <Stream acts={acts} standings={NO_STANDINGS} bound={STREAM_BOUND} />
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
  // The run's stream so far (RG297), in the order it was written. Started again by every asking.
  const [lines, setLines] = useState<readonly string[]>([])
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
      setLines([])
      setExplaining({ kind: 'asking', started: Date.now() })
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

  // What the run is doing, while it does it (RG297): its own events, keyed on the project and
  // named by the line, so a dialog open on another line hears them and keeps none. A line is
  // placed by its index, so one heard twice is one row.
  const asking = explaining.kind === 'asking'
  useEffect(() => {
    if (!asking) return undefined
    return getBridge()?.subscribe('gloss', root, (event) => {
      if (event.id !== id) return
      setLines((held) => (event.index < held.length ? held : [...held, event.line]))
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
          {/* Free to be narrower than what it holds (RG297): a grid item is as wide as its widest
              line by default, and the stream's paths and file text would push the whole dialog
              past a phone's width. What is too wide scrolls in its own region instead. */}
          <div className="mt-4 min-w-0">
            {explaining.kind === 'asking' ? (
              <Asking lines={lines} started={explaining.started} />
            ) : null}
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
