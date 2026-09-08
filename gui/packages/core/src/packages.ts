/**
 * The three packages this repository is split into, and what each one is allowed to
 * know. The split is the design, not a folder convention: `core` is the half a web
 * service would keep, `ui` is the half it would serve to a browser, and `shell` is
 * the half it would throw away.
 *
 * This table is the scaffold's own evidence. The renderer draws it, so a window that
 * shows three rows has proved that all three packages compile against each other and
 * that a value made in `core` reached React through the process that opened the
 * window. It is placeholder data in the sense that nothing reads a backlog yet, and
 * it is not placeholder in the sense that the split it describes is what every later
 * task is filed against.
 *
 * The names are here and the sentences are not: a package name is an identifier a person
 * reads as a name, and a sentence about it is this app's own voice, which since RG51 lives
 * in the wording catalogue with everything else somebody reads.
 */
export const PACKAGES = ['core', 'ui', 'shell'] as const

export type PackageName = (typeof PACKAGES)[number]
