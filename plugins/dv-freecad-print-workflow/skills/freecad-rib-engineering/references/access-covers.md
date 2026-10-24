# Simple access covers for components and cable connections

Current sequencing: finish the FreeCAD design round before Bambu Studio print preparation. Any slicing/printed-path checks below belong to that later stage, not a mandatory intermediate CAD gate. Use the active SKILL.md and current project decisions for execution and scope.


Configurable package guidance. Use with the unchanged FreeCAD production suite and the existing [plastic-interface rules](enclosure-interfaces.md). This guidance records options and visual discussion preferences, not a validated component library or authorization to alter unrelated projects.

## Preferred simple removable-cover example

The default discussion example is a small flat cover inspired by an OKW battery-compartment lid. **Show [the saved top and underside draft](../assets/access-covers/flat-snap-cover-top-and-underside-draft.png) when discussing this arrangement or its properties.** Resolve the path from this installed skill and display it inline using an absolute local path; if that is unavailable, open the image and give its link. Do not merely mention a filename when the view is needed to explain the mechanism.

The preferred example is a thin rounded rectangular plate, a shallow locating rim, two locating tabs at one end and a small integral releasable snap tongue at the other. It favors simple compact geometry without large external clasps or bulky added mechanisms. It is a discussion reference rather than a universal prescription. The hidden catch in the illustration is proposed geometry; it is not a verified reproduction of the manufacturer's mechanism. Define the actual spring root, free length, catch engagement and release clearance before treating it as a working design. A rigid nub with no credible flex path is insufficient.

The package favors simple, compact cover examples by default; sliding, L-profile or bulkier concepts remain available when project requirements justify them. A cover can have an L profile if the opening genuinely crosses an edge, but an L-shaped cover and an L-shaped spring are different choices. Do not assume that the default flat-cover example implies a hinge or that a regular lid must be hinged.

## User discussion and selection

Inspect the existing part, access purpose, component/connector model and prior decisions first. Ask only unresolved questions, usually no more than three together. Offer two or three feasible options with a reasoned recommendation, and reuse permission to recommend or compare.

1. **What needs access, and should the cover come off or stay attached?** Component replacement, adjustment, programming or cable mating can require different opening sizes and access directions. Reuse an established attached/removable choice.
2. **Which simple cover arrangement or retained connection suits this case?** For removable covers, start with the saved preferred example where suitable. For attached covers, use the [active H1/H2/H3/H7/H8 choices and illustrations](attached-cover-connections.md). Do not prescribe one design for every location.
3. **What must opening permit?** Resolve whether a cable stays plugged in, whether fingers or a tool release the catch, required clear access, the allowed opening/swing direction, and whether the lid must remain open by itself. Ask about an external-envelope restriction or concealed connection when it matters; do not assume the earlier exposed pivots are mandatory.

Cover outline/shape, locating/seating interface, captive connection, closed-position retention, and hold-open/stop behavior are independent functions. A hinge can replace the earlier locating tabs; do not simply add it to unchanged removable-lid geometry. A spring-retractable hinge pin engages an attachment and does not automatically spring the lid open or close it.

## Parameters and integration

Derive opening position/outline from the actual component and service envelope. Expose the relevant cover length/width, corner radius, thickness, seating/overlap dimensions, rim depth, flush/recess offset, lateral and axial clearances, locating-tab size/engagement/positions, and finger/tool access. Keep the fit conventions and dimension dependencies from [the interface parameter reference](enclosure-interface-parameters.md); use its integral-clip controls for the snap tongue instead of maintaining a competing set of defaults.

Use stable datums and named parameters; derive mating geometry from the chosen fit rather than independently constraining both parts and clearance. Manufactured separate parts remain separate Bodies; a one-piece flexible region is modeled according to its actual manufactured construction. Preserve PCB/component envelopes, connector mating/unmating travel, cable bend and service loops, and check pinch/abrasion throughout opening and closing. Do not use an electrical cable as the retaining tether.

Keep supporting borders and ledges intentional. Apply rounded structural roots where appropriate without consuming mating lands, spring free motion or hinge running clearance. Structural screw-gusset/R1 defaults do not automatically govern flexible clips, flexures or bearings. Required material, opening frequency/cycle target, temperature and retention requirements govern detailed sizing; no universal numerical dimensions or lifetime are adopted.

Use production-suite parametric modeling, assembly, additive-manufacturing and analysis workflows for the actual design. Check final solids, fit, engagement, insertion/removal, complete motion and relevant parameter limits. Inspect actual slicer paths and representative clip/fit trials before claiming reliable printing or repeated use. Report geometric, print and life/retention evidence separately. Snap retention does not automatically imply sealing, deliberate hold-open behavior or a load rating.

## Primary reference

[OKW Soft-Case](https://www.okwenclosures.com/en/Plastic-enclosures/Soft-Case.htm) documents a commercial clip-on battery-compartment lid. Its molded design, material and product ratings do not qualify the proposed printed cover. Other mechanism references are recorded with [the attached-cover options](attached-cover-connections.md).
