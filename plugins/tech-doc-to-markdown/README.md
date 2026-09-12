# tech-doc-to-markdown

Turn a technical document into Markdown that a person or a later AI session can
use *instead of* the original: every number, table, diagram and caveat present
as text, everything the transcriber added marked as such, and the result checked
by scripts and by an independent reviewer.

Handles PDF (digital or scanned), DjVu, DOC/DOCX, RTF, ODT, EPUB, XPS, FB2, CBZ,
HTML/CHM and bare page images. Tables become Markdown tables, block diagrams
become Mermaid plus a connection list, timing diagrams become generated ASCII
waveforms plus a parameter table, dot matrices become character grids. Only
genuine pictures — photographs, 3D renders — are saved as image files.

See `skills/tech-doc-to-markdown/SKILL.md` for the full workflow.

## How it works

Ten stages, each of which exists because it caught an error the previous one
missed:

| Stage | What happens |
|---|---|
| 0–1 | Read the user's own rules (shell restrictions, read-only locations), pick the Python environment, identify the format |
| 2 | Cheap survey and previews, choose a document profile, show a classification card, ask only what the defaults do not settle |
| **2.5** | **Dispatch the transcription to a dedicated subagent with a clean context — one document per subagent** |
| 3–4 | Render pages, read every one of them, transcribe in page order with `<!-- page N -->` markers |
| 5 | Structural self-checks, each proven able to fail before a pass is trusted |
| 6 | Adversarial fidelity review against the page images, then a verified fix pass |
| 7–9 | Optional split into index + parts, quick-reference extras, and an honest report |

## Why the transcription runs in a subagent

Stage 2.5 is the rule the rest of the design leans on. A transcriber that
inherits the conversation has already "learned" what the document contains — from
the classification card, from previews, from a neighbouring document — and will
write fluent, structured, confidently wrong prose that no checker catches,
because checkers validate structure, not truth.

Observed in practice: a transcriber that wrote a section from its briefing rather
than from the page invented two program listings, a wrong numeric range, and a
claim that a printed example was missing. All three were plausible for that class
of document.

A cold start does not make the subagent smarter. It makes it *unable* to answer
from memory, so it opens the image instead. `references/subagent-dispatch.md`
holds the dispatch template and the anti-patterns.

## Core principles

1. **Text, not pictures** — the output must be searchable, diffable, and readable
   by a model without vision.
2. **Faithful before helpful** — transcribe what is printed; never silently fix a
   reversed arrow, a typo or a contradiction. Keep it and add a Transcriber's
   note. Mark every addition as *derived* or *inferred*.
3. **Measure instead of guessing** — zoom with crops, count dots with a script,
   compare cell by cell.
4. **Verify by machine, then by an adversary** — and prove each checker can fail
   before trusting a pass.
5. **Ask at decision points, not constantly.**
6. **One document, one subagent, clean context.**

## Document profiles

`references/profiles/` adapts the workflow per document type — `datasheet`,
`reference-manual`, `service-manual`, `standard-spec`, `application-note`,
`generic`. Each holds type-specific custom steps, clarifying questions, split
suggestions and useful extras. `profiles/README.md` explains how to add one.

## Bundled scripts

`skills/tech-doc-to-markdown/scripts/` — see its `README.md` for packages and
example invocations.

| Script | Purpose |
|---|---|
| `survey.py` | Metadata, TOC, per-page inventory, text dump, page renders |
| `crop.py` | Zoomed crops by points or page fractions |
| `dot_grid.py` | Measure filled and empty squares in dot-matrix figures |
| `wavegen.py` | Generate aligned ASCII timing diagrams from a JSON spec |
| `patch_md.py` | Exact-match edits with all-or-nothing checks, backup and diff |
| `check_markdown.py` | Structural checks for one Markdown file |
| `check_mermaid.mjs` | Parse Mermaid blocks with the real parser |
| `docx_extract.py` | Draft Markdown from DOCX, export embedded images |
| `office_convert.ps1` | Convert DOC/DOCX/RTF/ODT via Microsoft Word (Windows) |
| `split_doc.py` / `split_verify.py` | Build and verify an index + parts split |

Python scripts run on any Python 3.10+; most need only `pymupdf`. Nothing is
installed globally and no system tool is installed without asking first.

## Notes

- **Language is preserved.** Labels, signal names, error messages and numbers are
  never translated. Note that `check_markdown.py --expect-figures/--expect-tables`
  match English `Figure N` / `Table N` only, so a non-English document needs an
  equivalent coverage check in its own language rather than translated headings.
- **No API calls.** `references/claude-platform-pdf.md` is reference material
  only; the skill does not call the Claude API unless explicitly asked.
- **Scratch discipline.** Renders, crops, specs and backups go to the session
  scratchpad, never next to the source and never into a knowledge base.
