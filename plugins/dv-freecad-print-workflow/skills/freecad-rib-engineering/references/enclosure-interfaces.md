# Plastic-to-plastic enclosure interfaces

Current sequencing: finish the FreeCAD design round before Bambu Studio print preparation. Any slicing/printed-path checks below belong to that later stage, not a mandatory intermediate CAD gate. Use the active SKILL.md and current project decisions for execution and scope.


Configurable package guidance. Applies to enclosure split decisions, plastic mating geometry and integral clips. Screws, metal inserts/nuts, separate latches/locks and adhesive joining remain separate topics. Existing engineering projects and upstream suite files are unchanged. No completed CAD/print qualification of this interface family is claimed.

For user discussion, show the saved [nine-example image](../assets/enclosure-interfaces/overview-01-09.png) and refer to its panel numbers. The [parameter review for all nine examples](enclosure-interface-parameters.md) defines editable dimensions, dependencies and checks. The image illustrates concepts; it is not a dimensioned or validated CAD model.

When explaining property locations, use the selected annotated sheets for [1–3](../assets/enclosure-interfaces/parameters-01-03.png), [4–6](../assets/enclosure-interfaces/parameters-04-06.png) and [7–9](../assets/enclosure-interfaces/parameters-07-09.png). They are schematic parameter callouts, with exact definitions maintained in the parameter reference.

## Case split decisions and visual discussion

Before detailed enclosure modeling, ask the user to select unresolved split decisions or authorize comparison/recommendation. Inspect available CAD and reuse existing preferences first; do not restart an already chosen two-piece or fastening concept.

- **How should the case be divided?** Offer feasible alternatives such as deep base plus shallow lid, clamshell halves, or main shell with removable panels. Explain the number of manufactured parts, opening direction, component insertion and printing tradeoffs.
- **Which proposed seam location do you prefer?** Show feasible split planes/heights on the actual design and their effects on ports, components, service access and printing. Do not impose a 50/50 split or a seam through the PCB by default.
- Then resolve lid position, mating geometry and integral clips using the questions below. Ask no more than three concise questions together and offer a reasoned recommendation with the relevant options. Respect authorization to choose rather than repeatedly asking.

**Show pictures during the discussion.** At an initial interface choice or when terminology is ambiguous, display the supplied overview to the user and identify the applicable numbered examples. When discussing a selected type's dimensions, display its relevant parameter-callout sheet. Preserve example numbering 1–9 and state that lid position, mating features and clip choice can be combined. Reuse the supplied images instead of regenerating equivalent pictures or merely linking a filename without showing the relevant view. Resolve image paths from this installed skill and render them with absolute local paths; if inline display is unavailable, open the selected image and provide its file link.

The selected pictures are conceptual aids. Parameter definitions and later CAD geometry govern precise measurements; do not infer exact arrow endpoints, fit values, strength or print qualification from a generated illustration. Use a project-specific section/view if the stock example would misrepresent the actual geometry. Show only relevant sheets once a choice is established.

## Three independent design choices

### 1. Where the lid sits relative to the side walls

| ID | Position | Definition | Review |
|---|---|---|---|
| P1 | Over the sides / outside cap | A lid skirt extends down around the exterior of the case walls. | Added outer envelope, skirt fit, lower edge clearance, removal travel and wall taper/warp. |
| P2 | On the sides / seated on the rim | The lid bears on the top rim of the walls. Local lips or locators can be added without changing this primary seating arrangement. | Rim flatness, load-bearing width, lateral location and seam appearance. |
| P3 | Inside the sides / inset | The lid fits between the walls and seats on an internal ledge, shoulder or tabs. | Remaining wall section, ledge strength, insertion/removal access, recessed or flush top position and internal component clearance. |

These positions do not themselves specify how the lid is retained. Flushness is a separate dimension; an inset lid may be flush or recessed.

### 2. How the plastic edges locate and overlap

