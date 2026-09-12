"""Apply exact, all-or-nothing edits to a Markdown file, with backup and diff.

Usage:
  python patch_md.py DOC.md EDITS.json [--backup DIR] [--dry]

EDITS.json is a list of operations, applied in order to the text (line endings normalized to LF):
  {"old": "exact text", "new": "replacement", "count": 1}
  {"regex": "pattern", "new": "replacement with \\1", "count": 1, "multiline": true}
  {"rename_line": "### Old heading", "to": "### New heading", "next_startswith": "optional context"}
  {"insert_before_line": "## Heading", "lines": ["<!-- page 3 -->", ""], "next_startswith": null}
  {"insert_after_line": "exact line", "lines": ["new line"], "next_startswith": null}

"count" is the exact number of matches required (default 1). "next_startswith" narrows line operations to
lines whose next non-blank line starts with the given text. If any operation does not match as required,
nothing is written and every problem is listed. On success the file is written with LF endings and a unified
diff of the change is printed.
"""
import difflib
import json
import pathlib
import re
import shutil
import sys
import time


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    doc = pathlib.Path(sys.argv[1])
    edits = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
    dry = "--dry" in sys.argv
    original = doc.read_text(encoding="utf-8").replace("\r\n", "\n")
    text = original
    problems = []

    def line_hits(lines, target, next_startswith):
        hits = []
        for i, l in enumerate(lines):
            if l != target:
                continue
            if next_startswith is not None:
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j >= len(lines) or not lines[j].startswith(next_startswith):
                    continue
            hits.append(i)
        return hits

    for n, e in enumerate(edits, 1):
        want = e.get("count", 1)
        if "old" in e:
            found = text.count(e["old"])
            if found != want:
                problems.append(f"#{n} text: expected {want}, found {found}: {e['old'][:80]!r}")
                continue
            text = text.replace(e["old"], e["new"])
        elif "regex" in e:
            flags = re.M if e.get("multiline", True) else 0
            new_text, found = re.subn(e["regex"], e["new"], text, flags=flags)
            if found != want:
                problems.append(f"#{n} regex: expected {want}, found {found}: {e['regex']!r}")
                continue
            text = new_text
        else:
            lines = text.split("\n")
            key = next(k for k in ("rename_line", "insert_before_line", "insert_after_line") if k in e)
            hits = line_hits(lines, e[key], e.get("next_startswith"))
            if len(hits) != want:
                problems.append(f"#{n} {key}: expected {want}, found {len(hits)}: {e[key]!r}")
                continue
            for i in sorted(hits, reverse=True):
                if key == "rename_line":
                    lines[i] = e["to"]
                elif key == "insert_before_line":
                    lines[i:i] = e["lines"]
                else:
                    lines[i + 1:i + 1] = e["lines"]
            text = "\n".join(lines)

    if problems:
        print("NOT WRITTEN. Problems:")
        print("\n".join("  " + p for p in problems))
        sys.exit(1)

    diff = [l for l in difflib.unified_diff(original.split("\n"), text.split("\n"), "before", "after",
                                            lineterm="", n=0)]
    print("\n".join(diff))
    changed = sum(1 for l in diff if l[:1] in "+-" and not l.startswith(("+++", "---")))
    print(f"changed lines: {changed}")
    if dry:
        print("dry run: nothing written")
        return
    if "--backup" in sys.argv:
        bdir = pathlib.Path(sys.argv[sys.argv.index("--backup") + 1])
        bdir.mkdir(parents=True, exist_ok=True)
        dest = bdir / f"{doc.stem}.{time.strftime('%Y%m%d-%H%M%S')}{doc.suffix}"
        shutil.copy2(doc, dest)
        print(f"backup: {dest}")
    doc.write_text(text, encoding="utf-8", newline="\n")
    print(f"written: {doc}")


if __name__ == "__main__":
    main()
