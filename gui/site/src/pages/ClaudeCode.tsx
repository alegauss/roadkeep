import { claudeCode as cc } from '../lib/site-content'
import { product } from '../lib/product'
import { Nav } from '../components/Nav'
import { Footer } from '../components/Footer'
import { Rich } from '../components/ui/Rich'

// The page for the person who runs the agent. The verb lists at the bottom are generated from
// the two tables in packages/core, so the page cannot name a verb the window cannot send.
export function ClaudeCode() {
  return (
    <>
      <Nav />
      <header className="hero page-hero" id="top">
        <div className="wrap">
          <div className="eyebrow">{cc.eyebrow}</div>
          <h1>{cc.heading}</h1>
          <p className="sub">
            <Rich runs={cc.intro} />
          </p>
        </div>
      </header>

      <section>
        <div className="wrap">
          <div className="sec-head reveal">
            <h2>{cc.flowHeading}</h2>
          </div>
          <div className="steps reveal">
            {cc.flow.map((step) => (
              <div className="step" key={step.title}>
                <div className="n">{step.n}</div>
                <h4>{step.title}</h4>
                <p>
                  <Rich runs={step.body} />
                </p>
              </div>
            ))}
          </div>
          <div className="sec-head sec-head-follow sec-head-last reveal">
            <h2>{cc.gateHeading}</h2>
            <p>
              <Rich runs={cc.gateBody} />
            </p>
          </div>
        </div>
      </section>

      <section>
        <div className="wrap">
          <div className="sec-head reveal">
            <h2>{cc.refusesHeading}</h2>
            <p>
              <Rich runs={cc.refusesLead} />
            </p>
          </div>
          <div className="refuses reveal">
            {cc.refuses.map((r) => (
              <div className="refuse" key={r.t}>
                <h4>
                  <em>✗</em> {r.t}
                </h4>
                <p>{r.b}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section>
        <div className="wrap">
          <div className="sec-head sec-head-last reveal">
            <h2>{cc.explainHeading}</h2>
            <p>
              <Rich runs={cc.explainBody} />
            </p>
          </div>
        </div>
      </section>

      <section>
        <div className="wrap">
          <div className="sec-head reveal">
            <h2>{cc.verbsHeading}</h2>
            <p>
              <Rich runs={cc.verbsLead} />
            </p>
          </div>
          <div className="verbs-split reveal">
            <div>
              <h3 className="verbs-head">
                {cc.readsHeading} · {product.reads.length}
              </h3>
              <ul className="verbs">
                {product.reads.map((verb) => (
                  <li className="verb" key={verb}>
                    <code>{verb}</code>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="verbs-head">
                {cc.writesHeading} · {product.writes.length}
              </h3>
              <ul className="verbs">
                {product.writes.map((verb) => (
                  <li className="verb" key={verb}>
                    <code>{verb}</code>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </>
  )
}
