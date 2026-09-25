// The copy lives here and nowhere else. Every section component imports a value from this
// module and only renders it, so a claim is an array element a reviewer can check against the
// product rather than a string welded into the markup that displays it. The composition (which
// section, in which order) lives in the JSX; this file is the words.
//
// Fragments carrying inline code or emphasis are a small tagged run list (`Rich`) rather than
// raw HTML, so a section renders them without dangerouslySetInnerHTML and the twin generator
// has a structure to convert rather than markup to parse.
//
// Every count below comes from product.ts, which reads it out of this repository's source at
// build time. The copy states the reason and the generator states the number.
import {
  spelledTitle,
  joined,
  nonGoalCount,
  product,
  readCount,
  spelled,
  writeCount,
} from './product'

export type Run = string | { code: string } | { b: string } | { i: string }

export type Rich = Run[]

/* ------------------------------------------------------------------ meta + chrome */

export const meta = {
  title: 'roadkeep-gui: every roadkeep backlog on this machine, in one window',
  description:
    'A free desktop app for Windows and Linux that reads the backlogs roadkeep governs in every repository you point it at, one row per project, and hands a line to Claude Code with its brief. It never writes a governed file: the roadkeep command does.',
  og: {
    title: 'roadkeep-gui',
    description:
      'Every roadkeep backlog on this machine in one window, read off what the command prints, with a line handed to Claude Code in one click.',
  },
} as const

export const repoUrl = 'https://github.com/alegauss/roadkeep'
export const parentUrl = 'https://alegauss.github.io/'
export const roadkeepUrl = 'https://alegauss.github.io/roadkeep/'

// The release page rather than a file: each installer carries its version in its name, so
// there is no version-independent URL for the asset itself. `releases/latest` is the one link
// that cannot go stale.
export const releasesUrl = `${repoUrl}/releases/latest`

// Section anchors act on the landing page; the page links are base-absolute so they resolve
// the same from every route.
export const navLinks = [
  { href: '/roadkeep/gui/#how', label: 'How it reads' },
  { href: '/roadkeep/gui/#rules', label: 'Rules' },
  { href: '/roadkeep/gui/claude-code/', label: 'Claude Code' },
  { href: '/roadkeep/gui/compare/', label: 'Compare' },
] as const

export const footer = {
  links: [
    { href: '/roadkeep/gui/claude-code/', label: 'Claude Code' },
    { href: '/roadkeep/gui/compare/', label: 'Compare' },
    { href: roadkeepUrl, label: 'roadkeep' },
    { href: repoUrl, label: 'GitHub' },
    { href: releasesUrl, label: 'Releases' },
    { href: `${repoUrl}/blob/main/docs/ROADMAP.md`, label: 'Roadmap' },
  ],
  // The licence is a link to the file, not a string in a sentence, so a change of licence is
  // a change the page follows rather than one it contradicts.
  disclaimer:
    'Unofficial companion to roadkeep, by the same author. Not affiliated with, endorsed by, or sponsored by Anthropic; “Claude” and “Claude Code” are trademarks of Anthropic, and this app runs the Claude Code you already have rather than shipping one. The licence is in LICENSE. © 2026 Alexandre Oliveira.',
} as const

/* --------------------------------------------------------------- sponsor */

// Mirrors alegauss.github.io/sponsor.json, the canonical sponsor declaration for these
// projects. Transcribed rather than fetched at runtime: the site is prerendered, and the point
// of naming a sponsor is that crawlers and LLMs read it in the served HTML.
export const sponsor = {
  label: 'Sponsored by',
  name: 'Viglet',
  url: 'https://www.viglet.org',
  siteLabel: 'viglet.org',
  logo: '/roadkeep/gui/viglet/viglet-logo.png',
  summary:
    'Open source search and content tools for organisations with a lot to publish. Run on your own servers, with no per-user licence.',
  products: [
    {
      name: 'Viglet Turing ES',
      url: 'https://turing.viglet.org',
      logo: '/roadkeep/gui/viglet/turing-logo.png',
      inline:
        'so visitors find what they came for, with AI answers drawn only from your own content',
    },
    {
      name: 'Viglet Shio CMS',
      url: 'https://shio.viglet.org',
      logo: '/roadkeep/gui/viglet/shio-logo.png',
      inline: 'so a new page goes live the same day, reviewed and approved by your own team',
    },
  ],
} as const

