// The host, which ships none of the rules (RK1011).
//
// Everything else this block proposes — a panel, a marker at a column, a prompt that knows a
// limit — is something inside a host that has to exist first: a manifest an editor
// recognises, an activation, a container in the sidebar, and one place that runs the command
// and turns a non-zero exit into a message. This is that and nothing more.
//
// Two properties decide whether it is right, and neither is about the view.
//
// It **activates on a governed workspace** — `workspaceContains:roadkeep.toml` in the
// manifest, not `*` and not every Markdown file — for the reason the write path is a
// trigger-loaded skill rather than a preamble (RK23): a surface that costs something on
// every session touching none of these files is paying for the sessions it does nothing in.
//
// And it **carries no rule**. No limit, no marker set, no id shape, no parser. Every fact
// below was read from a payload some verb printed, and `tests/test_editor.py` holds that: a
// literal marker, id or governed filename in this file is a rule compiled into a reader,
// which is L6 broken from the outside instead of the inside.
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
 * files and a reader disagreeing with it is the defect `engines` exists to name (RK79).
 * Then the console script, then the checkout — which is how this repository itself runs the
 * tool, and it has no installed entry point at all.
 */
function candidates(folder) {
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
 * Never throws for a non-zero exit: `lint` answers *and* exits 1 (RK271), so a reader that
 * treated a code as no output would drop the findings it was asked for. The two failures a
 * child process really has — not installed, and refused — are the ones the caller reports.
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
          code: error && typeof error.code === "number" ? error.code : error ? -1 : 0,
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
  for (const command of candidates(cwd)) {
    const said = await run([...command, ...argv, "--json"], cwd);
    tried.push(command.join(" "));
    if (said.missing) {
      continue;
    }
    if (!said.stdout.trim()) {
      return { error: said.stderr.trim() || `\`${tried[tried.length - 1]}\` printed nothing` };
    }
    try {
      return { value: JSON.parse(said.stdout) };
    } catch (_) {
      return { error: `\`${tried[tried.length - 1]}\` did not answer JSON` };
    }
  }
  return { error: `no roadkeep here — tried ${tried.join(", ")}` };
}

/**
 * The backlog as rows, read from `list --json` and never from the file.
 *
 * The fields are the ones RK1005 wrote down as promised, which is the whole of what this
 * reader may depend on: a key it reads and that test does not is a key free to move under it.
 */
class Backlog {
  constructor(root) {
    this.root = root;
    this.changed = new vscode.EventEmitter();
    this.onDidChangeTreeData = this.changed.event;
    this.said = "";
  }

  refresh() {
    this.changed.fire();
  }

  getTreeItem(row) {
    if (row.notice) {
      const item = new vscode.TreeItem(row.notice);
      item.iconPath = new vscode.ThemeIcon("warning");
      return item;
    }
    const item = new vscode.TreeItem(`${row.status} ${row.id}  ${row.symptom}`);
    item.description = `Block ${row.block}`;
    item.tooltip = row.why;
    item.command = {
      command: "vscode.open",
      title: "Open the line",
      arguments: [vscode.Uri.file(`${this.root}/${this.file}`)],
    };
    return item;
  }

  async getChildren(parent) {
    if (parent) {
      return [];
    }
    const answer = await payload(this.root, ["list"]);
    if (answer.error) {
      // A message and never an empty tree: an empty list is a claim that the backlog is
      // empty, which is the one thing a failed read cannot know.
      return [{ notice: answer.error }];
    }
    this.file = answer.value.file;
    return answer.value.tasks;
  }
}

function activate(context) {
  const folder = vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders[0];
  if (!folder) {
    return;
  }
  const backlog = new Backlog(folder.uri.fsPath);
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider("roadkeep.backlog", backlog),
    vscode.commands.registerCommand("roadkeep.refresh", () => backlog.refresh())
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
