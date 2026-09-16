import { folderName, nameOf, type Declared } from '@rk/core'
import { IconChevronRight, IconFolder } from '@tabler/icons-react'
import { BENTO_TONES, BentoBackLink, bentoChipClass } from '@viglet/viglet-design-system/bento'
import { Link } from 'react-router-dom'

import { projectPath, taskPath } from './areas'

/**
 * How a project is recognised on every screen that draws it (RG242).
 *
 * **The chip is the portfolio's.** The tinted square a row is known by — the logo where one
 * resolved, the declared emoji next, the folder glyph last (RG200, RG204) — in the tone its
 * name gives it. One component, so a project keeps its colour from the list to its task.
 * Decorative: hidden from a screen reader, since the name beside it says which project.
 */

/**
 * A tone for a project's chip, the same one every time for the same name. Decorative — the
 * chip is hidden from a screen reader and the name beside it says which project it is.
 */
function toneOf(name: string): (typeof BENTO_TONES)[number] {
  let sum = 0
  for (const character of name) sum = (sum * 31 + (character.codePointAt(0) ?? 0)) % 9973
  return BENTO_TONES[sum % BENTO_TONES.length] ?? 'slate'
}

/** What a chip is drawn from: the project's name and what it declared to stand for itself. */
export interface ProjectFace {
  readonly name: string
  /** The declared emoji, or empty. Text, never parsed (RG200). */
  readonly icon: string
  /** The declared logo as a data URL the shell resolved, or empty (RG204). */
  readonly mark: string
}

/**
 * The face of a project that opened, or null where it has not. The name is `nameOf`'s, the
 * one rule every screen names a project by (RG202); the logo is the picture the shell resolved.
 */
export function faceOf(
  opened: { readonly declares: Declared; readonly mark: string } | null,
  root: string,
): ProjectFace | null {
  if (opened === null) return null
  return { name: nameOf(opened.declares, root), icon: opened.declares.icon, mark: opened.mark }
}

const SIZES = {
  /** A portfolio row's, beside a name and a description. */
  row: { box: 'size-8 rounded-[10px]', picture: 'size-5', emoji: 'text-lg', glyph: 17 },
  /** An eyebrow's, beside a name in small capitals. */
  crumb: { box: 'size-5 rounded-md', picture: 'size-3.5', emoji: 'text-xs', glyph: 12 },
} as const

export function ProjectChip({
  face,
  size,
  unreadable = false,
}: {
  readonly face: ProjectFace
  readonly size: keyof typeof SIZES
  /** A project that did not open, drawn dashed and untinted as the portfolio draws it. */
  readonly unreadable?: boolean
}) {
  const sized = SIZES[size]
  const chip = unreadable
    ? 'text-muted-foreground border border-dashed'
    : `${bentoChipClass(toneOf(face.name))} text-white`

  return (
    <span
      aria-hidden="true"
      data-testid="project-chip"
      className={`flex shrink-0 items-center justify-center ${sized.box} ${chip}`}
    >
      {/* A picture where one resolved, the declared emoji next, the folder glyph last
          (RG204). The chain is why the emoji stays worth declaring beside a logo: every
          way of not having a picture is cosmetic rather than an empty cell. */}
      {face.mark !== '' ? (
        <img
          src={face.mark}
          alt=""
          data-testid="project-mark"
          className={`${sized.picture} object-contain`}
        />
      ) : face.icon === '' ? (
        <IconFolder size={sized.glyph} />
      ) : (
        <span className={sized.emoji}>{face.icon}</span>
      )}
    </span>
  )
}

/**
 * The eyebrow of a screen under a project: which project it is, and the way back to it.
 *
 * The page contract's own case for passing `eyebrow`: something after the link, composed with
 * `BentoBackLink` rather than a second arrow — the way `BentoEntityShell` puts its status
 * marker beside one. The link carries the chip and the name; `task` adds a crumb to that line
 * where the screen is under one. Every crumb navigates, so the arrow promises nothing a click
 * does not keep.
 *
 * `face` is null until the project opened. The name is then the folder's and no chip is drawn,
 * since a tone taken from the folder would change colour the moment the declared name lands.
 */
export function ProjectTrail({
  root,
  face,
  task,
}: {
  readonly root: string
  readonly face: ProjectFace | null
  readonly task?: string
}) {
  return (
    <span className="inline-flex flex-wrap items-center gap-x-2 gap-y-1" data-testid="trail">
      <BentoBackLink to={projectPath(root)}>
        <span className="inline-flex items-center gap-1.5" data-testid="trail-project">
          {face === null ? null : <ProjectChip face={face} size="crumb" />}
          {face === null ? folderName(root) : face.name}
        </span>
      </BentoBackLink>
      {/*
        Empty as well as absent (RG263): a session handed a gate finding carries no line id,
        and a crumb drawn from one is a link with no text in it — which is what the
        accessibility scan called this before the empty case was here.
      */}
      {task === undefined || task === '' ? null : (
        <>
          <IconChevronRight aria-hidden="true" size={12} />
          <Link
            to={taskPath(root, task)}
            className="hover:text-foreground font-mono"
            data-testid="trail-task"
          >
            {task}
          </Link>
        </>
      )}
    </span>
  )
}
