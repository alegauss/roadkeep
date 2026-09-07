# Decisions

## Block A — The client (payloads in, types out)

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