/* ------------------------------------------------------------------ hero */

export const hero = {
  // The version is package.json's, which is also what the release tag has to match.
  badge: `Windows and Linux · ${product.license} · v${product.version}`,
  titleLead: 'Every roadkeep backlog on this machine,',
  titleAccent: 'in one window.',
  sub: [
    'roadkeep-gui reads the backlogs ',
    { b: 'roadkeep' },
    ' governs in every repository you point it at, one row per project, and hands a line to Claude Code when you want it worked. It never writes a governed file: every change is a ',
    { code: 'roadkeep' },
    ' command it composes, shows you, and leaves the engine to run.',
  ] as Rich,
  // No emoji on these, and that is a writing rule rather than a taste: they are also bullets in
  // the Markdown twin an agent reads.
  meta: ['Free and open source', 'No account, nothing sent of its own', 'Ships no engine'],
  pills: [
    [{ b: 'Electron' }, ' · React 19 · a sandboxed renderer'] as Rich,
    [{ b: `${readCount} reads, ${writeCount} writes` }, ', in two separate tables'] as Rich,
    [{ b: joined(product.languages) }] as Rich,
  ],
}

// A drawing of the portfolio screen. The columns, the filter names and the footnote are the
// window's own strings; the projects, ids and counts are illustrative, and the note says so.
export const heroWindow = {
  title: 'roadkeep · Portfolio',
  filters: 'All · Gate drifted · Engine disagrees · Unreadable',
  rows: [
    {
      name: 'billing-service',
      backlog: '14 open · 3 startable',
      next: [{ code: 'BS41' }, ' the retry queue drops a job when the worker restarts'] as Rich,
      state: 'gate clean · roadkeep 0.2 via the project launcher',
    },
    {
      name: 'docs-site',
      backlog: '6 open · 1 startable',
      next: [{ code: 'DOC12' }, ' the search box returns pages that were unpublished'] as Rich,
      state: 'gate drifted: 2 findings · roadkeep on PATH',
    },
    {
      name: 'mobile-app',
      backlog: '22 open · 0 startable',
      next: ['every open line waits on another'] as Rich,
      state: 'gate clean · Engine disagrees: declared a launcher, PATH answered',
    },
  ],
  footnote: 'Every number on this screen is one a verb printed. Nothing is summed across projects.',
  note: [
    'Illustrative rows. The columns, the filters and the footnote are the window’s own; the projects are nobody’s. The footnote is the rule: a count on this screen is one ',
    { code: 'roadkeep' },
    ' printed for that project, never one the app added up.',
  ] as Rich,
}

/* ------------------------------------------------------------------ why */

