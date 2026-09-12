"""Generate aligned ASCII timing diagrams from a JSON spec, and insert them into a Markdown document.

Usage:
  python wavegen.py SPEC.json --print                 print every figure
  python wavegen.py SPEC.json --insert DOC.md [--dry] replace the ```text block that follows each figure's
                                                      anchor line (or a line <!-- WAVE:name -->) in DOC.md

SPEC.json:
{
  "figures": {
    "line-timing": {
      "anchor": "#### Figure 17. Line Timing",        exact line after which the ```text block sits (optional)
      "w": 5,                                          slot mode: characters per time slot
      "rows": [
        ["CCLK",  "sig",  ["C*6", "//", "C*5"]],
        ["HRTC",  "sig",  ["H", "L*5", "//", "L", "L", "H*3"]],
        ["LC0-3", "sig",  ["B:present line count*6", "//", "B:present line count*2", "B:next line count*3"]],
        ["",      "mark", ["-", "A:programmable 1 to 80 CCLKs", "a*4", "//", "a", "a", "-"]]
      ]
    },
    "dma": {
      "raw": 100,                                      raw mode: total columns
      "rows": [
        ["CCLK", "lvl", "H", [[6, 7, "f"], [15, 16, "r"]]],
        ["",     "mark", [[6, 10, "tKQ"]]],
        ["DB0-7","bus", [[0, "Z"], [50, "data valid"], [78, "Z"]]]
      ]
    }
  }
}

Slot-mode signal tokens (every row of a figure must have the same number of tokens):
  H / L        level; an edge is drawn at column 1 of the slot when the level changes
  C            one clock period starting high (falling edge at column 1)
  B:text       bus value; consecutive equal values merge and the text is centred if it fits
  X            unlabelled bus change
  Z            high impedance (~~~~)
  =            continue the previous state without an edge
  //           time break; put it in the same slot of every row
  T*n          repeat token T n times (e.g. "L*5", "B:valid*3")
Slot-mode marker tokens: "A:text" starts a span at column 1 of the slot, "a" continues it (a "//" between
"a" tokens also continues), "-" is empty. A span closes at column 1 of the next slot that is not "a".
Raw mode: "lvl" rows take an initial level and [start_col, end_col, "r"|"f"] edges (end-start > 1 draws a slow
edge with //// or \\\\); "bus" rows take [col, text] change points ("Z" = high impedance, "" = unlabelled);
"mark" rows take [start_col, end_col, text] spans.
"""
import json
import pathlib
import re
import sys

HI, LO = "‾", "_"


def expand(tokens):
    out = []
    for t in tokens:
        m = re.match(r"^(.*)\*(\d+)$", t) if isinstance(t, str) else None
        out.extend([m.group(1)] * int(m.group(2)) if m else [t])
    return out


def brk(w):
    left = (w - 2) // 2
    return " " * left + "//" + " " * (w - 2 - left)


