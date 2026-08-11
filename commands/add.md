---
description: File one task line from words you already typed
argument-hint: <block> | <symptom> | <why>
allowed-tools: mcp__roadkeep__add, mcp__plugin_roadkeep_roadkeep__add, mcp__roadkeep__next_id, mcp__plugin_roadkeep_roadkeep__next_id, Bash(roadkeep add:*), Bash(roadkeep next-id:*)
---

File the task the user described in `$ARGUMENTS`.

Read it as up to three parts separated by `|`: the block label, the symptom, the why. The
parts arrive in that order; a single `|` means the block came first and the rest is the
symptom.

Then call this session's `add` tool — `mcp__roadkeep__add` where the project declares the
server, `mcp__plugin_roadkeep_roadkeep__add` where the plugin provides it — with those parts
as `block`, `symptom` and `why`, or
`roadkeep add --block … --symptom … --why …` if that tool is not connected. Two rules bind
this, and neither is negotiable:

1. **Pass the user's words verbatim.** Do not shorten, rephrase, capitalize, translate or
   "improve" either field, and never compose one that was not typed. If the symptom or the
   why is missing, ask for it in one sentence and stop. The tool validates and renders; it
   does not write prose, and neither do you on its behalf.
2. **Report the answer as it came back.** On success, print the id, the file and the line.
   On a refusal, print what it said — it names the field, the length and the limit, which is
   what the user needs to decide what to cut. Do not retry with a shortened field.

If the user typed something that is a fix rather than a fault ("add caching", "use a queue"),
say so before calling: a line named after its solution cannot be falsified, so it never gets
closed. Ask what does not work today. That judgement is yours, because no schema can make it.
