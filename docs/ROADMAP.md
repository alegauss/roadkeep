# roadkeep — Roadmap (active backlog)

> **Single source of truth for task status.** Flat, one line per task.
> Only **unshipped** work lives here (📋 designed · 💭 idea · ⏳ partial · 🛠 in-progress).
> Shipped work moves to [CHANGELOG.md](CHANGELOG.md); design rationale lives in
> [IMPROVEMENTS.md](IMPROVEMENTS.md).
>
> **What this is.** A CLI that owns writes to a project's roadmap, changelog,
> improvements and strategy files, so the format is a schema at the point of
> insertion instead of a convention an author is asked to remember — shipped as a
> Claude Code plugin, because the author to constrain is usually an agent.
>
> **The one law.** *A field limit enforced only by a reviewer is a limit discovered
> after the prose is written.* `add` refuses an over-length field; `lint` refuses a
> file that drifted anyway. The tool validates — it never writes prose.
>
> **An entry here is one sentence: what + why + `→` pointer** — ≤320 characters,
> symptom in bold (what does not work), never a solution name. This file is the
> tool's own conformance fixture: if `lint` cannot pass it, `lint` is wrong.
>
> **How to pick work:** the lowest-numbered task whose `deps` are all shipped.

## Priority

## Block A — The model (a task is data before it is a line)

## Block B — Authoring (insert, never hand-edit)

- 📋 **RK1014** (deps: —) **A project with no queue is told to write the heading by hand, and the verb that would move one says the first writes it** — Each of the two queue doors names the other, so the one edit the guard denies is the only route to a section every other heading has a verb for. → §RK1014

## Block C — Query (consult without reading the file)

## Block D — The gate

- 📋 **RK1012** (deps: —) **A pointer can resolve to a heading with no prose, or to one with no title, and the gate reports neither** — Both are refused at the door and RK1004 measured them as the two states of forty-three that a file can hold with nothing saying so. → §RK1012
- 📋 **RK1015** (deps: —) **A door says nothing about whether running it writes, and the kind beside it describes the remedy and not the door** — One `decide` holds a read and a write, so a caller that has to know which it pressed cannot, and the safe reading is to treat every door as both. → §RK1015
- 📋 **RK1016** (deps: —) **The Layout index names a sixth surface nowhere, and what holds it reads package modules only** — RK203 gated the modules and left the surfaces to a reader, so an editor host and the script that packages it are in the tree and in no index. → §RK1016

## Block E — Adoption

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

## Block G — The editor surface (the backlog where the file is open)

- 📋 **RK1010** (deps: RK1011 ✅) **A surface written in another language has no gate in this tree, so CI proves the Python and nothing proves the client** — Five surfaces already ship from here with no build step, and the sixth brings a toolchain, a marketplace and a version bumped every commit. → §RK1010

## Non-goals

Deliberately **not** built — check this list before proposing work:

- **No web UI and no server.** Files and a CLI. The store is the repository.
- **No model and no prompts.** The tool validates and renders; it never writes the
  symptom or the rationale. A generator would reintroduce exactly the prose drift
  this exists to stop.
- **No enforced id scheme beyond `<prefix><n>`.** Non-contiguous, retired-never-reused
  is a property of real backlogs, not a defect to normalize.
- **No dates or quarters.** A marker is maturity, not a schedule.
- **No backlog in an issue tracker** (Jira, Linear, GitHub Issues.) A backlog that lives
  in a service is one an agent cannot `Grep`; a one-way report about this tool, sent
  explicitly, moves nothing out of the files.
- **No multi-line task line.** A task whose text wraps across paragraphs, with its deps
  on a `↳` line of their own, is a second grammar; reading only the first line would
  ship a truncated why and orphan the rest.
- **No supported Python API.** The CLI, the MCP tools and the plugin are the surface;
  `from roadkeep import Schema` is how the tests reach the vocabulary, so no `py.typed`
  ships and a rename inside the package breaks nobody.
- **No effort or size field.** Nothing can verify a letter, `pick`'s every tier is a
  fact, and what an agent pays is context — median to p90, files vary 1.4× against lines
  2.7×, so the letter prices the axis nobody pays.
