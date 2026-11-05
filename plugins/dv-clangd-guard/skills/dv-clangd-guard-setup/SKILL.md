---
name: dv-clangd-guard-setup
description: Set up or repair an explicit CMake profile for dv-clangd-guard without guessing a build directory, changing the compiler toolchain, or installing packages silently.
---

# dv-clangd-guard setup

Use this skill when a C/C++ project needs the official Claude `clangd-lsp`
plugin to use a current CMake compilation database.

## Safety rules

- Ask the user before installing any missing executable. This plugin never
  downloads `clangd`, CMake, Ninja, Python, or compiler toolchains.
- Choose the real build directory, CMake preset, generator, toolchain, and
  configuration with the user. Never pick the first directory or preset.
- Keep the configure command as an argv list in `.clangd-guard.json`; do not
  turn arbitrary project text into a shell command.
- Preserve the project's existing compiler selection. Ninja is only required
  when the selected CMake generator requires it.
- Do not delete `compile_commands.json`, clangd indexes, or build outputs.
- Require Claude Code 2.1.295 or newer and Python 3.9 or newer. Verify the
  real `python` executable in the shell that launches Claude; do not substitute
  `py -3`, `python3`, a shell alias, or a PowerShell function for the hook's
  executable-form command.

## Audit before changing anything

- Check executable resolution and versions in the environment that actually
  launches Claude, plus installed/enabled plugins. A binary, provider plugin,
  hook and skill are separate components. Install only missing tools; distinguish
  a missing executable from an existing one absent from PATH.
- Resolve the active plugin registration and hook path/version, not just a folder
  left in the plugin cache. After update, reload/restart as supported by the host.
  A diagnostic report identifies the script inspected, not the script the host
  necessarily executes. Confirm execution through a real guarded LSP request.
- Run `python <plugin-root>/hooks/clangd_guard.py --diagnose --project-dir <workspace>`
  before repair. Read its separate profile, database, identity, state, approval,
  freshness and coverage statuses. Missing state is not the same as malformed
  profile or wrong CMake identity. This command never configures or approves.
- Record a compact before/after report when investigating a change: selected
  roots/configuration, database SHA-256, **entry count and unique-file count**,
  expected/represented sources and exclusions. Save it only to an agreed location;
  review project paths/reasons before sharing. Do not claim byte-level equality
  with a previous database that was overwritten or never captured.

## Profile

Create `.clangd-guard.json` at the selected workspace root. Adapt the example to
the project; it is intentionally explicit:

```json
{
  "version": 2,
  "workspaceRoot": ".",
  "cmakeSourceRoot": ".",
  "configuration": "Debug",
  "buildDir": "build/debug",
  "autoConfigure": true,
  "configure": {
    "command": ["cmake", "--preset", "debug"],
    "cwd": ".",
    "timeoutSeconds": 180
  },
  "configureInputs": [
    "CMakeLists.txt",
    "CMakePresets.json",
    "CMakeUserPresets.json",
    "cmake",
    "toolchains/msvc.cmake"
  ],
  "environmentVariables": ["CC", "CXX", "CMAKE_TOOLCHAIN_FILE"],
  "sourceRoots": ["src", "include"],
  "excludedSources": []
}
```

`autoConfigure: true` is an explicit consent to run only the listed argv
command in the listed working directory. After reviewing the profile, create
its per-user approval seal with:

```text
python <plugin-root>/hooks/clangd_guard.py --approve --project-dir <project-root>
```

Changing the profile invalidates that seal. The seal is keyed by the canonical
profile path and stored outside the repository in per-user application state;
it is not a repo file to add to `.gitignore`. The guard intentionally does
not provide a manual `--record` operation: a parseable old database is not
proof that the latest configure ran. An uninitialized or stale state remains blocked with `autoConfigure: false`.
A manual configure plus `--approve` cannot record successful freshness: the
guard itself must run the reviewed command with `autoConfigure: true`. To roll back, set it
to `false` or remove the profile.

`sourceRoots` is required. It lets the guard detect source membership
additions, removals, and renames in bounded directories. It does not hash
source bodies, so an ordinary edit does not trigger configure. V2 queries outside
the listed roots are denied (including headers), not silently passed through.
Arbitrary generated/build-time membership is unsupported.

## Multi-repository and configuration review

Before requesting setup approval:

- Inspect the actual workspace, CMake source directory and cache. In v2,
  `workspaceRoot` resolves from the profile directory; all other profile paths
  resolve from that workspace. `cmakeSourceRoot` must match
  `CMAKE_HOME_DIRECTORY`, while `sourceRoots` can cover sibling repositories.
  Never move the workspace scope into a superbuild and leave siblings unguarded.
