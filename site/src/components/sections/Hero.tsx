import { SiteButton, SiteHero } from "@viglet/viglet-design-system/site";
import { brand, hero } from "../../lib/site-content";
import { Rich } from "../ui/Rich";

// The one screen that has to make the argument before a reader scrolls: what this costs an
// agent, not what it is. Drawn by the design system's hero (RK1714), which marks the actions
// `data-twin="omit"` itself. The chips carry an emoji each and it is marked omit too, because a
// glyph is a label in a browser and a stray codepoint in the flat file an agent reads.
export function Hero() {
  return (
    <SiteHero
      icon={{ src: brand.logo, alt: "roadkeep", logoShape: "mark" }}
      badge={hero.badge}
      title={hero.headline.lead}
      titleAccent={hero.headline.accent}
      sub={<Rich runs={hero.sub} />}
      meta={[hero.note]}
      actions={hero.ctas.map((cta) => (
        <SiteButton key={cta.href} variant={cta.kind} href={cta.href}>
          {cta.label}
        </SiteButton>
      ))}
      pills={hero.chips.map((chip) => (
        <span key={chip.icon}>
          <span data-twin="omit">{chip.icon} </span>
          <Rich runs={chip.text} />
        </span>
      ))}
    />
  );
}
