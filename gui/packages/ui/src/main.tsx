import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter } from 'react-router-dom'

import './index.css'
import { choicesAtLaunch } from './launch'
import { RoutedSurfaces } from './routes'
import { startSpeaking } from './speaking'
import { ProviderStack } from './stack'

const host = document.getElementById('root')
if (!host) {
  throw new Error('index.html has no #root to mount into')
}

// Both settings are asked for before anything mounts, so the first frame is already in the
// right language and on the right ground. One call for the two: they come out of one file,
// and a window that mounted on the answer to half of them would repaint for the other half.
//
// The tag goes to i18next and not to the provider. The design system's components read the
// language off that instance, so it is the one place a language can be decided — and the
// catalogue takes its tag from there rather than being handed one in parallel.
void choicesAtLaunch().then(async ({ locale, theme }) => {
  await startSpeaking(locale)

  // The stack and the routes are the harness's too (RG126); what is only this file's is the
  // two things a test must not have. `StrictMode`, because a test asserting one toast would
  // see two under a double mount. And a hash router, because a packaged build is loaded from
  // `file://` and a path router asks the filesystem for a directory that is not there — the
  // URL is not a thing anybody types here, it is how the shell knows which surface is open.
  createRoot(host).render(
    <StrictMode>
      <ProviderStack initial={theme ?? undefined}>
        <HashRouter>
          <RoutedSurfaces />
        </HashRouter>
      </ProviderStack>
    </StrictMode>,
  )
})
