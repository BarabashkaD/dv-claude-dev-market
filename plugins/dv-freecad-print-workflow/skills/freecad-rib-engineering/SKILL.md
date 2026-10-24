---
name: freecad-rib-engineering
description: Apply configurable FreeCAD FDM enclosure defaults for splits, plastic interfaces, removable and attached access covers, integral clips, ventilation, PCB mounting and case fastening, ribs, gussets and rounded screw supports. Complements the installed FreeCAD production suite with illustrated selection and editable local design rules.
---

# FreeCAD enclosure and rib engineering

This package supplies configurable enclosure-interface, ventilation, rib-selection and structural-joint defaults. Current project requirements and explicit user choices override these defaults. Use [cad-print-workflow](../cad-print-workflow/SKILL.md) for stage transitions and shared decisions. Use the installed FreeCAD production suite for detailed engineering methods, without changing its upstream files. These local preferences are not general manufacturing standards. Load only relevant references; preserve project-specific decisions over illustrative examples.

Complete the FreeCAD design round before Bambu Studio preparation. Print-aware design is required, but repeated intermediate slicing is not. Slicing requirements in older references apply only after the CAD-ready gate. Existing case choices are not automatically imposed on unrelated products.

## Always begin with a quick visual draft, then user direction

When starting a case or exploring a new enclosure design direction, always show a fast first visual overview of basic concepts before extensive research or detailed modeling. This ordering precedes the feature-specific questionnaires below. Inspect only the available model, established constraints and relevant saved examples needed to make that first overview meaningful. Use simple envelope/block models, rough 3D views or existing suitable concept pictures; when source geometry is unavailable, label the overview generic and its dimensions provisional. The first draft communicates direction, not a finished or validated enclosure.

Show a small useful comparison, normally two or three simple alternatives. Where coverage is the unresolved choice, illustrate a full enclosure, a compact enclosure with selected protrusions/exposed functions, or a hybrid envelope. Keep the alternatives simple and case-relevant rather than researching or rendering every possible feature. Reuse the user's supplied examples and accepted pictures where they fit.

After showing the overview, ask for the user's preferred option or direction and any useful constraints or reference examples that could narrow the search: device parts that must remain exposed, external size/shape limits, intended placement, access needs or an existing product they want to follow. Ask only unresolved questions, normally no more than three together. Incorporate the response before dependent detailed research, refinement or engineering work; continue independent preparation where useful. Research the remaining uncertainties along the chosen direction instead of broad exploration first. If the user explicitly requests research first, follow that instruction.

Reuse earlier choices and delegated design authority. Still provide the early visual overview, but do not repeat answered questions or turn an already authorized, fully specified design into a new mandatory approval step. Apply this rule to new case/concept exploration; routine edits to an established design do not require restarting concept selection. Record the chosen direction and newly supplied constraints for later stages.

The [enclosure-startup and coverage research draft](references/enclosure-startup-and-coverage.md) records proposed full, compact and hybrid envelope choices for a supplied device model. It remains a discussion draft, not an adopted detailed sizing standard or validated algorithm. Use it to clarify unresolved user direction without silently promoting all proposed rules. Qualify its labels as **coverage C1/C2/C3** to distinguish them from **rib-connection C1/C2/C3** in the rib reference.

## Enclosure split and plastic mating interfaces

For case splitting, lid placement, plastic alignment geometry or integral clips, read [references/enclosure-interfaces.md](references/enclosure-interfaces.md). Ask the unresolved split/part-count, seam-location and lid-position questions with suitable options and a recommendation; reuse established choices or authorization to recommend.

**Show the supplied numbered pictures during the relevant user discussion:** the overview for choosing concepts and the relevant annotated sheet for explaining properties. The reference links all four images stored in this skill. Use the images to clarify terminology, keep numbers 1–9 stable, and explain that lid placement, mating geometry and clip behavior are independent choices that may combine. Do not substitute generated pictures for exact geometry or numerical measurements.

