# Enclosure ventilation: types, questions and design rules

Current sequencing: finish the FreeCAD design round before Bambu Studio print preparation. Any slicing/printed-path checks below belong to that later stage, not a mandatory intermediate CAD gate. Use the active SKILL.md and current project decisions for execution and scope.


Status: configurable package engineering defaults, not universal standards. The pictures are conceptual parameter-location references, not dimensioned CAD or proof of cooling performance.

## Scope and independent choices

Decide cooling method, opening geometry, passage direction, and protective/service accessories separately. A filter or fan module can combine with round holes, slots or another suitable grille; these are not eight mutually exclusive complete cooling systems. Compatible patterns may have straight passages normal to the wall or tilted through it. Tilt is a shared option, not a ninth opening pattern.

Cooling methods to discuss are a closed housing with deliberate heat paths, passive ventilation, and fan-assisted ventilation. A closed housing is not automatically sealed or thermally adequate. Do not add vents merely because a case has a flat panel, or assume more opening area is always the best overall design.

## Questions to ask the user

Inspect the actual CAD, known use and prior choices first. Ask only unresolved questions, normally no more than three concise questions together. Show the relevant saved pictures with stable V1–V8 numbers and offer two or three feasible candidates with a recommendation. Reuse authorization to recommend/compare rather than repeating the same questions.

1. **How will the case be used and oriented?** Tabletop, wall-mounted or another specified orientation; identify nearby walls, surfaces and stacking. Ask about dust, splash exposure or access protection where relevant. The installed position governs available external airflow space and louver direction.
2. **Which cooling approach should we develop?** Closed case with assessed heat paths, passive openings, or fan-assisted ventilation; alternatively compare and recommend. For a meaningful thermal decision obtain heat dissipation, duty cycle, ambient range and allowable component/enclosure temperatures where available. Unknown inputs permit a clearly labeled concept, not a cooling guarantee.
3. **Which opening style do you prefer?** Shortlist suitable patterns from V1–V6, explain appearance, printable webs, available open area and structural consequences, and allow comparison/recommendation. Never declare honeycomb or another pattern universally strongest or best for airflow.
4. **Which surfaces may contain vents?** Show candidate inlet/outlet zones on the actual model, with effects on appearance, mounting, service, cable paths and component access. Obtain permission before removing material from protected interfaces or changing an established envelope.
5. **Does the design need a removable filter or fan provision?** Explain cleaning/replacement access, added flow resistance, space, power and noise requirements. Preserve a purely passive option when appropriate. A filter/fan is conditional, not automatically required.
6. **Should the passages be perpendicular to the wall or angled?** For an angled choice, establish the lean direction relative to the installed case and ask whether to specify an angle or compare suitable values. Define tilt from the wall normal (zero is perpendicular); optionally display the complementary angle to the surface (90 degrees is perpendicular). Keep this distinct from slot rotation within a panel and louver hood angle. Ask only if this remains an open design choice.

These are future case-specific prompts. Installing these rules does not authorize changing an existing enclosure.

## Eight illustrated examples

Saved 3D concept sheets: [V1–V4: perforated panels](../assets/ventilation/ventilation-v1-v4-parameters.png) and [V5–V8: louvers, baffle, filter and fan](../assets/ventilation/ventilation-v5-v8-parameters.png). Use these stable numbers during discussion together with the [complete parameter definitions](ventilation-parameters.md).

The leaders indicate properties schematically; they are not calibrated measurement spans. Blue arrows in the second sheet only illustrate an intended path, not simulated flow. The louver picture combines a hood and internal slats; a simpler single-hood version may omit slats, while a slatted version must also define slat count, pitch, angle and thickness. Text and eventual CAD geometry govern exact definitions.

