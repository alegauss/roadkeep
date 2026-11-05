import { SiteButton, SiteHero, SiteRich } from '@viglet/viglet-design-system/site'
import { download, hero, repoUrl } from '../../lib/site-content'
import { HeroWindow } from '../HeroWindow'

// The hero is the design system's (RK1714), which marks the actions `data-twin="omit"`: the
// call to action converts a reader and costs an agent the same words on every page. The button
// scrolls to the download section rather than leaving, because what the installer needs and
// touches is the question between a reader and an install, and that section answers it.
//
// The props are module constants: the copy is static, so nothing here is rebuilt per render.
const icon = { src: '/roadkeep/gui/logo.svg', alt: 'roadkeep-gui logo' }
const sub = <SiteRich runs={hero.sub} />
const actions = (
  <>
    <SiteButton href="#download">{download.cta}</SiteButton>
    <SiteButton variant="ghost" href={repoUrl}>
      ★ View on GitHub
    </SiteButton>
  </>
)
const feature = <HeroWindow />
const pills = hero.pills.map((runs) => <SiteRich key={JSON.stringify(runs[0])} runs={runs} />)

export function Hero() {
  return (
    <SiteHero
      icon={icon}
      badge={hero.badge}
      title={hero.titleLead}
      titleAccent={hero.titleAccent}
      sub={sub}
      actions={actions}
      meta={hero.meta}
      feature={feature}
      pills={pills}
    />
  )
}
