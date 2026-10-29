# Project profile template

Copy to `<work>/controller-profile.md` and fill it in with the user. Use paths relative to the workspace root only. No machine paths, user names or host names.

```markdown
# Controller profile

## Paths (relative to the workspace root)
- Working folder `<work>`: _sdd/
- Ledger: _sdd/ledger.md
- Decisions log: _sdd/decisions.md
- Future features list: _sdd/future.md
- Controller handover: _sdd/controller-handover.md
- Plan(s): <path to the current plan>
- Briefs, reports, reviews: _sdd/<milestone>/

## Repositories
- <repo-a> (branch <branch>)
- <repo-b> (branch <branch>)

## Risky areas (2 critics + arbiter on conflict)
- concurrency and threading
- resource lifetime and error recovery
- build system and dependency gates
- release and packaging gates
- <project-specific areas>

## Tests (tiers; each with its usual time)
- T0, after each change: <only the relevant tests of the changed repo, e.g. a sanity label or a name filter> (<seconds>)
- T1, before each commit: <all tests of the changed repo and of the app, quick checks in the repos between, formatter on changed files, privacy lint> (<minutes>)
- T2, when a task is mostly done and at checkpoints (every ~3 tasks, milestone end): <full workflows on every platform, sanitizers, static analysis; package dry run only for packaging or release changes> (<an hour or more>)
- UI-only changes (a dialog's look or text): <compile, the one relevant test, start the app once and check it; no full runs>
- CI: <what runs on every pull request and on every push to main>
- Configurations that need their own validation when conditional code changes: <list>

## Workstreams and pull requests
- A branch is a workstream (a component or the app) from main: <prefix>/<workstream>; several tasks and fixes, any number of work commits.
- Cleanup before each pull request and after each fix round: the fewest meaningful commits (`git reset --soft` and regroup, or a scripted rebase); `git push --force-with-lease` on the pull request's branch only.
- One pull request per topic; closely related changes together. CI runs on it; findings are fixed in the same pull request.
- Merge method: <rebase merge (default, linear history) | squash | merge commit>, after green CI.
- Who merges: <the user | the controller with the user's go-ahead>.
- Before a release: list the repository's open small items and ask whether they go in first.

## Dependency pinning
- Pin mechanism: <e.g. submodules, a lock file, a version in the build file>.
- Dependents and their components: <app -> component-a, component-b; component-b -> component-a>.
- On main: tags only. Component tags are deliberate, after several pull requests; dependents move to new tags in batches.
- Workstream branches: any commit for joint testing; back on tags before the pull request merges.

## Commits
- Identity: <how it is set per repo>
- Message prefix during a milestone: <e.g. wip:>
- Trailer: <e.g. a Co-Authored-By line>

## Outward writes needing a STOP (in addition to push, tag, release, repo create/rename)
- <e.g. publishing a package, posting an issue>

## Limits (defaults shown; change only with the user)
- Agents at once: 2 + 1 read-only third
- Implementer: handover ~45, hard stop 60. Critic: ~40. Scoped re-review: ~20
- Controller restart: ~100 calls or ~250K context
- Status tick: on, every 30 minutes

## Session-start rituals subagents skip
- <e.g. reading a personal notes vault named by global instructions>
```
