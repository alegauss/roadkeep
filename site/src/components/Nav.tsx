import { SiteButton, SiteNav } from "@viglet/viglet-design-system/site";
import { brand, nav } from "../lib/site-content";

// The bar is drawn by the design system's site layer (RK1714). What is left here is this
// page's half of it: anchors into this one page plus one link that leaves it — /roadkeep/docs/
// is a second build under the same base, so it is written as a path and there is no route for
// it in routes.tsx. When the labels give way the GitHub button is what is left, which is why
// that button is the only entry here that is not also in the footer. No theme toggle: the
// pitch is dark only (index.css says why).
export function Nav() {
  return (
    <SiteNav
      brand={brand}
      parent={{ ...nav.parent, title: "alegauss — small developer tools" }}
      links={nav.links}
      actions={<SiteButton href={nav.cta.href}>{nav.cta.label}</SiteButton>}
    />
  );
}
