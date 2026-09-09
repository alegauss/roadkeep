import type { GateHealth } from './gate'
import type { RecordedProject } from './catalogue'
import type { CallOptions } from './client'
import type { OpenProject } from './opening'
import { fillRow, readRow, unreadableRow, type ProjectRow } from './portfolio'
import type { Parsed } from './reading'
import type { Answer } from './refusals'
import { saidBy, type Unreadable } from './limits'
import { EngineCallFailed } from './transport'

/**
 * Filling a row out of a project that is already open, in two moments rather than four.
 *
 * A filled row wants counts, the next line, the gate and the engine, and drawing one used
 * to be four interpreter starts — sixty-eight over seventeen projects, and most of what a
 * cold start costs. Three things take that apart and they are an order rather than a
 * choice.
 *
 * **The engine read is already done.** Resolution answered it when the project opened
 * (RG103), so asking `engines` per row was one call this app made twice for one answer.
 * That is a quarter of the cost removed by not spending it.
 *
 * **Not every read is needed to draw a row.** Counts and the engine are what a list is
 * scanned for — how big, whose roadkeep, is it modified — and the next line is what
 * somebody reads once they have found the project they came for. So `glanceRow` is one
 * call and `withNext` is the second, and a screen can draw seventeen rows after seventeen
 * calls instead of sixty-eight.
 *
 * **The gate is not a read at all.** Its verdict comes off the ledger, because running
 * `lint` seventeen times to draw a list is the cost this whole arrangement avoids.
 *
 * What would remove the problem rather than manage it is one verb answering all four, and
 * that is roadkeep's to decide and not this app's to invent.
 */

/**
 * A read that cannot take a screen down with it.
 *
 * `client.call` raises where the call never happened — unspawnable, past its ceiling,
 * cancelled — because that is the transport failing and not an answer (RG99). A list over
 * twenty projects has to draw nineteen when one of them hangs, so the raise ends here and
 * becomes the state the row is in. RG99 is about giving every caller one door instead of
 * this; until it does, this is the door a row uses.
 */
async function ask<T>(
  call: () => Promise<Parsed<Answer<T>>>,
  verb: string,
): Promise<{ ok: true; value: T } | { ok: false; why: Unreadable }> {
  let answer: Parsed<Answer<T>>
  try {
    answer = await call()
  } catch (cause) {
    if (!(cause instanceof EngineCallFailed)) throw cause
    return {
      ok: false,
      why: {
        reason: cause.reason,
        message: cause.message,
        elapsedMs: cause.durationMs,
        argv: [verb],
        said: '',
      },
    }
  }

  const failed = whyNot(verb, answer)
  if (failed !== null) return { ok: false, why: failed }
  if (!answer.ok || answer.value.kind === 'refused') return { ok: false, why: never(verb) }
  return { ok: true, value: answer.value.value }
}

/** The counts and the engine: enough to draw a row somebody is scanning past. */
export async function glanceRow(
  recorded: RecordedProject,
  project: OpenProject,
  options: CallOptions = {},
): Promise<ProjectRow> {
  const stats = await ask(() => project.client.call(project.root, 'stats', {}, options), 'stats')
  if (!stats.ok) return unreadableRow(recorded, stats.why)

  return readRow(recorded, {
    stats: stats.value,
    // Never asked for: the payload resolution already read is the payload this needs.
    engines: project.engine.payload,
  })
}

/**
 * The same row with the next line on it, and the gate's last verdict beside it.
 *
 * Takes the row rather than rebuilding it, so what a screen already drew is what it keeps:
 * a second pass that recomputed the counts would make a list flicker for no new fact.
 */
export async function withNext(
  row: ProjectRow,
  project: OpenProject,
  gate: GateHealth | null = null,
  options: CallOptions = {},
): Promise<ProjectRow> {
  const pick = await ask(() => project.client.call(project.root, 'pick', {}, options), 'pick')
  // A row that could not learn its next line is still a row: the counts are true, and
  // drawing it as unreadable would throw away what the first pass already knew.
  return pick.ok ? fillRow(row, { pick: pick.value, gate }) : fillRow(row, { gate })
}

/**
 * Why a read did not answer, or null where it did.
 *
 * The two failures are different sentences and a screen shows both: a payload this app
 * could not read means it is behind the engine, and a refusal means the engine declined.
 */
function whyNot<T>(verb: string, answer: Parsed<Answer<T>>): Unreadable | null {
  if (!answer.ok) {
    return {
      reason: 'unreadable-payload',
      message:
        `\`${verb}\` answered with ${answer.failure.got} where ` +
        `${answer.failure.path || 'the answer'} should have been ${answer.failure.expected}`,
      elapsedMs: 0,
      argv: [verb],
      said: '',
    }
  }
  if (answer.value.kind === 'refused') {
    return {
      reason: 'unreadable-payload',
      message: `\`${verb}\` was refused`,
      elapsedMs: 0,
      argv: [verb],
      said: saidBy(answer.value.refusal.said),
    }
  }
  return null
}

function never(verb: string): Unreadable {
  return {
    reason: 'unreadable-payload',
    message: `\`${verb}\` answered nothing this app can read`,
    elapsedMs: 0,
    argv: [verb],
    said: '',
  }
}
