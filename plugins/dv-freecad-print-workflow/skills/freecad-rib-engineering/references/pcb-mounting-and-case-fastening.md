# PCB mounting and enclosure fastening

Current sequencing: finish the FreeCAD design round before Bambu Studio print preparation. Any slicing/printed-path checks below belong to that later stage, not a mandatory intermediate CAD gate. Use the active SKILL.md and current project decisions for execution and scope.


Configurable package guidance. Applies to new designs and authorized revisions; it does not authorize changing an existing PCB or enclosure. Use the production suite for engineering and verification. These selection and geometry rules are not physical validation.

Before positioning PCB supports, screw holders or inserts, distinguish **PCB retention** from **enclosure closure**. Present these two architectures when the choice remains unresolved. Reuse established user decisions.

## PCB-F1 — Independent fastening

Secure the PCB to one enclosure part using dedicated supports and fasteners aligned with suitable PCB mounting holes. Use separate fasteners to join the enclosure parts.

- Select enclosure screw locations independently, considering the seam, available structure, components, connectors and tool access.
- Prefer this arrangement when the PCB must remain securely attached during enclosure opening, or when straightforward assembly and servicing are priorities.
- Explain that additional screws and holders may consume space, but a larger enclosure is not inevitable.

## PCB-F2 — Shared fastening

Use common fasteners through suitable PCB mounting holes to join the enclosure parts and retain the PCB.

- Evaluate this arrangement when reducing fastener count or enclosure size is a priority.
- Derive support locations from the verified PCB hole pattern; check whether those locations also provide adequate enclosure closure.
- Define the complete support and clamping stack before detailing screw holders.
- Establish assembly order, screw entry direction and PCB retention during opening. Face-down assembly is an option, not a requirement.
- Explain that shared fastening may reduce size, but does not automatically improve positioning accuracy or simplify assembly.

## Selection discussion

Show a quick conceptual comparison before detailed modeling, following the skill's first-draft rule. Use a section view when needed to explain the support stack. Do not present a conceptual image as verified CAD geometry.

Ask only unresolved questions, normally no more than three together:

1. **Which is the priority: easier assembly and servicing, or minimum enclosure size and screw count?** Offer independent fastening, shared fastening, or a comparison before choosing.
2. **Must the PCB remain securely attached to one case part when the enclosure opens?** Identify the preferred part if relevant.
3. **What assembly restrictions apply?** Establish permitted screwdriver access, whether inversion is acceptable, and whether cables or components constrain handling.

Ask follow-up questions only when they affect the design: opening frequency, connector/button forces, hardware preferences, or permission to modify PCB holes. Obtain dimensions and hole information from available CAD before asking the user. Reuse delegated design authority; do not turn an established choice into a repeated approval step.

Recommend independent fastening as the initial candidate for serviceability. Evaluate shared fastening for compactness when its support stack and assembly sequence are practical. Neither architecture is compulsory.

## Support and clamping requirements

For either architecture:

- Verify board revision, thickness, mounting-hole coordinates and diameters, copper/component keep-outs, and clearance above and below each mounting point.
- Do not assume an existing hole is suitable for the selected hardware. Do not alter the PCB without authorization.
- Define locating surfaces separately from fasteners; clearance screws alone do not establish accurate positioning.
- Preserve component, connector, cable, screw-head, insert-installation and screwdriver envelopes.
- Apply the existing [screw-feature support rules](screw-feature-supports.md) to plastic screw-load carriers, including gussets, root fillets and rounded solid-filled joints. Keep separate manufactured parts separate; never merge a carrier or gusset into the reference PCB.

For shared fastening, explicitly choose and document the load path:

- **Direct PCB clamping:** support the board locally at each clamped mounting area and control opposing contact heights to avoid bending it.
- **Load-bypassing shoulder or spacer:** carry the main enclosure clamping force through the shoulder/spacer and define how the PCB is separately captured. Prevent unintended looseness or excessive compression.

Account for board, printed-part and hardware tolerances. Ensure enclosure closure and PCB retention can occur together without board bowing, unintended gaps, screw bottoming or hardware contact with electronics. Define tightening requirements for the actual joint and hardware; do not invent a universal torque from screw diameter alone.

## Parameters and verification

Expose the selected architecture, mounting case part, hole map, PCB seating height, support/contact dimensions, fastener specification, thread engagement, insert location, locating clearances and—where applicable—shoulder height and PCB capture clearance. Dimensions remain project-specific.

Check assembly and removal paths, retention when opened, remaining material, interference, support continuity and screw engagement. Document the assembly sequence and unresolved assumptions.

Treat valid CAD geometry as geometric evidence only. Physical fit, tightening behavior and durability require appropriate prototype checks. State which checks were performed and which remain pending.
