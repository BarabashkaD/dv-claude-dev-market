# Ventilation parameters V1–V8

Current sequencing: finish the FreeCAD design round before Bambu Studio print preparation. Any slicing/printed-path checks below belong to that later stage, not a mandatory intermediate CAD gate. Use the active SKILL.md and current project decisions for execution and scope.


Visual references: [V1–V4](../assets/ventilation/ventilation-v1-v4-parameters.png) and [V5–V8](../assets/ventilation/ventilation-v5-v8-parameters.png). These are conceptual property callouts, not calibrated dimensions. See the [decision guide](ventilation-design.md) for selection questions, integration rules and research sources.

Status: configurable package parameter definitions; not a validated parametric CAD library. Use alongside [the decision and design guide](ventilation-design.md).

## Common parameters and conventions

Define the owning part/surface, local normal, gravity/operating orientation, build orientation, vent role (entry/exit/undetermined), zone position/rotation, zone width/height or bounded sketch, parent wall thickness, structural border, keep-out distances and available external/internal clearance.

Units: lengths in mm, angles in degrees with reference axes declared, area in mm², counts as integers. Name whether a pitch is center-to-center and whether a clearance is per side, diametral or an assembled end gap. Use model-level preferred values with documented per-zone overrides after neighborhood review. No universal numerical sizes are adopted.

Choose a consistent pattern-driving mode: opening size plus pitch and bounds can derive the count, or count plus bounds can derive spacing. Do not independently constrain all of them. Derive receiving filter/fan geometry from the selected reference plus declared clearance. Keep calculated open area, minimum remaining ligament and actual pattern count in a reporting layer without cyclic dependencies.

The pictured callouts identify relevant properties schematically. Written definitions and actual CAD geometry control exact measurements; no numerical values may be inferred from the pictures.

## A — Angled through-passages: shared option

Show the [angled-pattern 3D cutaway and direction/section callouts](../assets/ventilation/angled-vent-passages-parameters.png) when discussing these parameters. This adds to the V1–V8 sheets rather than replacing them; it illustrates the axis-normal cylindrical-bore option. Spacing and geometry in the illustration are schematic.

Passage direction is an independent option for compatible patterns, especially V1–V4. A normal hole is not mandatory. A slanted straight passage is distinct from rotating a slot within the panel, tilting a louver hood, or constructing a turning baffle path. V7/V8 may use an angled supporting grille after checking compatibility with the filter/fan and available space; do not silently tilt the fan or media.

Ask the unresolved question: **Should the passages run perpendicular to the wall, or at an angle?** If angled, ask which way they should lean and whether the user wants to specify the angle or have suitable values compared for this case. Show the intended outside-to-inside direction in the actual mounted orientation. Establish a common preferred direction/angle with explicit per-zone exceptions where needed.

- `PassageTilt` (theta): angle away from the inward wall normal. Zero means perpendicular to the surface; a straight through-passage requires 0 <= theta < 90 degrees. The usable upper limit must be tighter when required by actual geometry and manufacturing. This is a geometric domain, not a recommended operating range.
- `PassageAngleToSurface` (alpha): optional alternative display/input, alpha = 90 degrees - theta. A perpendicular hole has alpha = 90 degrees. Choose one driving angle; derive the other.
- `PassageAzimuth` (phi): direction of the sideways lean, measured from a named local surface X axis towards Y. With inward unit normal n and right-handed local unit axes x and y, the outside-to-inside passage axis is a = cos(theta)n + sin(theta)(cos(phi)x + sin(phi)y). Azimuth has no effect at zero tilt. Declare its relation to installed up/down/left/right rather than the camera.
- `PassageProfilePlane`: choose **normal to passage axis** or **on the reference wall face**. Define `HoleDiameter`, slot dimensions and cell dimensions in that plane. A circular bore normal to its own axis has an elliptical opening on a flat wall when tilted; a circular face opening extruded obliquely produces a different passage. Do not call both geometries the same diameter definition.
- `EntryAnchor`, `ReferenceSurface`, `LocalFrame`: locate the entry profile and define direction. A planar panel uses its face/datums; a curved wall needs an explicit fixed-direction or per-location local-normal mode, followed by actual geometric intersection checks.
- `DirectionMode`: common direction for a zone by default; optional explicitly parameterized alternating/group directions. Review the full depth for crossings and remaining webs when axes differ.
- `CutExtent`: enough tool length to pass completely through the actual wall, with declared construction overrun if needed. Construction overrun is not an extra opening allowance.
- Derived `ExitOffset`, `PassageLength`, `EntryFootprint`, `ExitFootprint`, `MinimumPassageArea` and `MinimumRemainingWeb3D`. For a straight passage through parallel flat faces with normal thickness t: offset magnitude = t tan(theta), axis travel between the faces = t / cos(theta). For a circular cylindrical bore of axis-normal diameter D, the face ellipse has axes D and D / cos(theta). These formulas do not apply unchanged to curved/nonparallel walls, hoods or turning ducts.

