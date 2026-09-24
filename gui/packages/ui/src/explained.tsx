import { lanesOf, type BriefPayload, type Gloss } from '@rk/core'
import { useMemo } from 'react'

import { PanelTitle } from './forms'
import { Glyph } from './marks'
import { Prose } from './prose'
import { useWording } from './wording'

/**
 * The gloss as shapes rather than paragraphs (RG286).
 *
 * Drawn as prose, an explanation is a longer design. A task is grasped at a glance by its shape:
 * what it waits on and what waits on it, what is true now against what is true after, and the
 * path of steps between them.
 *
 * **Facts off the brief, words off the gloss.** Every node of the chain is one the engine
 * answered — `depsResolved` and `unblocks` — with its own marker and readiness, and the gloss
 * only captions it. A dep the gloss skipped keeps its id and says nothing, which is honest; a
 * caption for something the brief never held was dropped before it reached here (RG283).
 *
 * **The shapes are this app's.** Two panels and an arrow, a numbered path, lanes of places, a
 * glossary grid, a callout each for the risks: React and the design system's tokens, so both
 * grounds hold without a palette of their own, and the arrow is the one piece of inline SVG.
 *
 * **No diagram the agent wrote.** Mermaid or SVG in an answer is a program this window would
 * have to run, which `skipHtml` (RG271) and the content policy both refuse. Fixed slots keep
 * every gloss legible and keep the window's drawing its own.
 *
 * Each shape carries its words beside it, and the chain is a list to a screen reader.
 */

/** One node of the chain: what the engine said it is, and what the gloss called it. */
interface Node {
  readonly id: string
  /** The marker and the state the engine answered, never a word worked out here. */
  readonly marker: string
  readonly standing: string
  readonly said: string
}

function nodesBefore(payload: BriefPayload, gloss: Gloss): Node[] {
  return payload.depsResolved.map((dep) => ({
    id: dep.dep,
    marker: '',
    standing: dep.status,
    said: gloss.deps[dep.dep] ?? '',
  }))
}

function nodesAfter(payload: BriefPayload, gloss: Gloss): Node[] {
  const unblocks = payload.unblocks
  if (unblocks === null) return []
  const ids = [...new Set([...unblocks.direct, ...unblocks.transitive])]
  return ids.map((id) => ({ id, marker: '', standing: '', said: gloss.unblocks[id] ?? '' }))
}

/** One node drawn: its id, what the engine says of it, and the gloss's sentence under both. */
function Chip({ node, testid }: { readonly node: Node; readonly testid: string }) {
  return (
    <li
      className="bg-card flex min-w-0 flex-col gap-0.5 rounded-lg border px-3 py-2"
      data-testid={testid}
      data-id={node.id}
    >
      <span className="flex items-center gap-1.5">
        {node.marker === '' ? null : <Glyph>{node.marker}</Glyph>}
        <span className="font-mono text-xs font-semibold">{node.id}</span>
        {node.standing === '' ? null : (
          <span className="text-muted-foreground text-[11px]">{node.standing}</span>
        )}
      </span>
      {node.said === '' ? null : (
        <span className="text-muted-foreground text-xs">
          <Prose text={node.said} />
        </span>
      )}
    </li>
  )
}

/** The one piece of inline SVG: an arrow between two panels, or down them when narrow. */
function Arrow() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className="text-muted-foreground size-5 shrink-0 max-sm:rotate-90"
    >
      <path
        d="M3 12h16M13 6l6 6-6 6"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

