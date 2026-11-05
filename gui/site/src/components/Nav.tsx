import { SiteButton, SiteNav, SiteThemeToggle } from '@viglet/viglet-design-system/site'
import {
  brand,
  download,
  navLinks,
  parentUrl,
  releasesUrl,
  repoUrl,
  THEME_KEY,
} from '../lib/site-content'

const themeLabel = (next: string) => `Switch to ${next} theme`
const parent = {
  href: parentUrl,
  name: 'alegauss',
  pre: 'part of',
  title: 'alegauss: small developer tools',
}

// The bar every route shares, drawn by the design system's site layer (RK1714). What is left
// here is this product's half of it: which links, and which words.
export function Nav() {
  return (
    <SiteNav
      brand={brand}
      parent={parent}
      links={navLinks}
      actions={
        <>
          {/* The download is the primary button because a release exists. GitHub keeps its
              place beside it: the repository is what a reader checks before installing. */}
          <SiteButton href={releasesUrl}>{download.cta}</SiteButton>
          <SiteButton variant="ghost" href={repoUrl}>
            ★ View on GitHub
          </SiteButton>
          <SiteThemeToggle storageKey={THEME_KEY} label={themeLabel} />
        </>
      }
    />
  )
}
