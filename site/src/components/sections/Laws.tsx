import { laws, nonGoals } from "../../lib/site-content";
import { Rich } from "../ui/Rich";

// The six laws and the non-goals, in one section because they are one claim: what this tool
// will not do is the reason the six can be held to. Both lists have an owner in the repository
// — `docs/ROADMAP.md` for the non-goals, `docs/IMPROVEMENTS.md` §0.3 for the laws — and this
// is the compressed reading of them, which is the only copy this page is allowed to carry.
export function Laws() {
  return (
    <section style={{ paddingTop: "26px" }}>
      <div className="wrap">
        <div className="sec-head reveal">
          <div className="eyebrow">{laws.eyebrow}</div>
          <h2>{laws.heading}</h2>
          <p>
            <Rich runs={laws.intro} />
          </p>
        </div>
        <div className="laws reveal">
          {laws.items.map((law) => (
            <div className="law" key={law.id}>
              <span className="id">{law.id}</span>
              <p>
                <Rich runs={law.text} />
              </p>
            </div>
          ))}
        </div>

        <div className="sec-head reveal" style={{ marginTop: "56px", marginBottom: 0 }}>
          <div className="eyebrow">{nonGoals.eyebrow}</div>
          <h2>{nonGoals.heading}</h2>
          <p>
            <Rich runs={nonGoals.intro} />
          </p>
        </div>
        <div className="nogoals reveal">
          {nonGoals.items.map((item, i) => (
            <div className="nogoal" key={i}>
              <span className="x">✕</span>
              <p>
                <Rich runs={item} />
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
