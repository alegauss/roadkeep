import { spawn } from 'node:child_process'

/**
 * Run one argv to its exit and answer the code, or -1 where it could not start.
 *
 * No shell and no window, and nothing read from its streams: the callers ask a yes-or-no of a
 * command — does this `claude` answer, is this Python new enough, did the install succeed —
 * and the exit code is that answer. Shared by the plugin offer and the Python probe (RK1700,
 * RK1701) so the two ask the machine the same way.
 */
export function exitOf(argv: readonly string[]): Promise<number> {
  return new Promise((resolve) => {
    const [command, ...rest] = argv
    if (command === undefined) {
      resolve(-1)
      return
    }
    const child = spawn(command, rest, { stdio: 'ignore', windowsHide: true, shell: false })
    child.once('error', () => resolve(-1))
    child.once('exit', (code) => resolve(code ?? -1))
  })
}
