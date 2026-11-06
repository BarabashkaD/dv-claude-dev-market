# Guards for a zone edit

Fragments are generic; `part` (before), `new` (after), `zones`, `boxes` (disjoint boxes) are `Part.Shape` objects, `exported_parts` is a dict. Numbers are defaults a project may override. Do not run booleans on the whole body when a boxed one will do; see `../../freecad-headless-analysis/references/collision-scope.md` for the same reasoning.

```
def grown(box, m):   # box grown by m mm on every side
    b = box.BoundBox
    return Part.makeBox(b.XLength + 2*m, b.YLength + 2*m, b.ZLength + 2*m,
                        FreeCAD.Vector(b.XMin - m, b.YMin - m, b.ZMin - m))
```

## 1. Outside the zones, xor is 0

Work in a check box per zone: the zone grown by about 20 mm (default), minus the zone itself. Cut only the local pieces:

```
for box in boxes:
    chk = grown(box, 20.0)                       # Part.makeBox around the zone, +20 mm each side
    a = part.common(chk).cut(box)
    b = new.common(chk).cut(box)
    leak = a.cut(b).Volume + b.cut(a).Volume
    assert leak <= 1e-3   # mm3
```

Between the check boxes, the aggregate guard 2 covers the rest: total dV and dA equal the sum of the zone changes, so nothing else moved in volume or area. A whole-body xor (`part.cut(new)` etc.) only when allowed and under the run limits.

The outside-zone measure is this xor-0 guard (plus the aggregate guard 2); there is no separate distance guard.

## 2. dV and dA match the written calculation, per zone and in total

Write the expected numbers into the record before the run, then compare each zone's change and the total:

```
def tol(expected):                               # 0.001 % of the EXPECTED change, floor 1e-3
    return max(1e-5 * abs(expected), 1e-3)

for z_old, z_new, eV, eA in zone_records:        # per zone
    assert abs((z_new.Volume - z_old.Volume) - eV) <= tol(eV)
    assert abs((z_new.Area - z_old.Area) - eA) <= tol(eA)
assert abs((new.Volume - part.Volume) - total_eV) <= tol(total_eV)
assert abs((new.Area - part.Area) - total_eA) <= tol(total_eA)
```

Never express the tolerance relative to the whole body: 0.001 % of a large part can be larger than the edit itself. Do not adjust expected values after seeing the result. If the measurement is right and the calculation wrong, say so in the report.

## 3. "Before" repeats the previous round

Take volume, area, solid and face counts of the part from the previous round's recorded output. In the first round there is no previous record: measure the baseline file yourself and record it as "before". If a later fresh measurement of the baseline differs, stop: the baseline file changed or was read differently.

## 4. `check(True)` of the zones

```
for z in zones:
    z.check(True)   # raises on an invalid shape
```

Run the same on the whole body only when permitted (time; see the run-limit rules in `guarding-autonomous-runs`).

## 5. Print mesh closed, also at neighbouring values

```
import MeshPart

def closed(shape, lin, ang):
    m = MeshPart.meshFromShape(Shape=shape.copy(), LinearDeflection=lin,
                               AngularDeflection=ang, Relative=False)
    return m.isSolid() and not m.hasNonManifolds()

for lin in (0.0145, 0.015, 0.0155):
    for ang in (0.075, 0.08, 0.085):
        assert closed(new, lin, ang), (lin, ang)
```

Scope (one rule everywhere): during the round run this on the zones or the check boxes (`new` cut to each box), at the default and at the neighbouring values. Mesh the whole body once at round closure (the single full check after the round closes, see `cad-print-workflow`), or earlier only if the plan allows it. Do not mesh the whole body at nine deflection values inside a round.

Defaults: `LinearDeflection=0.015, AngularDeflection=0.08, Relative=False`; neighbours 0.0145...0.0155 x 0.075...0.085. If a neighbouring value opens the mesh, the corner is fragile: fix the geometry (sliver face, near-tangent faces, tiny edge). Do not change mesh parameters to hide it.

## 6. Collisions

Method and scope: `../../freecad-headless-analysis/references/collision-scope.md` (pair boxes, then a localized `common` in a box of about 20 mm around the zone; the project sets which pairs and what overlap is allowed).

```
for name, other in exported_parts.items():   # excludes the edited part itself
    if name == edited_name or not new.BoundBox.intersect(other.BoundBox):
        continue
    for box in boxes:
        chk = grown(box, 20.0)
        assert new.common(chk).common(other.common(chk)).Volume <= 1e-3, (name, box)
```

Build `exported_parts` from the files actually exported for printing or assembly, not from a loop over all document objects (helpers, sketches, references and hidden bodies give false hits and cost time).

## Targeted seam removal

Verified in FreeCAD 1.1.4: the class is `Part.ShapeUpgrade.UnifySameDomain(shape, UnifyEdges, UnifyFaces, ConcatBSplines)`; methods `keepShape(s)`, `keepShapes([s, ...])`, `build()`, `shape()` (a method, there is no `.Shape` attribute). `keepShapes` takes edges or vertices, not faces (kept faces were merged anyway in the test).

```
region = boxes[0].multiFuse(boxes[1:]) if len(boxes) > 1 else boxes[0]
keep = [e for e in new.Edges
        if not e.BoundBox.intersect(region.BoundBox) or e.common(region).Length < 1e-7]   # edges outside the zones (box prefilter first)
u = Part.ShapeUpgrade.UnifySameDomain(new, True, True, True)
u.keepShapes(keep)
u.build()
clean = u.shape()
assert clean.isValid() and abs(clean.Volume - new.Volume) <= 1e-3
print(len(new.Faces), "->", len(clean.Faces))   # compare with the expected drop
```

Test on three boxes fused in a row (14 faces): unifying everything gives 6 faces; keeping the edges outside a zone around the first seam gives 10, volume unchanged, so only that seam is removed. `Shape.removeSplitter()` behaves like the whole-body call (6).

## BRep tolerance after booleans (repair default)

Booleans and ShapeFix often inflate `Edge.Tolerance` (also face and vertex tolerances). Default rule, a project may override: an edge, face or vertex with an inflated tolerance is lowered to its measured geometric deviation x 1.1, and no tolerance is ever set above 5e-4 mm (the cap). A vertex may be raised only up to the tolerance of an incident edge.

Verified in FreeCAD 1.1.4 (`Part.Shape`): `s.fixTolerance(value, Part.Edge)` forces that value on all edges of `s` (returns None); `s.limitTolerance(0, 5e-4)` caps every tolerance at 5e-4 and returns True if anything changed (`limitTolerance(tmin, tmax, ShapeType)`; tmin = 0 means only the maximum is applied). Read values with `e.Tolerance`.

```
changed = clean.limitTolerance(0, 5e-4)       # enforce the cap on the whole result
assert clean.isValid()
```

Notes:
- Lowering tolerances alone does not close an open print mesh. A fragile corner is fixed in geometry, for example by filling a vanishing fillet with a small box-bounded patch, fused in, with seams removed by targeted `UnifySameDomain`.
- An over-aggressive limit (for example 1e-7) can make the body invalid: reject that variant and keep the previous one.
