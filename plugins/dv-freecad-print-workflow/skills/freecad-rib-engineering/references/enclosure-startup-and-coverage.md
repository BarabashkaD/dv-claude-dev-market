# Enclosure startup from a device model: coverage modes

Current sequencing: finish the FreeCAD design round before Bambu Studio print preparation. Any slicing/printed-path checks below belong to that later stage, not a mandatory intermediate CAD gate. Use the active SKILL.md and current project decisions for execution and scope.


Status: optional enclosure-startup discussion draft, not a validated sizing algorithm.

The installed [local engineering entrypoint](../SKILL.md) now points here for discussion context; that pointer does not adopt this entire proposal as a detailed sizing standard. When recording or comparing choices, write **coverage C1/C2/C3**. The separate rib reference uses **rib-connection C1/C2/C3** for integral/contact/fastened load paths; those are different decisions and their labels are not interchangeable.

## Starting point and model authority

An enclosure may start from an existing 3D device assembly, including an assembled PCB exported from KiCad, a supplier STEP assembly, or another supplied CAD model. Keep the device as a separate reference assembly rather than fusing it into the manufactured case. Record source/revision/variant, units and placement transform, and identify missing or simplified clearance-critical geometry. A visually populated export is not automatically a complete representation of connector mating travel, button movement, cable bend space or tool access. Add these as identified reference envelopes where required; do not invent missing dimensions as confirmed geometry.

Choose the device coordinate frame and mounted orientation before calculating bounds. “Minimum bounding box” normally means the smallest permitted box in that declared frame around the selected protected geometry with required clearances and construction allowances. Do not silently rotate the device to obtain a smaller volume. If rotation/orientation optimization is wanted, define the permitted orientations and the sizing objective, then compare them explicitly.

Establish sizing mode separately: inside-driven, externally constrained or mixed. Coverage determines what must be inside; it does not override external limits, manufacturing wall sections or an already established component arrangement.

## Coverage choice to present to the user

Ask: **How should the enclosure cover the device: fully surround it, fit closely around the protected body with selected parts exposed, or combine those approaches in different regions?** Offer the three modes below, identify their consequences on the actual device and reuse prior selections.

| ID | Mode | Definition |
|---|---|---|
| C1 | Full bounding enclosure | Enclose the entire selected device assembly, including its connectors and protruding parts, with specified clearances. Connector bodies, button caps and other projections remain within the selected enclosure envelope. Any later cable/access opening must be explicitly planned and does not silently change the initial coverage decision. |
| C2 | Compact bounding enclosure | Size a close-fitting case around the geometry that must remain protected. Selected button actuators/caps, socket mouths, connector noses or other functional regions may extend outside. Those exposure regions may be excluded from the size-driving bounds; they still exist and remain collision/access references. Their corresponding cutouts are planned now and created in the next modeling stage. |
| C3 | Hybrid overlapping envelopes | Assign full or compact coverage to different device regions, define their separate local envelopes, and combine overlapping construction volumes into a continuous intended enclosure envelope. A raised fully enclosing region and a compact connector region may coexist; the shape need not have uniform height. |

Coverage is not lid position, case split or retention. Resolve those separately once the envelope is understood. Full coverage does not by itself establish sealing, cooling or an ingress rating.

## Exposure and contact classification

For each relevant component or functional subregion, record one or more roles with explicit geometry:

- **Enclosed/protected region:** must remain inside with the chosen clearance.
- **Exposed/pass-through region:** may project outside and defines a candidate cutout and access/movement envelope.
- **Intentional contact interface:** a named face or area permitted to contact or support the case, with its reason and fit/load basis. Contact permission does not extend to every surface of the component.
- **Reference-only geometry:** does not drive enclosure dimensions, but remains available for review. Do not use this label to ignore a real conflict with the finished case.

A single connector can have an enclosed rear body and an exposed mating nose. A button can have a protected mechanism and an exposed moving cap. Split these functional regions when necessary rather than simply removing the whole component from bounding calculations. “Disregarded for sizing” never means deleting the actual component or accepting interference with it.

