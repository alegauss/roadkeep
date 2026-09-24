import { readFileSync } from 'node:fs'
import path from 'node:path'

import {
  asRecord,
  GLOSS_SHAPE,
  LOCALE_TAGS,
  NOTHING_GLOSSED,
  NOTHING_WALKED,
  readGloss,
  readWalkthrough,
  withGloss,
  withWalkthrough,
  type BriefPayload,
} from '@rk/core'

import { saveGlosses } from './glosses-file'
import { CAPTURED_GLOSS } from './scripted-agent'
import { saveWalkthroughs } from './walkthroughs-file'

/**
 * The answers a machine has kept, written before a shots run starts (RG300).
 *
 * Two dialogs draw an answer somebody asked for, and neither could be photographed in the state
 * that matters: a fresh run answers a gloss that is neither stale nor written under an earlier
 * shape, and the walkthrough dialog was never opened at all. What was missing is a machine whose
 * store holds something — which is what RG287 and RG292 keep anyway, so this writes it.
 *
 * **The prose is a real answer's.** Both come out of the captured runs this repository already
 * keeps, read out of the same streams the replays use, so a picture shows what Claude Code wrote
 * and not what a fixture author typed.
 *
 * **Per language.** A kept answer is kept per tag, and the run photographs every locale — so a
 * language with nothing kept would ask the scripted agent instead and draw the fresh state.
 */

const CAPTURED_WALKTHROUGH = path.resolve(
  import.meta.dirname,
  '..',
  'src',
  'captured',
  'walkthrough-steps.jsonl',
)

/** The `structured_output` a captured run ended with, which is the answer it gave. */
function structuredOf(capture: string): unknown {
  for (const line of readFileSync(capture, 'utf8').trim().split('\n').toReversed()) {
    const message = asRecord(JSON.parse(line))
    if (message?.['type'] === 'result' && message['structured_output'] !== undefined) {
      return message['structured_output']
    }
  }
  throw new Error(`${capture} ends in no structured answer, so there is nothing to keep`)
}

/**
 * The line a kept gloss was written about, which is deliberately not the line it is drawn beside.
 *
 * `glossStands` compares six fields, and a picture of the stale notice needs them to differ. The
 * symptom is enough and is the field a reader would notice, so it is the one that moves.
 */
const MOVED_SINCE = {
  symptom: 'the line said something else when this was written',
  why: 'It has been restated since.',
  design: '',
  deps: [],
  binds: [],
  doneWhen: [],
}

/**
 * Keep one gloss and one walkthrough, so both dialogs open on an answer (RG300).
 *
 * The gloss is kept **old both ways**: its line has moved and its shape predates this build, so
 * the picture shows the two notices stacked where they are stacked — which is the layout question
 * a picture is the only way to ask.
 *
 * @param line the brief of the task the gloss is drawn beside — the capture is about another
 *   project's line, so every entry it keyed by an id drops and the prose is what stays
 * @param entry the shipped entry the walkthrough is about
 * @param commit the commit that shipped it, so the walkthrough reads as standing
 */
export function keepAnswers(
  userData: string,
  root: string,
  line: BriefPayload,
  entry: string,
  commit: string,
): void {
  const gloss = readGloss(structuredOf(CAPTURED_GLOSS), line)
  const walkthrough = readWalkthrough(structuredOf(CAPTURED_WALKTHROUGH))

  let glosses = NOTHING_GLOSSED
  let walked = NOTHING_WALKED
  for (const tag of LOCALE_TAGS) {
    glosses = withGloss(glosses, {
      root,
      id: line.id,
      tag,
      gloss,
      version: '2.1.278',
      model: 'claude-opus-5',
      answered: '2026-09-21T10:00:00.000Z',
      // Older than this build's, so the answer reads as one the schema has outgrown (RG290).
      shape: GLOSS_SHAPE - 1,
      line: MOVED_SINCE,
    })
    walked = withWalkthrough(walked, {
      root,
      id: entry,
      tag,
      walkthrough,
      version: '2.1.278',
      model: 'claude-opus-5',
      answered: '2026-09-21T10:00:00.000Z',
      commit,
    })
  }
  saveGlosses(userData, glosses)
  saveWalkthroughs(userData, walked)
}
