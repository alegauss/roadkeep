import { PACKAGES, type RendererBridge } from '@rk/core'
import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { App } from './App'

function withBridge(bridge: RendererBridge): void {
  Object.defineProperty(window, 'roadkeep', { value: bridge, configurable: true })
}

afterEach(() => {
  Reflect.deleteProperty(window, 'roadkeep')
})

describe('RG37: the scaffold screen', () => {
  it('renders without a display', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: 'roadkeep' })).toBeTruthy()
  })

  it('draws a row for every package core names', () => {
    render(<App />)
    for (const name of PACKAGES) {
      expect(screen.getByText(name)).toBeTruthy()
    }
  })
})

describe('RG44: the renderer through the bridge', () => {
  it('renders with no bridge at all, which is what a browser tab gives it', async () => {
    render(<App />)
    expect(await screen.findByText(/no bridge/)).toBeTruthy()
  })

  it('names the transport the bridge reports, without knowing what is behind it', async () => {
    withBridge({ identify: () => Promise.resolve({ transport: 'ipc' }) })
    render(<App />)
    expect(await screen.findByText(/over IPC/)).toBeTruthy()
  })

  it('renders the same screen over a transport that is not a process', async () => {
    withBridge({ identify: () => Promise.resolve({ transport: 'http' }) })
    render(<App />)
    expect(await screen.findByText(/over HTTP/)).toBeTruthy()
    for (const name of PACKAGES) {
      expect(screen.getByText(name)).toBeTruthy()
    }
  })

  it('falls back to absent when the bridge rejects', async () => {
    withBridge({ identify: () => Promise.reject(new Error('channel closed')) })
    render(<App />)
    expect(await screen.findByText(/no bridge/)).toBeTruthy()
  })
})
