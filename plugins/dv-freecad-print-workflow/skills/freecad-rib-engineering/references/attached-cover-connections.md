# Covers that remain attached when open

Current sequencing: finish the FreeCAD design round before Bambu Studio print preparation. Any slicing/printed-path checks below belong to that later stage, not a mandatory intermediate CAD gate. Use the active SKILL.md and current project decisions for execution and scope.


Configurable package discussion options; engineering models remain unvalidated. The [simple removable cover](access-covers.md) is a default appearance and snap-closure reference. The default shortlist is H1, H2, H3, H7 and H8; no connection is preselected for a project.

## Saved 3D discussion examples

Show the active examples during concept discussion: [H1–H3: pin, snap-in and living hinges](../assets/access-covers/attached-covers-h1-h3.png) and [H7: integral ball pivot with retaining socket](../assets/access-covers/attached-cover-h7-ball-pivot.png). Preserve these identifiers to avoid confusion. H4–H6 are outside the default shortlist but may be included when justified by the project. The views show proposed open arrangements and simplified enlarged joint details; exact assembly compliance, retention, stops, mating sections, closed configurations and clearances must be designed and checked in CAD. Drawn open poses do not establish friction or hold-open capability. H1's extended pin and H2's separated pivot in the detail views explain assembly; the main views represent retained connections.

Separate three functions: the connection that keeps the cover captive, the catch that retains it closed, and any stop/detent/friction that limits motion or holds it open. A hinge alone does not imply hold-open behavior. A tether can prevent loss without guiding the lid.

| ID | Connection | Movement and main consideration |
|---|---|---|
| H1 | Pin hinge | Interleaved knuckles rotate around a separate retained pin, which can be plastic. Requires bore/knuckle clearance and pin retention; define opening stop where needed. |
| H2 | Snap-assembled pivot | Integral axle ends/trunnions snap into receiving sockets, then rotate. Requires intentional assembly deflection and adequate retention throughout opening, not just in the closed position. |
| H3 | Integral living hinge | A thin flexible region joins lid and case. Material, bending geometry, build orientation and repeated-use evidence govern suitability. Do not assume a rigid case filament can use molded hinge dimensions. |
| H7 | Integral ball pivot and retaining ball socket | Spherical ball and neck integral with one part, captive in a matching socket integral with the other. A single ball permits swiveling; two separated aligned ball centers guide rotation around their joining line in the nominal rigid geometry. Retention lip, assembly flex and neck clearance require explicit design. |

Additional options outside the default shortlist: H4 retaining strap/tether, H5 captive slide, H6 captive slide-and-pivot. Their identifiers are not reused.

Print-in-place is a manufacturing approach for some articulated connections, not an independent motion type. Treat release gaps, freedom after printing and trapped supports as process-specific checks. All-plastic connection geometry can be considered without introducing metal hardware by default.

For a simple cover, compare H1, H2, H3, H7 and the H8 spring-retractable candidate; shortlist two or three for the actual case rather than presenting every option by default. H1 has a separate retained pin; H2 uses cylindrical trunnions and sockets; H3 bends a flexible web; H7 uses genuinely spherical balls in retaining sockets. H3 requires a deliberate flexure/material choice. Preserve shallow profile and simple release operation. These are concept candidates, not proven performance rankings.

## Discussion views and motion-specific parameters

When the selected concept is being explained, show the relevant saved 3D draft inline with an absolute local path, or open it and provide the link if inline display is unavailable. Use the preferred simple cover shape as the visual starting point and keep the drawings compact. Do not regenerate equivalent stock pictures when the saved reference is sufficient. Exact CAD and text govern dimensions; no picture establishes retention, printability or lifetime.

H8 has no saved 3D view yet. If requested or needed to avoid misunderstanding, create a clearly labeled draft and retain it alongside these discussion assets in a permitted workspace. Show an internal retracting pin/ball carried by an integral plastic spring arm, or a separate spring/plunger if that construction is actually under discussion. Mark the variant, show an engaged and retracted detail, the socket and free spring-motion region, and a case section showing the closed envelope and opening clearance. Do not imply an external fixed hinge demonstrates a hidden retracting joint. Keep the image conceptual until actual CAD validates the mechanism. Avoid installing a new asset into a protected skill location without the required filesystem access.

Relevant parameters beyond the common cover/clip dimensions:

- H1: pivot axis/offset, pin and bore sizes with declared running fit, knuckle lengths/gaps/walls, retained-pin end geometry, and opening stops.
- H2: trunnion diameters/lengths/spacing, socket dimensions and capture, assembly entry/compliance, root radii, running/end clearances and opening range. A snap-in rotary connection is distinct from the catch holding the lid closed.
- H3: flexible-web length/width/thickness/profile, root transitions, bend path/radius and operating range. Record material, build orientation and intended cycles rather than copying molded living-hinge sizes into FDM.
- H7: use the sphere/socket definitions below; one ball permits swivel, while two separated ball centers nominally define the hinge axis.
- H8: retracting feature diameter/shape, stroke, extended engagement, extension/retraction stops, release access and spring layout. For a plastic arm add free length/width/thickness, root radius, motion gap and assembled preload; for a separate spring record its actual specification and available travel. Avoid duplicated spring-force targets and independent dimensions that conflict.

