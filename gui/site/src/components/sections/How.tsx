import { how } from '../../lib/site-content'
import { Rich } from '../ui/Rich'

export function How() {
  return (
    <section id="how">
      <div className="wrap">
        <div className="sec-head reveal">
          <div className="eyebrow">{how.eyebrow}</div>
          <h2>{how.heading}</h2>
          <p>
            <Rich runs={how.intro} />
          </p>
        </div>
        <div className="steps reveal">
          {how.steps.map((step) => (
            <div className="step" key={step.title}>
              <div className="n">{step.n}</div>
              <h4>{step.title}</h4>
              <p>
                <Rich runs={step.body} />
              </p>
            </div>
          ))}
        </div>
        <div className="term reveal">
          <div className="bar">
            <i />
            <i />
            <i />
            <span>{how.termTitle}</span>
          </div>
          <pre>{how.term}</pre>
        </div>
        <p className="win-note reveal">{how.termNote}</p>
      </div>
    </section>
  )
}
