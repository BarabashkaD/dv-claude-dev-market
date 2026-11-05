# Changelog

## 0.1.0

- Initial release: skill `proving-netlist-equivalence` with
  `netlist_equiv.py` (register-cut-point equivalence of two flat netgen
  Verilog netlists: exhaustive and BDD comparison, normalised flip-flop next
  state, exact register correspondence, one-sided duplicate aliasing) and
  `make_mutant.py` (one-LUT mutants to validate the checker).
- The checker refuses hierarchical netlists and unknown primitives, and maps
  unreadable input or an internal failure to exit code 2 so that a crash can
  never be read as NOT EQUIVALENT.
- Unit tests on synthetic netlists: self-compare, an equivalent refactor,
  four mutants, a wide-AND clock enable register, input errors and the CLI.