| ID | Type | Candidate purpose | Main review |
|---|---|---|---|
| V1 | Round-hole pattern | Simple perforated panel | Hole diameter, layout and remaining webs; sidewall holes may need print-orientation review. |
| V2 | Rounded slots | Elongated openings with smooth ends | Slot span, orientation, retained strips and bridging. |
| V3 | Rounded-square grid | Repeated rectangular/square openings | Two-direction webs, corner radii, pattern coverage and panel stiffness. |
| V4 | Hexagonal/honeycomb perforation | Cellular-looking vent field | Cell size, wall thickness, orientation, edge cells and actual net area. |
| V5 | Hooded louvers | Directional openings under individual overhangs | Minimum throat, hood depth/angle, gravity direction and support access. No assumed ingress rating. |
| V6 | Offset-baffle / covered vent | An indirect air path behind a cover | Continuous entrance-to-exit passage, bottleneck, resistance, cleaning and inspection. |
| V7 | Removable filter module | Filter media in a serviceable plastic carrier | Actual medium, pressure loss, bypass around its edges and replacement travel. |
| V8 | Fan opening with guard provision | A selected fan and air-moving route | Supplier envelope, installed operating flow, guard spacing, rotor/cable clearance and a complementary air path. |

## Placement and integration

For angled passages, read [the shared direction parameters](ventilation-parameters.md#a--angled-through-passages-shared-option). Establish the profile measurement plane, entry anchor, wall normal, tilt and azimuth. Review both surface footprints and the entire passage: a tilted bore shifts its exit, can enlarge its surface footprint and can approach structural features or neighboring channels inside the wall. The normal-passage pictures remain examples of the zero-tilt variant; do not infer angled geometry from them.

- Define gravity and the intended mounted orientation. For passive concepts, review lower entry and higher exit opportunities around the heat sources; do not label every low hole an inlet or promise a flow direction without an adequate driving path. Horizontal orientation and obstructions can change the result.
- Trace an intended path through the heat-producing region. Check that the PCB, ribs, gussets, wire bundles or nearby walls do not block it. Avoid a short circuit from inlet to outlet that bypasses the equipment. For fan assistance, consider both push/pull arrangements based on the actual layout and ambient conditions.
- Keep a structural border around each vent field. Protect screw bosses/channels, their gussets and runouts, clip flexures, locating features, seams, mating lands, PCB supports and user-defined keep-outs. Show any proposed conflicts rather than silently cutting through these features.
- Place bottom openings only with adequate clearance from the supporting surface, including feet and intended installation. Consider blockage by a desk, soft surface or another stacked item. Do not move existing functional parts simply to fit a pattern without reviewing the consequences.
- Verify the strength and printability of remaining webs and unsupported spans. Add an intentional reinforcing frame or adjust the pattern when needed; do not assume infill automatically reinforces thin vent strips.
- Define where air passes through every hood, baffle and filter carrier. A decorative cover over holes is not useful if its edges or attachment close all the passages.
- Include cleaning, filter replacement and assembly/removal envelopes. A detachable carrier uses the existing plastic-interface rules; its working clips must remain flexible and are not ordinary structural gussets.

## Open area and flow are different records

Define the vent-field boundary and calculate `OpenAreaRatio = ThroughOpeningArea / GrossVentFieldArea` in one declared reference face or projection plane: both numerator and denominator must use that same area convention. For a flat panel, report the actual aperture footprints on the selected panel face divided by the gross field area on that face. State which face/plane is used and whether the field area includes the border. For a curved panel, declare whether both values use actual surface area or projection onto a specified plane; do not mix these conventions. Use actual clipped openings near keep-outs and borders, not a full-cell estimate when cells have been removed or cut off.

For an angled cylindrical bore, its elliptical panel-face aperture area and circular area normal to its axis are different quantities. Use the face aperture for the face-based ratio above; record the axis-normal minimum throat area separately for passage assessment. Likewise, louver/baffle bottlenecks are separate from the field's surface open-area ratio. Keep the conventions identical when comparing patterns or tilt angles.

Projected perforation area is not an aerodynamic effective area. Louvers/baffles have a minimum passage section and turns; filters have pressure-loss behavior; the inlet and outlet are serial parts of a path rather than areas to sum as though they were a single opening. Record those separately.

An open-area target may be a design input or comparison metric, not proof that temperatures are acceptable. No universal open-area percentage, opening size, minimum web or inlet/outlet area ratio is adopted as a universal rule.

For fan-assisted work, use the fan's performance information with the system's resistance and intended speed/voltage. Do not substitute free-air maximum flow or maximum static pressure for the installed operating flow. Include grille/filter/duct losses and the relevant loaded-filter condition. A basic heat balance is only a first screen and must state what heat is assigned to ventilation versus other heat paths.

## FreeCAD and verification route

Use the installed production suite for primary modeling and engineering work. Select the manufactured Body and stable local surface/datums. Define a bounded vent zone, keep-outs and positive remaining-section constraints, create the opening/cover prototype, and pattern it with named inputs. Derive repeated mating/profile geometry rather than duplicating independent dimensions. Keep fan and filter supplier geometry as references when applicable.

Recompute and check valid connected solids, successful cuts, remaining wall sections, edge distances and interference after final dress-up features. Exercise opening size, pitch, count, border and orientation limits, especially near interrupted patterns and ribs. Confirm the exported Body tip includes the intended vents.

Use the additive-manufacturing guidance to check horizontal holes, slot bridges, louvers, inaccessible supports and terminating webs in the actual print orientation. Inspect generated slicer paths; record when this was not performed. No numerical printer capability is inferred from the 0.4 mm nozzle alone.

Use the suite's engineering-analysis workflow for thermal/flow claims, selecting a solver only after checking its installed capabilities. Record thermal inputs, boundary assumptions, heat balance, mesh/time convergence where appropriate and comparison with physical temperature tests. Check worst intended orientation, duty and ambient conditions. Maintain separate geometry, printability and cooling verdicts.

Ordinary vents, louvers and printed grilles do not establish an IP rating, filtration performance, touch protection or an EMC/fire claim. If such a requirement exists, define and verify it explicitly rather than inferring it from a concept picture.

## Research basis and limits

- [Protocase ventilation options](https://www.protocase.com/blog/2017/12/8/ventilation-options-for-your-custom-enclosure/) illustrates cutout patterns, perforated panels and louvers. Use its geometry vocabulary; sheet-metal manufacturing limits and tooling dimensions are not FDM rules. Its introductory statement that heat cannot pass through solid metal is incorrect and is not adopted.
- [Protocase louver explanation](https://www.protocase.com/blog/2019/12/03/proto-tech-tip-louvers/) describes a hooded opening protected on three sides. A printed version still needs its own support and passage review; no protection rating transfers.
- [Rittal fan-and-filter white paper](https://www.rittal.com/imf/none/54_1017/) discusses heat load, ambient versus enclosure temperature, installation geometry and fan/filter sizing. Industrial cabinet examples are screening context, not dimensional defaults for small printed cases.
- [Hammond fan selection](https://www.hammfg.com/electrical/products/climate/blowers-selection) discusses low intake/high opposing exhaust opportunities and ambient limits for forced convection. Treat placement as layout-dependent and do not transfer its sizing margins automatically.
- [Noctua inlet-spacing tests](https://www.noctua.at/en/expertise/tech/na-is1-performance-guidelines) show that grille shape, spacing, fan model and resistance affect flow and noise. Its round/hex/slot results do not establish a universal winning pattern.
- [Noctua grille offset results](https://www.noctua.at/en/expertise/tech/na-fg1-improvements-from-offset-mounting) support reviewing fan-to-obstruction spacing; vendor-specific spacings and gains are not universal requirements.

The V1–V8 classification and user prompts are our proposed engineering workflow, not a published standard or tested parametric library. The offset-baffle example is a design candidate requiring its own path/pressure/cleaning verification.

For the independent passage-direction option, show the [angled vent parameter illustration](../assets/ventilation/angled-vent-passages-parameters.png): a 3D patterned panel cutaway, a section explaining tilt/surface angle and exit displacement, and a plan view explaining azimuth. This is a conceptual reference, not a manufactured CAD model or evidence of cooling performance.
