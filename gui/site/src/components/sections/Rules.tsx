import { rules } from '../../lib/site-content'
import { Rich } from '../ui/Rich'

// The three parties, then the rules in the order a reader meets them.
export function Rules() {
  return (
    <section id="rules">
      <div className="wrap">
        <div className="sec-head reveal">
          <div className="eyebrow">{rules.eyebrow}</div>
          <h2>{rules.heading}</h2>
          <p>
            <Rich runs={rules.intro} />
          </p>
        </div>

        <div className="actors reveal">
          {rules.actors.map((actor) => (
            <div className={actor.first ? 'actor actor-first' : 'actor'} key={actor.who}>
              <div className="actor-head">
                <span className="actor-who">{actor.who}</span>
                <span className="actor-sub">{actor.sub}</span>
              </div>
              <div className="actor-iface">{actor.iface}</div>
              <div className="actor-job">{actor.job}</div>
            </div>
          ))}
        </div>
        <p className="actors-note reveal">
          <Rich runs={rules.actorsNote} />
        </p>

        <div className="sec-head sec-head-follow reveal">
          <div className="eyebrow">{rules.lawsEyebrow}</div>
          <h2>{rules.lawsHeading}</h2>
          <p>
            <Rich runs={rules.lawsIntro} />
          </p>
        </div>
        <div className="laws reveal">
          {rules.laws.map((law) => (
            <div className="law" key={law.id}>
              <span className="law-id">{law.id}</span>
              <div className="law-body">
                <h3>{law.title}</h3>
                <p>{law.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
