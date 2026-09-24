import { download, hero, repoUrl } from '../../lib/site-content'
import { Rich } from '../ui/Rich'
import { HeroWindow } from '../HeroWindow'

export function Hero() {
  return (
    <header className="hero" id="top">
      <div className="wrap">
        <img className="hero-icon" src="/roadkeep-gui/logo.svg" alt="roadkeep-gui logo" />
        <div className="badge">
          <span className="dot" /> {hero.badge}
        </div>
        <h1>
          {hero.titleLead}
          <br />
          <span className="grad">{hero.titleAccent}</span>
        </h1>
        <p className="sub">
          <Rich runs={hero.sub} />
        </p>
        {/* The call to action is dropped from the Markdown twin by this attribute: it converts
            a reader and costs an agent the same words on every page. The button scrolls to the
            download section rather than leaving, because what the installer needs and touches
            is the question between a reader and an install, and that section answers it. */}
        <div className="hero-cta" data-twin="omit">
          <a className="btn btn-primary" href="#download">
            {download.cta}
          </a>
          <a className="btn btn-ghost" href={repoUrl}>
            ★ View on GitHub
          </a>
        </div>
        <div className="hero-meta">
          {hero.meta.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
        <HeroWindow />
        <div className="pills">
          {hero.pills.map((runs, i) => (
            <span className="pill" key={i}>
              <Rich runs={runs} />
            </span>
          ))}
        </div>
      </div>
    </header>
  )
}
