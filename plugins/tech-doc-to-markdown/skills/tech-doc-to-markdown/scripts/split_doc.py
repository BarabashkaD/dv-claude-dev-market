"""Split a Markdown transcription into an umbrella index plus self-contained parts, driven by a JSON plan.

Usage:
  python split_doc.py PLAN.json [--overwrite]

The plan format is documented in references/splitting.md. Parts are cut in source order; verbatim content is
wrapped in <!-- source: FILE La-b --> ... <!-- /source --> so split_verify.py can prove nothing was lost or
changed. Refuses to write into a non-empty output folder unless --overwrite is given and every existing file
is one this plan produces.
"""
import json
import pathlib
import re
import sys

LINK_RE = re.compile(r"\{L(\d+)(?::([^}]*))?\}")


def q(s):
    return json.dumps(s, ensure_ascii=False)


def qlist(items):
    return "[" + ", ".join(q(x) for x in items) + "]"


def load_plan(path):
    plan = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    plan.setdefault("page_marker_regex", r"^<!-- page (.+?) -->$")
    plan.setdefault("figure_heading_regex", r"^#{2,6} ((?:Figures? \d+(?:, ?\d+)*|Table \d+))\.")
    plan.setdefault("note_regex", r"^> \*\*Transcriber's note:\*\*")
    plan.setdefault("drop_sections", [])
    plan.setdefault("shared", {})
    plan.setdefault("rewrites", {})
    plan["parts"] = sorted(plan["parts"], key=lambda p: int(p["n"]))
    return plan


def read_lines(path):
    return pathlib.Path(path).read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")


def index_file(plan):
    return f"{plan['prefix']}-00-index.md"


def excluded_lines(lines, plan):
    """0-based indexes that belong to no part: the title line and dropped sections."""
    ex = set()
    title = next((i for i, l in enumerate(lines) if l.startswith("# ")), None)
    if title is not None:
        ex.add(title)
    for heading in plan["drop_sections"]:
        for i, l in enumerate(lines):
            if l != heading:
                continue
            ex.add(i)
            j = i + 1
            while j < len(lines) and not re.match(r"^(---\s*$|#{1,2} )", lines[j]):
                ex.add(j)
                j += 1
    return ex


def compute_cuts(lines, plan):
    starts, prev = {}, 0
    for p in plan["parts"]:
        hits = [i for i, l in enumerate(lines) if i >= prev and l == p["start"]]
        if not hits:
            sys.exit(f"part {p['n']}: start line {p['start']!r} not found after line {prev + 1}")
        starts[int(p["n"])] = hits[0]
        prev = hits[0] + 1
    end = None
    if plan.get("end_line"):
        hits = [i for i, l in enumerate(lines) if l == plan["end_line"]]
        if len(hits) != 1:
            sys.exit(f"end_line found {len(hits)} times")
        end = hits[0]
    order = [int(p["n"]) for p in plan["parts"]]
    ranges = {}
    for k, n in enumerate(order):
        nxt = starts[order[k + 1]] if k + 1 < len(order) else (end if end is not None else len(lines))
        a, b = starts[n], nxt
        while a < b and not lines[a].strip():
            a += 1
        while b > a and (not lines[b - 1].strip() or re.match(r"^---\s*$", lines[b - 1])):
            b -= 1
        ranges[n] = (a, b)
    conv = None
    prefix = plan.get("conventions_first_line_prefix")
    if prefix:
        h0 = next((i for i, l in enumerate(lines) if l.startswith(prefix)), None)
        if h0 is None:
            sys.exit(f"conventions line starting with {prefix!r} not found")
        h1, fence = h0, False
        while h1 < len(lines):
            l = lines[h1]
            if l.startswith("```"):
                fence = not fence
            elif not fence and (re.match(r"^---\s*$", l) or l.startswith("## ")):
                break
            h1 += 1
        while h1 > h0 and not lines[h1 - 1].strip():
            h1 -= 1
        conv = (h0, h1)
    return order, ranges, end, conv


def pages_of(lines, plan, a, b):
    rx = re.compile(plan["page_marker_regex"])
    markers = {i: m.group(1) for i, l in enumerate(lines) if (m := rx.match(l))}
    before = [i for i in markers if i <= a]
    inside = [i for i in markers if a <= i < b]
    if not before and not inside:
        return ""
    first = markers[max(before)] if before else markers[min(inside)]
    last = markers[max(inside)] if inside else first
    return first if first == last else f"{first} to {last}"


