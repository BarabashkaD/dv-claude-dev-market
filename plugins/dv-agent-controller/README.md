# dv-agent-controller

A development policy for Claude Code: one session acts as the **controller**, and every task runs in a fresh subagent. The controller dispatches, adjudicates reviews and keeps records. Agents write their work to files and reply in 3 lines.

It is documentation only: two skills and two agent definitions. No hooks, no scripts, no dependencies.

## Install

```text
/plugin marketplace add BarabashkaD/dv-claude-dev-market
/plugin install dv-agent-controller@dv-claude-dev-market
```

## Contents

| Component | Use |
|---|---|
| Skill `controlling-subagent-development` | The controller's loop: classify, brief, dispatch, review by tier, decide, log. Limits, STOP gates, restart and status tick. Templates for the project profile, the ledger line, the decision entry and the controller handover. |
| Skill `writing-agent-briefs` | The brief and dispatch-prompt shape, with templates for task, fix, continuation, cleanup, review and verifier briefs. |
| Agent `implementer` | Implements, fixes or checks one task. Budget first, batch test rule, handover at ~45 calls. |
| Agent `critic` | Read-only reviewer, re-reviewer or arbiter. Writes one review file with a verdict, C/I/M counts and file:line evidence. |

## Use it in a project

1. Start a session in the workspace and say: "You are the controller. Use `dv-agent-controller:controlling-subagent-development`."
2. On first use the controller creates `<work>/controller-profile.md` with you. `<work>` is a working folder you choose, for example `_sdd/` at the workspace root. Keep it out of the repositories or ignore it there.
3. Give the controller a plan. It runs task by task and stops at every push, tag, release or repository change for your go-ahead.

## Policy in short

- A fresh agent per task; handover through files, never follow-up messages to a running agent.
- Risky tasks: 2 critics with different lenses, an arbiter on conflict, a scoped re-review after fixes. Mechanical tasks: 1 critic, a short re-review only after Critical or Important findings.
- Budgets: implementer handover at ~45 calls, hard stop 60; critic ~40; scoped re-review ~20.
- At most 2 agents at once plus 1 read-only third; one writer per repository; the next task may run while the previous one is in review.
- Tests by tier: T0 (relevant tests) after each change, T1 before each commit, T2 (full workflows, sanitizers, static analysis) at task end and checkpoints; a short check for UI-only changes. Batch rule: run all, collect all failures, fix together, re-run once.
- Workstream planning: before execution, the controller groups all planned and open tasks into workstreams (same repository or release together) to minimise version bumps and test cycles, and shows the grouping to you.
- Workstreams and pull requests: a branch is a workstream with several tasks and any number of work commits; a cleanup pass regroups them into the fewest meaningful commits before the pull request; one pull request per topic, CI on it, fixes in it followed by another cleanup. The profile names the merge method (default: rebase merge, linear history) and who merges. Before a release, the controller asks whether open small items go in first.
- Dependency pinning: on main every repository depends only on tagged versions; components are tagged deliberately after several pull requests, and dependents move to new tags in batches. A workstream branch may pin any commit for joint testing and is back on tags before its merge.
- The controller restarts at ~100 calls or ~250K context through a handover file.

## Agent model

The agents use `model: inherit`, so they run on the controller's model. To pin a model, override the agent in your project's `.claude/agents/`.