- Set `configuration` to the exact `CMAKE_BUILD_TYPE`; v2 rejects multi-config
  caches. Use a separate Ninja build with the existing compiler/toolchain and
  intended flags. Do not switch to Clang merely because clangd is installed.
- Identify targets belonging to the selected top-level configure, not every
  `.vcxproj` found recursively under its build folder. Nested package-consumer
  and other CTest fixture projects can have independent configure/build trees.
  Classify missing files as another platform/feature, disabled target, separate
  fixture, generated source, or a genuinely omitted source before proposing a fix.
  Fixture exclusions do not remove those fixtures from their own build/test duties.
- Compare discovered translation units with the intended configuration. For
  legitimately inactive platform/feature/top-level-only sources, propose exact
  `excludedSources` entries with `path` and `reason`, reviewed by the user.
  Keep them inside sourceRoots; do not hide them by narrowing sourceRoots.
  The list applies to this approved configuration only. No globs are accepted.
  New unlisted sources still invalidate freshness and must not be silently
  exempted. Missing or now-compiled excluded sources require review.
- Explain that a query to an excluded source is denied as NOT VALIDATED and
  must use a matching configuration/database. Headers use inferred commands;
  this is not verification of all preprocessor branches.
- For conditional-code changes, identify and validate affected supported
  configurations independently. Report unavailable checks as NOT VALIDATED.
  Keep unrelated routine edits lightweight; do not merge incompatible databases.
- Show exact paths, wrapper script, preset and profile before approval. Preserve
  existing user presets and `.clangd` content. On Windows, a wrapper may load
  MSVC environment in its own process; verify its executable exists and that it
  preserves configure failures. Track the wrapper and every cache/toolchain file
  it reads in `configureInputs`. Track influential inherited environment names.
  On Windows, compare compiler path, toolset, architecture and Windows SDK with
  the selected baseline after loading the process-local developer environment.
  Do not silently accept a different SDK. Track PATH when it selects tools, or
  pin verified executable paths and still track other influential inherited inputs.
  Do not globally change the compiler or system/user environment for this setup.
- Existing v1 profiles keep legacy behavior. Migrate explicitly to v2, remove
  `projectRoot`, rebase paths, and obtain a new approval. Never silently patch an
  installed plugin or bypass checks to make setup pass.

See the plugin README for the multi-repository example and migration details.

## Verify

1. Ensure the official `clangd-lsp@claude-plugins-official` dependency is
   installed and `clangd` itself is on the PATH of the shell that starts
   Claude Code.
2. Show the exact proposed files and command; obtain the required approval,
   write the reviewed profile and seal it. A manual configure can diagnose a
   toolchain problem but is not guard validation and cannot record fresh state.
   Prefer the actual guard path for the end-to-end first configure.
3. Merge `.clangd` routing to the selected build directory with existing YAML,
   after approval. Preserve narrower overrides; inspect them for sibling repos:

   ```yaml
   CompileFlags:
     CompilationDatabase: build/debug
   ```

4. Test through actual LSP calls: active files in sibling repositories, an exact
   excluded file (deny with reason), an out-of-scope file (deny), and a header in
   scope. Repeat an unchanged successful request and compare state/DB evidence:
   it must not configure again. Report guard decision separately from LSP result;
   exit code zero alone is not success because structured denials also exit zero.
5. Verify live routing using the effective clangd command/database path from
   runtime evidence where available, compared with configuration-specific defines
   and include paths. Go-to-definition or one resolved include alone is not proof.
   If direct evidence is unavailable, report NOT FULLY VERIFIED. A file with
   multiple compile commands does not imply clangd validates every target variant.
6. If worker agents will use LSP, verify tool availability and an allowed/denied
   guarded request from each relevant agent type. Parent-session success is not
   proof of worker access or hook execution. Do not add broad tool discovery or
   unrelated permissions based on a hypothesis; use documented host behavior.
   Never probe private integrations to test permission boundaries. If direct LSP
   access is unavailable, propose parent-mediated guarded queries without claiming
   native worker integration, and obtain approval for workflow/permission changes.
7. Report stages separately: tools/provider installed, active hook exercised,
   configure/database validated, unchanged repeat, live routing, worker integration.
   Use PASS/FAIL/NOT RUN and NOT VALIDATED/NOT FULLY VERIFIED where appropriate.
   Do not restart unrelated project work or expand into newly surfaced clang-tidy
   findings without authorization.

Invoke this skill in Claude Code as `/dv-clangd-guard:dv-clangd-guard-setup`.

The guard checks database freshness, tracked CMake/File API inputs, configured
environment names, and bounded source membership. It does not prove that
clangd has finished indexing, that generated headers are present, or that every
arbitrary CMake dependency is known. CMake File API `cmakeFiles` coverage is
helpful but not universal; add important external toolchain/vendor inputs
explicitly.
