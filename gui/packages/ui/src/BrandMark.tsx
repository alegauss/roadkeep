/**
 * roadkeep's mark, as its site carries it (RG136): four task lines of increasing length
 * stopping at a gate, the fourth cut there and the refused remainder beyond it.
 *
 * The drawings put an amber folder glyph at the head of this header and the window put
 * nothing, and neither was an answer — the glyph was the canvas's own invention. The mark
 * already existed: `roadkeep/site/public/assets/roadkeep-mark.svg`, which the site uses as
 * its favicon and beside its name.
 *
 * **Inlined, for the site's reason and one more.** The asset picks its palette off the
 * reader's system theme, and this window's ground is a setting that can disagree with the
 * system (RG52). So the geometry is the site's, rect for rect — keep it in step with that
 * file — and the colours are the ground's: the lines in the text colour they sit beside,
 * the gate in the accent this app claims, which is the amber the site's gate is.
 *
 * Decorative. The wordmark beside it already says roadkeep, and a header a screen reader
 * names twice is a header that stutters.
 */
export function BrandMark({ className }: { readonly className?: string }) {
  return (
    <svg viewBox="0 0 160 160" aria-hidden="true" focusable="false" className={className}>
      <rect fill="currentColor" x="24" y="34" width="46" height="12" rx="6" />
      <rect fill="currentColor" x="24" y="62" width="72" height="12" rx="6" />
      <rect fill="currentColor" x="24" y="90" width="58" height="12" rx="6" />
      <rect fill="currentColor" x="24" y="118" width="90" height="12" rx="6" />
      <rect className="fill-[var(--vg-accent-fg)]" x="120" y="22" width="8" height="116" rx="4" />
      <rect fill="currentColor" opacity="0.26" x="136" y="118" width="30" height="12" rx="6" />
    </svg>
  )
}