export const why = {
  eyebrow: 'Why it exists',
  heading: 'roadkeep answers one project at a time. You work across twelve.',
  intro: [
    'roadkeep keeps a backlog in Markdown files inside the repository, where an agent can grep it and a hook refuses a hand edit. That is right for an agent working in one checkout. A person deciding where the afternoon goes needs every backlog at once, and until now that meant a terminal per repository.',
  ] as Rich,
  cards: [
    {
      icon: '🗂',
      title: 'One row per project',
      body: [
        'What is open, what is startable, the next ready line, whether the gate is clean and which engine answered, for every governed checkout under the folders you named. Sorted as you choose, filtered to the ones that need you.',
      ] as Rich,
    },
    {
      icon: '🧾',
      title: 'It reads what the command prints',
      body: [
        'Every row is a payload a verb returned with ',
        { code: '--json' },
        '. The app parses no governed Markdown, so it cannot disagree with roadkeep about what a file says: there is only one reader, and it is the tool.',
      ] as Rich,
    },
    {
      icon: '✍️',
      title: 'The command writes, never the app',
      body: [
        'Filing a line composes ',
        { code: 'roadkeep add' },
        ' with your words as arguments, shows it before it runs, and lets the engine validate and write. The main process refuses any command line its two verb tables did not produce.',
      ] as Rich,
    },
    {
      icon: '🧭',
      title: 'Each project’s own engine answers',
      body: [
        'The project’s committed launcher first, then the ',
        { code: 'roadkeep' },
        ' on your PATH. Which copy answered is on the row, and a project that got a different copy from the one it declared says so rather than being read by a stranger.',
      ] as Rich,
    },
    {
      icon: '🤖',
      title: 'A line handed over, not retyped',
      body: [
        { b: 'Hand to Claude Code' },
        ' claims the line and gives your own Claude Code, in the project’s root, the ',
        { code: 'brief' },
        ' roadkeep printed for it, verbatim. The session runs under the project’s settings, not this app’s.',
      ] as Rich,
    },
    {
      icon: '🔒',
      title: 'Nothing sent of its own',
      body: [
        'No account, no telemetry, nothing uploaded. The one request the app makes by itself is ',
        { b: 'Check for updates' },
        ', and only when you pick it from the Help menu. A session you start talks to whatever your Claude Code already talks to.',
      ] as Rich,
    },
  ],
}

/* ------------------------------------------------------------------ how it reads */

export const how = {
  eyebrow: 'How it reads',
  heading: 'Nowhere, until you name a folder',
  intro: [
    'An app that scans a drive on first launch reads somebody’s whole disk to draw a list. So there is no default root: the first run asks, and the scan goes exactly as deep as you said.',
  ] as Rich,
  steps: [
    {
      n: '1',
      title: 'Name a folder',
      body: [
        `Add a root and a depth: ${spelled(product.scan.defaultDepth)} levels by default, which reaches `,
        { code: '~/code/<org>/<repo>' },
        `, and never more than ${spelled(product.scan.depthCeiling)}. A root that disappears, like an unplugged drive, is kept and marked missing rather than forgotten.`,
      ] as Rich,
    },
    {
      n: '2',
      title: 'It looks for roadkeep.toml',
      body: [
        'Nothing else marks a governed checkout. Hidden folders, ',
        { code: 'node_modules' },
        ', ',
        { code: 'dist' },
        ' and the other build directories are skipped, a found project is not descended into, and worktrees are grouped by reading git’s own files. No git command is run.',
      ] as Rich,
    },
    {
      n: '3',
      title: 'Each project answers for itself',
      body: [
        'The engine is asked through ',
        { code: 'engines --json' },
        ' and the project’s declared invocation is followed. A project with no engine reachable is shown as unreadable, with the reason, and never guessed at.',
      ] as Rich,
    },
    {
      n: '4',
      title: 'The files change, the row follows',
      body: [
        'The folders holding each project’s governed files are watched. A ',
        { code: 'ship' },
        ' that writes three files arrives as one refresh, and the gate runs again without anybody opening it.',
      ] as Rich,
    },
    {
      n: '5',
      title: 'A filter is an argument',
      body: [
        'Narrowing a project to a block, a marker or startable lines passes that to ',
        { code: 'list' },
        '. The engine selects; the window does not filter a copy of its own.',
      ] as Rich,
    },
    {
      n: '6',
      title: 'Then it waits',
      body: [
        'Readings are cached between launches, so the portfolio opens on what was true last time, marked as such, while each project is asked again.',
      ] as Rich,
    },
  ],
  termTitle: 'what the window runs, per project',
  term: [
    '# every call is an argv array: -C <root>, the verb, its flags, --json',
    'roadkeep -C ~/code/billing-service list --block F --startable --json',
    '',
    '# filing a line is a command you read before it runs',
    'roadkeep -C ~/code/billing-service add --block F --symptom "…" --why "…" --json',
  ].join('\n'),
  termNote:
    'No shell is involved: the argument list goes to the process as it is, so a symptom with quotes or a semicolon in it is a symptom and never a second command.',
}

