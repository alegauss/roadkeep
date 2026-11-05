import { SiteFeatureIndex } from '@viglet/viglet-design-system/site'
import { features } from '../../lib/features'
import { spelledTitle } from '../../lib/product'

// The home for the depth pages: one card per record, so the list and the pages cannot disagree
// about what exists. The cards are the design system's (RK1714).
const items = features.map((f) => ({
  href: `/roadkeep/gui/features/${f.slug}/`,
  heading: f.heading,
  description: f.description,
}))

export function FeatureIndex() {
  return (
    <SiteFeatureIndex
      id="features"
      eyebrow="In depth"
      title={`${spelledTitle(features.length)} pages, one per part of the window`}
      description="Each has a page to link at, whether from a README, an issue or a search result."
      goLabel="Read the page →"
      items={items}
    />
  )
}
