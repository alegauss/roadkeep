import { Nav } from '../components/Nav'
import { Footer } from '../components/Footer'
import { Rich } from '../components/ui/Rich'
import { features, type FeatureRecord } from '../lib/features'

export function FeaturePage({ record }: { record: FeatureRecord }) {
  const idx = features.findIndex((f) => f.slug === record.slug)
  const prev = idx > 0 ? features[idx - 1] : null
  const next = idx < features.length - 1 ? features[idx + 1] : null

  return (
    <>
      <Nav />
      <header className="hero page-hero" id="top">
        <div className="wrap">
          <a className="feature-back" href="/roadkeep/gui/#features">
            ← The window
          </a>
          <div className="eyebrow">{record.eyebrow}</div>
          <h1>{record.heading}</h1>
          <p className="sub">
            <Rich runs={record.lead} />
          </p>
        </div>
      </header>

      <section>
        <div className="wrap">
          <div className="feature-body">
            {record.sections.map((s) => (
              <div className="feature-section reveal" key={s.heading}>
                <h2>{s.heading}</h2>
                {s.body && (
                  <p>
                    <Rich runs={s.body} />
                  </p>
                )}
                {s.list && (
                  <ul className="feat-list">
                    {s.list.map((item, i) => (
                      <li key={i}>
                        <span className="chk">✓</span>
                        <span>
                          <Rich runs={item} />
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
            {record.slug === 'sessions' && (
              <p className="reveal">
                <a className="feature-link" href="/roadkeep/gui/claude-code/">
                  How the hand-over works, and what it refuses to decide →
                </a>
              </p>
            )}
          </div>

          <div className="feature-nav reveal">
            {prev ? (
              <a className="feature-nav-link" href={`/roadkeep/gui/features/${prev.slug}/`}>
                ← {prev.heading}
              </a>
            ) : (
              <span />
            )}
            {next ? (
              <a className="feature-nav-link next" href={`/roadkeep/gui/features/${next.slug}/`}>
                {next.heading} →
              </a>
            ) : (
              <span />
            )}
          </div>
        </div>
      </section>

      <Footer />
    </>
  )
}