/* ------------------------------------------------------------------ the three parties and the rules */

export const rules = {
  eyebrow: 'Who does what',
  heading: 'The engine writes. The window reads. You decide.',
  intro: [
    'Three parties touch a backlog here, and the whole design is keeping each to its own half. roadkeep is the only thing that writes a governed file; the window is the only thing that draws one; the prose is always a person’s or an agent’s.',
  ] as Rich,
  actors: [
    {
      who: 'roadkeep',
      sub: 'the engine, per project',
      iface: 'roadkeep -C <root> <verb> --json',
      job: 'Validates, writes the governed files, and answers every question as a payload',
      first: true,
    },
    {
      who: 'The window',
      sub: 'this app',
      iface: `${readCount} reads · ${writeCount} writes`,
      job: 'Draws what a verb printed, composes a command line, names which engine answered',
      first: false,
    },
    {
      who: 'You, or Claude Code',
      sub: 'at the keyboard, or handed a line',
      iface: 'the filing form · a session',
      job: 'Decide what to work, type the symptom and the why, approve what an agent asks',
      first: false,
    },
  ],
  actorsNote: [
    'That is why the window has a form for a new line and no editor for an old one: correcting a line is a roadkeep verb, and a verb has one implementation.',
  ] as Rich,
  lawsEyebrow: 'The design rules',
  lawsHeading: 'Eight rules the window is judged by',
  lawsIntro: [
    'Binding, in the sense that a feature which breaks one is wrong even if somebody asked for it. Each names the failure it prevents.',
  ] as Rich,
  laws: [
    {
      id: 'R1',
      title: 'One writer per file',
      body: 'The app composes an argv and the command writes. Two programs writing one Markdown file is how a round trip stops being byte-identical, so the second one is refused at the process boundary.',
    },
    {
      id: 'R2',
      title: 'A number is one a verb printed',
      body: 'Nothing is summed across projects and nothing is derived from a file. A figure the window computed would be a figure roadkeep never agreed to.',
    },
    {
      id: 'R3',
      title: 'Name the engine',
      body: 'Three copies of roadkeep on one machine can differ. Which one answered is on every row, nothing is bundled, and nothing is chosen silently.',
    },
    {
      id: 'R4',
      title: 'No rule compiled in',
      body: 'Markers, id shapes, limits, block labels and file names are per-project configuration. The window reads them from the project, so it cannot hold a stale copy of any of them.',
    },
    {
      id: 'R5',
      title: 'Nowhere until you say',
      body: 'No default root and no drive walk. The scan covers the folders you named, to the depth you chose, and a missing one stays on the list.',
    },
    {
      id: 'R6',
      title: 'A refusal lands on its field',
      body: 'The character budget comes from roadkeep’s own budget verb while you type, and when the engine refuses anyway, its reason appears under the field it names.',
    },
    {
      id: 'R7',
      title: 'The agent is yours',
      body: 'Your claude, in the project’s root, under the project’s settings. The window sets no model and no permission mode, and never writes to .claude.',
    },
    {
      id: 'R8',
      title: 'The renderer is a browser',
      body: 'Context isolation, the sandbox and web security stay on, and packaging refuses a build that lost any of them. A window that can delete a file is not a reader.',
    },
  ],
}

/* ------------------------------------------------------------------ the hand-over session */

