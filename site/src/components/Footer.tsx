import { SiteFooter, SiteSponsor } from "@viglet/viglet-design-system/site";
import { brand, footer, sponsor } from "../lib/site-content";
import { ConsentSettings } from "./Consent";

// The footer and the sponsor block are the design system's (RK1714). The sponsor is rendered
// markup rather than a runtime fetch, on purpose: a block drawn after load is one the crawlers
// and the models reading this page never see, and the sponsor is the reason the page can be
// free of anything else. Its data mirrors alegauss.github.io/sponsor.json in the content module.
export function Footer() {
  return (
    <SiteFooter
      brand={brand}
      links={footer.links}
      sponsor={<SiteSponsor declaration={sponsor} moreLabel="More at" />}
      disclaimer={
        <>
          {footer.disclaimer} <ConsentSettings />
        </>
      }
    />
  );
}
