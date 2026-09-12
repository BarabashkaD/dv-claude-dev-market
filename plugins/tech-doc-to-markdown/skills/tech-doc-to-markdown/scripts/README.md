# Scripts

All Python scripts run with any Python 3.10+. Install packages per the user's environment rules; without rules, `uv run --no-project --with <packages> python <script> ...` needs no setup. Paths below use `<skill>` for this skill's folder.

| Script | Purpose | Packages |
|---|---|---|
| `survey.py` | Metadata, TOC, per-page inventory, text layer dump, page renders (full 165 DPI, halves 220 DPI, or previews) | pymupdf |
| `crop.py` | Zoomed crops by points or page fractions, single or from a JSON spec | pymupdf |
| `dot_grid.py` | Measure filled and empty squares in dot-matrix figures | pymupdf, numpy, scipy |
| `wavegen.py` | Generate aligned ASCII timing diagrams from a JSON spec; insert or regenerate them in a document | none |
| `patch_md.py` | Apply exact-match edits, line renames and insertions with all-or-nothing checks; backup and diff | none |
| `check_markdown.py` | Structural checks for one Markdown file | none |
| `check_mermaid.mjs` | Parse Mermaid blocks with the real parser | Node.js, npm `mermaid`, `jsdom` |
| `docx_extract.py` | Draft Markdown from DOCX in document order, export embedded images | python-docx |
| `office_convert.ps1` | Convert DOC/DOCX/RTF/ODT to PDF or DOCX with Microsoft Word (Windows) | Word |
| `split_doc.py` | Build index + parts from a split plan JSON | none |
| `split_verify.py` | Verify a split against its source and plan | pyyaml |

## Examples

```text
uv run --no-project --with pymupdf python <skill>/scripts/survey.py "doc.pdf" --out <scratch>/survey --pages 1-3 --preview
uv run --no-project --with pymupdf python <skill>/scripts/survey.py "doc.pdf" --out <scratch>/survey
uv run --no-project --with pymupdf python <skill>/scripts/crop.py "doc.pdf" --page 12 --rect 64 268 478 526 --dpi 400 --out <scratch>/crops/fig23.png
uv run --no-project --with pymupdf --with numpy --with scipy python <skill>/scripts/dot_grid.py "doc.pdf" --page 6 --rect 150 453 396 487
python <skill>/scripts/wavegen.py <scratch>/waves.json --print
python <skill>/scripts/wavegen.py <scratch>/waves.json --insert out.md
python <skill>/scripts/patch_md.py out.md <scratch>/edits.json --backup <scratch>/backups
python <skill>/scripts/check_markdown.py out.md --expect-figures 1-26
uv run --no-project --with python-docx python <skill>/scripts/docx_extract.py "spec.docx" --out <scratch>/draft.md --assets <scratch>/docx-assets
powershell -NoProfile -File <skill>/scripts/office_convert.ps1 -InputPath "old.doc" -OutDir <scratch> -To pdf
python <skill>/scripts/split_doc.py <scratch>/split-plan.json
uv run --no-project --with pyyaml python <skill>/scripts/split_verify.py <scratch>/split-plan.json
```

## Mermaid checker setup (once per session)

```text
mkdir <scratch>/mmdcheck
cd <scratch>/mmdcheck
npm init -y
npm install --no-audit --no-fund mermaid jsdom
copy <skill>/scripts/check_mermaid.mjs .        (cp on macOS/Linux)
node check_mermaid.mjs <file.md>
```

The script must sit next to the `node_modules` folder so Node can resolve the packages.