def clock(w):
    low = max(1, (w - 1) // 2)
    s = HI + "\\" + LO * low + "/"
    return (s + HI * w)[:w]


def fill_char(kind):
    if kind[0] == "lvl":
        return HI if kind[1] == "H" else LO
    return "~" if kind[0] == "z" else "="


def slot_signal(tokens, w):
    segs, kinds, prev = [], [], None
    for t in tokens:
        if t == "//":
            segs.append(brk(w)); kinds.append(None); continue
        if t == "C":
            segs.append(clock(w)); kinds.append(("clk",)); prev = ("lvl", "H"); continue
        if t == "=":
            if prev is None:
                raise ValueError("'=' needs a previous state")
            segs.append(fill_char(prev) * w); kinds.append(prev); continue
        if t in ("H", "L"):
            cur, edge = ("lvl", t), ("/" if t == "H" else "\\")
        elif t == "Z":
            cur, edge = ("z",), "X"
        elif t == "X":
            cur, edge = ("bus", object()), "X"
        elif t.startswith("B:"):
            cur, edge = ("bus", t[2:]), "X"
        else:
            raise ValueError(f"bad token {t!r}")
        ch = fill_char(cur)
        if prev is None or prev == cur:
            seg = ch * w
        else:
            if prev[0] != "lvl" or cur[0] != "lvl":
                edge = "X"
            seg = fill_char(prev) + edge + ch * (w - 2)
        segs.append(seg); kinds.append(cur); prev = cur

    line = list("".join(segs))
    run_kind, placed, i, n = None, False, 0, len(tokens)
    while i < n:
        k = kinds[i]
        if k is None:
            i += 1
            continue
        j = i
        while j < n and kinds[j] == k:
            j += 1
        if k != run_kind:
            run_kind, placed = k, False
        if k[0] == "bus" and isinstance(k[1], str) and k[1] and not placed:
            text, start, end = k[1], i * w + 2, j * w
            area = end - start
            s = f" {text} " if len(text) + 2 <= area else (text if len(text) <= area else None)
            if s:
                off = start + (area - len(s)) // 2
                line[off:off + len(s)] = list(s)
                placed = True
        i = j
    return "".join(line)


def render_marks(length, spans):
    row = [" "] * (length + 2)
    for c0, c1, text in spans:
        n = c1 - c0 - 1
        if n >= len(text) + 2:
            extra = n - len(text) - 2
            a = extra // 2
            inner = "<" + "-" * a + text + "-" * (extra - a) + ">"
        elif n >= len(text):
            inner = text.center(n)
        else:
            raise ValueError(f"marker {text!r} needs {len(text)} columns, has {n}; widen the slots or shorten it")
        row[c0] = "|"
        row[c1] = "|"
        row[c0 + 1:c1] = list(inner)
    return "".join(row).rstrip()


def slot_marks(tokens, w):
    spans, i, n = [], 0, len(tokens)
    while i < n:
        t = tokens[i]
        if t.startswith("A:"):
            j = i + 1
            while j < n and (tokens[j] == "a" or (tokens[j] == "//" and j + 1 < n and tokens[j + 1] == "a")):
                j += 1
            spans.append((i * w + 1, j * w + 1 if j < n else n * w, t[2:]))
            i = j
        else:
            i += 1
    return render_marks(n * w, spans)


def raw_level(init, edges, length):
    level, row, c = init, [], 0
    for c0, c1, d in sorted(edges):
        row += [HI if level == "H" else LO] * (c0 - c)
        row += ["/" if d == "r" else "\\"] * (c1 - c0)
        level, c = ("H" if d == "r" else "L"), c1
    row += [HI if level == "H" else LO] * (length - c)
    return "".join(row)


def raw_bus(changes, length):
    row = []
    pts = sorted((int(c), t) for c, t in changes) + [(length, None)]
    for (c0, text), (c1, _) in zip(pts, pts[1:]):
        seg = ["~" if text == "Z" else "="] * (c1 - c0)
        if c0 > 0:
            seg[0] = "X"
        label = "" if text in ("Z", "") else text
        area = len(seg) - 1
        if label:
            s = f" {label} " if len(label) + 2 <= area else (label if len(label) <= area else None)
            if s is None:
                raise ValueError(f"bus text {label!r} does not fit in {area} columns")
            off = 1 + (area - len(s)) // 2
            seg[off:off + len(s)] = list(s)
        row += seg
    return "".join(row)


def build(name, fig):
    rows = fig["rows"]
    width = max(len(r[0]) for r in rows) + 2
    out, count = [], None
    for row in rows:
        label, kind = row[0], row[1]
        if "raw" in fig:
            n = int(fig["raw"])
            if kind == "lvl":
                body = raw_level(row[2], row[3], n)
            elif kind == "bus":
                body = raw_bus(row[2], n)
            elif kind == "mark":
                body = render_marks(n, [tuple(s) for s in row[2]])
            else:
                raise ValueError(f"{name}: unknown raw row kind {kind!r}")
        else:
            tokens = expand(row[2])
            if kind == "sig":
                if count is not None and len(tokens) != count:
                    raise ValueError(f"{name}: row {label!r} has {len(tokens)} slots, expected {count}")
                count = len(tokens)
                body = slot_signal(tokens, int(fig["w"]))
            elif kind == "mark":
                body = slot_marks(tokens, int(fig["w"]))
            else:
                raise ValueError(f"{name}: unknown row kind {kind!r}")
        out.append((label.ljust(width) + body).rstrip())
    return "\n".join(out)


def insert(doc_path, figures, dry):
    lines = pathlib.Path(doc_path).read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    done = []
    for name, (fig, block) in figures.items():
        anchor = fig.get("anchor")
        hits = [i for i, l in enumerate(lines) if l == f"<!-- WAVE:{name} -->"]
        if hits:
            i = hits[0]
            lines[i:i + 1] = ["```text"] + block.split("\n") + ["```"]
            done.append(name)
            continue
        if not anchor:
            print(f"skip {name}: no anchor and no <!-- WAVE:{name} --> placeholder")
            continue
        hits = [i for i, l in enumerate(lines) if l == anchor]
        if len(hits) != 1:
            sys.exit(f"{name}: anchor {anchor!r} found {len(hits)} times")
        s = hits[0] + 1
        while s < len(lines) and not lines[s].startswith("```text"):
            if lines[s].startswith("#"):
                sys.exit(f"{name}: no ```text block between the anchor and the next heading")
            s += 1
        if s >= len(lines):
            sys.exit(f"{name}: no ```text block after the anchor")
        e = s + 1
        while lines[e] != "```":
            e += 1
        lines[s:e + 1] = ["```text"] + block.split("\n") + ["```"]
        done.append(name)
    if not dry:
        pathlib.Path(doc_path).write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(("would regenerate: " if dry else "regenerated: ") + ", ".join(done))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    spec = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    figures = {name: (fig, build(name, fig)) for name, fig in spec["figures"].items()}
    if "--print" in sys.argv or "--insert" not in sys.argv:
        for name, (_, block) in figures.items():
            print(f"--- {name}\n{block}\n")
    if "--insert" in sys.argv:
        insert(sys.argv[sys.argv.index("--insert") + 1], figures, "--dry" in sys.argv)


if __name__ == "__main__":
    main()
