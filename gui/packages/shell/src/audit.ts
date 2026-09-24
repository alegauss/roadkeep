import { spawnSync } from 'node:child_process'

import { ACCEPTED, advisoriesIn, GATED_AT, outlived, unexcused } from './advisories'

/**
 * The gate over `npm audit` (RG95).
 *
 * Nothing else in this repository reads a security advisory: `npm ci` does not audit,
 * roadkeep's gate is about governed files, and the suite has no opinion. So the one advisory
 * this project knows about was found by somebody installing a linter for another reason,
 * which is the way of finding out this exists to replace.
 *
 * **`--json` and never the exit code.** `npm audit` exits non-zero for anything at or above
 * the level it was given, accepted or not, so reading the code would make the exception list
 * unreachable. The report is the answer and the rule is `advisories.ts`.
 *
 * **It fails on two things.** An advisory nobody wrote a reason for, which is the point; and
 * an exception the report no longer names, which is how the list stays a record of what is
 * true rather than of what somebody once worried about.
 *
 * Run as `npm run audit`, and in CI beside the other gates.
 */

// One literal command line through a shell, and no argument array.
//
// Windows needs the shell: `npm` there is `npm.cmd`, and since Node 20 `spawnSync` refuses
// a `.cmd` outright with `EINVAL` unless a shell runs it. What a shell usually costs is a
// quoting question — which is why Node warns about passing *arguments* alongside one — and
// there is none here: this string is fixed, nothing is interpolated into it, and there is
// no caller who could put anything there.
const audit = spawnSync('npm audit --json', { encoding: 'utf8', shell: true })

if (audit.stdout === '') {
  process.stderr.write(
    `roadkeep-gui: npm audit printed nothing, so this says nothing about advisories:\n${
      audit.stderr || 'no output on either stream'
    }\n`,
  )
  process.exit(1)
}

let report: unknown
try {
  report = JSON.parse(audit.stdout)
} catch {
  process.stderr.write('roadkeep-gui: npm audit did not answer with JSON, so nothing was read\n')
  process.exit(1)
}

const found = advisoriesIn(report)
const unanswered = unexcused(found)
const stale = outlived(found)

for (const one of unanswered) {
  process.stderr.write(
    `roadkeep-gui: ${one.severity} advisory nobody has answered: ${one.id} in ${one.of || 'a dependency'}\n` +
      `  ${one.title}\n  ${one.url}\n` +
      '  Read it, and either upgrade or add it to ACCEPTED in packages/shell/src/advisories.ts\n' +
      '  with why it does not reach this executable and the date you established that.\n',
  )
}

for (const one of stale) {
  process.stderr.write(
    `roadkeep-gui: ${one.id} is accepted in advisories.ts and npm audit no longer reports it.\n` +
      '  Delete the entry: an exception nobody removes is how the list stops meaning anything.\n',
  )
}

if (unanswered.length > 0 || stale.length > 0) process.exit(1)

process.stdout.write(
  `roadkeep-gui: no unanswered advisory at ${GATED_AT} or above` +
    ` (${String(ACCEPTED.length)} accepted, each with a reason and a date)\n`,
)
