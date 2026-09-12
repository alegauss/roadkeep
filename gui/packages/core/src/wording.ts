/**
 * Every string this app says in its own voice, in one place.
 *
 * English is the base and **English is the type**: `MessageKey` is this object's own keys,
 * so a screen cannot ask for a string nobody wrote, and a key no screen asks for shows up
 * as dead the way an unused export does.
 *
 * A second locale is a `Partial` of the same shape beside it. That is deliberate — a
 * half-translated locale is the normal state of a translation, not a broken one — and the
 * fallback is **per key**, so a missing entry shows the English sentence rather than the
 * identifier. A locale file is never a reason for a screen to show `portfolio.footnote`.
 *
 * **Two things are never in here.** What a payload printed is the project's own prose, in
 * whatever language its author wrote it, and translating it would be this app rewriting
 * somebody's backlog. A refusal is the engine's words, quoted. What is translated is this
 * app's own voice and nothing else.
 *
 * The word *catalogue* is already spoken for by the project record in `catalogue.ts`, which
 * is why this file is not called that. Two catalogues in one app is one too many names.
 */

import type { NarrowedCase } from './backlog'
import type { WithheldCode } from './bridge'
import type { Unreadable, UnreadableCode } from './limits'
import type { Lost, Theme } from './settings'
import { keysOf } from './reading'

/** Named holes, filled by name. Positional would be a promise about word order. */
export type Fill = Readonly<Record<string, string | number>>

/**
 * The base wording. Values may carry `{name}` holes; nothing else is special.
 *
 * Keys read from the general to the particular, so one screen's strings sort together and
 * an unused one is visible.
 */
