import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter, Route, Routes } from 'react-router-dom'

import { GroundProvider } from './ground'
import './index.css'
import { choicesAtLaunch } from './launch'
import { SURFACES } from './routes'
import { AppShell } from './Shell'
import { startSpeaking } from './speaking'
import { WordingProvider } from './wording'

const host = document.getElementById('root')
if (!host) {
  throw new Error('index.html has no #root to mount into')
}

// A `Route`'s `element` is configuration the router reads, not a prop a component renders,
// so this is built once here rather than on every pass through the tree. The routed
// elements are built the same way, in `routes` (RG117), which is the one place they are
// written: this file mounts what that array says and knows no path of its own.
const SHELL = <AppShell />

// Both settings are asked for before anything mounts, so the first frame is already in the
// right language and on the right ground. One call for the two: they come out of one file,
// and a window that mounted on the answer to half of them would repaint for the other half.
//
// The tag goes to i18next and not to the provider. The design system's components read the
// language off that instance, so it is the one place a language can be decided — and the
// catalogue takes its tag from there rather than being handed one in parallel.
void choicesAtLaunch().then(async ({ locale, theme }) => {
  await startSpeaking(locale)

  createRoot(host).render(
    <StrictMode>
      <GroundProvider initial={theme ?? undefined}>
        <WordingProvider>
          {/*
           * A hash router, because a packaged build is loaded from `file://` and a path
           * router asks the filesystem for a directory that is not there. The URL is not a
           * thing anybody types here — it is how the shell knows which surface is open.
           */}
          <HashRouter>
            <Routes>
              <Route element={SHELL}>
                {SURFACES.map((surface) => (
                  <Route key={surface.path} path={surface.path} element={surface.element} />
                ))}
              </Route>
            </Routes>
          </HashRouter>
        </WordingProvider>
      </GroundProvider>
    </StrictMode>,
  )
})