For selected geometry, read [references/enclosure-interface-parameters.md](references/enclosure-interface-parameters.md). Preserve separate lateral/axial clearances, derive mating dimensions consistently, use preferred model values with local review, and verify insertion/removal paths and remaining sections. Keep screw fastening and separate locks/latches outside this plastic-interface conversation. Integral flexible clips remain included; do not apply structural screw-gusset rules in a way that prevents their required motion.

## Access covers and retained connections

For component/cable access covers, read [references/access-covers.md](references/access-covers.md). Use the packaged thin flat snap-fit cover as the preferred removable-cover discussion example, not a compulsory geometry for every project. Distinguish access-cover shape, captive connection, closed-position catch and hold-open function.

For covers that stay attached, read [references/attached-cover-connections.md](references/attached-cover-connections.md). The active choices are H1 pin hinge, H2 snap-in cylindrical pivot, H3 living hinge, H7 integral ball and retaining socket, and H8 concealed spring-retractable pivot candidate. Keep identifiers stable. H4–H6 are outside the default shortlist, not prohibited; include them when project requirements justify them. No connection is preselected for a project.

**During a relevant discussion or when explanation is needed, show the saved 3D draft views linked in the references.** Show the preferred removable cover, H1–H3 sheet or H7 view as applicable. H8 has no saved picture yet: generate a clearly labeled case-relevant draft if requested or needed, distinguishing spring-arm and separate-spring versions. Do not depict an exposed fixed pivot as a concealed retractable one. Use exact CAD sections where a concept picture would mislead, preserve user simplicity preferences and keep sizes project-specific. No illustration is validated CAD or proof of retention/life.

## Enclosure ventilation and angled passages

For enclosure ventilation, read [references/ventilation-design.md](references/ventilation-design.md) and the relevant sections of [references/ventilation-parameters.md](references/ventilation-parameters.md). Ask only unresolved case-specific questions about installed orientation/environment, cooling approach, opening style, permitted surfaces, filter/fan needs and normal versus angled passages. Usually present no more than three questions together, with two or three suitable candidates and a recommendation; reuse established choices.

**Show the saved illustrated sheets during ventilation discussions:** [V1–V4 patterns](assets/ventilation/ventilation-v1-v4-parameters.png), [V5–V8 protected/service/fan options](assets/ventilation/ventilation-v5-v8-parameters.png), and [angled-passage 3D cutaway and angle definitions](assets/ventilation/angled-vent-passages-parameters.png) when applicable. Keep V1–V8 numbering stable. Cooling approach, pattern, passage direction and filter/fan additions are independent choices that can combine. These are conceptual property references; exact CAD and written definitions govern dimensions.

Define editable pattern dimensions, borders, keep-outs, remaining webs and passage clearances for the actual neighborhood. For tilted passages, define tilt from the inward normal (zero is perpendicular), lean azimuth, profile measurement plane and entry anchor. Derive the complementary surface angle, exit displacement and passage length where applicable; check entry/exit footprints and the full depth for interference and thin sections. Slot rotation, hood angle and passage tilt are different parameters.

Protect the established rib/gusset, clip, mating, hardware and component envelopes. Apply the package rounded structural-root defaults where new load-bearing supports are introduced, preserving intended openings and flexible clip motion. Dimensions and angular limits remain case-specific. Use the production suite for editable CAD, additive-manufacturing review and supported thermal/flow analysis; report geometry, slicing and cooling evidence separately. The packaged examples have not completed representative CAD, print or thermal trials and do not establish a cooling or protection rating.

## Select ribs for the specific case

Read [references/rib-design.md](references/rib-design.md) for rib types, native modeling and connections.

Inspect the intended CAD part, supports, existing dimensions and keep-outs first. Classify the design by layout, section/height profile and connection intent. When layout remains a meaningful open choice, offer two or three suitable candidates with a recommendation and ask the user to choose or authorize a comparison. Reuse an existing selection or authorization to recommend; do not ask repeatedly.

Ask only missing information that affects this design: the reinforcement goal and load location, permitted side/height, and whether connections are integral or involve separate parts. Obtain material, force, environment and life information when needed for performance claims. Unknown loading permits a clearly labeled concept, not an invented strength rating.

