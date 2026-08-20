// The host, and the list where the file is open (RK1011, RK1006).
//
// A person with the roadmap open sees 320-character lines under six headings. The order that
// matters is not the order on the page — ready before blocked, the blocker named on the ones
// that are not — and every one of those is an answer some verb already gives. What was
// missing is a place to show them at the moment somebody is looking at the file.
//
// Three properties decide whether this is right, and none of them is about the view.
//
// It **activates on a governed workspace** — `workspaceContains:roadkeep.toml` in the
// manifest, not `*` and not every Markdown file — for the reason the write path is a
// trigger-loaded skill rather than a preamble: a surface that costs something on every
// session touching none of these files is paying for the sessions it does nothing in.
//
// It **carries no rule**. No limit, no marker set, no id shape, no parser. Every fact below
// was read from a payload some verb printed, and `tests/test_editor.py` holds that: a
// literal marker, id or governed filename here is a rule compiled into a reader, which is L6
// broken from the outside instead of the inside.
//
// And the gate is a **translation and not a feature**: a finding already carries
// `file:line:column`, a code and — since every one of them names the command that closes it
// — a complete argv with the id and the line number substituted. That is the payload a
// problems panel and a quick-fix menu take, so nothing here decides anything about it. A
// door the tool marked incomplete becomes no action at all, because the blank in it is prose
// only the author can write.
//
// The write door is the same argument again. A view that only reads sends its user to a
// terminal to write, and the terminal is where the format is typed from memory — the whole
// failure this project is about, moved one window across. So the prompt carries the schema:
// `budget` answers, before the first word, what each field has left on *this* line, and the
// input counts it down. It is **not a second validator** — `add` still decides, and its
// refusal is what the editor reports — and nothing here writes the file, ever: the command
// writes and the watcher shows the result, which keeps one writer (L3).
//
// And it **never parses Markdown**. Readiness is not derived from the dep list a row carries
// — that would be this client re-implementing the resolver, which is the second
// implementation this project exists to remove and the easy thing to write. It comes from
// `deps`, one call per row, asked when a block is opened and cached until the file changes.
//
// Plain CommonJS and no dependencies, which is not thrift — it is the same argument the
// package makes about `argparse` over `click`: five surfaces already ship from this tree
// with no build step, and a sixth that needs a toolchain is a toolchain in everyone's CI.
"use strict";

const cp = require("child_process");
const vscode = require("vscode");

/** How long a read may take before it is reported rather than waited on. */
const TIMEOUT_MS = 15000;

/**
 * The one roadkeep this view may call: the workspace's declaration, or nothing (RK1009).
 *
 * **A declared setting and never a search.** Three copies of this tool can already be in
 * play — the plugin the hook and the skill come from, the action CI gates on, and whatever
 * the caller runs — and `engines` exists because they are allowed to differ. An editor adds
 * a fourth and it is the one most likely to be wrong: resolved from a PATH the shell
 * configured, a virtualenv the workspace happened to activate, a `uvx` cache nobody pinned.
 *
 * The failure is quiet, which is what decides it. A panel showing findings a commit will not
 * produce — or missing ones it will — is worse than a panel that says which setting to fill
 * in, because the first is discovered when a hook denies a write the panel said was fine.
 *
 * The cost is real and taken deliberately: this does not work out of the box for somebody
 * who has `roadkeep` on PATH. What they get instead is one sentence naming the setting, and
 * an answer they can trust from the moment it appears.
 */
function declared() {
  const said = vscode.workspace.getConfiguration("roadkeep").get("command");
  return said ? said.trim().split(/\s+/) : null;
}

/** The sentence a reader gets instead of a guess. Names the setting and nothing else. */
const UNDECLARED =
  "roadkeep.command is not set: name the roadkeep this workspace writes with, so the view " +
  "answers from the copy your commits do and not from whatever PATH resolves";