/** What the line waits on, the line itself, and what finishing it frees. */
function Chain({ payload, gloss }: { readonly payload: BriefPayload; readonly gloss: Gloss }) {
  const say = useWording()
  const before = nodesBefore(payload, gloss)
  const after = nodesAfter(payload, gloss)
  // The line itself, as the engine marks and reads it: its own node in the chain.
  const here = useMemo(
    () => ({ id: payload.id, marker: payload.status, standing: payload.readiness, said: '' }),
    [payload],
  )
  if (before.length === 0 && after.length === 0) return null

  return (
    <section className="mt-5" data-testid="explain-chain">
      <PanelTitle>{say('explain.chain')}</PanelTitle>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-stretch">
        <div className="min-w-0 flex-1">
          <p className="text-muted-foreground mb-1 text-[11px]">{say('explain.deps')}</p>
          <ul className="flex flex-col gap-1.5">
            {before.length === 0 ? (
              <li className="text-muted-foreground text-xs">{say('explain.chain.none')}</li>
            ) : (
              before.map((node) => <Chip key={node.id} node={node} testid="explain-dep" />)
            )}
          </ul>
        </div>
        <div className="flex items-center justify-center">
          <Arrow />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-muted-foreground mb-1 text-[11px]">{say('explain.chain.this')}</p>
          <ul className="flex flex-col gap-1.5">
            <Chip node={here} testid="explain-this" />
          </ul>
        </div>
        <div className="flex items-center justify-center">
          <Arrow />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-muted-foreground mb-1 text-[11px]">{say('explain.unblocks')}</p>
          <ul className="flex flex-col gap-1.5">
            {after.length === 0 ? (
              <li className="text-muted-foreground text-xs">{say('explain.chain.none')}</li>
            ) : (
              after.map((node) => <Chip key={node.id} node={node} testid="explain-unblocks" />)
            )}
          </ul>
        </div>
      </div>
    </section>
  )
}

/** What is true now against what is true after: two panels, and the arrow between them. */
function BeforeAfter({ gloss }: { readonly gloss: Gloss }) {
  const say = useWording()
  if (gloss.today === '' && gloss.after === '') return null

  return (
    <section className="mt-5" data-testid="explain-turn">
      <div className="flex flex-col items-stretch gap-2 sm:flex-row sm:items-center">
        <div className="bg-muted/40 min-w-0 flex-1 rounded-lg border p-3">
          <PanelTitle>{say('explain.today')}</PanelTitle>
          <div className="text-sm">
            <Prose text={gloss.today} />
          </div>
        </div>
        <Arrow />
        <div className="bg-card min-w-0 flex-1 rounded-lg border p-3">
          <PanelTitle>{say('explain.after')}</PanelTitle>
          <div className="text-sm">
            <Prose text={gloss.after} />
          </div>
        </div>
      </div>
    </section>
  )
}

/** The steps as a path: across where there is room, down where there is not. */
function Steps({ steps }: { readonly steps: readonly string[] }) {
  const say = useWording()
  if (steps.length === 0) return null

  return (
    <section className="mt-5" data-testid="explain-steps">
      <PanelTitle>{say('explain.steps')}</PanelTitle>
      <ol className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {steps.map((step, at) => (
          <li
            key={step}
            className="bg-card flex min-w-0 flex-1 items-start gap-2 rounded-lg border p-3 text-sm"
          >
            <span className="bg-muted text-muted-foreground flex size-5 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold">
              {at + 1}
            </span>
            <span className="min-w-0">
              <Prose text={step} />
            </span>
          </li>
        ))}
      </ol>
    </section>
  )
}

/**
 * Where the work lands (RG288): one lane per top-level folder, each place under its own.
 *
 * The lanes are the paths' own — `lanesOf` groups on what the answer spelled — because which
 * folders a project has is the project's, and a list of them here would draw this repository and
 * no other. A file at the root gets the lane with no folder, which the wording names.
 */
