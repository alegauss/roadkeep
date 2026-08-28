import { closing } from "../../lib/site-content";
import { Rich } from "../ui/Rich";

// The page ends on the buttons and nothing follows them: a reader who has come this far has
// decided, and the last thing they should meet is the install and not another section.
export function Closing() {
  return (
    <section style={{ paddingTop: "20px" }}>
      <div className="wrap reveal">
        <div className="closing">
          <h2>{closing.heading}</h2>
          <p>
            <Rich runs={closing.body} />
          </p>
          <div className="hero-cta" data-twin="omit">
            {closing.ctas.map((cta) => (
              <a key={cta.href} className={`btn btn-${cta.kind}`} href={cta.href}>
                {cta.label}
              </a>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
