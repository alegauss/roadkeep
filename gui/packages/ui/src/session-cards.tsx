import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  pointerWithin,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
  type Announcements,
  type DragMoveEvent,
  type DragStartEvent,
  type KeyboardCoordinateGetter,
} from '@dnd-kit/core'
import {
  isSessionCard,
  moveCard,
  placeOf,
  sameLayout,
  steppedPlace,
  type CardPlace,
  type CardStep,
  type MessageKey,
  type SessionCard,
  type SessionLayout,
  type SessionSide,
} from '@rk/core'
import { IconDotsVertical, IconGripVertical } from '@tabler/icons-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@viglet/viglet-design-system'
import { useCallback, useMemo, useRef, useState, type ReactNode } from 'react'

import { chooseSessionLayout, useSessionLayout } from './preferring'
import { useWording } from './wording'

/**
 * The session screen's grid: the stream in the middle, and a side bar each side of it holding
 * the cards the settings file puts there (RG276). Each card moves by the grip in its title row,
 * to the other side bar or along its own (RG277), the way VS Code moves a view by its title.
 *
 * **The stream is written first**, and placed in the middle (RG225): stacked below `lg`, the
 * grid falls in the order it is written, so the session's own words — what a reader opened this
 * screen for — come before the cards at 400 wide, and first for a screen reader at every width.
 *
 * **Laid out as an editor is** (RG237): from `xl` a side bar left of the stream and one right of
 * it. A side bar left empty gives its column to the stream, and while a card is being moved it
 * is a thin strip that still takes a drop. Between `lg` and `xl` one side column holds the left
 * bar's cards over the right's, the stream spanning both rows, since three columns at 1024 would
 * leave the stream where the reading column had it.
 *
 * **The drop lands where the pointer is**, under an insertion line: counted against the middle
 * of each card in the side bar under the pointer, and drawn in the gap it will open. So the drag
 * is `@dnd-kit/core` and not its sortable preset, whose lists reorder by sliding cards aside as
 * the dragged one passes — a card that tall slides the drop target out from under the pointer.
 *
 * **The grip is drawn from `xl`**, where two side bars exist. A key moves a card by places, not
 * by pixels: Space picks it up, the arrows choose a place, Space drops it and Escape puts it
 * back, each said in the window's language. Beside the grip, a menu makes the same moves with no
 * drag at all (RG278), one arrow key's step per entry.
 */

const SIDES: readonly SessionSide[] = ['left', 'right']

/** Each card by its own title, which is what a person moving it is told it is. */
const CARD_TEXT: Readonly<Record<SessionCard, MessageKey>> = {
  handed: 'session.handed',
  moved: 'session.moved',
  files: 'session.edited',
}

/** Where a card being moved would land, said as it moves. */
const AT_TEXT: Readonly<Record<SessionSide, MessageKey>> = {
  left: 'session.card.at.left',
  right: 'session.card.at.right',
}

const DROPPED_TEXT: Readonly<Record<SessionSide, MessageKey>> = {
  left: 'session.card.dropped.left',
  right: 'session.card.dropped.right',
}

/** The id each side bar takes a drop under, which no card is called. */
const SIDE_ID: Readonly<Record<SessionSide, string>> = { left: 'side-left', right: 'side-right' }

function sideOf(id: unknown): SessionSide | null {
  if (id === SIDE_ID.left) return 'left'
  if (id === SIDE_ID.right) return 'right'
  return null
}

const STEPS = new Map<string, CardStep>([
  ['ArrowUp', 'up'],
  ['ArrowDown', 'down'],
  ['ArrowLeft', 'left'],
  ['ArrowRight', 'right'],
])

/** A pointer moves nothing until it has travelled this far, so a click on a grip stays a click. */
const POINTER = { activationConstraint: { distance: 4 } }

/**
 * Nothing said by the library: a key moves a card without moving the pointer it tracks, so its
 * announcements would say where the card was picked up for the whole of a keyboard move. The
 * screen says each place itself, from the one state the drop reads.
 */
const SILENT: Announcements = {
  onDragStart: () => undefined,
  onDragOver: () => undefined,
  onDragEnd: () => undefined,
  onDragCancel: () => undefined,
}

