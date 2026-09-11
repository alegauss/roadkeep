import {
  anyOver,
  counterFor,
  blanksIn,
  fieldsRefused,
  folderName,
  sectionCounter,
  type Bounds,
  type BudgetPayload,
  type Counter,
  type Door,
  type Translate,
} from '@rk/core'
import { Button } from '@viglet/viglet-design-system'
import { BentoHero, BentoPanel } from '@viglet/viglet-design-system/bento'
import { useCallback, useEffect, useMemo, useState, type ChangeEvent, type ReactNode } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { projectPath, taskPath } from './areas'
import { Pill } from './marks'
import { EMPTY_DRAFT, useFiling, type Draft } from './useFiling'
import { useWording } from './wording'

/**
 * Filing a line from the window (RG151). `docs/design/Escrita.dc.html` is the drawing, opened
 * by File a line on the project surface.
 *
 * **Every number beside a field is the engine's.** `budget` prices the draft and the counters
 * are what it answered — the allowance moves as deps are added, because the rendered line is
 * what binds, and a count worked out here would be this app keeping a limit of its own. The
 * aim is drawn as advice and the allowance as the wall.
 *
 * **The command is shown before it runs**, and filing is that argv run: the prose is elided in
 * the middle so the line stays readable, and Copy takes the whole of it.
 *
 * **A refusal lands on the field it names**, never in a toast, and the doors it offers are
 * taken by name through the bridge (RG165) — a complete one runs as it stands, and an
 * incomplete one asks for the words the engine left blanks for. Nothing here composes a second
 * command line.
 */

function Label({ children }: { readonly children: ReactNode }) {
  return (
    <span className="text-muted-foreground text-[11px] font-semibold tracking-wider uppercase">
      {children}
    </span>
  )
}

/** One field's counter, in the engine's numbers. Over the limit it says by how much. */
function Counted({ counter }: { readonly counter: Counter | null }) {
  const say = useWording()
  if (counter === null) return null

  const over = counter.over > 0
  let said = say('filing.counter', { left: counter.left, allowed: counter.allowed })
  if (over) {
    said = say('filing.counter.over', {
      taken: counter.taken,
      allowed: counter.allowed,
      over: counter.over,
    })
  } else if (counter.room > 0) {
    said = say('filing.counter.aim', {
      left: counter.left,
      allowed: counter.allowed,
      room: counter.room,
    })
  }

  return (
    <span
      className={`text-xs ${over ? 'text-destructive font-semibold' : 'text-muted-foreground'}`}
    >
      {said}
      {counter.boundBy === '' ? null : ` · ${say('filing.counter.line')}`}
    </span>
  )
}

function Field({
  label,
  about,
  counter,
  refused,
  children,
}: {
  readonly label: string
  readonly about?: string
  readonly counter?: Counter | null
  readonly refused?: string
  readonly children: ReactNode
}) {
  return (
    <label className="flex flex-col gap-1" data-testid="field">
      <span className="flex flex-wrap items-baseline justify-between gap-2">
        <Label>{label}</Label>
        <Counted counter={counter ?? null} />
      </span>
      {children}
      {about === undefined ? null : <span className="text-muted-foreground text-xs">{about}</span>}
      {refused === undefined ? null : (
        <span className="text-destructive text-xs font-medium" data-testid="refused-field">
          {refused}
        </span>
      )}
    </label>
  )
}

const BOX = 'border-input bg-background rounded-md border px-3 py-2 text-sm'

/** The parts of a draft a person types into. The deps are chips and go their own way. */
type Typed = Exclude<keyof Draft, 'deps'>

/** How a box says what was typed: by the field's own name, so one handler serves them all. */
type Typing = (field: Typed, value: string) => void

/**
 * A box bound to one field. It exists so each handler is made once per field rather than per
 * render — the draft moves on every keystroke, and an inline closure would rebuild every box
 * in the form each time one of them changed.
 */
function Box({
  field,
  value,
  on,
  area,
  className,
}: {
  readonly field: Typed
  readonly value: string
  readonly on: Typing
  readonly area?: boolean
  readonly className?: string
}) {
  const changed = useCallback(
    (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      on(field, event.target.value)
    },
    [field, on],
  )
  const dressed = `${BOX} ${className ?? ''}`
  return area === true ? (
    <textarea className={dressed} value={value} onChange={changed} />
  ) : (
    <input className={dressed} value={value} onChange={changed} />
  )
}

