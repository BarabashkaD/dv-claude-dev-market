# Upstream provenance and modification notice

This adapted skill is not an unmodified Qwen release.

- Upstream: https://github.com/QwenLM/Qwen-MM-Plugins/blob/ce46a1eb4e4ff81ed9ff4518e16901d840509d54/src/capabilities/freecad/skill/SKILL.md
- Pinned upstream commit: ce46a1eb4e4ff81ed9ff4518e16901d840509d54.
- Original Git blob: fb7af8cbbfd331160a0f89860f7ac0af86e5e00b.
- The upstream Apache-2.0 [LICENSE](../LICENSE) is retained unchanged.

Modified for package 1.1.0: narrowed to existing bridge operation; added MCP-preferred execution with bounded high-level native-script exceptions, sequential CAD-then-slicer routing, runtime capability checks, document safety and separate geometry/parametric evidence. The surrounding skill collection remains evolving and incomplete, with static checks only and no live FreeCAD/Bambu qualification.

Current tool schemas and verified state govern operations. This package contains neither a new MCP server nor production-suite code. Attribution does not grant installation, execution, publishing or print-dispatch authorization.
