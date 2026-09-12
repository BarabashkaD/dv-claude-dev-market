---
name: tech-doc-to-markdown
description: Convert technical documentation (datasheets, reference and service manuals, schematics, standards, application notes) from PDF, scanned PDF, DjVu, DOC/DOCX, RTF, ODT, EPUB or page images into faithful, verified Markdown where tables, block diagrams, timing diagrams, bit fields, pinouts, register maps and dot patterns become text (Markdown tables, Mermaid, aligned ASCII waveforms). Covers first-page classification with clarifying questions, page rendering and zoomed reading of scans, self-check scripts, an adversarial fidelity review, quick-reference extras, and splitting large documents into an index plus parts. The transcription itself always runs in a dedicated subagent with a clean context, one document per subagent. Use it whenever the user wants to digitize, transcribe, process, recognize or convert a technical document file to Markdown or knowledge-base notes, or to extract its tables, diagrams or timing data as text, even if they only point at the file and say "process this manual". Not for a single quick question about a document or for editing PDFs.
---

# Technical Documentation to Markdown

Turn a technical document into Markdown that a person or a later AI session can use *instead of* the original: every number, table, diagram and caveat is present as text, anything the transcriber added is marked, and the result has been checked by scripts and by an independent reviewer.

The workflow below was distilled from a full conversion of a scanned 24-page datasheet. The stages exist because each one caught real errors the previous one missed.

## Principles

1. **Text, not pictures.** The output must be searchable, diffable and readable by a model without vision. Tables become Markdown tables, block diagrams become Mermaid plus a connection list, timing diagrams become generated ASCII waveforms plus a table of what each parameter measures, dot patterns become character grids. Only genuine pictures (photographs, 3D renders, artwork that cannot be expressed as text) are saved as image files: crop them accurately, save them next to the Markdown, embed them with a one- or two-sentence description.
2. **Faithful before helpful.** Transcribe what is printed. Do not silently fix a reversed arrow, a typo, a swapped label or a contradiction between two figures; keep it and add a `> **Transcriber's note:**` explaining it. Mark every addition — hex values computed from bit patterns, formulas, inferred numbering, descriptive captions — as *derived* or *inferred*. In the reference session, two "logical" corrections made silently were later flagged as the most serious errors.
3. **Measure instead of guessing.** Small print, dot matrices and bit tables are where reading errors hide. Zoom in with crops; count dots with a script; compare cell by cell.
4. **Verify by machine, then by an adversary.** Scripts catch structural slips (broken Mermaid, uneven tables, misaligned boxes). A separate reviewer working only from the page images catches meaning errors the author cannot see. Prove each checker can fail before trusting a pass.
5. **Ask at decision points, not constantly.** Classify the document first, then ask only what the defaults do not settle.
6. **One document, one subagent, clean context.** Never transcribe in the session that talked to the user. Classification happens in the main session because it asks questions; everything from Stage 3 on runs in a dedicated subagent that starts cold, holds exactly one document, and returns a report. A transcriber carrying conversation history writes from what it remembers being told about the document instead of from the page in front of it — and that failure is invisible, because the invented text is plausible. See Stage 2.5.

## Defaults

These were confirmed by the user. Apply them unless the user or the document requires otherwise, and say which defaults you applied.

| Topic | Default |
|---|---|
| Execution | Stages 0–2 in the main session; Stages 3–8 in a dedicated subagent per document, started cold (never a context-inheriting fork) |
| Output content | Text only; images only for genuine pictures, cropped and embedded with a description |
| Layout | One Markdown file first; split into index + parts after approval |
| Recognition depth | L2 Structured (see Stage 2), L3 when the user wants verified output |
| Block diagrams | Mermaid flowchart + plain-text connection list |
| Timing diagrams | Generated ASCII waveform + parameter table |
| Language | Keep the source language; never translate labels, signal names or numbers |
| Save location | Current working directory, file name from the document title; confirm during classification |
| Python packages | Follow the user's environment rules if any exist; otherwise `uv`; otherwise `python -m venv` in the scratchpad |
| System tools (DjVuLibre, LibreOffice, Tesseract) | Never install silently; show the exact install command and ask |
| Claude Platform (API) | Reference material only (`references/claude-platform-pdf.md`); do not call the API unless the user explicitly asks |
| Scratch files | Renders, crops, scripts and backups go to the session scratchpad, never next to the source or into a knowledge base |

