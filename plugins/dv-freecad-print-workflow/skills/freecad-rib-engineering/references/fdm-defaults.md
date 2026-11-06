# FDM defaults: minimum features, fits, build order, latches

Starting values for FDM parts printed with a 0.4 mm nozzle and about 0.2 mm layers. They are defaults: the project or the user may override any of them, and the actual nozzle, material and printer must be confirmed for each project. Fits depend on the printer and material; confirm critical ones with a small test print and record the values that worked.

## Minimum features

- No wall, rib, tab or other feature thinner than one nozzle width (0.4 mm). Prefer at least two extrusion widths (0.8 mm), so the slicer lays two perimeters instead of a single fragile line or nothing.
- Load-bearing walls and ribs: several extrusion widths. 1.8–2.0 mm is a reasonable first trial for ribs (see [rib-design.md](rib-design.md)); it is an example, not a rule.
- A gap between two features that must stay apart: at least one nozzle width plus the fit clearance below, or the paths merge.
- Heights and steps along Z: prefer multiples of the layer height, so the step really appears.
- Small printed holes come out undersize, and horizontal holes sag at the top. Add a diameter allowance from a test print, or use a flat or pointed top for horizontal holes.

## Fits between printed parts (clearance per side)

| Fit | Per side, default | Typical use |
|---|---|---|
| Press | 0–0.05 mm | parts that must not move; expect force and possible cracking |
| Snug, locating | 0.10–0.15 mm | lids and locating features assembled by hand without play |
| Sliding, running | 0.20–0.25 mm | hinges, slides, rotating pins |
| Free | 0.30–0.40 mm | covers that must drop in, parts with print-to-print variation |

- State per side or diametral explicitly (diametral = 2 × per side) and keep lateral, axial and end clearances separate, as in [enclosure-interface-parameters.md](enclosure-interface-parameters.md).
- A pocket for an inserted item (board, magnet, nut, purchased part) gets its own fit clearance parameter, measured from the real item, not from a nominal catalogue size.
- Derive the mating side from its counterpart plus the fit; do not dimension both sides and the clearance independently.

## Build order

1. **Purchased components first.** Take real dimensions (datasheet, supplier STEP, a measurement) and build their envelopes before modelling around them: body, connector mating travel and plug body, cable bend radius and service loop, finger and tool access, tolerance band. Check the envelopes against the planned case before modelling the case.
2. **Main shape, walls and structural joints.**
3. **Fillets, then cuts.** Round the edges while the edge network is still simple, then cut holes, vents, pockets and slots; the cut trims the rounding cleanly. Rounding after cutting meets short edges and slivers and often fails. A failed fillet is a signal to find the cause (a tiny edge, tangent faces, a radius larger than a neighbouring face, an earlier sliver), not a reason to shrink the radius until it passes.
4. **Edge treatment by print orientation.** Edges on the bed and downward-facing outer edges get chamfers (for example 45°, 0.4–1.0 mm), not fillets: a downward convex fillet starts as a flat overhang, and a chamfer also hides first-layer squish. Top and vertical edges may have fillets. Concave root fillets growing up from a panel print well.

## Integral snap latches

A latch works only when three things are designed together. Parameter names are in section 9 of [enclosure-interface-parameters.md](enclosure-interface-parameters.md).

- **Engagement.** The hook overlaps the catch by a defined amount in the assembled state (`HookEngagement`). A lead-in slope on the entry side; the retaining face angle decides releasable (sloped) or permanent (near square).
- **Deflection during assembly.** The arm must bend at least by the hook projection to pass the catch. Check the root strain against the actual material's allowable strain; for a straight rectangular cantilever, strain ≈ 1.5 · thickness · deflection / length². Lengthen or thin the arm rather than accept a strain the material cannot take (brittle filaments allow little). Let the arm flex within the layer plane, not across layers.
- **Room for the deflection.** Keep free space in the flex direction of at least the hook projection plus clearance (`FreeFlexGap`), clear of walls, ribs, components, fillets and supports, along the whole arm. Add an overtravel stop where over-bending would break the arm. Round the flexible root for the clip, not with the structural screw-support radii.

## At hand-over

Compare the overall size with the requirements, and list the key parameters (fits, wall, latch engagement, nozzle assumption) in a short table, offering to change them without re-asking everything.
