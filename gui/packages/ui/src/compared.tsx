import { COMPARE_CEILING, type Comparison, type CompareLine, type CompareMark } from '@rk/core'
import { Button } from '@viglet/viglet-design-system'
import { useCallback } from 'react'

import { useWording } from './wording'

/**
 * A file against what it was before the session (RG282).
 *
 * **Marked in text as well as colour.** Every line leads with `+`, `−` or a space, so what
 * changed is readable where the tint is not: in the other ground, on a projector, printed, or
 * by somebody who does not see the two colours apart. The tint is the second telling.
 *
 * **Both sides' numbers.** A hunk says which line of the file before and which line of the file
 * now, because a reviewer reads this to go and look at one of them.
 *
 * **Inline first, side by side on asking.** Inline is the shape that reads at any width and the
 * one a narrow sheet has room for; side by side is what a person comparing whole blocks asks
 * for, and it widens the sheet.
 *
 * **Drawn here rather than with the design system's `BentoDiff`**, which compares two versions of
 * a record field by field and marks the words inside one. A file is compared by line, with both
 * sides' numbers on every row, and neither of those is a shape that component draws.
 *
 * Nothing is highlighted and no Markdown is rendered, for the reasons the viewer gives: this
 * app parses no Markdown, and a grammar per language would be a second parser.
 */

/** What a line is marked with, in text. A space keeps every line the same width. */
const MARK_GLYPH: Readonly<Record<CompareMark, string>> = {
  same: ' ',
  added: '+',
  removed: '−',
}

/** The tint behind each, which says the same thing a second time. */
const MARK_TINT: Readonly<Record<CompareMark, string>> = {
  same: '',
  added: 'bg-emerald-500/10',
  removed: 'bg-rose-500/10',
}

function number(at: number): string {
  return at === 0 ? '' : String(at)
}

/** One line of the comparison, inline: both numbers, its mark, and the line itself. */
function Line({ line }: { readonly line: CompareLine }) {
  return (
    <div
      className={`flex ${MARK_TINT[line.mark]}`}
      data-testid="compare-line"
      data-mark={line.mark}
    >
      <span aria-hidden="true" className="text-muted-foreground w-10 shrink-0 px-2 text-right">
        {number(line.before)}
      </span>
      <span aria-hidden="true" className="text-muted-foreground w-10 shrink-0 px-2 text-right">
        {number(line.after)}
      </span>
      <pre className="min-w-0 flex-1 px-2 whitespace-pre-wrap">
        {MARK_GLYPH[line.mark]} {line.text}
      </pre>
    </div>
  )
}

/** The same line with each side in its own column, for reading whole blocks against each other. */
function Pair({ line }: { readonly line: CompareLine }) {
  return (
    <div className="flex" data-testid="compare-line" data-mark={line.mark}>
      <div className={`flex w-1/2 min-w-0 ${line.mark === 'added' ? '' : MARK_TINT[line.mark]}`}>
        <span aria-hidden="true" className="text-muted-foreground w-10 shrink-0 px-2 text-right">
          {number(line.before)}
        </span>
        <pre className="min-w-0 flex-1 px-2 whitespace-pre-wrap">
          {line.mark === 'added' ? '' : `${MARK_GLYPH[line.mark]} ${line.text}`}
        </pre>
      </div>
      <div
        className={`flex w-1/2 min-w-0 border-l ${line.mark === 'removed' ? '' : MARK_TINT[line.mark]}`}
      >
        <span aria-hidden="true" className="text-muted-foreground w-10 shrink-0 px-2 text-right">
          {number(line.after)}
        </span>
        <pre className="min-w-0 flex-1 px-2 whitespace-pre-wrap">
          {line.mark === 'removed' ? '' : `${MARK_GLYPH[line.mark]} ${line.text}`}
        </pre>
      </div>
    </div>
  )
}

export function Compared({
  comparison,
  onSideBySide,
  sideBySide,
}: {
  readonly comparison: Comparison
  /** Told that the reader wants the two sides in columns, which widens the sheet. */
  readonly onSideBySide: (side: boolean) => void
  readonly sideBySide: boolean
}) {
  const say = useWording()
  const toggled = useCallback(() => {
    onSideBySide(!sideBySide)
  }, [onSideBySide, sideBySide])

  if (comparison.refused) {
    return (
      <p className="text-muted-foreground p-4 text-sm" data-testid="compare-refused">
        {say('session.file.compare.refused', { ceiling: COMPARE_CEILING })}
      </p>
    )
  }
  if (comparison.same) {
    return (
      <p className="text-muted-foreground p-4 text-sm" data-testid="compare-same">
        {say('session.file.compare.same')}
      </p>
    )
  }

  // What each hunk skips over: the unchanged lines between it and the one before, counted
  // rather than drawn. Worked out before anything is drawn, since a variable moving while a
  // render runs is a render that answers differently the second time.
  const skipped = comparison.hunks.map((hunk, at) => {
    const last = comparison.hunks[at - 1]?.lines.at(-1)?.before ?? 0
    return hunk.before - last - 1
  })
  return (
    <div data-testid="compare">
      <div className="text-muted-foreground flex flex-wrap items-center gap-3 border-b px-4 py-2 text-xs">
        <span data-testid="compare-counts">
          {say('session.file.compare.added', { count: comparison.added })} ·{' '}
          {say('session.file.compare.removed', { count: comparison.removed })}
        </span>
        <Button variant="outline" size="sm" onClick={toggled}>
          {say(sideBySide ? 'session.file.compare.inline' : 'session.file.compare.side')}
        </Button>
      </div>
      <div className="font-mono text-xs leading-5">
        {comparison.hunks.map((hunk, at) => {
          const gap = skipped[at] ?? 0
          return (
            <div key={`${String(hunk.before)}-${String(hunk.after)}`}>
              {gap <= 0 ? null : (
                <p
                  className="text-muted-foreground bg-muted/40 px-4 py-1 text-[11px]"
                  data-testid="compare-folded"
                >
                  {say('session.file.compare.folded', { count: gap })}
                </p>
              )}
              {hunk.lines.map((line) =>
                sideBySide ? (
                  <Pair
                    key={`${String(line.before)}-${String(line.after)}-${line.mark}`}
                    line={line}
                  />
                ) : (
                  <Line
                    key={`${String(line.before)}-${String(line.after)}-${line.mark}`}
                    line={line}
                  />
                ),
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
