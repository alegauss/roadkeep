import { open, stat } from 'node:fs/promises'

import { FILE_TEXT_CEILING, type FileRefusal, type FileText } from '@rk/core'

import { shownUnder } from './edited-at'
import { withinRoot } from './root-paths'

/**
 * One file a session edited, as the disk holds it now (RG245).
 *
 * **Resolved as `editedAt` resolves**, under the root the session was started in, so a path that
 * leads out of the project is refused before the disk is asked anything. What is under the root
 * is read only where it is a file, no larger than `FILE_TEXT_CEILING`, and text.
 *
 * **Text is judged by a NUL in its first block**, the test a diff tool makes: a source file has
 * none, and an image, an archive or a compiled file almost always has one early. The characters
 * are decoded as UTF-8 and handed over as they are; nothing is parsed, highlighted or kept.
 */

/** How much of a file is looked at for a NUL before its text is trusted. */
export const TEXT_PROBE = 8000

/** What the disk is asked, so a test answers without one. */
export interface Disk {
  /** The size and whether it is a file, or null where nothing is there. */
  readonly stat: (file: string) => Promise<{ readonly size: number; readonly file: boolean } | null>
  /** Every byte of it. Rejects where it cannot be read. */
  readonly read: (file: string) => Promise<Uint8Array>
}

export const REAL_DISK: Disk = {
  stat: async (file) => {
    try {
      const found = await stat(file)
      return { size: found.size, file: found.isFile() }
    } catch {
      return null
    }
  },
  read: async (file) => {
    const handle = await open(file, 'r')
    try {
      return await handle.readFile()
    } finally {
      await handle.close()
    }
  },
}

function refused(
  path: string,
  code: FileRefusal,
  fields: Readonly<Record<string, string>> = {},
): FileText {
  return { kind: 'refused', path, code, fields }
}

export async function fileText(
  root: string,
  spelled: string,
  disk: Disk = REAL_DISK,
): Promise<FileText> {
  const full = withinRoot(root, spelled)
  if (full === null) return refused(spelled, 'outside')

  const found = await disk.stat(full)
  if (found === null) return refused(spelled, 'missing')
  if (!found.file) return refused(spelled, 'unreadable')
  if (found.size > FILE_TEXT_CEILING) {
    return refused(spelled, 'too-large', {
      bytes: String(found.size),
      ceiling: String(FILE_TEXT_CEILING),
    })
  }

  let bytes: Uint8Array
  try {
    bytes = await disk.read(full)
  } catch {
    return refused(spelled, 'unreadable')
  }
  // Measured again on what was read: the file may have grown between the two questions.
  if (bytes.length > FILE_TEXT_CEILING) {
    return refused(spelled, 'too-large', {
      bytes: String(bytes.length),
      ceiling: String(FILE_TEXT_CEILING),
    })
  }
  if (bytes.subarray(0, TEXT_PROBE).includes(0)) return refused(spelled, 'not-text')

  return {
    kind: 'read',
    path: spelled,
    shown: shownUnder(root, full),
    text: new TextDecoder('utf-8').decode(bytes),
    bytes: bytes.length,
  }
}
