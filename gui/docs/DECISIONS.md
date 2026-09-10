# Decisions

## Block A — The client (payloads in, types out)

- ✅ **RG64** **the fast suite and the one that spawns a real engine are one command, so every run pays for both** — A test that spawns a process, opens a window or reads the build is named `*-live.test.*`; suites.test.ts reads every test file and fails when one is filed under a fast name.
- ✅ **RG65** **resolving an engine costs two interpreter starts on Windows, where the same file is spelled two ways** — A rule about what a path means is handed into `core` and never folded inside it, even written as pure string work.
- ✅ **RG75** **two live tests still name RG9, so the commit that ships it fails a suite nothing changed to break** — A live test names no open id: it asks the engine for a line in the state it is about.
- ✅ **RG84** **every live file resolves the engine itself, so one being rebuilt mid-run reds the suite four ways** — The live suite asks its engine what it is once per run and spends that one reading; it never resolves an engine of its own.
- ✅ **RG122** **the transport that reads in 6ms is proven by a test and reached by nothing a person would run** — An open project holds an engine process and is closed by whoever opened it; the pool now bounds only the reads that fall back to a spawn.
- ✅ **RG134** **the contract reads this repository's own lint for a finding, so a clean gate leaves it nothing to assert** — A contract test produces the state it asserts about; it never reads this repository's own gate for one.

### §RG65 What a path means is not core's to know

The cheaper fix was one line inside `core`: normalise the separator in both strings
before comparing. It was rejected because a backslash is an ordinary character in a
filename on Linux, so the fold would report two different files as one — and the branch
it lies to is the one saying the declared copy was *reached*. Claiming to have run an
engine nobody ran is the failure this module exists to avoid, and a comparison correct
on one platform is not cheaper than a second process start.

So `resolveEngine` takes the comparison and defaults to a literal one: slow on Windows,
never wrong anywhere. `root-paths.ts` had answered the same question for folders without
recording why. This is the second instance, and the constraint is general: a rule about
paths belongs to whoever has the filesystem, even written as pure string work that would
compile in `core` untouched.

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

## Block G — The shell (an executable now, a service later)

- ✅ **RG37** **there is no application at all: no window, no build and no way to run any of this** — The desktop shell is Electron over Vite and React, not a native toolkit: the renderer has to be the half a web service later serves to a browser unchanged.
- ✅ **RG85** **the handler proving the seam runs any argv against any root, which a real service cannot** — A service transport refuses what the test handler allows: a root the server was not started with, an argv the verb table did not compose, every write verb, and a bind that is not loopback.
- ✅ **RG129** **the verb table is declared with string keys, so the file owning it asserts its own key type and nothing checks the pair** — A table this repository writes is declared by its key type; a narrowing it cannot carry lives in reading.ts, never at a call site.

### §RG37 Electron, and what it costs

Electron rather than a native toolkit because the second life of this project is a web
service, and in that life `ui` is served to a browser while `core` runs behind an HTTP
handler with a different transport under the same interface. The cost is honest and
worth stating: a large runtime, a heavier executable, and a renderer that has to be
locked down because it is a browser. Tauri would spend less and would leave the same
seam; it was not chosen because the toolchain here is already the one roadkeep's own
site is built with, so the build conventions exist in a repository beside this one. Vite
and React 19 follow from that. One thing settled while building against the choice
belongs with it: everything is ESM and TypeScript, launchers included, so one `tsc -b`
spans every file the project runs and not only what it ships.

### §RG85 What the server refuses, decided before there is one

Four refusals, each one a power the test handler has and a service must not.

**A root it was not started with.** The wire carries a root and the handler runs it; a
server holds its own and the call names one or is refused. Validating the path was
rejected: a rule about what a path may be is one somebody spells around.

**An argv the verb table did not compose.** A command line over a socket is a shell. A
service takes a verb and its arguments and composes the argv itself.

**Every write verb.** Reads cross; a write is somebody's working tree, and the desktop
already says the command writes and the app does not.

**A bind that is not loopback.** Until identity exists there is nobody to serve.

They are written here and not in the handler because a design starting from working code
inherits its permissions.

## Block H — The look (a design system for governed prose)

