---
name: cad-print-workflow
description: Coordinate FreeCAD design completion, human design decisions and subsequent Bambu Studio print preparation for 3D-printed parts. Use for multi-stage CAD-to-print projects or deciding whether print findings require a new design round.
---

# Design first, prepare printing second

## Workflow ownership

Complete the current FreeCAD design round as fully as possible before entering Bambu Studio. Always design with the intended printer/process in mind, but do not require repeated intermediate slicing. The installed production suite supplies engineering methods, not a conflicting stage schedule. This skill coordinates the package default sequence without modifying upstream skills.

Use [freecad-mcp-operations](../freecad-mcp-operations/SKILL.md) for MCP-preferred CAD execution, [freecad-rib-engineering](../freecad-rib-engineering/SKILL.md) for applicable enclosure preferences, and [bambu-print-preparation](../bambu-print-preparation/SKILL.md) after CAD readiness. Missing optional suite methods are a capability gap to report, not permission to install software. Scale records to the task; a simple part need not acquire an elaborate project bureaucracy.

## Verify current methods

Before adopting a new construction method, follow [current documentation and capability checks](references/current-documentation.md): identify the installed versions, consult official version-relevant native-tool guidance, and distinguish application capability from MCP coverage. Reuse recorded evidence for routine repetition; recheck on version/method changes or unexpected failures. KiCad checks apply only to actual ECAD work, not automatically to a supplied valid STEP reference.

## CAD design round

Read the current project, accepted decisions and authoritative model before asking for information. Establish intended material, printer/build envelope, relevant surface/fit/strength goals and print assumptions early. Do not silently substitute materials: a change can alter fits, flexible joints and structural assumptions.

Resolve structural, engineering and visual design choices in FreeCAD: arrangement, part boundaries, walls, reinforcing features, hardware/retention, motion and access. Consider plausible print orientations, anisotropy, overhangs, support removal and assembly, without claiming slicer verification. Preserve reference assemblies and their coordinates separately from manufactured parts.

Use named driving dimensions, units and stable references, native high-level features, reusable feature prototypes and patterns. Keep distinct manufactured parts distinct. Test expected part counts explicitly rather than accepting any valid solid collection. Preserve a baseline before consequential edits; serialize CAD writes and perform independent review on snapshots.

### Decisions and batches

Maintain one short project decision record shared across feature discussions; use [project-record template](references/project-record-template.md) only where useful. Record decision, reason/source, status and affected parts. Reuse answered questions and delegated authority.

Bundle related unresolved questions with visual evidence, a recommendation and consequences. Consult on design direction and meaningful technical alternatives that are comparable in suitability, required parameters, tolerances and simplifications. Choose routine internal implementation autonomously within agreed intent. Do not ask the user to choose unexplained engineering alternatives or reconfirm every edit. Silence is not approval for a blocked decision; proceed with independent work.

Apply approved changes as coherent dependency-aware batches, then check affected geometry and interfaces. Do not reopen unrelated design topics or launch Bambu after every batch. Record provisional assumptions, distinguishing harmless reversible assumptions from decisions that need the user.

## CAD-ready gate

Move to print preparation when substantial design decisions are settled, no unresolved question materially changes the construction, the intended model/assembly checks have passed, and a named source revision plus matching export exists. Report exceptions explicitly; do not label an incomplete design CAD-ready just because export succeeded.

Relevant checks include recompute state, valid expected solids, dimensions/clearances, fit/motion/access and regenerated nominal geometry. For a parametrically reusable design, exercise meaningful boundary/representative values on copies. A shape audit alone is not proof of parametrization. A selected sweep is not proof over the entire continuous domain.

Slicer checks may remain NOT RUN at CAD readiness. This is intentional, not a failure of the CAD phase. Any unavailable physical/mechanical validation remains an explicit unresolved qualification, not a fabricated PASS.

## Print preparation and return rules

Only now use Bambu Studio to prepare the accepted design for printing. Keep a link between CAD revision, exported geometry, Bambu project/settings and generated results. A settings-only change stays in print preparation. Each proposed CAD change at this stage needs a specific print-related finding and impact assessment.

A local correction may be made in FreeCAD and rechecked without reopening the whole design if it preserves accepted function, appearance, mating interfaces, layout and load paths. A small dimension edit can still be significant if it changes a fit or latch behavior.

For substantial changes, aggregate the findings and viable alternatives, explain their consequences and obtain the user's direction on reopening design (unless that exact decision authority was already delegated). Pause slicing iterations, begin a dedicated FreeCAD-only redesign round, and return through the same CAD-ready gate. Do not let the slicer become an uncontrolled parallel geometry source. New aesthetic ideas unrelated to printing do not silently expand print preparation.

## Evidence and release

Use [release-evidence template](references/release-evidence-template.md) where a reusable record is useful. Distinguish CAD validation, export integrity, slicing/layer review, mechanical analysis and physical fit/print trials. Record raw report/log paths and input revision/settings identity; do not invent PASS values for missing evidence.

When using existing suite validators: numeric assertions must cover every relevant target part, not merely the first reported target. Release cases must actually pass required checks. Expected-failure negative-regression cases belong to a separate test category and cannot qualify a release model as valid. These are acceptance requirements, not a claim that the installed suite scripts have been patched.

After geometry changes, invalidate prior dependent export/slice evidence; after profile/orientation changes, invalidate affected slicing/layer evidence. Keep unaffected checks with their actual scope. CAD-ready, slice-reviewed and physically qualified are different statuses. Preparing a print package does not authorize sending it to a printer or publishing it.
