import { download, releasesUrl } from '../../lib/site-content'
import { CopyButton } from '../ui/CopyButton'
import { Rich } from '../ui/Rich'

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
        <div className="hero-cta" data-twin="omit">
          <a className="btn btn-primary" href={releasesUrl}>
            {download.cta}
          </a>
          <a className="btn btn-ghost" href={releasesUrl}>
            {download.secondary}
          </a>
        </div>
        <div className="hero-meta">
          {download.facts.map((fact) => (
            <span key={fact}>{fact}</span>
          ))}
        </div>
        <div className="narrow engine-line">
          <p className="allowlist-lead">{download.engineLead}</p>
          <div className="codeblock copy">
            <code>{download.engineLine}</code>
            <CopyButton text={download.engineLine} label="Copy the install command" />
          </div>
        </div>
        <p className="allowlist-note">
          <Rich runs={download.note} />
        </p>
      </div>
    </section>
  )
}
