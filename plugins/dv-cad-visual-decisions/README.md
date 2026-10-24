# CAD Visual Decisions · 1.0.0

An independent, CAD-general skill for presenting comparable alternatives before significant mechanical or appearance-defining design nodes, recording stable owner decisions, and carrying approved choices into print-aware CAD work.

Status: 1.0.0 is an initial, evolving skill. It provides decision guidance and ledger structure; it does not validate strength, fit, printability, safety, or physical performance.

## What it does

- Maps new significant nodes and batches 3-5 genuine alternatives when feasible.
- Uses stable option IDs and comparable option cards with mating-part, assembly, appearance, constraint, and tradeoff context.
- Preserves decisions by project, node, revision, parameters, datums, rationale, evidence status, and approval scope.
- Supports FreeCAD-first, existing-MCP-preferred work without installing tools or dispatching prints.

It does not create a universal design catalog, invent alternatives, silently apply one hinge choice globally, or treat a visual selection as engineering approval.

## Кратко по-русски

Перед важным узлом модели навык предлагает несколько реальных вариантов с устойчивыми ID, показывает различия и ждёт выбора владельца. Выбранный вариант записывается для конкретного проекта, узла и ревизии; повторные одинаковые узлы не требуют нового вопроса. Эскиз или визуальный выбор не заменяет проверку CAD, печать и физические испытания.

## Installation and integration

The repository-native marketplace exposes this plugin alongside the FreeCAD workflow. Use the host's supported marketplace flow; do not install duplicate copies through a standalone `.agents/skills` route and a plugin route at the same time. This package has no MCP server, installer, hook, or printer-control code and does not configure FreeCAD.

## License and provenance

This package contains original instructions for this repository and no copied third-party assets. The repository's existing marketplace licenses and attribution remain separate; no additional third-party license is claimed here.
