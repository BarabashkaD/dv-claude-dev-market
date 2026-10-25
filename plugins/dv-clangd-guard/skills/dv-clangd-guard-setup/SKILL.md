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

## Profile

Create `.clangd-guard.json` at the selected project root. Adapt the example to
the project; it is intentionally explicit:

```json
{
  "version": 1,
  "projectRoot": ".",
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
  "sourceRoots": ["src", "include"]
}
```

`autoConfigure: true` is an explicit consent to run only the listed argv
command in the listed working directory. Set it to `false` when configure must
be run manually; the hook will still validate freshness and block stale LSP
calls.

`sourceRoots` is optional but recommended. It lets the guard detect source
membership additions, removals, and renames in bounded directories. It does not
hash source bodies, so an ordinary edit does not trigger configure.

## Verify

1. Ensure the official `clangd-lsp@claude-plugins-official` dependency is
   installed and `clangd` itself is on the PATH of the shell that starts
   Claude Code.
2. Confirm the selected CMake command succeeds manually once, with
   `CMAKE_EXPORT_COMPILE_COMMANDS=ON` (or the equivalent preset cache option).
3. Ask Claude to use the LSP on a matching C/C++ file. The first call may run
   the configured configure command. A stale, missing, malformed, or replaced
   database remains blocked until a successful validation.

The guard checks database freshness, tracked CMake/File API inputs, configured
environment names, and bounded source membership. It does not prove that
clangd has finished indexing, that generated headers are present, or that every
arbitrary CMake dependency is known. CMake File API `cmakeFiles` coverage is
helpful but not universal; add important inputs explicitly.
