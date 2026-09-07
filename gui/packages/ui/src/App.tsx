import { PACKAGES, RESPONSIBILITY } from '@rk/core'

import { useTransport } from './useTransport'

const TRANSPORT_LABEL: Record<string, string> = {
  asking: 'asking the bridge…',
  absent: 'no bridge — this page is running as a plain browser page',
  ipc: 'bridged over IPC',
  http: 'bridged over HTTP',
}

/**
 * The scaffold screen. It draws a table `core` owns and names the transport the bridge
 * reports, which together are the only claims this window is entitled to make yet: the
 * three packages compile against each other, and the renderer can reach the outside
 * through exactly one seam. Nothing here reads a backlog — that call path is RG1's.
 */
export function App() {
  const transport = useTransport()

  return (
    <main className="flex h-full flex-col gap-6 overflow-auto bg-neutral-950 p-10 text-neutral-200">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-50">roadkeep</h1>
        <p className="text-sm text-neutral-400">
          The window opens and the three packages are wired. No backlog is read yet.
        </p>
        <p className="text-sm text-neutral-500" data-testid="transport">
          {TRANSPORT_LABEL[transport] ?? transport}
        </p>
      </header>

      <dl className="flex flex-col gap-3">
        {PACKAGES.map((name) => (
          <div
            key={name}
            className="rounded-md border border-neutral-800 bg-neutral-900 px-4 py-3"
          >
            <dt className="font-mono text-sm text-neutral-50">{name}</dt>
            <dd className="mt-1 text-sm text-neutral-400">{RESPONSIBILITY[name]}</dd>
          </div>
        ))}
      </dl>
    </main>
  )
}
