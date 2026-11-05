import { SiteButton } from "@viglet/viglet-design-system/site";
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
          <div className="closing-cta" data-twin="omit">
            {closing.ctas.map((cta) => (
              <SiteButton key={cta.href} variant={cta.kind} href={cta.href}>
                {cta.label}
              </SiteButton>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