/** One dep, which drops when pressed. Its own component so the handler is made per dep. */
function Chip({ dep, onDrop }: { readonly dep: string; readonly onDrop: (dep: string) => void }) {
  const say = useWording()
  const drop = useCallback(() => {
    onDrop(dep)
  }, [dep, onDrop])
  return (
    <button
      type="button"
      className="bg-muted rounded px-2 py-0.5 font-mono text-xs"
      aria-label={say('filing.deps.drop', { id: dep })}
      onClick={drop}
    >
      {dep}
    </button>
  )
}

/** The deps, as chips with one place to add another: each takes room from the sentence. */
function Deps({
  deps,
  onChange,
}: {
  readonly deps: readonly string[]
  readonly onChange: (deps: readonly string[]) => void
}) {
  const say = useWording()
  const [adding, setAdding] = useState('')
  const add = useCallback(() => {
    const one = adding.trim()
    if (one === '' || deps.includes(one)) return
    onChange([...deps, one])
    setAdding('')
  }, [adding, deps, onChange])
  const drop = useCallback(
    (dep: string) => {
      onChange(deps.filter((one) => one !== dep))
    },
    [deps, onChange],
  )
  const typing = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setAdding(event.target.value)
  }, [])

  return (
    <div className="flex flex-col gap-2">
      <Label>{say('filing.deps')}</Label>
      <div className="flex flex-wrap items-center gap-2">
        {deps.length === 0 ? (
          <span className="text-muted-foreground text-xs">{say('filing.deps.none')}</span>
        ) : (
          deps.map((dep) => <Chip key={dep} dep={dep} onDrop={drop} />)
        )}
      </div>
      <div className="flex gap-2">
        <input
          className={`${BOX} w-32 font-mono`}
          value={adding}
          aria-label={say('filing.deps.add')}
          onChange={typing}
        />
        <Button variant="outline" size="sm" onClick={add}>
          {say('filing.deps.add')}
        </Button>
      </div>
    </div>
  )
}

/** The argv, with the prose elided in the middle so the line stays one a person can read. */
function shortened(word: string): string {
  return word.length <= 24 ? word : `${word.slice(0, 12)}…${word.slice(-8)}`
}

function Command({ argv }: { readonly argv: readonly string[] }) {
  const say = useWording()
  const [copied, setCopied] = useState(false)
  const whole = argv.join(' ')
  const copy = useCallback(() => {
    void Promise.resolve()
      .then(() => navigator.clipboard.writeText(whole))
      .then(
        () => setCopied(true),
        () => setCopied(false),
      )
  }, [whole])

  return (
    <BentoPanel contentClassName="p-5">
      <Label>{say('filing.command')}</Label>
      <pre
        data-testid="command"
        className="bg-muted mt-2 overflow-x-auto rounded p-3 font-mono text-[11px] whitespace-pre-wrap"
      >
        {argv.map(shortened).join(' ')}
      </pre>
      <div className="mt-2 flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={copy}>
          {say('filing.copy')}
        </Button>
        <output className="text-muted-foreground text-xs">
          {copied ? say('filing.copied') : null}
        </output>
      </div>
    </BentoPanel>
  )
}

/** One blank of a door, which says which of them it is when a word is put in it. */
function Blank({
  index,
  word,
  onWord,
}: {
  readonly index: number
  readonly word: string
  readonly onWord: (index: number, word: string) => void
}) {
  const say = useWording()
  const typed = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      onWord(index, event.target.value)
    },
    [index, onWord],
  )
  return (
    <input
      className={`${BOX} mt-2 w-full`}
      aria-label={say('filing.door.blank')}
      value={word}
      onChange={typed}
    />
  )
}

