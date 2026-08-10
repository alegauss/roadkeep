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
  const backlog = new Backlog(folder.uri.fsPath);
  // The store is the repository, so there is nothing else to observe: the file changing is
  // the whole of the event, and re-running the verbs is the whole of the response.
  const watcher = vscode.workspace.createFileSystemWatcher(
    new vscode.RelativePattern(folder, "**/*.md")
  );
  watcher.onDidChange(() => backlog.refresh());
  context.subscriptions.push(
    watcher,
    vscode.window.registerTreeDataProvider("roadkeep.backlog", backlog),
    vscode.commands.registerCommand("roadkeep.refresh", () => backlog.refresh())
  );
}

function deactivate() {}

// `Backlog` is exported for `harness.js` and for nothing an editor calls: the two hooks
// above are the whole of the contract, and the provider is here because the two properties
// worth proving about this surface — grouped by block, blocked separated and named — are
// not renderable and break silently.
module.exports = { activate, deactivate, Backlog };