export const EN = {
  'app.name': 'roadkeep',

  'transport.absent': 'no bridge - running as a plain browser page',

  'portfolio.kicker': 'Portfolio',
  'portfolio.title': '{count} projects on this machine',
  'portfolio.title.unknown': 'Projects on this machine',
  'portfolio.tally': '{read} read · {pending} still reading · {unreadable} unreadable',
  'portfolio.progress': '{stage}: {done} of {total}',
  'portfolio.stage.counting': 'counting each backlog',
  'portfolio.stage.next': 'asking for each next line',
  'portfolio.asking': 'Looking under the roots the settings name.',
  'portfolio.failed': 'The bridge did not say which projects there are: {reason}',
  'portfolio.none': 'No project was found under the roots the settings name.',
  'portfolio.none.hint':
    'A folder holding a roadkeep.toml under one of those roots is listed here the next time the window asks.',
  'portfolio.filter.all': 'All {count}',
  'portfolio.filter.drifted': 'Gate drifted {count}',
  'portfolio.filter.disagrees': 'Engine disagrees {count}',
  'portfolio.filter.unreadable': 'Unreadable {count}',
  'portfolio.filter.label': 'Narrow the list',
  'portfolio.order': "order: the record's",
  'portfolio.column.project': 'Project',
  'portfolio.column.backlog': 'Backlog',
  'portfolio.column.next': 'Next ready line',
  'portfolio.column.gate': 'Gate',
  'portfolio.column.engine': 'Engine',
  'portfolio.worktree': 'worktree',
  'portfolio.pending': 'still reading',
  'portfolio.open': '{count} open',
  'portfolio.startable': '{startable} startable · {waiting} waiting',
  'portfolio.uncounted': '{count} not counted',
  'portfolio.tier': 'tier: {tier}',
  'portfolio.next.none': 'nothing ready · {blocked} blocked',
  'portfolio.next.missing': 'the next line did not arrive',
  'portfolio.gate.unknown': 'unknown',
  'portfolio.gate.clean': 'clean',
  'portfolio.gate.drifted': 'drifted',
  'portfolio.gate.never': 'never run here',
  'portfolio.gate.findings': '{count} findings',
  'portfolio.gate.stale': 'stale',
  'portfolio.engine.modified': 'working tree',
  'portfolio.unreadable': 'unreadable',
  'portfolio.tried': 'what was tried',
  'portfolio.kept': 'still on the list',
  'portfolio.footnote':
    'Every number on this screen is one a verb printed. Nothing is summed across projects.',

  'project.back': 'Portfolio',
  'project.counts':
    '{open} open · {startable} startable · {waiting} waiting on a requirement · {uncounted} uncounted',
  'project.opening': 'Opening the project.',
  'project.refused': 'This project did not open: {reason}',
  'project.roles': 'Governed files',
  'project.blocks': 'Blocks',
  'project.block.finished': 'finished',
  'project.filter.marker': 'marker',
  'project.filter.requirement': 'requirement',
  'project.filter.note': 'readiness is what deps answered for each line, never worked out here',
  'project.listing': 'Reading the lines.',
  'project.none': 'No line answers this narrowing.',
  'project.design.written': 'design written · §{ref}',
  'project.design.none': 'no design yet',
  'project.deps.none': 'no deps',
  'project.readiness.asking': 'asking',
  'project.waiting': 'waiting on {ids}',
  'project.cycle': 'in a cycle with {ids}',
  'project.unheld': 'marked, unheld',
  'project.unheld.why': 'the marker says started; the claim registry names nobody',
  'project.held': 'held by {by}',
  'project.tab.unread': 'This file is governed and this window does not read it yet.',
  'project.changelog.none': 'Nothing has shipped yet.',
  'project.undone': 'undone by {by}',
  'project.decisions.none': 'No decision is recorded yet.',
  'project.decision.reasoning': 'the reasoning',
  'project.decision.asking': 'Reading the section.',
  'project.decision.bare': 'This decision keeps no section of its own.',
  'project.deferred.none': 'Nothing is set aside.',
  'project.deferred.order': 'In the order the engine gave: {order}.',
  'project.deferred.since': 'set aside {count} commits ago',
  'project.improvements.none': 'No open line has a design written yet.',
  'project.read.failed': 'This file did not answer: {reason}',
  'project.line.open': 'Open',
  'project.line.open.named': 'Open {id}',

  'task.opening': 'Opening the line.',
  'task.refused': 'This line did not open: {reason}',
  'task.block': 'Block {block}',
  'task.shipped': 'shipped, and in the ledger',
  'task.copy': 'Copy the brief',
  'task.copied': 'Copied',
  'task.copy.failed': 'The brief was not copied: {reason}',
  'task.design.where': '§{anchor} · {where}',
  'task.design.budget': '{taken} of {limit} {unit}',
  'task.design.over': '{taken} of {limit} {unit}, {over} over',
  'task.design.count': '{words} words',
  'task.design.face': 'shown exactly as the file wraps it · no Markdown parsed in this app',
  'task.design.none': 'No design is written for this line.',
  'task.readiness': "{readiness} — the engine's word, not this app's",
  'task.requires': 'needs {what}',
  'task.dep.open': 'Open {id}',
  'task.unblocks': 'shipping this unblocks {count} of {of} open lines',
  'task.underway': 'Underway',
  'task.underway.working': '{by} is working it, since {since}',
  'task.underway.held': 'held by {by}, since {since}',
  'task.underway.started': 'started, and no claim on it is still live',
  'task.underway.idle': 'not started, and the claim registry names nobody',
  'task.underway.agree': 'the marker and the registry agree',
  'task.underway.disagree': 'the marker and the registry disagree',
  'task.binds': 'What binds this line · block {block}',
  'task.criteria.none': 'This block declares no criterion.',
  'task.criteria.own': 'What this line must check',
  'task.criteria.folded': 'from {id}',
  'task.criteria.elided': '{count} more criteria not listed',
  'task.quoted': 'Non-goals this design quotes',
  'task.bounds': 'Non-goals',
  'task.bounds.elided': '{count} more not listed',
  'task.paused': 'This line is set aside.',
  'task.paused.back': '{verb} {id} brings it back',
  'task.unfiled': 'Nothing in this project carries {id}.',
  'task.unknown': 'Not found, in a read that did not see every line.',
  'task.handOver': 'Hand to Claude Code',
  'task.handing': 'Taking the line and starting the session.',
  'task.held.named': 'Held by {by}, since {since}, so no second session is offered.',
  'task.handOver.unready': 'The engine calls this line {readiness}, so it was not taken.',
  'task.handOver.refused': 'The line was not taken: {reason}',
  'task.handOver.unavailable':
    'No Claude Code answered on this machine, so the line was not taken. Tried: {tried}',
  'task.handOver.withheld': 'The line was not handed over: {reason}',
  'task.session.open': 'Open the session',

  'session.opening': 'Finding the session.',
  'session.missing': 'This window holds no session by that name.',
  'session.stop': 'Stop the session',
  'session.state.starting': 'starting',
  'session.state.running': 'running',
  'session.state.done': 'done',
  'session.state.failed': 'failed',
  'session.state.cancelled': 'stopped',
  'session.state.unavailable': 'no Claude Code',
  'session.claim': 'claim taken: {from} → {to}',
  'session.handed': 'Handed over',
  'session.handed.design': 'the design, {words} words',
  'session.handed.nodesign': 'no design written',
  'session.handed.deps': '{count} deps',
  'session.handed.criteria': '{count} criteria',
  'session.handed.bounds': '{count} non-goals',
  'session.handed.agent': 'started with {command}, Claude Code {version}',
  'session.stream': 'The stream',
  'session.stream.empty': 'Nothing has been written yet.',
  'session.act.roadkeep': 'roadkeep call',
  'session.act.governed': 'touches {files}',
  'session.act.failed': 'failed',
  'session.act.raw': 'the raw line',
  'session.moved': 'What moved',
  'session.moved.none': 'Nothing about the line has moved yet.',
  'session.change.marker': 'marker {from} → {to}',
  'session.change.design.written': 'design written',
  'session.change.design.deleted': 'design deleted',
  'session.change.shipped': 'shipped, and in the ledger',
  'session.change.symptom': 'symptom restated',
  'session.change.why': 'why amended',
  'session.change.depsAdded': 'deps added: {ids}',
  'session.change.depsDropped': 'deps dropped: {ids}',
  'session.change.left': 'the line left: {said}',
  'session.result': 'its last word: {result}',
  'session.files': 'The governed files',
  'session.file.never': 'not written yet',
  'session.claims': 'Claims held elsewhere',
  'session.claims.none': 'No other line of this project is claimed.',
  'session.claim.since': '{state}, {since}',

  'sessions.kicker': 'Sessions',
  'sessions.title': '{count} sessions this window started',
  'sessions.title.none': 'Sessions this window started',
  'sessions.none': 'No session has been started from this window.',
  'sessions.none.hint':
    'Hand to Claude Code on a line starts one, and it is listed here while this window runs.',
  'sessions.column.line': 'Line',
  'sessions.column.project': 'Project',
  'sessions.column.state': 'State',
  'sessions.open': 'Open {id}',
  'sessions.footnote':
    'Sessions live with this window: what is listed here is what this process started and still holds.',

  'filing.title': 'File a line',
  'filing.about': 'One line and the design it points at, in one command.',
  'filing.id': 'this would be {id}',
  'filing.block': 'Block',
  'filing.marker': 'Marker',
  'filing.deps': 'Deps',
  'filing.deps.add': 'Add a dep',
  'filing.deps.none': 'no deps',
  'filing.deps.drop': 'Drop {id}',
  'filing.symptom': 'Symptom',
  'filing.symptom.about': 'What does not work, never a fix name.',
  'filing.why': 'Why',
  'filing.why.about': 'One sentence, and it ends in a stop.',
  'filing.section': 'The design',
  'filing.section.title': 'Its heading',
  'filing.section.body': 'The prose',
  'filing.counter': '{left} left of {allowed}',
  'filing.counter.aim': '{left} left of {allowed}, {room} to the aim',
  'filing.counter.over': '{taken} of {allowed}, {over} over',
  'filing.counter.line': 'what the rendered line leaves',
  'filing.structure': '{structure} of {max} is structure, leaving {prose} for prose',
  'filing.words': '{taken} of {limit} {unit}',
  'filing.pricing': 'Asking what this line leaves.',
  'filing.near': 'What block {block} already has',
  'filing.near.none': 'Nothing in this block is near it yet.',
  'filing.near.open': 'open',
  'filing.near.shipped': 'shipped',
  'filing.near.order': 'Nearest first. There is no score: read them and judge.',
  'filing.bounds': 'What binds a line here',
  'filing.bounds.none': 'This project declares no non-goal.',
  'filing.command': 'The command, before it runs',
  'filing.copy': 'Copy the command',
  'filing.copied': 'Copied',
  'filing.save': 'File it',
  'filing.saving': 'Filing the line.',
  'filing.wrote': 'Filed as {id}, and this screen follows it.',
  'filing.refused': 'The engine refused it: {said}',
  'filing.failed': 'The command did not run: {reason}',
  'filing.unreadable': 'The answer could not be read: {reason}',
  'filing.doors': 'What the engine offers instead',

  'door.writes': 'writes a governed file',
  'door.take': 'Take it',
  'door.blank': 'what goes where the engine left a blank',

  'gate.title': 'The gate',
  'gate.about': 'What the governed files say about themselves, and what closes each finding.',
  'gate.run': 'Run the gate',
  'gate.running': 'Running the gate.',
  'gate.failed': 'The gate did not run: {reason}',
  'gate.unreadable': 'The gate answered something this build could not read: {reason}',
  'gate.held.clean': 'Clean when it last ran.',
  'gate.held.drifted': '{problems} findings when it last ran.',
  'gate.taken': 'Last run {taken}.',
  'gate.never': 'Not run in this window yet.',
  'gate.stale': 'The files moved since, so this is what they said before.',
  'gate.clean': 'Clean: {lines} lines and {sections} sections, and nothing to answer for.',
  'gate.problems': '{problems} findings over {lines} lines and {sections} sections',
  'gate.notes': 'Said without failing for it',
  'gate.doors': 'What closes it',
  'gate.doors.none': 'Nothing here closes this one on its own.',
  'gate.decision': 'Settle this first: {decision}',
  'gate.awaits': 'Waits on {awaits}',
  'gate.sequence': 'In this order, not a choice.',
  'gate.checked': 'Read: {checked}',

  'backlog.over.narrows':
    '{count} lines in {file} were not listed: this read is {characters} characters against the {limit} this project declares, so ask for {narrows}.',
  'backlog.over.whole':
    '{count} lines in {file} were not listed: this read is {characters} characters against the {limit} this project declares, and no block is small enough to ask for on its own.',
  'backlog.refused.one':
    'One line in {file} carries a marker the grammar did not accept, so nothing counts or picks it.',
  'backlog.refused.many':
    '{count} lines in {file} carry a marker the grammar did not accept, so nothing counts or picks them.',
  'backlog.refused.reasons': 'What the gate said: {reasons}',

  'unreadable.not-json': '`{command}` answered with something that is not JSON.',
  'unreadable.shape':
    'The answer was not a shape this build reads: {path} should have been {expected}, and was {got}.',
  'unreadable.declares':
    '`{verb}` was refused, so this project declares nothing this app can read.',
  'unreadable.behind':
    'The copy answering here is roadkeep {version}, which has no `{verb}`. Update that checkout.',
  'unreadable.refused': '`{verb}` was refused.',
  'unreadable.ungoverned':
    'The engine answering here says no roadkeep project governs this folder.',
  'unreadable.nothing-offered':
    'Nothing was offered as an engine for this project, so nothing was asked.',
  'unreadable.none-answered':
    'No candidate answered `engines --json`, so which roadkeep governs this project is unknown.',
  'unreadable.withheld': 'This folder is not one the scan of your roots found.',

  'withheld.not-carried': 'That is not a request this app carries to the engine.',
  'withheld.no-such-door':
    'No door by that name is on offer for this project. Read again and take one the answer carries.',
  'withheld.not-the-words': 'A door takes one word for each blank it has, and that was not it.',
  'withheld.not-catalogued': '`{root}` is not a project the scan of your roots found.',
  'withheld.not-open': '`{root}` did not open, so the request never ran: {why}',

  'roots.label': 'Roots',
  'roots.add': 'Add a root',
  'roots.rescan': 'Rescan roots',
  'roots.choose': 'Choose a folder to look under',
  'roots.depth': '{depth} levels deep',
  'roots.missing': 'missing',
  'roots.remove': 'Stop looking under {path}',
  'roots.deeper': 'Look one level deeper under {path}',
  'roots.shallower': 'Look one level less deep under {path}',
  'roots.none': 'No root is named yet, so nothing is walked.',
  'roots.none.hint': 'Add a root to name a folder this window may look under.',
  'roots.unsaved': 'The roots could not be saved: {reason}',

  'settings.reset': 'Some settings could not be read, so they are back to their defaults.',
  'settings.unsaved': 'That choice could not be saved, so the next launch will not have it.',

  'settings.lost.unparsable': '{file} is not readable as JSON, so it is left alone',
  'settings.lost.file':
    'the settings file is not an object, so every setting is back to its default',
  'settings.lost.unversioned':
    'the settings file names no version, so it is read as this build writes them',
  'settings.lost.version':
    'the settings file is version {found} and this build reads {reads}, so the file is left alone',
  'settings.lost.roots': 'the roots were not a list, so none were read',
  'settings.lost.dropped': '{count} root(s) could not be read and were dropped',
  'settings.lost.skip': 'the skip list was not a list of names, so the default one is used',
  'settings.lost.width': 'the pool width was not a whole number, so it is back to {width}',
  'settings.lost.theme': 'the theme was not one this build knows, so it is back to {theme}',
  'settings.lost.locale': 'the locale was not a string, so the desktop decides',

  'shell.home': 'Home',
  'shell.palette': 'Find a line in every backlog',
  'shell.shortcuts': 'Keyboard shortcuts',
  'shell.notices': 'Notifications',

  'menu.help': 'Help',
  'update.check': 'Check for updates…',
  'update.title': 'Updates',
  'update.newer': 'You are on {current}. The newest published is {latest}.',
  'update.current': 'You are on {current}, which is the newest published.',
  'update.ahead': 'You are on {current}, which is ahead of the newest published, {latest}.',
  'update.none': 'You are on {current}. No release has been published yet.',
  'update.failed': 'You are on {current}. The check did not reach an answer: {reason}',
  'update.failed.status': 'GitHub answered {status}.',
  'update.failed.not-json': 'GitHub answered something that is not JSON.',
  'update.failed.missing': 'The answer had no {path}.',
  'update.failed.version': '{version} is not a version this can compare.',
  'update.open': 'Open the release page',
  'update.close': 'Close',

  'ground.system': 'ground: following the desktop',
  'ground.light': 'ground: light',
  'ground.dark': 'ground: dark',
  'ground.action': 'Change the ground',
} as const

