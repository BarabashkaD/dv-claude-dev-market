# Validation: 0.2.0

## Executed in the assistant's isolated Linux workspace

- Python 3.12 unittest discovery: **28 passed, 0 skipped**.
- Includes real CMake 4.4.4 / Ninja 1.13.2 / GNU C++ multi-repository fixtures.
- Covers sibling scope, independent CMake source identity, exact exclusions,
  active/excluded/header/out-of-scope queries, mixed queries, added/removed files,
  configuration mismatch/switch, stale exclusions, source-extension filtering,
  symlink root escape, approval changes, failed configure, previous timeout/crash,
  locking, File API discovery, malformed/replaced databases, and v1 compatibility.
- Python bytecode compilation and `git diff --check` passed.
- Plugin/marketplace JSON parsed; guard version metadata agrees at 0.2.0.

Run the complete suite (CMake, Ninja, and a C++ compiler required for real fixtures):

```text
python -m unittest discover -s plugins/dv-clangd-guard/tests -v
```

## Not validated here

- Windows/MSVC or macOS execution.
- The user's actual multi-repository workspace or its PowerShell wrapper.
- Claude Code plugin CLI validation or live `clangd-lsp` routing/indexing.
- Actual Debug/Release/ASan/Linux application build and test matrices.

Synthetic and Linux fixture success does not establish any of those results.
After installation, review a v2 profile in the actual workspace, run the guard
through a real LSP request, and verify sibling routing and intentional denials
before relying on it. Do not patch the installed copy or bypass failed checks.
