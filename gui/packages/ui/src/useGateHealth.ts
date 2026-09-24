import { UNKNOWN_GATE, type GateHealth } from '@rk/core'
import { useEffect, useState } from 'react'

import { getBridge } from './bridge'

/**
 * What the gate last said about one project, for the tab that counts it (RG255).
 *
 * **Asked once and then heard**, the way a portfolio row hears one (RG166): the carrier runs
 * the gate for a project whose files moved under its verdict, and a count beside a tab that
 * only changed when somebody opened it would be a number going quietly stale on screen.
 *
 * Null until something answers — not `unknown`, which is a verdict a screen may draw: a tab
 * showing *unknown* before the ledger has been asked would say the gate never ran here when
 * nothing has looked.
 */
export function useGateHealth(root: string): GateHealth | null {
  const [health, setHealth] = useState<GateHealth | null>(null)

  useEffect(() => {
    const bridge = getBridge()
    if (bridge === undefined) return undefined
    let live = true

    const stop = bridge.subscribe('gate', root, (gate) => {
      if (live) setHealth(gate.health)
    })
    void bridge.gates().then(
      (gates) => {
        if (!live) return
        const mine = gates.find((one) => one.root === root)
        setHealth(mine?.health ?? UNKNOWN_GATE)
      },
      () => undefined,
    )

    return () => {
      live = false
      stop()
    }
  }, [root])

  return health
}
