# Historical provenance and modification notice

This operational skill is not an unmodified upstream release. It retains historical adapted material for attribution and licensing context; it has no Qwen runtime dependency.

- Historical upstream: https://github.com/QwenLM/Qwen-MM-Plugins/blob/ce46a1eb4e4ff81ed9ff4518e16901d840509d54/src/capabilities/freecad/skill/SKILL.md
- Historical upstream commit: ce46a1eb4e4ff81ed9ff4518e16901d840509d54.
- Historical source Git blob: fb7af8cbbfd331160a0f89860f7ac0af86e5e00b.
- The upstream Apache-2.0 [LICENSE](../LICENSE) is retained unchanged.

Modified for package 1.1.0: renamed as `freecad-mcp-operations`, narrowed to the existing bridge operation, and documented the version-scoped FreeCAD MCP reference contract with MCP-preferred execution, bounded high-level native-script exceptions, sequential CAD-then-slicer routing, runtime capability checks, document safety and separate geometry/parametric evidence. The surrounding skill collection remains evolving and incomplete, with static checks only and no live FreeCAD/Bambu qualification.

The documented FreeCAD MCP reference is not proof of local installation provenance. Verify current tool schemas, health and version before use; report mismatches and do not install, launch or substitute a different bridge. This package contains neither a new MCP server nor production-suite code. Attribution does not grant installation, execution, publishing or print-dispatch authorization.
