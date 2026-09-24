// The depth pages, one record each. The route table, the page metadata, the landing index and
// the pages themselves all read this list, so a page cannot exist without a route or a route
// without a title.
import type { Rich } from './site-content'
import { joined, product, spelled, writeCount, readCount } from './product'

export interface FeatureSection {
  readonly heading: string
  readonly body?: Rich
  readonly list?: readonly Rich[]
}

export interface FeatureRecord {
  readonly slug: string
  readonly title: string
  readonly description: string
  readonly ogTitle: string
  readonly ogDescription: string
  readonly eyebrow: string
  readonly heading: string
  readonly lead: Rich
  readonly sections: readonly FeatureSection[]
}

export const features: readonly FeatureRecord[] = [
  {
    slug: 'portfolio',
    title: 'roadkeep-gui: the portfolio, every backlog in one list',
    description:
      'One row per governed project: what is open, what is startable, the next ready line, the gate and the engine that answered. Filtered, sorted and searched without a number the app invented.',
    ogTitle: 'The portfolio',
    ogDescription:
      'Every governed project on this machine, one row each, read off what roadkeep printed.',
    eyebrow: 'The portfolio',
    heading: 'Every governed project on this machine, one row each',
    lead: [
      'The screen the window opens on. It answers the question a person has before choosing a repository: where is there work that can start, and where is something wrong.',
    ],
    sections: [
      {
        heading: 'Five columns, each one a verb’s answer',
        body: [
          'Project, backlog, next ready line, gate and engine. The backlog is what the project’s ',
          { code: 'stats' },
          ' counted, the next line is what its ',
          { code: 'pick' },
          ' chose, and the gate is the last verdict its ',
          { code: 'lint' },
          ' returned, shown as unknown until one has run rather than assumed clean. None of them is a figure the window worked out, and nothing is summed across projects, because a total nobody’s roadkeep printed is one nobody can check.',
        ],
      },
      {
        heading: 'Filters for the rows that need you',
        list: [
          [{ b: 'Gate drifted' }, ': projects whose files no longer pass their own gate'],
          [
            { b: 'Engine disagrees' },
            ': projects answered by a different roadkeep from the one they declare',
          ],
          [{ b: 'Unreadable' }, ': projects no engine could answer for, each with the reason'],
          [
            { b: 'Sort' },
            ': by name either way, or by open lines, and the order you chose is kept for next time',
          ],
        ],
      },
      {
        heading: 'Worktrees, and the last launch',
        body: [
          'Worktrees of one repository are grouped, found by reading git’s own files rather than by running git. Readings are cached between launches, so the list opens on what was true last time, marked as such, while every project is asked again.',
        ],
      },
      {
        heading: 'Find a line in every backlog',
        body: [
          'The command palette searches the payloads already in memory, across every project, and does not rank them: an order is a claim about relevance that no roadkeep made.',
        ],
      },
    ],
  },
  {
    slug: 'project',
    title: 'roadkeep-gui: one project, its files, its gate and its lines',
    description:
      'One backlog as rows, filtered by the engine, with a tab per governed file, the gate with the fix roadkeep offers for each finding, and a task screen joined by brief.',
    ogTitle: 'One project',
    ogDescription:
      'The backlog as rows, a tab per governed file, the gate and its fixes, and the task a brief describes.',
    eyebrow: 'One project',
    heading: 'A backlog read as rows, and nothing parsed',
    lead: [
      'Open a row and the project fills the window: its lines, its governed files, its gate, and each task as roadkeep describes it.',
    ],
    sections: [
      {
        heading: 'The filters are arguments',
        body: [
          'Block, marker, requirement and startable-only all go to ',
          { code: 'list' },
          ' as flags. The engine selects the lines; the window never filters a copy, so what you see is what roadkeep would answer an agent asking the same question.',
        ],
      },
      {
        heading: 'A tab per governed file',
        body: [
          'The roadmap first, then the changelog, the decisions, the deferred work and the improvements, each read through roadkeep. Where the engine supports it, one more tab lists the shipped lines still waiting on a person to confirm them.',
        ],
      },
      {
        heading: 'The gate, with the fix it offers',
        body: [
          'Each finding is a row: its code, where it is, and the gate’s own sentence. Under it, the command roadkeep offers as what closes it, which the window can run as it stands or hand to Claude Code. The window fills the engine’s placeholders and refuses any word the engine did not put there.',
        ],
      },
      {
        heading: 'A task, joined by brief',
        body: [
          'One line with its design as the file stores it, its readiness, its deps and what it unblocks, its claim, and the criteria and non-goals that bind its block. ',
          { b: 'Copy the brief' },
          ' puts that payload on the clipboard for an agent you run yourself.',
        ],
      },
    ],
  },
  {
    slug: 'writing',
    title: 'roadkeep-gui: filing a line without writing a file',
    description:
      'How roadkeep-gui adds a line: a form measured against roadkeep’s own budget, the blocks’ existing lines beside it, the exact command shown before it runs, and the refusal landing on the field it names.',
    ogTitle: 'Filing a line',
    ogDescription:
      'A form measured against roadkeep’s budget, the command shown before it runs, and a refusal on the field it names.',
    eyebrow: 'The write path',
    heading: 'The app composes a command line. roadkeep writes.',
    lead: [
      'There is a form for a new line and no editor for an old one, and that asymmetry is the design: writing a governed file is roadkeep’s job, and a second writer is how a file stops round-tripping.',
    ],
    sections: [
      {
        heading: 'File a line',
        list: [
          [
            { b: 'The budget is roadkeep’s' },
            ': how long a symptom, a why and a design may be comes from its ',
            { code: 'budget' },
            ' verb as you type, never from a number compiled in',
          ],
          [
            { b: 'What the block already has' },
            ' sits beside the form, so a line that restates a shipped one is noticed before it is filed',
          ],
          [
            { b: 'The command, before it runs' },
            ': the exact ',
            { code: 'roadkeep add' },
            ' argv, with a copy button, for a person who would rather run it themselves',
          ],
          [
            { b: 'A refusal lands on its field' },
            ': when the engine says no, its reason appears under the field it names rather than in a toast',
          ],
        ],
      },
      {
        heading: 'What the process boundary refuses',
        body: [
          `The renderer asks and the main process decides. A command line is carried only if it opens with the project root, closes with `,
          { code: '--json' },
          `, names a verb from one of the two tables (${spelled(readCount)} reads, ${spelled(writeCount)} writes), and carries only flags that verb’s own builder produces. A file-reading flag is refused outright, and so is a root the scan never found.`,
        ],
      },
      {
        heading: 'The other writes',
        body: [
          'A verdict on a walkthrough is a ',
          { code: 'validate' },
          ', and handing a line over is a ',
          { code: 'brief --claim' },
          '. The remaining write verbs are in the table so an offered fix can name them, and correcting a line stays a command you run: ',
          {
            code: joined(product.writes.filter((w) => w !== 'add' && w !== 'validate').slice(0, 4)),
          },
          ' and the rest.',
        ],
      },
    ],
  },
  {
    slug: 'sessions',
    title: 'roadkeep-gui: a Claude Code session, carried in the window',
    description:
      'What a hand-over looks like once it is running: the stream with roadkeep calls marked, the files edited against their originals, what moved read from the files, the permission questions, a reply and Stop.',
    ogTitle: 'Sessions',
    ogDescription:
      'The stream, the files it edited, what moved according to the files, and every question answered in the window.',
    eyebrow: 'Sessions',
    heading: 'Watch a line being worked, and answer what it asks',
    lead: [
      'A session is your Claude Code working one line in one project. The window does not drive it; it shows it, carries its questions, and checks its claims against the files.',
    ],
    sections: [
      {
        heading: 'Three columns',
        list: [
          [
            { b: 'The stream' },
            ', with every roadkeep call marked and every touch on a governed file flagged',
          ],
          [{ b: 'What was handed over' }, ': the brief, as it went in'],
          [
            { b: 'What moved' },
            ', read from the files rather than from what the agent said, and the files it edited, each against its original, side by side or inline',
          ],
        ],
      },
      {
        heading: 'Changed on disk while it ran',
        body: [
          'A second watch lists every file that changed under the project during the session, including the ones the agent never mentioned.',
        ],
      },
      {
        heading: 'Questions, a reply, and Stop',
        body: [
          'A permission question offers ',
          { b: 'Allow this call' },
          ', ',
          { b: 'Allow for this session' },
          ' or ',
          { b: 'Decline' },
          '. A reply continues the same conversation by its id. Stop ends the process and leaves the claim to expire on its own rather than guessing what should happen to it.',
        ],
      },
      {
        heading: 'Every session this window started',
        body: [
          'Listed while the window is open. The list is kept in memory and not on disk: Claude Code keeps the transcript, and a second copy here would be one that goes stale.',
        ],
      },
    ],
  },
  {
    slug: 'engine',
    title: 'roadkeep-gui: which roadkeep answers, and the window around it',
    description:
      'How roadkeep-gui picks the engine for each project and names it, why it bundles none, the renderer posture a packaged build must keep, and the languages and grounds the window follows.',
    ogTitle: 'The engine and the window',
    ogDescription:
      'Each project answered by its own roadkeep, named on the row, in a renderer that stays a browser.',
    eyebrow: 'The engine and the window',
    heading: 'Each project answered by its own roadkeep, named on the row',
    lead: [
      'The window ships no engine. That is not a missing feature: three copies of roadkeep on one machine can differ, and the only honest answer to which one wrote is to ask each project and say.',
    ],
    sections: [
      {
        heading: 'Where the engine comes from',
        list: [
          [
            { b: 'The project’s committed launcher' },
            ', first: the same one its hooks and its agent use',
          ],
          [{ b: 'Then roadkeep on your PATH' }],
          [
            { b: 'Never a bundled copy' },
            ': a project with none reachable is shown as unreadable, with the reason',
          ],
          [
            { b: 'Named on the row' },
            ': the version that answered, and ',
            { b: 'Engine disagrees' },
            ' when it was not the one the project declares',
          ],
        ],
      },
      {
        heading: 'A process per call, or one per project',
        body: [
          'Reads spawn the engine with the argument list as it is, no shell, standard input closed, a timeout on every call. An opened project can keep one ',
          { code: 'roadkeep mcp' },
          ' process alive instead and fall back to spawning when it cannot.',
        ],
      },
      {
        heading: 'A renderer that stays a browser',
        body: [
          'The window runs with ',
          {
            code: Object.entries(product.posture)
              .map(([flag, value]) => `${flag}: ${String(value)}`)
              .join(', '),
          },
          '. Packaging reads that posture and refuses a build that lost any of it, and CI runs the refusal on every change.',
        ],
      },
      {
        heading: 'Its ground and its language',
        body: [
          'Light and dark follow the desktop until you choose one, and the window speaks ',
          joined(product.languages),
          '. It is drawn with the Viglet design system, the same package Turing, Shio and Dumont use, re-keyed to roadkeep’s amber.',
        ],
      },
    ],
  },
]