/** What a screen may ask for. Anything else is a string somebody typed into a component. */
export type MessageKey = keyof typeof EN

/**
 * What the ground control says it is set to.
 *
 * `system` has wording of its own rather than borrowing whichever ground it resolved to:
 * *following the desktop* and *light* look identical on a machine set to light, and the
 * difference is the whole reason `system` is a setting.
 */
export const THEME_TEXT: Readonly<Record<Theme, MessageKey>> = {
  system: 'ground.system',
  light: 'ground.light',
  dark: 'ground.dark',
}

/**
 * What a settings file lost, said in this app's own voice (RG123).
 *
 * The same arrangement as the theme and for a sharper reason: these sentences used to be
 * composed where the file is read, which is `core` for nine of them and `shell` for the
 * tenth, and neither has a locale. RG115 draws them under a translated frame, so a window
 * in Portuguese said the frame in Portuguese and the detail in English.
 *
 * Spelled out rather than built from the code, so a loss added without a sentence fails to
 * compile — and the values carry the holes the reader fills, which is why the reader hands
 * back fields and not prose.
 */
export const RESET_TEXT: Readonly<Record<Lost, MessageKey>> = {
  unparsable: 'settings.lost.unparsable',
  file: 'settings.lost.file',
  unversioned: 'settings.lost.unversioned',
  version: 'settings.lost.version',
  roots: 'settings.lost.roots',
  dropped: 'settings.lost.dropped',
  skip: 'settings.lost.skip',
  width: 'settings.lost.width',
  theme: 'settings.lost.theme',
  locale: 'settings.lost.locale',
}

