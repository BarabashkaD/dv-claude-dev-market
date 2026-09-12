"""Measure dot-matrix figures: each drawn square (outlined = empty, solid = filled) becomes one character.

Works for figures that draw every grid position as a box. Grids that draw only the lit dots (no outline for
empty positions) show gaps as '?'; infer the pitch from neighbouring rows and confirm visually.

Output per detected row: count, then '#' filled, '.' empty, '?' missing position (gap of one pitch),
and fill ratios between 0.3 and 0.7 listed as ambiguous (re-check those visually).

Usage:
  python dot_grid.py INPUT --page N --rect X0 Y0 X1 Y1 [--dpi 900] [--threshold 150] [--fill 0.5]
Coordinates in PDF points. Use a high DPI (600-900) so neighbouring squares stay separate blobs.
"""
import argparse

import numpy as np
import pymupdf
from scipy import ndimage


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--page", type=int, required=True)
    ap.add_argument("--rect", type=float, nargs=4, required=True)
    ap.add_argument("--dpi", type=int, default=900)
    ap.add_argument("--threshold", type=int, default=150, help="gray level below which a pixel is dark")
    ap.add_argument("--fill", type=float, default=0.5, help="interior dark ratio above which a square is filled")
    args = ap.parse_args()

    doc = pymupdf.open(args.input)
    pix = doc[args.page - 1].get_pixmap(dpi=args.dpi, clip=pymupdf.Rect(*args.rect), colorspace=pymupdf.csGRAY)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    dark = img < args.threshold
    blobs = ndimage.binary_fill_holes(dark)
    lab, _ = ndimage.label(blobs)
    boxes = []
    for sl in ndimage.find_objects(lab):
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        if h >= 8 and w >= 8:
            boxes.append((sl, h, w))
    if not boxes:
        print("no square-like blobs found; try another --threshold or --dpi")
        return
    med = float(np.median([b[1] for b in boxes]))
    squares = []
    for sl, h, w in boxes:
        if 0.6 * med < h < 1.5 * med and 0.6 * med < w < 1.5 * med:
            core = dark[sl][h // 4: h - h // 4, w // 4: w - w // 4]
            squares.append(((sl[0].start + sl[0].stop) / 2, (sl[1].start + sl[1].stop) / 2, float(core.mean())))
    if not squares:
        print("no squares of consistent size found")
        return
    squares.sort()
    rows, current = [], [squares[0]]
    for s in squares[1:]:
        if abs(s[0] - current[-1][0]) < med * 0.6:
            current.append(s)
        else:
            rows.append(current)
            current = [s]
    rows.append(current)

    print(f"{len(rows)} rows, square size ~{med:.0f}px at {args.dpi} DPI")
    for row in rows:
        row.sort(key=lambda s: s[1])
        xs = [s[1] for s in row]
        pitch = float(np.median(np.diff(xs))) if len(xs) > 1 else med
        line, prev = "", None
        for s in row:
            if prev is not None:
                line += "?" * max(int(round((s[1] - prev) / pitch)) - 1, 0)
            line += "#" if s[2] > args.fill else "."
            prev = s[1]
        amb = [round(s[2], 2) for s in row if 0.3 < s[2] < 0.7]
        print(f"{len(line):4d} {line}" + (f"   ambiguous fill ratios: {amb}" if amb else ""))


if __name__ == "__main__":
    main()
