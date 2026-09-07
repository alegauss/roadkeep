import { PACKAGES } from '@roadkeep-gui/core'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { App } from './App.js'

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