def shared_block(lines, conv, items):
    block = lines[conv[0]:conv[1]]
    out = []
    for item in items:
        if "line_prefix" in item:
            hits = [l for l in block if l.startswith(item["line_prefix"])]
            if len(hits) != 1:
                sys.exit(f"shared line prefix {item['line_prefix']!r} found {len(hits)} times in conventions")
            out.append(hits[0])
        elif "fence_containing" in item:
            idx = next((i for i, l in enumerate(block) if item["fence_containing"] in l), None)
            if idx is None:
                sys.exit(f"shared fence containing {item['fence_containing']!r} not found in conventions")
            s = idx
            while s >= 0 and not block[s].startswith("```"):
                s -= 1
            e = idx + 1
            while e < len(block) and not block[e].startswith("```"):
                e += 1
            if s < 0 or e >= len(block):
                sys.exit(f"fence around {item['fence_containing']!r} is not closed in conventions")
            if out and out[-1] != "":
                out.append("")
            out += block[s:e + 1]
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    plan = load_plan(sys.argv[1])
    src = pathlib.Path(plan["source"])
    out_dir = pathlib.Path(plan["out_dir"])
    lines = read_lines(src)
    meta = plan["meta"]
    parts = {int(p["n"]): p for p in plan["parts"]}
    idx_name = index_file(plan)
    total = len(parts)

    produced = {idx_name} | {p["file"] for p in parts.values()}
    if out_dir.exists() and any(out_dir.iterdir()):
        existing = {f.name for f in out_dir.iterdir()}
        if existing - produced:
            sys.exit(f"{out_dir} holds files this plan does not produce: {sorted(existing - produced)}")
        if "--overwrite" not in sys.argv:
            sys.exit(f"{out_dir} is not empty; re-run with --overwrite to replace the generated files")
    out_dir.mkdir(parents=True, exist_ok=True)

    def fname(n):
        return idx_name if n == 0 else parts[n]["file"]

    def short(n):
        return "Index" if n == 0 else f"{n:02d} {parts[n]['short']}"

    def resolve(text):
        return LINK_RE.sub(lambda m: fname(int(m.group(1))) + (f"#{m.group(2)}" if m.group(2) else ""), text)

    order, ranges, end, conv = compute_cuts(lines, plan)
    excluded = excluded_lines(lines, plan)
    for n, (a, b) in ranges.items():
        if any(a <= i < b for i in excluded):
            sys.exit(f"part {n} contains a dropped section or the title line; adjust drop_sections or starts")
    fig_rx = re.compile(plan["figure_heading_regex"], re.M)
    note_rx = re.compile(plan["note_regex"], re.M)
    stats, log_rewrites = {}, []

    for n in order:
        p = parts[n]
        a, b = ranges[n]
        body = "\n".join(lines[a:b])
        for old, new, count in plan["rewrites"].get(str(n), []):
            found = body.count(old)
            if found != count:
                sys.exit(f"part {n}: rewrite {old!r} expected {count}, found {found}")
            body = body.replace(old, resolve(new))
            log_rewrites.append(n)
        contains = fig_rx.findall(body) + p.get("extras", [])
        notes = len(note_rx.findall(body))
        pages = pages_of(lines, plan, a, b)

        fm = ["---", f"title: {q(p['title'])}", f"aliases: {qlist(p.get('aliases', []))}",
              f"subject: {q(meta['subject'])}", "doc_type: doc-part", f"part: {n}",
              f"parent: {q('[[' + idx_name[:-3] + ']]')}",
              f"prev: {q('[[' + fname(n - 1 if n - 1 in parts else 0)[:-3] + ']]')}"]
        if n + 1 in parts:
            fm.append(f"next: {q('[[' + fname(n + 1)[:-3] + ']]')}")
        fm.append("related:")
        fm += [f"  - {q('[[' + fname(int(r))[:-3] + ']]')}" for r, _ in p.get("related", [])]
        fm += [f"source_doc: {q(meta['source_doc'])}"]
        if meta.get("source_id"):
            fm.append(f"source_id: {q(meta['source_id'])}")
        fm += [f"source_file: {q(src.name)}", f"source_sections: {qlist(p.get('sections', []))}",
               f"source_lines: {q(f'{a + 1}-{b}')}", f"source_pages: {q(pages)}",
               f"contains: {qlist(contains)}", f"transcriber_notes: {notes}",
               f"tags: {qlist(meta.get('base_tags', []) + p.get('tags', []))}",
               f"split_version: {meta.get('split_version', 1)}", "---"]

        prev_n = n - 1 if n - 1 in parts else 0
        nav = f"Part {n} of {total} · [Index]({idx_name})"
        if prev_n:
            nav += f" · Previous: [{short(prev_n)}]({fname(prev_n)})"
        if n + 1 in parts:
            nav += f" · Next: [{short(n + 1)}]({fname(n + 1)})"

        page_text = f"**Source:** {'pages' if ' to ' in pages else 'page'} {pages}. " if pages else ""
        doc = fm + ["", f"# {p['title']}", "", nav, "", f"{page_text}**Summary.** {resolve(p['summary'])}", ""]
        if p.get("read_first"):
            doc += ["> **Read first.**"] + [f"> - {resolve(x)}" for x in p["read_first"]] + [""]
        if p.get("shared"):
            if conv is None:
                sys.exit("parts use shared blocks but conventions_first_line_prefix is not set")
            doc += [f"**Conventions in this part.** Full list in the [index]({idx_name}#conventions).", ""]
            for name in p["shared"]:
                doc += [f"<!-- shared:{name} -->"] + shared_block(lines, conv, plan["shared"][name]) + ["<!-- /shared -->"]
            doc.append("")
        if p.get("cont"):
            doc += [p["cont"], ""]
        doc += [f"<!-- source: {src.name} L{a + 1}-{b} -->", body, "<!-- /source -->"]
        if p.get("related"):
            doc += ["", "---", "", "**Related parts**", ""]
            doc += [f"- [{short(int(r))}]({fname(int(r))}): {resolve(why)}" for r, why in p["related"]]
        text = "\n".join(doc) + "\n"
        (out_dir / p["file"]).write_text(text, encoding="utf-8", newline="\n")
        stats[n] = dict(lines=text.count("\n"), words=len(text.split()), chars=len(text), pages=pages)

    ix = plan["index"]
    catalog = []
    for n in order:
        p, c = parts[n], parts[n].get("catalog", {})
        pages = stats[n]["pages"]
        where = f" · {'pages' if ' to ' in pages else 'page'} {pages}" if pages else ""
        catalog.append(f"**{n:02d} · [{p['short']}]({p['file']})** · ~{stats[n]['chars'] / 3500:.1f}k tokens{where}"
                       + (f" · {c['sections']}" if c.get("sections") else ""))
        if c.get("desc"):
            catalog.append(f"- {resolve(c['desc'])}")
        look = c.get("look", [])
        if len(look) == 1:
            catalog.append(f"- *Look here for:* {resolve(look[0])}.")
        elif look:
            catalog += ["- *Look here for:*"] + [f"  - {resolve(x)}" for x in look]
        catalog.append("")

    fm = ["---", f"title: {q(ix['title'])}", f"aliases: {qlist(ix.get('aliases', []))}",
          f"subject: {q(meta['subject'])}", "doc_type: doc-index", "part: 0", "parts:"]
    fm += [f"  - {q('[[' + parts[n]['file'][:-3] + ']]')}" for n in order]
    fm += [f"source_doc: {q(meta['source_doc'])}"]
    if meta.get("source_id"):
        fm.append(f"source_id: {q(meta['source_id'])}")
    fm += [f"source_file: {q(src.name)}", f"tags: {qlist(meta.get('base_tags', []) + ['index'])}",
           f"split_version: {meta.get('split_version', 1)}", "---"]

    doc = fm + ["", f"# {ix['title']}", ""]
    if ix.get("intro"):
        doc += [resolve(ix["intro"]), ""]
    if ix.get("before_catalog"):
        doc += [resolve(ix["before_catalog"]).rstrip(), ""]
    doc += ["## Parts catalog", ""] + catalog
    if ix.get("after_catalog"):
        doc += [resolve(ix["after_catalog"]).rstrip(), ""]
    if conv:
        doc += ["## Conventions", "", f"<!-- source: {src.name} L{conv[0] + 1}-{conv[1]} -->"] + lines[conv[0]:conv[1]] + ["<!-- /source -->", ""]
    title = next((l for l in lines if l.startswith("# ")), None)
    doc += ["## Split log", "", "| Change | Where |", "|---|---|"]
    if title:
        doc.append(f"| Title line `{title}` became the index H1 `# {ix['title']}` | 00 |")
    for heading in plan["drop_sections"]:
        doc.append(f"| `{heading}` was dropped; the parts catalog replaces it | 00 |")
    for n in order:
        if parts[n].get("cont"):
            doc.append(f"| Added continuation heading `{parts[n]['cont']}` | {n:02d} |")
    if log_rewrites:
        where = ", ".join(f"{n:02d}" for n in sorted(set(log_rewrites)))
        doc.append(f"| Links rewritten to point across parts; visible link text unchanged | {where} |")
    for change, where in ix.get("split_log_extra", []):
        doc.append(f"| {change} | {where} |")
    doc += ["", f"Verbatim content sits between `<!-- source: {src.name} La-b -->` and `<!-- /source -->` markers, "
                "with line numbers of the source at this split version. Text outside the markers was written for "
                "navigation.", ""]
    if end is not None:
        doc += [f"<!-- source: {src.name} L{end + 1}-{end + 1} -->", lines[end], "<!-- /source -->"]
    index_text = "\n".join(doc) + "\n"
    (out_dir / idx_name).write_text(index_text, encoding="utf-8", newline="\n")

    print(f"{'file':56s} {'lines':>5s} {'~tokens':>8s}  pages")
    print(f"{idx_name:56s} {index_text.count(chr(10)):5d} {len(index_text) / 3500:7.1f}k")
    for n in order:
        s = stats[n]
        print(f"{parts[n]['file']:56s} {s['lines']:5d} {s['chars'] / 3500:7.1f}k  {s['pages']}")


if __name__ == "__main__":
    main()