function Where({ gloss }: { readonly gloss: Gloss }) {
  const say = useWording()
  const lanes = useMemo(() => lanesOf(gloss.where), [gloss.where])
  if (lanes.length === 0) return null

  return (
    <section className="mt-5" data-testid="explain-where">
      <PanelTitle>{say('explain.where')}</PanelTitle>
      <div className="flex flex-col gap-2">
        {lanes.map((lane) => (
          <div
            key={lane.folder}
            className="bg-card rounded-lg border p-3"
            data-testid="explain-lane"
            data-folder={lane.folder}
          >
            <p className="font-mono text-xs font-semibold wrap-anywhere">
              {lane.folder === '' ? say('explain.where.root') : lane.folder}
            </p>
            <ul className="mt-2 grid gap-2 sm:grid-cols-2">
              {lane.places.map((place) => (
                <li
                  key={place.path}
                  className="bg-muted/40 min-w-0 rounded-lg border p-2"
                  data-testid="explain-place"
                >
                  <p className="font-mono text-xs wrap-anywhere">{place.path}</p>
                  <div className="text-muted-foreground mt-1 text-sm">
                    <Prose text={place.said} />
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  )
}

/** The words the line uses, as a glossary: the term, and what it means here. */
function Terms({ gloss }: { readonly gloss: Gloss }) {
  const say = useWording()
  if (gloss.terms.length === 0) return null

  return (
    <section className="mt-5" data-testid="explain-terms">
      <PanelTitle>{say('explain.terms')}</PanelTitle>
      <dl className="grid gap-2 sm:grid-cols-2">
        {gloss.terms.map((term) => (
          <div key={term.term} className="bg-card rounded-lg border p-3">
            <dt className="font-mono text-xs font-semibold wrap-anywhere">{term.term}</dt>
            <dd className="text-muted-foreground mt-1 text-sm">
              <Prose text={term.said} />
            </dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

/** Each risk as a callout, and what finished looks like beside it. */
function RisksAndDone({ gloss }: { readonly gloss: Gloss }) {
  const say = useWording()
  return (
    <>
      {gloss.risks.length === 0 ? null : (
        <section className="mt-5" data-testid="explain-risks">
          <PanelTitle>{say('explain.risks')}</PanelTitle>
          <ul className="flex flex-col gap-2">
            {gloss.risks.map((risk) => (
              <li
                key={risk}
                className="border-l-primary bg-muted/40 rounded-r-lg border border-l-4 p-3 text-sm"
              >
                <Prose text={risk} />
              </li>
            ))}
          </ul>
        </section>
      )}
      {gloss.done.length === 0 ? null : (
        <section className="mt-5" data-testid="explain-done">
          <PanelTitle>{say('explain.done')}</PanelTitle>
          <ul className="ml-5 flex list-outside list-disc flex-col gap-1.5 text-sm">
            {gloss.done.map((one) => (
              <li key={one}>
                <Prose text={one} />
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  )
}

/** The non-goals binding the line: the lead as the file spells it, over what it means here. */
function Binds({ payload, gloss }: { readonly payload: BriefPayload; readonly gloss: Gloss }) {
  const say = useWording()
  const bound = payload.nonGoals.filter((lead) => gloss.binds[lead] !== undefined)
  if (bound.length === 0) return null

  return (
    <section className="mt-5" data-testid="explain-binds">
      <PanelTitle>{say('explain.binds')}</PanelTitle>
      <div className="grid gap-2 sm:grid-cols-2">
        {bound.map((lead) => (
          <div key={lead} className="bg-card rounded-lg border p-3">
            <p className="text-xs font-semibold wrap-anywhere">{lead}</p>
            <div className="text-muted-foreground mt-1 text-sm">
              <Prose text={gloss.binds[lead] ?? ''} />
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

/** The whole gloss, in the shapes above: the headline first, and the chain under it. */
export function Explained({
  payload,
  gloss,
}: {
  readonly payload: BriefPayload
  readonly gloss: Gloss
}) {
  return (
    <div data-testid="explain-said">
      {gloss.headline === '' ? null : (
        <div className="text-lg font-semibold wrap-anywhere">
          <Prose text={gloss.headline} />
        </div>
      )}
      <BeforeAfter gloss={gloss} />
      <Chain payload={payload} gloss={gloss} />
      <Steps steps={gloss.steps} />
      <Where gloss={gloss} />
      <Terms gloss={gloss} />
      <RisksAndDone gloss={gloss} />
      <Binds payload={payload} gloss={gloss} />
    </div>
  )
}
