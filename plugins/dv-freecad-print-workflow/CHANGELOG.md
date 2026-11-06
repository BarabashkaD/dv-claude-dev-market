# Changelog

## 2.0.0

Reworked around three ways of working: headless scripts for analysis and checks, a separate GUI-macro run for files a person opens, and MCP for the live window only. "MCP-preferred execution" is dropped.

- New skill `freecad-zone-edit`: local edits to a finished solid with zone guards and a guards reference.
- New skill `freecad-headless-analysis`: numeric headless checks and measurements, a quiet wrapper `fc-quiet.sh`, collision-scope and section-example references.
- New skill `freecad-gui-macro`: a template macro run as a separate GUI process (when to use it; input left unchanged; the process ends by itself).
- New agent `freecad-worker` (Claude Code only): headless executor for one local CAD round.
- Reworked `cad-print-workflow`, `freecad-mcp-operations` (MCP is the live-window route; Apache-2.0 notice kept, changed files marked), `freecad-rib-engineering` (new `fdm-defaults.md`) and `bambu-print-preparation`.
- Removed the reference `rib-selection-and-modeling-guide.md`; `rib-design.md` supersedes it.
- Removed the wording that treats an external production suite as an installed dependency.
- The print-mesh guard has one scope everywhere: zones or check boxes during a round, the whole body once at round closure.
- Run-limit rules have one source, `guarding-autonomous-runs` (plugin dv-agent-controller; install it as well); a parametric FCStd for a person is edited and saved in a GUI-macro run.

## 1.3.0

- Add local refinement rounds to the existing CAD workflow: minimal edits, mandatory local checks and one full relevant validation at explicit round closure.
- Ask per remark whether a yellow-highlighted overview is wanted; when requested, wait for interpretation confirmation before editing.
- Keep CAD-ready/release gates, MCP preference and design-before-print sequencing; clarify deferred parameter sweeps in the operational skill.

## 1.2.0

- Add the portable root plugin manifest and a native repo marketplace for ChatGPT Desktop and Codex.
- Keep the native catalog intentionally scoped to this validated FreeCAD package while retaining the full Claude-compatible catalog.
- Document marketplace setup, restart/new-conversation testing, cached-copy refresh behavior and the separate standalone `.agents/skills` route.

## 1.1.0

- Status: evolving and incomplete skill collection; static checks and manual review only, with no live FreeCAD/Bambu qualification.
- Rename the operational bridge skill to `freecad-mcp-operations` and document the existing FreeCAD MCP reference contract at version 0.1.27 without adding a runtime dependency, installer or launcher.

- Package four skills as a Claude plugin with marketplace registration.
- Separate CAD design completion from subsequent Bambu Studio preparation; reopen a dedicated CAD round for significant design changes.
- Prefer MCP with bounded native high-level scripting exceptions and runtime capability checks.
- Add version-aware official documentation checks and separate geometry, parameter regeneration, slicing and physical qualification evidence.
- Preserve configurable enclosure, rib, screw-support, ventilation, access-cover and PCB guidance with 10 concept illustrations.
- Replace personal preference history with configurable package defaults and private project examples with generic examples.
- Remove private provenance, machine-specific identifiers and image correlation metadata from public copies; retain public upstream attribution and unchanged decoded illustration pixels.

No executable installer, hook, CAD generator or printer-dispatch code is included.
