// The shape scripts/product.mjs writes into product.generated.ts. Declared by hand so the
// generated file is data and nothing else, and so a field the copy reads that the generator
// stopped writing is a type error rather than an `undefined` on the page.

export interface Product {
  /** package.json's version, which is also what the release tag has to match. */
  readonly version: string
  readonly license: string
  /** The read verbs, spelled as `commands` publishes them: `list`, `non-goal list`. */
  readonly reads: readonly string[]
  /** The write verbs, from the separate table. */
  readonly writes: readonly string[]
  /** Each language the window speaks, by the name it calls itself. */
  readonly languages: readonly string[]
  readonly scan: { readonly defaultDepth: number; readonly depthCeiling: number }
  /** The renderer flags a packaged build must keep, or `npm run stamp` refuses it. */
  readonly posture: Readonly<Record<string, boolean>>
  /** What an "Explain" question may use, and how many turns it gets. */
  readonly question: { readonly tools: readonly string[]; readonly turns: number }
  /** The electron-builder targets, per platform. `mac` is declared and never built. */
  readonly installers: {
    readonly win: readonly string[]
    readonly linux: readonly string[]
    readonly mac: readonly string[]
  }
  readonly nonGoals: readonly { readonly title: string; readonly why: string }[]
}