/**
 * The sentence for each way a listing is narrower than its file (RG172). Same arrangement
 * as the two tables beside it: a case added without a sentence fails to compile.
 */
export const NARROWED_TEXT: Readonly<Record<NarrowedCase, MessageKey>> = {
  'over-narrows': 'backlog.over.narrows',
  'over-whole': 'backlog.over.whole',
  'refused-one': 'backlog.refused.one',
  'refused-many': 'backlog.refused.many',
}

/**
 * The sentence for each way this app could not read an answer (RG168).
 *
 * The same arrangement `RESET_TEXT` uses and for the same reason: a code added without a
 * sentence fails to compile, and the values the code carries are the holes this fills. The
 * empty code has no entry — it means the prose belongs to the engine, and a lookup is the
 * wrong thing to do with somebody else's words.
 */
export const UNREADABLE_TEXT: Readonly<Record<Exclude<UnreadableCode, ''>, MessageKey>> = {
  'not-json': 'unreadable.not-json',
  shape: 'unreadable.shape',
  declares: 'unreadable.declares',
  behind: 'unreadable.behind',
  refused: 'unreadable.refused',
  ungoverned: 'unreadable.ungoverned',
  'nothing-offered': 'unreadable.nothing-offered',
  'none-answered': 'unreadable.none-answered',
  withheld: 'unreadable.withheld',
}