/** One door the engine offered: complete, it runs; incomplete, it asks for its blanks. */
function DoorRow({
  door,
  which,
  onTake,
}: {
  readonly door: Door
  readonly which: number
  readonly onTake: (which: number, words: readonly string[]) => void
}) {
  const say = useWording()
  const blanks = blanksIn(door.argv)
  const [words, setWords] = useState<string[]>(() => blanks.map(() => ''))
  const ready = words.every((word) => word.trim() !== '')
  const take = useCallback(() => {
    onTake(
      which,
      words.map((one) => one.trim()),
    )
  }, [onTake, which, words])
  const word = useCallback((index: number, said: string) => {
    setWords((was) => was.map((one, at) => (at === index ? said : one)))
  }, [])

  return (
    <li className="border-t px-4 py-3 first:border-t-0" data-testid="door">
      <div className="font-mono text-[11px] wrap-anywhere">{door.argv.join(' ')}</div>
      {door.what === '' ? null : <p className="text-muted-foreground mt-1 text-xs">{door.what}</p>}
      {door.writes ? (
        <p className="mt-1">
          <Pill intent="warn">{say('filing.door.writes')}</Pill>
        </p>
      ) : null}
      {blanks.map((at, index) => (
        <Blank key={at} index={index} word={words[index] ?? ''} onWord={word} />
      ))}
      <Button size="sm" className="mt-2" disabled={!ready} onClick={take}>
        {say('filing.door.take')}
      </Button>
    </li>
  )
}

/** What the engine said back, which is either the line it wrote or why it would not. */
function Answered({
  filing,
  say,
}: {
  readonly filing: ReturnType<typeof useFiling>
  readonly say: Translate
}) {
  const { filed, takeDoor } = filing
  if (filed.kind === 'none') return null
  if (filed.kind === 'filing') {
    return <p className="text-muted-foreground text-xs">{say('filing.saving')}</p>
  }
  if (filed.kind === 'failed') {
    return (
      <p className="text-destructive text-xs" data-testid="failed">
        {say('filing.failed', { reason: filed.reason })}
      </p>
    )
  }
  if (filed.kind === 'wrote') {
    return (
      <p className="text-xs" data-testid="wrote">
        {say('filing.wrote', { id: filed.added.id })}
      </p>
    )
  }

  // A refusal: its own sentence, and whatever it offered instead.
  return (
    <div className="flex flex-col gap-2" data-testid="refusal">
      <p className="text-destructive text-xs wrap-anywhere">
        {say('filing.refused', { said: filed.refusal.said })}
      </p>
      {filed.doors.length === 0 ? null : (
        <BentoPanel className="overflow-hidden" contentClassName="p-0">
          <Label>
            <span className="px-4 pt-3 inline-block">{say('filing.doors')}</span>
          </Label>
          <ul>
            {filed.doors.map((door, which) => (
              <DoorRow key={door.argv.join(' ')} door={door} which={which} onTake={takeDoor} />
            ))}
          </ul>
        </BentoPanel>
      )}
    </div>
  )
}

/** What a line here is bound by, which is what decides whether it may be filed at all. */
function Bound({ bounds }: { readonly bounds: Bounds | null }) {
  const say = useWording()
  if (bounds === null) return null

  return (
    <BentoPanel contentClassName="p-5">
      <Label>{say('filing.bounds')}</Label>
      {bounds.nonGoals.length === 0 ? (
        <p className="text-muted-foreground mt-2 text-xs">{say('filing.bounds.none')}</p>
      ) : (
        <ul className="mt-2 flex flex-col gap-2">
          {bounds.nonGoals.map((one) => (
            <li key={one.lead}>
              <div className="text-[13px] font-medium wrap-anywhere">{one.lead}</div>
              {one.why === null || one.why === '' ? null : (
                <div className="text-muted-foreground text-xs wrap-anywhere">{one.why}</div>
              )}
            </li>
          ))}
        </ul>
      )}
    </BentoPanel>
  )
}

/** The words `budget` puts on the section, in its own unit. */
function Words({ budget }: { readonly budget: BudgetPayload | null }) {
  const say = useWording()
  const section = budget === null ? null : sectionCounter(budget)
  if (section === null || section.limit === 0) return null
  return (
    <span className="text-muted-foreground text-xs">
      {say('filing.words', {
        taken: section.taken,
        limit: section.limit,
        unit: section.unit,
      })}
    </span>
  )
}

