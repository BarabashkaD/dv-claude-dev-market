---
name: freecad-zone-edit
description: Zone method for local edits of a BRep solid in FreeCAD, with guards that prove the edit is correct. Use for a local edit, repair, moving a feature, repeated identical features (latches, bosses, pockets), or patching a solid or STEP/BRep body in FreeCAD without rebuilding it. Not for new parametric modelling from scratch or for CadQuery/OpenSCAD work.
---

# Zone-method local edits of a BRep solid

Change a small region of a finished solid, leave everything else unchanged, and prove it with numbers. Work in FreeCAD 1.1.4 headless (Part module). Headless execution, the launcher and quiet output: `freecad-headless-analysis`. Run limits: `guarding-autonomous-runs` (plugin dv-agent-controller). Collision scope: `../freecad-headless-analysis/references/collision-scope.md`.

Numbers below are defaults; a project may override them.

## When to use

- Local edit, repair, moved feature, or one feature repeated at several sites on an existing solid.
- The body has no usable feature tree (imported STEP/BRep), or a recompute would disturb unrelated geometry.

If the part is rebuilt wholesale, use the normal parametric workflow instead.

## Before building

1. Write down the expected result first: which regions change, expected dV and dA per zone and in total. Do this before any run; the guards compare against this record.
2. Take "before" values from the previous round's recorded result. In the first round there is none: record your own measurement of the baseline file (volume, area, solid and face counts) and use it as "before" (see [guards](references/guards.md)).
3. Keep the baseline file untouched; write the edit to a new file. Save the result as BREP/STEP; an FCStd meant for a person goes through `freecad-gui-macro` (a headless FCStd is a trap).

## Build (zone method)

1. **Cut the region.** Choose a box around the edit, slightly larger than the feature, aligned to existing faces where possible. Keep the cut-out piece as the "old zone". Boxes must be pairwise disjoint. The local check box for guards is the zone grown by about 20 mm (default).
2. **Build the reference zone once.** Choose a typical, sound site as the reference, not a defective one. Construct the new content of one box (new feature, repaired geometry) as a closed solid that fills the box and meets the box walls exactly.
3. **Place identical sites as copies.** Get the rigid transform from the sites (site datums, or bounding-box centres plus the known orientation) and verify it: compare the site's old zone with the reference old zone under that transform (xor volume <= 1e-3 mm3). A mirrored site needs a mirrored reference or counts as conflicting. If it matches, place a rigid copy of the new reference zone. A conflicting site (different neighbouring wall, nearby edge, extra hole) is cut and built separately; never force the reference onto it.
   To move a feature along a uniform wall, shift the whole strip (the box content across the full run of the wall), not the feature alone, so no seam appears inside the wall.
4. **Integrate.** `(part - boxes) + zones`: one pair of booleans on the body. Cut all boxes in one operation, fuse all zones in one operation. Many small booleans on the body accumulate tolerance and slow runs.
5. **Remove seams.** Use `Part.ShapeUpgrade.UnifySameDomain` (1.1.4), not `Shape.removeSplitter()`, which merges the whole body. `keepShapes` protects the listed edges or vertices from being merged away, so pass every edge that does not touch a zone; only seams on the box walls and inside the zones are removed. Confirm by the face count dropping by the expected number and the volume unchanged. Fragment: [references/guards.md](references/guards.md#targeted-seam-removal).

Then run the guards.

## Guards (proof of correctness)

All must pass before the edit is accepted. Call fragments: [references/guards.md](references/guards.md).

- Outside the zones, xor between before and after is 0.
- dV and dA equal the calculation written down before the run, per zone and in total (tolerance 0.001 % of each zone's expected change, floor 1e-3 mm3 / mm2; never relative to the whole body).
- "Before" values repeat the previous round's numbers.
- `check(True)` on the zones; on the whole body only when allowed (it can be slow on large bodies).
- The print mesh of the zones or check boxes is closed with the default parameters and at neighbouring deflection values; the whole body is meshed once at round closure (earlier only if the plan allows). A fragile corner is fixed in the geometry, not by tuning mesh parameters.
- Collisions are tested only against exported physical parts, never against every document object.

## Reporting

State the zones, expected versus measured dV/dA, guard results, and anything skipped. A failed guard is a finding: localise the first cause (shrink the box, test one site, test one boolean) before changing anything else.
