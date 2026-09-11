import { blanksIn, type Door } from '@rk/core'
import { Button } from '@viglet/viglet-design-system'
import { useCallback, useState, type ChangeEvent } from 'react'

import { BOX } from './forms'
import { Pill } from './marks'
import { useWording } from './wording'

/**
 * A door the engine offered, drawn the one way this app draws one (RG152).
 *
 * It came out of the write path, where RG151 drew a refusal's doors, because the gate offers
 * the same thing: a finding names the command that closes it in the shape `explain` publishes
 * for a refusal's code, so a screen that drew them differently would be saying they are
 * different. They are the same thing at two moments.
 *
 * **The argv shown is the engine's and is never sent.** A complete door runs as it stands; an
 * incomplete one has the blanks the engine left and waits for a word in each. What crosses is
 * which door and the words — the carrier holds the argv (RG165) — so nothing here can compose
 * a command, and a door whose blanks are not all filled cannot be taken at all.
 */

/** One blank of a door, which says which of them it is when a word goes in it. */
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
      aria-label={say('door.blank')}
      value={word}
      onChange={typed}
    />
  )
}

export function DoorRow({
  door,
  which,
  onTake,
}: {
  readonly door: Door
  /** Its place in the batch the carrier kept, which is the only name it has. */
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
          <Pill intent="warn">{say('door.writes')}</Pill>
        </p>
      ) : null}
      {blanks.map((at, index) => (
        <Blank key={at} index={index} word={words[index] ?? ''} onWord={word} />
      ))}
      <Button size="sm" className="mt-2" disabled={!ready} onClick={take}>
        {say('door.take')}
      </Button>
    </li>
  )
}
