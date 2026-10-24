---
name: freecad-mcp-operations
description: Operate the existing configured FreeCAD MCP bridge for document inspection, editable modeling, views and connection recovery, with bounded native-script exceptions. Does not install or replace CAD servers.
license: Apache-2.0
---

# Existing FreeCAD MCP operations

This skill documents operations for the existing configured FreeCAD MCP bridge. It adds no MCP server, runtime dependency, installer, launcher, autostart behavior or printer control. [Provenance](references/provenance.md) records historical adaptation and public references, not installed provenance or present permissions.

## Reference contract and version

The documented reference is FreeCAD MCP version 0.1.27, using the official snapshot [execution contract](https://github.com/neka-nat/freecad-mcp/blob/78bf0230a03324b56c9a0b7f55150fb5be2a0d42/docs/execution.md), [tool contract](https://github.com/neka-nat/freecad-mcp/blob/78bf0230a03324b56c9a0b7f55150fb5be2a0d42/docs/tools.md) and [server source](https://github.com/neka-nat/freecad-mcp/blob/78bf0230a03324b56c9a0b7f55150fb5be2a0d42/src/freecad_mcp/server.py). This pinned public reference confirms the documented contract; it does not prove which bridge is installed or how it was registered on the current host.

Before using the skill, verify the actual current tool schemas, bridge health and reported version. If the installed bridge differs, report the mismatch and use its supported contract only; do not silently substitute another bridge or claim that this reference proves local installation provenance.

For a new modeling approach, also use [current documentation and capability checks](../cad-print-workflow/references/current-documentation.md) to verify built-in FreeCAD alternatives for the installed version. Keep native application capability and MCP exposure separate.

## Preferred route and bounded script exception

Use the existing MCP connection whenever it offers a practical route. Prefer supported high-level editable operations: Bodies, constrained Sketches, Pad/Pocket, patterns/mirrors, additive features, datums and purposeful dress-up operations. Reuse accepted parameters and feature prototypes rather than reconstructing each repeat numerically.

A native FreeCAD Python script, macro or headless FreeCADCmd operation is appropriate only when no suitable supported high-level route exists or it materially shortens the requested result. Record why and its bounded scope. Prefer scripts that create or modify the same native editable features instead of opaque point/edge/BRep reconstruction. Skill availability is not execution permission; use the current task and environment authorization, read unfamiliar code before running it and preserve a recoverable baseline.

## Health, discovery and document ownership

- `get_rpc_status()` is the GUI-independent health and version probe. Use it first when checking bridge health.
- `list_documents()` uses GUI dispatch and is not an independent health probe.
- Discover the actual exposed tools and schemas before selecting commands. Use only supported equivalents and report missing capabilities.
- Identify the intended document by name and exact object names, types, placements and properties. An active GUI document alone does not establish task ownership. Preserve unsaved work, serialize document writes and use transactions/checkpoints for related changes.

## GUI operations

`execute_code(code, include_screenshot=True, view_name='Isometric', timeout=None)` runs GUI-thread operations in a shared namespace with async jobs. Prefer supported high-level object tools where suitable; use bounded native-feature Python only under the exception policy above. Do not mutate GUI documents from background workers.

`get_view(view_name, width=None, height=None, focus_object=None)` requests an explicit image when optional images are suppressed. Use only view names supported by the current bridge and documentation. `reload_document(doc_name)` closes and reopens a saved document; reconcile unsaved work before using it.

Queue expiry before a GUI operation starts cancels a pending operation, but execution expiry does not stop an already-started mutation. Inspect `get_rpc_status()` for `GUI_DISPATCH_STUCK`, then inspect job and document state. Never retry a possibly executed mutation blindly, duplicate features or launch a competing profile to hide uncertainty.

## Async and headless contracts

- `execute_code_async(code)` returns a `job_id` for independent geometry/CPU work only. Do not change documents, recompute/save or access GUI state from the worker.
- `get_async_status(job_id='')` reports running, done or failed jobs; an empty ID lists running and recent jobs. Use this bridge contract rather than assuming another async API.
- `async commit(fn, timeout=120)` runs a callback on the GUI thread. Alternatively, store worker results and apply them later with `execute_code`. Use only the documented supported contract.
- `execute_code_headless(code, timeout=600)` runs a separate FreeCADCmd process on the MCP server machine, independent of `--host`, with a fresh namespace. Use explicit imports and open/save paths. A positive finite timeout kills the headless process and may retain partial output. Unsaved GUI state does not carry over.

Keep detailed numeric timeout defaults in this version-scoped contract, not as universal rules. Report performed, failed and unperformed checks separately.

## Evidence and workflow boundaries

Recompute after coherent batches, inspect final tips, validate expected solids and measure affected interfaces. A valid shape does not prove functional correctness or editable regeneration. Exercise meaningful parameter cases in an isolated model copy when parametric behavior matters; restore and verify the nominal model.

Use [cad-print-workflow](../cad-print-workflow/SKILL.md) for CAD-ready and release gates. FreeCAD remains the source of design geometry; do not repeatedly invoke a slicer during an unfinished CAD round. This skill does not authorize changing unrelated projects, installing software, changing MCP configuration, publishing, or printing.
