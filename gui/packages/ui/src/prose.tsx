import type { ComponentProps, ReactNode } from 'react'
import Markdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { useWording } from './wording'

/**
 * What an agent wrote for a person to read, rendered (RG271).
 *
 * **Rendered where a person reads, raw where a tool measures.** An agent writes Markdown for a
 * terminal that renders it, and drawn as characters its bold is asterisks and its choices are a
 * list to decode. `No Markdown parsed in this app` is about facts read off a governed file, and
 * nothing is read out of these words: this draws them and keeps nothing. So a session's words and
 * its last word come through here, and every surface a gate measures, a commit diffs, a line
 * number points into or a verb reads back stays raw — a tool call's input and output, a file in
 * the viewer, a design section, a symptom, a why, the raw line.
 *
 * **It reaches for nothing.** No raw HTML is rendered, since the words are a program's and HTML
 * in them is a page this window would be running. No image is fetched: an image is drawn as its
 * description, since a stream that loads a URL an agent wrote is a request nobody chose to make.
 * A link opens in its own window, which the shell's guard turns into the desktop's browser for
 * the schemes it allows and into nothing for the rest.
 *
 * **In the design system's type, in either ground.** Every element takes this app's tokens rather
 * than a stylesheet of its own, and a wide code block scrolls inside the stream rather than
 * pushing the page sideways. A heading is drawn as a strong paragraph: the page's outline is the
 * screen's, and an agent's `#` is emphasis inside one act, not a section of this window.
 */

const COMPONENTS: Components = {
  p: ({ node: _node, ...props }) => <p className="my-1.5 first:mt-0 last:mb-0" {...props} />,
  strong: ({ node: _node, ...props }) => <strong className="font-semibold" {...props} />,
  em: ({ node: _node, ...props }) => <em className="italic" {...props} />,
  ul: ({ node: _node, ...props }) => <ul className="my-1.5 list-disc pl-5" {...props} />,
  ol: ({ node: _node, ...props }) => <ol className="my-1.5 list-decimal pl-5" {...props} />,
  li: ({ node: _node, ...props }) => <li className="my-0.5" {...props} />,
  h1: ({ node: _node, ...props }) => <p className="mt-3 mb-1 font-semibold" {...props} />,
  h2: ({ node: _node, ...props }) => <p className="mt-3 mb-1 font-semibold" {...props} />,
  h3: ({ node: _node, ...props }) => <p className="mt-2 mb-1 font-semibold" {...props} />,
  h4: ({ node: _node, ...props }) => <p className="mt-2 mb-1 font-medium" {...props} />,
  h5: ({ node: _node, ...props }) => <p className="mt-2 mb-1 font-medium" {...props} />,
  h6: ({ node: _node, ...props }) => <p className="mt-2 mb-1 font-medium" {...props} />,
  blockquote: ({ node: _node, ...props }) => (
    <blockquote className="text-muted-foreground my-1.5 border-l-2 pl-3" {...props} />
  ),
  code: ({ node: _node, className, ...props }) =>
    // A fenced block names its language in the class; inline code does not.
    typeof className === 'string' && className.startsWith('language-') ? (
      <code className={`font-mono ${className}`} {...props} />
    ) : (
      <code className="bg-muted rounded px-1 py-0.5 font-mono text-[12px]" {...props} />
    ),
  pre: ({ node: _node, ...props }) => (
    <Scrolls>
      <pre className="bg-muted rounded p-2 font-mono text-[12px] leading-snug" {...props} />
    </Scrolls>
  ),
  table: ({ node: _node, ...props }) => (
    <Scrolls>
      <table className="text-[12px]" {...props} />
    </Scrolls>
  ),
  th: ({ node: _node, ...props }) => (
    <th className="border-b px-2 py-1 text-left font-semibold" {...props} />
  ),
  td: ({ node: _node, ...props }) => <td className="border-b px-2 py-1" {...props} />,
  hr: ({ node: _node, ...props }) => <hr className="my-3" {...props} />,
  a: ({ node: _node, href, children }) => (
    <a className="underline" href={href} target="_blank" rel="noreferrer noopener">
      {children}
    </a>
  ),
  // Drawn as what it describes, and never loaded.
  img: ({ alt }) => <span className="text-muted-foreground">{alt ?? ''}</span>,
  input: ({ checked }) => <TaskMark done={checked === true} />,
}

/**
 * What may be wider than the stream, scrolled inside it: a code block, a table. A tab stop, since a
 * region only a pointer can scroll is one a keyboard never reads the end of.
 */
function Scrolls({ children }: { readonly children: ReactNode }) {
  const say = useWording()
  return (
    <section
      className="my-2 max-w-full overflow-x-auto rounded"
      tabIndex={0}
      aria-label={say('session.prose.wide')}
    >
      {children}
    </section>
  )
}

/**
 * A task list's box, as a mark rather than a control: nothing here can tick it, and an unlabelled
 * disabled checkbox is one a screen reader announces with nothing to say about it.
 */
function TaskMark({ done }: { readonly done: boolean }) {
  const say = useWording()
  return (
    <>
      <span
        aria-hidden="true"
        className="mr-1.5 inline-block size-3 translate-y-px rounded-sm border align-baseline data-[done=true]:bg-current"
        data-done={done}
      />
      <span className="sr-only">
        {say(done ? 'session.prose.task.done' : 'session.prose.task.open')}
      </span>
    </>
  )
}

const PLUGINS: ComponentProps<typeof Markdown>['remarkPlugins'] = [remarkGfm]

export function Prose({ text }: { readonly text: string }) {
  return (
    <div className="text-[13px] leading-relaxed wrap-anywhere" data-testid="prose">
      <Markdown remarkPlugins={PLUGINS} components={COMPONENTS} skipHtml>
        {text}
      </Markdown>
    </div>
  )
}
