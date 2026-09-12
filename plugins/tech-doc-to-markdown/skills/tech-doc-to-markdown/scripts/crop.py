"""Render zoomed crops of document pages.

Coordinates are PDF points (1/72 inch, origin top-left; survey.json lists page sizes) or page fractions 0..1.
To convert a pixel position p in a render made at D DPI: points = p * 72 / D.

Usage:
  python crop.py INPUT --page N --rect X0 Y0 X1 Y1 [--units pt|frac] [--dpi 400] --out FILE.png
  python crop.py INPUT --spec crops.json --out-dir DIR
      crops.json: {"name": [page, x0, y0, x1, y1, dpi], ...}   (points; add "frac" as 7th item for fractions)
"""
import argparse
import json
import pathlib
import sys

import pymupdf


def crop(doc, page_no, rect, units, dpi, out_path):
    page = doc[page_no - 1]
    x0, y0, x1, y1 = rect
    if units == "frac":
        w, h = page.rect.width, page.rect.height
        x0, x1, y0, y1 = x0 * w, x1 * w, y0 * h, y1 * h
    clip = pymupdf.Rect(x0, y0, x1, y1) & page.rect
    if clip.is_empty:
        sys.exit(f"crop {out_path}: rectangle is outside page {page_no} ({page.rect})")
    out_path = pathlib.Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pix = page.get_pixmap(dpi=dpi, clip=clip)
    pix.save(out_path)
    print(f"{out_path}  page {page_no}  {clip}  {pix.width}x{pix.height}px")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--page", type=int)
    ap.add_argument("--rect", type=float, nargs=4)
    ap.add_argument("--units", choices=["pt", "frac"], default="pt")
    ap.add_argument("--dpi", type=int, default=400)
    ap.add_argument("--out")
    ap.add_argument("--spec")
    ap.add_argument("--out-dir")
    args = ap.parse_args()

    doc = pymupdf.open(args.input)
    if args.spec:
        if not args.out_dir:
            sys.exit("--spec needs --out-dir")
        spec = json.loads(pathlib.Path(args.spec).read_text(encoding="utf-8"))
        for name, item in spec.items():
            page_no, x0, y0, x1, y1, dpi = item[:6]
            units = item[6] if len(item) > 6 else "pt"
            crop(doc, int(page_no), (x0, y0, x1, y1), units, int(dpi), pathlib.Path(args.out_dir) / f"{name}.png")
    else:
        if not (args.page and args.rect and args.out):
            sys.exit("give --page, --rect and --out, or --spec and --out-dir")
        crop(doc, args.page, args.rect, args.units, args.dpi, args.out)


if __name__ == "__main__":
    main()