// A scripted session. The flow, the button names and the permission choices are the window's
// own; the ids and file names are illustrative.
export const session = {
  eyebrow: 'Hand a line to Claude Code',
  heading: 'One button between reading a line and having it worked',
  intro: [
    'On a task, ',
    { b: 'Hand to Claude Code' },
    ' does three things: claims the line so a second session cannot take it, starts your Claude Code in that project’s root, and gives it the ',
    { code: 'brief' },
    ' payload roadkeep printed. The window then carries the session: the stream, the permission questions, the files it touched.',
  ] as Rich,
  ask: 'BS41: the retry queue drops a job when the worker restarts',
  steps: [
    {
      who: 'app' as const,
      line: [
        { code: 'brief BS41 --claim' },
        ' → the line is this session’s, in the same transaction',
      ] as Rich,
    },
    {
      who: 'app' as const,
      line: [
        'claude starts in ~/code/billing-service with the brief, verbatim: the line, its design, its deps, what shipping it unblocks',
      ] as Rich,
    },
    { who: 'agent' as const, line: ['Read src/queue/retry.ts · Grep "ack" src/queue'] as Rich },
    { who: 'agent' as const, line: ['Edit src/queue/retry.ts'] as Rich },
    {
      who: 'app' as const,
      line: [
        'Claude Code asks to run ',
        { code: 'npm test' },
        ': Allow this call · Allow for this session · Decline',
      ] as Rich,
    },
    { who: 'you' as const, line: ['Allow this call'] as Rich },
    { who: 'agent' as const, line: [{ code: 'roadkeep ship BS41 --why "…"' }] as Rich },
    {
      who: 'app' as const,
      line: [
        'What moved, read from the files and not the stream: BS41 left the roadmap, the changelog gained its entry',
      ] as Rich,
    },
    {
      who: 'you' as const,
      line: ['Reply: file the flaky test you hit as a line of its own'] as Rich,
    },
  ],
  note: [
    'A scripted session with illustrative ids. The permission question is Claude Code’s, and the window only carries it: ',
    { b: 'no permission mode is set and nothing is written to the project’s .claude settings' },
    '. A reply resumes the same conversation by its id; Stop ends the process and leaves the claim to expire on its own.',
  ] as Rich,
}

/* ------------------------------------------------------------------ non-goals */

export const nonGoals = {
  eyebrow: 'Scope',
  heading: 'What it is not',
  intro: [
    `${spelledTitle(nonGoalCount)} refusals, read at build time from the roadmap where roadkeep keeps them, so this list is the project’s own and not a summary of it. Where one names L4 or L6, those are roadkeep’s laws: L4, the tool never writes prose; L6, configuration and not convention.`,
  ] as Rich,
  // The titles and reasons are generated (product.nonGoals); the laws named above are what the
  // test holds this intro to, so a non-goal citing a new law fails the build until it is said.
  explainedLaws: ['L4', 'L6'],
}

/* ------------------------------------------------------------------ download */

// No version number typed here: a version is a figure this page cannot keep, and
// `releases/latest` resolves to whatever shipped.
export const download = {
  eyebrow: 'Take the installer',
  heading: 'Two installers, and neither brings an engine',
  intro: [
    'The release page carries a Windows installer and a Linux AppImage. The Windows one installs for your account, asks where, and wants no administrator. Neither carries roadkeep: each project answers through its own launcher or the ',
    { code: 'roadkeep' },
    ' already on your PATH, which is the only way the window can say which one answered.',
  ] as Rich,
  facts: [
    'Windows 10 or 11, 64-bit: a per-user installer',
    'Linux: an AppImage, no install step',
    'Claude Code: only to hand a line over',
  ],
  cta: '⬇ Download',
  secondary: 'Release notes',
  engineLead: 'And the engine, if no project brings its own:',
  engineLine: 'pip install roadkeep',
  note: [
    { b: 'Unsigned for now.' },
    ' Windows warns before the first run, and the certificate is an open line on the roadmap rather than a thing this page pretends is done. No macOS build has ever been made, so none is offered.',
  ] as Rich,
}

/* ------------------------------------------------------------------ /claude-code page */