/**
 * Run one command in the workspace and hand back its stdout, its stderr and its code.
 *
 * Never throws for a non-zero exit: `lint` answers *and* exits 1, so a reader that treated a
 * code as no output would drop the findings it was asked for. The two failures a child
 * process really has — not installed, and refused — are the ones the caller reports.
 */
function run(argv, cwd) {
  return new Promise((resolve) => {
    cp.execFile(
      argv[0],
      argv.slice(1),
      { cwd, timeout: TIMEOUT_MS, encoding: "utf8", windowsHide: true },
      (error, stdout, stderr) => {
        const missing = error && (error.code === "ENOENT" || error.code === "EACCES");
        resolve({
          stdout: stdout || "",
          stderr: stderr || "",
          missing: Boolean(missing),
        });
      }
    );
  });
}

/**
 * One payload, or a reason there is none.
 *
 * The candidates are tried in order and the *first one that is installed* answers, however
 * it exits: a roadkeep that ran and refused is the engine this workspace has, and moving on
 * to the next candidate would report the second engine's opinion about the first one's file.
 */
async function payload(cwd, argv) {
  const command = declared();
  if (!command) {
    return { error: UNDECLARED };
  }
  const spelled = command.join(" ");
  const said = await run([...command, ...argv, "--json"], cwd);
  if (said.missing) {
    return { error: `\`${spelled}\` is not runnable here` };
  }
  if (!said.stdout.trim()) {
    return { error: said.stderr.trim() || `\`${spelled}\` printed nothing` };
  }
  try {
    return { value: JSON.parse(said.stdout) };
  } catch (_) {
    return { error: `\`${spelled}\` did not answer JSON` };
  }
}

/**
 * Run one command for its effect rather than its payload — a repair, or a door.
 *
 * Separate from `payload` because what a caller does with the two differs: this one is
 * reported to the person who pressed something, and its exit code is the tool's own verdict.
 */
async function command(cwd, argv) {
  const found = declared();
  if (!found) {
    return { error: UNDECLARED };
  }
  const said = await run([...found, ...argv], cwd);
  if (said.missing) {
    return { error: `\`${found.join(" ")}\` is not runnable here` };
  }
  return { output: said.stdout.trim(), error: said.stderr.trim() };
}

/**
 * The gate's findings as diagnostics, anchored where the report already points.
 *
 * One collection for the whole workspace and not one per document: `lint` judges the files
 * together — a pointer resolving into another file, a block heading two of them disagree
 * about — so a per-file run would answer a question nobody asked.
 */
class Gate {
  constructor(root, diagnostics) {
    this.root = root;
    this.diagnostics = diagnostics;
    // Kept so a code action can find the finding its diagnostic came from: a `Diagnostic`
    // carries no room for a remedy, and re-running the gate to look one up would answer
    // about a file that may have been written since.
    this.remedies = new Map();
  }

  async check() {
    const answer = await payload(this.root, ["lint"]);
    this.diagnostics.clear();
    this.remedies.clear();
    if (answer.error) {
      return answer.error;
    }
    const byFile = new Map();
    for (const finding of answer.value.findings) {
      const at = new vscode.Range(
        Math.max(finding.line - 1, 0),
        finding.column ? finding.column - 1 : 0,
        Math.max(finding.line - 1, 0),
        finding.column ? finding.column - 1 : Number.MAX_SAFE_INTEGER
      );
      const said = new vscode.Diagnostic(at, finding.message, vscode.DiagnosticSeverity.Error);
      // The gate's own code, unmapped: `lint` exits non-zero on any finding, so a severity
      // table here would be this reader grading what the tool already decided.
      said.code = finding.code;
      said.source = "roadkeep";
      const uri = vscode.Uri.joinPath(vscode.Uri.file(this.root), ...finding.file.split("/"));
      if (!byFile.has(uri.fsPath)) {
        byFile.set(uri.fsPath, { uri, found: [] });
      }
      byFile.get(uri.fsPath).found.push(said);
      this.remedies.set(`${uri.fsPath}:${finding.line}:${finding.code}`, finding.remedy);
    }
    for (const { uri, found } of byFile.values()) {
      this.diagnostics.set(uri, found);
    }
    return "";
  }

