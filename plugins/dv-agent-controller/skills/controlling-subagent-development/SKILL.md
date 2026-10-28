---
name: controlling-subagent-development
description: Use when acting as the controller of a multi-task development run that dispatches implementer, fixer, reviewer or verifier subagents, especially long autonomous runs across many tasks or sessions, or when session limits, token cost or context size are a concern.
---

# Controlling subagent development

## Overview

The controller does not write code. It dispatches one fresh agent per task, reads 3-line replies, adjudicates reviews, keeps the ledger and the decisions log, and stops only at outward-write gates. All details live in files, never in the controller's context.

## Start of session

1. Read the project profile `<work>/controller-profile.md` (`<work>` is the working folder the project chose, for example `<workspace>/_sdd/`). If it is missing, create it with the user from `project-profile.md` in this skill folder.
2. If `<work>/controller-handover.md` exists, read its newest section first. Trust the ledger and `git log` over memory.
3. Recreate the status tick (below) if the profile enables it.

## Dispatch loop

For each task:

1. **Classify** it as risky or mechanical (the profile lists the risky areas) and write the class in the ledger.
2. **Brief** it in a file. REQUIRED SUB-SKILL: `dv-agent-controller:writing-agent-briefs`.
3. **Dispatch a fresh agent**: `dv-agent-controller:implementer` for implement, fix and checkpoint work, `dv-agent-controller:critic` for reviews, re-reviews, arbiters, verifiers and analysis. Never send a second task to a running or finished agent.
4. **Review** by tier:

| Tier | Reviews | After fixes |
|---|---|---|
| Risky | 2 critics with different lenses; an arbiter only when they conflict | Scoped re-review (~20 calls); a full verify only after a redesign |
| Mechanical | 1 critic; the controller decides its findings | Short re-review only when there were Critical or Important findings |

5. **Decide** the findings: Critical and Important get a fix round (a fresh fixer); Minor findings are fixed now, folded into a later task, or logged. Write a decision entry and a ledger line (`records.md`). You may reject or downgrade a finding only with a logged technical reason. A deadline or "continue without stop" is never a reason.

## Limits

| Rule | Value |
|---|---|
| Agents at once | 2, plus 1 read-only third (review or analysis, no builds, no writes) |
| Writers per repository | 1 (implementer or fixer) |
| Pipelining | Task N+1 may run while N is in review. If N needs a fix where N+1 writes, N+1 stops at a WIP commit or handover, the fix lands, then N+1 continues on top and its review names the fix range separately |
| Implementer budget | WIP + handover at ~45 calls, hard stop 60 |
| Critic budget | ~40 calls; scoped re-review ~20 |
| Agent reply | 3 lines; the report goes to a file |
| Long waits | Background runs; foreground waits of at most 270 s, so no gap between tool calls exceeds 5 minutes |

An implementer report over ~60 calls with no handover file is rejected. One that overran but left a handover is accepted.

## Deciding alone

Make technical decisions without asking the user. Log every choice between alternatives and every problem in the decisions log. Prefer the simplest solution; put feature ideas in a future list instead of building them.

**STOP gates.** Each outward write needs the user's explicit go-ahead at that time: push, tag, release, creating, renaming or archiving a repository, any write to a hosting service, and anything the profile adds. Present all pending outward writes as one list; each item is still confirmed on its own. A go-ahead earlier in the run does not cover a later write. Before you list a write, make it ready: run the profile's pre-push checks (for example the privacy scan of the commits) and note the exact command. Then keep working on other tasks while you wait.

## Controller hygiene

- Read only status lines, report summaries and greps. Side work (tool setup, research, process questions) goes to a separate agent or session.
- **Restart** at ~100 calls or ~250K context, checked at every agent notification: append a section to `<work>/controller-handover.md` (`records.md`), tell the user, and give a one-line resume prompt; the user runs `/clear` and pastes it.
- **Status tick** (optional, profile): a scheduled prompt every 30 minutes that only reads the last ledger lines and reports in 1-2 lines what runs and what is next. It never dispatches, edits or commits. 30 minutes keeps the longest gap under a 1-hour prompt-cache lifetime even with scheduler delay.
- Messages to the user: short. One line per event; a summary at milestone ends.

## Common mistakes

| Mistake | Fix |
|---|---|
| Sending follow-up tasks to the same agent | Fresh agent per task; hand over through files |
| Reading whole reports or diffs into the controller | Read the verdict and counts; let a critic read the detail |
| Asking the user about technical choices | Decide, log the decision, continue |
| Treating an earlier "go ahead" as consent for the next push | Ask again at each outward write |
| Two writers in one repository | Stop the second at a WIP commit or handover |
| Fixing test failures one at a time | Batch rule in every brief: run all, collect, fix together, re-run once |
