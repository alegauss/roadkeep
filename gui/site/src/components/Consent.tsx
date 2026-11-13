import { useCallback, useEffect, useState } from 'react'

// Google Analytics loads only after the visitor allows it, the flow the hub runs (its AG1).
// Nothing reaches googletagmanager.com before a choice: the tag is not in the HTML, and this
// adds it only for "granted". A refusal is remembered as firmly as a consent, and the footer's
// "Analytics settings" asks again.
//
// The key and the measurement id are the hub's on purpose. This site is served from the same
// origin (alegauss.com/roadkeep/gui/), so the two share one localStorage and one
// property, and a visitor who has answered on either has answered for both.

const KEY = 'alegauss-consent'
const ASK = 'alegauss:consent-ask'
const MEASUREMENT_ID = 'G-6HG45Q9BHP'
type Choice = 'granted' | 'denied'

declare global {
  interface Window {
    dataLayer?: unknown[]
    gtag?: (...args: unknown[]) => void
  }
}

function readChoice(): Choice | null {
  try {
    const v = localStorage.getItem(KEY)
    return v === 'granted' || v === 'denied' ? v : null
  } catch {
    return null
  }
}

let loaded = false
function loadAnalytics() {
  if (loaded) return
  loaded = true
  const dataLayer: unknown[] = window.dataLayer ?? []
  window.dataLayer = dataLayer
  window.gtag = function gtag() {
    // gtag.js reads the arguments object itself, not an array
    // eslint-disable-next-line prefer-rest-params
    dataLayer.push(arguments)
  }
  window.gtag('js', new Date())
  window.gtag('config', MEASUREMENT_ID)
  const s = document.createElement('script')
  s.async = true
  s.src = `https://www.googletagmanager.com/gtag/js?id=${MEASUREMENT_ID}`
  document.head.appendChild(s)
}

function ask() {
  window.dispatchEvent(new Event(ASK))
}

/** The footer's way back to the banner. A button, so the Markdown twin drops it. */
export function ConsentSettings() {
  return (
    <button type="button" className="consent-settings" onClick={ask}>
      Analytics settings
    </button>
  )
}

/** Mounted, not hydrated: the prerendered page carries no banner and no tag. */
export function ConsentBanner() {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const choice = readChoice()
    if (choice === 'granted') loadAnalytics()
    if (choice === null) setOpen(true)
    const reopen = () => setOpen(true)
    window.addEventListener(ASK, reopen)
    return () => window.removeEventListener(ASK, reopen)
  }, [])

  const choose = useCallback((choice: Choice) => {
    try {
      localStorage.setItem(KEY, choice)
    } catch {
      /* private mode: the choice lasts this page */
    }
    if (choice === 'granted') loadAnalytics()
    else if (loaded) {
      // the tag cannot be unloaded from a running page; the next one will not load it
      Reflect.set(window, `ga-disable-${MEASUREMENT_ID}`, true)
    }
    setOpen(false)
  }, [])
  const decline = useCallback(() => choose('denied'), [choose])
  const allow = useCallback(() => choose('granted'), [choose])

  if (!open) return null
  return (
    <section className="consent" aria-label="Analytics consent">
      <p>
        This site counts visits with Google Analytics only if you allow it, and analytics is not
        loaded until you choose. The house ad at the foot of the page loads either way; it counts
        nothing and sets no identifiers. The app itself sends nothing of its own.
      </p>
      <div className="consent-actions">
        {/* SiteButton is an anchor, and these act rather than go somewhere: its classes on a button */}
        <button type="button" className="vg-site-btn vg-site-btn-ghost" onClick={decline}>
          Decline
        </button>
        <button type="button" className="vg-site-btn vg-site-btn-primary" onClick={allow}>
          Allow analytics
        </button>
      </div>
    </section>
  )
}
