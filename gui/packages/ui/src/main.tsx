import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter, Route, Routes } from 'react-router-dom'

import { App } from './App'
import { HOME_ROUTE } from './areas'
import { GroundProvider } from './ground'
import './index.css'
import { choicesAtLaunch } from './launch'
import { AppShell } from './Shell'
import { startSpeaking } from './speaking'
import { WordingProvider } from './wording'

const host = document.getElementById('root')
if (!host) {
  throw new Error('index.html has no #root to mount into')
}

// A `Route`'s `element` is configuration the router reads, not a prop a component renders,
// so these are built once here rather than on every pass through the tree.
const SHELL = <AppShell />
const HOME = <App />

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
                <Route path={HOME_ROUTE} element={HOME} />
              </Route>
            </Routes>
          </HashRouter>
        </WordingProvider>
      </GroundProvider>
    </StrictMode>,
  )
})