Model the selected profile and direction as a real through-cut/sweep with stable datums. Check all entrance and exit footprints, the complete internal path, neighboring holes, border sections, ribs, bosses, mating lands and component/cable clearances. For nonparallel channels, face spacing alone cannot establish the remaining material. Re-evaluate unsupported ceilings and toolpaths in the selected print orientation. An angled path alone does not establish rain, dust, touch protection, directional airflow or improved cooling.

Illustrative geometry only: for t = 2.4 mm and theta = 30 degrees (alpha = 60 degrees), the exit shifts approximately 1.39 mm and the axis travel is approximately 2.77 mm. These values are not project defaults. The existing V1–V4 pictures show normal passages; they do not depict this optional tilt.

## V1 — Round holes

- `HoleDiameter`: clear through-hole diameter before optional edge treatment.
- `PitchX`, `PitchY`: center-to-center spacing in declared local axes.
- `RowStagger`: alternate-row offset; zero for a rectangular array.
- `Rows`, `Columns` or bounded pattern extent, with counts derived where chosen.
- `BorderMargin`: distance from outermost opening edge to the vent-zone boundary.
- `MinimumLigament`: minimum actual material between adjacent holes, reported/checked against a requirement. For normal cylindrical holes in an unstaggered row this is pitch minus diameter; staggered patterns need all neighboring distances checked.
- `EdgeBreak`: optional opening-edge treatment, with retained wall thickness protected.

## V2 — Rounded slots

- `SlotLength`: overall tip-to-tip length, not straight-center-section length.
- `SlotWidth`: clear opening width.
- `EndRadius`: for a true capsule slot, derive as half slot width; use an explicitly different profile when end curvature is independently controlled.
- `SlotAngle`: orientation in the panel relative to a named local axis.
- `PitchAlong`, `PitchAcross`: center spacings in the declared pattern axes.
- `Count`/rows/columns or bounded extent; `Stagger` where relevant.
- `BorderMargin`, `MinimumLigament`, and parent `PanelThickness`.
- `UnsupportedSpan`: print-orientation-dependent result/constraint, not automatically slot length in every build direction.

## V3 — Rounded-square / rectangular grid

- `OpeningWidth`, `OpeningHeight`: clear opening spans; equality gives square openings.
- `OpeningCornerRadius`: internal corner radius bounded by the opening size.
- `PitchX`, `PitchY`: center-to-center cell spacing.
- `WebX`, `WebY`: retained material between aligned openings; derive from pitch minus opening span for the simple aligned, normal-passage case. Angled passages require the full-depth section check.
- `Rows`, `Columns` or bounded field extent.
- `BorderMargin`, optional `GridAngle`, and parent `PanelThickness`.

## V4 — Hexagonal / honeycomb perforation

- `CellAcrossFlats`: clear distance between opposite parallel faces of a regular hexagonal opening.
- `WebThickness`: minimum normal material thickness between neighboring parallel cell walls in the chosen tiling.
- `CellOrientation`: declared flat-top/point-top orientation or angle from the local axis.
- `ArrayExtent`, rows/counts and stagger pattern as applicable.
- `CenterPitch`: derive from cell geometry, web definition and tiling orientation rather than independently driving a conflicting spacing.
- `BorderMargin`, `EdgeCellPolicy` (omit/clip with minimum-section checks), and parent `PanelThickness`.
- Optional `CornerReliefRadius`, reviewed for area and retained sections.

Check short ligaments at clipped cells, keep-outs and curved borders; a regular interior-cell thickness does not establish boundary strength.

## V5 — Hooded louvers

