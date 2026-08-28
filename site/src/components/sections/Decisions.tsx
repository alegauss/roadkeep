import { decisions } from "../../lib/site-content";
import { Rich } from "../ui/Rich";
import { Terminal } from "../ui/Terminal";

// The answer to the obvious objection about `ship`: it deletes the design section, so where
// does the verdict go. This section exists because that question is the first one a reader who
// has understood the rest of the page asks, and an answer further down would be one they left
// before reaching.
export function Decisions() {
  return (
    <section style={{ paddingTop: "26px" }}>
      <div className="wrap">
        <div className="sec-head reveal">
          <div className="eyebrow">{decisions.eyebrow}</div>
          <h2>{decisions.heading}</h2>
          <p>
            <Rich runs={decisions.intro} />
          </p>
        </div>

        <div className="split even reveal">
          <Terminal transcript={decisions.terminal} />
          <div className="card">
            <span className="kicker">{decisions.card.kicker}</span>
            <h3>{decisions.card.heading}</h3>
            <p>
              <Rich runs={decisions.card.body} />
            </p>
            <p style={{ marginTop: "12px", color: "var(--muted)", fontSize: ".92rem" }}>
              <Rich runs={decisions.card.aside} />
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
