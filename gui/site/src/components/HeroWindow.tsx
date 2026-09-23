import { heroWindow } from '../lib/site-content'
import { Rich } from './ui/Rich'

// The portfolio screen, drawn in HTML rather than shown as a screenshot, so the Markdown twin
// and a crawler read its rows as text. What it shows is the argument of the page: one row per
// project, every figure one a verb printed.
export function HeroWindow() {
  return (
    <>
      <div className="win reveal">
        <div className="bar">
          <i />
          <i />
          <i />
          <span>{heroWindow.title}</span>
        </div>
        <div className="win-body">
          <div className="win-engine">{heroWindow.filters}</div>
          {heroWindow.rows.map((row) => (
            <div className="win-row" key={row.name}>
              <span className="win-name">{row.name}</span>
              <span className="win-counts">{row.backlog}</span>
              <span className="win-next">
                <Rich runs={row.next} />
              </span>
              <span className="win-next">{row.state}</span>
            </div>
          ))}
        </div>
        <div className="win-engine">{heroWindow.footnote}</div>
      </div>
      <p className="win-note">
        <Rich runs={heroWindow.note} />
      </p>
    </>
  )
}
