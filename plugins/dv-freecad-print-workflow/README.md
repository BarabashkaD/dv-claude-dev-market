# FreeCAD and print workflow · 1.1.0

Four documentation-only skills for editable FreeCAD design followed by Bambu Studio print preparation. This package adds no MCP server, installer, executable hook, CAD generator, slicer or printer-dispatch code.

Status: 1.1.0 is an evolving, incomplete skill collection. It has static checks and manual review only; it is not live FreeCAD/Bambu qualified.

## Skills

- [cad-print-workflow](skills/cad-print-workflow/SKILL.md): decisions, coherent changes, CAD readiness, print preparation and return-to-design rules.
- [qwen-mm-plugins-freecad](skills/qwen-mm-plugins-freecad/SKILL.md): discover the actual MCP bridge, operate safely and preserve native editable features.
- [freecad-rib-engineering](skills/freecad-rib-engineering/SKILL.md): configurable enclosure, rib, screw-support, interface, cover, ventilation and PCB mounting guidance.
- [bambu-print-preparation](skills/bambu-print-preparation/SKILL.md): prepare accepted geometry, inspect actual layers/supports and classify findings.

## Workflow

Finish and verify the FreeCAD design round first. Consider printing throughout design, but do not require repeated intermediate slicing. Then prepare the accepted revision in Bambu Studio. Correct local print-related geometry in the source model; significant concept, fit, layout or load-path changes reopen a dedicated FreeCAD round before slicing resumes.

MCP is strongly preferred. Scripts, macros or FreeCADCmd are bounded exceptions when no suitable supported route exists or they materially shorten the path. Prefer built-in high-level editable features over opaque generated geometry. The skill does not grant execution, installation, publishing or printing authority.

Before using a new method, verify the installed application's official version-relevant documentation and actual bridge capabilities separately. Reuse evidence for routine operations; recheck when versions, methods or assumptions change or an unexpected failure occurs. KiCad checks apply only to actual ECAD work.

## Install and check

From the marketplace, install `dv-freecad-print-workflow@dv-claude-dev-market`. Update the marketplace first if it is already configured. Installation provides instructions and assets, not application installation or proof of live compatibility. Back up custom skill changes outside discoverable skill directories; avoid duplicate copies of these four skill names. Verify discovery in a fresh session using the host's current supported workflow.

For Codex Work, installing through the Claude marketplace does not establish Codex skill discovery. Confirm the active skill location supported by the current Codex environment, then copy or symlink all four whole skill folders from this package into that location as siblings, preserving their references and assets. Do not assume a fixed installation path or leave duplicate older versions in other discoverable locations. Back up existing customizations first and verify discovery of all four names in a fresh Codex session.

FreeCAD and Bambu Studio must be available for their respective tasks. An existing suitable MCP bridge is preferred; discover actual schemas at runtime. The external FreeCAD Production Suite is a complementary source of methods, not bundled code or an automatically installed dependency. Report missing methods rather than silently installing software or pretending a namespaced skill is available.

To remove or revert, use the host's supported plugin removal/version workflow and restore any separately backed-up custom skills. This package does not alter existing CAD projects, upstream plugins or application settings by itself.

## Configurable defaults and illustrations

Structural joint rules, gusset counts, default cover shortlist and visual-first discussion are package defaults, not universal manufacturing standards or assumptions about every user. Explicit project requirements and user choices take precedence. Dimensions require local engineering review; no concept image establishes fit, strength, cooling, printability or service life.

The 10 bundled illustrations are AI-generated conceptual references, not validated CAD or production drawings. No new images were generated for this release. Only embedded caBX/C2PA correlation metadata was removed from the public copies; decoded pixel data is unchanged. Authenticated content credentials are therefore not retained; the AI-generated origin is disclosed here.

## Verification and licensing

See [VALIDATION.md](VALIDATION.md) for completed static checks and unperformed runtime tests, [CHANGELOG.md](CHANGELOG.md) for changes and [PROVENANCE.md](PROVENANCE.md) for public attribution and licensing boundaries. This package has not been qualified by live FreeCAD/MCP or Bambu Studio execution, printer operation or physical trials. CAD-ready, slice-reviewed and physically qualified are separate statuses.

The adapted Qwen skill retains its Apache-2.0 license and modification notice. No license for the original package materials and illustrations is declared in this release; do not interpret the Qwen license as licensing the entire package.
