import { wordingFor } from '@rk/core'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { App } from './App'
import { GroundProvider } from './ground'
import './index.css'
import { localeAtLaunch } from './locale'
import { WordingProvider } from './wording'

const host = document.getElementById('root')
if (!host) {
  throw new Error('index.html has no #root to mount into')
}

// The locale is asked for before anything mounts, so the first frame is already in the
// right language. The ground is not passed yet and still starts at its default of following
// the desktop: it is the same settings object over the same bridge, and RG87 is what makes
// the file's answer the one that wins.
void localeAtLaunch().then((locale) => {
  createRoot(host).render(
    <StrictMode>
      <GroundProvider>
        <WordingProvider over={wordingFor(locale)}>
          <App />
        </WordingProvider>
      </GroundProvider>
    </StrictMode>,
  )
})
