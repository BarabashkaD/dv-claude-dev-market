# dv-public-repo-guard

`dv-public-repo-guard` keeps personal data out of public git repositories. Its
one skill, `public-repo-guard`, installs a pre-commit hook that refuses a
commit when a staged file contains an absolute home path (macOS, Linux or
Windows home directory) or an e-mail address. GitHub noreply addresses and the
Claude co-author noreply address are allowed.

A text grep is not enough for the files people actually publish, so the
checker also looks inside:

- zip-based files: FreeCAD `FCStd`, `3mf`, `zip`, Office (`docx`, `xlsx`,
  `pptx`), OpenDocument (`odt`, `ods`, `odp`) and `epub`, both their text
  members and the PNG/JPEG images inside them. An FCStd keeps object
  properties in `Document.xml`; a docx keeps its author in
  `docProps/core.xml`.
- image metadata: PNG `tEXt`, `zTXt`, `iTXt` and `eXIf` chunks and JPEG
  APPn/COM segments. FreeCAD's `saveImage`, for one, writes the absolute
  output path into the PNG `Title` of every render.

## Contents

- `skills/public-repo-guard/SKILL.md`: when to use it, installation, what is
  and is not caught, how to fix findings.
- `scripts/check_private.py`: the checker (Python 3.8+, standard library
  only). `--staged` scans the staged blobs, i.e. what the commit will contain.
- `assets/pre-commit`: hook template; runs `python3`, or the interpreter in
  env `CHECK_PRIVATE_PYTHON`; fails closed.
- `scripts/strip_png_text.py`: removes PNG text chunks in place, every other
  chunk (pixels, colour profile) kept byte for byte.

## Install

```text
/plugin marketplace add BarabashkaD/dv-claude-dev-market
/plugin install dv-public-repo-guard@dv-claude-dev-market
```

Then, in the project: copy `check_private.py` to `tools/` and `pre-commit` to
`.githooks/`, make the hook executable, and run once per clone
`git config core.hooksPath .githooks`. Details and the fault-injection check
are in the SKILL.md.

## Limits

- Skips `.step`, `.stp`, `.brep`, `.brp`, `.stl`, `.pdf` and other binary
  files (GIF, WebP, TIFF, fonts, executables).
- Catches home-directory paths only: a temporary folder, `/opt/...` or a
  mounted volume is not caught; neither are names or phone numbers without an
  e-mail address.
- Guards new commits only; it does not scan history.

## Tests

```text
python -m pytest plugins/dv-public-repo-guard/skills/public-repo-guard/tests
```

All fixtures are generated at runtime; see `VALIDATION.md`.