  /** The doors a finding names, as actions — and only the ones the tool called complete. */
  provideCodeActions(document, range, context) {
    const out = [];
    for (const said of context.diagnostics) {
      if (said.source !== "roadkeep") {
        continue;
      }
      const remedy = this.remedies.get(
        `${document.uri.fsPath}:${said.range.start.line + 1}:${said.code}`
      );
      for (const door of (remedy && remedy.doors) || []) {
        if (!door.complete) {
          // A marked blank is a title, a shorter symptom or a reason — prose the tool does
          // not compose (L4), and an editor is not the place to start writing one.
          continue;
        }
        const action = new vscode.CodeAction(
          `roadkeep ${door.argv.join(" ")} — ${door.what}`,
          vscode.CodeActionKind.QuickFix
        );
        action.diagnostics = [said];
        action.command = { command: "roadkeep.run", title: "Run it", arguments: [door.argv] };
        out.push(action);
      }
      const explain = new vscode.CodeAction(
        `roadkeep explain ${said.code}`,
        vscode.CodeActionKind.QuickFix
      );
      explain.command = { command: "roadkeep.explain", title: "Explain", arguments: [said.code] };
      out.push(explain);
    }
    return out;
  }
}

/**
 * Completion and hover in `roadkeep.toml`, from the shape the package prints (RK1270, RK1271).
 *
 * The half before the save. The gate half already worked and needed nothing built — the
 * config is in `lint`'s checked list, its findings carry `file:line:column` and the door that
 * closes them, and the two providers above are registered for any file the gate names. What
 * was absent is the moment before: which key it was, answered while somebody is typing.
 *
 * **It carries no rule, and that is the whole reason this waited on a verb.** A completion
 * list written here would be nine frozensets restated in a language the parser never reads —
 * the widest L6 break this surface could make, and the easy thing to write. Every table,
 * every key, every type, every default and every sentence below came out of one payload.
 *
 * What it does know is **TOML**, which is not a roadkeep rule: a line starting with `[` opens
 * a table, and a key belongs to the last one opened above it. That is the whole of the
 * parsing, and it is deliberately the whole of it — a client that resolved values would be
 * the second reader of this format, which is what `config` exists to make unnecessary.
 *
 * Cached until the file changes, like every other read this view makes: the shape moves when
 * the *engine* moves, so an upgrade is what `reread` is for and a save is not.
 */
class Settings {
  constructor(root) {
    this.root = root;
    this.shape = null;
  }

  /** Forget the shape — for a refresh, which is the ask an upgrade arrives through. */
  reread() {
    this.shape = null;
  }

  async keys() {
    if (this.shape === null) {
      const answer = await payload(this.root, ["config"]);
      // An empty list and never an invented one: a read that failed knows nothing about
      // which keys exist, and offering a guess is the compiled-in rule this must not be.
      this.shape = answer.error ? [] : answer.value.keys;
    }
    return this.shape;
  }

