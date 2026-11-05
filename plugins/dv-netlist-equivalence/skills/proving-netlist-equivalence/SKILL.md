---
name: proving-netlist-equivalence
description: Use when a refactored Xilinx ISE/XST design must be shown to synthesize to unchanged logic - the bitstream changed after a hierarchy change, module move, wrapper or rename; no Conformal, Formality or Yosys equivalence flow is available; netgen Verilog netlists of both .ngc files can be produced; or XST register duplication and renumbered nets defeat a netlist diff.
---

# Proving netlist equivalence (ISE/XST)

## Overview

`scripts/netlist_equiv.py` (Python 3.8+, standard library) is a validated checker; do not write a new one. It compares two flat netgen netlists at register cut points: outputs of flip-flops, RAM, SRL, DSP, clock and black-box cells are free variables; every input of a matched cut cell and every output port is a checkpoint, compared exhaustively up to 16 variables, by BDD above. Registers match by instance name; duplicates merge only by exact proof.

**Core principle: a checker never seen failing on your netlists proves nothing.**

Not for Vivado flows, designs a formal tool can check, or intended logic changes (expect mismatches; review them).

## Procedure

`<skill>` is this skill's directory.

1. Build both versions with identical XST options and a flat netlist (`-keep_hierarchy no`).
2. `netgen -w -ofmt verilog old/top.ngc base.v`, likewise `new.v`.
3. `python -B <skill>/scripts/netlist_equiv.py --dump-types base.v new.v`: no `UNKNOWN`.
4. Validate the checker:
   - `netlist_equiv.py base.v base.v` must exit 0;
   - `make_mutant.py base.v mut.v --mode flip`, then `netlist_equiv.py base.v mut.v` must exit 1 and name the printed flip-flop; repeat with `--mode swap`.
5. `netlist_equiv.py base.v new.v --strip u_wrap/ > equiv.txt`, one `--strip` per instance prefix the refactor added. Exit 0 EQUIVALENT, 1 NOT EQUIVALENT, 2 no verdict.

## Reading the report

- `checkpoints compared: N (exhaustive, bdd, random)`: exhaustive and bdd are proofs; `random` (function over the BDD budget, 4096 random vectors) is evidence only. Retry with a larger `--bdd-budget`.
- Correspondence log `random fallback N`: N > 0 means those merges are unproven.
- `REGISTER CORRESPONDENCE CLASSES`: registers proven equal inside one netlist (XST copies `x_1`); `ALIASES`: one-sided copies folded into a partner.
- `MISMATCHES`: checkpoint (`r.D` raw pin, `r:NS` normalised next state), both nets, supports, a counterexample over cut variables, both values.
- `NOTES: raw FF pin differs, next state equal`: e.g. a reset moved between the R pin and the D logic; fine.
- `UNMATCHED CUT CELLS`: `USED` fails the run (renamed register, missing `--strip`); unused ones are listed, confirm they are dead.
- `undriven nets`: free variables (unconnected DSP PCIN); expect them on both sides.

## Common mistakes

| Mistake | Instead |
|---|---|
| Writing a parser/evaluator | Run the script |
| Trusting 0 mismatches unvalidated | Self-compare + mutants first |
| Merging registers by random signatures | Exact only: a wide-AND enable looks constant under thousands of vectors |
| Name-based netlist diff | XST renumbers nets; compare functions |
| Judging by MAP LUT counts or bitstream diff | Neither shows logic |
| Hand-parsing netgen | Escaped names end with a space, `\name [i]` is a bus bit, Coregen cores are black boxes, unknown primitives must abort |

## Limits

- Needs stable register and instance names; renaming beyond prefixes leaves `USED` unmatched cells.
- `random` checkpoints are evidence, not proof.
- Not checked: timing (run TRCE), pin and IO constraints (diff UCF and pad reports), black-box contents beyond their pins (diff the Coregen `.xco`/`.ngc`), initial RAM contents beyond INIT parameters, behaviour (simulate).