Use preferred model-level dimensions with case-specific local review. Keep radial versus diametral clearance explicit and separate free-running clearance from temporary assembly deflection and positive retaining overlap.

## H7 — ball and retaining socket

The new illustration proposes two integral ball pivots to guide hinge-like opening without a separate pin. Ball count/positions remain case-specific: a single ball permits additional swivel, while two spaced ball centers constrain the nominal rotation axis. Both cups must accommodate their center spacing, assembly route and actual tolerances without binding or excessive wobble. Do not assume spherical geometry automatically corrects a spacing mismatch.

Expose ball diameter, neck diameter/length, neck-root radius, ball-center positions/spacing, socket running clearance (declare radial or diametral), socket wall thickness, retaining-mouth size/coverage, relief-slot geometry and required opening range. Derive socket cavity size from ball diameter and running clearance. Distinguish rotational running clearance from retention undercut and temporary assembly deflection. A retaining lip must actually capture the ball; a hemisphere resting in an open bowl is not sufficient.

Check insertion strain/force, pull-out resistance, neck/root loading, remaining cup sections and neck/cover/frame clearance throughout opening and closing. If a slot accommodates neck motion or assembly, verify it does not create an unintended escape route at another angle. Round structural roots without consuming the running gap or obstructing assembly flexibility. The cutaway in the picture removes material for explanation only; it is not a proposed half-cup manufactured shape. The illustrated approximately 100-degree open pose is not a target or verified motion limit. No dimensions, retention force or life are validated.

Resolve the required swing direction and concealed/exposed joint envelope; whether it must remain open by itself; required access angle/clear opening; and whether service removal should be deliberately possible. Obtain opening-cycle/material/environment requirements when sizing a real connection. Check cables and fingers, hinge sweep, snap release and component access in both states. A hinge may replace the earlier locating tabs, so do not blindly add it to the unchanged removable-cover geometry.

## H8 candidate — concealed spring-retractable pivot

H8 is an optional concealed spring-retractable pivot candidate for compact assembly. Confirm whether the required spring function is pivot retraction or automatic opening/closing of the lid. This is not a validated design or preselected project connection. Exposed illustrations do not require H1/H2/H7 to be exposed in every implementation.

A pin retracts inward for fitting or deliberate removal, then spring force extends it into an internal bearing socket. In the assembled state it rotates in that socket. Consider either a separate plunger and compression spring or a pin/ball supported by an integral compliant plastic arm. The latter must provide a real compliant stroke and controlled strain; it is not simply an unsupported flexible bump. Neither variant is automatically smaller, flush, stronger or longer-lived than a fixed pivot.

Treat closed-envelope concealment, motion clearance and spring actuation as separate requirements. Locate pivot centers and allow the lid edge/rim to clear the case through its full swing. Preserve engagement during use; specify extension stop, stroke, bearing engagement, retraction access, pull-out/load paths and unintended release prevention. Review elastic preload/creep for plastic spring arms and whether service removal is intended. A retractable pivot does not itself provide a closed-position catch, hold-open function or spring-assisted lid movement.

[Southco concealed retractable-pin hinges](https://southco.com/en_us_int/hinges/concealed-hinges/f6-concealed-door-removal-hinges) demonstrate spring-loaded pins for installation/removal and secure engaged operation. These commercial designs support the mechanism vocabulary, not dimensional or performance claims for a printed integral flexure. A torsion/return spring acting on opening angle is a different function from axial pin retraction.

## Primary references and limits

- [Fictiv plastic hinge case study](https://www.fictiv.com/articles/fictivmade-7-hinge-design): compares pin and snap hinge constructions and describes retention/clearance iterations. It does not qualify a small FDM access-cover hinge.
- [OKW enclosure comparison](https://www.okwenclosures.com/en/news/blog/BLG2309-industrial-electronics-enclosures.htm): commercial enclosures use hinges or lid-retaining straps to keep lids attached during service. Its material and ratings belong to those products.
- [Protolabs printed living hinges](https://www.protolabs.com/en-gb/resources/insight/3d-printing-living-hinges/): highlights geometry, material and process sensitivity when transferring flexible hinges to additive manufacturing. No example dimensions or life ratings are adopted.
- [Protolabs molded living hinges](https://www.protolabs.com/resources/design-tips/designing-living-hinges-that-fold-flat/): distinguishes a broad-bending tether strap from a tightly bending living hinge. Molding material/process guidance is not an FDM prescription.

- [igus polymer ball-and-socket joint](https://www.igus.com/product/igubal-WGRM_WGLM) provides a primary example of polymer ball/socket components for rotation and swiveling. Its separate commercial components, proprietary materials and performance do not validate the proposed integral printed H7 geometry.

The active discussion identifiers are H1, H2, H3, H7 and H8, with H4–H6 set aside. Dimensions, retention and life remain unvalidated until an actual design and appropriate trials exist.
