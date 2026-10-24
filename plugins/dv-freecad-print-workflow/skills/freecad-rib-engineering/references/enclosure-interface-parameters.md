# Parameters for the nine plastic enclosure interface examples

Current sequencing: finish the FreeCAD design round before Bambu Studio print preparation. Any slicing/printed-path checks below belong to that later stage, not a mandatory intermediate CAD gate. Use the active SKILL.md and current project decisions for execution and scope.


Configurable package guidance. Active local parameter reference. No universal numerical defaults are assigned; choose preferred model values and review each location. This is not a tested parametric component library or structural qualification.

## Visual reference and discussion use

Read [the enclosure decision and discussion rules](enclosure-interfaces.md). Show the [overview](../assets/enclosure-interfaces/overview-01-09.png) for concept selection and the appropriate annotated sheet when explaining parameters:

- [Examples 1–3: lid placement](../assets/enclosure-interfaces/parameters-01-03.png).
- [Examples 4–6: stepped edges, grooves and pins](../assets/enclosure-interfaces/parameters-04-06.png).
- [Examples 7–9: lugs, rails and clips](../assets/enclosure-interfaces/parameters-07-09.png).

Keep the same example numbers during user discussions. Images locate relevant properties schematically; use the written definitions and actual CAD geometry for exact dimensions and dependencies. The selected images are discussion aids, not production drawings. Do not infer exact dimension spans from illustrative arrows.

## Parameter conventions

- Lengths use explicit units, normally mm; angles use degrees; counts are integers. Name the reference plane, fit direction and feature owner.
- Read existing case/lid dimensions from the parent definition rather than introducing conflicting duplicate inputs.
- Use preferred model-level values with per-interface/per-location overrides and recorded reasons. Review material, printer, orientation, component neighborhood, remaining wall thickness, assembly access and required service behavior. No universal clearance, radius or feature size is adopted.
- Distinguish clearance **per side**, total width difference and **diametral** clearance. Keep lateral, axial and end clearances separate.
- Derive a mating feature from its counterpart plus the chosen fit. Do not independently dimension both sides and then also constrain their clearance.
- Use explicit bearing/stop surfaces to establish the seated position. A visible seam gap must be compatible with those surfaces rather than leaving the lid unsupported.
- Root radii and edge treatments must preserve mating lands, required engagement and remaining sections. The R1-linked radii from the screw-support rules apply to screw supports, not automatically to these interfaces or flexible clips.

## 1 — Lid over the walls (outside cap)

| Parameter | Definition |
|---|---|
| `LidThickness` | Cover plate thickness; share the parent lid parameter. |
| `SkirtThickness` | Thickness of the downward outer skirt. |
| `SkirtDepth` | Distance the skirt extends below the underside reference of the lid. |
| `SkirtOverlap` | Actual vertical overlap with the case walls in the seated state; derive from depth and seating position when appropriate. |
| `SkirtClearanceX`, `SkirtClearanceY` | Per-side gaps between skirt inner faces and case outer faces. |
| `SeatHeight`, `SeatingLandWidth` | Location and width of the real surface supporting the lid. |
| `SkirtEndClearance` | Gap from skirt end to any lower shoulder or obstructing structure. |
| `EntryLeadIn`, `CornerFitRadius` | Entry treatment and compatible corner geometry. |

For a straight rectangular cap without taper, the internal skirt span is the case outside span plus twice the respective per-side clearance; the outer envelope also includes skirt thickness. Review skirt flexibility, warp, external footprint and removal travel.

## 2 — Lid on the rim

| Parameter | Definition |
|---|---|
| `LidThickness` | Cover plate thickness. |
| `OverhangX`, `OverhangY` | Per-side projection beyond the case exterior; a zero value gives a nominally aligned exterior in that direction. |
| `RimBearingWidth` | Available contact width between cover and wall rim, derived or checked against the parent wall section. |
| `SeatHeight` | Elevation of the seating plane. |
| `VisibleSeamGap` | Deliberate visible separation only where compatible with the bearing/stop arrangement. |
| `CornerRadius`, `EdgeBreak` | Outer plan radius and edge treatment that preserve the seating surface. |
| `LocatorSetback` | Position of optional pins/lugs/lips relative to the rim when another interface type is combined. |

A flat lid sitting on a rim has no inherent sideways locator. Specify a compatible locating feature separately if needed; do not invent a locating clearance for an absent skirt.

## 3 — Lid inside the walls (inset)

