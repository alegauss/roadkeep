import { refuseIfStale } from './built'

/**
 * What a live run establishes before it starts (RG96).
 *
 * Both live projects have tests whose subject is on disk rather than in the source Vitest
 * compiles: one starts the built app, one reads what the renderer shipped. Run after a
 * source edit and no rebuild, those answer green about code nobody is looking at.
 *
 * A global setup rather than a check in each of them, because the fact is about the run:
 * *this run cannot say anything yet* is one sentence, said once, before any file is loaded.
 * And in one place, so a third test whose subject is the build inherits it.
 */
export function setup(): void {
  refuseIfStale()
}
