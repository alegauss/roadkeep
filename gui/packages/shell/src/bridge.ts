import {
  acceptRoots,
  BRIDGE_CHANNELS,
  BRIDGE_UNSUBSCRIBE,
  EVERY_SOURCE,
  isTopic,
  projectsAtOnce,
  requestFrom,
  resolveAgent,
  translator,
  withheldResult,
  withPreference,
  withPresence,
  wordingFor,
  type BridgedResult,
  type BridgeIdentity,
  type EditedFile,
  type FileText,
  type GovernedFile,
  type HandedOver,
  type KnownRoot,
  type LaunchSettings,
  type OpenedProject,
  type ProjectGate,
} from '@rk/core'
import { cpus } from 'node:os'

import { app, BrowserWindow, dialog, ipcMain, type WebContents } from 'electron'

import { AGENT_VAR, agentCandidates, agentOverride } from './agent-candidates'
import { loadCatalogue, saveCatalogue } from './catalogue-file'
import { createCarrier, type Carrier } from './carrier'
import { editedAt } from './edited-at'
import { fileText } from './file-text'
import { governedAt } from './governed-at'
import { createSubscriptions, type Subscriber } from './subscriptions'
import { localeChoice } from './locale'
import { createProcessTransport } from './process-transport'
import { rootExists, rootKey } from './root-paths'
import { sessionEnvironment } from './session-environment'
import { createSessions } from './sessions'
import { loadSettings, saveSettings } from './settings-file'
import { readStamp } from './stamp'

/**
 * The main-process end of the renderer's one channel. Every handler registered here is a
 * power the renderer gains, so the list is meant to stay short and to stay readable in one
 * screen: what this file handles is exactly what a compromised renderer can reach. Since
 * RG143 that includes the engine, bounded by what `carrier.ts` refuses.
 *
 * The build is read once, as the bridge is registered. It cannot change while the app runs,
 * and reading a file on every call would be a file read a renderer gets to ask for.
 */
export interface BridgeHooks {
  /** Called once a language is saved, so what this process draws itself can follow (RG50). */
  readonly localeSaved?: () => void
}

/**
 * Register every handler, and hand back what holds processes: the carrier's engines and the
 * sessions started from a window (RG153), which are what quitting awaits.
 */
