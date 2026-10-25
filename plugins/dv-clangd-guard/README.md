# dv-clangd-guard

`dv-clangd-guard` is a small fail-closed `PreToolUse` guard for Claude Code's
explicit `LSP` tool calls. It validates that the selected CMake build tree has
a current, parseable `compile_commands.json` before Claude uses the official
`clangd-lsp` provider. If the profile opts in to automatic configure, it runs
the exact argv command the user configured, under a per-build lock, and writes
success state atomically only after validation.

It does not install software, infer a build directory or preset, switch a
generator/toolchain, delete an index, build the project, or provide another
clangd provider. Install `clangd` separately and install the official
`clangd-lsp@claude-plugins-official` plugin dependency.

## Install

The pull request for this plugin is currently a Draft. The marketplace commands
below are for use after the PR is merged. To test this branch before merge,
clone the branch and register that checkout as a local marketplace:

```text
git clone --branch feat-dv-clangd-guard https://github.com/BarabashkaD/dv-claude-dev-market.git
/plugin marketplace add /path/to/dv-claude-dev-market
/plugin install dv-clangd-guard@dv-claude-dev-market
```

Add this marketplace and install the plugin from a Claude Code session:

```text
/plugin marketplace add BarabashkaD/dv-claude-dev-market
/plugin install dv-clangd-guard@dv-claude-dev-market
```

The plugin depends on `clangd-lsp@claude-plugins-official`. The marketplace
allowlist enables that dependency, but it does not install the `clangd`
executable. Claude Code's current code-intelligence documentation says the
official LSP plugin and the language-server binary are separate installs.

Use Claude Code 2.1.295 or newer: this plugin relies on hook
`onFailure: "block"` for fail-closed handling of a missing interpreter, crash,
or host timeout. The checker requires Python 3.9 or newer and uses only the
standard library. The hook uses the real executable named `python`; verify
that exact command in the shell that launches Claude. `py -3` and `python3`
are useful version checks but are not substitutes for the executable invoked
by the hook.

## Install missing executables

First check what is already available and install only what is missing. These
commands do not alter the selected compiler or CMake toolchain.

### Windows PowerShell

```powershell
Get-Command python,clangd,cmake,ninja,py -ErrorAction SilentlyContinue
python --version
clangd --version
cmake --version
ninja --version
py -3 --version
```

Install only missing packages (WinGet package IDs):

```powershell
winget install --exact --id LLVM.LLVM --source winget
winget install --exact --id Kitware.CMake --source winget
winget install --exact --id Ninja-build.Ninja --source winget
winget install --exact --id Python.Python.3.13 --source winget
```

Restart PowerShell or start Claude from a shell with the updated PATH. If the
LLVM installer did not expose `clangd`, verify the common location without
overwriting anything:

```powershell
& "$env:ProgramFiles\LLVM\bin\clangd.exe" --version
```

Append that directory to the current session only if needed, then launch
Claude from the same shell:

```powershell
$env:Path += ";$env:ProgramFiles\LLVM\bin"
clangd --version
```

`py -3` is not a substitute for the `python` command used by this hook. If
WinGet installed Python but only `py` works, locate the real interpreter and
add only its directory to the current launch session (no alias or global
configuration change):

```powershell
$pythonExe = py -3 -c "import sys; print(sys.executable)"
$pythonDir = Split-Path -Parent $pythonExe
$currentPython = Get-Command python.exe -ErrorAction SilentlyContinue
if ($null -eq $currentPython -or $currentPython.Source -ne $pythonExe) {
  $env:Path = "$pythonDir;$env:Path"
}
$resolvedPython = (Get-Command python.exe -ErrorAction Stop).Source
if ($resolvedPython -ne $pythonExe) { throw "python.exe does not resolve to the py -3 interpreter: $resolvedPython" }
python --version
```

No pip packages are required. Keep the hook's executable-form `command`/`args`;
it does not need Git Bash.

### macOS

```bash
command -v python clangd cmake ninja python3 || true
python --version
clangd --version
cmake --version
ninja --version
python3 --version
```

