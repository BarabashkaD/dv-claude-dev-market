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

## Tests
- Per task: <build + all tests + formatter on changed files + privacy lint>
- Checkpoint (every ~3 tasks and at milestone end): <release build, sanitizers, static analysis, package tests>
- Configurations that need their own validation when conditional code changes: <list>

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
