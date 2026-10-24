# Verification and CLI cautions

These cautions were derived from a source review of Bambu Studio v02.08.02.61, commit 926a7192574bcb9b3a732e1ec59a46d79cb45466. They are not a promise about other versions; verify installed help and behavior.

Sources:
- https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage
- https://github.com/bambulab/BambuStudio/tree/v02.08.02.61

## Keep complete evidence

- A summary warning_message can retain only one message; retain full diagnostics rather than treating it as an exhaustive issue list.
- Preserve the program's result semantics; an OS exit-code representation may not preserve a signed internal error value directly.
- Support detection warnings can be conditional on support settings and checks being enabled. No warning is not proof that supports are unnecessary.
- Support-generation CPU time is not the time the printer will spend printing support material. Use the actual estimate with its field meaning verified.
- Geometric thresholds in detection algorithms are heuristics, not universal printable dimensions.

## Commands are version-sensitive

In the reviewed build, --export-gcode was not an available implemented option in the same sense as ordinary documented slicing/export operations; do not invent a CLI invocation around it. Verify how the actual version emits plate G-code. Exporting project 3MF and exporting internal slice cache are different operations; internal cache is not a printability report. Check output existence and content rather than assuming a flag name proves success.

Do not pass an arbitrary inheritance-only preset leaf where the CLI expects resolved settings. Record the exact printer/nozzle/filament/process combination. Explicitly decide arrangement and orientation instead of accidentally inheriting changes from generic command examples.

## Layer review is a separate check

A clean mesh and a completed slice can still omit thin geometry, bridge a functional gap, create inaccessible supports or compromise a surface. Inspect critical layers. A support-enabled slice may suppress warnings that were visible with support disabled; compare only intentionally and record settings. Do not prescribe an automatic second slice for every object without a useful diagnostic purpose.

CAD checks, toolpath checks, mechanical analysis and physical trials answer different questions. In particular, toolpath survival is not a verified load capacity, and a thumbnail does not establish layer continuity.
