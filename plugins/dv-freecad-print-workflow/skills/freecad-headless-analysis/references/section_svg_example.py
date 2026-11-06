"""Example for the freecad-headless-analysis skill: cross-section of a solid to SVG,
headless (Shape.slice + hand-written SVG).

Run (freecadcmd treats argv as files, so parameters are environment variables):
  SEC_IN=model.step SEC_AXIS=y SEC_AT=10 SEC_OUT=section.svg scripts/fc-quiet.sh references/section_svg_example.py

  SEC_IN      input model (.step/.stp/.brep/.FCStd)                      [required]
  SEC_OBJ     FCStd only: name of the object to cut (default: all top-level objects)
  SEC_AXIS    plane normal: x | y | z (default y)
  SEC_AT      plane offset along the axis, mm (default: middle of the exact bounding box)
  SEC_BOX     optional slab clip "xmin,ymin,zmin,xmax,ymax,zmax" (mm): only this region is cut
              (use it on big/complex bodies; the whole-body slice can take minutes)
  SEC_OUT     output .svg (default: <input>_section.svg)
  SEC_ALLOW_MULTI=1   allow several solids (they are fused as a compound; overlaps are NOT checked)
  SEC_EXPECT_AREA     optional expected area, mm2: RESULT gets area_err

View convention (standard engineering views, never mirrored): axis x = right view (screen: y right, z up),
axis y = front view (x right, z up), axis z = top view (x right, y up).
SVG user units = millimetres at 1:1 (viewBox in mm); stroke and font scale with the part size.
Prints exactly one line: RESULT {json}. Any failure prints RESULT {"error": ...}.
Tested only on a small prismatic part (box with a hole and a step); not on BSpline/large bodies.
"""
import os, sys, time, json
import FreeCAD as App, Part
V = App.Vector

def fail(msg, **kw):
    print("RESULT " + json.dumps(dict(error=msg, **kw), ensure_ascii=False))

def load(src):
    names = []
    if src.lower().endswith(".fcstd"):
        doc = App.openDocument(src)
        obj_name = os.environ.get("SEC_OBJ")
        objs = [doc.getObject(obj_name)] if obj_name else [o for o in doc.Objects if not o.InList]
        if obj_name and objs[0] is None:
            raise RuntimeError("object %s not found" % obj_name)
        solids = []
        for o in objs:
            try:
                s = Part.getShape(o, "", transform=True)   # resolves App::Link / App::Part placements
            except Exception:
                continue
            if s.isNull() or not s.Solids:
                continue
            names.append(o.Name); solids += s.Solids
        return solids, names
    return Part.read(src).Solids, names

try:
    src = os.environ.get("SEC_IN")
    if not src:
        raise RuntimeError("set SEC_IN")
    axis = os.environ.get("SEC_AXIS", "y").lower()
    if axis not in ("x", "y", "z"):
        raise RuntimeError("SEC_AXIS must be x, y or z")
    out = os.environ.get("SEC_OUT") or os.path.splitext(src)[0] + "_section.svg"
    t0 = time.time()
    solids, names = load(src)
    if not solids:
        raise RuntimeError("no solids in input")
    if len(solids) > 1 and os.environ.get("SEC_ALLOW_MULTI") != "1":
        raise RuntimeError("input has %d solids %s; select one (SEC_OBJ) or set SEC_ALLOW_MULTI=1" % (len(solids), names))
    shape = solids[0] if len(solids) == 1 else Part.Compound(solids)
    box = os.environ.get("SEC_BOX")
    if box:
        a = [float(x) for x in box.split(",")]
        shape = shape.common(Part.makeBox(a[3]-a[0], a[4]-a[1], a[5]-a[2], V(a[0], a[1], a[2])))
    bb = shape.optimalBoundingBox() if hasattr(shape, "optimalBoundingBox") else shape.BoundBox
    n = {"x": V(1, 0, 0), "y": V(0, 1, 0), "z": V(0, 0, 1)}[axis]
    lo, hi = {"x": (bb.XMin, bb.XMax), "y": (bb.YMin, bb.YMax), "z": (bb.ZMin, bb.ZMax)}[axis]
    at = float(os.environ.get("SEC_AT", (lo + hi) / 2))

    def prj(p):                       # screen coords, y down (SVG)
        if axis == "x": return (p.y, -p.z)
        if axis == "y": return (p.x, -p.z)
        return (p.x, -p.y)

    wires = shape.slice(n, at)
    if not wires:
        raise RuntimeError("empty section at %s=%g" % (axis, at))
    # Area from faces (outer/inner nesting resolved by the face maker), not from wire orientation.
    face = Part.makeFace(wires, "Part::FaceMakerBullseye")
    area = face.Area
    paths, xs, ys = [], [], []
    for w in wires:
        pts = [prj(p) for p in w.discretize(Deflection=0.01)]   # 0.01 mm chord tolerance on arcs
        xs += [p[0] for p in pts]; ys += [p[1] for p in pts]
        paths.append("M" + " L".join("%.4f,%.4f" % p for p in pts) + " Z")
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    Wd, Hd = x1 - x0, y1 - y0
    size = max(Wd, Hd, 1e-6)
    sw, fs, off = size/300, size/25, size/12      # stroke, font size, dimension offset: scale with the part
    dim = ('<g stroke="#0044cc" stroke-width="%g" fill="#0044cc" font-size="%g" font-family="sans-serif">'
           '<line x1="%g" y1="%g" x2="%g" y2="%g"/><text x="%g" y="%g" text-anchor="middle" stroke="none">%.2f mm</text>'
           '<line x1="%g" y1="%g" x2="%g" y2="%g"/><text x="%g" y="%g" stroke="none">%.2f mm</text></g>'
           % (sw*0.7, fs, x0, y1+off, x1, y1+off, (x0+x1)/2, y1+off-fs*0.3, Wd,
              x1+off, y0, x1+off, y1, x1+off+fs*0.3, (y0+y1)/2, Hd))
    m = off + 6*fs
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%g %g %g %g" width="%gmm" height="%gmm">'
           '<g fill="#dddddd" stroke="#000000" stroke-width="%g" fill-rule="evenodd">%s</g>%s</svg>'
           % (x0-off, y0-off, Wd+off+m, Hd+off+m, Wd+off+m, Hd+off+m, sw, "".join('<path d="%s"/>' % p for p in paths), dim))
    open(out, "w", encoding="utf8").write(svg)
    res = {"time_s": round(time.time() - t0, 3), "axis": axis, "at": round(at, 4), "n_solids": len(solids),
           "wires": len(wires), "faces": len(face.Faces), "width": round(Wd, 4), "height": round(Hd, 4),
           "area": round(area, 4), "svg_bytes": len(svg)}
    exp = os.environ.get("SEC_EXPECT_AREA")
    if exp: res["area_err"] = round(area - float(exp), 6)
    print("RESULT " + json.dumps(res))
except Exception as e:
    fail(repr(e)[:300])
