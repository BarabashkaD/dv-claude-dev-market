---
name: writing-agent-briefs
description: Use when writing the brief or dispatch prompt for an implementer, fixer, continuation, verifier, reviewer or arbiter subagent, or when a subagent overran its budget, returned a long reply or left no report file.
---

# Writing agent briefs

## Overview

A brief is a short file the agent reads first. It points at the plan and the inputs instead of copying them, puts the budget first, and names one report file. The dispatch prompt is 3-6 lines that name the brief.

## Brief shape

Every brief has these parts, in this order:

1. **Title**: task, kind, tier.
2. **Context**: the workspace placeholder, branches, start heads. Nothing pushed or what is.
3. **Budget (before the task)**: call limits, wait limit, output size.
4. **Task**: numbered steps that point at plan sections and review findings by ID and line range.
5. **Rules**: one writer per repo, batch test rule, privacy, commit rules, what not to touch.
6. **Verify**: the exact checks that prove the task is done.
7. **Report**: one file path, its required contents, "Reply in 3 lines".

Templates for each kind: `templates.md` in this skill folder.

## Fixed lines

Copy these into every implementer, fixer and continuation brief:

- Budget: "WIP commit + handover in the report at ~45 calls; hard stop 60. Background runs with foreground waits of at most 270 s. Read by range; keep tool output small."
- Batch rule: "Run the complete test set once without stopping at the first failure, collect every failure, group them by root cause, fix them together, re-run the complete set once. If failures remain after the re-run, do one more batch at most, then report them as open (BLOCKED if they block the task). A test that also fails on the start head is pre-existing: report it, and fix it only if the brief says so."
- Configurations: "A single build configuration is a baseline only. When conditional code changes, validate each affected configuration with its own build and tests, or report it as NOT VALIDATED."

Critic briefs use "~40 calls" (scoped re-review: "~20 calls") and "read-only: write only the review file".

## Dispatch prompt shape

```text
Budget: <limits>. Skip <session-start rituals named in the profile>.
<Kind> for <task>: read <brief path> first; it wins over anything else.
<Only what is not in the brief: a head hash, a message from another review.>
Report: <report path>. Reply in 3 lines.
```

## Review packages

Give critics a package file, not a pasted diff: repo, base..head per repo, the files changed (stat only), the brief and report paths, and the lens. Two critics on a risky task get different lenses (for example A: correctness and concurrency, B: API, build and docs).

## Common mistakes

| Mistake | Fix |
|---|---|
| Pasting plan text or diffs into the prompt | Point at file and line ranges |
| Budget at the end of the brief | Budget is section 3, before the task |
| Several report files or none | Exactly one report path |
| Brief says "fix the findings" | Name each finding by ID with its review file and line |
| Same lens for both critics | Name two different lenses |
| Approximate line ranges ("~300-330") | Check the range and write it exactly |
