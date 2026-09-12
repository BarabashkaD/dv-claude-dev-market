# Splitting into an Index and Parts

A split lets a later session load a small index plus one part instead of the whole transcription. Done well, "index + one part" costs about a third of the full document, and every part is readable on its own.

## Contents

1. When to split
2. Design rules
3. Part file layout
4. Index file layout
5. Plan JSON format
6. Running and verifying
7. Obsidian and GitHub compatibility

---

## 1. When to split

Recommend a split when the transcription exceeds roughly 15k tokens or 40 pages, or covers clearly separate reader tasks (hardware hookup, programming, timing analysis). Ask before splitting; small documents are better as one file.

## 2. Design rules

- **Group by reader task, keep source order.** Parts follow the original line order with no reordering, so verification is "each part equals its source lines". Cut at section boundaries where possible; split a section when its halves serve different tasks; merge tiny sections into a neighbour.
- **Size band:** about 2k–4.5k tokens per part (characters / 3.5 is a fair estimate; glyph-heavy waveforms tokenize worse).
- **Rename colliding headings in the source first.** Two headings with the same text in one part produce `-1` anchors; rename (for example "Clock Timing" → "Clock Timing Waveform") with `patch_md.py` before splitting.
- **Page markers** (`<!-- page X -->`) in the source give each part its `source_pages` automatically.
- **Conventions:** the canonical copy lives in the index; each part repeats only the convention lines it needs, byte-identical, inside `<!-- shared:name -->` markers.
- **Transcriber's notes stay exactly once**, in the part where they sit. Other affected parts get a "Read first" pointer, never a copy.
- **Links:** same-part links stay `(#anchor)`; cross-part links become `(<part-file>.md#anchor)` with unchanged visible text. Textual references like "(See Programming Section.)" may become links without changing their words.
- **Keep the single-file source** unless the user decides to archive it; the split is reproducible from it.

## 3. Part file layout

```markdown
---
title: "<Subject> — <Part title>"
aliases: [...]
subject: <Subject>
doc_type: doc-part
part: 7
parent: "[[<prefix>-00-index]]"
prev: "[[...]]"
next: "[[...]]"
related:
  - "[[...]]"
source_doc: "<full document title>"
source_id: <document number>
source_file: "<source>.md"
source_sections: [...]
source_lines: "1041-1343"
source_pages: "5-116 to 5-119"
contains: ["Figure 23", "Table 2", ...]
transcriber_notes: 2
tags: [...]
split_version: 1
---

# <title>

Part 7 of 9 · [Index](...) · Previous: [...] · Next: [...]

**Source:** pages ... **Summary.** <what the part covers, which task it serves, what it does not cover>

> **Read first.**
> - <pointer to a note or caveat in another part>

**Conventions in this part.** Full list in the [index](<index>#conventions).

<!-- shared:conventions-core -->
- <verbatim convention lines>
<!-- /shared -->

<continuation heading if the part starts mid-section, e.g. "## 4. Functional Description (continued)">

<!-- source: <source>.md L1041-1343 -->
<verbatim source lines, with only link targets rewritten>
<!-- /source -->

---

**Related parts**

- [08 ...](...): <one-line reason>
```

## 4. Index file layout

1. Frontmatter with `parts:` (quoted wikilinks) and source metadata.
2. H1 `<Document title> — Index` and a two-sentence "how to use this index".
3. **At a glance:** what the subject is, key limits.
4. **Quick facts:** the most-asked numbers, each with the part that holds it. Copy values exactly from the transcription.
5. **Read-first caveats:** numbered source inconsistencies and traps, each with its part.
6. **Parts catalog** (generated): per part, size, pages, sections, a description and "look here for" keywords.
7. **Question routing** table (question → parts) and **topic threads** (topic → parts in reading order).
8. **Conventions:** the canonical header block from the source, inside a source marker.
9. **Split log** (generated): title change, continuation headings, link rewrites, renames.

## 5. Plan JSON format

