import { PRODUCT, saidOfVersion, THEME_TEXT } from '@rk/core'
import { AppFooter, Button, LanguageSwitcher, Toaster, toast } from '@viglet/viglet-design-system'
import {
  BentoBackToTop,
  BentoCommandPalette,
  BentoNavRail,
  BentoShortcutsDialog,
} from '@viglet/viglet-design-system/bento'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Outlet } from 'react-router-dom'

import { AREAS, HOME_ROUTE, surfacesIn } from './areas'
import { useGround } from './ground'
import { noticesAtLaunch } from './launch'
import { SPOKEN_LOCALES } from './speaking'
import { useIdentity } from './useTransport'
import { useWording } from './wording'

/**
 * The chrome, adopted once, before any screen is written against it.
 *
 * The design system's bento layer is a shared page vocabulary — a rail, a header, a command
 * palette, a shortcuts sheet, a back-to-top — and its own guidance is that the first mistake
 * is a page that looks bento inside a console that does not. So this is the shell and not a
 * screen: what it draws is the frame every surface in blocks C to F will open inside.
 *
 * **The rail is the nav and the palette is the mobile one.** The rail is fixed, one width
 * and hidden below `md`; `bento-rail-gutter` on the wrapper is what keeps content out from
 * under it. There is no second always-visible nav, and no provider between the pieces —
 * nothing here holds state another piece reads.
 *
 * **The shell owns the reading column.** The max width, the gutters and the vertical rhythm
 * are set here once, so every page begins and ends on the same line. A page that sets its
 * own is the defect that exists only *between* screens, which is why nobody reviewing one of
 * them ever sees it.
 *
 * **`BentoUserMenu` is absent rather than passed empty strings.** Its props are
 * `accountRoute` and `logoutUrl` and it exists to sign somebody out, which *no account, no
 * auth and no remote store in the desktop build* forbids outright. The shortcuts button
 * takes the corner it would have had: the package's own answer for reaching that sheet is
 * the user menu, and with no user menu the only way in would be a keyboard shortcut nothing
 * on screen mentions.
 *
 * **And it names the build** (RG118). `AppFooter` is the package's own answer and the one
 * region `authoring.md` leaves unsettled, its rule being that either the shell carries a
 * footer for every page or the chrome has none — so it is mounted here, where every screen
 * inherits it, and never by a page. What it prints is the line `core` composes for a defect
 * report, because a person quoting a version and being asked for the commit is a report
 * that has become a conversation about which build they have.
 *
 * The header was the alternative, and `docs/design/Main.dc.html` turns out not to draw this
 * there: the pill on its trailing edge is the *engine's* version behind a status dot, which
 * is a different fact about a different program.
 *
 * **And it carries the notice surface** (RG115). A setting that could not be read, and a
 * choice that could not be saved, are both things the app knew and nobody was told — the
 * sentences were composed and thrown away. `Toaster` is the design system's and reads the
 * ground from the same `next-themes` this app already mounts, so there is one of it and it
 * lives here, where every screen is already inside it.
 */

/** Past which the two global keys are the platform's own. */
function isMac(): boolean {
  return typeof navigator === 'object' && navigator.userAgent.includes('Mac')
}

/**
 * Whether a keystroke belongs to whatever the reader is typing into.
 *
 * `?` is a global, and a global that fires inside a search box is a search box that cannot
 * contain a question mark.
 */
function typingInto(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  return (
    target.isContentEditable ||
    target instanceof HTMLInputElement ||
    target instanceof HTMLTextAreaElement ||
    target instanceof HTMLSelectElement
  )
}

/** A prop, so it is built once: a fresh array per render re-renders the menu. */
const LOCALE_ROWS = [...SPOKEN_LOCALES]

