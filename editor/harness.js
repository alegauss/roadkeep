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
      constructor(startLine, startColumn, endLine, endColumn) {
        this.start = { line: startLine, character: startColumn };
        this.end = { line: endLine, character: endColumn };
      }
    },
    Uri: {
      file: (fsPath) => ({ fsPath }),
      // A virtual document's address (RK1754): the scheme and the path are all it carries.
      parse: (spelled) => {
        const at = spelled.indexOf(":");
        return { scheme: spelled.slice(0, at), path: spelled.slice(at + 1) };
      },
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
      createFileSystemWatcher: () => ({
        onDidChange() {},
        // RK1277. The config's watcher takes a creation too — a project declaring its first
        // `[budgets]` is a file that appears rather than one that changes.
        onDidCreate() {},
        dispose() {},
      }),
      onDidSaveTextDocument: () => ({ dispose() {} }),
      registerTextDocumentContentProvider: () => ({ dispose() {} }),
    },
    Diagnostic: class {
      constructor(range, message, severity) {
        Object.assign(this, { range, message, severity });
      }
    },
    DiagnosticSeverity: { Error: 0 },
    CodeAction: class {
      constructor(title, kind) {
        Object.assign(this, { title, kind });
      }
    },
    CodeActionKind: { QuickFix: "quickfix" },
    // What the config providers hand back (RK1271). Recorded rather than drawn, for the
    // reason the tree is: what a completion *offers* is not renderable and breaks silently.
    CompletionItem: class {
      constructor(label, kind) {
        Object.assign(this, { label, kind });
      }
    },
    CompletionItemKind: { Property: 9 },
    MarkdownString: class {
      constructor(value) {
        this.value = value;
      }
    },
    Hover: class {
      constructor(contents, range) {
        Object.assign(this, { contents, range });
      }
    },
    languages: {
      createDiagnosticCollection: () => ({
        entries: new Map(),
        clear() {
          this.entries.clear();
        },
        set(uri, found) {
          this.entries.set(uri.fsPath, found);
        },
        dispose() {},
      }),
      registerCodeActionsProvider: () => ({ dispose() {} }),
      registerCompletionItemProvider: () => ({ dispose() {} }),
      registerHoverProvider: () => ({ dispose() {} }),
    },
    StatusBarAlignment: { Left: 1, Right: 2 },
    window: {
      registerTreeDataProvider() {},
      // A view and a status bar item record what they were told (RK1755): the header and the
      // engine are where the status went when it left the rows.
      createTreeView: () => ({ dispose() {} }),
      createStatusBarItem: () => ({ show() {}, hide() {}, dispose() {} }),
      // Every message is kept rather than shown: what the write door is judged on is the
      // refusal it reports, and a stub that swallowed it would prove nothing.
      said: [],
      showInformationMessage(text) {
        this.said.push(text);
      },
      showErrorMessage(text) {
        this.said.push(text);
      },
      showQuickPick: (items) => Promise.resolve(items[Number(process.env.ROADKEEP_PICK || 0)]),
      // The prompts are recorded as they change, because the budget counting down beside
      // the words is the whole of RK1008 and it exists only in that string.
      prompts: [],
      createInputBox() {
        const window = this;
        const typed = JSON.parse(process.env.ROADKEEP_TYPED || "[]");
        const value = typed[window.prompts.length] || "";
        return {
          value: "",
          onDidChangeValue(listener) {
            this.changed = listener;
          },
          onDidAccept(listener) {
            this.accepted = listener;
          },
          onDidHide() {},
          hide() {},
          dispose() {},
          show() {
            this.value = value;
            this.changed();
            window.prompts.push(this.prompt);
            this.accepted();
          },
        };
      },
    },
    commands: {
      registerCommand: () => ({ dispose() {} }),
      executeCommand: () => Promise.resolve(),
    },
  };
}

const editor = stub();
const load = Module._load;
Module._load = function (request, parent, isMain) {
  return request === "vscode" ? editor : load(request, parent, isMain);
};

