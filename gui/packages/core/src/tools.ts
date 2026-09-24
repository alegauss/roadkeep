import type { Spelling } from './verbs'
import { spell } from './verbs'
import { asRecord } from './reading'

/**
 * The same call, spelled for the engine's other surface (RG101).
 *
 * `roadkeep mcp` is one process that starts once and answers over stdio, and a call to it
 * costs what an in-process call costs — where spawning the CLI costs about a second and a
 * half, almost all of it Python starting. What it takes is not an argv: every tool has a
 * schema, so the arguments arrive as an object with the names that schema publishes.
 *
 * **So a request carries both spellings and each transport reads the one it speaks.** The
 * alternative is a transport that parses the argv back into an object, which is composing a
 * command line in order to take it apart again — and which would go wrong on exactly the
 * fields where quoting is hard, which are the ones a person typed.
 *
 * **Both are derived from the same table**, so a verb cannot be spelled one way for one
 * transport and another way for the other. The two rules below are the whole difference:
 * the tool name is the verb's words joined with an underscore, and an argument name is the
 * input field in the snake case the schema publishes.
 */

/** A call as the MCP surface takes it: a tool, and arguments its schema names. */
export interface EngineCall {
  readonly tool: string
  readonly arguments: Readonly<Record<string, unknown>>
}

/**
 * The tool a verb is published as.
 *
 * `non-goal list` is `non_goal_list`: the words the CLI separates with a space, joined with
 * an underscore, and a hyphen inside one is an underscore too. Read off the same spelling
 * table the argv is built from.
 */
export function toolFor(verb: string, spelled: Spelling): string {
  return spell(verb, spelled).join('_').replaceAll('-', '_')
}

/** `noBody` becomes `no_body`, which is the name the schema publishes. */
export function argumentName(field: string): string {
  return field.replaceAll(/[A-Z]/g, (upper) => `_${upper.toLowerCase()}`)
}

/**
 * The arguments one input becomes.
 *
 * A field nobody set is left out rather than sent as `null`: the schemas mark almost
 * everything optional, and a key present with no value is a different thing from an absent
 * one to a validator.
 */
export function argumentsFor(input: unknown): Record<string, unknown> {
  const fields = asRecord(input)
  if (fields === null) return {}

  const out: Record<string, unknown> = {}
  for (const [field, value] of Object.entries(fields)) {
    if (value !== undefined) out[argumentName(field)] = value
  }
  return out
}

/** The whole call, for a verb this app chose and an input it holds. */
export function callFor(verb: string, input: unknown, spelled: Spelling): EngineCall {
  return { tool: toolFor(verb, spelled), arguments: argumentsFor(input) }
}
