import {
  isSessionNotes,
  isTheme,
  THEME_ORDER,
  type MessageKey,
  type SessionNotes,
  type Theme,
} from '@rk/core'
import { IconCheck, IconPalette, IconTerminal2 } from '@tabler/icons-react'
import { ToggleGroup, ToggleGroupItem } from '@viglet/viglet-design-system'
import { BentoFormSection, BentoHero } from '@viglet/viglet-design-system/bento'
import { changeLanguage } from 'i18next'
import { useCallback, useId, useMemo } from 'react'

import { useGround } from './ground'
import { chooseSessionNotes, useSessionNotes } from './preferring'
import { SPOKEN_LOCALES, useSpokenLocale } from './speaking'
import { useWording } from './wording'

/**
 * The preferences a person chooses, on one screen (RG207).
 *
 * The ground and the language were controls in the header and nowhere else, each with a
 * bridge method named for it, and the next preference had no place to go. This is the place:
 * a hero, and one `BentoFormSection` per group.
 *
 * **Applied as chosen, so there is no save bar.** Every control here writes the moment it
 * changes, as the header's always have — through `PREFERENCES`, the one write the bridge
 * offers. A screen that staged changes behind a Save would disagree with the header about
 * whether the ground a reader just picked is kept.
 *
 * **The same state the header moves, never a copy.** The ground is `useGround`, which is
 * `next-themes`; the language is i18next, whose own event is what writes it back. Choosing
 * here moves the header's control too, and choosing there moves this one.
 */

/** The words for each ground, as a choice rather than as the header's sentence about it. */
const GROUND_TEXT: Readonly<Record<Theme, MessageKey>> = {
  system: 'settings.ground.system',
  light: 'settings.ground.light',
  dark: 'settings.ground.dark',
}

/** How a session draws its system notes (RG208), shown first because that is the default. */
const NOTES_ORDER: readonly SessionNotes[] = ['shown', 'hidden']

const NOTES_TEXT: Readonly<Record<SessionNotes, MessageKey>> = {
  shown: 'settings.notes.shown',
  hidden: 'settings.notes.hidden',
}

interface Option {
  readonly value: string
  readonly label: string
}

/**
 * Each language by the name it calls itself, as the header's menu names it — the reader
 * looking for a language is the one who cannot read the one on screen. Built once, from the
 * same rows the menu takes.
 */
const LANGUAGES: readonly Option[] = SPOKEN_LOCALES.map(({ code, label }) => ({
  value: code,
  label,
}))

/**
 * One labelled choice among a few, all visible at once.
 *
 * A toggle group and not a select: two to four options read at a glance and take one click,
 * and a menu would hide the thing being chosen behind the act of opening it. Radix answers a
 * click on the chosen option with an empty value, which is not a choice, so it is dropped.
 */
function Choice({
  label,
  value,
  options,
  onChoose,
}: {
  readonly label: string
  readonly value: string
  readonly options: readonly Option[]
  readonly onChoose: (value: string) => void
}) {
  const labelled = useId()
  const chose = useCallback(
    (next: string) => {
      if (next !== '') onChoose(next)
    },
    [onChoose],
  )

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <span id={labelled} className="text-sm font-medium">
        {label}
      </span>
      <ToggleGroup
        type="single"
        variant="outline"
        size="sm"
        value={value}
        onValueChange={chose}
        aria-labelledby={labelled}
      >
        {/* The chosen option carries a mark, not the package's accent alone: measured in the
            dark ground, that accent sits at 1.27:1 against the panel — a state told by a
            shade nobody can see, and by colour at that. `aria-checked` says it to a reader. */}
        {options.map((option) => (
          <ToggleGroupItem key={option.value} value={option.value}>
            {option.value === value ? <IconCheck size={14} aria-hidden="true" /> : null}
            {option.label}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>
    </div>
  )
}

export function Settings() {
  const say = useWording()
  const { theme, setTheme } = useGround()
  const spoken = useSpokenLocale()

  const grounds = useMemo(
    () => THEME_ORDER.map((one) => ({ value: one, label: say(GROUND_TEXT[one]) })),
    [say],
  )

  const chooseGround = useCallback(
    (next: string) => {
      if (isTheme(next)) setTheme(next)
    },
    [setTheme],
  )
  const chooseLanguage = useCallback((next: string) => {
    void changeLanguage(next)
  }, [])

  const notes = useSessionNotes()
  const noteChoices = useMemo(
    () => NOTES_ORDER.map((one) => ({ value: one, label: say(NOTES_TEXT[one]) })),
    [say],
  )
  const chooseNotes = useCallback((next: string) => {
    if (isSessionNotes(next)) chooseSessionNotes(next)
  }, [])

  return (
    <>
      <BentoHero
        eyebrow={say('settings.kicker')}
        title={say('settings.title')}
        subtitle={say('settings.subtitle')}
      />
      <BentoFormSection
        icon={IconPalette}
        tone="amber"
        title={say('settings.appearance')}
        description={say('settings.appearance.about')}
      >
        <div className="flex flex-col gap-4" data-testid="appearance">
          <Choice
            label={say('settings.ground')}
            value={theme}
            options={grounds}
            onChoose={chooseGround}
          />
          <Choice
            label={say('settings.language')}
            value={spoken}
            options={LANGUAGES}
            onChoose={chooseLanguage}
          />
        </div>
      </BentoFormSection>
      <BentoFormSection
        icon={IconTerminal2}
        tone="amber"
        title={say('settings.sessions')}
        description={say('settings.sessions.about')}
      >
        <div className="flex flex-col gap-4" data-testid="sessions-settings">
          <Choice
            label={say('settings.notes')}
            value={notes}
            options={noteChoices}
            onChoose={chooseNotes}
          />
        </div>
      </BentoFormSection>
    </>
  )
}