export const claudeCode = {
  meta: {
    title: 'roadkeep-gui and Claude Code: handing one line over',
    description:
      'How roadkeep-gui hands a roadkeep line to Claude Code: the claim, the brief passed verbatim, a session under the project’s own settings, and the read-only Explain that answers a question without writing anything.',
    ogTitle: 'roadkeep-gui for Claude Code',
    ogDescription:
      'The claim, the brief verbatim, the project’s own settings, and what the window refuses to decide for the agent.',
  },
  eyebrow: 'For the agent’s operator',
  heading: 'The window hands the line over, and then gets out of the way',
  intro: [
    'roadkeep already tells an agent where to start: ',
    { code: 'brief' },
    ' prints the line, its design, its deps and what shipping it unblocks. The window’s whole contribution is not retyping any of it, and not deciding anything the project or the person already decided.',
  ] as Rich,
  flowHeading: 'What one click does',
  flow: [
    {
      n: '1',
      title: 'Claims the line',
      body: [
        { code: 'brief <id> --claim' },
        ', the one read that writes. A line another worker holds is named and not handed over, so two sessions never work one task.',
      ] as Rich,
    },
    {
      n: '2',
      title: 'Passes the brief verbatim',
      body: [
        'The prompt is a three-sentence frame around the JSON roadkeep printed. Paraphrasing it would be a second account of a line the tool already stated.',
      ] as Rich,
    },
    {
      n: '3',
      title: 'Runs your claude where the project is',
      body: [
        'The working directory is the project root, so its own ',
        { code: 'roadkeep.toml' },
        ', guard, skill and ',
        { code: '.mcp.json' },
        ' answer. The claude is yours: the one on PATH, never a bundled copy.',
      ] as Rich,
    },
    {
      n: '4',
      title: 'Carries the session',
      body: [
        'The stream, with roadkeep calls marked and governed-file touches flagged; each edited file against its original; what changed on disk while it ran; and each permission question, answered in the window.',
      ] as Rich,
    },
    {
      n: '5',
      title: 'Reads what moved from the files',
      body: [
        'Not from what the agent said it did. A ship that happened is in the changelog; a ship the stream mentioned and the engine refused is not, and the card shows the difference.',
      ] as Rich,
    },
    {
      n: '6',
      title: 'Resumes on a reply',
      body: [
        'Your reply goes to the same conversation by its session id, as written. Tools you allowed after a refusal apply to that turn and no longer.',
      ] as Rich,
    },
  ],
  gateHeading: 'A gate finding can be handed over too',
  gateBody: [
    'When ',
    { code: 'roadkeep lint' },
    ' reports a finding, the engine also offers the command that closes it. The window can run that command, or hand the finding to Claude Code with that exact command and one instruction: run it, write the prose it leaves blank, and do not edit the governed file directly.',
  ] as Rich,
  refusesHeading: 'What the window refuses to decide',
  refusesLead: [
    'Each of these is something the project or the person already decides, and a default chosen here would be the app overruling them quietly.',
  ] as Rich,
  refuses: [
    { t: 'No model', b: 'Whatever your Claude Code is set to.' },
    { t: 'No permission mode', b: 'Claude Code asks; the window only carries the question.' },
    { t: 'No settings written', b: 'The project’s .claude is the project’s.' },
    { t: 'No bundled claude', b: 'Yours on PATH, or where the installer put it.' },
    { t: 'No git', b: 'Staging and committing stay yours.' },
    { t: 'No prose of its own', b: 'The brief goes in as printed; a reply goes as typed.' },
  ],
  explainHeading: 'Explain, and how to check it: questions that cannot write',
  explainBody: [
    'On a task, ',
    { b: 'Explain' },
    ' asks Claude Code what a line means, in the project’s own vocabulary, and ',
    { b: 'How to check it' },
    ' asks for the steps a person follows to confirm a shipped line works. Both run as one-shot questions with the tools limited to ',
    { code: joined(product.question.tools) },
    ` (a walkthrough may also run one bounded git show), no MCP servers, at most ${product.question.turns} turns, and nothing kept in your session history. A walkthrough ends in a verdict you give, and the verdict is a roadkeep `,
    { code: 'validate' },
    '.',
  ] as Rich,
  verbsHeading: 'Everything the window can ask roadkeep',
  verbsLead: [
    `Two tables, kept apart on purpose: ${spelled(readCount)} reads and ${spelled(writeCount)} writes, read out of the source when this page was built. The main process refuses a command line that names anything else, carries a flag its verb does not produce, or points at a root the scan did not find.`,
  ] as Rich,
  readsHeading: 'reads',
  writesHeading: 'writes',
}