/**
 * Why a project could not be read, in the window's language where the sentence is this
 * app's and in the engine's own words where it is not (RG168).
 *
 * Nothing is composed here: a code picks a key and `say` fills its holes, so a language this
 * build ships says it in that language and one it does not falls back the way every other
 * sentence does.
 */
export function reasonOf(unreadable: Unreadable, say: Translate): string {
  return unreadable.code === ''
    ? unreadable.message
    : say(UNREADABLE_TEXT[unreadable.code], unreadable.fields)
}

/**
 * The sentence for each way the carrier would not run a request (RG192).
 *
 * `UNREADABLE_TEXT`'s arrangement and for its reason: a code added without a sentence fails
 * to compile. The empty code has no entry here either — it is the prose of a transport, or
 * this app's own report of a command line it composed, and neither is looked up.
 */
export const WITHHELD_TEXT: Readonly<Record<Exclude<WithheldCode, ''>, MessageKey>> = {
  'not-carried': 'withheld.not-carried',
  'no-such-door': 'withheld.no-such-door',
  'not-the-words': 'withheld.not-the-words',
  'not-catalogued': 'withheld.not-catalogued',
  'not-open': 'withheld.not-open',
}

/** What a refusal carries: the sentence for a log, and the code a screen says instead. */
export interface Withholding {
  readonly message: string
  readonly code: WithheldCode
  readonly fields: Readonly<Record<string, string>>
}