export function registerBridge(hooks: BridgeHooks = {}): Pick<Carrier, 'close'> {
  const build = readStamp(import.meta.dirname, app.isPackaged)

  ipcMain.handle(BRIDGE_CHANNELS.identify, (): BridgeIdentity => ({ transport: 'ipc', build }))

  // The settings, unlike the build, are read per call: the file is documented as one a
  // person may edit by hand, and a copy taken at startup is one only a restart refreshes.
  // The path read is this app's own settings file and never one the renderer names, which
  // is what keeps a handler that touches the filesystem off the list of powers it gains.
  ipcMain.handle(BRIDGE_CHANNELS.settings, (): LaunchSettings => {
    const read = loadSettings(app.getPath('userData'))
    return {
      ...read,
      locale: localeChoice(read.settings.locale, app.getLocale()),
      // Decided here for the same reason the locale is (RG250): the file may name no number,
      // and what stands in for none is this machine's core count.
      projectsAtOnce: projectsAtOnce(read.settings.projectsAtOnce, cpus().length),
    }
  })

  // The one write of a preference the renderer can ask for (RG207), and it reaches exactly
  // the fields `PREFERENCES` names. The file is re-read rather than remembered so a root
  // somebody added by hand a moment ago survives a click on the ground, and both arguments
  // are checked here because a channel argument is the renderer's word: each row's check is
  // the reader's, so nothing gets in that a later read would reset. A refusal throws, which
  // rejects the page's call — a choice not kept is said, not discovered at the next launch.
  ipcMain.handle(BRIDGE_CHANNELS.savePreference, (_event, key: unknown, value: unknown): void => {
    const userData = app.getPath('userData')
    const written = withPreference(loadSettings(userData).settings, key, value)
    if (written === null) throw new Error(`${String(key)} cannot be set to that value`)
    saveSettings(userData, written)
    if (key === 'locale') hooks.localeSaved?.()
  })

  // The three that reach an engine (RG143). Where to look is read per call, like the
  // settings above, so a root somebody added by hand is scanned the next time the window
  // asks. Every argument is still the renderer's word: a root that is not a string opens
  // nothing, and a request that is not one runs nothing — both before the carrier is asked.
  // The carrier is made before the subscriptions it publishes through — they are made from
  // its own `follow` — so what it tells is held here and filled in below. Before that, a
  // verdict is on record and `gates` answers it; nobody is listening yet either way.
  let tellGate: (gate: ProjectGate) => void = () => undefined
  let tellCatalogue: (changed: number) => void = () => undefined
  const carrier = createCarrier({
    onGate: (gate) => {
      tellGate(gate)
    },
    onCatalogue: (changed) => {
      tellCatalogue(changed)
    },
    looking: () => {
      const { roots, skip, width } = loadSettings(app.getPath('userData')).settings
      return { roots, skip, width }
    },
    // What the last launch found, beside the settings (RG164): the first screen draws it
    // while the walk behind it runs, and a project that went missing stays on the list as
    // missing instead of being forgotten at the quit.
    remembered: () => loadCatalogue(app.getPath('userData')),
    remember: (catalogue) => {
      saveCatalogue(app.getPath('userData'), catalogue)
    },
  })

  ipcMain.handle(BRIDGE_CHANNELS.projects, () => carrier.projects())

  ipcMain.handle(BRIDGE_CHANNELS.open, (_event, root: unknown): Promise<OpenedProject> => {
    if (typeof root !== 'string') {
      return Promise.resolve({ kind: 'withheld', root: '', reason: 'no root was named' })
    }
    return carrier.open(root)
  })

  ipcMain.handle(
    BRIDGE_CHANNELS.run,
    (_event, root: unknown, request: unknown): Promise<BridgedResult> => {
      const asked = requestFrom(request)
      if (typeof root !== 'string' || asked === null) {
        return Promise.resolve(
          withheldResult('the request is not one this bridge carries', 'not-carried'),
        )
      }
      return carrier.run(root, asked)
    },
  )

  // Taking a door the engine offered (RG165). Every argument is the renderer's word and
  // none of them is a command line: the argv is the one the carrier kept for that answer,
  // and what a page supplies is which door and the prose for its blanks.
  ipcMain.handle(
    BRIDGE_CHANNELS.door,
    (_event, root: unknown, offered: unknown, which: unknown, words: unknown) => {
      if (
        typeof root !== 'string' ||
        typeof offered !== 'string' ||
        typeof which !== 'number' ||
        !Array.isArray(words) ||
        !words.every((word) => typeof word === 'string')
      ) {
        return Promise.resolve(
          withheldResult('that is not a door this bridge can take', 'no-such-door'),
        )
      }
      return carrier.door(root, offered, which, words)
    },
  )

  // What main hears and nobody asked for (RG144). Sent rather than invoked: a subscription
  // has no answer, and its events arrive on the topic's own channel for as long as it
  // stands. A window's subscriptions go with the page they belong to — a reload leaves a
  // new page with no listeners, and a closed window leaves nothing to send to.
  const subscriptions = createSubscriptions({
    governed: (root, heard) => carrier.follow(root, heard),
  })
  // A gate the carrier ran, told to whoever is watching that project (RG166). No source to
  // start: like a session's lines, these arrive because something happened, not because a
  // subscription went looking.
  tellGate = (gate) => {
    subscriptions.publish('gate', gate.root, gate)
  }
  // The walk behind the record landed and moved something (RG180). One catalogue, so one
  // key, which is the one a screen subscribes with.
  tellCatalogue = (changed) => {
    subscriptions.publish('catalogue', EVERY_SOURCE, { changed })
  }
  const windows = new Map<number, Subscriber>()
  const subscriberOf = (sender: WebContents): Subscriber => {
    const known = windows.get(sender.id)
    if (known !== undefined) return known
    const made: Subscriber = {
      id: sender.id,
      send: (channel, event) => {
        sender.send(channel, event)
      },
      isDestroyed: () => sender.isDestroyed(),
    }
    windows.set(sender.id, made)
    const forget = (): void => {
      subscriptions.drop(made)
    }
    sender.on('did-navigate', forget)
    sender.once('destroyed', () => {
      windows.delete(sender.id)
      forget()
    })
    return made
  }

  ipcMain.on(BRIDGE_CHANNELS.subscribe, (event, topic: unknown, key: unknown) => {
    if (!isTopic(topic) || typeof key !== 'string') return
    subscriptions.subscribe(subscriberOf(event.sender), topic, key)
  })
  ipcMain.on(BRIDGE_UNSUBSCRIBE, (event, topic: unknown, key: unknown) => {
    if (!isTopic(topic) || typeof key !== 'string') return
    subscriptions.unsubscribe(subscriberOf(event.sender), topic, key)
  })

  // Where to look, written from the window (RG146) — the third write, and the one that names
  // folders. A folder reaches the file only through the dialog below or because the file
  // already held it, so the roots are a list the person made and never one a page typed: the
  // keys of what the dialog answered are what `acceptRoots` checks a new root against.
  const chosen = new Set<string>()
  const known = (roots: LaunchSettings['settings']['roots']): Promise<KnownRoot[]> =>
    withPresence(roots, rootExists)

  ipcMain.handle(BRIDGE_CHANNELS.roots, () =>
    known(loadSettings(app.getPath('userData')).settings.roots),
  )

  ipcMain.handle(BRIDGE_CHANNELS.chooseRoot, async (event): Promise<string | null> => {
    const settings = loadSettings(app.getPath('userData')).settings
    // The tag twice rather than once: it chooses the translation, and it is the rule that
    // chooses among a counted sentence's forms (RG216).
    const tag = localeChoice(settings.locale, app.getLocale())
    const say = translator(wordingFor(tag), tag)
    const options = { title: say('roots.choose'), properties: ['openDirectory' as const] }
    const parent = BrowserWindow.fromWebContents(event.sender)
    const answer =
      parent === null
        ? await dialog.showOpenDialog(options)
        : await dialog.showOpenDialog(parent, options)
    const picked = answer.canceled ? undefined : answer.filePaths[0]
    if (picked === undefined) return null
    chosen.add(rootKey(picked))
    return picked
  })

  ipcMain.handle(BRIDGE_CHANNELS.saveRoots, (_event, asked: unknown): Promise<KnownRoot[]> => {
    const userData = app.getPath('userData')
    const settings = loadSettings(userData).settings
    const roots = acceptRoots(asked, settings.roots, chosen, rootKey)
    saveSettings(userData, { ...settings, roots })
    return known(roots)
  })

  // A line handed to Claude Code (RG153), and the one power here that starts an agent. The
  // renderer names a root and an id; the prompt is the brief `sessions` reads through the
  // carrier, so a page cannot put words of its own in front of a session.
  const sessions = createSessions({
    carrier,
    agent: (root) =>
      resolveAgent(
        (command) =>
          createProcessTransport({ command: command[0] ?? '', prefixArgs: command.slice(1) }),
        root,
        // A scripted agent first where an unpackaged app was pointed at one (RG210).
        agentCandidates({ override: agentOverride(process.env[AGENT_VAR], app.isPackaged) }),
      ),
    // The login this machine's Claude Code has, over a key the machine carries (RG205).
    environment: (agent, root) =>
      sessionEnvironment(
        (command, env) =>
          createProcessTransport({ command: command[0] ?? '', prefixArgs: command.slice(1), env }),
        agent.command,
        root,
      ),
    // Which folders are not a session's work, read per call like everything else off the
    // settings (RG247): a name added by hand reaches the next session started.
    skip: () => loadSettings(app.getPath('userData')).settings.skip,
    publish: (event) => {
      subscriptions.publish('session', event.session, event)
    },
  })

  ipcMain.handle(
    BRIDGE_CHANNELS.handOver,
    (_event, root: unknown, id: unknown): Promise<HandedOver> => {
      if (typeof root !== 'string' || typeof id !== 'string') {
        return Promise.resolve({ kind: 'withheld', reason: 'no line was named' })
      }
      return sessions.handOver(root, id)
    },
  )
  // When each governed file last changed (RG153), which is the disk's answer and not the
  // engine's. Which files those are is the project's own config, read off the opening, so a
  // root this carrier will not open is answered with nothing rather than with a stat.
  ipcMain.handle(
    BRIDGE_CHANNELS.governedAt,
    async (_event, root: unknown): Promise<GovernedFile[]> => {
      if (typeof root !== 'string') return []
      const opened = await carrier.open(root)
      return opened.kind === 'open' ? governedAt(root, opened.governed) : []
    },
  )
  // What the disk says about the files a session's calls edited (RG244). The page names the
  // session and the paths; the root is the one this process started that session in, so a key
  // it never issued is answered with nothing, and a path outside that root is never statted.
  ipcMain.handle(BRIDGE_CHANNELS.editedAt, (_event, key: unknown, paths: unknown): EditedFile[] => {
    if (typeof key !== 'string' || !Array.isArray(paths)) return []
    const spelled = paths.filter((one): one is string => typeof one === 'string')
    const root = sessions.rootOf(key)
    return root === null ? [] : editedAt(root, spelled)
  })
  // One of those files as the disk holds it now (RG245), on the same terms: the root is the
  // session's, a path outside it is refused before anything is asked, and so is a key this
  // process never issued. What crosses is the text or a code, never an error's English.
  ipcMain.handle(
    BRIDGE_CHANNELS.fileText,
    (_event, key: unknown, path: unknown): Promise<FileText> => {
      const spelled = typeof path === 'string' ? path : ''
      const root = typeof key === 'string' ? sessions.rootOf(key) : null
      if (root === null) {
        return Promise.resolve({ kind: 'refused', path: spelled, code: 'no-session', fields: {} })
      }
      return fileText(root, spelled)
    },
  )

  // The gate verdicts on record (RG152): a read of the ledger the carrier dates, never a run.
  ipcMain.handle(BRIDGE_CHANNELS.gates, () => carrier.gates())
  ipcMain.handle(BRIDGE_CHANNELS.sessions, () => sessions.list())
  ipcMain.handle(BRIDGE_CHANNELS.stopSession, (_event, key: unknown): void => {
    if (typeof key === 'string') sessions.stop(key)
  })

  return {
    // The sessions first: each one stands in its project, and the engines it reads through
    // are the carrier's.
    close: async () => {
      await sessions.close()
      await carrier.close()
    },
  }
}