- ✅ **RG39** **there is no design system, so every screen decides its own type, spacing and colour on the spot** — The design system is @viglet/viglet-design-system, a dependency shared with Turing, Shio and Dumont: this app declares no colour, type scale, spacing or radius of its own.
- ✅ **RG52** **there is one ground, so somebody who works in dark reads this app in light** — The design system owns the theme switch; this app resolves the setting and never mounts a second theme system.
- ✅ **RG86** **the locale setting reaches no screen, so choosing one changes nothing** — A locale ships inside the bundle and nothing reads a translation off disk, so adding a language is a release.
- ✅ **RG88** **one screen has two translation systems, and only one of them was chosen** — A string belongs to whoever draws it: this app's own components read a MessageKey, the design system's read an i18next key, and one instance holds the locale both take.
- ✅ **RG63** **there is no page chrome, so the first real screen will invent a shape the design system already has** — The shell is bento and the content inside it is not: a backlog is drawn as rows, because a 120-character symptom fits in no tile.
- ✅ **RG116** **there is no control for the language, so choosing one means editing the settings file by hand** — A control the design system owns may keep its own cache; the settings file is the source, and the write back hangs on whatever holds the state rather than on the control.
- ✅ **RG123** **a sentence shown in a toast is English whatever the window is speaking, and the run that would catch it looks elsewhere** — A settings loss crosses as a code and its fields, and the pseudo-locale run reads document.body with the sheet, the palette and a toast open.
- ✅ **RG124** **a design system control draws its flags from a CDN, so a screen adopting one shows the image the policy refused** — Every host the built renderer names is accounted for by name in a live test, and no image source in it may carry one.
- ✅ **RG125** **the i18next half of the wording is two hand-written objects, so a key added to one and missed in the other is silent** — Both halves of the wording are held complete by one rule in core: every path of the base in every language, and a copied value is an error unless it is a name.
- ✅ **RG126** **the provider stack is spelled twice, so one added to the window is missing from every test that renders it** — The window's providers and route tree are one component each; a caller supplies only its router and whether it runs under StrictMode.
- ✅ **RG127** **the artboards draw a header the window no longer has, and they are what the next screen is designed against** — An artboard marks each control the window renders with data-control; one drawn but not rendered yet is dashed and left unmarked.

### §RG39 A shared design system, not a copied one

The design this replaces planned to copy shadcn into this repository, so a variant would
be an edit rather than a fork. That reasoning is sound and it was answered by a package
that already exists: `@viglet/viglet-design-system` holds those components, and Turing,
Shio and Dumont render with it. A fourth copy would have been a fourth set of tokens
drifting from three that agree.

What is given up is real: this app cannot edit a component in place, and a change it
needs is a release of somebody else's package. Against that, a token declared here is a
token the other three do not have. The exception that remains shows the supported shape
— the four `--vg-accent-*` variables are re-keyed on `:root` to roadkeep's own site
colours.

The dependency also arrives with a high-severity advisory through `xlsx`, filed as its
own line rather than accepted quietly.

### §RG86 Why a translation is a release

The alternative was a locale directory beside `settings.json`, read at launch the way
the settings themselves are. It is cheap, and it is what somebody asking for their own
language would want. It was rejected for what it makes this app: a program whose visible
text is supplied by whatever is on the disk it starts from. Every string then has two
sources, only one of which the suite can see; the pseudo-locale run stops proving
anything about a shipped build; and a broken file becomes a screen nobody can read
rather than a compile error. So the list is written in `core`, one line per language,
and adding one is editing this repository. The cost is real: a translation waits for a
release. What buys it is that every string is in the bundle that was tested, and
`untranslated` and `stale` run over all of them at once.

### §RG88 Two catalogues, one locale

The alternative was one catalogue: drop RG51's typed lookup for i18next, or re-declare
the package's strings as `MessageKey`s. Both were rejected, for opposite reasons.

Dropping RG51 spends what it bought. `MessageKey` is a type, so a key nobody wrote fails
to compile, and the pseudo-locale run fails on a literal typed into a component. i18next
resolves a missing key to the key itself, at runtime, on screen.

Re-declaring the package's strings is worse: its components resolve their own keys
internally and cannot be handed a translation, so the copy drifts on the release that
rewords one.

So two catalogues, divided by who renders the element — checkable by reading the JSX
rather than by remembering a rule. What is never two is the locale: the package reads it
off the shared i18next instance and cannot be told otherwise, so that instance is the
source the catalogue is fed from.

### §RG63 Bento outside, rows inside

The layer's page shape for a listing is a mosaic of tiles, and this app will not use it
for a backlog. A symptom runs to 120 characters and a tile has room for a name; drawing
lines as tiles truncates the one field a reader scans for, and a tooltip recovering it
is a screen nobody can read without a mouse. Block H's criterion is legibility at the
lengths the format allows, and rows are what that costs.

So the division is the chrome and not the content: the rail, the header, the palette and
the frosted surfaces are the package's, whole, and what sits inside the reading column
is drawn for the shape of the data. `docs/design/` drew both readings, and
`Main.dc.html` is the one it settles on.

Tiles keep every other use the layer intends — a hub, a stats strip, a project card.
