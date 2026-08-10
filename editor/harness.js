// Run the host's tree against a real roadkeep, with the editor stubbed (RK1006).
//
// The two things worth proving about this surface are not renderable: that the rows are
// **grouped by the block the payload gave** and that a blocked line is **separated and
// carries its blocker**. Neither is visible to a Python test reading the source, and both
// break silently — a tree that groups wrong still draws.
//
// So the editor is stubbed and the tool is not. `child_process` is the real one, the verbs
// are the real ones, and the workspace is whatever path is passed in: what this exercises is
// the client's own reading of two payloads, which is the only part of it this tree owns.
//
// Prints one JSON document on stdout, for `tests/test_editor.py` to assert against — the
// same arrangement every other surface here has, where the thing that cannot explain itself
// is checked from the language the rest of the suite is written in.
"use strict";

const path = require("path");
const Module = require("module");

/** The smallest editor an activation touches, with every call recorded rather than drawn. */
function stub() {
  class EventEmitter {
    constructor() {
      this.event = () => ({ dispose() {} });
    }
    fire() {}
  }
  class TreeItem {
    constructor(label, state) {
      this.label = label;
      this.collapsibleState = state;
    }
  }
  return {
    EventEmitter,
    TreeItem,
    TreeItemCollapsibleState: { Expanded: 2, Collapsed: 1 },
    ThemeIcon: class {
      constructor(id) {
        this.id = id;
      }
    },
    Range: class {
      constructor(line) {
        this.line = line;
      }
    },
    Uri: {
      file: (fsPath) => ({ fsPath }),
      joinPath: (base, ...parts) => ({ fsPath: path.join(base.fsPath, ...parts) }),
    },
    RelativePattern: class {
      constructor(folder, glob) {
        this.glob = glob;
      }
    },
    workspace: {
      workspaceFolders: undefined,
      getConfiguration: () => ({ get: () => process.env.ROADKEEP_COMMAND || "" }),
      createFileSystemWatcher: () => ({ onDidChange() {}, dispose() {} }),
    },
    window: { registerTreeDataProvider() {} },
    commands: { registerCommand() {} },
  };
}

const editor = stub();
const load = Module._load;
Module._load = function (request, parent, isMain) {
  return request === "vscode" ? editor : load(request, parent, isMain);
};

async function main() {
  const root = process.argv[2];
  const { activate, Backlog } = require("./extension.js");
  // `activate` is exercised for what it wires — a stub with no window records the calls and
  // hands nothing back, so the provider under test is built directly.
  editor.workspace.workspaceFolders = [{ uri: editor.Uri.file(root) }];
  activate({ subscriptions: [] });

  const backlog = new Backlog(root);
  const out = { blocks: [] };
  for (const block of await backlog.getChildren()) {
    if (block.notice) {
      out.notice = block.notice;
      continue;
    }
    const rows = await backlog.getChildren(block);
    out.blocks.push({
      group: block.group,
      rows: rows.map((row) => ({ id: row.id, blockers: row.blockers })),
      label: backlog.getTreeItem(block).label,
    });
  }
  process.stdout.write(JSON.stringify(out));
}

main().catch((error) => {
  process.stdout.write(JSON.stringify({ notice: String(error) }));
});
