# Brief templates

Placeholders: `<work>` = the working folder from the controller profile, `W` = the workspace root. Write paths relative to `W`. Keep each brief under ~40 lines.

## Task brief (implementer)

```markdown
# <milestone> <task> brief: <title> (<risky|mechanical>)

W = the workspace folder. Repos on branch <branch>; nothing pushed.
Start heads: <repo> <hash>, ...

## Budget
WIP commit + handover in the report at ~45 calls; hard stop 60. Background runs with foreground
waits of at most 270 s. Read by range; keep tool output small. Skip <session-start rituals>.

## Task
1. The plan text: <plan path> section <n> "<title>", lines <a>-<b> (exact; check them before you dispatch).
2. Review hand-overs (read only these): <review file>: <finding IDs>.
3. <ordering constraint, e.g. "change lib first, then bump its pin in app">. You are the only writer in <repos>.

## Rules
- Batch rule: run the complete test set once, collect every failure, group by root cause, fix together, re-run once.
- Configurations: validate each affected configuration or report it as NOT VALIDATED.
- Privacy: no machine paths, user or host names, no internal IDs in committed text.
- Commits: <prefix>, <trailer>. Do not push, tag or write to any hosting service.

## Verify
<exact builds, tests, lints and checks>

## Report
<work>/<milestone>/task-<task>-report.md: commits per repo (base..head), test results with counts,
skipped items with reasons, open issues. On handover also: done, left (concrete next steps), WIP commit, test status at the WIP head. Reply in 3 lines.
```

## Fix brief (fixer)

```markdown
# <task>-F brief: fix round (<tier>)

W = the workspace folder. Start head: <repo> <hash> (the reviewed head).

## Budget
<same budget lines as the task brief>

## Findings to fix (and nothing else)
- <review file> <ID> (<file:line>): <one-line summary>. Decision: <fix as suggested | fix differently: how>.
- ...
Not fixed (logged, leave alone): <IDs>.

## Rules
<same rules as the task brief>

## Verify
<the checks that cover the fixed findings, plus the per-task test set>

## Report
<work>/<milestone>/task-<task>-F-report.md: per finding FIXED / NOT FIXED with commit and evidence,
the fix range base..head, test results. Reply in 3 lines.
```

## Continuation brief (after a HANDOVER)

```markdown
# <task> continuation <n>

Read <previous report / handover file> first: it lists what is done and what is left.
Start from WIP commit <hash>. The original brief <path> still applies.

## Budget
<same budget lines>

## Left to do
<copy the "left" list from the handover, nothing more>

## Report
Append a section "Continuation <n>" to <the same report file>. Reply in 3 lines.
```

## Review request (critic)

```markdown
# <task> review <A|B> (<tier>)

## Budget
~40 calls (scoped re-review: ~20). Read-only on all repositories; write only the review file.
Read by range; never print whole diffs or logs.

## Inputs
- Package: <work>/<milestone>/<task>-review.txt (repos, base..head, changed files)
- Brief: <path>. Report: <path>. Plan section: <path> lines <a>-<b>.

## Lens
<A: correctness, concurrency, resource lifetime | B: API, build, docs, tests | arbiter: decide the
conflicting findings <IDs> from <review files> | re-review: findings <IDs> only, FIXED / NOT FIXED>

## Output
<work>/<milestone>/<task>-review-<A|B>.md in the review file format of the critic agent.
Reply in 3 lines: C/I/M counts, verdict, file path.
```

## Verifier brief (checkpoint, no commits)

```markdown
# <checkpoint> brief: <platform> (fresh verifier; local runs only, NO commits)

## Budget
Handover in the report at ~45 calls; hard stop 60. Long runs in the background.

## Steps
1. <full build and test workflow per configuration>
2. <package / dry run with the expected names and versions>
3. <scripted smoke test; steps that cannot be scripted are marked "for the user">
4. <fresh-clone test in a short scratch path; delete it afterwards>
5. <privacy audit of new or changed files and commits>

## Rules
No edits and no commits. A failure is reported, not fixed (batch rule: run everything, group failures
by root cause). A timing-only flake under load gets one rerun, noted in the report.

## Report
<path>: per step PASS/FAIL with evidence lines, failures grouped by root cause, items for the user.
Reply in 3 lines.
```
