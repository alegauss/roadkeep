import { createElement, useEffect } from 'react'
import { componentFor } from './routes'

// The client shell. No router: the page is chosen from the route map by the current path, and
// every cross-route link is a plain full load, because each route is a static file the
// prerender already wrote. The same App is what entry-server renders on the build side, so the
// client and the static file agree by construction.
//
// The path never changes for the life of a page (a link is a full load), so the reveal observer
// below runs once, on mount.
export function App({ path }: { path: string }) {
  useEffect(() => {
    const els = Array.from(document.querySelectorAll<HTMLElement>('.reveal'))
    if (!('IntersectionObserver' in window)) {
      els.forEach((el) => el.classList.add('in'))
      return undefined
    }
    // Only the reader moves the window: this toggles an element's own opacity class and never
    // scrolls anything.
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('in')
            io.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.12 },
    )
    els.forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, [])

  // The route table holds a component per path, declared at module scope in routes.tsx; this
  // only looks one up, which is why it is created by reference rather than defined here.
  return createElement(componentFor(path))
}
