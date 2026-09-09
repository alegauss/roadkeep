# Decisions

## Block A — The client (payloads in, types out)

- ✅ **RG64** **the fast suite and the one that spawns a real engine are one command, so every run pays for both** — A test that spawns a process, opens a window or reads the build is named `*-live.test.*`; suites.test.ts reads every test file and fails when one is filed under a fast name.
- ✅ **RG65** **resolving an engine costs two interpreter starts on Windows, where the same file is spelled two ways** — A rule about what a path means is handed into `core` and never folded inside it, even written as pure string work.
- ✅ **RG75** **two live tests still name RG9, so the commit that ships it fails a suite nothing changed to break** — A live test names no open id: it asks the engine for a line in the state it is about.

### §RG65 What a path means is not core's to know

The cheaper fix was one line inside `core`: normalise the separator in both strings
before comparing. It was rejected because a backslash is an ordinary character in a
filename on Linux, so the fold would report two different files as one — and the branch
it lies to is the one saying the declared copy was *reached*. Claiming to have run an
engine nobody ran is the failure this module exists to avoid, and a comparison correct
on one platform is not cheaper than a second process start.

So `resolveEngine` takes the comparison and defaults to a literal one: slow on Windows,
never wrong anywhere. `root-paths.ts` had answered the same question for folders without
recording why. This is the second instance, and the constraint is general: a rule about
paths belongs to whoever has the filesystem, even written as pure string work that would
compile in `core` untouched.

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

## Block G — The shell (an executable now, a service later)

- ✅ **RG37** **there is no application at all: no window, no build and no way to run any of this** — The desktop shell is Electron over Vite and React, not a native toolkit: the renderer has to be the half a web service later serves to a browser unchanged.

### §RG37 Electron, and what it costs

Electron rather than a native toolkit because the second life of this project is a web
service, and in that life `ui` is served to a browser while `core` runs behind an HTTP
handler with a different transport under the same interface. The cost is honest and
worth stating: a large runtime, a heavier executable, and a renderer that has to be
locked down because it is a browser. Tauri would spend less and would leave the same
seam; it was not chosen because the toolchain here is already the one roadkeep's own
site is built with, so the build conventions exist in a repository beside this one. Vite
and React 19 follow from that. One thing settled while building against the choice
belongs with it: everything is ESM and TypeScript, launchers included, so one `tsc -b`
spans every file the project runs and not only what it ships.

## Block H — The look (a design system for governed prose)

- ✅ **RG39** **there is no design system, so every screen decides its own type, spacing and colour on the spot** — The design system is @viglet/viglet-design-system, a dependency shared with Turing, Shio and Dumont: this app declares no colour, type scale, spacing or radius of its own.
- ✅ **RG52** **there is one ground, so somebody who works in dark reads this app in light** — The design system owns the theme switch; this app resolves the setting and never mounts a second theme system.

### §RG39 A shared design system, not a copied one

The design this replaces planned to copy shadcn into this repository, so a variant would
be an edit rather than a fork. That reasoning is sound and it was answered by a package
that already exists: `@viglet/viglet-design-system` holds those components, and Turing,
Shio and Dumont render with it. A fourth copy would have been a fourth set of tokens
drifting from three that agree.

What is given up is real: this app cannot edit a component in place, and a change it
needs is a release of somebody else's package. Against that, a token declared here is a
token the other three do not have. The exception that remains shows the supported shape
— the four `--vg-accent-*` variables are re-keyed on `:root` to roadkeep's own site
colours.

The dependency also arrives with a high-severity advisory through `xlsx`, filed as its
own line rather than accepted quietly.
