import {
  hasWalkthrough,
  refusalOf,
  type MessageKey,
  type Translate,
  type Walkthrough,
  type WalkthroughAnswer,
} from '@rk/core'
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@viglet/viglet-design-system'
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
  type ReactNode,
} from 'react'

import { getBridge } from './bridge'
import { useVerdict } from './useVerdict'
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

/**
 * The verdict a `nothingToSee` answer proposes, as the engine spells it.
 *
 * One word and not a set: what is published is the set, and this is the single member the
 * walkthrough's own slot corresponds to. An engine that spells it otherwise pre-selects nothing,
 * which is the right answer to *I do not know which of your verdicts this is*.
 */
const NOTHING_VERDICT = 'nothing to see'

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
function Region({ title, children }: { readonly title: string; readonly children: ReactNode }) {
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
 * The label this build has for each verdict it knows (RG294).
 *
 * **The set is `commands`' and this is only the words.** A build that grows a fourth verdict
 * offers a fourth button the day it does, and one that drops a verdict stops offering it; what
 * is on this side is how to say the ones this build has a sentence for.
 *
 * Spelled out rather than built from the word, which RG183's guard is about: a key composed at
 * run time is a key nothing can be shown to say, so a label added here and never drawn reads as
 * dead like any other.
 */
const VERDICT_LABELS: Readonly<Record<string, MessageKey>> = {
  worked: 'project.validation.verdict.worked',
  failed: 'project.validation.verdict.failed',
  'nothing to see': 'project.validation.verdict.nothing-to-see',
}

/** A verdict as a button says it, or as the engine spells it where this build has no sentence. */
function labelOf(word: string, say: Translate): string {
  const key = VERDICT_LABELS[word]
  return key === undefined ? word : say(key)
}

/**
 * One verdict to choose, as a radio and not a button with a role on it.
 *
 * Its own component because the pick is a callback per word: an arrow written in the loop is a
 * new function every render, and a real `input` is what a screen reader already knows how to say.
 */
function Choice({
  word,
  chosen,
  onPick,
}: {
  readonly word: string
  readonly chosen: boolean
  readonly onPick: (word: string) => void
}) {
  const say = useWording()
  const pick = useCallback(() => {
    onPick(word)
  }, [onPick, word])

  return (
    <label
      className={`cursor-pointer rounded-full border px-3 py-1 text-sm ${
        chosen ? 'border-primary bg-muted font-semibold' : 'text-muted-foreground'
      }`}
      data-testid="verdict-choice"
      data-verdict={word}
    >
      <input
        type="radio"
        name="verdict"
        value={word}
        checked={chosen}
        onChange={pick}
        className="sr-only"
      />
      {labelOf(word, say)}
    </label>
  )
}

/**
 * Saying what happened, under the steps (RG294).
 *
 * **The sentence is required.** A verdict with no account is a tick box, and a ledger of bare
 * verdicts is what this block exists to replace. Nothing here measures it: the engine holds the
 * limit, and a refusal comes back naming the field it refused.
 *
 * **One answer is suggested and only one.** Where the run found nothing to open, that verdict is
 * chosen and its own sentence is in the box to accept or rewrite — the answer that costs least to
 * be wrong about, since a walkthrough wrongly skipped is a row somebody re-opens rather than a
 * false claim in the ledger.
 */
function Saying({
  root,
  id,
  choices,
  suggested,
  onWrote,
}: {
  readonly root: string
  readonly id: string
  readonly choices: readonly string[]
  /** The verdict the walkthrough proposes, and the sentence it proposes with it. */
  readonly suggested: { readonly word: string; readonly saw: string } | null
  readonly onWrote: () => void
}) {
  const say = useWording()
  const { verdict, send } = useVerdict(root, id)
  const [chosen, setChosen] = useState(suggested?.word ?? '')
  const [saw, setSaw] = useState(suggested?.saw ?? '')
  const wrote = verdict.kind === 'wrote'

  useEffect(() => {
    if (wrote) onWrote()
  }, [wrote, onWrote])

  const submit = useCallback(
    (event: FormEvent) => {
      event.preventDefault()
      send(chosen, saw)
    },
    [send, chosen, saw],
  )
  const type = useCallback((event: ChangeEvent<HTMLTextAreaElement>) => {
    setSaw(event.target.value)
  }, [])

  if (choices.length === 0) return null
  if (verdict.kind === 'wrote') {
    return (
      <div className="mt-5 border-t pt-4 text-sm" data-testid="verdict-wrote">
        <p>
          {say('project.validation.sent', {
            id: verdict.written.id,
            verdict: labelOf(verdict.written.verdict, say),
          })}
        </p>
        {/* The one thing a reader could not tell from the ledger afterwards: the last verdict
            wins, so a second one leaves no trace of the first. */}
        {verdict.written.replaced === null ? null : (
          <p className="text-muted-foreground mt-1" data-testid="verdict-replaced">
            {say('project.validation.rewrote')}
          </p>
        )}
      </div>
    )
  }

  return (
    <form className="mt-5 border-t pt-4" onSubmit={submit} data-testid="verdict-form">
      <fieldset className="flex flex-wrap gap-2 border-0 p-0">
        <legend className="sr-only">{say('project.validation.send')}</legend>
        {choices.map((word) => (
          <Choice key={word} word={word} chosen={word === chosen} onPick={setChosen} />
        ))}
      </fieldset>
      <label className="mt-3 block text-sm">
        <span className="mb-1 block font-medium">{say('project.validation.saw')}</span>
        <textarea
          value={saw}
          onChange={type}
          rows={3}
          placeholder={say('project.validation.saw.placeholder')}
          data-testid="verdict-saw"
          className="border-input bg-background w-full rounded-md border px-3 py-2 text-sm"
        />
      </label>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <Button
          type="submit"
          size="sm"
          disabled={chosen === '' || saw.trim() === '' || verdict.kind === 'sending'}
          data-testid="verdict-send"
        >
          {say(
            verdict.kind === 'sending' ? 'project.validation.sending' : 'project.validation.send',
          )}
        </Button>
        {/* The engine's own words for what it would not take, with the field it named — never
            a sentence this app composed about somebody's writing. */}
        {verdict.kind === 'refused' ? (
          <p className="text-sm" data-testid="verdict-refused">
            {say('project.validation.refused', { said: verdict.refusal.said })}
          </p>
        ) : null}
        {verdict.kind === 'failed' ? (
          <p className="text-sm" data-testid="verdict-failed">
            {say('project.validation.unwritable', { reason: refusalOf(verdict.reason, say) })}
          </p>
        ) : null}
        {verdict.kind === 'unreadable' ? (
          <p className="text-sm" data-testid="verdict-failed">
            {say('project.validation.unwritable', { reason: verdict.reason })}
          </p>
        ) : null}
      </div>
    </form>
  )
}

/**
 * The verdict this walkthrough proposes, where it proposes one (RG294).
 *
 * Only for a run that found nothing to open, and only where the engine publishes a verdict whose
 * word says so: the sentence is the agent's own, in the box to accept or rewrite. Nothing else is
 * ever suggested — this is the answer that costs least to be wrong about, because a walkthrough
 * wrongly skipped is a row somebody re-opens and not a false claim in the ledger.
 *
 * The word is matched against the published set rather than written here, so an engine spelling
 * it otherwise suggests nothing rather than pre-selecting a button it does not offer.
 */
function suggestedBy(
  walkthrough: Walkthrough,
  choices: readonly string[],
): { readonly word: string; readonly saw: string } | null {
  if (walkthrough.nothingToSee === '') return null
  const word = choices.find((one) => one === NOTHING_VERDICT)
  return word === undefined ? null : { word, saw: walkthrough.nothingToSee }
}

/**
 * The button on a row, and the dialog it opens.
 *
 * Its own component per row so the ask belongs to the row somebody pressed: the state, the
 * cancel and the run are one entry's, and a second row opened while the first is out is a
 * second question the far side joins or starts on its own.
 */
export function Checking({
  root,
  id,
  choices,
  onWrote,
}: {
  readonly root: string
  readonly id: string
  /** The verdicts this engine publishes (RG294). Empty offers no form at all. */
  readonly choices: readonly string[]
  /** A verdict landed, so the list this row is in is a query whose answer has moved. */
  readonly onWrote: () => void
}) {
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
            {/* Under the steps, and only once there are some: a verdict about a walkthrough
                nobody has read is a verdict about nothing (RG294). */}
            {said === null ? null : (
              <Saying
                root={root}
                id={id}
                choices={choices}
                suggested={suggestedBy(said, choices)}
                onWrote={onWrote}
              />
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
