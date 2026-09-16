import { blanksIn, isBody, type Door } from '@rk/core'
import { Button, Textarea } from '@viglet/viglet-design-system'
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

/**
 * One blank of a door, which says which of them it is when a word goes in it.
 *
 * **A `-` is drawn as prose** (RG261). It is the same blank filled in the same order, but what
 * the engine reads there is a body — paragraphs, where a one-line box would say a word will do.
 */
function Blank({
  index,
  word,
  body,
  onWord,
}: {
  readonly index: number
  readonly word: string
  readonly body: boolean
  readonly onWord: (index: number, word: string) => void
}) {
  const say = useWording()
  const typed = useCallback(
    (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      onWord(index, event.target.value)
    },
    [index, onWord],
  )
  if (body) {
    return (
      <Textarea
        className="mt-2 w-full"
        rows={5}
        aria-label={say('door.body')}
        value={word}
        onChange={typed}
      />
    )
  }
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
  onHandOver,
}: {
  readonly door: Door
  /** Its place in the batch the carrier kept, which is the only name it has. */
  readonly which: number
  readonly onTake: (which: number, words: readonly string[]) => void
  /**
   * Hand this door to a Claude Code session instead (RG263), where the screen offers it.
   *
   * Absent on the filing screen, which is about a line being written now: its refusal's doors
   * are about the draft in the form, and an agent started on one would be working from a
   * command line whose blanks the person in front of it is still filling.
   */
  readonly onHandOver?: (which: number) => void
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
  const hand = useCallback(() => {
    onHandOver?.(which)
  }, [onHandOver, which])

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
        <Blank
          key={at}
          index={index}
          word={words[index] ?? ''}
          body={isBody(door.argv[at] ?? '')}
          onWord={word}
        />
      ))}
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <Button size="sm" disabled={!ready} onClick={take}>
          {say('door.take')}
        </Button>
        {/*
          Never disabled by the blanks (RG263): writing them is the work being handed over,
          and a control that waited for the prose would be waiting for the thing it exists to
          spare the reader.
        */}
        {onHandOver === undefined ? null : (
          <Button size="sm" variant="outline" onClick={hand}>
            {say('door.handOver')}
          </Button>
        )}
      </div>
    </li>
  )
}
