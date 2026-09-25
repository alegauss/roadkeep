import { features } from '../../lib/features'
import { spelledTitle } from '../../lib/product'

// The home for the depth pages: one link per record, so the list and the pages cannot disagree
// about what exists.
export function FeatureIndex() {
  return (
    <section id="features">
      <div className="wrap">
        <div className="sec-head reveal">
          <div className="eyebrow">In depth</div>
          <h2>{spelledTitle(features.length)} pages, one per part of the window</h2>
          <p>Each has a page to link at, whether from a README, an issue or a search result.</p>
        </div>
        <div className="feature-index reveal">
          {features.map((f) => (
            <a className="feature-card" href={`/roadkeep/gui/features/${f.slug}/`} key={f.slug}>
              <h3>{f.heading}</h3>
              <p>{f.description}</p>
              <span className="feature-card-go">Read the page →</span>
            </a>
          ))}
        </div>
      </div>
    </section>
  )
}