| Parameter | Definition |
|---|---|
| `LidThickness` | Cover plate thickness. |
| `InsetClearanceX`, `InsetClearanceY` | Per-side gaps between lid edges and case inner walls. |
| `TopOffset` | Signed lid-top elevation relative to the wall rim: zero flush, negative recessed, positive proud. |
| `LedgeProjection` | Distance the supporting ledge projects inward. |
| `LedgeThickness` | Structural thickness beneath the ledge's bearing surface. |
| `LedgeCoverage`, `LedgeLocations` | Continuous perimeter ledge or selected supporting tabs and their extent/positions. |
| `EntryLeadIn`, `CornerFitRadius` | Entry treatment and compatible internal/external corner geometry. |
| `RemovalNotchWidth`, `RemovalNotchDepth`, `RemovalNotchLocation` | Optional access for lifting a removable inset lid. |

For straight rectangular walls, derive lid spans from the inside spans minus twice the respective per-side clearance. Derive ledge seat elevation from rim elevation plus `TopOffset` minus lid thickness. Review remaining opening, internal clearance, ledge bearing and ability to remove the lid.

## 4 — L + L stepped edges

Here L + L means two complementary stepped edge sections; assign the outer/inner step explicitly to the relevant part.

| Parameter | Definition |
|---|---|
| `StepHeight` | Vertical extent of the stepped overlap. |
| `StepOffset` | Lateral shift between the two levels of the edge section. |
| `UpperLegThickness`, `LowerLegThickness` | Remaining plastic thicknesses of the complementary legs; derive where controlled by parent wall geometry. |
| `EngagementLength` | Actual overlap in the seated configuration. |
| `LateralClearance` | Per-side or single-interface gap, explicitly identified, between the overlapping faces. |
| `EndClearance` | Axial gap at non-bearing ends to prevent premature bottoming. |
| `BearingLandWidth` | Width of the surface intended to establish seating. |
| `ProfileExtent`, `BreakLocations` | Continuous perimeter or segmented runs and interruptions around ports/features. |
| `LeadIn`, `RootRadius` | Entry and structural corner treatments. |

Check correct complementary orientation, retained wall sections, corner fit, seating sequence and whether a step catches during opening.

## 5 — Tongue-and-groove

| Parameter | Definition |
|---|---|
| `TongueThickness` | Web thickness of the projecting tongue. |
| `TongueHeight` | Projection above its attachment reference. |
| `EngagementDepth` | Actual penetration into the groove when seated. |
| `GrooveSideClearance` | Clearance on each side of the tongue for the stated centered fit. |
| `GrooveBottomClearance` | Clearance between tongue end and groove floor when other surfaces establish seating. |
| `GrooveWallThickness` | Remaining thickness of the two receiving walls. |
| `GrooveFloorThickness` | Remaining material beneath a blind groove. |
| `ProfileExtent`, `BreakLocations` | Continuous or interrupted runs. |
| `EntryLeadIn`, `TongueRootRadius`, `GrooveCornerRelief` | Entry and corner compatibility treatments. |

For a centered straight rectangular tongue, derive groove width as tongue thickness plus twice the side clearance. Groove depth equals engagement plus bottom clearance when measured from the same entry datum. Review inner-corner interference and cleaning/printing access. A groove is not automatically a seal or a latch.

## 6 — Locating pins and sockets

| Parameter | Definition |
|---|---|
| `PinDiameter` | Diameter of the functional locating section. |
| `PinProjection` | Total protruding length from the parent surface. |
| `EngagementLength` | Pin length inside the receiving socket in the seated state. |
| `RadialClearance` | Radial gap; diametral clearance is twice this value. |
| `SocketEndClearance` | Clearance beyond the engaged pin end in a blind socket. |
| `PinCount`, `PinPositions` | Number and datum-based positions; derive spacing from positions or vice versa. |
| `PinRootRadius`, `TipLeadIn`, `SocketEntryLeadIn` | Root and entry treatments. |
| `SocketWallThickness`, `SocketFloorThickness` | Retained surrounding and blind-end material. |
| `LocatorReliefMode`, `ReliefDirection`, `ReliefAmount` | Optional slot/diamond/relieved receiving geometry to accommodate redundant constraints. |
| `KeyingPattern` | Optional asymmetry or different locator shapes to prevent reversed assembly. |

For a round clearance socket, derive socket diameter as pin diameter plus twice radial clearance. For a blind socket, derive required depth from actual engagement plus end clearance. Fit type must be intentional; default discussion should not assume a press fit or strength retention from a locating pin.

## 7 — Locating lugs and pockets