The illustration includes optional internal slats. If used, also parameterize `SlatCount`, `SlatPitch`, `SlatAngle`, `SlatThickness` and their root radii/clearances; include them in passage and printability checks. They are omitted for a simple single-hood opening.

- `OpeningWidth`: width across the clear passage.
- `ThroatHeight`: minimum clear opening height, distinct from overall hood height.
- `HoodProjection`: outward/inward depth relative to the parent panel.
- `HoodAngle`: angle to the parent surface with the angular datum declared.
- `HoodThickness`, `RootRadius`, `LipLength` where present.
- `RowPitch`, `ColumnPitch`, count or bounded extent.
- `OpeningDirection`: relation to gravity/installation, not merely the CAD camera.
- `BorderMargin`, parent `PanelThickness`, and support/cleaning access.
- `MinimumPassageArea`: derived bottleneck area in the true passage direction.

## V6 — Offset-baffle / covered vent

- `EntranceWidth`, `EntranceHeight`: external entrance dimensions.
- `CoverStandOff`: separation between the cover and the parent panel.
- `BaffleOffset`: relative displacement of successive openings/baffles.
- `BaffleOverlap`: amount by which the baffle interrupts a direct line of sight.
- `PassageGap`: minimum clear separation along the intended continuous route.
- `BaffleThickness`, `CoverThickness`, `RootRadius`.
- `BaffleCount`, `PathLength` and turn layout, using derived values where dependent.
- `ExitDimensions`, edge margins and assembly/removal/cleaning access.
- `MinimumPassageArea`: calculated across all route sections, not just the front aperture.

Check that the cover attachments leave a real connected air route; do not create a sealed decorative cap. Treat line-of-sight blockage separately from a verified ingress or safety rating.

## V7 — Removable filter carrier

- `VentOpeningWidth`, `VentOpeningHeight` and selected supporting grille geometry.
- `FilterWidth`, `FilterHeight`, `FilterThickness`: actual media/envelope data.
- `CarrierWallThickness`, `FilterSeatWidth`, `MediaEdgeOverlap`.
- `InsertionClearanceX`, `InsertionClearanceY`, `ThicknessClearance`: explicitly per side or total as defined.
- `RemovalDirection`, `RequiredRemovalTravel`, grip/access feature dimensions.
- `RetainingFeatureGeometry`: selected plastic lugs/rails/clips, using the installed interface rules; no new screw concept is assumed.
- `SealCompression` and perimeter contact only if a compatible seal is deliberately chosen; do not assume filter bypass is prevented.
- Process/performance records: selected medium, filtration requirement, clean/loaded pressure-loss data, replacement interval/criterion and flame/environment compatibility where required.

Do not select a nominal filter pore size as proof of the whole enclosure's filtration or thermal performance.

## V8 — Fan opening with guard provision

- `FanReference`: exact model and supplier drawing/configuration.
- `FanFrameWidth`, `FanFrameHeight`, `FanDepth`, mounting-interface pattern and cable envelope: reference-controlled dimensions, not arbitrary redesign variables.
- `PanelCutout`: shape and dimensions compatible with the selected fan flow passage and retained panel.
- `GuardPattern`, `GuardOpeningGap`, `GuardWebThickness`, frame/border geometry.
- `FanToGuardStandOff`, `RotorClearance`, `CableKeepOut`, `GuardDeflectionAllowance`.
- `AirflowDirection`: selected intake/exhaust relative to the actual enclosure path.
- `DuctOrPlenumDepth` where justified; complementary inlet/outlet geometry and separation.
- Performance/process records: supply/control, speed range, fan flow-pressure data, system resistance, required installed flow, acoustic target and failure/maintenance assumptions where relevant.

Guard gap and spacing are geometry parameters; access protection requires a defined requirement and evidence. This guidance does not certify a printed guard as finger-safe or select a hardware fastening method.

## Requirements and derived outputs

Record heat dissipation/duty, ambient range, allowable temperatures, mounting/orientation, contamination concerns, noise target and service needs as requirements, not merely sketch dimensions. Derived outputs include actual open area, field area ratio, remaining minimum webs, passage bottlenecks, predicted installed airflow and temperatures where a justified analysis exists. Measured temperatures and airflow are separate test results.

For comparisons, hold the thermal load, orientation and available field envelope constant where meaningful; report tradeoffs in open area, retained structure, printability, pressure loss, noise and cleaning. Do not infer a winning pattern from appearance alone.
