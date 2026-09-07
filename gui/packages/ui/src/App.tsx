import { PACKAGES, RESPONSIBILITY } from '@roadkeep-gui/core'

/**
 * The scaffold screen. It draws a table `core` owns, which is the only claim this
 * window is entitled to make yet: the three packages compile against each other and
 * a value made outside React reached the renderer. Nothing here reads a backlog —
 * that call path is RG1's, and this screen is what it replaces.
 */
export function App() {
  return (
    <main className="flex h-full flex-col gap-6 overflow-auto bg-neutral-950 p-10 text-neutral-200">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-50">roadkeep</h1>
        <p className="text-sm text-neutral-400">
          The window opens and the three packages are wired. No backlog is read yet.
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
