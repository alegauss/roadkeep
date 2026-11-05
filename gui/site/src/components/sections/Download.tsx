import { download, releasesUrl } from '../../lib/site-content'
import { SiteButton, SiteCopyButton, SiteRich as Rich } from '@viglet/viglet-design-system/site'

// The section the argument ends in: the reader who accepted it can have the thing. The buttons
// carry data-twin="omit" for the reason the hero's do, but the prose around them does not,
// because what the installer needs and what it leaves out are facts an agent evaluating this
// app is right to want.
export function Download() {
  return (
    <section id="download">
      <div className="wrap">
        <div className="sec-head reveal">
          <div className="eyebrow">{download.eyebrow}</div>
          <h2>{download.heading}</h2>
          <p>
            <Rich runs={download.intro} />
          </p>
        </div>
        <div className="download-cta" data-twin="omit">
          <SiteButton href={releasesUrl}>{download.cta}</SiteButton>
          <SiteButton variant="ghost" href={releasesUrl}>
            {download.secondary}
          </SiteButton>
        </div>
        <div className="download-facts">
          {download.facts.map((fact) => (
            <span key={fact}>{fact}</span>
          ))}
        </div>
        <div className="narrow engine-line">
          <p className="allowlist-lead">{download.engineLead}</p>
          <div className="codeblock copy">
            <code>{download.engineLine}</code>
            <SiteCopyButton
              text={download.engineLine}
              label="Copy the install command"
              copyLabel="Copy"
              copiedLabel="Copied"
            />
          </div>
        </div>
        <p className="allowlist-note">
          <Rich runs={download.note} />
        </p>
      </div>
    </section>
  )
}
