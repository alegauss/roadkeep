import path from 'node:path'

/**
 * Which bash runs a workflow step here (RG218).
 *
 * The release workflow's steps are bash, so the test that runs one needs a bash — and on Windows
 * `bash` on PATH is whichever directory comes first that holds a `bash.exe`. Where that is
 * `%LOCALAPPDATA%\Microsoft\WindowsApps`, it is WSL's launcher: the script runs inside a Linux
 * distribution with no `node`, exits 127, and reads exactly like the step refusing. The runner
 * has Git's bash first, which is why the test only ever failed on a person's machine.
 *
 * **Git's bash, found beside git.** Git for Windows installs `cmd\git.exe` for PATH and
 * `bin\bash.exe` beside it, so the bash is found from where git is, with no git command run to
 * ask. Anywhere but Windows, `bash` on PATH is the one a step runs and stays.
 *
 * Pure over the platform, the PATH and a way to ask whether a file exists, so a machine with
 * WSL first is a test and not a machine somebody has to own.
 */

export type BashAnswer =
  | { readonly kind: 'found'; readonly command: string }
  | { readonly kind: 'missing'; readonly said: string }

/** Where Git for Windows puts its bash, relative to the directory `git.exe` was found in. */
const BASH_BESIDE_GIT = [
  // `…\Git\cmd\git.exe`, the directory the installer puts on PATH.
  path.win32.join('..', 'bin', 'bash.exe'),
  // `…\Git\mingw64\bin\git.exe`, the one a shell inside Git already has on PATH.
  path.win32.join('..', '..', 'bin', 'bash.exe'),
]

export function bashFor(
  platform: string,
  pathValue: string,
  exists: (file: string) => boolean,
): BashAnswer {
  if (platform !== 'win32') return { kind: 'found', command: 'bash' }

  const looked: string[] = []
  for (const directory of pathValue.split(';').filter((entry) => entry !== '')) {
    if (!exists(path.win32.join(directory, 'git.exe'))) continue
    for (const relative of BASH_BESIDE_GIT) {
      const bash = path.win32.resolve(directory, relative)
      if (exists(bash)) return { kind: 'found', command: bash }
      looked.push(bash)
    }
  }

  return {
    kind: 'missing',
    said:
      looked.length === 0
        ? 'no directory on PATH holds git.exe, so there is no Git bash to run a workflow step with'
        : `Git is on PATH but its bash is not beside it: looked for ${looked.join(', ')}`,
  }
}
