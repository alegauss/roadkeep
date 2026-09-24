import { useEffect, useRef } from 'react'
import { session } from '../../lib/site-content'
import { Rich } from '../ui/Rich'

const WHO = { app: 'window', agent: 'claude', you: 'you' } as const

// The hand-over, as an autoplaying transcript. Every step renders on the server and with no
// JavaScript, so the twin and a crawler read the whole thing; the autoplay only reveals them one
// at a time after mount, which keeps the server render and the first client render identical.
//
// Only the reader moves the window. As each step lands the panel scrolls ITS OWN element
// (scrollTop), never scrollIntoView, which would drag a reader who has scrolled past it back
// to it on every step.
export function Session() {
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const panel = panelRef.current
    if (!panel) return undefined
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined

    const steps = Array.from(panel.querySelectorAll<HTMLElement>('.session-step'))
    if (steps.length === 0) return undefined

    // Not started until the panel is on screen: a transcript that played out above the fold
    // while the reader was still in the hero is one they arrive at already finished.
    let timer = 0
    let i = 0
    const tick = () => {
      if (i >= steps.length) return
      steps[i].classList.add('in')
      panel.scrollTop = panel.scrollHeight
      i += 1
      timer = window.setTimeout(tick, 1100)
    }
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          io.disconnect()
          panel.classList.add('session--playing')
          timer = window.setTimeout(tick, 350)
        }
      },
      { threshold: 0.3 },
    )
    io.observe(panel)
    return () => {
      io.disconnect()
      window.clearTimeout(timer)
    }
  }, [])

  return (
    <section id="session">
      <div className="wrap">
        <div className="sec-head reveal">
          <div className="eyebrow">{session.eyebrow}</div>
          <h2>{session.heading}</h2>
          <p>
            <Rich runs={session.intro} />
          </p>
        </div>
        <div className="session reveal">
          <div className="session-ask">
            <span className="session-ask-tag">Task</span>
            <span className="session-ask-text">{session.ask}</span>
          </div>
          <div className="session-scroll" ref={panelRef}>
            {session.steps.map((step, i) => (
              <div className="session-step" key={i}>
                <span className={`session-who ${step.who}`}>{WHO[step.who]}</span>
                <span className="session-line">
                  <Rich runs={step.line} />
                </span>
              </div>
            ))}
          </div>
        </div>
        <p className="session-note">
          <Rich runs={session.note} />
        </p>
      </div>
    </section>
  )
}
