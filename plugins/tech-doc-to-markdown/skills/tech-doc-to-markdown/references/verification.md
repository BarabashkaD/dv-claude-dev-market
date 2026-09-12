# Verification

Three layers: self-check scripts, an adversarial review, and a disciplined fix pass.

## Contents

1. Self-check scripts
2. Negative tests
3. Adversarial reviewer prompt template
4. Triage: verify findings before fixing
5. Fix procedure

---

## 1. Self-check scripts

Run after transcription and after every fix pass.

```text
python <skill>/scripts/check_markdown.py <doc.md> [--expect-figures 1-26] [--expect-tables 1-2]
node <scratch>/mmdcheck/check_mermaid.mjs <doc.md>
```

`check_markdown.py` reports: leftover placeholders (`<!-- WAVE:`, `<!-- CONTINUE`, `TODO`), unbalanced code fences, table rows whose cell count differs from the header, tables without a separator row, internal `](#anchor)` links that match no heading (GitHub slug rules, duplicate headings get `-1`, `-2`), uneven box widths inside ```text blocks, figure/table numbers never mentioned, page markers out of order, and counts (lines, tables, Mermaid blocks, text blocks, Transcriber's notes).

`check_mermaid.mjs` parses each ```mermaid block with the real Mermaid parser under jsdom and prints the parse error with the block's line number.

For split output, `split_verify.py` replaces both (see `splitting.md`).

## 2. Negative tests

Before trusting a checker in a session, make it fail once:

- Mermaid: a copy with a broken block (`A["unclosed --> ((`) must report an error and exit non-zero.
- Markdown: a copy with a table row missing a cell must be reported.
- Split verifier: a copy of the output with one number changed must fail with "content differs".

Record the negative test results in the final report.

## 3. Adversarial reviewer prompt template

Launch one general-purpose subagent. Fill the placeholders. Split very long documents across several reviewers by page range, each with the same template.

```text
You are a skeptical, adversarial technical reviewer. Find every error, omission and unsupported claim in a
Markdown transcription of a technical document. Assume it contains mistakes until you have checked it against
the original page images yourself. Do NOT modify the Markdown. Produce a written report only.

## Environment rules (mandatory)
<shell rules from the user, e.g. "Native Windows; never use bash, use PowerShell">
Write only inside: <scratchpad>/review. Do not touch <protected locations>.

## Inputs
- Document under review: <doc.md> (<lines> lines).
- Original: <source file>. <"Scan without text layer; read the page images." if applicable>
- Page renders: <scratch>/survey/full/pNNN.png (165 DPI) and <scratch>/survey/half/pNNN_a.png / _b.png (220 DPI).
- Existing crops: <scratch>/crops/.
- Crop tool: <python command> <skill>/scripts/crop.py <source> --page N --rect x0 y0 x1 y1 --dpi 400 --out <file>
- Page map: image pNNN = printed page <mapping>. Content map: <page: headings, figures, tables>.

## Intentional conventions (not errors by themselves)
<paste the conventions list from the document header>
Transcriber's notes and values marked derived/inferred are additions; still check that each is correct.

## Review, page by page
1. Tables: every cell (numbers, units, conditions, bit patterns, pin numbers).
2. Diagrams: every block, label, connection and arrow direction; derived equations.
3. Waveforms: signal list, edge order, which edges each parameter spans, brace texts, causal arrows.
   Timing is not to scale; report only order, edge and label errors.
4. Grids, screens and pictures: cell by cell, row counts.
5. Every sentence and number in prose; meaning-changing paraphrases; dropped sentences.
6. Omissions: notes, footnotes, asterisks, captions, figure-internal labels, page furniture.
7. Transcriber's notes and derived/inferred values: correct, wrong, or overstated?
8. Improvements for reuse: extra information derivable from the original that would save future sessions from
   re-reading the scan (quick references, consolidated tables, formulas, inconsistency lists). State source
   pages and whether each is pure derivation or needs assumptions.

## Method
Work through every page; keep a coverage checklist; zoom in before reporting anything uncertain.
Do not report guesses as confirmed.

## Output
Write <scratchpad>/review/fidelity_review.md with:
1. Summary with counts by severity (critical = wrong number/bit/pin/connection/edge; major = missing or
   meaning-changing content or a silent deviation; minor = labels, wording, unmarked additions, formatting).
2. Findings table: ID | severity | md lines | original page/location | document says | original says |
   suggested fix | confidence (confirmed/likely).
3. Verdicts on Transcriber's notes and derived values.
4. Omissions list.
5. Page coverage checklist.
6. Prioritized improvement suggestions.
Final reply: report path, counts per severity, top 10 findings with md lines, top 5 improvements.
```

## 4. Triage: verify findings before fixing

- Re-crop every critical and major finding at 400–600 DPI and look yourself. Confirm, reject or narrow each.
- Minor findings: accept when the reviewer's evidence is concrete (quoted label, counted rows); spot-check a few.
- Improvement suggestions are not findings. Apply them only if the user asked for extras.
- Tell the user which findings you confirmed and how, before or together with the fixes.

## 5. Fix procedure

1. Back up the document to the scratchpad.
2. Write an edits JSON and apply it with `scripts/patch_md.py <doc> <edits.json> --backup <scratch>` — every text edit must match exactly the expected number of times or nothing is written.
3. Regenerate generated blocks (`wavegen.py <spec> --insert <doc>`) after spec changes.
4. Review the unified diff that `patch_md.py` prints: only intended changes.
5. Re-run the self-checks. Update Transcriber's notes whose verdict changed (overstated → reworded as inferred, incomplete → completed).