export function Filing() {
  const say = useWording()
  const params = useParams()
  const navigate = useNavigate()
  const root = decodeURIComponent(params['root'] ?? '')
  const [draft, setDraft] = useState<Draft>(EMPTY_DRAFT)
  const filing = useFiling(root, draft)
  const { budget, command, filed } = filing

  const change = useCallback<Typing>((field, value) => {
    setDraft((was) => ({ ...was, [field]: value }))
  }, [])
  const changeDeps = useCallback((deps: readonly string[]) => {
    setDraft((was) => ({ ...was, deps }))
  }, [])

  // The line it wrote is where this screen goes next, which is what makes filing one act:
  // what a person reviewed as a command becomes the task they are now reading.
  const wrote = filed.kind === 'wrote' ? filed.added.id : ''
  useEffect(() => {
    if (wrote !== '') void navigate(taskPath(root, wrote), { replace: true })
  }, [navigate, root, wrote])

  // The id this would be, which is the engine's answer and not a count of anything here:
  // `budget` names the line `add` would write next, and it moves when someone else files one.
  const named = budget === null ? '' : budget.id
  const about = useMemo(
    () => (
      <span className="flex flex-col gap-0.5">
        <span>{say('filing.about')}</span>
        {named === '' ? null : (
          <span className="font-mono text-xs" data-testid="next-id">
            {say('filing.id', { id: named })}
          </span>
        )}
      </span>
    ),
    [named, say],
  )

  const refused = new Set(fieldsRefused(filed.kind === 'refused' ? filed.refusal : NOTHING))
  const over = budget !== null && anyOver(budget)
  const trailing = useMemo(
    () => (
      <Button size="sm" onClick={filing.file} disabled={over || filed.kind === 'filing'}>
        {say('filing.save')}
      </Button>
    ),
    [filing.file, over, filed.kind, say],
  )

  return (
    <>
      <BentoHero
        backTo={projectPath(root)}
        backLabel={folderName(root)}
        title={say('filing.title')}
        subtitle={about}
        trailing={trailing}
      />
      <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <BentoPanel className="min-w-0" contentClassName="p-6">
          <div className="flex flex-col gap-5">
            <div className="flex flex-wrap gap-4">
              <Field label={say('filing.block')}>
                <Box field="block" value={draft.block} on={change} className="w-24" />
              </Field>
              <Field label={say('filing.marker')}>
                <Box field="status" value={draft.status} on={change} className="w-24" />
              </Field>
              <div className="min-w-48 flex-1">
                <Deps deps={draft.deps} onChange={changeDeps} />
              </div>
            </div>

            {budget === null ? (
              <p className="text-muted-foreground text-xs">{say('filing.pricing')}</p>
            ) : (
              <p className="text-muted-foreground text-xs" data-testid="structure">
                {say('filing.structure', {
                  structure: budget.structure,
                  max: budget.lineMax,
                  prose: budget.prose,
                })}
              </p>
            )}

            <Field
              label={say('filing.symptom')}
              about={say('filing.symptom.about')}
              counter={budget === null ? null : counterFor(budget, 'symptom')}
              refused={refused.has('symptom') ? say('filing.refused', { said: '' }) : undefined}
            >
              <Box field="symptom" value={draft.symptom} on={change} area className="min-h-16" />
            </Field>

            <Field
              label={say('filing.why')}
              about={say('filing.why.about')}
              counter={budget === null ? null : counterFor(budget, 'why')}
              refused={refused.has('why') ? say('filing.refused', { said: '' }) : undefined}
            >
              <Box field="why" value={draft.why} on={change} area className="min-h-16" />
            </Field>

            <Label>{say('filing.section')}</Label>

            <Field label={say('filing.section.title')}>
              <Box field="section" value={draft.section} on={change} />
            </Field>

            <Field label={say('filing.section.body')}>
              <Box
                field="sectionBody"
                value={draft.sectionBody}
                on={change}
                area
                className="min-h-40"
              />
              <Words budget={budget} />
            </Field>
          </div>
        </BentoPanel>

        <div className="flex min-w-0 flex-col gap-3">
          <Command argv={command.argv} />
          <Answered filing={filing} say={say} />
          <Bound bounds={filing.bounds} />
        </div>
      </div>
    </>
  )
}

/** A refusal with nothing in it, so the field marks are read the same way in every state. */
const NOTHING = { refused: [], beside: '', about: '', said: '' }