export function AppShell() {
  const say = useWording()
  const { theme, cycle } = useGround()
  const identified = useIdentity()
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [shortcutsOpen, setShortcutsOpen] = useState(false)
  const mac = isMac()

  const openPalette = useCallback(() => {
    setPaletteOpen(true)
  }, [])
  const openShortcuts = useCallback(() => {
    setShortcutsOpen(true)
  }, [])

  // Once per mount and never per render: React mounts twice under StrictMode in
  // development, and a person opening the app would see every sentence twice.
  const said = useRef(false)
  useEffect(() => {
    if (said.current) return
    said.current = true

    // The frame is this app's own voice and translated; the sentences are the ones
    // `readSettings` composed, shown as it wrote them. One toast per loss, because two
    // fields resetting for two reasons is two things a person may want to act on.
    for (const lost of noticesAtLaunch()) {
      toast.warning(say('settings.reset'), { description: lost })
    }
  }, [say])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setPaletteOpen((open) => !open)
        return
      }
      if (event.key === '?' && !typingInto(event.target)) {
        event.preventDefault()
        setShortcutsOpen(true)
      }
    }

    window.addEventListener('keydown', onKey)
    return () => {
      window.removeEventListener('keydown', onKey)
    }
  }, [])

  return (
    <>
      <BentoNavRail groups={AREAS} homeRoute={HOME_ROUTE} homeLabel={say('shell.home')} />

      <header className="bento-shell-header bento-glass sticky top-0 z-30 flex items-center gap-4 px-4 py-3 md:pl-20">
        <span className="font-brand text-lg font-semibold tracking-tight">{say('app.name')}</span>

        {/*
         * The palette trigger carries the platform's own hint, which is why the glyph is
         * computed and not written: a window on a Mac that says `Ctrl K` is a window that
         * lies about its own keyboard.
         */}
        <Button
          variant="outline"
          size="sm"
          className="text-muted-foreground min-w-0 flex-1 justify-between gap-3"
          onClick={openPalette}
          data-testid="palette-trigger"
        >
          <span className="truncate">{say('shell.palette')}</span>
          <kbd className="font-mono text-xs">{mac ? '⌘K' : 'Ctrl K'}</kbd>
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={openShortcuts}
          aria-label={say('shell.shortcuts')}
          data-testid="shortcuts"
        >
          <kbd className="font-mono text-xs">?</kbd>
        </Button>

        {/*
         * The language, beside the ground, which is where `authoring.md` puts a second
         * global control (RG116). Until this the app spoke two languages and offered no way
         * to say which: choosing one meant editing the settings file by hand.
         *
         * It holds nothing and takes no handler, which is right rather than a gap - it
         * moves i18next, i18next holds the language, and `speaking` keeps whatever it is
         * now speaking. The alternative in the package, `LanguageSelect`, draws each row's
         * flag from `flagcdn.com`: a network request out of a desktop app that reads local
         * repositories, on a screen that works offline by design.
         */}
        <LanguageSwitcher languages={LOCALE_ROWS} />

        {/*
         * The ground says which of the three it is set to and not which of the two it
         * resolved to - `system` and `light` look identical on a machine set to light, and
         * the setting is what the person chose. Words rather than an icon, because nothing
         * on this screen is told by colour or shape alone.
         */}
        <Button
          variant="outline"
          size="sm"
          onClick={cycle}
          aria-label={say('ground.action')}
          data-testid="ground"
        >
          {say(THEME_TEXT[theme])}
        </Button>
      </header>

      <div className="bento-rail-gutter">
        <main className="mx-auto flex w-full max-w-5xl flex-col gap-8 px-6 py-10">
          <Outlet />
        </main>
      </div>

      {/*
       * Named, always; versioned once the bridge answers. A build nobody has been told
       * about yet is drawn as the product alone rather than as a guess or a blank — which
       * is also what a plain browser tab shows, honestly, for as long as it has no bridge.
       */}
      <AppFooter
        productName={PRODUCT}
        version={identified.kind === 'known' ? saidOfVersion(identified.identity.build) : undefined}
      />

      <BentoCommandPalette
        open={paletteOpen}
        onOpenChange={setPaletteOpen}
        items={surfacesIn(AREAS)}
      />
      <BentoShortcutsDialog open={shortcutsOpen} onOpenChange={setShortcutsOpen} isMac={mac} />
      <BentoBackToTop />
      {/*
       * One of these, in the chrome, so a notice from any screen has somewhere to land and
       * nothing has to mount a second. It reads the ground from the `next-themes` this app
       * already has (RG52), which is why it takes nothing here.
       */}
      <Toaster />
    </>
  )
}
