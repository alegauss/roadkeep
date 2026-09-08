import { describe, expect, it } from 'vitest'

import { PACKAGES } from './packages'
import { BASE, PACKAGE_TEXT } from './wording'

describe('RG37: the package split', () => {
  it('says what every package it names is responsible for', () => {
    // RG51 moved the sentences into the wording catalogue; what is asserted is unchanged —
    // a package this app names has something to say about itself.
    for (const name of PACKAGES) {
      expect(BASE[PACKAGE_TEXT[name]]).toBeTruthy()
    }
  })

  it('describes no package it does not name', () => {
    expect(Object.keys(PACKAGE_TEXT).sort()).toEqual([...PACKAGES].sort())
  })
})
