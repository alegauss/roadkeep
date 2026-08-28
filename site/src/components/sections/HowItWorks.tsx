import { howItWorks } from "../../lib/site-content";
import { Rich } from "../ui/Rich";
import { Terminal } from "../ui/Terminal";

// Four verbs and one transcript running all of them against the same task. The step numbers
// are rendered and dropped from the twin by class: they are the shape of the list, and a flat
// file already numbers what it lists.
export function HowItWorks() {
  return (
    <section style={{ paddingTop: "26px" }}>
      <div className="wrap">
        <div className="sec-head reveal">
          <div className="eyebrow">{howItWorks.eyebrow}</div>
          <h2>{howItWorks.heading}</h2>
          <p>
            <Rich runs={howItWorks.intro} />
          </p>
        </div>

        <div className="steps reveal">
          {howItWorks.steps.map((step, i) => (
            <div className="step" key={step.verb}>
              <div className="n">{i + 1}</div>
              <h4>{step.verb}</h4>
              <p>
                <Rich runs={step.body} />
              </p>
            </div>
          ))}
        </div>

        <Terminal
          transcript={howItWorks.terminal}
          className="reveal"
          style={{ maxWidth: "900px", margin: "0 auto" }}
        />

        <p
          className="tbl-note reveal"
          style={{ marginTop: "18px", maxWidth: "820px", marginLeft: "auto", marginRight: "auto" }}
        >
          <Rich runs={howItWorks.note} />
        </p>
      </div>
    </section>
  );
}
