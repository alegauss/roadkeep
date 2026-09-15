# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

### §RG257 A verdict word the window uses elsewhere

**`divergente` is `portfolio.gate.drifted` in `pt-br.ts`**, and the filter chip reads
"Verificação divergente {count}". Nothing past the row uses the word: the column is
"Verificação", the count is "achados", the gate screen is "A verificação" and its rows
are "achados". In a window whose rows carry worktree and branch badges (RG199), a thing
that diverged reads as a branch, and the reader who reported this took six findings for
six items that had diverged.

**The Portuguese verdict becomes `reprovada`**, and the chip "Verificação reprovada
{count}". `reprovar` is already this catalogue's verb for what the gate does, since
`gate.notes` is "Dito sem reprovar por isso", so the pill, the chip and the gate screen
share one family of words, and "reprovada · 6 achados" says a check failed and how much
it found.

**English keeps `drifted`**, the word `docs/design/Main.dc.html` draws and `gate.ts` is
written around. There the column and the screen already share "gate", so the pill sits
under the name of the check it reports.

Tests: none new. `wording.test.ts` and `locales.test.ts` hold both catalogues' keys, and
`portfolio.test.tsx` reads the base language. The check is `npm run shots` in pt-BR,
reading the portfolio row and the chip.

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

### §RG258 What a finding's code means, asked of explain

**A finding row draws its code as a pill and the gate's message beside it** (`Finding`
in `Gate.tsx`). The message is about one line. What the class is, why `ref.unresolved`
exists and whether it means different things in different places, is what `explain
<code>` answers. `readExplanation` in `refusals.ts` reads that into `cause` and
`varies`, a live contract test holds it, and nothing draws it.

**The code becomes a disclosure.** Opening it runs `explain` through the read table for
that code, once per code per screen, so a report of six findings over three codes costs
at most three reads, and only for the codes a person opened. What comes back is drawn in
the engine's words, untranslated, as every payload's prose is.

**Its doors are not drawn.** The finding's own remedy already draws them, filled in for
this line, while `explain`'s doors are the class's, with `…` wherever the finding has a
value.

**A build that cannot run it offers nothing.** `capabilities.ts` answers
`byVerb.explain.callable`, and where that is false the code stays a pill: a disclosure
that opens on a refusal is a control that lies.

Tests: `gate.test.tsx`: opening a code reads `explain` once and draws its cause, a
second finding with the same code reads nothing, and no disclosure is drawn where the
capability is off.

On ship: --recorded-in packages/ui/src/Gate.tsx

## Block F — The agent surface (handing one task to Claude Code)

## Block G — The shell (an executable now, a service later)

### §RG49 The signature, and what it needs that code cannot supply

Signing is not work that can be finished by writing anything: it needs a certificate
somebody bought, held somewhere a build can reach. So the line states the requirement
and is set aside for a caller that says it has one, rather than coming back as the next
ready task forever. What can be built without it is the pipeline that would use it, and
the about surface saying plainly that this build is unsigned — which is the honest half
and is worth having on its own.

## Block H — The look (a design system for governed prose)

### §RG62 Joining the checks the other consoles already answer to

Depending on the design system is half of consuming it. The other half is the two
mechanisms Shio and Dumont run.

**The gate is done.** `viglet-ds-check-duplicates` is wired into `npm run lint` over the
three source roots, and a test plants a duplicate and requires it to be found — because
a gate pointed at the wrong directory reports a clean tree in exactly the same words as
a clean tree, which is what both consoles learned the hard way.

**Registration is not, and is deliberately not.** The package's `consumers.json` is the
declared set it holds itself to, and its own reasoning says prose naming a subset as
though it were the whole is a test failure. The entry this app wants is:

```
{ "id": "roadkeep-gui", "name": "roadkeep", "package": "@rk/ui",
  "framework": "vite", "chrome": "console",
  "entries": [".", "./styles", "./fonts", "./preset"] }
```

`accent` is the field to stop at. Every one of the six consumers records `cool`, and the
file says so on purpose: the accent was made a token so a product could re-key without
forking a header, and none had. This app has — amber, in its own `:root`. So adding it
is not a row, it is the first case that file was written to anticipate, and the parity
digest is then required to carry that set.

That is a commit in somebody else's repository with a consequence for five other apps,
which is why it is written down here rather than made quietly.
