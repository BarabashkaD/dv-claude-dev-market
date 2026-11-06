# Collision checks: scope and method

## Scope belongs to the project

The skill gives the method. Which parts interact, which pairs to test, the minimum clearance and the allowed overlap come from the project (its interference or clearance spec). If the project has none, ask before choosing; do not invent a threshold.

## Work on exported parts

Use the parts exported as separate shapes (one solid per part, placement applied; links through `Part.getShape(obj, "", transform=True)`), not the assembly as one body. Order the work as pairs or small groups.

## Method per pair

1. Exact boxes: `a.optimalBoundingBox()`, `b.optimalBoundingBox()`. If the boxes, grown by the required clearance, do not intersect, the pair is clear; stop.
2. Otherwise localize: take the overlap of the grown boxes (or a box of about 20 mm around the closest area; a default) and cut both parts with it: `a_loc = a.common(box)`, `b_loc = b.common(box)`.
3. Interference: `a_loc.common(b_loc).Volume`; zero (within the project tolerance) means no overlap.
4. Clearance: `a_loc.distToShape(b_loc)[0]`, compare with the required value.
5. If a localized operation is still slow, shrink the box or split the part into zones and combine the results.

## Reporting

Print one `RESULT {json}` line: pair names, overlap volume, minimum distance, box used. Heavy operations on a whole assembly (`common`, `distToShape`, `check`, `section`) can run for minutes or hang; that is why the box is the default. Run limits: `guarding-autonomous-runs`.
