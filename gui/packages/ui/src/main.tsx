import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { App } from './App.js'
import './index.css'

const host = document.getElementById('root')
if (!host) {
  throw new Error('index.html has no #root to mount into')
}

createRoot(host).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
