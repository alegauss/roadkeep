# The design canvas

Nine artboards drawing this app's screens, and the manifest that lays them out. Published
as a canvas at <https://claude.ai/code/artifact/30eca0a9-a607-4109-92b2-b489988ccbd5>.

These files are the source; the published page is generated. Claude Code's `design` skill
wraps them in an editor with `seed-canvas.mjs`, and that output is two megabytes of
machinery around content this directory already holds, so it is not kept here. Re-seed from
these files to republish to the same URL, and extract from the published page when somebody
has saved a version in the browser — never edit both ends.

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
The rail's colour is RG105, still open, which is why the rail is drawn grey above. The face
became a criterion of block H rather than a task, there being no code to change yet.
