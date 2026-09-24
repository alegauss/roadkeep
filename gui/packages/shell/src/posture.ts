/**
 * The posture the renderer runs under, as one value and nothing else.
 *
 * Its own module, importing nothing, because three different things have to read it: the
 * window that is constructed with it, the build step that refuses to package a build that
 * lost it, and the test that asserts it. A constant living beside `BrowserWindow` would
 * drag Electron into a plain Node build script, and the script would then either start
 * Electron or keep a second copy — which is the copy that stops agreeing.
 *
 * Every flag here is Electron's own default except `webviewTag`. They are written out
 * anyway: a default is a thing a later edit can turn off without the diff looking like it
 * took anything away, and this list is the difference between a renderer that is a browser
 * and one that can delete a file.
 */
export const RENDERER_POSTURE = {
  contextIsolation: true,
  nodeIntegration: false,
  nodeIntegrationInWorker: false,
  sandbox: true,
  webSecurity: true,
  /** Not a default. A `<webview>` is a second renderer with its own preferences. */
  webviewTag: false,
} as const

/**
 * What a shipped renderer must be.
 *
 * Spelled separately from `RENDERER_POSTURE` on purpose: one is what this build *is* and
 * the other is what a shipped build *must be*, and the build step's whole job is to notice
 * when they stop matching. Two names for the same values is the point here, where
 * everywhere else it would be the duplication to remove.
 */
export const REQUIRED_POSTURE: Readonly<Record<string, boolean>> = {
  contextIsolation: true,
  nodeIntegration: false,
  nodeIntegrationInWorker: false,
  sandbox: true,
  webSecurity: true,
  webviewTag: false,
}

/** Every flag whose value is not the one a shipped build must have. */
export function posturesLost(
  posture: Readonly<Record<string, boolean>>,
  required: Readonly<Record<string, boolean>> = REQUIRED_POSTURE,
): string[] {
  return Object.entries(required)
    .filter(([flag, value]) => posture[flag] !== value)
    .map(([flag, value]) => `${flag} must be ${String(value)}, is ${String(posture[flag])}`)
}