Install only missing formulas:

```bash
brew install llvm
brew install cmake
brew install ninja
brew install python
```

Homebrew may place the unversioned `python` executable in the Python
formula's `libexec/bin`. If `python --version` is not found, expose that real
directory in the shell that starts Claude without creating an alias:

```bash
export PATH="$PATH:$(brew --prefix python)/libexec/bin"
python --version
```

Homebrew's `llvm` is keg-only. Preserve the existing compiler selection and
expose only clangd with a non-destructive user-bin link if it is absent:

```bash
mkdir -p "$HOME/.local/bin"
test -e "$HOME/.local/bin/clangd" || ln -s "$(brew --prefix llvm)/bin/clangd" "$HOME/.local/bin/clangd"
export PATH="$PATH:$HOME/.local/bin"
clangd --version
```

Persist that final PATH addition in the shell startup file you actually use,
then restart Claude. Do not prepend the entire LLVM bin directory merely to
find clangd, because that can replace the project's compiler selection.

### Debian or Ubuntu

```bash
command -v python clangd cmake ninja python3 || true
python --version
clangd --version
cmake --version
ninja --version
python3 --version
```

Install only missing packages from the distribution repositories:

```bash
sudo apt update
sudo apt install clangd cmake ninja-build python3 python3-venv
```

Debian/Ubuntu commonly provide only `python3`, not an unversioned `python`.
Create an isolated user-local environment so the hook gets a real `python`
executable without changing a system alias:

```bash
python3 -m venv "$HOME/.local/share/dv-clangd-guard/python"
. "$HOME/.local/share/dv-clangd-guard/python/bin/activate"
python --version
claude
```

Start Claude from that activated shell, or add only this venv's `bin` directory
to the launcher's user/session PATH. Do not replace `/usr/bin/python` or add a
shell alias.

Ubuntu may place `clangd` in `universe`; enable that repository only if the
package is unavailable and the user approves the repository change. WSL needs
the Linux packages inside the WSL distribution, not only on Windows.

### Fedora

```bash
command -v python clangd cmake ninja python3 || true
python --version
clangd --version
cmake --version
ninja --version
python3 --version
sudo dnf install clang-tools-extra cmake ninja-build python3
```

Fedora's `clang-tools-extra` package provides `clangd`.
If `python --version` is not available after installing `python3`, use an
isolated user-local venv for the hook without changing a system alias:

```bash
python3 -m venv "$HOME/.local/share/dv-clangd-guard/python"
. "$HOME/.local/share/dv-clangd-guard/python/bin/activate"
python --version
claude
```

### Arch Linux

```bash
command -v clangd cmake ninja python || true
clangd --version
cmake --version
ninja --version
python --version
sudo pacman -S --needed clang cmake ninja python
```

Do not run `pacman -Sy` without a full upgrade; preserve Arch's partial-upgrade
rule.

## Configure a project

Run the setup skill or create `.clangd-guard.json` at the explicit project root.
Do not copy the example blindly: choose the actual build directory, preset,
generator, toolchain, and configuration. The smallest useful profile is:

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
  "configureInputs": ["CMakeLists.txt", "CMakePresets.json"],
  "environmentVariables": ["CC", "CXX", "CMAKE_TOOLCHAIN_FILE"],
  "sourceRoots": ["src", "include"]
}
```

The configure command must produce `buildDir/compile_commands.json`, using
`CMAKE_EXPORT_COMPILE_COMMANDS=ON` or an equivalent preset option. A configure
command is executed without a shell, so pipes, redirects, and shell expansion
are not supported. Put important `.cmake`, include, preset, toolchain, and
cache-selection inputs in `configureInputs`; the CMake File API can discover
many `cmakeFiles` inputs after a successful configure but cannot guarantee
complete coverage of arbitrary project logic.

The v0.1 guard intentionally does not support blessing a manually configured
database: `--record` is not available because a parseable old database is not
proof that the latest configure ran. Use the exact configured argv with
`autoConfigure: true`, then approve that profile once after reviewing it:

```text
python <plugin-root>/hooks/clangd_guard.py --approve --project-dir <project-root>
```

The approval seal is stored in per-user application state outside the project,
keyed by the canonical profile path and its SHA-256. It is not a repo file and
does not need a `.gitignore` rule. Changing the profile invalidates the seal.
To roll back automatic execution, set `autoConfigure` to `false` or remove the
profile; the old state remains blocked and no command is run.

## Route clangd to the selected build

clangd does not reliably discover an arbitrary out-of-tree database merely
because `compile_commands.json` exists. In the project-root `.clangd`, merge
the following setting with the existing YAML instead of replacing that file:

```yaml
CompileFlags:
  CompilationDatabase: build/debug
