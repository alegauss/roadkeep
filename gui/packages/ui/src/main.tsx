import { wordingFor } from '@rk/core'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { App } from './App'
import { GroundProvider } from './ground'
import './index.css'
import { choicesAtLaunch } from './launch'
import { WordingProvider } from './wording'

const host = document.getElementById('root')
if (!host) {
  throw new Error('index.html has no #root to mount into')
}

// Both settings are asked for before anything mounts, so the first frame is already in the
// right language and on the right ground. One call for the two: they come out of one file,
// and a window that mounted on the answer to half of them would repaint for the other half.
void choicesAtLaunch().then(({ locale, theme }) => {
  createRoot(host).render(
    <StrictMode>
      <GroundProvider initial={theme ?? undefined}>
        <WordingProvider over={wordingFor(locale)}>
          <App />
        </WordingProvider>
      </GroundProvider>
    </StrictMode>,
  )
})
