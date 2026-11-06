# Changelog

## 0.1.0

- Initial release: skill `public-repo-guard`, generalised from a project-local pre-commit guard of a
  public FreeCAD enclosure repository.
- `scripts/check_private.py`: blocks absolute home paths (macOS, Linux, Windows; also JSON-escaped and
  forward-slash forms) and e-mail addresses (GitHub noreply and the Claude co-author noreply address
  allowed) in text files, in text and PNG/JPEG members of zip-based files (FCStd, 3mf, zip, docx, xlsx,
  pptx, odt, ods, odp, epub) and in PNG `tEXt`/`zTXt`/`iTXt`/`eXIf` chunks and JPEG APPn/COM segments.
  Unparseable images, mislabelled images and unreadable archives are findings.
- `--staged` scans the staged blobs (what the commit contains), not the working tree; submodules are
  skipped, symlink targets are scanned. `--hint` or env `CHECK_PRIVATE_HINT` sets the fix hint.
- `assets/pre-commit`: generic hook template (`python3`, override with env `CHECK_PRIVATE_PYTHON`); it
  fails closed when the interpreter or the script is missing.
- `scripts/strip_png_text.py`: removes PNG text chunks in place; every other chunk is kept byte for byte.
- Tests: every check is shown failing on an injected fault and passing on clean input; `--staged` and
  the hook run in a temporary git repository.
