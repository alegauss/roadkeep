import { describe, expect, it } from 'vitest'

import { reviewNavigation, reviewWindowOpen } from './navigation'

const DEV = 'http://localhost:5173/'
const BUNDLE = 'file:///d:/app/packages/ui/dist/index.html'

describe('RG44: navigating in development', () => {
  it('lets the app move within its own dev server', () => {
    expect(reviewNavigation('http://localhost:5173/settings', DEV)).toBe('allow')
  })

  it('refuses another port on the same machine', () => {
    expect(reviewNavigation('http://localhost:9229/', DEV)).toBe('open-externally')
  })

  it('sends a link somewhere else to the system browser', () => {
    expect(reviewNavigation('https://example.com/', DEV)).toBe('open-externally')
  })

  it('refuses a local file, which no page should be able to reach for', () => {
    expect(reviewNavigation('file:///c:/windows/win.ini', DEV)).toBe('refuse')
  })
})

describe('RG44: navigating in a packaged run', () => {
  it('lets the bundle load its own sibling', () => {
    expect(reviewNavigation('file:///d:/app/packages/ui/dist/about.html', BUNDLE)).toBe('allow')
  })

  it('refuses a file outside the bundle, which origin alone would have allowed', () => {
    expect(reviewNavigation('file:///d:/secrets/keys.txt', BUNDLE)).toBe('refuse')
  })

  it('refuses a path that only starts like the bundle', () => {
    expect(reviewNavigation('file:///d:/app/packages/ui/dist-evil/x.html', BUNDLE)).toBe('refuse')
  })

  it('still sends the web outward', () => {
    expect(reviewNavigation('https://example.com/', BUNDLE)).toBe('open-externally')
  })
})

describe('RG44: the schemes that are never followed', () => {
  it.each([
    'javascript:alert(1)',
    'data:text/html,<script>alert(1)</script>',
    'about:blank',
    'not a url at all',
  ])('refuses %s', (target) => {
    expect(reviewNavigation(target, DEV)).toBe('refuse')
    expect(reviewWindowOpen(target)).toBe('refuse')
  })

  it('refuses an unparseable app URL rather than guessing', () => {
    expect(reviewNavigation('https://example.com/', 'nonsense')).toBe('refuse')
  })
})

describe('RG44: opening a window', () => {
  it('never opens one, and hands the web to the system browser', () => {
    expect(reviewWindowOpen('https://example.com/')).toBe('open-externally')
    expect(reviewWindowOpen('mailto:someone@example.com')).toBe('open-externally')
  })

  it('refuses a file even though a navigation inside the bundle would be allowed', () => {
    expect(reviewWindowOpen('file:///d:/app/packages/ui/dist/index.html')).toBe('refuse')
  })
})
