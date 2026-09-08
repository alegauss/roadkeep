import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { App } from './App'
import './index.css'
import { WordingProvider } from './wording'

const host = document.getElementById('root')
if (!host) {
  throw new Error('index.html has no #root to mount into')
}

// No translation is passed yet, which is English. The locale is a setting the shell holds,
// so the day the bridge carries settings across, it arrives here and nothing else moves.
createRoot(host).render(
  <StrictMode>
    <WordingProvider>
      <App />
    </WordingProvider>
  </StrictMode>,
)
