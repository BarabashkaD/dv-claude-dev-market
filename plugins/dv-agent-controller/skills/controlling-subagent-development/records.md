# Controller records

Three files, all append-only. Keep entries to one line where possible. No internal IDs from other projects, no machine paths.

## Ledger line

One line per state change of a task:

```text
<date> <task> [<risky|mechanical>] <STATUS> <repo> <base>..<head> -> <report path>; next: <action>
```

STATUS is one of: DISPATCHED, HANDOVER, DONE, IN REVIEW, FIX, COMPLETE, BLOCKED, STOP (waiting for the user).

Example:

```text
2026-01-12 T7 [risky] DONE app 1a2b3c4..5d6e7f8 -> _sdd/m2/task-T7-report.md; next: critics A (concurrency) + B (API)
```

## Decision entry

One entry per adjudication or per choice between alternatives:

```text
- <TASK>-<KIND> (controller <date>): <verdict>. <how each finding group is handled>. <why a re-review is or is not needed>. <next step>.
```

KIND: REV (review adjudication), DEC (design or process choice), PROB (problem found).

Example:

```text
- T7-REV (controller 2026-01-12): reviews A ACCEPT (C0 I0 M3), B ACCEPT_WITH_FIXES (C0 I1 M2), no conflict. B-I1 and the 5 minors go to one fix round T7-F in app; scoped re-review of B-I1 only. T8 may start in lib meanwhile (other repo).
```

## Controller handover

Append a new section; the newest section supersedes the older ones.

```markdown
## Handover <n> (<date time>) - READ THIS FIRST (supersedes <n-1>)
- Done: <tasks COMPLETE>; heads: <repo> <hash>, ...
- Running: <agent kind, task, output file> or "nothing"
- If an output file is missing after the restart: <re-dispatch instruction with the same lens and package>
- Pending decisions: <reviews to adjudicate>
- Next action: <exact next dispatch>
- Then: <ordered list of the remaining tasks and STOP gates>
- Rules in force: <only the run-specific ones; the profile holds the rest>
- Recreate: status tick (<schedule>, <prompt>)
```

Resume line to give the user (paste after `/clear`):

```text
You are the controller. Use dv-agent-controller:controlling-subagent-development. Read <work>/controller-handover.md (newest section) and continue.
```
