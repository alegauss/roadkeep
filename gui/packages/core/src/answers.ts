import { readCommandsPayload, type CommandsPayload } from './capabilities'
import { readEnginesPayload, type EnginesPayload } from './engines'
import {
  readBlockListPayload,
  readBriefAnswer,
  readBudgetPayload,
  readConfigPayload,
  readCriteriaPayload,
  readDeliveredPayload,
  readDepsPayload,
  readLintPayload,
  readListPayload,
  readNonGoalsPayload,
  readPickPayload,
  readReversalsPayload,
  readShowPayload,
  readStatsPayload,
  type BlockListPayload,
  type BriefAnswer,
  type BudgetPayload,
  type ConfigPayload,
  type CriteriaPayload,
  type DeliveredPayload,
  type DepsPayload,
  type LintPayload,
  type ListPayload,
  type NonGoalsPayload,
  type PickPayload,
  type ReversalsPayload,
  type ShowPayload,
  type StatsPayload,
} from './payloads'
import type { Reader } from './reading'
import { readExplanation, type Explanation } from './refusals'
import type { VerbName } from './verbs'

/**
 * What each verb answers with — the other half of the verb table.
 *
 * `verbs.ts` says how a verb becomes a command line. The shapes say how an answer becomes
 * a value. For a while those were two lists with nothing between them, and a verb could be
 * added to one and not the other: the command line built, the call ran, and the payload
 * came back as a string for whoever made the call to interpret. That is the `any` this
 * package spent a task removing, arriving one layer up.
 *
 * This is the join, and it is a type rather than a convention. `{ [K in VerbName]: ... }`
 * is what makes a verb with no shape a compile error instead of a hole, and it is why the
 * table below has to be spelled out rather than derived — a `Partial` here would be the
 * gap written down.
 *
 * It lives in its own file because of what it has to import. `verbs.ts` deliberately
 * imports nothing, and `commands`' shape lives in `capabilities.ts`, which reads the verb
 * table to check a build against it. Putting the readers in `verbs.ts` would close that
 * circle, and the two modules would initialise in an order neither of them chose.
 */

/** The payload each verb answers with, by the name this app calls the verb. */
export interface VerbAnswers {
  list: ListPayload
  show: ShowPayload
  stats: StatsPayload
  brief: BriefAnswer
  deps: DepsPayload
  delivered: DeliveredPayload
  reversals: ReversalsPayload
  budget: BudgetPayload
  nonGoalList: NonGoalsPayload
  criterionList: CriteriaPayload
  lint: LintPayload
  engines: EnginesPayload
  explain: Explanation
  commands: CommandsPayload
  config: ConfigPayload
  pick: PickPayload
  blockList: BlockListPayload
}

export const ANSWERS: { [K in VerbName]: Reader<VerbAnswers[K]> } = {
  list: readListPayload,
  show: readShowPayload,
  stats: readStatsPayload,
  brief: readBriefAnswer,
  deps: readDepsPayload,
  delivered: readDeliveredPayload,
  reversals: readReversalsPayload,
  budget: readBudgetPayload,
  nonGoalList: readNonGoalsPayload,
  criterionList: readCriteriaPayload,
  lint: readLintPayload,
  engines: readEnginesPayload,
  explain: readExplanation,
  commands: readCommandsPayload,
  config: readConfigPayload,
  pick: readPickPayload,
  blockList: readBlockListPayload,
}
