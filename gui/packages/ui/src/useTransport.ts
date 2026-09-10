import type { BridgeIdentity, TransportName } from '@rk/core'
import { useEffect, useState } from 'react'

import { getBridge } from './bridge'

/** Absent means no bridge answered — a plain browser tab, or a preload that did not load. */
export type TransportState = TransportName | 'absent' | 'asking'

/**
 * What the bridge says about itself, as a screen reads it.
 *
 * Three states and not a nullable identity: *asking* and *absent* are different things to
 * draw, and a screen handed `null` for both would have to guess which one it was looking
 * at. `identify` answers them together because they are one question — what is carrying
 * these calls, and what is this build — and RG44 put the build there rather than on a
 * method of its own so that widening the bridge did not cost the web port.
 */
export type IdentityState =
  | { readonly kind: 'asking' }
  | { readonly kind: 'absent' }
  | { readonly kind: 'known'; readonly identity: BridgeIdentity }

const ASKING: IdentityState = { kind: 'asking' }
const ABSENT: IdentityState = { kind: 'absent' }

/**
 * Ask the bridge who it is.
 *
 * Each caller asks for itself rather than sharing a cached promise. It is one IPC round
 * trip against a value the main process read once at startup, and a module-level cache
 * would be state a test has to reset — which is the kind of thing that makes two tests
 * pass only in the order they happen to run.
 */
export function useIdentity(): IdentityState {
  const [state, setState] = useState<IdentityState>(ASKING)

  useEffect(() => {
    const bridge = getBridge()
    if (!bridge) {
      setState(ABSENT)
      // `undefined` rather than a bare return: this effect's other path hands React a
      // cleanup, and the two branches have to agree about what the function answers.
      return undefined
    }

    let live = true
    void bridge.identify().then(
      (identity) => {
        if (live) setState({ kind: 'known', identity })
      },
      () => {
        if (live) setState(ABSENT)
      },
    )

    return () => {
      live = false
    }
  }, [])

  return state
}

/**
 * Which transport is carrying the calls. The renderer's only proof that the seam is real,
 * and deliberately the only thing a screen knows about how it is being served.
 */
export function useTransport(): TransportState {
  const state = useIdentity()
  return state.kind === 'known' ? state.identity.transport : state.kind
}
