import type { Edited, EditedFile } from '@rk/core'
import { useEffect, useState } from 'react'

import { getBridge } from './bridge'

/** Built once: a fresh map per render is a new dependency for everything below it. */
const NOTHING_ANSWERED: ReadonlyMap<string, EditedFile> = new Map()

/**
 * What the disk says about each file a session edited, keyed by the path its call spelled (RG244).
 *
 * **Asked when the stream gives a reason, and never on a timer.** A new file in the list, an edit
 * call answered, and the session ending are each a moment the disk may have moved; nothing is
 * watched that the stream did not name. Nothing is asked before the first edit call is answered,
 * since a call still running has not moved the disk yet, unless the session has ended. An answer
 * to an older ask that lands after a newer one is dropped, so the map is the latest ask's.
 */
export function useEditedAt(
  key: string,
  edited: readonly Edited[],
  ended: boolean,
): ReadonlyMap<string, EditedFile> {
  const [answered, setAnswered] = useState<ReadonlyMap<string, EditedFile>>(NOTHING_ANSWERED)
  // The reasons to ask again, as values an effect can depend on: the paths, and how many
  // editing calls have had their answer.
  const paths = edited.map((one) => one.path).join('\n')
  const settled = edited.filter((one) => one.answered).reduce((sum, one) => sum + one.calls, 0)

  useEffect(() => {
    const bridge = getBridge()
    if (bridge === undefined || paths === '' || (settled === 0 && !ended)) return undefined
    let live = true
    void bridge.editedAt(key, paths.split('\n')).then(
      (files) => {
        if (live) setAnswered(new Map(files.map((file) => [file.path, file])))
      },
      () => undefined,
    )
    return () => {
      live = false
    }
  }, [key, paths, settled, ended])

  return answered
}
