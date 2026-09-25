; The Claude Code half of the install (RK1700), run after the app is placed.
;
; The reader and the plugin were two procedures: this installer placed the app, and a person
; then ran `claude plugin marketplace add alegauss/roadkeep` and `claude plugin install
; roadkeep@alegauss` by hand. This runs those two commands, and nothing else: the plugin's
; files are the `claude` CLI's to place and to update, never copied from here, so an update to
; the plugin stays Claude Code's.
;
; Asked and never assumed. The step is offered only where `claude` answers on PATH, a person can
; decline it, and a silent install (`/S`) skips it: an unattended install that reached out to a
; marketplace would be doing a thing nobody watching it asked for. Declining, a missing CLI or a
; failed command all leave the app installed and working as a reader of projects whose engine is
; already present — the outcome is written to the install log either way.
;
; **What the plugin needs is named before it is offered** (RK1701). Its MCP server is
; `python scripts/roadkeep.py mcp`, so a machine without Python 3.11 got a plugin that installed
; and failed on its first call, far from the cause. Both prerequisites are checked first; a
; missing one is said, with where to get it, and the step is skipped. Neither is installed here.

!define ROADKEEP_PYTHON_URL "https://www.python.org/downloads/"
!define ROADKEEP_CLAUDE_URL "https://docs.claude.com/en/docs/claude-code/setup"

!macro customInstall
  IfSilent roadkeep_plugin_done

  nsExec::ExecToStack 'cmd /c python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"'
  Pop $0
  Pop $1
  StrCmp $0 "0" roadkeep_python_ok
  DetailPrint "roadkeep: Python 3.11 or newer is not on PATH, so the Claude Code plugin was not installed"
  MessageBox MB_OK|MB_ICONINFORMATION "The roadkeep plugin for Claude Code needs Python 3.11 or newer on PATH, and none answered, so the plugin was not installed.$\r$\n$\r$\nGet Python from ${ROADKEEP_PYTHON_URL}, then run:$\r$\n  claude plugin marketplace add alegauss/roadkeep$\r$\n  claude plugin install roadkeep@alegauss"
  Goto roadkeep_plugin_done

  roadkeep_python_ok:
  nsExec::ExecToStack 'cmd /c where claude'
  Pop $0
  Pop $1
  StrCmp $0 "0" roadkeep_plugin_ask
  DetailPrint "roadkeep: the claude CLI is not on PATH, so the Claude Code plugin was not installed"
  MessageBox MB_OK|MB_ICONINFORMATION "The roadkeep plugin installs through the claude CLI, which is not on PATH, so the plugin was not installed.$\r$\n$\r$\nClaude Code is set up as ${ROADKEEP_CLAUDE_URL} describes."
  Goto roadkeep_plugin_done

  roadkeep_plugin_ask:
  MessageBox MB_YESNO|MB_ICONQUESTION "Also install the roadkeep plugin into Claude Code?$\r$\n$\r$\nThis runs:$\r$\n  claude plugin marketplace add alegauss/roadkeep$\r$\n  claude plugin install roadkeep@alegauss" IDYES roadkeep_plugin_run
  DetailPrint "roadkeep: the Claude Code plugin was declined"
  Goto roadkeep_plugin_done

  roadkeep_plugin_run:
  nsExec::ExecToLog 'cmd /c claude plugin marketplace add alegauss/roadkeep'
  Pop $0
  nsExec::ExecToLog 'cmd /c claude plugin install roadkeep@alegauss'
  Pop $0
  StrCmp $0 "0" roadkeep_plugin_installed
  DetailPrint "roadkeep: claude plugin install exited $0; the app is installed without the plugin"
  Goto roadkeep_plugin_done

  roadkeep_plugin_installed:
  DetailPrint "roadkeep: the Claude Code plugin is installed"

  roadkeep_plugin_done:
!macroend
