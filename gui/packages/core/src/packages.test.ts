import { describe, expect, it } from 'vitest'

import { PACKAGES, RESPONSIBILITY } from './packages.js'

describe('RG37: the package split', () => {
  it('says what every package it names is responsible for', () => {
    for (const name of PACKAGES) {
      expect(RESPONSIBILITY[name]).toBeTruthy()
    }
  })

  it('describes no package it does not name', () => {
    expect(Object.keys(RESPONSIBILITY).sort()).toEqual([...PACKAGES].sort())
  })
})
