import { PACKAGES, RESPONSIBILITY } from '@rk/core'
import { Badge, Card, CardContent, CardHeader, CardTitle } from '@viglet/viglet-design-system'

import { useTransport } from './useTransport'

const TRANSPORT_LABEL: Record<string, string> = {
  asking: 'asking the bridge',
  absent: 'no bridge - running as a plain browser page',
  ipc: 'bridged over IPC',
  http: 'bridged over HTTP',
}

/**
 * The scaffold screen. It draws a table `core` owns and names the transport the bridge
 * reports, which together are the only claims this window is entitled to make yet: the
 * three packages compile against each other, and the renderer can reach the outside
 * through exactly one seam. Nothing here reads a backlog - that call path is RG1's.
 *
 * Every colour, radius and face on this screen comes from the design system's tokens.
 * The utility classes name roles - `bg-background`, `text-muted-foreground`, `border` -
 * and never values, which is what lets the same markup render on either ground once RG52
 * wires the switch.
 */
export function App() {
  const transport = useTransport()

  return (
    <main className="bg-background text-foreground h-full overflow-auto">
      <div className="mx-auto flex max-w-3xl flex-col gap-8 px-8 py-12">
        <header className="flex flex-col gap-3">
          <h1 className="font-brand text-3xl font-semibold tracking-tight">roadkeep</h1>
          <p className="text-muted-foreground text-base">
            The window opens and the three packages are wired. No backlog is read yet.
          </p>
          <div>
            <Badge variant="secondary" className="font-mono" data-testid="transport">
              {TRANSPORT_LABEL[transport] ?? transport}
            </Badge>
          </div>
        </header>

        <section className="flex flex-col gap-4">
          {PACKAGES.map((name) => (
            <Card key={name}>
              <CardHeader>
                <CardTitle className="font-mono text-sm">{name}</CardTitle>
              </CardHeader>
              <CardContent className="text-muted-foreground text-sm">
                {RESPONSIBILITY[name]}
              </CardContent>
            </Card>
          ))}
        </section>
      </div>
    </main>
  )
}
