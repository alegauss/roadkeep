import { PACKAGE_TEXT, PACKAGES, type MessageKey } from '@rk/core'
import { Badge, Card, CardContent, CardHeader, CardTitle } from '@viglet/viglet-design-system'

import type { TransportState } from './useTransport'
import { useTransport } from './useTransport'
import { useWording } from './wording'

/**
 * Which string names each state the bridge can be in. Spelled out rather than built from
 * the state, so a state added without wording fails to compile.
 */
const TRANSPORT_TEXT: Readonly<Record<TransportState, MessageKey>> = {
  asking: 'transport.asking',
  absent: 'transport.absent',
  ipc: 'transport.ipc',
  http: 'transport.http',
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
 *
 * **No sentence is written here.** Everything a person reads comes through `say`, and the
 * only bare text left is the package names, which are identifiers. A pseudo-locale test
 * holds that: a literal typed into this file shows up unwrapped and fails the run.
 */
export function App() {
  const transport = useTransport()
  const say = useWording()

  return (
    <main className="bg-background text-foreground h-full overflow-auto">
      <div className="mx-auto flex max-w-3xl flex-col gap-8 px-8 py-12">
        <header className="flex flex-col gap-3">
          <h1 className="font-brand text-3xl font-semibold tracking-tight">{say('app.name')}</h1>
          <p className="text-muted-foreground text-base">{say('app.tagline')}</p>
          <div>
            <Badge variant="secondary" className="font-mono" data-testid="transport">
              {say(TRANSPORT_TEXT[transport])}
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
                {say(PACKAGE_TEXT[name])}
              </CardContent>
            </Card>
          ))}
        </section>
      </div>
    </main>
  )
}