/**
 * Why a request did not run, in the window's language where the sentence is this app's and
 * in the words they were written in where it is not (RG192).
 *
 * `reasonOf`'s shape, because it is the same question asked of the other half of the bridge:
 * a code picks a key, `say` fills its holes, and an empty code is prose nobody translates.
 */
export function refusalOf(withholding: Withholding, say: Translate): string {
  return withholding.code === ''
    ? withholding.message
    : say(WITHHELD_TEXT[withholding.code], withholding.fields)
}

/** A sentence that is already what a person should read, as a refusal the screens can take. */
export function saidPlainly(message: string): Withholding {
  return { message, code: '', fields: {} }
}

/**
 * A time, written in the language the window is speaking (RG177).
 *
 * Every time this app draws crosses as ISO-8601 — a fact, not a rendering — and this is the
 * one place that turns one into a string a person reads. The tag is the window's, resolved at
 * launch by the side that can ask the desktop, so a window set to one language on a machine
 * set to another does not write its sentences in the first and its times in the second.
 *
 * **A stamp this cannot read is answered as it arrived.** A blank where a time should be is
 * worse than an unfamiliar one, and the string is still the filesystem's own answer.
 *
 * `No dates, estimates, velocity or burndown` bounds this and does not forbid it: what that
 * refuses is a schedule this app would have to invent — a date roadkeep does not store, a
 * rate, a line drawn through time. A file's last change is read and never computed.
 */