async function main() {
  const root = process.argv[2];
  const extension = require("./extension.js");
  const { activate, Backlog, Gate, Settings, compose } = extension;
  // `activate` is exercised for what it wires — a stub with no window records the calls and
  // hands nothing back, so the provider under test is built directly.
  editor.workspace.workspaceFolders = [{ uri: editor.Uri.file(root) }];
  await activate({ subscriptions: [] });

  const backlog = new Backlog(root);
  // `rows` is what kind each top-level row is, so a test can say what the top of the tree
  // holds without a second read (RK1755).
  const out = { blocks: [], rows: [] };
  for (const block of await backlog.getChildren()) {
    out.rows.push(Object.keys(block)[0]);
    if (block.notice) {
      out.notice = block.notice;
      continue;
    }
    const children = await backlog.getChildren(block);
    const rows = children.filter((row) => !row.pauses);
    // The deferred node, opened the way a reader opens it (RK1752): what each row says and
    // where selecting it goes, both of which are the payload's and neither of which draws.
    const pauses = [];
    for (const node of children.filter((row) => row.pauses)) {
      for (const row of await backlog.getChildren(node)) {
        const item = backlog.getTreeItem(row);
        pauses.push({
          id: row.paused.id,
          label: item.label,
          description: item.description,
          tooltip: item.tooltip,
          context: item.contextValue,
          opens: item.command.arguments[0].fsPath,
          line: item.command.arguments[1].selection.start.line,
        });
      }
    }
    out.blocks.push({
      group: block.group,
      description: backlog.getTreeItem(block).description,
      rows: rows.map((row) => ({ id: row.id, blockers: row.blockers })),
      label: backlog.getTreeItem(block).label,
      tooltip: backlog.getTreeItem(block).tooltip,
      pauses,
    });
  }
  // The view's own status, which left the rows for the header and the status bar (RK1755):
  // read where the tree put it, in the shape the rows used to carry.
  const status = backlog.status;
  if (status.engine) {
    out.engine = { label: status.engine.engine, detail: status.engine.detail };
  }
  if (status.count) {
    out.count = { label: status.count.count, detail: status.count.detail };
  }

  if (process.env.ROADKEEP_FIND) {
    // The designs view, searched the way the find command searches it (RK1755).
    const designs = new extension.Designs(root);
    const rows = await designs.search(process.env.ROADKEEP_FIND);
    out.found = {
      total: designs.total,
      rows: rows.map((row) => {
        const item = designs.getTreeItem(row);
        return {
          label: item.label,
          description: item.description,
          argv: item.command ? item.command.arguments : null,
        };
      }),
    };
    if (rows.length && rows[0].carrier) {
      const first = rows[0].carrier;
      const design = new extension.Design(root);
      out.found.opened = await design.provideTextDocumentContent(
        design.uri(first.anchor, first.role)
      );
    }
  }

  if (process.env.ROADKEEP_SHIPPED) {
    // The ledger view, every block opened the way a reader opens one (RK1756).
    const shipped = new extension.Shipped(root);
    out.shipped = [];
    for (const head of await shipped.getChildren()) {
      if (head.notice) {
        out.shipped.push({ notice: head.notice });
        continue;
      }
      const entries = await shipped.getChildren(head);
      out.shipped.push({
        label: shipped.getTreeItem(head).label,
        description: shipped.getTreeItem(head).description,
        entries: entries.map((row) => {
          const item = shipped.getTreeItem(row);
          return {
            id: row.entry.id,
            context: item.contextValue,
            opens: item.command.arguments[0].fsPath,
            line: item.command.arguments[1].selection.start.line,
          };
        }),
      });
    }
  }

  // The gate half: findings become diagnostics anchored where the report points, and a
  // door the tool marked incomplete is offered to nobody.
  const collection = editor.languages.createDiagnosticCollection();
  const gate = new Gate(root, collection);
  out.gate = { notice: await gate.check(), files: [] };
  for (const [file, found] of collection.entries) {
    out.gate.files.push({
      file: path.relative(root, file).split(path.sep).join("/"),
      found: found.map((one) => ({
        code: one.code,
        line: one.range.start.line,
        column: one.range.start.character,
        source: one.source,
      })),
    });
    for (const said of found) {
      const actions = gate.provideCodeActions(
        { uri: { fsPath: file } },
        said.range,
        { diagnostics: [said] }
      );
      out.gate.actions = (out.gate.actions || []).concat(
        actions.map((one) => ({ code: said.code, title: one.title, argv: one.command.arguments }))
      );
    }
  }

  if (process.env.ROADKEEP_SETTINGS) {
    // The half before the save (RK1271). A document is stubbed rather than opened: what is
    // under test is which rows the provider picks for a position, and a real editor buffer
    // would add a file format this surface deliberately does not parse.
    const lines = JSON.parse(process.env.ROADKEEP_SETTINGS);
    const document = {
      lineAt: (at) => ({ text: lines[at] }),
      getText: (range) => range.word,
      getWordRangeAtPosition: (position) => ({ word: lines[position.line].trim() }),
    };
    const settings = new Settings(root);
    const at = lines.length - 1;
    const offered = await settings.provideCompletionItems(document, { line: at });
    const hovered = await settings.provideHover(document, { line: at });
    out.settings = {
      table: settings.table(document, at),
      offered: offered.map((one) => ({
        label: one.label,
        inserted: one.insertText,
        detail: one.detail,
        documentation: one.documentation ? one.documentation.value : "",
      })),
      hover: hovered ? hovered.contents.value : null,
    };
    if (process.env.ROADKEEP_REDECLARED) {
      // RK1277. The config is written *after* the shape was read, and the cache is dropped
      // the way a save of that file drops it — so what the second reading answers is whether
      // the two facts in one payload are now on the same clock.
      const fs = require("fs");
      fs.appendFileSync(
        path.join(root, "roadkeep.toml"),
        process.env.ROADKEEP_REDECLARED,
        "utf8"
      );
      out.settings.stale = (await settings.provideHover(document, { line: at })).contents.value;
      settings.reread();
      out.settings.fresh = (await settings.provideHover(document, { line: at })).contents.value;
      // And which saves drop it, which is the half that keeps RK1017's cost off a keystroke.
      out.settings.declares = {
        config: extension.declares({ uri: { fsPath: path.join(root, "roadkeep.toml") } }),
        prose: extension.declares({ uri: { fsPath: path.join(root, "docs", "ROADMAP.md") } }),
      };
    }
  }

  if (process.env.ROADKEEP_DESIGN) {
    // A line's design, read the three ways a reader meets it (RK1754): the preview behind the
    // action, the document the virtual address resolves to, and the hover on the row.
    const id = process.env.ROADKEEP_DESIGN;
    const design = new extension.Design(root);
    const read = await design.read(id);
    const hovered = new Backlog(root, undefined, design);
    const item = await hovered.resolveTreeItem(
      { tooltip: "" },
      { id, why: "the reason on the line" }
    );
    out.design = {
      read,
      document: await design.provideTextDocumentContent(design.uri(id)),
      scheme: design.uri(id).scheme,
      tooltip: item.tooltip.value,
    };
  }

  if (process.env.ROADKEEP_CYCLES) {
    // A save and then an explicit refresh, so a caller counting the child processes can see
    // which reads each one makes (RK1017). Nothing is asserted here — the log is the answer.
    backlog.refresh();
    await backlog.getChildren();
    backlog.reread();
    await backlog.getChildren();
  }

  if (process.env.ROADKEEP_TYPED) {
    out.wrote = await compose(root);
    out.prompts = editor.window.prompts;
    out.said = editor.window.said;
  }

  process.stdout.write(JSON.stringify(out));
}

main().catch((error) => {
  process.stdout.write(JSON.stringify({ notice: String(error) }));
});
