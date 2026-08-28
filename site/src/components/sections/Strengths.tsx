import { strengths } from "../../lib/site-content";
import { Rich } from "../ui/Rich";

// Eight cards, each a property the tool can be held to rather than a claim about it. The
// emoji sits in its own `.ico` element, which the twin generator drops by class: a glyph is a
// label to a reader and a stray codepoint to the agent reading the flat file.
export function Strengths() {
  return (
    <section id="strengths">
      <div className="wrap">
        <div className="sec-head reveal">
          <div className="eyebrow">{strengths.eyebrow}</div>
          <h2>{strengths.heading}</h2>
          <p>
            <Rich runs={strengths.intro} />
          </p>
        </div>
        <div className="cards">
          {strengths.cards.map((card) => (
            <div className="card reveal" key={card.kicker}>
              <div className="ico">{card.icon}</div>
              <span className="kicker">{card.kicker}</span>
              <h3>{card.heading}</h3>
              <p>
                <Rich runs={card.body} />
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
