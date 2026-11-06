# Multi-agent rules

Defaults; a project profile or the plan may override them.

## Single shared resources

- A GUI application window, a live-session bridge to it (an MCP server, a socket, a fixed port) and the user's open session are one resource. Only one worker uses it at a time, by the coordinator's permission.
- GUI runs go strictly one after another. A shared profile writes its configuration on exit and leaves recovery files that disturb the next start.
- Subagents do not start GUI runs. The coordinator does, after checking that no user window is open (ask the user to close it and wait if it is).
- Do not run a GUI run and a live-bridge session at the same time: they compete for the same port and profile.

## Heavy parallel runs

- Parallel headless runs are fine, but they compete for CPU. The plan sets the cap on simultaneous heavy runs from a measured comparison (one run alone against several in parallel on this machine).
- Example: one full check took 260 s alone and 298 s with 4 parallel runs. The slowdown is modest, yet it can push a run over the 5-minute limit. Under load either assign a larger limit in the plan beforehand, or divide the run into parts.
- Under load the watcher judges heartbeats and CPU time, not elapsed time alone: a loaded but advancing run is not stalled, and a run silent past the silent interval is stalled at any load. Example of a heartbeat-less call: a single long geometry boolean or section; watch its CPU time.
- Independent parts (zones, items, files) can be spread across workers when their results combine.

## Isolation

- Each worker writes only into its own round folder. Inputs are read-only.
- Reusable intermediate outputs (exported parts, caches) are shared read-only between rounds.
- No worker edits another worker's folder or the coordinator's plan.

## Exchange

- Short messages to the coordinator: start, key numbers, obstacles.
- A question goes to the coordinator, not into a search through other rounds.
- The next stage is a continuation of the same worker: cheaper than a new start.
- The coordinator re-checks the worker's assumptions and numbers.

## Environment limits

- Where the environment blocks subagent `.md` writes, the subagent's report goes in its final reply or in a machine-readable file in its own folder (for example `evidence/report.json`), and the coordinator writes the human report. A report path named in the dispatch prompt wins over this.
- A subagent cannot see its own context counter. The coordinator takes token use from the completion notice of the subagent.
