import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'

import type { Translate } from '@rk/core'

import { agentCandidates } from './agent-candidates'

/**
 * The Claude Code plugin, offered on the first launch of a build with no install phase (RK1700).
 *
 * The Windows installer runs the two `claude plugin` commands after placing the app. An AppImage
 * is a file somebody runs and a dmg is a folder somebody drags, so neither has a moment to run
 * anything in — the app's first launch is the only one, and this is it.
 *
 * **Asked once, and only where it can work.** Nothing is offered on Windows, whose installer
 * already asked, nor from a checkout, which is a developer's and wired by hand. Nothing is
 * offered where no `claude` answers `--version` or no Python 3.11 answers on PATH (RK1701): a
 * question whose only answer is an error is not a question, so what is missing is named instead,
 * with where to get it. And the answer is recorded whichever it was, so a person who declined is not
 * asked on every launch — the commands are the ones `claude plugin --help` documents, and the
 * dialog names them, so running them later is theirs to do.
 *
 * **Through the CLI and never by copying.** The plugin's files are Claude Code's to place and to
 * update, so this runs its commands and does not know where they put anything.
 *
 * Kept as data and injected effects, like `menu-template.ts`, so what it promises is tested
 * without an Electron process: `main.ts` hands it the dialog and the spawn.
 */

/** The two commands, as argv after the executable. */
export const PLUGIN_COMMANDS: readonly (readonly string[])[] = [
  ['plugin', 'marketplace', 'add', 'alegauss/roadkeep'],
  ['plugin', 'install', 'roadkeep@alegauss'],
]

/** The record that the offer was made, beside the settings in this app's own directory. */
export const OFFERED_FILE = 'plugin-offered'

export interface OfferedWhere {
  readonly platform: NodeJS.Platform
  readonly packaged: boolean
  readonly userData: string
}

/** Whether this launch is the one that asks: a packaged AppImage or dmg, not asked before. */
export function offerWanted(where: OfferedWhere): boolean {
  if (!where.packaged) return false
  if (where.platform !== 'linux' && where.platform !== 'darwin') return false
  return !existsSync(path.join(where.userData, OFFERED_FILE))
}

export interface OfferDialog {
  readonly title: string
  readonly message: string
  readonly buttons: readonly string[]
}

/** The commands as a person would type them, which is how the dialog names them. */
const TYPED = PLUGIN_COMMANDS.map((argv) => ['claude', ...argv].join(' '))

export function askDialog(say: Translate): OfferDialog {
  return {
    title: say('plugin.title'),
    message: say('plugin.ask', { commands: TYPED.join('\n') }),
    buttons: [say('plugin.install'), say('plugin.decline')],
  }
}

/** What the second dialog says: the command that failed and its exit, or that it worked. */
export function resultDialog(failed: { command: string; code: number } | null, say: Translate) {
  return {
    title: say('plugin.title'),
    message:
      failed === null
        ? say('plugin.done')
        : say('plugin.failed', { command: failed.command, code: String(failed.code) }),
    buttons: [say('update.close')],
  } satisfies OfferDialog
}

export interface Offering extends OfferedWhere {
  readonly say: Translate
  /** Run one argv and answer its exit code, or -1 where it could not start. */
  readonly run: (argv: readonly string[]) => Promise<number>
  /** Show a dialog and answer which button was chosen, by index. */
  readonly show: (dialog: OfferDialog) => Promise<number>
  readonly home?: string
}

/**
 * The check the plugin's server needs to pass (RK1701): it is `python scripts/roadkeep.py mcp`,
 * and roadkeep's floor is 3.11. Run and never imported — nothing of the package is read, so the
 * "no supported Python API" non-goal is not what this touches.
 */
export const PYTHON_FLOOR = 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'

/** The names a Python goes by, in the order a Unix PATH is likelier to answer. */
const PYTHONS = ['python3', 'python']

/** Whether some Python on PATH is 3.11 or newer. */
export async function pythonAnswers(offering: Offering): Promise<boolean> {
  for (const python of PYTHONS) {
    if ((await offering.run([python, '-c', PYTHON_FLOOR])) === 0) return true
  }
  return false
}

/** What is missing, each with where to get it, in the words the window speaks. */
export function missingDialog(
  missing: readonly ('python' | 'claude')[],
  say: Translate,
): OfferDialog {
  return {
    title: say('plugin.title'),
    message: [
      say('plugin.missing'),
      ...missing.map((one) =>
        say(one === 'python' ? 'plugin.missing.python' : 'plugin.missing.claude'),
      ),
      say('plugin.missing.later', { commands: TYPED.join('\n') }),
    ].join('\n\n'),
    buttons: [say('update.close')],
  }
}

/** The `claude` that answers `--version`, first of the candidates the sessions use, or null. */
export async function answeringClaude(offering: Offering): Promise<readonly string[] | null> {
  for (const candidate of agentCandidates(
    offering.home === undefined ? {} : { home: offering.home },
  )) {
    if ((await offering.run([...candidate, '--version'])) === 0) return candidate
  }
  return null
}

/**
 * Ask, run, report — or do nothing. Answers what happened, for the test and the log.
 *
 * The record is written the moment the question is decided — asked, or found pointless —
 * and before anything runs, so a crash mid-install is not a question asked again forever.
 */
export async function offerPlugin(
  offering: Offering,
): Promise<'not-wanted' | 'missing' | 'declined' | 'installed' | 'failed'> {
  if (!offerWanted(offering)) return 'not-wanted'
  const claude = await answeringClaude(offering)
  const python = await pythonAnswers(offering)
  // Named rather than skipped in silence (RK1701): a plugin installed on a machine with no
  // Python fails on its first call, far from the cause, and one never offered because the CLI
  // is absent leaves a person not knowing there was anything to offer. Said once, like the ask.
  const missing = [
    ...(python ? [] : ['python' as const]),
    ...(claude === null ? ['claude' as const] : []),
  ]
  if (claude === null || missing.length > 0) {
    record(offering.userData)
    await offering.show(missingDialog(missing, offering.say))
    return 'missing'
  }
  const chosen = await offering.show(askDialog(offering.say))
  record(offering.userData)
  if (chosen !== 0) return 'declined'

  let failed: { command: string; code: number } | null = null
  for (const argv of PLUGIN_COMMANDS) {
    const code = await offering.run([...claude, ...argv])
    // `marketplace add` exits non-zero where the marketplace is already there, which is the
    // state it exists to reach; the install is the one whose exit is the answer.
    if (argv[1] === 'install' && code !== 0) {
      failed = { command: ['claude', ...argv].join(' '), code }
    }
  }
  await offering.show(resultDialog(failed, offering.say))
  return failed === null ? 'installed' : 'failed'
}

function record(userData: string): void {
  mkdirSync(userData, { recursive: true })
  writeFileSync(path.join(userData, OFFERED_FILE), '', 'utf8')
}