`scripts/split_doc.py` reads this plan. Text fields may contain `{L7}` (link to part 7's file) or `{L7:anchor}` (with anchor); `{L0}` is the index.

```json
{
  "source": "work/exm500.md",
  "out_dir": "work/exm500",
  "prefix": "exm500",
  "meta": {
    "subject": "EXM-500",
    "source_doc": "EXM-500 Programmable Display Controller (datasheet)",
    "source_id": "EXM-00500A",
    "base_tags": ["datasheet", "exm-500"],
    "split_version": 1
  },
  "drop_sections": ["## Contents"],
  "end_line": "*End of transcription of the EXM-500 datasheet, pages 5-101 to 5-124.*",
  "conventions_first_line_prefix": "> Transcribed from",
  "shared": {
    "conventions-core": [{"line_prefix": "- Active-low signals"}, {"line_prefix": "- Paragraphs marked"}],
    "waveform-legend": [{"line_prefix": "- Timing diagrams"}, {"fence_containing": "Waveform legend"}]
  },
  "parts": [
    {
      "n": 1,
      "file": "exm500-01-pinout-and-bus-interface.md",
      "short": "Pinout and Bus Interface",
      "title": "EXM-500 — Pinout and Bus Interface",
      "aliases": ["EXM-500 pinout"],
      "tags": ["pinout"],
      "start": "<!-- page 5-101 -->",
      "cont": null,
      "sections": ["1. Features", "2. Block Diagram and Pin Configuration"],
      "extras": ["Bus control truth table"],
      "shared": ["conventions-core"],
      "summary": "What the chip is and how it connects to a CPU bus ...",
      "read_first": [],
      "related": [[2, "the internal blocks of Figure 1 in detail."]],
      "catalog": {
        "desc": "Features, block diagram, pinout, pin functions.",
        "look": ["Figure 1, Figure 2, Table 1", "pin numbers and I/O types"],
        "sections": "sections 1-3"
      }
    }
  ],
  "rewrites": {
    "2": [["[Figure 1](#figure-1-block-diagram)", "[Figure 1]({L1:figure-1-block-diagram})", 2]]
  },
  "index": {
    "title": "EXM-500 Programmable Display Controller — Index",
    "aliases": ["EXM-500"],
    "intro": "This transcription is split into nine self-contained parts ...",
    "before_catalog": "## At a glance\n\n...\n\n## Quick facts\n\n...\n\n## Read-first caveats\n\n...",
    "after_catalog": "## Question routing\n\n...\n\n## Topic threads\n\n...",
    "split_log_extra": [["Section 12 headings renamed before the split", "09"]]
  }
}
```

Field notes:

- `start` is the exact text of the part's first line (a page marker or heading), searched after the previous part's start. Parts end where the next part starts; trailing blank lines and `---` rules at the cut are dropped.
- `drop_sections` headings are removed from the parts together with their content up to the next `---` or `##` heading (typically the table of contents).
- `end_line` (optional) moves a closing line into the index.
- `conventions_first_line_prefix` marks the first line of the header block copied into the index; the block ends before the first `---` or `## ` heading after it.
- `shared` items copy either one convention line (`line_prefix`) or the whole fenced block containing a line (`fence_containing`).
- `contains` is generated from figure and table headings plus `extras`; `transcriber_notes` is counted.
- Optional overrides: `page_marker_regex`, `figure_heading_regex`, `note_regex`, `glyphs` (extra characters whose counts the verifier compares).

## 6. Running and verifying

```text
python <skill>/scripts/split_doc.py plan.json            # refuses to overwrite unless --overwrite
python <skill>/scripts/split_verify.py plan.json         # needs PyYAML
node <scratch>/mmdcheck/check_mermaid.mjs <each part>
```

`split_verify.py` checks: each source block equals its source lines (ignoring link targets); every non-blank, non-rule source line is covered exactly once except the title and dropped sections; counts of Mermaid and text fences, figure/table headings, notes, table separators, page markers and glyphs match; figure headings appear once and match the `contains` fields; all links resolve (file and anchor); frontmatter parses and `source_lines`, `transcriber_notes`, `source_pages` agree with the content; shared blocks match the index conventions; the index lists every part.

Then run the negative test: copy the output folder, change one number in a copy, run `split_verify.py plan.json --dir <copy>`, and confirm it fails.

## 7. Obsidian and GitHub compatibility

- Body links: standard relative Markdown links (work on GitHub, in editors, and for AI sessions that open paths directly). Obsidian follows them too; heading anchors may land at the top of the note, which short parts make acceptable.
- Frontmatter links: quoted wikilinks (`"[[exm500-00-index]]"`) for Obsidian's graph and Properties view; flat keys only (Properties does not edit nested objects); tags without spaces and not purely numeric.
- File names: `<prefix>-NN-topic.md`, lowercase with hyphens, unique across a vault.
- Never write into a knowledge base without explicit permission; produce the folder in the working directory and let the user move it.
