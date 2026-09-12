# Dispatching the Transcription Subagent

Stages 3–8 always run in a subagent that starts cold. This file is the how.

## Contents

1. Why cold
2. What counts as one document
3. Central setup before dispatch
4. The prompt template
5. Receiving the report
6. Anti-patterns

---

## 1. Why cold

A transcriber that inherits the conversation has already "learned" what the document contains — from the classification card, from the previews the dispatcher looked at, from its own summary of a neighbouring document. It will then write fluent, structured, confidently wrong prose that no checker catches, because a checker validates structure, not truth.

This is not hypothetical. In the reference batch a transcriber produced, without reading the page: two invented program listings, a line-number range of 1–32767 where the document said 0–65529, and a claim that a printed example was missing. All three were plausible for that class of document. They were found only because the agent re-read every page afterwards and reported the failure itself.

A cold start does not make the subagent smarter. It makes it *unable* to answer from memory, so it opens the image instead. That is the whole mechanism.

The second benefit is cheaper and still real: a 24-page datasheet with 40 crops costs hundreds of thousands of tokens. Kept in a subagent, none of it reaches the conversation the user is reading.

## 2. What counts as one document

One subagent per document — not per file, and not per folder.

- Three magazine instalments of one series → **one** document. They share conventions, numbering and cross-references; splitting them across subagents produces two headers, two conventions blocks and broken «Продолжение» chains.
- Two unrelated articles that happen to sit in the same folder → **two** documents, even if both are about the same subject. Merging them produces a file that misrepresents its own completeness.
- A datasheet plus its addendum, bound in one PDF → **one** document.
- Volume 1 and Volume 2 of a manual, separately paginated → **two**, cross-linked afterwards.

The test: would a reader expect one source statement and one set of conventions to cover it? Then it is one document. Decide during classification, state it in the classification card, and let the user overrule you.

## 3. Central setup before dispatch

Do these once in the main session, then tell the subagents they are done:

1. Create the output folder for each document. Give each document its own folder holding the single-file transcription, its `assets/`, and later its split parts — so relative image links resolve identically from the single file and from every part.
2. Create a separate scratch folder per document under the session scratchpad.
3. Install the Mermaid checker once (`scripts/README.md`) at a shared path and pass that path in.
4. Run the negative tests for `check_markdown.py` and `check_mermaid.mjs` — feed each a deliberately broken file and confirm a non-zero exit. Quote the result to the user. Each subagent still runs its own `split_verify.py` negative test, which is document-specific.

## 4. The prompt template

Fill every section. Omissions become questions the subagent cannot ask.

```markdown
You are converting ONE technical document to Markdown by following the installed skill
`tech-doc-to-markdown`. Work autonomously to completion — you cannot ask the user
questions; every open decision is already settled below. Record any judgment call you
make in your final report.

## Read these first, in full, before touching the document
1. <skill>\SKILL.md
2. <skill>\references\representation-guide.md
3. <skill>\references\profiles\<chosen profile>.md
4. <skill>\references\verification.md
5. <skill>\references\splitting.md          (only if splitting)
6. <skill>\references\quick-reference-extras.md   (only if extras were selected)
7. <skill>\scripts\README.md

## Environment rules (mandatory — from the user's own rules)
- <shell restriction, quoted, not summarised>
- <Python runner, with the exact command form>
- <Node / checker path, and which negative tests are already done>
- Scratchpad: <this document's scratch folder>
- NEVER write to <read-only locations, e.g. the user's knowledge base>

## The document
<source path(s). For page images, a table of reading order → filename → printed page.>

Stage 2 classification is already done for you:
- Title / publisher / document number / revision:
- Profile: ... Language: ... (and whether to keep it untranslated)
- Structure: <what lives where, in page ranges>

**These classification facts are pointers, not source.** They tell you where to look.
Every fact in your output must come from a page image or the file itself, never from
this briefing. Where the briefing and the page disagree, the page wins — transcribe the
page and report the disagreement. Some numbers here are estimates from a low-resolution
preview and may be wrong.

## Decisions the user has already made
- Recognition depth: L<n> <and what that entails here>
- Split: yes/no
- Quick-reference extras: yes/no <which>
- Verification report: yes
- <any document-specific ruling, e.g. how to treat a risky table>

## Output location
<folder>, containing:
- <name>.md              — the full single-file transcription (source of the split)
- assets\*.png           — genuine pictures only
- <prefix>-00-index.md + <prefix>-NN-<topic>.md   — if splitting

## Specific instructions for this document
<The traps you found during classification: dense tables, worn glyphs, foreign columns
on a shared page, repeated page numbers needing a disambiguation scheme, active-low
conventions, footnotes with no text, anything the profile does not cover.>

## Workflow to follow
Stages 3 → 4 → 5 → <6> → <7> → <8> → 9 of SKILL.md.
<Any stage-specific requirement, e.g. the split negative test.>

## Final report (return this as your answer)
1. Output paths written.
2. What was produced: sections, figures, tables, parts, extras, line count.
3. Verification results: exact pass/fail output of every checker, and the negative test.
4. <Any document-specific accounting, e.g. address ranges and uncertain rows.>
5. Source inconsistencies you flagged with Transcriber's notes (list them).
6. Defaults applied, judgment calls, and anywhere the briefing was wrong.
7. Anything NOT done or NOT verified — be explicit and honest.
```

Quote the user's environment rules verbatim. A summarised rule gets reasoned around; a quoted one does not. In the reference batch a subagent reported that the quoted "never use bash" rule overrode a conflicting session-level instruction to prefer it — which is the correct resolution and only possible because it had the rule's actual words.

## 5. Receiving the report

- **Relay it.** The user asked for a conversion and gets the transcriber's own account of it. Keep the "not done / not verified" section intact; that is the part with the shortest half-life and the highest value.
- **Spot-check, do not re-derive.** Confirm the files exist at the claimed paths and sizes. Do not re-read the document in the main session to check the work — that re-pollutes the context this whole design protects, and the subagent has already looked far harder than a spot-check will.
- **Where the report contradicts itself**, resolve it with one cheap command rather than an opinion (a count, a listing) and say what you found.
- **For fixes, go back to the same subagent** with `SendMessage`. It still holds the crops, the scripts and the page map. Re-dispatching cold repeats hours of reading.

## 6. Anti-patterns

- **Forking instead of starting cold.** A fork inherits everything and defeats the purpose entirely. Use a general-purpose subagent.
- **One subagent, several documents.** Document two gets written partly from document one's conventions, and the report blurs which findings belong to which.
- **Two subagents, one output file.** They will overwrite each other; nothing in the checkers detects it.
- **Transcribing "just the first page" yourself** to show the user progress. That is the polluted-context failure in miniature, and it seeds the subagent's prompt with your reading instead of the page.
- **Summarising the report instead of relaying it**, especially the caveats. The subagent is the only witness to what it did not verify.
- **Editing the document to make a checker go green.** Fidelity outranks a clean exit code; explain the exit instead.
