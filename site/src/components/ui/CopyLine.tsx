import { useEffect, useRef, useState, type CSSProperties } from "react";

/**
 * A command with a button that copies it.
 *
 * The command is the element's own text, never a second copy held for the clipboard: a button
 * that pastes a string the reader cannot see is one that can paste a different command than
 * the one on screen. The clipboard API is unavailable on an insecure origin and in some
 * embedded views, so there is a `execCommand` fallback behind it — and if both are gone the
 * command is still selectable text, which is what it was before there was a button.
 *
 * The label reverts on a timer, and the timer is cleared on unmount so a copy on a page being
 * left does not set state on a component that is gone.
 */
export function CopyLine({ command, style }: { command: string; style?: CSSProperties }) {
  const [copied, setCopied] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current);
  }, []);

  function flash() {
    setCopied(true);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => setCopied(false), 1800);
  }

  function fallback() {
    const ta = document.createElement("textarea");
    ta.value = command;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand("copy");
      flash();
    } catch {
      /* no clipboard route left: the command is on screen to select by hand */
    }
    ta.remove();
  }

  function copy() {
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(command).then(flash).catch(fallback);
    } else {
      fallback();
    }
  }

  return (
    <div className="copyline" style={style}>
      <code data-copy="">{command}</code>
      <button
        className={copied ? "copy-btn copied" : "copy-btn"}
        type="button"
        aria-label="Copy command"
        onClick={copy}
      >
        <span className="ic">{copied ? "✓" : "⧉"}</span>
        <span className="lbl">{copied ? "Copied!" : "Copy"}</span>
      </button>
    </div>
  );
}