export function timeIn(stamp: string, locale: string): string {
  const at = new Date(stamp)
  if (Number.isNaN(at.getTime())) return stamp
  // A tag this build does not ship, or a runtime that will not take it, is not worth
  // failing a screen over: the time is the point and the desktop's own format will do.
  try {
    return at.toLocaleString(locale === '' ? undefined : locale)
  } catch {
    return at.toLocaleString()
  }
}

/** A translation. Partial because a translation in progress is still worth shipping. */
export type Wording = Partial<Readonly<Record<MessageKey, string>>>

/** The base, widened: every key present, which is what makes the fallback total. */
export const BASE: Readonly<Record<MessageKey, string>> = EN

/** The tag the base is written in. */
export const BASE_LOCALE = 'en'

/** Every key there is, in the order they were written. */
export function keys(): readonly MessageKey[] {
  return keysOf(BASE)
}

/**
 * Fill a value's named holes.
 *
 * A hole nobody filled is left as it was written rather than blanked: a visible `{count}`
 * is a defect somebody reports, and a gap where a number should be is one nobody notices.
 */
export function fill(value: string, values: Fill = {}): string {
  return value.replace(/\{(\w+)\}/g, (whole, name: string) => {
    const given = values[name]
    return given === undefined ? whole : String(given)
  })
}

/** What a screen calls to get a string. */
export type Translate = (key: MessageKey, values?: Fill) => string

/**
 * Build the lookup for one locale.
 *
 * @param over the translation, covering any part of the base. Absent keys fall through to
 *   English one at a time, which is what makes a partial translation usable.
 */
export function translator(over: Wording = {}): Translate {
  return (key, values) => fill(over[key] ?? BASE[key], values)
}

/**
 * Choose which locale answers, from what the settings asked for.
 *
 * A tag is tried whole and then by its language — `pt-BR` before `pt` — because a
 * translation is usually written for the language and specialised later, if ever. An empty
 * request means the desktop's own tag, which the caller passes in: nothing here reads an
 * environment, because `core` has none to read.
 */
export function localeFor(asked: string, available: readonly string[]): string {
  const wanted = asked.trim().toLowerCase()
  if (wanted === '') return BASE_LOCALE

  const language = wanted.split('-')[0] ?? wanted
  const found =
    available.find((one) => one.toLowerCase() === wanted) ??
    available.find((one) => one.toLowerCase() === language) ??
    available.find((one) => (one.toLowerCase().split('-')[0] ?? '') === language)

  return found ?? BASE_LOCALE
}

/**
 * Which keys a translation has not covered yet, in the base's own order.
 *
 * A report and never a refusal: a locale is allowed to be incomplete, and what the person
 * translating it needs is the list of what is left.
 */
