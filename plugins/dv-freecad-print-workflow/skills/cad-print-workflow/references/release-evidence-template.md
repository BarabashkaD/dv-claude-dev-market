# Release evidence template

Use actual outcomes: PASS | FAIL | NOT RUN | NOT APPLICABLE (with reason). Do not replace missing raw evidence with a hand-written PASS.

## Identity
- CAD source path/revision and content hash where available:
- Export path/hash, units, mesh/export settings and part mapping:
- Bambu version/build and project path/hash:
- Printer/nozzle/material/process profiles, resolved settings/overrides:
- Object orientation/placement and plate mapping:

## Checks
For each check: scope/target parts, acceptance condition, actual result, raw report/log or image location, and limitations.
- CAD recompute, expected solids, geometric validity:
- Critical dimensions, interfaces, assembly/motion/access:
- Regeneration cases and per-part assertions; negative regressions recorded separately:
- Export scale, orientation, completeness and mesh integrity:
- Slicing exit/result status, full diagnostics and warnings:
- Layer review: thin features, gaps, supports, bridges and support access:
- Estimated print time/material, with source and no implied physical accuracy:
- Physical fit/print/strength/life qualification:

## Findings and readiness
- Outstanding findings / accepted tradeoffs / owner decision:
- CAD changes since last slice, if any:
- Status: CAD-ready, slice-reviewed, print-package-ready, or physically-qualified (state scope):
- Dispatch authorization: not included merely by preparing this record.
