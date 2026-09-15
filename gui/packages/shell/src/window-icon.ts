import path from 'node:path'

/**
 * The icon a window names, which is only ever the unpackaged one's (RG236).
 *
 * RG138 put roadkeep's mark into the executable, through `buildResources` and the resource
 * edit, and neither reaches a window that is not packaged: `npm run dev` and `npm start` run
 * `electron.exe`, whose own icon is the atom, so a window naming nothing wore it in the title
 * bar and the taskbar on exactly the runs a developer looks at most.
 *
 * **The PNG, not the SVG.** `build/icon.svg` is the source, and Electron's native image reads
 * PNG and ICO and never SVG; `build/icon.png` is the committed render of it, which `npm run
 * icon` keeps in step.
 *
 * **Nothing, packaged.** `buildResources` is not copied into the app, so the path would name a
 * file that is not there, and the executable already carries the icon Windows draws.
 *
 * `beside` is the directory the compiled main process lives in — `shell/dist`, or `shell/src`
 * under a test — which sit at one depth, so the repository root is three steps up from either.
 */
export function windowIcon(
  beside: string = import.meta.dirname,
  packaged = false,
): string | undefined {
  if (packaged) return undefined
  return path.join(beside, '..', '..', '..', 'build', 'icon.png')
}
