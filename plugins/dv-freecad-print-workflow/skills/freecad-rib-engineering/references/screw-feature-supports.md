# Screw-feature supports: configurable defaults

Current sequencing: finish the FreeCAD design round before Bambu Studio print preparation. Any slicing/printed-path checks below belong to that later stage, not a mandatory intermediate CAD gate. Use the active SKILL.md and current project decisions for execution and scope.


Configurable package guidance. Applies to new or explicitly authorized revisions of plastic screw-support features. This is the active local design reference; existing enclosure geometry and upstream production-suite files are unchanged. Native CAD, slicing and physical validation of this complete gusset workflow remain pending.

## Scope and support layout

Plastic features that carry screw loads—including screw bosses, structural screw-channel columns, nut-pocket carriers and insert carriers—shall have triangular gusset support to their parent surface or surrounding structure, regardless of the feature's angle to that surface. This concerns the supporting plastic, not the metal screw or the pocket void.

Select the arrangement per item and make the gusset count, orientation, reach, height, thickness and blend radii editable. Counts may be 1, 2, 3 or more where surrounding structural connections justify the arrangement. An isolated feature remote from surrounding support requires at least three gussets distributed around it. Four is an illustrative configuration, not an additional universal default. The count is a configurable package design default, not proof of load capacity.

For a feature near another structural object, review whether the two can share a continuous load path. Prefer connection to the highest suitable load-bearing surrounding element, especially a side wall, where clearances and the part's function permit. Define proximity from feasible connection reach and the actual layout; no universal distance is assumed. Keep independently manufactured/removable parts separate unless a real joint is intentionally designed.

Existing stiffening ribs may serve as gussets when they reach and merge into the screw-feature carrier with an effective load-transfer section. Review extending, redirecting or moving a rib to meet the pocket carrier as an optimization option. Preserve the panel's reinforcement purpose, pocket axis, screw/driver access and functional keep-outs. Do not move the pocket merely to align it with a rib without authorization.

All gusset-to-floor, gusset-to-boss and gusset-to-wall/rib structural junctions require rounded, solid-filled transitions. Avoid acute re-entrant creases, free-standing knife edges, unsupported thin wedges, gaps and edge-only contact. Preserve flat hardware bearing seats, nut anti-rotation geometry, insert installation access and the screw channel. Blend radii are project-specific.

## Zero-height termination

For a free gusset end on the case floor, reduce added height progressively until its upper surface merges into the parent floor at exactly zero added height, with a horizontal tangent. There must be no upright nose, residual step, raised end pad or abrupt final drop. The floor continues under the entire transition; this is a smooth change in the thickness of one solid, not a detached zero-thickness fin.

In a local section, let the floor top be height zero and let x increase outward from the supported object's exterior toward the end. The nominal end conditions are h(L) = 0 and dh/dx at L = 0. Check the final dressed/filleted geometry against these conditions; rounding a blunt end is not equivalent. The physical print approximates the smooth nominal surface in layers; inspect the sliced termination rather than promising mathematically exact printed tangency.

## Two primary sizing parameters

| Parameter | Definition | Configuration |
|---|---|---|
| `GussetAttachmentHeight` | Vertical attachment height on the supported object, measured above the parent floor at the junction. This is the requested height of overlap, not overlap volume or an interference-fit allowance. | Enter an absolute height or an attachment percentage of the object's available structural height above the floor. Use one driving mode; derive the other value. |
| `GussetRunoutDistance` | Distance on the floor from the supported object's exterior at the attachment direction to the zero-height end. It is not measured from the object's center. | Enter a preferred reach for the model, with per-gusset overrides where the neighborhood requires them. |

Define `AvailableSupportHeight` explicitly from a stable datum. In percentage mode, `GussetAttachmentHeight = AttachmentPercent / 100 * AvailableSupportHeight`. The nominal attachment height is the web profile's height at the support; inspect any additional blend envelope separately. Protect the pocket opening, bearing seat and insertion/tool access.

For inclined objects, define the height direction, parent reference surface and runout direction explicitly in a local frame. Do not silently substitute length along an inclined object for vertical attachment height. If the parent is curved, define the runout measurement convention rather than treating it as a flat-floor distance.