| ID | Interface | Definition | Review |
|---|---|---|---|
| J1 | L + L overlapping steps | Two complementary L-shaped edge sections overlap in a stepped seam. This is the local descriptive meaning of L + L, not an asserted universal joint designation. | Complementary orientation, finite wall sections, seating land, overlap, lateral/axial clearances and assembly direction. |
| J2 | Tongue-and-groove | A projecting plastic tongue enters a receiving groove bounded on both sides. | Tongue/groove thickness, depth and clearance; corner fit, cleaning and printable orientation. |
| J3 | Locating pins and sockets | Discrete integral pins enter corresponding holes or sockets. | Pin strength and lead-in, socket depth, location and positional tolerances, and relief of redundant constraints. Pins may be asymmetric to prevent reversed assembly. |
| J4 | Locating lugs and pockets | Short, wider tabs or lugs enter matching recesses. | Enough bearing section, insertion clearance, tab roots and interference with components. Useful where small round pins would be delicate. |
| J5 | Sliding plastic rails / dovetail | Complementary rails guide one part into the other along a defined sliding path. | Full insertion travel, printable undercuts, fit/warp, end stop and the intended resistance to sliding back out. Do not imply it automatically retains every direction. |

An edge-locating geometry may resist some sideways motion while still permitting separation in the opening direction. Record constrained and free directions. Do not require a press fit for locating pins by default or assume zero nominal clearance. No universal fit value is selected.

### 3. Whether integral plastic clips are wanted

Offer three states: no integral clip in this interface study; releasable integral clips; or one-way integral clips only when expressly desired. This reference covers integral clips; separate latch/lock mechanisms are outside its scope.

An integral clip is a flexible molded/printed beam or hook belonging to one part and engaging a receiving ledge/window in the other. Record its flex direction, engagement, required displacement, release access and expected reopening cycles. Keep rigid alignment geometry distinct from the flexible clip region where useful. Do not gusset a working clip so that it can no longer flex. Review layer orientation, material strain, creep and repeated use; the existing structural screw-gusset defaults are not a clip design prescription.

## User questions for each case

Inspect the model and reuse existing decisions. Present feasible options with small sections/views and a recommendation, rather than asking the user to infer geometry from names alone.

1. **Where should the lid sit: over the outside walls, on the wall rim, or inset between the walls?** Offer only feasible choices and show their envelope/clearance consequences.
2. **How should the plastic parts locate: L + L steps, tongue-and-groove, pins/sockets, lugs/pockets, or sliding rails?** Shortlist two or three suitable options for the actual geometry, or compare and recommend if delegated.
3. **Should this interface include integral clips, and should they be releasable?** Separate flexible retention from alignment. If no clip is chosen, leave other retention outside this discussion rather than inventing screw or lock hardware.

Choose position first, then compatible interface details. These choices can be combined: for example, an inset lid with an internal ledge, locating lugs and releasable clips. Do not imply every position accepts every edge profile without checking the wall section and assembly path.

## Editable dimensions and checks

Use model-level preferred dimensions with location-specific review: lid height/flush offset; skirt depth and clearance for outside caps; seating width and ledge depth; step/lip engagement; tongue/groove dimensions; pin/lug size, length, position and lead-in; lateral versus axial clearance; and clip profile/deflection dimensions when chosen. Keep independently controlled fit directions separate. Check root blends without consuming functional mating faces or a clip's required flexibility.

Use separate manufactured Bodies, stable datum/interface references, actual insertion/removal paths, component and cable envelopes, minimum sections, final shape validity and parameter limits. Check slicer paths and representative mating coupons before assuming the preferred clearances fit. A guided seam is not automatically a seal or a verified load-bearing/retained assembly.

## Evidence and scope

This classification is a configurable package design vocabulary for plastic interfaces, not a published ranking or dimensional standard.

- [Prusa connector documentation](https://help.prusa3d.com/article/cut-tool_1779): plug, separate dowel, snap and dovetail examples. This environment should retain authoritative editable geometry in FreeCAD.
- [Formlabs enclosure guide](https://formlabs-media.formlabs.com/rs/060-UIG-504/images/WP-EN-How-to-Design-and-3D-Print-Snap-Fit-Enclosures.pdf): separate enclosure halves, cantilever snaps and locating lugs; its example dimensions are not FDM defaults.
- [Formlabs snap-fit guidance](https://formlabs.com/blog/designing-3d-printed-snap-fit-enclosures/): material, strain and print-direction considerations for flexible clips.
- [Protolabs self-mating guidance](https://www.protolabs.com/resources/design-tips/creating-self-mating-parts-in-injection-molding-design/): complementary pins/sockets, tongue/groove and clips; injection-molding process details do not become FDM requirements.
