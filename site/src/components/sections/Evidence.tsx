import { evidence } from "../../lib/site-content";
import { Rich } from "../ui/Rich";

// Three readings from a real repository, and the finding under them that decided the design.
// The numbers are the whole section: each is a measurement of a file that declared a rule
// about itself, and the caption under it is the rule that was declared.
export function Evidence() {
  return (
    <section style={{ paddingTop: "26px" }}>
      <div className="wrap">
        <div className="sec-head reveal">
          <div className="eyebrow">{evidence.eyebrow}</div>
          <h2>{evidence.heading}</h2>
          <p>
            <Rich runs={evidence.intro} />
          </p>
        </div>
        <div className="readings reveal">
          {evidence.readings.map((reading) => (
            <div className="reading" key={reading.file}>
              <div className="file">{reading.file}</div>
              <div className="num">
                {reading.figure} <small>{reading.unit}</small>
              </div>
              <div className="unit">
                <Rich runs={reading.caption} />
              </div>
              <div className="rule">
                <b>{evidence.ruleLabel}</b> <Rich runs={reading.rule} />
              </div>
            </div>
          ))}
        </div>
        <div className="finding reveal">
          <p>
            <Rich runs={evidence.finding.lead} />
          </p>
          <p>
            <Rich runs={evidence.finding.body} />
          </p>
        </div>
      </div>
    </section>
  );
}
