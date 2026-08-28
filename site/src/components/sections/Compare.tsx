import { compare } from "../../lib/site-content";
import { Rich } from "../ui/Rich";
import { Terminal } from "../ui/Terminal";

// Two halves that have to sit together. The first is the claim — everything else in this space
// reports, and reporting is a position on a timeline — and the transcript beside it is that
// timeline drawn. The second is the honest table, which is what keeps the first from being a
// straw man: each of those five is good at what it does, and the column that matters is the
// third.
//
// The table scrolls inside its own container rather than shrinking the page, because a matrix
// squeezed to a phone width is one nobody can read either way.
export function Compare() {
  return (
    <section id="compare" style={{ paddingTop: "26px" }}>
      <div className="wrap">
        <div className="diff reveal">
          <div>
            <div className="eyebrow">{compare.eyebrow}</div>
            <h3>{compare.heading}</h3>
            {compare.paragraphs.map((paragraph, i) => (
              <p key={i}>
                <Rich runs={paragraph} />
              </p>
            ))}
          </div>
          <Terminal transcript={compare.terminal} />
        </div>

        <div className="sec-head reveal" style={{ marginTop: "60px" }}>
          <div className="eyebrow">{compare.table.eyebrow}</div>
          <h2>{compare.table.heading}</h2>
          <p>
            <Rich runs={compare.table.intro} />
          </p>
        </div>
        <div className="tbl-scroll reveal">
          <table>
            <thead>
              <tr>
                {compare.table.columns.map((column) => (
                  <th key={column}>{column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {compare.table.rows.map((row, i) => (
                <tr key={i}>
                  <td className="who">
                    <Rich runs={row.who} />
                  </td>
                  <td className="good">{row.good}</td>
                  <td className="why">
                    <Rich runs={row.why} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="tbl-note reveal">
          <Rich runs={compare.table.note} />
        </p>
      </div>
    </section>
  );
}
