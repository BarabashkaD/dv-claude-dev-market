# Validation: 0.1.0

## Unit tests (executed on macOS, Python 3 with pytest)

```text
python -m pytest plugins/dv-public-repo-guard/skills/public-repo-guard/tests
47 passed
```

All fixtures are generated in the test at runtime (no binary fixtures, no real
user names). Each check has a clean input that passes and the same input with
an injected fault that fails with the expected `file[:member]:line: what`:

- plain text: macOS, Linux and JSON-escaped Windows home paths; a non-noreply
  e-mail;
- PNG: e-mail in `tEXt`, home path in compressed `iTXt`, home path in the
  `zTXt` `Title` (the FreeCAD `saveImage` case), home path in `eXIf`, a corrupt
  `zTXt`, a `.png` that is not a PNG;
- JPEG: Windows path in a COM segment, a JPEG without start of scan;
- zip-based: FCStd `Document.xml` home path, 3mf metadata e-mail, docx
  `docProps/core.xml` e-mail, a PNG with a `Title` path inside a zip, a corrupt
  archive.

Also: GitHub and Claude noreply addresses pass; STEP/BRep/STL/PDF and other
binary files are skipped; `--hint` and `CHECK_PRIVATE_HINT` replace the hint.
In a temporary git repository: `--staged` scans staged files only, scans the
staged blob rather than a cleaned but unstaged working file, handles a rename
from a subdirectory, and exits 2 outside a repository; the hook template
refuses a dirty commit, accepts the clean one, and refuses when the
interpreter or the script is missing. `strip_png_text.py` removes the text
chunks, keeps every other chunk byte for byte, and leaves a non-PNG unchanged.
The skill's own files pass both this checker and `tools/check_public.py`.

## Mutation check of the tests

Each of these faults was injected into `check_private.py` by hand and the
suite was re-run; every one made at least one test fail:

| Injected fault | Failing tests |
|---|---|
| `zTXt` chunks ignored | 4 (zTXt Title, corrupt zTXt, PNG in zip, staged) |
| zip text members ignored | 4 (FCStd, 3mf, docx, hook) |
| no allowed e-mail addresses | 4 (noreply, AUTHORS clean, hook, own files) |
| `--staged` reads the working tree | 2 (index vs working tree, rename) |
| JPEG without start of scan accepted | 1 |
| non-image `.png` accepted | 1 |
| JPEG COM segment ignored | 1 |

## Not validated here

- Windows and Linux hosts (only macOS was executed; the CI workflow runs the
  tests on Ubuntu).
- Real FreeCAD, Office or Bambu Studio files: the fixtures reproduce their
  structure (member names, chunk layout) but were not produced by those
  applications in this repository. The source project's guard, on which this
  one is based, ran on real FCStd files and FreeCAD renders.
- Live skill triggering in a Claude Code or Codex session.
