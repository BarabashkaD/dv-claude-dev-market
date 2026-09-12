"""Survey a document and render page images for reading.

Opens anything PyMuPDF supports: PDF, XPS, EPUB, MOBI, FB2, CBZ, SVG and common image formats.

Writes into --out:
  survey.json          metadata, outline, per-page inventory
  text/pNNN.txt        text layer per page (may be empty for scans)
  full/pNNN.png        full page at --dpi (default 165)
  half/pNNN_a.png      top 55 % at --half-dpi (default 220)
  half/pNNN_b.png      bottom 55 % at --half-dpi
  preview/pNNN.png     with --preview: small renders at 110 DPI only (fast classification)

Usage:
  python survey.py INPUT --out DIR [--pages 1-5,9] [--preview] [--no-render] [--no-halves]
                   [--dpi 165] [--half-dpi 220] [--password PW]
"""
import argparse
import json
import pathlib
import sys

import pymupdf


def parse_pages(spec, count):
    if not spec:
        return list(range(1, count + 1))
    pages = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            pages.extend(range(int(a), int(b) + 1))
        else:
            pages.append(int(part))
    return [p for p in dict.fromkeys(pages) if 1 <= p <= count]


def image_coverage(page):
    area = abs(page.rect)
    if not area:
        return 0.0
    covered = 0.0
    for img in page.get_images(full=True):
        try:
            for r in page.get_image_rects(img[0]):
                covered += abs(r & page.rect)
        except Exception:
            pass
    return min(covered / area, 1.0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--out", required=True)
    ap.add_argument("--pages")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--no-halves", action="store_true")
    ap.add_argument("--dpi", type=int, default=165)
    ap.add_argument("--half-dpi", type=int, default=220)
    ap.add_argument("--password")
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    doc = pymupdf.open(args.input)
    if doc.needs_pass:
        if not args.password or not doc.authenticate(args.password):
            sys.exit("The document requires a user password; ask the user for it (--password).")

    pages = parse_pages(args.pages, doc.page_count)
    (out / "text").mkdir(parents=True, exist_ok=True)
    info = {
        "file": str(pathlib.Path(args.input).resolve()),
        "format": doc.metadata.get("format") if doc.metadata else None,
        "page_count": doc.page_count,
        "is_pdf": doc.is_pdf,
        "encrypted_permissions_only": bool(doc.metadata and doc.metadata.get("encryption")) and not doc.needs_pass,
        "metadata": doc.metadata,
        "outline": doc.get_toc(simple=True)[:500],
        "pages": [],
    }

    print(f"{doc.page_count} pages, format {info['format']}, outline entries {len(info['outline'])}")
    print(f"{'page':>4} {'label':>8} {'size(pt)':>11} {'chars':>6} {'imgs':>4} {'cover':>5} {'vec':>5}  kind")
    for pno in pages:
        page = doc[pno - 1]
        text = page.get_text("text")
        (out / "text" / f"p{pno:03d}.txt").write_text(text, encoding="utf-8", newline="\n")
        images = page.get_images(full=True)
        try:
            vectors = len(page.get_drawings())
        except Exception:
            vectors = None
        cover = image_coverage(page)
        chars = len(text.strip())
        if chars < 20 and cover > 0.6:
            kind = "scan"
        elif cover > 0.6 and chars >= 20:
            kind = "scan+text-layer"
        elif chars >= 20:
            kind = "digital"
        else:
            kind = "vector/blank"
        try:
            label = page.get_label() or ""
        except Exception:
            label = ""
        rec = dict(page=pno, label=label, width_pt=round(page.rect.width, 1), height_pt=round(page.rect.height, 1),
                   chars=chars, images=len(images), image_coverage=round(cover, 2), vector_drawings=vectors, kind=kind)
        info["pages"].append(rec)
        print(f"{pno:4d} {label:>8} {page.rect.width:5.0f}x{page.rect.height:<5.0f} {chars:6d} {len(images):4d} "
              f"{cover:5.2f} {vectors if vectors is not None else '-':>5}  {kind}")

        if args.no_render:
            continue
        if args.preview:
            (out / "preview").mkdir(exist_ok=True)
            page.get_pixmap(dpi=110).save(out / "preview" / f"p{pno:03d}.png")
            continue
        (out / "full").mkdir(exist_ok=True)
        page.get_pixmap(dpi=args.dpi).save(out / "full" / f"p{pno:03d}.png")
        if not args.no_halves:
            (out / "half").mkdir(exist_ok=True)
            r = page.rect
            top = pymupdf.Rect(r.x0, r.y0, r.x1, r.y0 + r.height * 0.55)
            bottom = pymupdf.Rect(r.x0, r.y0 + r.height * 0.45, r.x1, r.y1)
            page.get_pixmap(dpi=args.half_dpi, clip=top).save(out / "half" / f"p{pno:03d}_a.png")
            page.get_pixmap(dpi=args.half_dpi, clip=bottom).save(out / "half" / f"p{pno:03d}_b.png")

    kinds = {}
    for rec in info["pages"]:
        kinds[rec["kind"]] = kinds.get(rec["kind"], 0) + 1
    info["summary"] = kinds
    (out / "survey.json").write_text(json.dumps(info, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    print("page kinds:", kinds)
    print("written:", out.resolve())


if __name__ == "__main__":
    main()
