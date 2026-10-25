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

Add this marketplace and install the plugin from a Claude Code session:

```text
/plugin marketplace add BarabashkaD/dv-claude-dev-market
/plugin install dv-clangd-guard@dv-claude-dev-market
```

The plugin depends on `clangd-lsp@claude-plugins-official`. The marketplace
allowlist enables that dependency, but it does not install the `clangd`
executable. Claude Code's current code-intelligence documentation says the
official LSP plugin and the language-server binary are separate installs.

## Install missing executables

First check what is already available and install only what is missing. These
commands do not alter the selected compiler or CMake toolchain.

### Windows PowerShell

```powershell
Get-Command clangd,cmake,ninja,py -ErrorAction SilentlyContinue
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

`py -3` is not a substitute for the `python` command used by this hook. The
hook needs a working `python` executable on PATH; verify `python --version` as
well if `py -3` is the only launcher available. No pip packages are required.
On Windows without Git Bash, use a Claude Code version that supports
`onFailure: "block"` and keep the hook's executable-form `command`/`args`.

### macOS

```bash
command -v clangd cmake ninja python3 || true
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
command -v clangd cmake ninja python3 || true
clangd --version
cmake --version
ninja --version
python3 --version
```

Install only missing packages from the distribution repositories:

```bash
sudo apt update
sudo apt install clangd cmake ninja-build python3
```

Ubuntu may place `clangd` in `universe`; enable that repository only if the
package is unavailable and the user approves the repository change. WSL needs
the Linux packages inside the WSL distribution, not only on Windows.

### Fedora

```bash
command -v clangd cmake ninja python3 || true
clangd --version
cmake --version
ninja --version
python3 --version
sudo dnf install clang-tools-extra cmake ninja-build python3
```

Fedora's `clang-tools-extra` package provides `clangd`.

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

Set `autoConfigure` to `false` if configure must be manual. The guard still
blocks missing, malformed, replaced, or stale databases until the manual
configure has succeeded and the next LSP preflight records fresh state.

## What the guard means

- A source-body/header edit does not force configure.
- Explicitly tracked CMake/configure inputs, tracked environment values, a
  changed database, or bounded source membership changes do force a fresh
  configure (or block when auto-configure is disabled).
- Failed, crashed, or timed-out configure never blesses an old database.
- Concurrent sessions serialize configure per build directory and recheck
  freshness after taking the lock.
- Fresh database, generated-header availability, and clangd index readiness
  are separate states. This hook only proves the first one.
- Changes made by unrelated build processes can race this private lock; rerun
  the LSP after those processes settle.
- Only explicit Claude `LSP` calls are guarded. Automatic diagnostics and
  other clients are outside the hook's scope.

The guard uses only Python's standard library; it has no pip dependencies.

## Test locally

From the repository root:

```powershell
py -3 plugins/dv-clangd-guard/tests/test_clangd_guard.py
claude plugin validate plugins/dv-clangd-guard
claude plugin validate .
```

The tests use an isolated fixture and do not install packages or modify the
user's Claude configuration. They exercise the hook payload, a real CMake
fixture when CMake and Ninja are available, malformed/replaced databases,
failed configure, timeout/crash, lock contention, source membership, and paths
containing spaces and Unicode.
