// The mark is inlined rather than <img src="assets/roadkeep-mark.svg">: that asset follows the
// reader's system theme and this page is dark in either, so the inline copy carries the dark
// palette the page needs. Keep it in sync with public/assets/.
//
// Declared once as a `<symbol>` at the top of the document and used three times — nav, hero,
// footer — because the prerender writes the whole tree into one file and three copies of the
// paths would be three copies in every byte counted.
export function MarkSprite() {
  return (
    <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true" focusable="false">
      <symbol id="mark" viewBox="0 0 160 160">
        <rect fill="#cbd5e1" x="24" y="34" width="46" height="12" rx="6" />
        <rect fill="#cbd5e1" x="24" y="62" width="72" height="12" rx="6" />
        <rect fill="#cbd5e1" x="24" y="90" width="58" height="12" rx="6" />
        <rect fill="#cbd5e1" x="24" y="118" width="90" height="12" rx="6" />
        <rect fill="#f59e0b" x="120" y="22" width="8" height="116" rx="4" />
        <rect fill="#cbd5e1" opacity=".26" x="136" y="118" width="30" height="12" rx="6" />
      </symbol>
    </svg>
  );
}

export function Mark({ label }: { label?: string }) {
  return label ? (
    <svg role="img" aria-label={label}>
      <use href="#mark" />
    </svg>
  ) : (
    <svg aria-hidden="true">
      <use href="#mark" />
    </svg>
  );
}