## Apply configurable joint defaults

- Add root fillets at load-bearing rib-to-panel attachments. Choose radii for the actual geometry, material, orientation and clearance; resolve or report a conflict instead of silently omitting a required blend.
- Where ribs transfer load into surrounding walls, bosses or other ribs, require continuous solid-filled connections with rounded transitions, without acute re-entrant creases, unsupported thin wedges or narrow trapped gaps.
- Preserve screw seats, bores, nut/insert pockets, locating faces, PCB/component and cable envelopes, tool access and assembly clearances.
- Keep independently manufactured parts in separate Bodies. A reference binder or visual contact is not a structural joint. Define actual clearance, contact, preload, fasteners or bonding when applicable.

## PCB mounting and enclosure fastening

Before positioning PCB supports, screw holders or inserts, read [references/pcb-mounting-and-case-fastening.md](references/pcb-mounting-and-case-fastening.md). Distinguish PCB-F1 independent PCB retention and enclosure closure from PCB-F2 shared fasteners through PCB mounting holes. Show a quick comparison and ask only unresolved priority, retention-on-opening and assembly-access questions; reuse established choices and delegated authority.

Inspect the board model before requesting dimensions. Define locating surfaces, support heights, clamping load path and assembly sequence. For shared fasteners, explicitly define direct PCB clamping or a load-bypassing shoulder/spacer with separate board capture. Preserve component/copper and tool clearances, account for tolerances and prevent board bending or unintended movement. Apply the screw-support rules below to the plastic carriers. No architecture or numerical dimensions are compulsory; PCB changes require authorization.

## Screw-feature supports

Read [references/screw-feature-supports.md](references/screw-feature-supports.md) for any plastic feature carrying screw loads. Apply the package screw-support defaults, not universal mechanical standards: triangular gusset support at any feature angle; at least three distributed gussets for an isolated feature; location-specific connection to suitable neighboring structure, preferably a high supporting side wall; and reuse or repositioning of compatible ribs where useful.

Expose attachment height H (absolute or percentage mode) and floor runout L, plus configurable count, orientation, thickness and reach. Reconsider preferred model values at each location. Free floor ends must reach zero added height with a horizontal tangent and no step. R1 is the master joint radius; link R2, R3 and R4 to R1 by default. Record necessary local overrides and preserve all functional hardware surfaces and clearances. These defaults belong to screw-feature support design; they are not universal dimensions or a strength qualification.

## Model and verify through the suite

Before introducing a new construction method or responding to a version-related failure, follow [current documentation and capability checks](../cad-print-workflow/references/current-documentation.md). Verify native high-level FreeCAD options and official recommended usage for the installed version; do not treat an MCP gap as a missing application feature. Routine repetition of an already verified method does not require renewed research.

Use `freecad-production-suite:freecad-parametric-modeling` for stable datums, editable parameters, additive features, patterns and robust regeneration. Keep one intended contiguous manufactured solid per Body. MCP is the strongly preferred route, not an absolute prohibition on scripts. Follow [freecad-mcp-operations](../freecad-mcp-operations/SKILL.md) for bounded exceptions and live-document operation. Skill installation supplies guidance, not standing execution authorization.

During CAD design, choose provisional printable widths from the intended material, nozzle/process and existing validated experience; choose height/spacing from the load case, available envelope and comparison. Verify actual generated paths later during print preparation, without inserting a slicing gate into each design step. Numerical examples in the reference are exploration values, not mandatory defaults. Do not impose injection-molding rib ratios on FDM.

Use the suite's additive-manufacturing/DFM guidance for printing and its engineering-analysis skill when claiming stiffness, strength, buckling resistance or life. Report geometry, slicing and mechanical evidence separately. A valid solid or completed simulation alone does not prove physical reliability. The packaged reference has not completed a representative end-to-end CAD/print trial.

Deliver the selected type and reason, parameters, connection map, native model and checks appropriate to the authorized task. Installing this skill does not authorize changing unrelated projects, committing or publishing.
