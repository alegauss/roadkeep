import { Fragment, type CSSProperties, type ReactNode } from "react";
import type { Terminal as Transcript, TermLine, TermRun } from "../../lib/site-content";

// A captured transcript, rendered from the run list the content module holds rather than from
// a `<pre>` somebody edits with the highlighting spans in it. The classes are the page's own
// terminal palette: `g` a verb, `c` a comment, `no` a refusal, `ok` a success, `dim` an exit
// code or an aside.
//
// The whole block is one `<pre>`, which is what the Markdown twin converts into a fence: the
// generator reads `.term pre` and strips the spans, so a colour here never reaches a reader
// who asked for the flat file.
function TermRunNode({ run }: { run: TermRun }): ReactNode {
  if (typeof run === "string") return run;
  if ("g" in run) return <span className="g">{run.g}</span>;
  if ("c" in run) return <span className="c">{run.c}</span>;
  if ("no" in run) return <span className="no">{run.no}</span>;
  if ("ok" in run) return <span className="ok">{run.ok}</span>;
  if ("dim" in run) return <span className="dim">{run.dim}</span>;
  return <b>{run.b}</b>;
}

export function Lines({ lines }: { lines: readonly TermLine[] }) {
  return (
    <>
      {lines.map((line, i) => (
        <Fragment key={i}>
          {line.map((run, j) => (
            <TermRunNode key={j} run={run} />
          ))}
          {i < lines.length - 1 ? "\n" : null}
        </Fragment>
      ))}
    </>
  );
}

export function Terminal({
  transcript,
  className,
  style,
}: {
  transcript: Transcript;
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <div className={className ? `term ${className}` : "term"} style={style}>
      <div className="term-bar">
        <i />
        <i />
        <i />
        <span className="t">{transcript.title}</span>
      </div>
      <pre>
        <Lines lines={transcript.lines} />
      </pre>
    </div>
  );
}
