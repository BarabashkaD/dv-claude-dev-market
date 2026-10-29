# Changelog

## 0.3.0

- Workstreams and pull requests replace "one small pull request per change" and "squash merge only": a branch is a workstream with several tasks; a cleanup pass regroups the work commits into the fewest meaningful commits before the pull request and after each fix round (non-interactive, `--force-with-lease` on the pull request's branch only); one pull request per topic; the merge method is a profile field (default: rebase merge); before a release, open small items are offered for inclusion.
- Dependency pinning: main depends on tags only; component tags are deliberate; dependents move to new tags in batches; workstream branches may pin any commit and return to tags before the merge.
- Workstream planning: the controller groups planned and open tasks into workstreams that minimise version bumps and test cycles and shows the grouping before execution.
- A cleanup brief template; the implementer and the critic check pins and commit grouping.

## 0.2.0

- Test tiers in the project profile, the controller skill, the implementer and the briefs: T0 after each change, T1 before each commit, T2 at task end and checkpoints, a short check for UI-only changes, and CI on pull requests.
- Changes and merges: a branch per change, one small pull request with CI, fixes in the same pull request, squash merge after green CI; the profile names who merges.

## 0.1.0

- Initial controller skill with the project profile, ledger, decision and handover templates.
- Brief-writing skill with task, fix, continuation, review and verifier brief templates.
- Generic `implementer` and `critic` agent definitions.
- Pressure-test fixes: findings are downgraded only with a logged reason, outward writes are made ready before asking, exact line ranges, budget before the task, a limit after the batch re-run, and fuller handovers.