## Joint radii — R1 is the master

User-defined default: all four nominal radii are equal, with R1 as the single driving radius. Use linked expressions rather than four independently entered equal numbers:

`R2 = R1`, `R3 = R1`, `R4 = R1`.

| Label | Parameter | Application | Default role |
|---|---|---|---|
| R1 | `BossFloorRadius` | External pocket-carrier/boss junction with the floor, including regions between gussets. | Master, independently editable radius with length units. |
| R2 | `GussetBossRadius` | Both sides of each gusset's structural junction with the boss/pocket carrier. | Derived from R1. |
| R3 | `GussetFloorRadius` | Both sides of each gusset's structural junction with the floor. | Derived from R1. |
| R4 | `GussetExposedEdgeRadius` | Applicable exposed gusset edges. | Derived from R1; preserve functional and mating geometry. |

Changing R1 shall update every linked radius. Choose its preferred value for the model and reconsider its feasibility at each support location. No universal numerical R1 value is adopted. An explicit per-joint override is permitted where surrounding geometry, wall/web thickness, protected interfaces or the zero-height runout prevents the common radius. Record the affected joint, replacement value/profile and reason; do not silently shrink, suppress or independently change a linked fillet.

Where the common radius does not fit, first review the master R1, gusset width, H, L and joint layout. Preserve hardware bearing seats, nut anti-rotation faces, insert installation surfaces, screw channels and keep-outs. At boss/gusset/floor intersections, require one continuous rounded, solid-filled junction; equal nominal radii alone do not establish a valid three-way blend.

The zero-height, horizontal-tangent end condition remains mandatory for a free floor termination. Do not add a constant-radius end cap that creates a step. Construct the smooth runout and validate the final blended shape. If a local variable-radius transition or another exception is needed to reconcile the master radius with that end condition, record it explicitly as an override.

## Preferred model values and neighborhood review

Use preferred model-level H, L and master R1 values as starting design inputs, with documented per-item overrides. No universal height percentage, reach or radius is adopted. Reconsider these parameters for each carrier and each gusset direction using:

- The available structural height and the area requiring bracing.
- Nearby walls, bosses and ribs that can receive a continuous structural connection.
- PCB, component, cable, driver, fastener and assembly/removal envelopes.
- Floor and boss thickness, gusset width, blend space, material, orientation and the intended loads.
- Whether an existing rib can be moved, extended or redirected without losing its panel-reinforcement function.

Where a nearby structural wall/rib is a better termination, connect into it with a rounded solid-filled joint. That connected end is distinct from a free end tapering to zero on the floor. If space prevents the preferred free runout, adjust direction/reach/height together or use a justified structural connection; do not replace the gentle transition with a hidden step. Record the selected values and the reason for overrides.

## Modeling and acceptance

Use the production suite for native editable modeling and engineering verification. Keep the new support in the correct manufactured Body; reference neighboring parts deliberately and verify placement. Establish local floor and object datums, sketch or construct the gusset profile with named H/L inputs, pattern only the intended count/directions, and blend the structural junctions. Use a smooth constructed profile for the zero-height runout rather than rounding a blunt end. Prefer MCP and built-in high-level FreeCAD features. Scripts/macros/FreeCADCmd are exceptions when no suitable route exists or they materially shorten the path; keep editable native features. Their use remains bounded by the current task and environment permissions.

Validate positive H, L and R1, an attachment percentage within the available structural height, a positive integer count and the feasible envelopes of all overridden values. Recompute at nominal and meaningful parameter limits. Check connected valid solids, root/junction continuity, zero-height end geometry, clear screw/insert/nut interfaces and assembly/tool/component envelopes after all dress-up features and cuts. Verify selected geometry with declared CAD tolerances rather than relying on a shaded image.

Review sliced webs, roots and terminating layers during the later print-preparation stage, when slicing is available. State when slicing or physical testing was not performed. Count and radius compliance do not establish stiffness, strength, buckling resistance, insert retention or durability; use the production suite's analysis and validation workflows for performance claims. Installing this reference does not authorize editing an existing device, publishing or releasing manufacturing files.
