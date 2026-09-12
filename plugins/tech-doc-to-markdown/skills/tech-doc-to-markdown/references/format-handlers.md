# Format Handlers

How to open each input format, which tools each route needs, and how to handle missing tools.

## Contents

1. Tool detection and install policy
2. PDF (text layer, scanned, mixed, protected)
3. DjVu
4. DOCX
5. DOC, RTF, ODT
6. EPUB, XPS, MOBI, FB2, CBZ, images
7. HTML and CHM
8. Very large files

---

## 1. Tool detection and install policy

Detect before planning; report what is missing in the classification card.

| Tool | Needed for | Detect |
|---|---|---|
| PyMuPDF (`pymupdf`) | PDF/XPS/EPUB/images: text, metadata, renders, crops | Python package, installed per environment rules |
| numpy, scipy | `dot_grid.py` | Python packages |
| python-docx | `docx_extract.py` | Python package |
| PyYAML | `split_verify.py` | Python package |
| Node.js + `mermaid` + `jsdom` | `check_mermaid.mjs` | `node --version`; npm packages in a scratch folder |
| DjVuLibre (`ddjvu`, `djvutxt`, `djvused`) | DjVu | command lookup (`Get-Command ddjvu` / `which ddjvu`) |
| Microsoft Word (COM, Windows) | DOC/RTF/ODT/DOCX → DOCX/PDF | try creating `Word.Application` |
| LibreOffice (`soffice`) | Same conversions, cross-platform | command lookup, `C:\Program Files\LibreOffice\program\soffice.exe` |
| Tesseract | Optional OCR text layer for searchable drafts | command lookup |

**Python packages:** follow the user's environment rules. Without rules, prefer `uv run --no-project --with pymupdf python script.py ...`; otherwise a venv in the scratchpad. Never install into the system Python.

**System tools:** do not install silently. Show the exact command and ask. On Windows use `winget search <name>` to find the package ID first, then `winget install --id <ID> -e`; on macOS `brew install <name>`; on Linux the distribution package manager. If no package exists, give the official download page and let the user decide.

OCR engines are rarely needed: the model reads rendered page images directly, which is more accurate for tables and diagrams. Use Tesseract only when the user wants a searchable text layer or a quick draft of very long, text-only scans.

## 2. PDF

`scripts/survey.py` reports per page: text characters, images, image coverage and vector drawings, and flags likely scans.

- **Text layer present, born-digital:** draft prose and tables from `text/pNNN.txt`, but read tables and figures from the renders; text extraction scrambles multi-column layouts and table cells. Vector diagrams render cleanly at any zoom.
- **Scanned (image-only):** render and read. Use halves for small print and crops for dense regions.
- **Scanned with an OCR text layer:** treat the text layer as a hint only. OCR confuses 0/O, 1/l/I, 5/S, 8/B and drops overbars and subscripts. Check every number against the image.
- **Mixed:** decide per page from `survey.json`.
- **Protected:** PyMuPDF opens owner-password (permissions-only) PDFs for reading. If a user password is required, ask the user for it; do not attempt to bypass protection.
- **Bookmarks and page labels:** `survey.json` includes the outline and printed page labels when present; use them for the page content map.

## 3. DjVu

- Text layer: `djvutxt input.djvu output.txt` (whole document) or `djvused input.djvu -e "select N; print-pure-txt"`.
- Page images: `ddjvu -format=tiff -page=N -scale=150 input.djvu pN.tif`, or convert everything to PDF with `ddjvu -format=pdf input.djvu output.pdf` and continue with the PDF route (`survey.py` renders PDF pages).
- Page count and structure: `djvused input.djvu -e "n"` and `djvused input.djvu -e "print-outline"`.
- If DjVuLibre is missing: ask to install it (see policy). PyMuPDF does not read DjVu.

## 4. DOCX

Born-digital documents carry real structure; use it.

1. `scripts/docx_extract.py input.docx --out <scratch>/draft.md --assets <scratch>/docx-assets` produces a draft in document order: headings from styles, paragraphs, list items, tables (merged cells repeated), and placeholders for embedded images (exported to the assets folder for inspection).
2. Export a PDF for visual verification and figures: `scripts/office_convert.ps1 -InputPath input.docx -OutDir <scratch> -To pdf` (Word) or `soffice --headless --convert-to pdf --outdir <scratch> input.docx`. Run `survey.py` on the PDF.
3. Rebuild figures from the page renders using the representation guide. Embedded images in DOCX are often diagrams drawn as pictures; transcribe them as text like any scan. Text boxes, SmartArt, equations (OMML) and drawing-canvas shapes are not in the python-docx draft; take them from the renders.

## 5. DOC, RTF, ODT

Convert first, then follow the DOCX route:

- Word (Windows): `scripts/office_convert.ps1 -InputPath file.doc -OutDir <scratch> -To docx` and `-To pdf`.
- LibreOffice: `soffice --headless --convert-to docx --outdir <scratch> file.doc`.

Old DOC files may render differently in modern Word; if the user has a PDF of the same document, prefer it for visual verification.

**Word automation can hang silently.** When Word is waiting on a first-run, sign-in, activation or repair dialog, every automated call blocks, including creating a blank document, and nothing is visible. `office_convert.ps1` runs the conversion with a time limit (`-TimeoutSec`, default 120), closes only the automation instance it started, and exits with code 2. When that happens, tell the user, ask them to open Word once interactively to clear the dialog, or offer LibreOffice. Never loop retries against a hung Word, and never stop Word processes you did not start: check that the command line contains `/Automation` and that the process started after your call.

## 6. EPUB, XPS, MOBI, FB2, CBZ, images

PyMuPDF opens these directly; `survey.py` works unchanged. Reflowable formats (EPUB, MOBI, FB2) have no fixed pages: survey renders them at a default page size, so use chapter headings instead of page numbers for markers (`<!-- section 3.2 -->`). For folders of page images (PNG/JPG/TIFF), pass each file or build a PDF with PyMuPDF (`pymupdf.open()` + `insert_pdf` of each opened image) and survey that.

## 7. HTML and CHM

- HTML: use the DOM structure (headings, tables, `pre`) for the draft; download or locate figure images and transcribe them as text.
- CHM: decompile to HTML first (`hh.exe -decompile <out-dir> file.chm` on Windows, `extract_chmLib` or `7z x file.chm` elsewhere), then follow the HTML route using the CHM table of contents (`.hhc`) for order.

## 8. Very large files

- Survey in ranges (`--pages 1-50`) to limit render time; render the rest when you reach it.
- Keep renders at 165/220 DPI; do not render everything at 400+ DPI — crop instead.
- Offer chapter-parallel transcription with subagents (see SKILL.md Stage 4) and a split into parts (Stage 7).
