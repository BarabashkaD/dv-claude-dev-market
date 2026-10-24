---
name: cad-visual-decisions
description: Compare and record significant CAD design choices with stable option IDs, visual or schematic cards, and explicit owner approval. Use before new mechanical or appearance-defining nodes when alternatives materially affect function, assembly, appearance, or printability; do not use for trivial edits or as a substitute for engineering validation.
---

# CAD visual decisions

Help the design owner choose among feasible alternatives before implementing a new significant CAD node. Make the choice easy to compare, preserve it in a project decision ledger, and carry it into the next CAD or print-preparation step without silently turning one choice into a global rule.

## When to activate

Use this skill when a new node has a meaningful choice of mechanism, interface, appearance, assembly method, or print consequence: for example a housing seam, hinge, latch, insert mount, rib family, foot, handle, cable entry, vent or panel.

Every NEW significant visible or functional choice needs an owner selection or explicit delegation, even when only one feasible option remains. Do not interrupt for a trivial fillet, a repeated instance of an already-approved identical node, a routine implementation step whose design decision is already recorded, or an autonomous parameter change that stays within approved limits and has no material behavior or appearance impact. If no genuine alternatives are feasible, say so and provide the best bounded recommendation instead of inventing options.

## Decision workflow

1. Map the new design nodes before implementing them. Group related choices and identify dependencies, affected datums, mating parts, constraints, and what has already been approved. Keep the map project-scoped.
2. Batch close decisions into a small review. Offer 3-5 materially different feasible options when that many exist; fewer is correct when space, function, process, or evidence rules out the rest. Use stable IDs such as `HINGE-A`, `HINGE-B`, and a revision when an option changes.
3. Separate the decision dimensions: mechanism, aesthetic finish, and parameters. Do not let a preference for one dimension silently select the others.
4. Show each option as a comparable card. Include the same scale and orientation where possible, exterior plus cutaway, motion, or assembly views when relevant, and the mating parts rather than an isolated latch or hinge. State the option ID/revision, functional difference, assembly and disassembly path, external appearance, retained hardware, CAD/geometric constraints, printing/material/process constraints, tradeoffs, and a recommended option with reasons.
5. Use real CAD previews or reliable schematic sources when available. Label conceptual diagrams as conceptual and distinguish them from geometry that was checked. For major or ambiguous nodes, prefer local alternatives on the actual model without rebuilding three complete products. If images cannot be produced, disclose that and give a structured text fallback; never imply visual approval that was not obtained.
6. Screen options for available space, interference, mating and assembly access, likely material/process feasibility, and known constraints before presenting them. Do not invent load capacities, clearances, tolerances, or print results. A selection is not strength, fit, printability, or safety validation.
7. Ask for the owner's selection by stable ID for every new significant visible or functional choice. Batch the question when alternatives are close, tradeoffs matter, or missing constraints affect several nodes. The owner may explicitly delegate selection; if delegated, choose the stated criteria and record that delegation rather than pretending the owner approved every tradeoff.
8. Implement only after the decision boundary is clear. For FreeCAD, design print-aware in the existing workflow first, prefer native high-level parametric operations through the already configured MCP, and use bounded scripts only when justified. Do not recreate opaque geometry or repeatedly iterate in a slicer before the CAD decision is settled.

## Decision ledger

Keep a project-local ledger when the work is more than a one-off question. For each selected node record:

```text
Node: <stable node ID and purpose>
Options reviewed: <IDs and revisions>
Selected: <ID and revision, or delegated criteria>
Parameters and datums: <values or references>
Constraints and rationale: <why this option fits the stated need>
Evidence checks: <CAD geometry: PASS/FAIL/NOT RUN; interference: PASS/FAIL/NOT RUN; assembly access: PASS/FAIL/NOT RUN; slice review: PASS/FAIL/NOT RUN; physical test: PASS/FAIL/NOT RUN>
Evidence revision/source: <model revision, material/settings, test revision or source; only if known>
Approval scope: <this node/instance or explicitly delegated scope>
Next review trigger: <what change requires a new choice>
```

Grow a concept catalog from useful patterns, but do not claim it exhausts all possible designs. A hinge decision applies to the recorded family, revision, parameters, and scope only; it does not establish a permanent user preference for unrelated hinges or projects. Reuse an approved identical instance without reprompting. Renew the choice when geometry, function, appearance, mating hardware, material, or process changes materially.

## Useful option families

Select only families relevant to the node. Common categories include:

- housing seams, joints, covers, and enclosure interfaces;
- hinges, slides, motion stops, and other motion interfaces;
- snaps, hooks, latches, and retention features;
- PCB, insert, screw, and boss mounts;
- ribs, gussets, and local supports;
- feet, handles, and grip features;
- cable entries and strain relief;
- ventilation, panels, windows, textures, and other appearance-defining features.

Keep mechanism, finish, and parameters distinct. For example, a closed bearing/knuckle hinge and a concealed hinge are different mechanism families even if both satisfy a closed-cover appearance goal.

## Boundaries and handoff

Record each evidence check independently as PASS, FAIL, or NOT RUN, with the relevant model/test revision or source. Concept discussion, CAD geometry, interference, assembly access, slicing, and physical testing are separate claims; passing one never implies another passed. If print feedback would change a selected mechanism, appearance, or major interface, return to the owner for a new decision and then run a dedicated CAD round. Preserve already-approved decisions while resolving only the changed node.

Use current, version-relevant official documentation for the actual CAD/MCP tools and trustworthy engineering sources for claims that need evidence. Do not invent APIs, capacities, or implementation support. Do not install a slicer, MCP server, application, or other dependency, upload a model, start a print, or dispatch a printer unless the user separately authorizes that action.