  /**
   * Which table the cursor is in, `""` for the top level and `null` for a header line.
   *
   * Read upwards from the line above the cursor, because the header that owns a key is the
   * last one before it — and a `<role>` or a `<path>` in the payload's own name is matched by
   * its stem, that placeholder being the address the project chooses and never a key.
   */
  table(document, line) {
    for (let at = line - 1; at >= 0; at -= 1) {
      const text = document.lineAt(at).text.trim();
      const opened = /^\[\s*([^\]]+?)\s*\]$/.exec(text);
      if (opened) {
        return opened[1];
      }
    }
    return "";
  }

  /** The payload's name for a table the file spells concretely — `limits.changelog` is the
   * `limits` this build published, and `budgets."agents.md"` is `budgets.<path>`. */
  named(written, tables) {
    if (tables.includes(written)) {
      return written;
    }
    const stem = written.split(".")[0];
    return tables.find((one) => one === stem || one.startsWith(`${stem}.`)) || written;
  }

  async provideCompletionItems(document, position) {
    const keys = await this.keys();
    if (!keys.length) {
      return [];
    }
    const tables = [...new Set(keys.map((one) => one.table))];
    const line = document.lineAt(position.line).text;
    // On a header line the subject is the table itself, so what is offered is the addresses
    // and not the keys — including the placeholders, which say a name goes there.
    if (line.trimStart().startsWith("[")) {
      return tables
        .filter((one) => one)
        .map((one) => this.item(one, `[${one}]`, `table`, ""));
    }
    const under = this.named(this.table(document, position.line), tables);
    return keys
      .filter((one) => one.table === under)
      .map((one) =>
        this.item(one.key, `${one.key} = `, one.type || "table", this.detail(one))
      );
  }

  async provideHover(document, position) {
    const range = document.getWordRangeAtPosition(position);
    if (!range) {
      return null;
    }
    const word = document.getText(range);
    const keys = await this.keys();
    const tables = [...new Set(keys.map((one) => one.table))];
    const under = this.named(this.table(document, position.line), tables);
    // This table's own row first, and any row carrying the name second: a hover on a header
    // line has no table of its own, and `why` under two tables is two rows and one word.
    const found =
      keys.find((one) => one.table === under && one.key === word) ||
      keys.find((one) => one.key === word || one.table === word);
    if (!found) {
      return null;
    }
    return new vscode.Hover(new vscode.MarkdownString(this.detail(found)), range);
  }

  /** What a row says, in the tool's own words — the type, the default, whether this project
   * declared it, and the sentence its source already carried. Nothing composed here. */
  detail(row) {
    const parts = [];
    if (row.type) {
      parts.push(`\`${row.type}\``);
    }
    parts.push(row.default === null ? "no default" : `default \`${row.default}\``);
    parts.push(row.declared ? "declared here" : "not declared here");
    const head = `**${row.address}** — ${parts.join(", ")}`;
    return row.note ? `${head}\n\n${row.note}` : head;
  }

  item(label, inserted, kind, detail) {
    const one = new vscode.CompletionItem(label, vscode.CompletionItemKind.Property);
    one.insertText = inserted;
    one.detail = kind;
    if (detail) {
      one.documentation = new vscode.MarkdownString(detail);
    }
    return one;
  }
}

/**
 * Ask for one field with its budget counting down beside it.
 *
 * `createInputBox` and not `showInputBox`, because the latter's only live hook is
 * `validateInput` — which *blocks* the accept button, and blocking is the second validator
 * this must not become. The number is shown; `add` decides.
 */
function ask(title, prompt, field) {
  return new Promise((resolve) => {
    const box = vscode.window.createInputBox();
    box.title = title;
    box.prompt = prompt;
    const left = () =>
      `${prompt} — ${field.left - box.value.length} of ${field.limit} left (${field.unit}), aim ${field.aim} words`;
    box.prompt = left();
    box.onDidChangeValue(() => {
      box.prompt = left();
    });
    box.onDidAccept(() => {
      const said = box.value;
      box.hide();
      resolve(said);
    });
    box.onDidHide(() => {
      box.dispose();
      resolve(undefined);
    });
    box.show();
  });
}

/**
 * The write door: a block, two fields with their budgets, and `add` deciding.
 *
 * Every number on screen came from `budget --block <x>`, which is derived from the id, the
 * marker, the deps and the pointer — all known before a word exists. The refusal, where
 * there is one, is printed verbatim: it names every field it looked at in one message, and
 * rewording it here would be this reader inventing a second vocabulary for one rule.
 */
