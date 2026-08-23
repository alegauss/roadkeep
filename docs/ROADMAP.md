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

- 📋 **RK1311** (deps: —) **amend --requires alone is refused as nothing to amend, then reports unchanged on the call that writes it** — The flag is parsed, documented and working, but the guard and the confirmation both ignore it, and show never prints the field. → §RK1311
- 📋 **RK1312** (deps: —) **section amend --replace refuses a sentence the section carries, because the stored copy is wrapped across lines** — The fragment that fits one stored line is the fragment likeliest to occur twice, so the two rules push opposite ways. → §RK1312

## Block C — Query (consult without reading the file)

- 📋 **RK1306** (deps: —) **brief states the ledger allowance but not what --recorded-in and --superseded-design spend from it** — A why composed to the published number is refused by arithmetic the caller had no way to do, which cost a round trip on five ships out of five. → §RK1306
- 📋 **RK1307** (deps: —) **The json payload drops the sentence and the remedy the human output carries, so an MCP caller gets less than the CLI** — Every agent reaches these reads through the served payload, so the reader that most needs the remedy named is the one that never sees it. → §RK1307
- 📋 **RK1309** (deps: —) **a new line's section budget is reachable only through brief, which needs an id, so the first body is written blind** — add's own help calls a limit reported after the prose exists too late, and the prose fields are where it still lands. → §RK1309
- 📋 **RK1310** (deps: —) **nothing resolves a sentence to the anchor carrying it, so a section amend addressed by text is guessed and retried** — A pointer takes an id to a section and no verb takes prose to one, and the refusal that knows the answer prints show instead. → §RK1310
- 📋 **RK1314** (deps: —) **config prints the criteria table under the non-goals sentence, so the read names the wrong table** — Both addresses map to `_SCOPE_KEYS`, so the docstring rides with the key set and the read that says what may be declared describes `[criteria]` as the roadmap's other bullet. → §RK1314

## Block D — The gate

- 📋 **RK1308** (deps: —) **lint exits 1 on install.stale, so a CI gate goes red on a backlog it has just reported clean** — The published action's contract is that exit code, and whether this checkout's wired surface matches the engine is not a fact about the branch. → §RK1308

## Block E — Adoption

- 📋 **RK1313** (deps: —) **init writes no [criteria] and no [requirements], so the verbs that fill them refuse on a fresh project** — RK1040 scaffolds `[non_goals]` empty so its verb works on day one, and the two opt-in tables added since left `criterion add` and `--requires` behind a hand edit. → §RK1313

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

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
- **No supported Python API.** The CLI, the MCP tools and the plugin are the surface; a
  boundary held by a test inside the package is not one, so nothing ships `py.typed` and
  a rename still breaks nobody.
- **No effort or size field.** Nothing can verify a letter, `pick`'s every tier is a
  fact, and what an agent pays is context — median to p90, files vary 1.4× against lines
  2.7×, so the letter prices the axis nobody pays.
