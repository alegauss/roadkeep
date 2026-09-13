---
name: screens
description: How to look at a roadkeep-gui screen before calling a change done — npm run shots for every surface in both grounds, both languages and two widths, the accessibility report beside it, Playwright MCP on the running window for a state no fixture reaches, and the checklist the pictures are read against. Use whenever a change touches anything under packages/ui/src that draws, when asked to check, screenshot, verify or look at a screen, and before committing a UI change.
---

# Looking at a screen

The fast suite renders jsdom, which lays nothing out. A chosen toggle at 1.27:1 against its panel
passed every test and was found by a screenshot somebody improvised (RG207). These are the two ways
to look that this repository keeps, and what to look for once you can.

## 1. Every surface at rest: `npm run shots`

```
npm run build                               # it refuses a stale bundle, as the live suite does
npm run shots -- --only settings            # the surfaces the change touched
npm run shots                               # all of them, before a commit that reaches several
npm run shots -- --a11y-only                # the accessibility pass alone, no pictures
```

Needs python and the wired launcher, like `npm run test:live`. It builds a fixture project, starts
a session on a scripted agent (RG210), and writes to `.shots/`:

- `<surface>[.<state>].<ground>.<locale>.<width>.png` — surfaces are `home`, `project`,
  `project-task`, `project-task-session` (states `following`, `scrolled`, `folded`), `sessions`,
  `project-file`, `project-gate`, `settings`; grounds `light` and `dark`; `en` and `pt-BR`; 1280
  and 400 wide.
- `index.json` — which captures settled.
- `a11y.json` — axe at WCAG A/AA and the chosen-state rule, per surface and ground (RG211). A
  `serious` or `critical` finding nobody excused fails the run; the exceptions are
  `ACCEPTED_FINDINGS` in `packages/shell/src/accessibility.ts`, each with a reason.

Read the pictures with the Read tool. Open the ones the change touched in both grounds and both
widths — never only the ground this machine happens to be on.

## 2. The running window: Playwright MCP

For a state no fixture reaches — a dialog half-filled, a refusal on screen, a menu open:

1. `npm run dev:inspect` in the background. It opens the development window with its debugging
   port at 9333.
2. Use the `mcp__playwright__*` tools (`browser_snapshot`, `browser_click`, `browser_type`,
   `browser_take_screenshot`). `.mcp.json` points the server at that port;
   `playwright-mcp-live.test.ts` holds that it attaches to this app.

If those tools are not in the session — the server was not approved, or the window is not up — say
so and use `npm run shots`. Do not improvise a CDP script.

## 3. What the pictures are checked for

Each is a defect this project has had:

- **A state told by colour alone, or by a shade under 3:1** (RG207). `a11y.json` measures chosen
  options; look anyway, since a state with no ARIA attribute is invisible to it.
- **Text clipped, overflowing or wrapping into a control at 400 wide** (RG215). Compare the `.400.`
  pictures with the `.1280.` ones.
- **A sentence left in English in a `pt-BR` picture**, or a count of one written as a plural
  (RG216).
- **The session stream**: following its end, _Jump to latest_ inside the window when scrolled up,
  folded notes counted (RG206, RG208, RG217).
- **Both grounds**: a border, a ring or a muted text that only one of them loses.
- **The artboard it answers to** — `Main` and `Shell` for the chrome, `Projeto`, `Tarefa`,
  `Escrita` and `Sessao` for their surfaces, `Fundos` for the grounds — and each departure from it
  on purpose, said in the change.

## 4. What pictures cannot show

- **Keyboard order and reach** — `keyboard.test.tsx` in jsdom, and a real Tab in the browser
  project when it lands (RG213, RG214).
- **What a screen reader announces** — axe checks names and roles, not the sentence heard; the
  tests assert accessible names by role.
- **Motion** — the design system's reduced-motion guard, not a still picture.
- **A state no fixture reaches** — the running window above, or a test that builds it.
