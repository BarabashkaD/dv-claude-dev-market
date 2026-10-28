# Changelog

## 0.2.0

- Test tiers in the project profile, the controller skill, the implementer and the briefs: T0 after each change, T1 before each commit, T2 at task end and checkpoints, a short check for UI-only changes, and CI on pull requests.
- Changes and merges: a branch per change, one small pull request with CI, fixes in the same pull request, squash merge after green CI; the profile names who merges.

## 0.1.0

- Initial controller skill with the project profile, ledger, decision and handover templates.
- Brief-writing skill with task, fix, continuation, review and verifier brief templates.
- Generic `implementer` and `critic` agent definitions.
- Pressure-test fixes: findings are downgraded only with a logged reason, outward writes are made ready before asking, exact line ranges, budget before the task, a limit after the batch re-run, and fuller handovers.
