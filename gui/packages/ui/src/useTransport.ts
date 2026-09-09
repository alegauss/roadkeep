import type { TransportName } from '@rk/core'
import { useEffect, useState } from 'react'

import { getBridge } from './bridge'

/** Absent means no bridge answered — a plain browser tab, or a preload that did not load. */
export type TransportState = TransportName | 'absent' | 'asking'

/**
 * Ask the bridge what is carrying its calls. This is the renderer's only proof that the
 * seam is real, and it is deliberately the only thing the screen knows about how it is
 * being served.
 */
export function useTransport(): TransportState {
  const [transport, setTransport] = useState<TransportState>('asking')

  useEffect(() => {
    const bridge = getBridge()
    if (!bridge) {
      setTransport('absent')
      // `undefined` rather than a bare return: this effect's other path hands React a
      // cleanup, and the two branches have to agree about what the function answers.
      return undefined
    }

    let live = true
    void bridge.identify().then(
      (identity) => {
        if (live) setTransport(identity.transport)
      },
      () => {
        if (live) setTransport('absent')
      },
    )

    return () => {
      live = false
    }
  }, [])

  return transport
}