async function compose(root) {
  const blocks = await payload(root, ["stats"]);
  if (blocks.error) {
    vscode.window.showErrorMessage(blocks.error);
    return false;
  }
  const block = await vscode.window.showQuickPick(
    blocks.value.blocks.map((one) => ({ label: one.block, description: `${one.counted}` })),
    { title: "roadkeep: which block" }
  );
  if (!block) {
    return false;
  }
  const budget = await payload(root, ["budget", "--block", block.label]);
  if (budget.error) {
    vscode.window.showErrorMessage(budget.error);
    return false;
  }
  const fields = new Map(budget.value.fields.map((one) => [one.field, one]));
  const symptom = await ask(
    `roadkeep: ${budget.value.id} in Block ${block.label}`,
    "what does not work — never the name of a fix",
    fields.get("symptom")
  );
  if (symptom === undefined) {
    return false;
  }
  const why = await ask(
    `roadkeep: ${budget.value.id} in Block ${block.label}`,
    "why it matters, in one sentence",
    fields.get("why")
  );
  if (why === undefined) {
    return false;
  }
  const said = await command(root, [
    "add",
    "--block",
    block.label,
    "--symptom",
    symptom,
    "--why",
    why,
  ]);
  // The refusal verbatim, because it already names every field it looked at in one message
  // — and the answer verbatim too, since it carries the id the tool derived.
  vscode.window.showInformationMessage(said.error || said.output || "written");
  return !said.error;
}

/**
 * The one line that says how much work there is, rendered and never computed (RK1018).
 *
 * Every number is `stats`'s: the total, and each marker with its count in the order the
 * payload lists them — which is the order `roadkeep.toml` declares, so a project with a
 * seventh marker gets a seventh number and nothing here changes (L6). A sort applied here
 * would be this reader holding an opinion about somebody else's vocabulary.
 *
 * `uncounted` shows only when it is not zero: a marker-bearing line the grammar refused is
 * the one thing a total must never silently absorb.
 */
function _counted(stats) {
  const parts = [`${stats.total} open`];
  for (const [marker, count] of Object.entries(stats.markers || {})) {
    parts.push(`${marker} ${count}`);
  }
  if (stats.uncounted) {
    parts.push(`${stats.uncounted} uncounted`);
  }
  return parts.join("   ");
}

/**
 * The backlog as a tree: blocks at the top, their lines under them, ready before blocked.
 *
 * The fields walked are the ones RK1005 wrote down as promised, which is the whole of what
 * this reader may depend on: a key it reads and that test does not is a key free to move
 * under it.
 */
class Backlog {
  constructor(root) {
    this.root = root;
    this.changed = new vscode.EventEmitter();
    this.onDidChangeTreeData = this.changed.event;
    this.file = "";
    // Cleared on every refresh, because the store is the repository and a cached readiness
    // is an answer about a file that has since been written.
    this.readiness = new Map();
    // **Not** cleared on a save (RK1017): which copy answered is a fact about the
    // *installation*, which moves when somebody upgrades and not when a line is edited —
    // and `provenance` says as much about the same question, asking git at most once per
    // process and never on a path that writes. A CLI invocation is a process, so a view that
    // shelled out per save asked it per save, on a keystroke nobody thinks about.
    this.engine = null;
  }

  /** A save: the reads about the file, and not the one about the tool. */
  refresh() {
    this.readiness.clear();
    this.changed.fire();
  }

  /** A refresh somebody asked for: everything, because an upgrade is the thing that moved. */
  reread() {
    this.engine = null;
    this.refresh();
  }

