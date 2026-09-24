import { nonGoals } from '../../lib/site-content'
import { product } from '../../lib/product'
import { Rich } from '../ui/Rich'

// The titles and reasons are the roadmap's own, generated at build time.
export function NonGoals() {
  return (
    <section id="scope">
      <div className="wrap">
        <div className="sec-head reveal">
          <div className="eyebrow">{nonGoals.eyebrow}</div>
          <h2>{nonGoals.heading}</h2>
          <p>
            <Rich runs={nonGoals.intro} />
          </p>
        </div>
        <div className="nots reveal">
          {product.nonGoals.map((item) => (
            <div className="not" key={item.title}>
              <h4>
                <em>✗</em> {item.title}
              </h4>
              <p>{item.why}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
