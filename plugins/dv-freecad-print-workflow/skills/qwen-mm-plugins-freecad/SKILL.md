---
name: qwen-mm-plugins-freecad
description: Operate an existing FreeCAD MCP bridge for document inspection, editable modeling, views and connection recovery, with bounded native-script exceptions. Does not install or replace CAD servers.
license: Apache-2.0
---

# FreeCAD MCP operation

This adapted skill owns execution and connection handling. Detailed engineering belongs to the available FreeCAD production-suite skills and local design guidance. [Provenance](references/provenance.md) records history, not permissions or present tool availability.

## Preferred route and script exception

Use the existing MCP connection whenever it offers a practical route. Prefer FreeCAD's built-in high-level features: Bodies, constrained Sketches, Pad/Pocket, patterns/mirrors, additive features, datums and purposeful dress-up operations. Reuse accepted parameters and feature prototypes rather than reconstructing each repeat numerically.

A script, macro or FreeCADCmd operation is appropriate when no suitable supported route exists or it materially shortens the path to the requested result. Briefly record why and its bounded scope. Prefer scripts that create/modify the same native editable features, rather than replacing the model with opaque point/edge/BRep-generated shapes. Sketch creation naturally uses points and lines; that is not prohibited. Imported reference geometry, shape inspection, export and validity checks are not a requirement to rebuild the source parametrically.

Skill availability is not blanket execution permission. Use the current task and environment's permissions; this skill adds no mandatory per-script approval beyond those boundaries. Read unfamiliar code before running it. Preserve a recoverable baseline, deterministic inputs and a readable model history. Do not disguise direct BRep output as a parametric model.

## Inspect the actual bridge

For a new modeling approach, use [current documentation and capability checks](../cad-print-workflow/references/current-documentation.md) to verify built-in FreeCAD alternatives for the installed version before deciding that a custom implementation is needed. Keep native capability and bridge exposure separate; cache the decision for routine reuse.

Discover the currently exposed tools and schemas before selecting commands. Names such as get_rpc_status, list_documents, execute_code, execute_code_async, execute_code_headless and get_view are illustrative bridge capability names, not a guarantee of availability or identical semantics on this host. Use only supported equivalents and report missing capabilities; do not invent tool calls or install a replacement server.

Identify the intended document by name and exact object names/types/placements/properties. The active GUI document alone does not establish task ownership. Preserve unsaved work. Use one writer per document and transactions/checkpoints for related changes.

Use supported object tools for straightforward live edits. If using a code tool, inspect its execution contract: GUI/document mutations must use its supported GUI-thread dispatch; do not mutate GUI documents from background workers. Async computation is suitable only where documented safe, with explicit result status and commit handling.

A headless process is a separate session. Give it explicit input/output paths and reconcile unsaved GUI changes before operating on file copies. Do not overwrite or reload unsaved work merely to make the headless result appear.

A timeout does not prove a mutation stopped. Inspect operation status and the document before retrying; do not duplicate features or launch a competing profile to hide uncertainty. Capture current views after changes, verify the intended object and view, and never expose base64 as a user deliverable.

## Model evidence

Recompute after coherent batches, inspect final tips, validate expected solids and measure affected interfaces. A valid shape does not prove functional correctness or editable regeneration. Exercise meaningful parameter cases in an isolated model copy when parametric behavior matters; restore and verify the nominal model.

Use [cad-print-workflow](../cad-print-workflow/SKILL.md) for CAD-ready and release gates. FreeCAD is the source of design geometry. Do not repeatedly invoke a slicer during an unfinished CAD round. Report performed, failed and unperformed checks separately.