```

Use the exact configured `buildDir` (relative to the project root). Preserve
all existing `.clangd` keys and get explicit user approval before editing it.
The guard validates the database and CMake identity; it does not prove that a
live clangd provider has loaded the database. Runtime provider routing was not
available for live testing in this repository environment.

## What the guard means

- A source-body/header edit does not force configure.
- Explicitly tracked CMake/configure inputs, tracked environment values, a
  changed database, or bounded source membership changes do force a fresh
  configure (or block when auto-configure is disabled).
- Failed, crashed, or timed-out configure never blesses an old database.
- Concurrent sessions serialize configure per build directory and recheck
  freshness after taking the lock.
- The hook host timeout is 1830 seconds: 1800 seconds maximum configure time,
  plus the bounded 10-second lock wait and small process overhead. A host kill
  is fail-closed through `onFailure: "block"`; it never turns an old database
  into fresh state.
- Fresh database, generated-header availability, and clangd index readiness
  are separate states. This hook only proves the first one.
- Changes made by unrelated build processes can race this private lock; rerun
  the LSP after those processes settle.
- Only explicit Claude `LSP` calls are guarded. Automatic diagnostics and
  other clients are outside the hook's scope.
- `sourceRoots` is required and intentionally bounded. New, removed, or
  renamed translation units inside those roots are fail-closed; files outside
  the roots and arbitrary generated/build-time membership are unsupported.
- Configure input tracking is conservative, not a complete CMake dependency
  graph. Keep important external toolchain/vendor `.cmake` files in
  `configureInputs` when File API discovery cannot cover them.
- A queried `.c/.cc/.cpp/.cxx/.m/.mm` translation unit must be present in the
  validated database. Headers are allowed to use clangd's inferred command
  behavior, but the guard does not claim a header-only database proves source
  coverage.

The guard uses only Python's standard library; it has no pip dependencies.

## Sources

- [Claude Code hooks](https://code.claude.com/docs/en/hooks)
- [Claude Code plugin dependencies](https://code.claude.com/docs/en/plugins/dependencies)
- [Claude Code code intelligence](https://code.claude.com/docs/en/plugins/code-intelligence)
- [clangd compilation database](https://clangd.llvm.org/design/compile-commands)
- [clangd compilation database routing](https://clangd.llvm.org/config#compilationdatabase)
- [CMake compile commands](https://cmake.org/cmake/help/latest/variable/CMAKE_EXPORT_COMPILE_COMMANDS.html)
- [CMake File API](https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html)

## Test locally

From the repository root:

```powershell
py -3 plugins/dv-clangd-guard/tests/test_clangd_guard.py
claude plugin validate plugins/dv-clangd-guard
claude plugin validate .
```

The setup skill can be invoked in Claude Code as
`/dv-clangd-guard:dv-clangd-guard-setup`; it asks for the real build directory,
preset, generator, toolchain, and configuration instead of guessing them.

The tests use an isolated fixture and do not install packages or modify the
user's Claude configuration. They exercise the hook payload, a real CMake
fixture when CMake, Ninja, and a C++ compiler are available, malformed/replaced
databases, failed configure, timeout/crash, lock contention, source
membership, and paths containing spaces and Unicode. If the compiler is not
available, the real compiler-database integration tests are skipped; the
remaining policy tests still run.
