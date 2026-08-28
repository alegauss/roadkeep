import { surfaces } from "../../lib/site-content";
import { Rich } from "../ui/Rich";
import { Terminal } from "../ui/Terminal";

// The four places the plugin is, in the order an agent meets them: the hook that refuses the
// edit, the server that carries the schema, the skill that carries the rules and the commands
// the person drives. The hook gets the transcript and the other three get cards, because the
// hook is the only one of the four whose whole argument is what it prints.
export function Surfaces() {
  return (
    <section id="agents" style={{ paddingTop: "26px" }}>
      <div className="wrap">
        <div className="sec-head reveal">
          <div className="eyebrow">{surfaces.eyebrow}</div>
          <h2>
            <Rich runs={surfaces.heading} />
          </h2>
          <p>
            <Rich runs={surfaces.intro} />
          </p>
        </div>

        <div className="split even reveal">
          <Terminal transcript={surfaces.terminal} />
          <div className="card">
            <span className="kicker">{surfaces.hook.kicker}</span>
            <h3>{surfaces.hook.heading}</h3>
            <p>
              <Rich runs={surfaces.hook.body} />
            </p>
          </div>
        </div>

        <div className="cards reveal" style={{ marginTop: "18px" }}>
          {surfaces.cards.map((card) => (
            <div className="card" key={card.kicker}>
              <span className="kicker">{card.kicker}</span>
              <h3>{card.heading}</h3>
              <p>
                <Rich runs={card.body} />
              </p>
            </div>
          ))}
        </div>

        <p
          className="tbl-note reveal"
          style={{ marginTop: "20px", maxWidth: "860px", marginLeft: "auto", marginRight: "auto" }}
        >
          <Rich runs={surfaces.note} />
        </p>
      </div>
    </section>
  );
}
