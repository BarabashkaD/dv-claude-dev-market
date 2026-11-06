---
name: public-repo-guard
description: Use when a git repository is or will become public and must not leak personal data - setting up a pre-commit privacy or personal-data check, before committing or publishing files, auditing a repo for absolute home paths or e-mail addresses, or stripping image metadata (PNG text chunks). Covers code, docs, images and zip-based archives (FreeCAD FCStd, 3mf, docx/xlsx/pptx, odt, epub, zip) whose members and metadata a plain text grep misses. Ships a stdlib-only checker, a pre-commit hook template and a PNG text-chunk stripper.
---

# Public repo guard

## Overview

`scripts/check_private.py` (Python 3.8+, standard library) blocks absolute home paths (macOS, Linux and
Windows home directories, also JSON-escaped and forward-slash forms) and e-mail addresses in files you
commit. GitHub noreply addresses and the `Co-Authored-By` noreply address of Claude are allowed.
`assets/pre-commit` runs it on every commit; `scripts/strip_png_text.py` cleans PNG metadata.

**Core principle: a guard nobody has seen fail proves nothing.** After installing, inject a fault and
watch the commit be refused before trusting a clean pass.

## What it scans

- Text files (no NUL byte in the first 4 KiB).
- Zip-based files `.fcstd .3mf .zip .docx .xlsx .pptx .odt .ods .odp .epub`: text members (xml, json,
  config, model, gcode, html, svg, ...) and PNG/JPEG members. FreeCAD keeps object properties, such as a
  provenance note with a source path, in `Document.xml` inside the FCStd; Office files keep the author
  in `docProps/core.xml`.
- Images `.png .jpg .jpeg`: PNG `tEXt`/`zTXt`/`iTXt`/`eXIf` chunks, JPEG APPn (EXIF, XMP) and COM
  segments. An image that does not parse, or a `.png` that is not a PNG, is a finding (fail closed).
- `--staged` reads the staged blobs, which is what the commit will contain, not the working tree.

Not scanned: `.step .stp .brep .brp .stl .pdf` and other binary files (GIF, WebP, TIFF, executables,
fonts). Not caught: absolute paths outside a home directory (temporary folders such as
`/private/tmp/...`, `/opt/...`, mounted volumes), user names without a path, names and phone numbers.
Scan PDFs and STEP headers separately if they can carry personal data.

## Install in a project

`<skill>` is this skill's directory.

1. `mkdir -p tools .githooks`; copy `<skill>/scripts/check_private.py` to `tools/` and
   `<skill>/assets/pre-commit` to `.githooks/pre-commit`; `chmod +x .githooks/pre-commit`.
2. Once per clone: `git config core.hooksPath .githooks`. Document this line in the README; a fresh
   clone has no hook until it is run.
3. Show it failing: put a home path in a scratch file, `git add` it, `git commit` must be refused with
   `file:1: home path ...`. Remove the file, unstage it.
4. Scan what is already tracked: `git ls-files -z | xargs -0 python3 -I tools/check_private.py`
   (history is not scanned; rewriting history is a separate decision for the owner).

Options:
- `--hint TEXT` or env `CHECK_PRIVATE_HINT`: the fix hint printed with the findings (default: use paths
  relative to the repository root). Example: `--hint 'Write paths as <archive>/...'`.
- env `CHECK_PRIVATE_PYTHON`: interpreter for the hook (default `python3`). A project that keeps its
  interpreter in an untracked file edits the hook to read it there (example in the hook's comments).
- Exit codes: 0 clean, 1 findings (`file[:member]:line: what`), 2 usage error or git failure.

## Fixing findings

- Write paths relative to the repository root, or as a named placeholder (`<archive>/...`).
- In FCStd/3mf, fix the property in the model and save again; do not edit the archive by hand.
- **FreeCAD trap:** `view.saveImage()` writes the absolute output path into the PNG `Title` zTXt chunk of
  every render. Strip it: `python3 -I <skill>/scripts/strip_png_text.py renders/*.png` removes only
  `tEXt`/`zTXt`/`iTXt`/`eXIf` chunks and copies every other chunk byte for byte, so the pixels and the
  colour profile are untouched. Re-run the checker afterwards.
- JPEG: remove EXIF/XMP with an image tool you trust, then re-run the checker.
- A false positive (a URL path `/home/<word>`) is fixed by rewording, not by weakening the patterns.

## Rules

- Never bypass the hook with `git commit --no-verify`. If it blocks, fix the file or ask the owner.
- Exit 2 or a crash is not a pass: the commit stays refused until the guard runs.
- After changing the patterns or the scanned types, inject a fault for each changed check and see it
  fail (the tests in `tests/` do this for every check).
- The hook guards new commits only; a pushed leak needs history rewriting and credential review.
