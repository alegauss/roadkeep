import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { App } from './App'
import { GroundProvider } from './ground'
import './index.css'
import { WordingProvider } from './wording'

const host = document.getElementById('root')
if (!host) {
  throw new Error('index.html has no #root to mount into')
}

// Neither the locale nor the ground is passed yet, so both start where their defaults are:
// English, and following the desktop. Both are settings the shell holds, so the day the
// bridge carries settings across they arrive here as props and nothing else moves.
createRoot(host).render(
  <StrictMode>
    <GroundProvider>
      <WordingProvider>
        <App />
      </WordingProvider>
    </GroundProvider>
  </StrictMode>,
)
