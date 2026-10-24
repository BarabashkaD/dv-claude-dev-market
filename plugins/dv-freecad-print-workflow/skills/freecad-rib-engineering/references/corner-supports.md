# Configurable corner-support defaults

Current sequencing: finish the FreeCAD design round before Bambu Studio print preparation. Any slicing/printed-path checks below belong to that later stage, not a mandatory intermediate CAD gate. Use the active SKILL.md and current project decisions for execution and scope.


Apply these configurable package defaults when creating or revising 3D-printed enclosure corner supports for a lid. They are local design preferences, not upstream FreeCAD requirements or a certified strength standard. Preserve archived revisions unless the user asks to change them.

- **Root fillets are required:** add fillets where each load-bearing corner support joins the base floor or lid. Choose and record radii that fit the material, print orientation, support dimensions and available clearance. If a required blend cannot fit, resolve or report that local design conflict rather than silently omitting it.
- **Join supports continuously to the surrounding case structure:** avoid acute angles, sharp re-entrant creases, thin wedges and narrow trapped gaps at support-to-wall joints. Prefer solid-filled joints with tangent, rounded transitions. Merely overlapping a cylinder with a wall is insufficient if it leaves those defects.
- **Protect functional geometry:** retain flat screw seats, nut-pocket dimensions, screw engagement, locating surfaces and mating clearance. Use exposed inner root blends where the outside must remain a locating surface. Do not create clearance by silently thinning the surrounding wall.
- **Validate the result:** use native editable features; check recompute state, valid single solids, clear screw bores and nut pockets, lid seating, electronics/cable/fastener clearance and watertight print meshes. Review sliced wall paths and small bridges during the later print-preparation stage, when slicing is available. Distinguish geometry checks from unperformed physical fit and strength tests.

## Generic dimensional example, not universal dimensions

An illustrative enclosure might use 0.8 mm fillets at four base corner roots, 1.2 mm tangent blends at filled column-to-wall joints, and 0.6 mm fillets at exposed inner roots of four lid nut supports while preserving outer locating surfaces. These are example values only, not verified dimensions or a strength rating. Adapt and verify the radii for each design.
