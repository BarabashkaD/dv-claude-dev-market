# dv-netlist-equivalence

`dv-netlist-equivalence` gives Claude a validated tool and a procedure for one
question: **does a refactored Xilinx ISE/XST design still synthesize to the
same logic?** It is meant for refactors that should not change behaviour (a
module moved, a wrapper added, a hierarchy reorganised, signals renamed) when
the bitstream nevertheless changed and no formal equivalence tool (Conformal,
Formality, a Yosys flow) is available.

The plugin contains one skill, `proving-netlist-equivalence`, with two
standard-library Python scripts:

- `scripts/netlist_equiv.py`: a register-cut-point equivalence checker for two
  flat netgen Verilog netlists (`netgen -w -ofmt verilog top.ngc out.v`).
- `scripts/make_mutant.py`: writes a one-LUT mutant of a netlist (flipped INIT
  bit or swapped inputs) so the checker can be seen to fail before its
  EQUIVALENT is trusted.

## Install

```text
/plugin marketplace add BarabashkaD/dv-claude-dev-market
/plugin install dv-netlist-equivalence@dv-claude-dev-market
```

Requirements: Python 3.8 or newer (standard library only) and the netgen tool
of Xilinx ISE 14.x to turn the two `.ngc` files into Verilog. The plugin does
not install or run ISE.

## How the checker works

- Parses the top module of each netlist (netgen escaped identifiers with a
  trailing space, bus bits `\name [i]`, concatenations, literals); refuses
  hierarchical netlists and unknown upper-case primitives (exit 2). Cell types
  with lower-case letters are Coregen black boxes; their pin directions are
  inferred from the netlist.
- Cut points: outputs of FD*/LD* flip-flops and latches, distributed RAM, SRL,
  block RAM, DSP48A1, PLL/DCM, global buffers, ODDR2/IDDR2/OSERDES2, IOBUF and
  black boxes, plus input ports. Undriven nets (for example unconnected DSP
  PCIN pins) become named free variables.
- Cut cells are matched by instance name after `--strip PREFIX` removal.
  Checkpoints are all inputs of matched cut cells and all output ports.
  Flip-flops of different types (FD vs FDR, FDRE vs FDE plus logic) are
  compared by their normalised behaviour: clock, async clear, async preset and
  next state.
- Each checkpoint is compared exhaustively when its support has at most 16
  variables, otherwise exactly with a BDD; only a function over the BDD node
  budget falls back to 4096 seeded random vectors, and the summary counts those
  checkpoints separately (`random`): evidence, not proof.
- Register correspondence inside each netlist (greatest fixpoint, exact BDD
  partition) folds XST register copies (`reg_1`, `reg_2`) into one
  representative. Random vectors only split classes, never merge them: a
  register with a 20 to 32 input AND clock enable looks constant under
  thousands of random vectors.

Exit codes: 0 EQUIVALENT, 1 NOT EQUIVALENT, 2 no verdict (usage error,
unreadable or unsupported netlist, internal failure).

## Quick use

```text
netgen -w -ofmt verilog old/top.ngc base.v
netgen -w -ofmt verilog new/top.ngc new.v
python -B netlist_equiv.py --dump-types base.v new.v
python -B netlist_equiv.py base.v base.v                  # must exit 0
python -B make_mutant.py base.v mut.v --mode flip
python -B netlist_equiv.py base.v mut.v                   # must exit 1
python -B netlist_equiv.py base.v new.v --strip u_wrap/ > equiv.txt
```

See `skills/proving-netlist-equivalence/SKILL.md` for how to read the report
and for the limits.

## Limits

- Assumes stable register and instance names between the two builds (plus
  removable prefixes). It is not a general sequential equivalence checker:
  retiming, state re-encoding or renamed registers show up as unmatched cells.
- Does not check timing (run TRCE), IO placement and constraints (diff the UCF
  and the pad report), the contents of Coregen black boxes beyond their pins,
  or behaviour (simulate).
- The cell library covers the Spartan-6 UNISIM primitives seen in ISE 14.x
  netlists; other primitives abort the run by name and need a table entry.

## Tests

```text
python -m unittest discover -s plugins/dv-netlist-equivalence/tests -v
```

The tests use small synthetic netgen-style netlists generated in
`tests/netgen_fixtures.py`; no real design files are included. See
`VALIDATION.md`.