| Parameter | Definition |
|---|---|
| `LugWidth`, `LugThickness` | Broad and thin dimensions of the locating tab section. |
| `LugProjection`, `EngagementDepth` | Overall protrusion and actual inserted length. |
| `WidthClearance`, `ThicknessClearance` | Explicit per-side gaps in the two section directions. |
| `PocketEndClearance` | Clearance beyond the engaged end. |
| `LugCount`, `LugPositions`, `LugOrientation` | Number, locations and orientation relative to datums. |
| `LugRootRadius`, `EntryLeadIn`, `PocketCornerRelief` | Root, entry and mating-corner treatments. |
| `PocketWallThickness`, `PocketFloorThickness` | Retained receiving material. |
| `KeyingPattern`, `RelievedDirection` | Optional reverse-assembly prevention and tolerance relief. |

For centered rectangular fits, derive pocket width/thickness from lug dimensions and their respective clearances. Check pinched corners, tab root loading and internal envelopes. A rigid lug is distinct from a flexible clip.

## 8 — Sliding rails / dovetail

| Parameter | Definition |
|---|---|
| `RailProfile` | Plain guide, T-like guide or dovetail as appropriate. |
| `RailHeight`, `RailBaseWidth` | Nominal profile section dimensions. |
| `FlankAngle` | Dovetail flank angle, explicitly measured from the local vertical; derive the dependent top width for the chosen profile orientation. |
| `SideClearance`, `VerticalClearance` | Fit gaps measured in declared lateral/vertical directions; for dovetails also state or derive the clearance normal to the flanks. |
| `RailLength`, `EngagedLength` | Total guide length and overlap in the final position. |
| `RailCount`, `RailSpacing` | Number and location of guides. |
| `SlideDirection`, `InsertionTravel` | Datum-based insertion direction and required unobstructed travel. |
| `EntryLeadIn`, `RailRootRadius` | Entry and root treatments. |
| `EndStopLocation`, `EndStopThickness`, `EndPlay` | End-stop geometry and clearance in the seated position. |

Do not simultaneously drive base width, top width, height and flank angle for the same simple trapezoid. Derive complementary track geometry. Verify insertion and withdrawal paths; rails may still permit sliding back out. No separate lock is added by this reference.

## 9 — Integral clips

| Parameter | Definition |
|---|---|
| `ClipStyle`, `ClipOwner`, `FlexDirection` | Cantilever or another justified integral form, owning part and working flex direction. |
| `BeamFreeLength`, `BeamWidth` | Unrestrained beam length and width. |
| `BeamRootThickness`, `BeamTipThickness` | Thickness distribution; derive tip thickness from a taper ratio if that is the selected driving mode. |
| `HookProjection`, `HookEngagement` | Hook protrusion and effective overlap with the catch when assembled. |
| `EntryRampAngle`, `ReleaseFaceAngle` | Lead-in and release/retaining face inclinations, with their angular datums declared. |
| `CatchOpeningSize`, `CatchLocation`, `CatchWallThickness` | Receiving window/ledge geometry and retained material. |
| `FreeFlexGap`, `OvertravelStopGap` | Space for working motion and an optional limit against excess deflection. |
| `ClipRootRadius`, `HookEdgeRadius` | Flexible root and hook treatments, selected for the clip geometry and material. |
| `ClipCount`, `ClipPositions` | Number and locations. |
| `ReleaseAccessWidth`, `ReleaseAccessDepth` | Finger/tool access where the clip must be reusable. |
| `RetainedPreload` | Intended assembled deflection; zero or nonzero must be deliberate and checked for creep. |

Treat required insertion/release deflection, peak strain, insertion/removal force and retention force as derived results or specified performance targets, not arbitrary independent geometry dimensions. Record opening-cycle target, material/temperature and print orientation as requirements/process inputs. Verify the flexible region remains free; do not apply screw-boss gussets or common screw-support radii to immobilize or over-thicken the clip.

## Review result and source boundary

This is the package editable parameter vocabulary. It does not claim the nine examples already exist as a tested parametric library. Choose only relevant controls and derive dependent geometry; the user need not manually enter every item in the tables.

Prusa documents configurable connector shape, size, depth and rotation, plus adjustable dovetail geometry. [Connector documentation](https://help.prusa3d.com/article/cut-tool_1779).

Formlabs discusses clip length/profile, material strain, fit, orientation and iteration; it does not establish universal FDM dimensions. [Snap-fit guidance](https://formlabs.com/blog/designing-3d-printed-snap-fit-enclosures/).

Protolabs discusses complementary pins/sockets, tongues/grooves and reusable versus permanent clips. Its molding examples support the interface vocabulary; molding process dimensions are not adopted here. [Self-mating guidance](https://www.protolabs.com/resources/design-tips/creating-self-mating-parts-in-injection-molding-design/).