/** Which columns the grid draws, by what each side bar holds. */
type Columns = 'both' | 'left' | 'right' | 'left-strip' | 'right-strip'

interface Placing {
  readonly grid: string
  readonly stream: string
  readonly left: string
  readonly right: string
}

/** A stream with a side bar on each side of it, at `xl`; one side column below it. */
const FLANKED = {
  stream: 'lg:col-start-2 lg:row-span-2 lg:row-start-1 xl:col-start-2 xl:row-span-1',
  left: 'lg:col-start-1 lg:row-start-1 xl:col-start-1',
  right: 'lg:col-start-1 lg:row-start-2 xl:col-start-3 xl:row-start-1',
}

// Spelled out whole, since Tailwind generates only the classes it finds written in a source.
const PLACING: Readonly<Record<Columns, Placing>> = {
  both: {
    grid: 'lg:grid-cols-[18rem_minmax(0,1fr)] lg:grid-rows-[auto_1fr] xl:grid-cols-[18rem_minmax(0,1fr)_18rem] xl:grid-rows-none',
    ...FLANKED,
  },
  'left-strip': {
    grid: 'lg:grid-cols-[18rem_minmax(0,1fr)] lg:grid-rows-[auto_1fr] xl:grid-cols-[2.5rem_minmax(0,1fr)_18rem] xl:grid-rows-none',
    ...FLANKED,
  },
  'right-strip': {
    grid: 'lg:grid-cols-[18rem_minmax(0,1fr)] lg:grid-rows-[auto_1fr] xl:grid-cols-[18rem_minmax(0,1fr)_2.5rem] xl:grid-rows-none',
    ...FLANKED,
  },
  left: {
    grid: 'lg:grid-cols-[18rem_minmax(0,1fr)]',
    stream: 'lg:col-start-2 lg:row-start-1',
    left: 'lg:col-start-1 lg:row-start-1',
    right: '',
  },
  right: {
    grid: 'lg:grid-cols-[18rem_minmax(0,1fr)] xl:grid-cols-[minmax(0,1fr)_18rem]',
    stream: 'lg:col-start-2 lg:row-start-1 xl:col-start-1',
    left: '',
    right: 'lg:col-start-1 lg:row-start-1 xl:col-start-2',
  },
}

function columnsOf(layout: SessionLayout, moving: boolean): Columns {
  if (layout.left.length === 0) return moving ? 'left-strip' : 'right'
  if (layout.right.length === 0) return moving ? 'right-strip' : 'left'
  return 'both'
}

/** Where the insertion line goes: beside one card, or in an empty side bar's strip. */
type Line =
  | { readonly kind: 'card'; readonly card: SessionCard; readonly edge: 'before' | 'after' }
  | { readonly kind: 'strip'; readonly side: SessionSide }

/** No line where the drop would leave the card where it is: nothing would move. */
function lineAt(layout: SessionLayout, card: SessionCard, place: CardPlace | null): Line | null {
  if (place === null || sameLayout(moveCard(layout, card, place.side, place.index), layout)) {
    return null
  }
  const others = layout[place.side].filter((one) => one !== card)
  const next = others[place.index]
  if (next !== undefined) return { kind: 'card', card: next, edge: 'before' }
  const last = others.at(-1)
  return last === undefined
    ? { kind: 'strip', side: place.side }
    : { kind: 'card', card: last, edge: 'after' }
}

function samePlace(one: CardPlace | null, other: CardPlace | null): boolean {
  return one?.side === other?.side && one?.index === other?.index
}

/** The vertical middle of a card as drawn, which the pointer is counted against. */
function middleOf(node: HTMLElement | undefined): number {
  if (node === undefined) return Number.POSITIVE_INFINITY
  const box = node.getBoundingClientRect()
  return box.top + box.height / 2
}

/**
 * What follows the pointer while a card moves: its title, not a second copy of the card.
 *
 * The overlay is the grip's size, and the grip sits at a card's right edge — so the title grows
 * leftward from it, where a card on the right side bar has room and the window's edge does not.
 */
function Lifted({ card }: { readonly card: SessionCard }) {
  const say = useWording()
  return (
    <div className="bg-card text-foreground pointer-events-none absolute top-0 right-0 inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-[11px] font-semibold tracking-wider whitespace-nowrap uppercase shadow-lg">
      <IconGripVertical size={14} aria-hidden="true" />
      {say(CARD_TEXT[card])}
    </div>
  )
}

