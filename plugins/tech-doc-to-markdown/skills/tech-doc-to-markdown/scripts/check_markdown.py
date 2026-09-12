"""Structural checks for one Markdown transcription.

Usage:
  python check_markdown.py DOC.md [--expect-figures 1-26] [--expect-tables 1-2]

Checks: leftover placeholders, balanced code fences, table column counts and separator rows, internal
](#anchor) links (GitHub slugs; duplicate headings get -1, -2), equal widths of box-drawing frames in ```text
blocks, figure/table numbers never mentioned, page markers (<!-- page X -->) present and not duplicated.
Prints counts. Exit code 1 when problems are found.
"""
import argparse
import re
import sys
import pathlib

PLACEHOLDERS = re.compile(r"<!-- (WAVE:|CONTINUE|TODO)|\bTODO\b|\bTBD\b")


def slug_set(lines):
    seen, out = {}, set()
    for l in lines:
        m = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", l)
        if not m:
            continue
        s = re.sub(r"[^\w\- ]", "", m.group(1).strip().lower()).replace(" ", "-")
        if s in seen:
            seen[s] += 1
            out.add(f"{s}-{seen[s]}")
        else:
            seen[s] = 0
            out.add(s)
    return out


def cells(row):
    row = row.strip()
    parts, cur, code, esc = [], "", False, False
    for ch in row:
        if esc:
            cur += ch
            esc = False
            continue
        if ch == "\\":
            esc = True
            cur += ch
            continue
        if ch == "`":
            code = not code
        if ch == "|" and not code:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return len(parts) - 2 if row.startswith("|") and row.endswith("|") else len(parts)


def parse_range(spec):
    if not spec:
        return []
    a, _, b = spec.partition("-")
    return list(range(int(a), int(b or a) + 1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("doc")
    ap.add_argument("--expect-figures")
    ap.add_argument("--expect-tables")
    args = ap.parse_args()

    lines = pathlib.Path(args.doc).read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    problems = []

    outside, blocks, fence, lang, start, buf = [], [], False, "", 0, []
    for i, l in enumerate(lines, 1):
        if re.match(r"^\s*```", l):
            if not fence:
                fence, lang, start, buf = True, l.strip()[3:].strip(), i, []
            else:
                blocks.append((start, lang, buf))
                fence = False
            continue
        if fence:
            buf.append((i, l))
        else:
            outside.append((i, l))
    if fence:
        problems.append(f"unclosed code fence starting at line {start}")

    for i, l in outside:
        if PLACEHOLDERS.search(l):
            problems.append(f"line {i}: placeholder left: {l.strip()[:80]}")

    table, tables = [], 0
    for i, l in outside + [(10 ** 9, "")]:
        if l.lstrip().startswith("|"):
            table.append((i, l))
            continue
        if table:
            tables += 1
            n0 = cells(table[0][1])
            if len(table) < 2 or not re.match(r"^\|?\s*:?-{3,}", table[1][1].strip()):
                problems.append(f"line {table[0][0]}: table without a separator row")
            for j, r in table:
                if cells(r) != n0:
                    problems.append(f"line {j}: table row has {cells(r)} cells, header has {n0}")
            table = []

    anchors = slug_set([l for _, l in outside])
    for i, l in outside:
        for target in re.findall(r"\]\(#([^)\s]+)\)", l):
            if target not in anchors:
                problems.append(f"line {i}: broken internal link #{target}")

    for s, lg, buf in blocks:
        if lg not in ("text", ""):
            continue
        frame = [(i, l.rstrip()) for i, l in buf if l.strip()[:1] in ("│", "╭", "╰", "┌", "└", "║", "╔", "╚")]
        if frame:
            widths = sorted({len(l) for _, l in frame})
            if len(widths) > 1:
                problems.append(f"text block at line {s}: box lines have uneven widths {widths}")

    body = "\n".join(l for _, l in outside)
    for n in parse_range(args.expect_figures):
        if not re.search(rf"\bFigures? (?:[\d, and]*\b)?{n}\b", body):
            problems.append(f"Figure {n} is never mentioned")
    for n in parse_range(args.expect_tables):
        if not re.search(rf"\bTable {n}\b", body):
            problems.append(f"Table {n} is never mentioned")

    markers = [(i, m.group(1)) for i, l in outside if (m := re.match(r"^<!-- page (.+?) -->$", l))]
    labels = [p for _, p in markers]
    for p in {x for x in labels if labels.count(x) > 1}:
        problems.append(f"page marker {p} appears {labels.count(p)} times")

    notes = sum(1 for _, l in outside if l.startswith("> **Transcriber's note:**"))
    mermaid = sum(1 for _, lg, _ in blocks if lg == "mermaid")
    text_blocks = sum(1 for _, lg, _ in blocks if lg == "text")
    print(f"lines={len(lines)} tables={tables} mermaid={mermaid} text_blocks={text_blocks} "
          f"headings={len(anchors)} page_markers={len(markers)} transcriber_notes={notes}")
    if problems:
        print("PROBLEMS:")
        print("\n".join("  " + p for p in problems))
        sys.exit(1)
    print("all structural checks passed")


if __name__ == "__main__":
    main()
