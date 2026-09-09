import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { App } from './App'
import { GroundProvider } from './ground'
import './index.css'
import { choicesAtLaunch } from './launch'
import { startSpeaking } from './speaking'
import { WordingProvider } from './wording'

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

  createRoot(host).render(
    <StrictMode>
      <GroundProvider initial={theme ?? undefined}>
        <WordingProvider>
          <App />
        </WordingProvider>
      </GroundProvider>
    </StrictMode>,
  )
})
