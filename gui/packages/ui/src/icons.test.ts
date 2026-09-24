import { readdirSync, readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

/**
 * RG133: the one prop that would make this renderer fetch a picture.
 *
 * RG124's check found three hosts in the built renderer that are not prose:
 * `api.iconify.design`, `api.simplesvg.com` and `api.unisvg.com`, Iconify's default
 * resource list inside `@iconify/react`. Iconify fetches an icon by name, one request per
 * name, and the packaged policy refuses all three — so a tile handed a name draws nothing,
 * on a machine that is online and one that is not.
 *
 * **What hands it a name is narrower than it looked.** RG133 was filed against the nav
 * rail, and the rail cannot do it: `BentoNavItem.icon` and `BentoNavSection.icon` are typed
 * as Tabler components, so `icon: 'mdi:folder'` on an entry in `AREAS` does not compile.
 * The two that take a string are `BentoEntityTile` and `BentoEntityShell`, whose `icon` is
 * documented as a user-picked Iconify name and whose `defaultIcon` is the bundled Tabler
 * one drawn when it is absent. This app has no user to pick one and no screen using either
 * yet — which is when a rule is cheapest to hold.
 *
 * So the rule is on the source, and it fails on the line being written rather than after a
 * build: a file that renders an entity tile or shell passes it no `icon` at all.
 */
const SOURCE = import.meta.dirname

/** This package's own source, tests excluded — a test may name the prop to prove the rule. */
function sources(): { readonly name: string; readonly text: string }[] {
  return readdirSync(SOURCE, { recursive: true, withFileTypes: true })
    .filter(
      (entry) => entry.isFile() && /\.tsx?$/.test(entry.name) && !entry.name.includes('.test.'),
    )
    .map((entry) => {
      const file = path.join(entry.parentPath, entry.name)
      return { name: path.relative(SOURCE, file), text: readFileSync(file, 'utf8') }
    })
}

/** The components whose `icon` is a name Iconify fetches. `defaultIcon` is not this. */
const FETCHING = /\bBentoEntity(?:Tile|Shell)\b/
const NAMED_ICON = /\sicon=/

/** Every file that renders one of them and passes an `icon` prop somewhere in it. */
function fetchingFiles(files: readonly { readonly name: string; readonly text: string }[]) {
  return files
    .filter((file) => FETCHING.test(file.text) && NAMED_ICON.test(file.text))
    .map((file) => file.name)
}

describe('RG133: a tile that would fetch its icon', () => {
  it('reads this package`s source, which is what makes the rule below mean anything', () => {
    // The control. A scan that found no files would pass the rule over nothing.
    expect(sources().map((file) => file.name)).toContain('Shell.tsx')
  })

  it('passes no icon name to an entity tile or shell', () => {
    expect(
      fetchingFiles(sources()),
      'these render BentoEntityTile or BentoEntityShell and pass `icon`, which is an Iconify' +
        ' name fetched from a host the packaged policy refuses. Pass a Tabler component as' +
        ' `defaultIcon` and leave `icon` unset.',
    ).toEqual([])
  })

  it('finds the prop when it is there, which is the guard on the guard', () => {
    // A specimen of the line this exists to catch, written here because the point is that
    // no source file in this package holds one. Beside it, the line that is fine.
    const caught = `<BentoEntityTile to="/p" defaultIcon={IconFolder} icon="mdi:folder" title="p" />`
    const fine = `<BentoEntityTile to="/p" defaultIcon={IconFolder} title="p" />`

    expect(fetchingFiles([{ name: 'caught.tsx', text: caught }])).toEqual(['caught.tsx'])
    expect(fetchingFiles([{ name: 'fine.tsx', text: fine }])).toEqual([])
  })
})
