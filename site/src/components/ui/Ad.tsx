/** The four layouts japode-ads draws. The page places the one that suits a full column. */
type AdFormat = "in-content" | "footer" | "sidebar" | "strip";

/**
 * One house ad slot.
 *
 * The container is rendered server-side and stays empty: the loader in index.html attaches a
 * shadow root to it and draws inside that, so the page stylesheet cannot reach the banner and
 * the banner cannot leak into the page. The box it will occupy is reserved in index.css, at
 * the height the loader reserves for the format, so nothing below it moves when it arrives —
 * and when the catalogue cannot be read the loader collapses the slot itself, leaving no gap.
 *
 * `data-ad-exclude` is how a product keeps itself off its own site: a campaign carries no host
 * of its own, so the host page names the id it does not want served to it.
 *
 * Dropped from the Markdown twin. An agent sent to evaluate roadkeep is not the reader this is
 * for, and someone else's product is forty words it would pay for on a page whose whole
 * argument is what a read costs.
 */
export function Ad({
  slot,
  format = "strip",
  className,
}: {
  readonly slot: string;
  readonly format?: AdFormat;
  readonly className?: string;
}) {
  return (
    <div
      className={className ? `promo-rail ${className}` : "promo-rail"}
      data-twin="omit"
    >
      <div className="wrap">
        <div
          className="ad"
          data-japode-ads=""
          data-ad-slot={slot}
          data-ad-format={format}
          data-ad-theme="dark"
          data-ad-exclude="roadkeep"
        />
      </div>
    </div>
  );
}