/**
 * The same moves without a drag (RG278), as VS Code's Move View is beside its drag: to the other
 * side bar, up and down. An entry that would move nothing is not offered — up on the first card,
 * down on the last — and each is the step an arrow key takes, so a menu and a key agree.
 */
function CardMenu({
  card,
  side,
  first,
  last,
  onStep,
  onTrigger,
  refocus,
}: {
  readonly card: SessionCard
  readonly side: SessionSide
  readonly first: boolean
  readonly last: boolean
  readonly onStep: (card: SessionCard, step: CardStep) => void
  readonly onTrigger: (card: SessionCard, node: HTMLButtonElement | null) => void
  readonly refocus: (card: SessionCard) => void
}) {
  const say = useWording()
  const across = useCallback(() => {
    onStep(card, side === 'left' ? 'right' : 'left')
  }, [card, side, onStep])
  const up = useCallback(() => {
    onStep(card, 'up')
  }, [card, onStep])
  const down = useCallback(() => {
    onStep(card, 'down')
  }, [card, onStep])
  const kept = useCallback(
    (node: HTMLButtonElement | null) => {
      onTrigger(card, node)
    },
    [card, onTrigger],
  )
  // A card moved to the other side bar is drawn anew there, so the trigger the menu would hand
  // focus back to is gone: focus goes to this card's trigger wherever it is drawn now.
  const closed = useCallback(
    (event: Event) => {
      event.preventDefault()
      refocus(card)
    },
    [card, refocus],
  )

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          ref={kept}
          type="button"
          aria-label={say('session.card.menu', { card: say(CARD_TEXT[card]) })}
          className="text-muted-foreground hover:text-foreground inline-flex rounded p-0.5 opacity-0 group-hover/card:opacity-100 focus-visible:opacity-100 data-[state=open]:opacity-100"
        >
          <IconDotsVertical size={14} aria-hidden="true" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" onCloseAutoFocus={closed}>
        <DropdownMenuItem onSelect={across}>
          {say(side === 'left' ? 'session.card.toRight' : 'session.card.toLeft')}
        </DropdownMenuItem>
        {first ? null : <DropdownMenuItem onSelect={up}>{say('session.card.up')}</DropdownMenuItem>}
        {last ? null : (
          <DropdownMenuItem onSelect={down}>{say('session.card.down')}</DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function MovableCard({
  card,
  side,
  first,
  last,
  lifted,
  line,
  onNode,
  onStep,
  onTrigger,
  refocus,
  children,
}: {
  readonly card: SessionCard
  readonly side: SessionSide
  readonly first: boolean
  readonly last: boolean
  readonly lifted: boolean
  readonly line: 'before' | 'after' | null
  readonly onNode: (card: SessionCard, node: HTMLDivElement | null) => void
  readonly onStep: (card: SessionCard, step: CardStep) => void
  readonly onTrigger: (card: SessionCard, node: HTMLButtonElement | null) => void
  readonly refocus: (card: SessionCard) => void
  readonly children: ReactNode
}) {
  const say = useWording()
  const { attributes, listeners, setNodeRef } = useDraggable({
    id: card,
    attributes: { roleDescription: say('session.card.role') },
  })
  const kept = useCallback(
    (node: HTMLDivElement | null) => {
      onNode(card, node)
    },
    [card, onNode],
  )

  return (
    <div
      ref={kept}
      className={`group/card relative min-w-0 ${lifted ? 'opacity-50' : ''}`}
      data-region={`session-${card}`}
    >
      {line === 'before' ? (
        <span
          aria-hidden="true"
          className="bg-primary absolute inset-x-0 -top-2.75 h-0.5 rounded-full"
          data-testid="card-line"
        />
      ) : null}
      {/* Before the card in the document, so Tab reaches the grip and then the menu at the
          card's title. */}
      <div className="absolute top-4 right-4 z-10 flex items-center gap-0.5 max-xl:invisible">
        <button
          ref={setNodeRef}
          type="button"
          {...attributes}
          {...listeners}
          aria-label={say('session.card.grip', { card: say(CARD_TEXT[card]) })}
          className="text-muted-foreground hover:text-foreground inline-flex cursor-grab rounded p-0.5 opacity-0 group-hover/card:opacity-100 focus-visible:opacity-100"
        >
          <IconGripVertical size={14} aria-hidden="true" />
        </button>
        <CardMenu
          card={card}
          side={side}
          first={first}
          last={last}
          onStep={onStep}
          onTrigger={onTrigger}
          refocus={refocus}
        />
      </div>
      {children}
      {line === 'after' ? (
        <span
          aria-hidden="true"
          className="bg-primary absolute inset-x-0 -bottom-2.75 h-0.5 rounded-full"
          data-testid="card-line"
        />
      ) : null}
    </div>
  )
}

function SideBar({
  side,
  placed,
  holds,
  moving,
  aimed,
  children,
}: {
  readonly side: SessionSide
  readonly placed: string
  readonly holds: number
  readonly moving: boolean
  /** Whether the insertion line is this side bar's strip. */
  readonly aimed: boolean
  readonly children: ReactNode
}) {
  const { setNodeRef } = useDroppable({ id: SIDE_ID[side] })
  if (holds === 0 && !moving) return null
  if (holds === 0) {
    return (
      <div
        ref={setNodeRef}
        className={`min-h-24 rounded-lg border-2 border-dashed xl:self-stretch ${aimed ? 'border-primary bg-primary/5' : 'border-border'} ${placed}`}
        data-side={side}
        data-testid="card-strip"
      />
    )
  }
  return (
    <div
      ref={setNodeRef}
      className={`flex min-w-0 flex-col gap-5 xl:self-stretch ${placed}`}
      data-side={side}
    >
      {children}
    </div>
  )
}

interface Moving {
  readonly card: SessionCard
  readonly place: CardPlace | null
}

export function SessionCards({
  stream,
  cards,
}: {
  readonly stream: ReactNode
  readonly cards: Readonly<Record<SessionCard, ReactNode>>
}) {
  const say = useWording()
  const layout = useSessionLayout()
  const [lifted, setLifted] = useState<SessionCard | null>(null)
  const [place, setPlace] = useState<CardPlace | null>(null)
  const [said, setSaid] = useState('')
  // What the handlers read, rather than a render's copy: one drag outlives many renders, and a
  // key pressed twice in a frame must step from where the first press left it.
  const moving = useRef<Moving | null>(null)
  const nodes = useRef(new Map<SessionCard, HTMLElement>())

  const held = useCallback((card: SessionCard, node: HTMLDivElement | null) => {
    if (node === null) nodes.current.delete(card)
    else nodes.current.set(card, node)
  }, [])

  const aim = useCallback(
    (next: CardPlace | null) => {
      const now = moving.current
      if (now === null || samePlace(now.place, next)) return
      moving.current = { card: now.card, place: next }
      setPlace(next)
      if (next !== null) {
        setSaid(say(AT_TEXT[next.side], { card: say(CARD_TEXT[now.card]), place: next.index + 1 }))
      }
    },
    [say],
  )

  const started = useCallback(
    (event: DragStartEvent) => {
      const card = event.active.id
      if (!isSessionCard(card)) return
      const at = placeOf(layout, card)
      moving.current = { card, place: at }
      setLifted(card)
      setPlace(at)
      setSaid(say('session.card.lifted', { card: say(CARD_TEXT[card]) }))
    },
    [layout, say],
  )

  // Only a pointer is followed: a key moves the card by places, and never moves this.
  const moved = useCallback(
    (event: DragMoveEvent) => {
      const now = moving.current
      const start = event.activatorEvent
      if (now === null || !(start instanceof PointerEvent)) return
      const side = sideOf(event.over?.id)
      if (side === null) {
        aim(null)
        return
      }
      const y = start.clientY + event.delta.y
      const above = layout[side].filter(
        (one) => one !== now.card && middleOf(nodes.current.get(one)) < y,
      )
      aim({ side, index: above.length })
    },
    [layout, aim],
  )

  const settle = useCallback((): Moving | null => {
    const now = moving.current
    moving.current = null
    setLifted(null)
    setPlace(null)
    return now
  }, [])

  const ended = useCallback(() => {
    const now = settle()
    if (now === null) return
    const name = say(CARD_TEXT[now.card])
    const lands =
      now.place === null ? layout : moveCard(layout, now.card, now.place.side, now.place.index)
    if (now.place === null || sameLayout(lands, layout)) {
      setSaid(say('session.card.back', { card: name }))
      return
    }
    setSaid(say(DROPPED_TEXT[now.place.side], { card: name, place: now.place.index + 1 }))
    chooseSessionLayout(lands)
  }, [layout, say, settle])

  const cancelled = useCallback(() => {
    const now = settle()
    if (now !== null) setSaid(say('session.card.back', { card: say(CARD_TEXT[now.card]) }))
  }, [say, settle])

  // A menu entry: the step an arrow key takes, kept as a drop is (RG278).
  const stepped = useCallback(
    (card: SessionCard, step: CardStep) => {
      const from = placeOf(layout, card)
      if (from === null) return
      const to = steppedPlace(layout, card, from, step)
      const lands = moveCard(layout, card, to.side, to.index)
      if (sameLayout(lands, layout)) return
      setSaid(say(DROPPED_TEXT[to.side], { card: say(CARD_TEXT[card]), place: to.index + 1 }))
      chooseSessionLayout(lands)
    },
    [layout, say],
  )

  const triggers = useRef(new Map<SessionCard, HTMLButtonElement>())
  const menuHeld = useCallback((card: SessionCard, node: HTMLButtonElement | null) => {
    if (node === null) triggers.current.delete(card)
    else triggers.current.set(card, node)
  }, [])
  // After the frame the move is drawn in, so the trigger found is the one drawn now.
  const refocus = useCallback((card: SessionCard) => {
    requestAnimationFrame(() => {
      triggers.current.get(card)?.focus()
    })
  }, [])

  const keys = useMemo(() => {
    const coordinateGetter: KeyboardCoordinateGetter = (event) => {
      const step = STEPS.get(event.code)
      const now = moving.current
      if (step === undefined || now === null) return undefined
      event.preventDefault()
      const from = now.place ?? placeOf(layout, now.card)
      if (from !== null) aim(steppedPlace(layout, now.card, from, step))
      // Nothing for the library to move: the place is the screen's, and the line draws it.
      return undefined
    }
    return { coordinateGetter }
  }, [layout, aim])
  const sensors = useSensors(useSensor(PointerSensor, POINTER), useSensor(KeyboardSensor, keys))

  const accessibility = useMemo(
    () => ({
      announcements: SILENT,
      screenReaderInstructions: { draggable: say('session.card.instructions') },
    }),
    [say],
  )

  const placing = PLACING[columnsOf(layout, lifted !== null)]
  const line = lifted === null ? null : lineAt(layout, lifted, place)

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={pointerWithin}
      accessibility={accessibility}
      onDragStart={started}
      onDragMove={moved}
      onDragEnd={ended}
      onDragCancel={cancelled}
    >
      <div className={`grid items-start gap-5 ${placing.grid}`}>
        <div className={`min-w-0 ${placing.stream}`} data-region="session-stream">
          {stream}
        </div>
        {SIDES.map((side) => (
          <SideBar
            key={side}
            side={side}
            placed={placing[side]}
            holds={layout[side].length}
            moving={lifted !== null}
            aimed={line?.kind === 'strip' && line.side === side}
          >
            {layout[side].map((card, index, all) => (
              <MovableCard
                key={card}
                card={card}
                side={side}
                first={index === 0}
                last={index === all.length - 1}
                lifted={lifted === card}
                line={line?.kind === 'card' && line.card === card ? line.edge : null}
                onNode={held}
                onStep={stepped}
                onTrigger={menuHeld}
                refocus={refocus}
              >
                {cards[card]}
              </MovableCard>
            ))}
          </SideBar>
        ))}
      </div>
      {/* Transparent to the pointer, which it follows: a drop lands on the card under it. */}
      <DragOverlay dropAnimation={null} className="pointer-events-none">
        {lifted === null ? null : <Lifted card={lifted} />}
      </DragOverlay>
      <div aria-live="assertive" aria-atomic="true" className="sr-only" data-testid="card-said">
        {said}
      </div>
    </DndContext>
  )
}
