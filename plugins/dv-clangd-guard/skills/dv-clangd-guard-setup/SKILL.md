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
- Existing v1 profiles keep legacy behavior. Migrate explicitly to v2, remove
  `projectRoot`, rebase paths, and obtain a new approval. Never silently patch an
  installed plugin or bypass checks to make setup pass.

See the plugin README for the multi-repository example and migration details.

## Verify

1. Ensure the official `clangd-lsp@claude-plugins-official` dependency is
   installed and `clangd` itself is on the PATH of the shell that starts
   Claude Code.
2. Confirm the selected CMake command succeeds manually once, with
   `CMAKE_EXPORT_COMPILE_COMMANDS=ON` (or the equivalent preset cache option).
3. If the build directory is outside the source tree's default clangd search,
   merge this into the project-root `.clangd`, preserving all existing keys and
   obtaining explicit approval before editing:

   ```yaml
   CompileFlags:
     CompilationDatabase: build/debug
   ```

   Replace `build/debug` with the exact configured build directory. The guard
   cannot prove that a live clangd provider loaded the database.
4. For multi-repository workspaces, test an active translation unit in each
   sibling repository, an intentionally excluded file (must deny with reason),
   an out-of-scope file (must deny), and a header in approved roots. Verify the
   DB routes correctly for siblings and inspect narrower `.clangd` overrides.
5. Ask Claude to use the LSP on a matching C/C++ file. The first call may run
   the configured configure command. A stale, missing, malformed, or replaced
   database remains blocked until a successful validation.

Invoke this skill in Claude Code as `/dv-clangd-guard:dv-clangd-guard-setup`.

The guard checks database freshness, tracked CMake/File API inputs, configured
environment names, and bounded source membership. It does not prove that
clangd has finished indexing, that generated headers are present, or that every
arbitrary CMake dependency is known. CMake File API `cmakeFiles` coverage is
helpful but not universal; add important external toolchain/vendor inputs
explicitly.
