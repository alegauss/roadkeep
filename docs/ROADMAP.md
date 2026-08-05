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

## Block A — The model (a task is data before it is a line)

## Block B — Authoring (insert, never hand-edit)

- 📋 **RK295** (deps: —) **A scope naming a path the tree does not have is recorded in silence** — `claim --path` takes the path verbatim and never asks the disk, so a typo is a file the commit will not stage and a scope that reads as complete. → §RK295
- 📋 **RK296** (deps: —) **An undeclared-block refusal still lists every label the file declares** — RK257 gave it the file and the verb and left the list, so a project with 90 blocks answers a question nobody asked and buries the two clauses that are the remedy. → §RK296
- 💭 **RK298** (deps: —) **A shipped line's commit cannot read the scope its claim carried** — `ship` releases the claim, so the `claim <id> --porcelain` agents.md stages from is refused at the one moment a commit needs it, naming a `status 🛠` the ledger refuses too. → §RK298
- 📋 **RK302** (deps: —) **section add writes an anchor another declared prose file already holds, and only a retired one is refused** — Reproduced on a two-file project: the second add reports success and lint then names four section.ambiguous findings whose own message says every verb reading one refuses. → §RK302

## Block C — Query (consult without reading the file)

- 📋 **RK303** (deps: —) **The section budget picks the first of two prose files declaring one anchor, where every other reader refuses** — It answered improvements about an address strategy declares too, and show calls that state a pointer resolving to neither — so a limit is priced for an unreachable section. → §RK303

## Block D — The gate

## Block E — Adoption

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

- 📋 **RK267** (deps: —) **A staleness note lists every changed module and hands relevance back** — The server appends `engine().stale` to any refusal, so one `schema.py` decided arrives naming three modules that did not, and the reader re-runs on a guess about which mattered. → §RK267
- 📋 **RK275** (deps: —) **No MCP tool asks whether git would run this driver** — `merge --check` is a pure query the server does not expose, so the agent the plugin exists for reaches it only by shelling out — the read L5 says a command should replace. → §RK275
- 📋 **RK304** (deps: —) **The one closed-set argument on the MCP surface publishes no enum, so a role nobody declared is refused after the call** — status publishes its markers and an id its pattern; role, declared in [files] and on four tools, publishes a sentence the client cannot validate. → §RK304

## Non-goals

Deliberately **not** built — check this list before proposing work:

- **No web UI and no server.** Files and a CLI. The store is the repository.
- **No model and no prompts.** The tool validates and renders; it never writes the
  symptom or the rationale. A generator would reintroduce exactly the prose drift
  this exists to stop.
- **No enforced id scheme beyond `<prefix><n>`.** Non-contiguous, retired-never-reused
  is a property of real backlogs, not a defect to normalize.
- **No dates or quarters.** A marker is maturity, not a schedule.
- **No effort or size field.** Nothing can verify a letter, `pick`'s every tier is a
  fact, and what an agent pays is context: 4 to 14 files a task, against lines that vary
  27-fold, so the letter prices the axis nobody pays.
- **No backlog in an issue tracker** (Jira, Linear, GitHub Issues.) A backlog that lives
  in a service is one an agent cannot `Grep`; a one-way report about this tool, sent
  explicitly, moves nothing out of the files.
- **No multi-line task line.** A task whose text wraps across paragraphs, with its deps
  on a `↳` line of their own, is a second grammar; reading only the first line would
  ship a truncated why and orphan the rest.
- **No supported Python API.** The CLI, the MCP tools and the plugin are the surface;
  `from roadkeep import Schema` is how the tests reach the vocabulary, so no `py.typed`
  ships and a rename inside the package breaks nobody.
