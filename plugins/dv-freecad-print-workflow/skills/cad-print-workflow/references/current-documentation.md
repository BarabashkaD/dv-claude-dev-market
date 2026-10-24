# Current documentation and native capability checks

Use this reference when selecting a new modeling method, introducing a tool not yet verified for the project, changing application versions, or investigating an unexpected failure. It is not a documentation lookup gate before every routine edit.

## Establish the relevant version and application

Record the installed application's exact version/build and, separately, the MCP bridge/tool version or exposed schema. Distinguish the application that owns the work: FreeCAD for the mechanical model; KiCad only when the authorized task actually involves KiCad or ECAD changes. A correct supplied STEP assembly may be used as reference geometry without reopening PCB design or invoking KiCad.

Before selecting a new construction method, check version-relevant official documentation for the available built-in high-level features and recommended workflow. Compare the relevant native alternatives before assuming a bespoke script or low-level geometry generator is necessary. A missing MCP tool does not imply the feature is absent from FreeCAD or KiCad; conversely, an application feature does not prove the bridge exposes it.

## Source order

- Start from official documentation/help for the installed version. FreeCAD's official entry point is https://www.freecad.org/ and its manual/wiki entry is https://wiki.freecad.org/Main_Page; these are source entry points, not a claim that their contents were accessible during package preparation. KiCad's official manual collection is https://docs.kicad.org/; select the matching release and relevant application manual.
- Consult official release notes for version-specific additions, changes or limitations; FreeCAD releases are listed at https://github.com/FreeCAD/FreeCAD/releases. Do not apply a feature documented only in a newer release as though it exists locally.
- If documentation is ambiguous, inspect the installed feature/help, current exposed tool schema and, when useful, official project source for the matching version. A small reversible test on a separate model copy can establish local behavior when authorized; preserve the live model.
- Community examples, tutorials and discussions may suggest methods or explain pitfalls, but identify them as examples rather than official capability guarantees. Verify consequential claims against official sources or an observed local test.
- For Bambu Studio, use the installed version's help and official documentation/source identified in its print-preparation references. Do not carry CLI behavior across versions without verification.

Do not guess command/property names, tool availability or recommended parameters from memory when a consequential new approach depends on them. If a source is blocked or cannot be accessed, do not bypass a challenge or restriction. Use installed help, available version-matched official documentation or tagged official source, and report the limitation. A web failure is not by itself a reason to stop a previously verified safe routine operation; continue within the established evidence and scope, while leaving any genuinely unverified new capability unresolved. Do not label an unverified recommendation as documented or tested.

## Record once, reuse appropriately

Keep a short method decision in the project record:
- Application and exact version/build; bridge version/schema where relevant.
- Method or native tool considered, and chosen alternative with reason.
- Official URL/document section, applicable version and date checked.
- What the documentation establishes, what the bridge supports, and what was observed locally.
- Remaining uncertainty and any task-specific assumption.

Reuse this evidence for repeated operations under the same relevant version and conditions. Recheck after application/bridge updates, a materially new method, changed assumptions, conflicting documentation, or an unexpected failure. Do not repeatedly interrupt the user or browse anew for every Pad, pattern instance or routine dimension change.

Prefer the verified native high-level route through MCP. If the native feature is not exposed by the bridge, assess a bounded script invoking native features under the execution policy rather than rebuilding the model point by point. Documentation verification does not itself authorize installing software, changing settings or expanding the task.