## Stage 0 — Rules and environment

Before touching the document:

- **Read the user's rules** that apply: global and project `CLAUDE.md`, `.claude/rules/`, and any knowledge-base agent rules the user points to. Obey shell restrictions (for example "never use bash" on Windows — run the scripts with the allowed shell), read-only locations, and privacy rules.
- **Pick the Python environment.** Search those rules, installed skills and plugins for a Python environment convention and use it. If there is none and `uv` exists, run scripts with `uv run --no-project --with <packages> python <script> ...` (nothing is installed globally). If `uv` is missing, create `python -m venv <scratchpad>/venv` and install there.
- **Scratchpad.** Create a working folder in the session scratchpad for renders, crops, specs and backups.

Package needs per script are listed in `scripts/README.md`.

## Stage 1 — Intake and format

Identify the format from extension and content, then follow `references/format-handlers.md`:

| Input | Route |
|---|---|
| PDF with a text layer | Use text for drafting, page renders for tables/figures and for checking numbers (OCR'd text layers are often wrong) |
| Scanned PDF, image-only | Render pages and read the images directly; no OCR engine needed |
| DjVu | `djvutxt`/`ddjvu` from DjVuLibre (ask before installing), or convert to PDF/TIFF, then as PDF |
| DOCX | `scripts/docx_extract.py` for a structural draft, plus PDF export (Word/LibreOffice) for figures and verification |
| DOC, RTF, ODT | Convert to DOCX/PDF with `scripts/office_convert.ps1` (Word) or LibreOffice, then as above |
| EPUB, XPS, MOBI, FB2, CBZ, images | Open with PyMuPDF (`survey.py` handles them) |
| HTML, CHM | Extract HTML (for CHM, decompile first), convert structure, render figures as needed |

## Stage 2 — Fast classification and clarifying questions

Spend a few minutes, not hours, before heavy work:

1. Run `scripts/survey.py <input> --out <scratch>/survey --pages 1-3 --preview` for a cheap look: metadata, bookmarks/TOC, page count, text layer or scan, and 110 DPI previews of the first pages. Also preview the last page (revision history, document number) and 3–5 pages spread through the document to estimate content.
2. Read the title page and first page: title, subject/product, publisher, document number, revision/date, language, intended audience.
3. Choose a profile from `references/profiles/` (datasheet, reference-manual, service-manual, standard-spec, application-note, generic) and read it. Profiles hold document-type-specific custom steps; the user can add new profiles.
4. Show the user a short **classification card**: type and profile, subject, document ID, language, pages, text layer vs scan and scan quality, content inventory (tables, block diagrams, timing, schematics, register maps, photos, code, formulas), and a proposed plan with the defaults applied.
5. Ask with the question tool — only what the defaults do not settle, but always confirm these:
   - **Recognition depth**
     | Level | Result | Cost |
     |---|---|---|
     | L1 Text | Prose, headings, lists and tables; figures captioned and described in 1–3 sentences | Lowest |
     | L2 Structured | L1 plus every diagram, waveform, bit field, pinout and grid as text | Medium |
     | L3 Verified | L2 plus zoomed reading of all dense areas, measured grids, self-checks, adversarial review and a fix pass | Highest, roughly double L2 |
   - **Splitting:** none, or index + parts after transcription (recommend when the document exceeds roughly 40 pages or 15k tokens, or mixes clearly separate topics).
   - **Save location and name** (default: current working directory).
   - **Optional stages:** adversarial review, quick-reference extras, profile custom steps.
   - **Unusual content:** photographs, fold-out schematics, very long page counts, mixed languages, damaged scans, content the profile does not cover.

## Stage 2.5 — Dispatch to a transcription subagent

**Mandatory. Stages 3–8 never run in the session that spoke to the user.** When classification is agreed, stop working on the document yourself and dispatch.

**Rules**

- **One document, one subagent.** Two magazine instalments of the same series are one document; two unrelated articles that happen to share a folder are two. Decide this during classification and say so in the classification card.
- **Start it cold.** Use a general-purpose subagent, never a fork or any mode that inherits this conversation. A cold start is the point: it forces the transcriber to read the pages.
- **No shared state between subagents.** Each gets its own scratch folder and its own output folder. They must never write to the same file.
- **Dispatch in parallel** when there are several documents; they have no ordering dependency.
- **The subagent cannot ask questions.** Every decision from Stage 2 must already be settled and written into its prompt. Tell it explicitly to act on those decisions and to record any judgment call in its report rather than stopping.
- **Do the shared setup once, centrally**, before dispatching: create the output folders, install the Mermaid checker, and run the `check_markdown.py` / `check_mermaid.mjs` negative tests. Tell each subagent these are done so it does not repeat them — but each still runs its own `split_verify.py` negative test, since that one is document-specific.

**What goes in the prompt:** use the template in `references/subagent-dispatch.md`. In outline — the reference files to read first; the user's environment rules quoted, not summarised (shell restriction, Python runner, read-only locations); its scratch folder; the source paths in reading order; the classification facts; the user's decisions; document-specific traps; the stages to run; and the report format.

**The classification card is a pointer, not a source.** Everything you put in the prompt is orientation for finding things on the page — never a substitute for reading it. State this in the prompt: *every fact in the output must come from a page image or the file itself, never from this briefing; where the briefing and the page disagree, the page wins and the disagreement goes in the report.* Briefing figures that turn out wrong are normal and useful — an estimate of "about 200 table rows" that the subagent corrects to 67 is the system working.

**When it returns:** relay its report. Do not paraphrase away its "not done / not verified" section, and do not re-verify its work by re-reading the document in the main session — that re-pollutes the context this stage exists to keep clean. Spot-check that the output files exist and are the size claimed; if something needs fixing, send the same subagent back with `SendMessage` so the fix happens in the context that did the work.

## Stage 3 — Survey and render

Run `scripts/survey.py` on the full document. It writes `survey.json` (per page: printed page label, text length, images, vector drawings, scan likelihood), page renders at 165 DPI (`full/`) and overlapping top/bottom halves at 220 DPI (`half/`). Those sizes let the image reader see a whole page at about 1550 px without downscaling, while the halves resolve 6-point table text.

Read every page before writing the section that contains it. Build a **page content map** — page, printed page number, headings, figures, tables — and keep it as the coverage checklist for later stages.

This is the rule the clean context exists to protect. You have a dispatch prompt describing the document; it tells you where to look and nothing more. **No sentence of output may be written from it.** If you find yourself typing a statement, a line-number range, a listing or a table row that you have not just looked at in an image, stop and open the crop.

## Stage 4 — Transcribe

- **Header first:** title; a source statement (full document title, document number, revision, page range, and "transcribed from page images" when scanned); a conventions list (signal naming such as `/RD` for active-low, inline subscripts, what the Mermaid/ASCII/dot notations mean, what a Transcriber's note is); and the legends you use.
- **Page markers:** put `<!-- page X -->` before the content of each original page, using printed page numbers. They make later verification and page ranges for split parts trivial.
- **Order and chunks:** work in page order, a few pages per edit. Keep original headings and numbering; keep every note, footnote and asterisk.
- **Representation:** read `references/representation-guide.md` before the first figure. It covers tables with merged cells, bit fields, register maps, block diagrams, logic and schematics, timing diagrams, state machines, dot grids, screen layouts, plots, package drawings, photos, equations and code.
- **Zoom:** any cell, label or dot you cannot read with certainty in the 220 DPI halves gets a crop with `scripts/crop.py` at 300–900 DPI. Count dot matrices with `scripts/dot_grid.py`.
- **Waveforms:** write a JSON spec and generate the ASCII with `scripts/wavegen.py` (it can insert or regenerate blocks in the document). Hand-aligned waveforms drift.
- **Large documents** (more than about 60 pages): you are already a subagent, but you may fan out further — chapter subagents that each receive the conventions header, the representation guide and a page range, then merge in page order. Same rules as Stage 2.5: cold start, one page range each, no shared files. Report that you did it; it multiplies cost.

## Stage 5 — Self-checks

- `scripts/check_markdown.py <doc>` — balanced fences, consistent table columns, internal links, aligned boxes in text blocks, leftover placeholders, figure coverage (`--expect-figures 1-26`).
- `scripts/check_mermaid.mjs` — parses every Mermaid block with the real Mermaid parser (setup in `scripts/README.md`).
- Once per session, feed each checker a deliberately broken input and confirm it fails. A checker that never fails proves nothing.

## Stage 6 — Adversarial review

For L3, or when the user selected it: launch a reviewer subagent with the prompt template in `references/verification.md`. It compares the Markdown against the page images page by page and returns findings by severity, verdicts on every Transcriber's note and derived value, omissions, and improvement ideas.

When it returns, **verify every critical and major finding yourself** with zoomed crops before changing anything — reviewers are also wrong sometimes. Then back up the document, apply fixes with `scripts/patch_md.py` (every edit must match exactly the expected number of times), regenerate generated blocks, diff against the backup, and re-run Stage 5.

## Stage 7 — Split into index + parts

After approval, follow `references/splitting.md`: write a split plan JSON (parts grouped by reader task, in source order), run `scripts/split_doc.py`, then `scripts/split_verify.py`, then a negative test (corrupt one value in a copy and confirm the verifier fails). Keep the single-file version as the source unless the user decides otherwise.

## Stage 8 — Quick-reference extras

If selected, add derived aids from `references/quick-reference-extras.md` (for example a byte decode map, a consolidated timing table, a command cheat sheet, a known-inconsistencies list). Every value must come from the document; design choices in worked examples are labelled as such.

## Stage 9 — Report

Finish with: output paths; what was produced (sections, figures, tables, parts); verification results, including the negative tests; source inconsistencies you flagged; defaults applied; and anything not done or not verified.

This report is the **only** thing that crosses back out of the subagent, so it carries the whole burden of honesty. Quote checker output exactly rather than characterising it — an exit 1 you can justify is worth more than a "passed" you cannot. State where the briefing you were given was wrong. If you drafted anything before reading its page and had to redo it, say so; that is the failure this design exists to catch, and a report that hides it defeats the purpose. The dispatcher relays this text to the user, so write it for them.

## Pitfalls seen in practice

- **Drafting from the briefing instead of the page.** The worst failure observed, because its output is fluent and wrong: a transcriber wrote a section from its dispatch prompt, inventing two program listings, a wrong numeric range and a false claim that a listing was absent. It survived only because the agent re-read every page afterwards. Nothing you were told about the document is evidence about the document.
- **Silent corrections:** redrawing an arrow in its "logical" direction, or labelling unlabelled waveform segments, reads as an error to a reviewer. Draw what is printed; explain in a note.
- **Dropped qualifiers:** words like "programmable", "typical", "max" inside figure braces carry meaning. Keep them.
- **Unmarked helpful sentences:** "DB0 is pin 12" may be true but is still an addition. Either omit it or mark it.
- **Repeated figures:** when a document redraws a base figure with highlights, transcribe the base once and describe each highlight; an error in the base then propagates, so check the base hardest.
- **Counting rows:** screen and grid figures lose or gain a blank row easily. Count lines in the crop.
- **Regex traps in scripts:** a pattern like `Figures? [\d, ]+\d` silently skips single-digit figures. Test extraction scripts against known counts.
- **English-only checker flags on a non-English document:** `--expect-figures` / `--expect-tables` match `Figure N` / `Table N` only, so they can never pass on a document that correctly keeps `Рис. N` / `Таблица N`. Do not translate headings to satisfy a checker. Run an equivalent coverage check in the source language and report which one you ran.
- **A checker failing on the source's own words:** a document that prints "TBD" in its own cells trips the leftover-placeholder check. Prove it with a control run (rename the token in a copy; confirm the file then passes clean), keep the faithful text, and explain the non-zero exit in the report rather than editing the document to go green.
- **Line endings:** Python `write_text` on Windows writes CRLF unless `newline="\n"` is given; mixed endings break exact-match patching.
- **Heading collisions:** two headings with the same text produce `-1` anchor suffixes and ambiguous search hits; rename them in the source before splitting.
- **Page mapping:** image file numbers are not printed page numbers. Record both in the page content map.

## Reference files

- `references/subagent-dispatch.md` — how to dispatch Stages 3–8 (read at Stage 2.5, before dispatching): why cold, what counts as one document, central setup, the prompt template, receiving the report.
- `references/representation-guide.md` — how to express each content type as text (read before transcribing figures).
- `references/format-handlers.md` — per-format extraction, tool detection and install policy.
- `references/verification.md` — self-check usage, negative tests, adversarial reviewer prompt, triage and fix procedure.
- `references/splitting.md` — split design, plan JSON format, verification.
- `references/quick-reference-extras.md` — derived aids and their rules.
- `references/claude-platform-pdf.md` — what the Claude API can do with PDFs (reference only).
- `references/profiles/` — document-type profiles with custom steps; `README.md` explains how to add one.
- `scripts/README.md` — every script, its purpose, its packages and example commands.
