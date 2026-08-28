import { install } from "../../lib/site-content";
import { CopyLine } from "../ui/CopyLine";
import { Rich } from "../ui/Rich";
import { Terminal } from "../ui/Terminal";

// Four steps, and the order is the one an adopter actually runs: install the plugin, measure
// the backlog you already have, declare the format, then make it a gate. Measuring comes
// second and not last because an estimate taken after the config is written is one taken too
// late to change anything.
//
// Every command is a `CopyLine`, which copies the element's own text: a button that pastes a
// string the reader cannot see is one that can paste a different command than the one shown.
export function Install() {
  return (
    <section id="install" style={{ paddingTop: "36px" }}>
      <div className="wrap">
        <div className="sec-head reveal">
          <div className="eyebrow">{install.eyebrow}</div>
          <h2>{install.heading}</h2>
          <p>
            <Rich runs={install.intro} />
          </p>
        </div>

        <div className="install">
          {install.steps.map((step, i) => (
            <div className="install-step reveal" key={step.heading}>
              <div className="n">{i + 1}</div>
              <div className="body">
                <h4>{step.heading}</h4>
                <p>
                  <Rich runs={step.body} />
                </p>
                {step.commands.map((command, j) => (
                  <CopyLine
                    key={command}
                    command={command}
                    style={j > 0 ? { marginTop: "9px" } : undefined}
                  />
                ))}
                {step.after.map((paragraph, j) => (
                  <p key={j} style={{ marginTop: "11px" }}>
                    <Rich runs={paragraph} />
                  </p>
                ))}
              </div>
            </div>
          ))}

          <div className="install-step reveal">
            <div className="n">{install.steps.length + 1}</div>
            <div className="body">
              <h4>{install.gate.heading}</h4>
              <p>
                <Rich runs={install.gate.body} />
              </p>
              <Terminal transcript={install.gate.terminal} style={{ marginTop: "4px" }} />
            </div>
          </div>

          <p className="install-foot reveal">
            <Rich runs={install.foot} />
          </p>
        </div>
      </div>
    </section>
  );
}
