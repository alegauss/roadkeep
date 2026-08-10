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
 * The argv that runs roadkeep here, in the order a workspace is most likely to answer.
 *
 * Configuration first, because a project that declared one has said which copy writes its
 * files and a reader disagreeing with it is the defect `engines` exists to name. Then the
 * console script, then the checkout — which is how this repository itself runs the tool, and
 * it has no installed entry point at all.
 */
function candidates() {
  const declared = vscode.workspace.getConfiguration("roadkeep").get("command");
  const found = [];
  if (declared) {
    found.push(declared.split(" "));
  }
  found.push(["roadkeep"]);
  found.push(["python", "-m", "roadkeep.cli"]);
  return found;
}

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
  const tried = [];
  for (const command of candidates()) {
    const said = await run([...command, ...argv, "--json"], cwd);
    tried.push(command.join(" "));
    if (said.missing) {
      continue;
    }
    const spelled = tried[tried.length - 1];
    if (!said.stdout.trim()) {
      return { error: said.stderr.trim() || `\`${spelled}\` printed nothing` };
    }
    try {
      return { value: JSON.parse(said.stdout) };
    } catch (_) {
      return { error: `\`${spelled}\` did not answer JSON` };
    }
  }
  return { error: `no roadkeep here — tried ${tried.join(", ")}` };
}

/**
 * Run one command for its effect rather than its payload — a repair, or a door.
 *
 * Separate from `payload` because what a caller does with the two differs: this one is
 * reported to the person who pressed something, and its exit code is the tool's own verdict.
 */
async function command(cwd, argv) {
  for (const found of candidates()) {
    const said = await run([...found, ...argv], cwd);
    if (said.missing) {
      continue;
    }
    return { output: said.stdout.trim(), error: said.stderr.trim() };
  }
  return { error: "no roadkeep here" };
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
  }

  refresh() {
    this.readiness.clear();
    this.changed.fire();
  }

  getTreeItem(row) {
    if (row.notice) {
      const item = new vscode.TreeItem(row.notice);
      item.iconPath = new vscode.ThemeIcon("warning");
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
    this.file = answer.value.file;
    const grouped = new Map();
    for (const task of answer.value.tasks) {
      if (!grouped.has(task.block)) {
        grouped.set(task.block, []);
      }
      grouped.get(task.block).push(task);
    }
    return [...grouped].map(([block, tasks]) => ({ group: block, tasks }));
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
    vscode.workspace.onDidSaveTextDocument(() => both()),
    vscode.commands.registerCommand("roadkeep.refresh", () => both()),
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
    vscode.commands.registerCommand("roadkeep.explain", async (code) => {
      const said = await command(root, ["explain", code]);
      vscode.window.showInformationMessage(said.output || said.error);
    })
  );
  both();
}

function deactivate() {}

// `Backlog` and `Gate` are exported for `harness.js` and for nothing an editor calls: the
// two hooks above are the whole of the contract, and the providers are here because what is
// worth proving about this surface — grouped by block, blocked separated and named, a
// finding anchored at its column, an incomplete door offered to nobody — is not renderable
// and breaks silently.
module.exports = { activate, deactivate, Backlog, Gate };