export function untranslated(over: Wording): readonly MessageKey[] {
  return keys().filter((key) => over[key] === undefined)
}

/** Keys a translation carries that the base no longer has — a string that outlived its screen. */
export function stale(over: Wording): readonly string[] {
  return Object.keys(over).filter((key) => !(key in BASE))
}

/**
 * The other half of the wording, and the same two questions asked of it (RG125).
 *
 * This app's strings reach the screen two ways: through the catalogue above, and through an
 * i18next bundle the design system's own components resolve — the nav labels, and the name
 * the language menu gives itself. The second half is nested rather than flat, is written
 * once per language rather than as a `Partial` of a base, and had nothing comparing the
 * copies at all: a key added to `en` and missed in `pt` drew English inside a Portuguese
 * window, and RG51's run could not see it, wrapping the base locale being the language it
 * renders in.
 *
 * **The rules are the catalogue's, not new ones.** A path the base names and a translation
 * does not is `untranslated`; a path a translation names and the base no longer does is
 * `stale`; and a value identical in both is the case `app.name` already settles — a name is
 * the same word in either language, and everything else identical is a translation nobody
 * wrote. All three come off one walk, because the answer wanted is all three at once.
 *
 * Here rather than beside the object it is asked about, for the reason every rule in this
 * package is: comparing two trees of strings needs no DOM and no i18next.
 */

/** A bundle as i18next takes one: a tree whose leaves are strings. */
export interface Bundle {
  readonly [key: string]: string | Bundle
}

export interface BundleGaps {
  /** Paths the base names and this translation does not. */
  readonly untranslated: readonly string[]
  /** Paths this translation names that the base does not. */
  readonly stale: readonly string[]
  /** Paths both name with the same string. A name, or a translation nobody wrote. */
  readonly identical: readonly string[]
}

/** Every path to a string in a bundle, dotted, in the order they were written. */
export function bundlePaths(bundle: Bundle, under = ''): readonly string[] {
  return Object.entries(bundle).flatMap(([key, value]) => {
    const path = under === '' ? key : `${under}.${key}`
    return typeof value === 'string' ? [path] : bundlePaths(value, path)
  })
}

/** What a bundle says at a dotted path, or `undefined` where it says nothing there. */
export function bundleSays(bundle: Bundle, path: string): string | undefined {
  let at: string | Bundle | undefined = bundle
  for (const step of path.split('.')) {
    if (at === undefined || typeof at === 'string') return undefined
    at = at[step]
  }
  return typeof at === 'string' ? at : undefined
}

/** One translation against the base it is a translation of. A report, never a refusal. */
export function bundleGaps(base: Bundle, over: Bundle): BundleGaps {
  const mine = bundlePaths(base)
  const theirs = bundlePaths(over)

  return {
    untranslated: mine.filter((path) => bundleSays(over, path) === undefined),
    stale: theirs.filter((path) => bundleSays(base, path) === undefined),
    identical: mine.filter((path) => bundleSays(over, path) === bundleSays(base, path)),
  }
}

/**
 * A locale nobody speaks, which is what proves the screens read from here.
 *
 * Every value is wrapped and every hole is kept, so rendering under it leaves anything
 * unwrapped on screen visible as a string written into a component instead of into this
 * file. A test sees that on the run after somebody types it, rather than on the day a
 * second locale is added.
 */
export const PSEUDO_OPEN = '⟦'
export const PSEUDO_CLOSE = '⟧'
export const PSEUDO_LOCALE = 'zz'

export function pseudo(): Wording {
  const out: Record<string, string> = {}
  for (const key of keys()) out[key] = `${PSEUDO_OPEN}${BASE[key]}${PSEUDO_CLOSE}`
  return out
}

/** Whether a string on screen came through the pseudo-locale. */
export function isPseudo(text: string): boolean {
  return text.includes(PSEUDO_OPEN) && text.includes(PSEUDO_CLOSE)
}
