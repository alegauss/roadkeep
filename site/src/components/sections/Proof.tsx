import { proof } from "../../lib/site-content";
import { Rich } from "../ui/Rich";

// The claim the whole page rests on, kept to one box: the format is proven by this
// repository's own files passing the gate, not asserted here. A section that argued it at
// length would be doing what the tool refuses.
export function Proof() {
  return (
    <section style={{ paddingTop: "30px" }}>
      <div className="wrap reveal">
        <div className="openbox">
          <div className="eyebrow">{proof.eyebrow}</div>
          <h2>{proof.heading}</h2>
          {proof.paragraphs.map((paragraph, i) => (
            <p key={i} style={i > 0 ? { marginTop: "14px" } : undefined}>
              <Rich runs={paragraph} />
            </p>
          ))}
        </div>
      </div>
    </section>
  );
}