  getTreeItem(row) {
    if (row.notice) {
      const item = new vscode.TreeItem(row.notice);
      item.iconPath = new vscode.ThemeIcon("warning");
      return item;
    }
    if (row.count) {
      const item = new vscode.TreeItem(row.count);
      item.description = row.detail;
      item.iconPath = new vscode.ThemeIcon("list-unordered");
      item.contextValue = "count";
      return item;
    }
    if (row.engine) {
      const item = new vscode.TreeItem(row.engine);
      item.description = row.detail;
      item.iconPath = new vscode.ThemeIcon("versions");
      item.contextValue = "engine";
      return item;
    }
    if (row.group) {
      const item = new vscode.TreeItem(
        row.group,
        vscode.TreeItemCollapsibleState.Expanded
      );
      item.description = `${row.tasks.length}`;
      item.contextValue = "block";
      return item;
    }
    const item = new vscode.TreeItem(`${row.status} ${row.id}  ${row.symptom}`);
    // What the page cannot say: whether this one can be started, and what to ship first if
    // it cannot. Both are the verb's words, never a judgement made here.
    item.description = row.blockers.length ? `waits on ${row.blockers.join(", ")}` : "";
    item.tooltip = row.why;
    item.iconPath = new vscode.ThemeIcon(row.blockers.length ? "circle-outline" : "circle-filled");
    item.command = {
      command: "vscode.open",
      title: "Reveal the line",
      arguments: [
        vscode.Uri.joinPath(vscode.Uri.file(this.root), ...this.file.split("/")),
        { selection: new vscode.Range(row.line - 1, 0, row.line - 1, 0) },
      ],
    };
    return item;
  }

  async getChildren(parent) {
    if (!parent) {
      return this.blocks();
    }
    if (parent.group) {
      return this.lines(parent.tasks);
    }
    return [];
  }

  /** The blocks, in the order the file declares them — which is the order a reader takes
   * for the shape of the plan, so it is the payload's and never sorted here. */
  async blocks() {
    const answer = await payload(this.root, ["list"]);
    if (answer.error) {
      // A message and never an empty tree: an empty list is a claim that the backlog is
      // empty, which is the one thing a failed read cannot know.
      return [{ notice: answer.error }];
    }
    // Which copy answered, above the rows it answered with (RK1009), asked once per window
    // rather than once per save (RK1017).
    if (this.engine === null) {
      const engines = await payload(this.root, ["engines"]);
      this.engine = engines.error
        ? { notice: engines.error }
        : {
            engine: `${engines.value.writing.version}  ${engines.value.verdict}`,
            detail: engines.value.writing.home,
          };
    }
    const said = this.engine;
    // How much work there is, above the blocks (RK1018). One more call where `engines` is
    // already made — but cached on the readiness map's terms and not the engine's: the
    // numbers are about the *file*, so a save invalidates them and an upgrade does not.
    const counted = await payload(this.root, ["stats"]);
    const header = counted.error
      ? { notice: counted.error }
      : { count: _counted(counted.value), detail: answer.value.file };
    this.file = answer.value.file;
    const grouped = new Map();
    for (const task of answer.value.tasks) {
      if (!grouped.has(task.block)) {
        grouped.set(task.block, []);
      }
      grouped.get(task.block).push(task);
    }
    return [
      said,
      header,
      ...[...grouped].map(([block, tasks]) => ({ group: block, tasks })),
    ];
  }

  /** One block's lines, each carrying what `deps` says about it, ready first.
   *
   * Concurrent and asked per block rather than for the whole backlog: what a reader opens
   * is what it costs, and a hundred-line roadmap is a hundred child processes if the answer
   * is fetched for rows nobody looked at. */
  async lines(tasks) {
    const asked = await Promise.all(
      tasks.map(async (task) => {
        if (!this.readiness.has(task.id)) {
          const answer = await payload(this.root, ["deps", task.id]);
          this.readiness.set(task.id, answer.error ? [] : answer.value.blockers);
        }
        return { ...task, blockers: this.readiness.get(task.id) };
      })
    );
    // Separated and not sorted by id: the order on the page is the file's, and the one that
    // matters here is whether a line can be started at all.
    return [...asked.filter((one) => !one.blockers.length), ...asked.filter((one) => one.blockers.length)];
  }
}

