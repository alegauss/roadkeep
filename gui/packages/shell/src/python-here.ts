import { exitOf } from './exit-code'

/**
 * Whether a Python roadkeep can run on answers on this machine (RK1701).
 *
 * Every launcher is a Python script and roadkeep's floor is 3.11, so a machine without one sees
 * every engine fail to answer — which read as *no candidate answered*, naming neither cause. The
 * check runs the interpreter and reads its exit; it imports nothing from the package, so the
 * "no supported Python API" non-goal is not what this touches.
 */
export const PYTHON_FLOOR = 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'

/** The names a Python goes by, in the order a Unix PATH is likelier to answer. */
export const PYTHONS: readonly string[] = ['python3', 'python']

/** Whether some Python on PATH is 3.11 or newer, asked through ``run``. */
export async function pythonAnswers(
  run: (argv: readonly string[]) => Promise<number>,
): Promise<boolean> {
  for (const python of PYTHONS) {
    if ((await run([python, '-c', PYTHON_FLOOR])) === 0) return true
  }
  return false
}

let probed: Promise<boolean> | undefined

/**
 * The answer for this process, asked once on first need.
 *
 * Once per start and not once per project: a portfolio opens every project on the machine, and
 * the answer is the machine's. Asked again on the next start, since Python can be removed or
 * installed between two — which is why this is not remembered on disk.
 */
export function pythonHere(): Promise<boolean> {
  probed ??= pythonAnswers(exitOf)
  return probed
}
