import { hero } from "../../lib/site-content";
import { Mark } from "../ui/Mark";
import { Rich } from "../ui/Rich";

// The one screen that has to make the argument before a reader scrolls: what this costs an
// agent, not what it is. The chips carry an emoji each and it is marked `data-twin="omit"`,
// because a glyph is a label in a browser and a stray codepoint in the flat file an agent
// reads.
export function Hero() {
  return (
    <header className="hero" id="top">
      <div className="wrap">
        <div className="hero-mark">
          <Mark label="roadkeep" />
        </div>
        <div className="badge">
          <span className="dot" />
          {hero.badge}
        </div>
        <h1>
          {hero.headline.lead}
          <br />
          <span className="grad">{hero.headline.accent}</span>
        </h1>
        <p className="sub">
          <Rich runs={hero.sub} />
        </p>
        <p className="note">{hero.note}</p>
        <div className="hero-cta" data-twin="omit">
          {hero.ctas.map((cta) => (
            <a
              key={cta.href}
              className={`btn btn-${cta.kind}`}
              href={cta.href}
            >
              {cta.label}
            </a>
          ))}
        </div>
        <div className="hero-meta">
          {hero.chips.map((chip, i) => (
            <span className="chip" key={i}>
              <span data-twin="omit">{chip.icon} </span>
              <Rich runs={chip.text} />
            </span>
          ))}
        </div>
      </div>
    </header>
  );
}
