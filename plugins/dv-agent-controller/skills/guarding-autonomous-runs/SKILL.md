---
name: guarding-autonomous-runs
description: Use when an agent starts or supervises a long, heavy or unattended run (checks, builds, batch scripts, an autonomous series of steps), when a run is slow or silent, when a worker reports "success", when work is split between a coordinator and workers, or when several agents run at once. Holds the flexible 5-minute rule, verify-the-artifact, candidate-not-release for autonomous series, and the coordinator/worker rules. Domain-neutral; other skills link here instead of restating it.
---

# Guarding autonomous runs

Rules for any agent that runs long work without a person watching. All numbers are defaults: a project profile or the plan may override them.

## 1. The 5-minute rule (flexible)

5 minutes is the default limit for one run. The decision to stop rests on progress and warnings, not on the clock alone.

**Visible progress** is a heartbeat: the script appends lines `PROGRESS <n>/<N> <label>` to a log file in its own round folder (never to stdout, which stays for the single result line), and the watcher tails that file. Progress means new heartbeats keep arriving with `n` growing, and no errors and no warnings. A single long call that cannot emit heartbeats is judged by the process's CPU time: it must keep growing, and the 5-minute limit still applies.

**Stop at once, without waiting for the limit**, when any of these holds: no new heartbeat for the silent interval (default 60 s; the plan may override it), or CPU time of a heartbeat-less call not growing; a warning appears; an error is suspected (odd numbers, repeated lines, a result that looks wrong). "No progress for 6 minutes" means the run should have been stopped after the first 60 s of silence; do not wait for the limit to confirm it. **The action on a stop is: terminate the process now, then localize or divide (below).**

**A larger limit** is allowed only when the plan assigned it beforehand, with a number, for that run. Without it the limit is 5 minutes even if progress is visible. You may not raise the limit yourself mid-run. Even with an assigned limit, progress and warnings still decide: stop at once on a stop signal.

Example: a full check runs 298 s with 4 parallel runs and heartbeats keep arriving. 298 s fits the default limit outright. A run still going at 300 s continues only if the plan assigned a larger limit with a number; otherwise terminate it and divide the check into parts (below). Load slows runs; see `references/multi-agent.md`.

**After a stop, two paths.** Both lead to runs of at most 5 minutes each:
1. **Localization.** Run sub-checks to find the FIRST cause (not a list of causes), fix it, repeat the run.
2. **Division.** Split the work into parts (zones, boxes, groups, items), run each part within 5 minutes, and combine the results. Divide only when the results combine (counts add; differences and intersections per part join); if they do not combine, localize instead.

**Anti-goal: hours of searching.** If the first cause is not found within about 30 minutes in total, stop and report to the coordinator or the user what is known: what was run, the numbers, what was ruled out, what to try next. Do not keep going.

Run long processes in the background with a watcher that tails the heartbeat log and terminates the process on a stop signal. Foreground waits stay short; never block on a silent process.

## 2. Verify the artifact, not the answer

"Success" from a script, tool or worker is not evidence. Before reporting a step done, check the thing itself:

- the file exists, is non-empty and has a fresh timestamp;
- the result is re-read from disk (reopened, reloaded, re-parsed), not taken from memory;
- the numbers match: sizes, counts, totals against the expected values or the previous state;
- for something a person will open: open it again in a fresh process and look for a clean start;
- a snapshot or export was actually produced, not only requested.

Report what was checked and the numbers. If a check could not be done, say so; do not write "verified".

## 3. Autonomous series gives a candidate

By default the result (a view or section plus the key numbers) is shown to the user before the check stage runs, unless the user granted autonomy.

If the user explicitly allowed autonomous work, the series runs to the end and hands over a **candidate**: the result plus the evidence (numbers, checks passed, checks skipped, assumptions). Then:

- only the user accepts a new version; the series never promotes its own result;
- manufacturing, printing, publishing, pushing, releasing and any irreversible external action need the user's direct permission, even inside an autonomous series; permission for the series is not permission for these;
- on a block (stop signal, unresolved question) the series stops and reports; it does not guess.

## 4. Coordinator and worker

- The coordinator keeps a local plan with a digest of the numbers, not the project history, and gives the worker only what the task needs.
- The worker has no project history and asks the coordinator when something is unclear. It does not search other rounds' files for answers.
- Scripts print only a single machine-readable result line (for example `RESULT {json}`); logs go to a file.
- The next stage (build, then checks) goes to the same worker as a continuation, not a new one: it already holds the context.
- The coordinator re-checks the worker's assumptions and numbers (baselines, how a total was decomposed) instead of accepting them. A number the coordinator did not check is reported as the worker's claim.
- Worker messages are short: start, key numbers, obstacles.

## 5. Several agents at once

Single shared resources (a GUI window, a live-session bridge, a port), the cap on heavy parallel runs, folder isolation and reporting limits are in `references/multi-agent.md`. Read it before starting more than one worker.

## Checklist before a long run

1. Is the limit 5 minutes, or a larger one assigned in the plan with a number?
2. Does the script write `PROGRESS n/N label` heartbeats to a log file (stdout stays result-only), and is a watcher tailing it with the silent interval (default 60 s)?
3. What happens on a stop: localize or divide?
4. Which artifact will be checked at the end, and how?
5. Does anything here need direct permission (manufacture, publish)? Then stop before it.
