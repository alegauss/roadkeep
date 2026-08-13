# Shio — Roadmap (a frozen excerpt)

> **Not a backlog.** One line, copied byte for byte out of Shio's own `docs/ROADMAP.md`
> at `b9302e8e`, because the shape it carries — a **block dep** — shipped out of the live
> tree and RK1144's re-pin retired the only evidence that it was ever real (RK1145).
>
> The provenance is prose on purpose: the parser reads task lines and ignores this, so a
> frozen fixture carries where it came from inside itself rather than in a table beside it.

## Block P — Publishing

## Block N — The editor

- ⏳ **SH238** (deps: SH233 ✅, SH182 ✅, Block P) **The Universal Editor is still not driven end to end** — The one fact the save-back rests on is checked from a browser now; the editor itself embeds site.url in an iframe, so nothing drives the panel, the fields or the save. → §XIV.15
