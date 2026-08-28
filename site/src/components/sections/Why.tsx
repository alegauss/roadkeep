import { why } from "../../lib/site-content";
import { Rich } from "../ui/Rich";

// The context ledger: one question a turn asks, what answering it costs without this tool and
// what it costs with it. It is the page's whole argument in six rows, which is why it is the
// first section and not a feature list.
//
// A grid of divs rather than a <table>: the three columns collapse to one on a phone and a
// table cannot be re-flowed that way without losing which column a cell was in.
export function Why() {
  return (
    <section id="why" style={{ paddingTop: "44px" }}>
      <div className="wrap">
        <div className="sec-head reveal">
          <div className="eyebrow">{why.eyebrow}</div>
          <h2>{why.heading}</h2>
          <p>
            <Rich runs={why.intro} />
          </p>
        </div>

        <div className="ledger reveal">
          <div className="lrow head">
            {why.columns.map((column) => (
              <div key={column}>{column}</div>
            ))}
          </div>
          {why.rows.map((row) => (
            <div className="lrow" key={row.ask}>
              <div className="ask">{row.ask}</div>
              <div className="was">
                <Rich runs={row.was} />
              </div>
              <div className="now">
                <Rich runs={row.now} />
              </div>
            </div>
          ))}
        </div>

        <p
          className="tbl-note reveal"
          style={{ marginTop: "20px", maxWidth: "820px", marginLeft: "auto", marginRight: "auto" }}
        >
          <Rich runs={why.note} />
        </p>
      </div>
    </section>
  );
}