function activate(context) {
  const folder = vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders[0];
  if (!folder) {
    return;
  }
  const root = folder.uri.fsPath;
  const backlog = new Backlog(root);
  const diagnostics = vscode.languages.createDiagnosticCollection("roadkeep");
  const gate = new Gate(root, diagnostics);
  const settings = new Settings(root);
  const both = async () => {
    backlog.refresh();
    const said = await gate.check();
    return said;
  };
  // The store is the repository, so there is nothing else to observe: the file changing is
  // the whole of the event, and re-running the verbs is the whole of the response.
  const watcher = vscode.workspace.createFileSystemWatcher(
    new vscode.RelativePattern(folder, "**/*.md")
  );
  watcher.onDidChange(() => both());
  context.subscriptions.push(
    watcher,
    diagnostics,
    vscode.window.registerTreeDataProvider("roadkeep.backlog", backlog),
    vscode.languages.registerCodeActionsProvider({ scheme: "file" }, gate, {
      providedCodeActionKinds: [vscode.CodeActionKind.QuickFix],
    }),
    // Narrowed to the one file, by name and not by language: a workspace with no TOML
    // support installed still has this file, and every other TOML here is somebody else's.
    vscode.languages.registerCompletionItemProvider(
      { scheme: "file", pattern: "**/roadkeep.toml" },
      settings,
      "[",
    ),
    vscode.languages.registerHoverProvider(
      { scheme: "file", pattern: "**/roadkeep.toml" },
      settings,
    ),
    vscode.workspace.onDidSaveTextDocument(() => both()),
    // The button is the explicit ask, so it re-reads the engine too — an upgrade is what
    // moves that answer, and a person pressing refresh is the one who just did it.
    vscode.commands.registerCommand("roadkeep.refresh", () => {
      backlog.reread();
      // And the shape, for the same reason: what this build accepts moves when the engine
      // does, and a person pressing refresh is the one who just upgraded it.
      settings.reread();
      return both();
    }),
    vscode.commands.registerCommand("roadkeep.repair", async () => {
      // The one action that belongs to the file rather than to a line, and it exits
      // non-zero while anything is left — so a clean panel means clean.
      const said = await command(root, ["repair"]);
      vscode.window.showInformationMessage(said.error || said.output || "nothing to repair");
      await both();
    }),
    vscode.commands.registerCommand("roadkeep.run", async (argv) => {
      // Shown and then re-read, whichever it was. A door is not marked read or write — the
      // remedy's `kind` describes the *remedy*, and `deps.unknown` is one `decide` holding a
      // read and a write — so a reader that guessed would be inventing a field. What every
      // door does have is an answer worth showing, and re-judging a file nothing wrote is a
      // second run of a command that already costs nothing.
      const said = await command(root, argv);
      vscode.window.showInformationMessage(said.output || said.error || "done");
      await both();
    }),
    vscode.commands.registerCommand("roadkeep.add", async () => {
      if (await compose(root)) {
        await both();
      }
    }),
    vscode.commands.registerCommand("roadkeep.explain", async (code) => {
      const said = await command(root, ["explain", code]);
      vscode.window.showInformationMessage(said.output || said.error);
    })
  );
  // **Returned and not fired and forgotten**: an editor awaits what `activate` hands back, so
  // the view is populated before anything asks it a question — and a caller counting the
  // child processes this makes sees them all, rather than some of them landing after it
  // looked. An un-awaited promise here is a race in every reader of this surface, which is
  // how `tests/test_editor.py`'s own count first became flaky.
  return both();
}

function deactivate() {}

// `Backlog` and `Gate` are exported for `harness.js` and for nothing an editor calls: the
// two hooks above are the whole of the contract, and the providers are here because what is
// worth proving about this surface — grouped by block, blocked separated and named, a
// finding anchored at its column, an incomplete door offered to nobody — is not renderable
// and breaks silently.
module.exports = { activate, deactivate, Backlog, Gate, Settings, compose };