The initial construction envelope may touch or cross selected pass-through geometry before cutouts are made. Mark those intersections as expected unfinished features and link them to specific cutout records. The finished housing must clear those parts throughout their required motion unless contact is deliberate and specified. Do not silently interpret “tiny/compact” as zero clearance on all parts. Contact on solder joints, leads, fragile components or moving features is not implicitly authorized.

## Cutout plan and subsequent modeling stage

Create a register linked to component IDs or KiCad reference designators, containing exposure role, owning case part/zone, source geometry, opening plane/axis, opening profile, position, clearance, through-wall extent and required functional travel. A button opening must allow its intended stroke; a connector opening must accommodate the selected plug approach/latch/release and any required cable bend or strain relief. Decide whether access to a bare socket or the connected plug is required.

After the basic envelope is reviewed, form the corresponding openings using controlled cut tools derived from source datums/geometry plus declared clearances. An exact solid subtraction of every device component is not the default: some openings need a functional rectangular/circular profile or a movement/access envelope larger than the component's static outline. Verify each cut reaches through the intended wall, preserves required bearing/retaining surfaces and does not unnecessarily cut neighboring walls, mating lands, supports or another manufactured part. Regenerate the cutout locations when the source component placement changes.

## Hybrid overlaps and shell construction

Associate each zone with its component group, coordinate frame, full/compact mode and margins. Overlapping envelope blocks used for one continuous shell should have a real positive-volume connection rather than only tangent-face, edge or point contact. Review the overlap/transition extent and final wall continuity. Resolve interior cavity joins deliberately so that construction-block boundaries do not leave accidental partitions or trapped inaccessible spaces. Retain real compartments where required.

Use rounded solid-filled structural transitions where zones/supports join, while preserving the intended voids, wall thickness, openings and assembly path. Check for thin slivers, isolated solids and abrupt local bottlenecks. Construction-volume union does not authorize fusing the device or separately manufactured case pieces; split the case into the selected manufactured Bodies with intentional mating interfaces.

## Initial parameter and decision record

| Group | Record |
|---|---|
| Source | Device model/revision/variant, units, missing geometry and placement transform |
| Frame | Device origin/axes, installed orientation and any allowed orientation alternatives |
| Sizing | Inside-driven, external limits or mixed; independent versus derived dimensions |
| Coverage | C1/C2/C3 globally, with per-region assignments for C3 |
| Membership | Size-driving protected regions, exposure regions and declared contact interfaces |
| Margins | Per-side and top/bottom clearances, contact exceptions and service/motion envelopes |
| Shell | Side-wall, floor and lid thickness; outline/corner radii, with related values derived where appropriate |
| Zones | Zone bounds/placement, overlap and transition geometry, component membership and intended cavity connections |
| Openings | Component-linked cutout profile/location/direction/clearance/travel and planned modeling status |
| Output | Derived internal/external extents, exposure/intersection review, provisional assumptions and unresolved choices |

Use one source of truth for each dimension; do not independently fix inner size, outer size and intervening thickness in conflicting ways. Set clearances and wall sizes for the specific material/process and neighborhood. No universal dimensions or global guarantee of an optimal/minimum volume are adopted.

## First reviewable result

Present the reference device, its source confidence, the selected size-driving regions, the C1/C2/C3 envelope, exposed regions and planned cutout markers, plus useful sections and overall dimensions. Resolve important ambiguities with the user before treating a compact boundary crossing as intentional. Then proceed to shell/split details, cutouts and mounting structures through the production suite. The staged envelope is a concept; final geometry, printed fit and functional performance require their own checks.

## Relationship to current skills

This extends the existing production brief, parameter provenance and stable-reference rules with an enclosure-specific coverage decision. The installed ECAD sourcing reference in the installed suite (resolve its current path at runtime) already requires exact board identity, reference geometry and connector/cable envelopes. The installed parametric-modeling skill in the installed suite governs actual editable model construction. This draft introduces no project changes or upstream modifications.
