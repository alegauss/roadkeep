import { SiteFooter, SiteSponsor } from '@viglet/viglet-design-system/site'
import { brand, footer, sponsor } from '../lib/site-content'
import { ConsentSettings } from './Consent'
import { Ad } from './ui/Ad'

// The footer and the sponsor block are the design system's (RK1714). The sponsor is rendered
// with the rest of the page, so it is in the served HTML rather than injected after load:
// content a crawler or an LLM never runs JavaScript to find would not be worth declaring.
const sponsorBlock = (
  <SiteSponsor
    declaration={sponsor}
    moreLabel="More at"
    note="Both Apache 2.0 and self-hostable."
  />
)
const disclaimer = (
  <>
    {footer.disclaimer} <ConsentSettings />
  </>
)
// The house ad, above the footer rather than inside it: it belongs to the end of the page's
// content, not to the chrome. Placed here because every route ends in this component, so a page
// added later cannot forget it and no page can have two.
const pageEndAd = <Ad slot="page-end" />

export function Footer() {
  return (
    <SiteFooter
      brand={brand}
      links={footer.links}
      sponsor={sponsorBlock}
      disclaimer={disclaimer}
      before={pageEndAd}
    />
  )
}
