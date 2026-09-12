"""Verify an index + parts split against its source Markdown and plan.

Usage:
  python split_verify.py PLAN.json [--dir OUTPUT_DIR]

--dir checks a copy of the output (use it for the negative test). Requires PyYAML.
Exit code 1 when any check fails.
"""
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from split_doc import compute_cuts, excluded_lines, index_file, load_plan, read_lines  # noqa: E402


def slugs(text):
    seen, out, fence = {}, set(), False
    for l in text.split("\n"):
        if l.startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = re.match(r"^#{1,6}\s+(.*?)\s*$", l)
        if m:
            s = re.sub(r"[^\w\- ]", "", m.group(1).lower()).replace(" ", "-")
            if s in seen:
                seen[s] += 1
                out.add(f"{s}-{seen[s]}")
            else:
                seen[s] = 0
                out.add(s)
    return out


def unlink(s):
    return re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    plan = load_plan(sys.argv[1])
    out_dir = pathlib.Path(sys.argv[sys.argv.index("--dir") + 1]) if "--dir" in sys.argv else pathlib.Path(plan["out_dir"])
    src = pathlib.Path(plan["source"])
    orig = read_lines(src)
    idx_name = index_file(plan)
    expected_files = [idx_name] + [p["file"] for p in plan["parts"]]
    problems = []

    def ok(cond, msg):
        if not cond:
            problems.append(msg)

    texts = {}
    for name in expected_files:
        f = out_dir / name
        ok(f.exists(), f"missing file {name}")
        if f.exists():
            texts[name] = f.read_text(encoding="utf-8")
    extra = sorted({f.name for f in out_dir.glob("*.md")} - set(expected_files))
    ok(not extra, f"unexpected files in output: {extra}")

    blocks = []
    rx = re.compile(rf"<!-- source: {re.escape(src.name)} L(\d+)-(\d+) -->\n(.*?)\n<!-- /source -->", re.S)
    for name, t in texts.items():
        for m in rx.finditer(t):
            blocks.append((name, int(m.group(1)), int(m.group(2)), m.group(3)))

    # 1. every block equals its source lines (link targets ignored)
    for name, a, b, body in blocks:
        exp = [unlink(l) for l in orig[a - 1:b]]
        got = [unlink(l) for l in body.split("\n")]
        if exp != got:
            k = next((i for i, (x, y) in enumerate(zip(exp, got)) if x != y), min(len(exp), len(got)))
            problems.append(f"{name} L{a}-{b}: content differs at source line {a + k}: "
                            f"{exp[k] if k < len(exp) else '<end>'!r} vs {got[k] if k < len(got) else '<end>'!r}")

    # 2. coverage
    excluded = {i + 1 for i in excluded_lines(orig, plan)}
    cover = [0] * (len(orig) + 2)
    for _, a, b, _ in blocks:
        for n in range(a, b + 1):
            cover[n] += 1
    bad = [n for n in range(1, len(orig) + 1)
           if n not in excluded and orig[n - 1].strip() and not re.match(r"^---\s*$", orig[n - 1]) and cover[n] != 1]
    ok(not bad, f"coverage: {len(bad)} source lines not covered exactly once, first {bad[:15]}")

    # 3. counts
    kept = "\n".join(l for i, l in enumerate(orig, 1) if i not in excluded)
    inblocks = "\n".join(b for _, _, _, b in blocks)
    checks = [("mermaid fences", r"(?m)^```mermaid"), ("text fences", r"(?m)^```text"),
              ("figure/table headings", plan["figure_heading_regex"]), ("transcriber notes", plan["note_regex"]),
              ("table separators", r"(?m)^\|\s*:?-{3,}"), ("page markers", plan["page_marker_regex"])]
    glyphs = ["‾", "█", "·", "─", "│"] + plan.get("glyphs", [])
    for label, pat in checks:
        s = len(re.findall(pat, kept, re.M))
        g = len(re.findall(pat, inblocks, re.M))
        ok(s == g, f"count {label}: source {s}, parts {g}")
        print(f"  {label:22s} source={s:6d} parts={g:6d}")
    for ch in glyphs:
        s, g = kept.count(ch), inblocks.count(ch)
        ok(s == g, f"count of {ch!r}: source {s}, parts {g}")

    # 4. figure headings once, matching frontmatter contains
    heads = re.findall(plan["figure_heading_regex"], inblocks, re.M)
    ok(len(heads) == len(set(heads)), f"duplicate figure/table headings: {sorted({h for h in heads if heads.count(h) > 1})}")
    declared = []

    # 5. links
    cache = {n: slugs(t) for n, t in texts.items()}
    nlinks = 0
    for name, t in texts.items():
        body = re.sub(r"(?s)\A---\n.*?\n---\n", "", t)
        body = re.sub(r"(?s)```.*?```", "", body)
        for m in re.finditer(r"\]\((?!https?://|mailto:)([^)#\s]*)(?:#([^)\s]+))?\)", body):
            nlinks += 1
            target = m.group(1) or name
            if target not in texts:
                problems.append(f"{name}: link to missing file {target!r}")
            elif m.group(2) and m.group(2) not in cache[target]:
                problems.append(f"{name}: missing anchor #{m.group(2)} in {target}")
    print(f"  links checked          {nlinks}")

    # 6. frontmatter, shared blocks
    conv = re.search(r"## Conventions\n\n<!-- source: [^>]*-->\n(.*?)\n<!-- /source -->", texts.get(idx_name, ""), re.S)
    conv_lines = conv.group(1).split("\n") if conv else []
    fig_rx = re.compile(plan["figure_heading_regex"], re.M)
    for name, t in texts.items():
        m = re.match(r"---\n(.*?)\n---\n", t, re.S)
        if not m:
            problems.append(f"{name}: no frontmatter")
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            problems.append(f"{name}: YAML error: {e}")
            continue
        ok(f"\n# {fm.get('title')}\n" in t, f"{name}: H1 does not match frontmatter title")
        if name == idx_name:
            ok(len(fm.get("parts", [])) == len(plan["parts"]), f"index lists {len(fm.get('parts', []))} parts")
            continue
        own = [(a, b, body) for n2, a, b, body in blocks if n2 == name]
        ok(len(own) == 1, f"{name}: expected 1 source block, found {len(own)}")
        if own:
            a, b, body = own[0]
            ok(fm.get("source_lines") == f"{a}-{b}", f"{name}: source_lines {fm.get('source_lines')!r} != '{a}-{b}'")
            notes = len(re.findall(plan["note_regex"], body, re.M))
            ok(fm.get("transcriber_notes") == notes, f"{name}: transcriber_notes {fm.get('transcriber_notes')} != {notes}")
            figs = fig_rx.findall(body)
            declared_here = [c for c in fm.get("contains", []) if c in figs or re.match(r"^(Figures?|Table) \d", c)]
            ok(sorted(declared_here) == sorted(figs), f"{name}: contains {declared_here} != headings {figs}")
            declared += declared_here
            pages = re.findall(plan["page_marker_regex"], body, re.M)
            if pages:
                ok(str(fm.get("source_pages", "")).endswith(pages[-1]), f"{name}: source_pages does not end at {pages[-1]}")
        for sm in re.finditer(r"<!-- shared:([\w-]+) -->\n(.*?)\n<!-- /shared -->", t, re.S):
            for l in sm.group(2).split("\n"):
                ok(l == "" or l in conv_lines, f"{name}: shared:{sm.group(1)} line not in index conventions: {l[:60]!r}")
    ok(sorted(declared) == sorted(heads), "frontmatter contains fields do not list every figure/table heading once")

    print(f"files={len(texts)} source_blocks={len(blocks)}")
    if problems:
        print("PROBLEMS:")
        print("\n".join("  " + p for p in problems))
        sys.exit(1)
    print("all split checks passed")


if __name__ == "__main__":
    main()
