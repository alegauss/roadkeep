# The design canvas

Nine artboards drawing this app's screens, and the manifest that lays them out.

These files are the source, and there is no published canvas: the one they were first
published to was deleted on 2026-09-09. Each `.dc.html` opens straight from the file tree.
Claude Code's `design` skill can wrap them in an editor again with `seed-canvas.mjs` — two
megabytes of machinery around content this directory already holds, so it is not kept here
— and a canvas published that way is a new address, extracted back into these files when
somebody saves a version in the browser. Never edit both ends.

Every `.dc.html` is one artboard. `canvas.json` places them, names the two pages and picks
the view a fresh open lands on.

| Page     | Artboards                                                                                                          |
| -------- | ------------------------------------------------------------------------------------------------------------------ |
| Telas    | the portfolio, the project surface, a task detail, the write path, an agent session, and the bento shell's anatomy |
| Decisões | two directions for the same screen, and the same components on both grounds                                        |

The numbers are read rather than invented. Colour, type, radius and the shell's measures
come from the resolved design system, so an artboard is checkable against
`node_modules/@viglet/viglet-design-system`; the backlog figures on the roadkeep-gui row are
this repository's own, and the other projects are sample rows, which the canvas says on the
page.

Three questions it turned up were open on the roadmap rather than answered here: what the
rail's "you are here" is coloured with, which face a section's preserved wrapping is set in,
and which of the two directions the screens follow. RG63 settled the third by adopting the
shell — `Main.dc.html` is the direction, and the chrome around it is the design system's.
The rail's colour was RG105, now shipped: the rail is drawn grey in `Shell.dc.html`
because that is what the package rendered before it. The face
became a criterion of block H rather than a task, there being no code to change yet.

**The chrome in `Main` and `Shell` is held to the window** (RG127). Three lines changed the
header and footer without redrawing either, and a person laying out the next screen measured
a header a control short. So each control the window renders is drawn with a `data-control`
naming the handle its tests find it by, the header and footer are marked with
`data-region`, and `packages/ui/src/artboards.test.tsx` renders the window and requires the
two to agree in order. Something drawn that the window does not render yet — the engine chip
in `Main` — is drawn dashed and left unmarked.
