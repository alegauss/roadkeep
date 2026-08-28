import { mechanism } from "../../lib/site-content";
import { Lines } from "../ui/Terminal";
import { Rich } from "../ui/Rich";

// One task written twice, side by side: hand-edited on the left, composed through `add` on the
// right. The two panes are the same width on purpose — the point is not that the tool's output
// is shorter but that the refusal happened before the prose, and an uneven split would read as
// a claim about length.
//
// Neither pane carries a terminal bar. The left one is a file, not a session, and giving the
// right one a chrome the left lacks would make the comparison about the frame.
export function Mechanism() {
  return (
    <section style={{ paddingTop: "26px" }}>
      <div className="wrap">
        <div className="sec-head reveal">
          <div className="eyebrow">{mechanism.eyebrow}</div>
          <h2>{mechanism.heading}</h2>
          <p>
            <Rich runs={mechanism.intro} />
          </p>
        </div>

        <p className="tbl-note reveal" style={{ marginBottom: "22px" }}>
          <Rich runs={mechanism.note} />
        </p>

        <div className="split even reveal">
          <div className="side bad">
            <div className="side-head">
              <span className="tag">{mechanism.bad.tag}</span> {mechanism.bad.label}
            </div>
            <div className="body">
              <pre>
                <Lines lines={mechanism.bad.lines} />
              </pre>
              <ul>
                {mechanism.bad.points.map((point, i) => (
                  <li key={i}>
                    <span className="m">✕</span>
                    <Rich runs={point} />
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="side good">
            <div className="side-head">
              <span className="tag">{mechanism.good.tag}</span> {mechanism.good.label}
            </div>
            <div className="body">
              <pre>
                <Lines lines={mechanism.good.lines} />
              </pre>
              <ul>
                {mechanism.good.points.map((point, i) => (
                  <li key={i}>
                    <span className="m">✓</span>
                    <Rich runs={point} />
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        <div className="quote reveal" style={{ marginTop: "52px" }}>
          <blockquote>
            {mechanism.quote.lines.map((line, i) => (
              <span key={i}>
                {line}
                {i < mechanism.quote.lines.length - 1 ? <br /> : null}
              </span>
            ))}
          </blockquote>
          <p>
            <Rich runs={mechanism.quote.body} />
          </p>
        </div>
      </div>
    </section>
  );
}