/* ------------------------------------------------------------------ /compare page */

export const compare = {
  meta: {
    title: 'roadkeep-gui vs an editor, the roadkeep CLI and an issue tracker',
    description:
      'What roadkeep-gui does that an editor open on the files, the roadkeep command line or an issue tracker does not, and what each of those is genuinely better at.',
    ogTitle: 'roadkeep-gui: the honest comparison',
    ogDescription:
      'Checkable rows grouped by what each is for, and a column for what every alternative wins.',
  },
  eyebrow: 'Against the alternatives',
  heading: 'What this does that the others do not, and where they win',
  intro: [
    'A backlog roadkeep governs can already be read three other ways. A matrix that wins every row is one nobody believes, so every alternative keeps the rows it genuinely wins.',
  ] as Rich,
  columns: ['roadkeep-gui', 'Editor on the files', 'roadkeep CLI', 'Issue tracker'],
  legend: [
    { sym: '✓', label: 'yes' },
    { sym: '~', label: 'partial' },
    { sym: '✗', label: 'no' },
  ],
  groups: [
    {
      law: 'Across projects',
      rows: [
        { cap: 'Every governed repository in one view', cells: ['✓', '~', '✗', '✓'] },
        { cap: 'Find a line in every backlog at once', cells: ['✓', '✓', '✗', '✓'] },
      ],
    },
    {
      law: 'Faithful to the files',
      rows: [
        { cap: 'Every change written by the engine', cells: ['✓', '✗', '✓', '✗'] },
        { cap: 'The backlog stays in the repository, greppable', cells: ['✓', '✓', '✓', '✗'] },
        { cap: 'A draft measured against the budget as you type', cells: ['✓', '✗', '~', '✗'] },
      ],
    },
    {
      law: 'For an agent',
      rows: [{ cap: 'Hand one line to Claude Code with its brief', cells: ['✓', '✗', '~', '~'] }],
    },
    {
      law: 'Where an alternative leads',
      rows: [
        { cap: 'Works with no display: over SSH, in CI', cells: ['✗', '✓', '✓', '~'] },
        { cap: 'Assignees, due dates, notifications', cells: ['✗', '✗', '✗', '✓'] },
        { cap: 'Correct an existing line in place', cells: ['✗', '✓', '✓', '✓'] },
        { cap: 'A macOS build', cells: ['✗', '✓', '✓', '✓'] },
      ],
    },
  ],
  winsHeading: 'What each alternative is genuinely better at',
  wins: [
    {
      name: 'An editor on the files',
      body: 'Nothing to install and every line in reach. Pick it for one repository, when you read Markdown fast and a hook stops the edits that would break it.',
    },
    {
      name: 'The roadkeep CLI',
      body: 'Scriptable, works over SSH, and every verb is there, including the corrections this window only offers as the command to run. It is also what the agent uses anyway.',
    },
    {
      name: 'An issue tracker',
      body: 'Assignees, due dates, notifications and a link to send somebody who will never open a repository. Pick it when the backlog belongs to a team that is not in the code.',
    },
  ],
  winsFooter: [
    'What is left is the axis where this one wins: every roadkeep backlog on the machine in one view, read off the engine’s own answers, with a line handed to an agent in one click and no second writer in the files.',
  ] as Rich,
}
