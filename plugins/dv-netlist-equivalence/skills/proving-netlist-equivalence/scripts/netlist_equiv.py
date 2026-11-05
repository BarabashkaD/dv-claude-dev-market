#!/usr/bin/env python3
"""netlist_equiv.py - register-cut-point equivalence check of two post-synthesis
netlists of the same FPGA design.

Input: flat Verilog netlists written by Xilinx netgen from the XST output,
    netgen -w -ofmt verilog <top>.ngc <out>.v
(ISE 14.x; the cell library covers the Spartan-6 UNISIM primitives, see
CUT_OUT / comb_nodes; any other upper-case primitive aborts the run).
Python 3.8 or newer, standard library only.

Usage:
    python -B netlist_equiv.py BASE.v NEW.v [--strip PREFIX]... [--seed N]
                 [--max-exhaustive 16] [--random 4096] [--bdd-budget 200000]
                 [--max-notes 20]
    python -B netlist_equiv.py --dump-types FILE.v [FILE.v ...]
    python -B netlist_equiv.py --help

  --strip PREFIX   remove an instance-name prefix before matching (repeatable),
                   e.g. --strip u_core/ when the refactor wrapped logic in a new
                   instance u_core.
  --dump-types     list the cell types of the files and how they are classified
                   (UNKNOWN types would abort a comparison).

Exit codes:
    0  EQUIVALENT: no mismatch, no failed alias check, no cell-level issue and
       no unmatched cut cell that feeds a checkpoint.
    1  NOT EQUIVALENT (see the MISMATCHES / CELL-LEVEL ISSUES / UNMATCHED
       sections of the report).
    2  no verdict: usage error, unreadable or unsupported netlist (unknown
       primitive, hierarchical netlist, parse error) or an internal failure.

Method
  * Each file must hold exactly one design module (a flat netlist) plus the
    `glbl` module that netgen appends (ignored).  A netlist with several
    modules (XST keep_hierarchy) is refused.
  * Cut points (free variables) are the output pins of sequential and black-box
    cells (FD*/LD*, distributed RAM, SRL, RAMB, DSP48, PLL/DCM, BUFG*, BUFIO2*,
    ODDR2/IDDR2/OSERDES2, IOBUF/OBUFT, Coregen black boxes) and the top-level
    input/inout ports.  A variable is called `<instance>.<pin>` (instance name
    after --strip) or `port:<name>`.
  * Combinational cells (LUT1..6, LUT6_2, MUXF5..8, MUXCY, XORCY, INV, BUF,
    IBUF/IBUFG/OBUF/OBUFDS, GND, VCC, assign aliases) are evaluated bit-parallel
    with Python ints as bit vectors.  An unknown UNISIM-style (upper-case)
    primitive aborts the run; a cell type that contains lower-case letters is
    a black box (Coregen core) whose pin directions are inferred from the
    netlist (a pin bit is an output if nothing else drives its net).
  * Cut cells are matched by normalised instance name.  Checkpoints are all
    input pins of matched cut cells and all top-level output ports.  For
    flip-flops/latches the decisive comparison is the normalised behaviour:
    clock/gate pin, asynchronous clear, asynchronous preset and the
    synchronous next state (e.g. FDRE: R ? 0 : (CE ? D : Q)), so FD vs FDR
    etc. compare correctly.  If both cells have the same type, the raw pins
    are compared first; a raw pin difference whose next state is still equal
    is reported as a note, not as a mismatch.
  * Supports (sets of cut variables) are computed structurally.  If the union
    support of a checkpoint has <= --max-exhaustive variables it is checked
    exhaustively, otherwise exactly with a BDD (node budget --bdd-budget per
    function); only a function over the budget falls back to --random random
    assignments (fixed seed) plus the all-zero and the all-one assignment.
    Such checkpoints are counted as `random` in the summary: evidence, not
    proof.
  * Register correspondence inside each netlist (greatest fixpoint): FD*/LD*
    cells start in classes per (latch/FF, clock polarity, INIT); every member
    output is replaced by the class representative and classes are split
    while CLK, CLR, PRE or the next state of their members differ (random
    signatures only split; the final partition is exact, by BDD).  Random
    vectors are never used to merge: a register whose clock enable is a wide
    AND looks constant under any practical number of random vectors.
    Representative: the smallest name present in both netlists, else the
    smallest name.  The member outputs are then replaced by the
    representative variable (per-netlist alias maps) before the comparison.
  * Register duplicates: a cut cell present in one netlist only is aliased to a
    matched cell of the same netlist if it has the same type and parameters
    and the same input functions (optimistic fixpoint: candidates by name
    `<reg>_<n>...`, then by input signature; a candidate is dropped when its
    inputs differ; the final alias set is re-verified with the same
    exhaustive/BDD check).  The alias output variable is replaced by the
    partner's variable everywhere.
  * Unmatched cut cells that no checkpoint uses are listed explicitly and do
    not fail the run.
"""

import argparse
import random
import re
import sys
import time
from collections import defaultdict, Counter

# --------------------------------------------------------------------------
# Tokenizer / parser
# --------------------------------------------------------------------------

TOKEN_RE = re.compile(r"""
   (?P<ws>\s+)
  |(?P<lc>//[^\n]*)
  |(?P<bc>/\*.*?\*/)
  |(?P<esc>\\\S+)
  |(?P<num>\d*'[sS]?[bBoOdDhH][0-9a-fA-FxXzZ_?]+|\d+\.\d+(?:[eE][-+]?\d+)?|\d+)
  |(?P<word>[A-Za-z_][A-Za-z0-9_$]*)
  |(?P<str>"[^"]*")
  |(?P<p>[()\[\]{},;.#:=@*+\-`/])
""", re.X | re.S)

MODULE_RE = re.compile(r'^[ \t]*(?:macro)?module\s+(\\\S+|[A-Za-z_][A-Za-z0-9_$]*)', re.M)

DECL_KW = {'input', 'output', 'inout', 'wire', 'tri', 'reg', 'supply0',
           'supply1', 'wand', 'wor', 'tri0', 'tri1'}
UNSUPPORTED_KW = {'defparam', 'initial', 'always', 'specify', 'parameter',
                  'localparam', 'generate', 'function', 'task'}


class NetlistError(Exception):
    pass


def tokenize_top(path):
    """Tokens of the first module: list of (kind, text); kind in id/w/num/str/p.
    'id' is an escaped identifier (backslash removed), 'w' a plain word."""
    with open(path, encoding='latin-1') as f:
        text = f.read()
    mods = [m.lstrip('\\') for m in MODULE_RE.findall(text)]
    design = [m for m in mods if m != 'glbl']
    if len(design) > 1:
        raise NetlistError('%s: %d modules (%s): hierarchical netlist; synthesize '
                           'flat (XST -keep_hierarchy no) or write a flat netlist'
                           % (path, len(design), ', '.join(design[:5])))
    toks = []
    pos, n = 0, len(text)
    match = TOKEN_RE.match
    started = False
    while pos < n:
        mo = match(text, pos)
        if not mo:
            raise NetlistError('%s: cannot tokenize at offset %d: %r'
                               % (path, pos, text[pos:pos + 60]))
        pos = mo.end()
        k = mo.lastgroup
        if k in ('ws', 'lc', 'bc'):
            continue
        t = mo.group()
        if k == 'esc':
            toks.append(('id', t[1:]))
            continue
        if k == 'word':
            if not started:
                if t == 'module':
                    started = True
                    toks.append(('w', t))
                continue
            if t == 'endmodule':
                return toks
            toks.append(('w', t))
            continue
        if not started:
            continue
        toks.append((k, t))
    raise NetlistError('%s: no complete module found' % path)


def literal_bits(lit):
    """Verilog literal -> list of constant net names, MSB first."""
    if "'" not in lit:
        if '.' in lit:
            raise NetlistError('real literal used as a net: %s' % lit)
        v = int(lit)
        return ['#1' if (v >> i) & 1 else '#0' for i in range(31, -1, -1)]
    w, rest = lit.split("'", 1)
    width = int(w) if w else 32
    rest = rest.lstrip('sS')
    base, digits = rest[0].lower(), rest[1:].replace('_', '').lower()
    bits = []  # LSB first
    if base == 'd':
        v = int(digits)
        bits = [(v >> i) & 1 for i in range(width)]
        bits = ['#1' if b else '#0' for b in bits]
    else:
        per = {'b': 1, 'o': 3, 'h': 4}[base]
        for ch in reversed(digits):
            if ch in 'xz?':
                bits.extend(['#' + ('z' if ch == '?' else ch)] * per)
            else:
                v = int(ch, 16)
                bits.extend(['#1' if (v >> i) & 1 else '#0' for i in range(per)])
    bits = (bits + ['#0'] * width)[:width]
    return list(reversed(bits))


def literal_int(lit):
    lit = lit.strip()
    if "'" not in lit:
        return int(lit)
    v = 0
    for b in literal_bits(lit):
        v = (v << 1) | (1 if b == '#1' else 0)
    return v


def bitname(name, idx):
    return '%s [%d]' % (name, idx)


def range_list(msb, lsb):
    if msb >= lsb:
        return list(range(msb, lsb - 1, -1))
    return list(range(msb, lsb + 1))


class Cell(object):
    __slots__ = ('typ', 'name', 'params', 'pins', 'norm')

    def __init__(self, typ, name, params, pins):
        self.typ = typ
        self.name = name
        self.params = params
        self.pins = pins      # list of (pinbit, net)
        self.norm = name


class Parsed(object):
    def __init__(self):
        self.module = None
        self.ports = []       # (name, dir, [bit nets])
        self.widths = {}      # declared bus name -> list of indices
        self.cells = []
        self.assigns = []     # (lhs net, rhs net)


def parse_netlist(path):
    toks = tokenize_top(path)
    P = Parsed()
    i = [0]
    N = len(toks)

    def peek(o=0):
        j = i[0] + o
        return toks[j] if j < N else ('eof', '')

    def nxt():
        t = peek()
        i[0] += 1
        return t

    def expect(text):
        t = nxt()
        if t[1] != text or t[0] not in ('p', 'w'):
            raise NetlistError('%s: expected %r, got %r near token %d'
                               % (path, text, t, i[0]))
        return t

    def ident():
        t = nxt()
        if t[0] not in ('id', 'w'):
            raise NetlistError('%s: expected identifier, got %r' % (path, t))
        return t[1]

    def number():
        t = nxt()
        if t[0] != 'num':
            raise NetlistError('%s: expected number, got %r' % (path, t))
        return int(t[1])

    def parse_expr():
        """-> (list of nets MSB first, is_vector)"""
        t = peek()
        if t == ('p', '{'):
            nxt()
            if peek()[0] == 'num' and peek(1) == ('p', '{'):
                rep = number()
                bits, _ = parse_expr()
                expect('}')
                return bits * rep, True
            bits = []
            while True:
                b, _ = parse_expr()
                bits.extend(b)
                t2 = nxt()
                if t2 == ('p', '}'):
                    break
                if t2 != ('p', ','):
                    raise NetlistError('%s: bad concatenation near %r' % (path, t2))
            return bits, True
        if t[0] == 'num':
            nxt()
            b = literal_bits(t[1])
            return b, len(b) > 1
        name = ident()
        if peek() == ('p', '['):
            nxt()
            a = number()
            if peek() == ('p', ':'):
                nxt()
                b = number()
                expect(']')
                return [bitname(name, k) for k in range_list(a, b)], True
            expect(']')
            return [bitname(name, a)], False
        if name in P.widths:
            return [bitname(name, k) for k in P.widths[name]], True
        return [name], False

    # module header
    expect('module')
    P.module = ident()
    if peek() == ('p', '('):
        depth = 0
        while True:
            t = nxt()
            if t == ('p', '('):
                depth += 1
            elif t == ('p', ')'):
                depth -= 1
                if depth == 0:
                    break
    expect(';')

    while i[0] < N:
        t = peek()
        if t[0] == 'w' and t[1] in DECL_KW:
            kw = nxt()[1]
            if peek() == ('p', '('):          # strength
                while nxt() != ('p', ')'):
                    pass
            rng = None
            if peek() == ('p', '['):
                nxt()
                a = number()
                expect(':')
                b = number()
                expect(']')
                rng = range_list(a, b)
            while True:
                name = ident()
                if rng is not None:
                    P.widths[name] = rng
                if kw in ('input', 'output', 'inout'):
                    bits = [bitname(name, k) for k in rng] if rng is not None else [name]
                    P.ports.append((name, kw, bits))
                t2 = nxt()
                if t2 == ('p', ';'):
                    break
                if t2 != ('p', ','):
                    raise NetlistError('%s: bad declaration near %r' % (path, t2))
            continue
        if t[0] == 'w' and t[1] == 'assign':
            nxt()
            if peek() == ('p', '('):
                while nxt() != ('p', ')'):
                    pass
            while True:
                lhs, _ = parse_expr()
                expect('=')
                rhs, _ = parse_expr()
                if len(rhs) < len(lhs):
                    rhs = ['#0'] * (len(lhs) - len(rhs)) + rhs
                rhs = rhs[len(rhs) - len(lhs):]
                for l, r in zip(lhs, rhs):
                    P.assigns.append((l, r))
                t2 = nxt()
                if t2 == ('p', ';'):
                    break
                if t2 != ('p', ','):
                    raise NetlistError('%s: bad assign near %r' % (path, t2))
            continue
        if t[0] == 'w' and t[1] in UNSUPPORTED_KW:
            raise NetlistError('%s: unsupported construct %r' % (path, t[1]))
        # instance
        typ = ident()
        params = {}
        if peek() == ('p', '#'):
            nxt()
            expect('(')
            while True:
                if peek() == ('p', ')'):
                    nxt()
                    break
                expect('.')
                pname = ident()
                expect('(')
                depth, val = 1, []
                while True:
                    t2 = nxt()
                    if t2 == ('p', '('):
                        depth += 1
                    elif t2 == ('p', ')'):
                        depth -= 1
                        if depth == 0:
                            break
                    val.append(t2[1])
                params[pname] = ''.join(val)
                t2 = nxt()
                if t2 == ('p', ')'):
                    break
                if t2 != ('p', ','):
                    raise NetlistError('%s: bad parameter list of %s near %r'
                                       % (path, typ, t2))
        name = ident()
        expect('(')
        pins = []
        if peek() == ('p', ')'):
            nxt()
        else:
            while True:
                t2 = peek()
                if t2 != ('p', '.'):
                    raise NetlistError('%s: positional connection in %s %s'
                                       % (path, typ, name))
                nxt()
                pin = ident()
                expect('(')
                if peek() == ('p', ')'):
                    nxt()
                else:
                    bits, vec = parse_expr()
                    expect(')')
                    if vec or len(bits) > 1:
                        L = len(bits)
                        for j, b in enumerate(bits):
                            pins.append(('%s[%d]' % (pin, L - 1 - j), b))
                    else:
                        pins.append((pin, bits[0]))
                t2 = nxt()
                if t2 == ('p', ')'):
                    break
                if t2 != ('p', ','):
                    raise NetlistError('%s: bad pin list of %s near %r'
                                       % (path, name, t2))
        expect(';')
        P.cells.append(Cell(typ, name, params, pins))
    return P


# --------------------------------------------------------------------------
# Cell library
# --------------------------------------------------------------------------

FF_RE = re.compile(r'^(FD|LD)(R?)(S?)(C?)(P?)(E?)(_1)?$')


class FFInfo(object):
    __slots__ = ('latch', 'neg', 'clk', 'ce', 'sync', 'clr', 'pre', 'init_default')

    def __init__(self, typ):
        m = FF_RE.match(typ)
        kind, r, s, c, p, e, neg = m.groups()
        self.latch = kind == 'LD'
        self.neg = bool(neg)
        self.clk = 'G' if self.latch else 'C'
        self.ce = ('GE' if self.latch else 'CE') if e else None
        self.sync = []
        if r:
            self.sync.append(('R', 0))
        if s:
            self.sync.append(('S', 1))
        self.clr = bool(c)
        self.pre = bool(p)
        self.init_default = '1' if (s or p) and not (r or c) else '0'


def ff_info(typ):
    m = FF_RE.match(typ)
    if not m:
        return None
    kind, r, s, c, p, e, neg = m.groups()
    if kind == 'LD' and (r or s):
        return None
    if (r or s) and (c or p):
        return None
    return FFInfo(typ)


_RAM_D = {'SPO', 'DPO'}
CUT_OUT = {
    'RAM16X1D': _RAM_D, 'RAM32X1D': _RAM_D, 'RAM64X1D': _RAM_D, 'RAM128X1D': _RAM_D,
    'RAM16X1D_1': _RAM_D,
    'RAM16X1S': {'O'}, 'RAM32X1S': {'O'}, 'RAM64X1S': {'O'}, 'RAM128X1S': {'O'},
    'RAM256X1S': {'O'}, 'RAM16X1S_1': {'O'}, 'RAM32X1S_1': {'O'}, 'RAM64X1S_1': {'O'},
    'RAM16X2S': {'O0', 'O1'}, 'RAM32X2S': {'O0', 'O1'}, 'RAM64X2S': {'O0', 'O1'},
    'RAM16X4S': {'O0', 'O1', 'O2', 'O3'}, 'RAM16X8S': {'O'}, 'RAM32X4S': {'O0', 'O1', 'O2', 'O3'},
    'RAM32X8S': {'O'},
    'RAM32M': {'DOA', 'DOB', 'DOC', 'DOD'}, 'RAM64M': {'DOA', 'DOB', 'DOC', 'DOD'},
    'SRL16': {'Q'}, 'SRL16E': {'Q'}, 'SRL16_1': {'Q'}, 'SRL16E_1': {'Q'},
    'SRLC16': {'Q', 'Q15'}, 'SRLC16E': {'Q', 'Q15'}, 'SRLC16_1': {'Q', 'Q15'},
    'SRLC16E_1': {'Q', 'Q15'}, 'SRLC32E': {'Q', 'Q31'},
    'RAMB8BWER': {'DOADO', 'DOBDO', 'DOPADOP', 'DOPBDOP'},
    'RAMB16BWER': {'DOA', 'DOB', 'DOPA', 'DOPB'},
    'DSP48A1': {'BCOUT', 'PCOUT', 'CARRYOUT', 'CARRYOUTF', 'M', 'P'},
    'PLL_BASE': {'CLKFBOUT', 'CLKOUT0', 'CLKOUT1', 'CLKOUT2', 'CLKOUT3', 'CLKOUT4',
                 'CLKOUT5', 'LOCKED'},
    'PLL_ADV': {'CLKFBOUT', 'CLKOUT0', 'CLKOUT1', 'CLKOUT2', 'CLKOUT3', 'CLKOUT4',
                'CLKOUT5', 'LOCKED', 'CLKFBDCM', 'CLKOUTDCM0', 'CLKOUTDCM1',
                'CLKOUTDCM2', 'CLKOUTDCM3', 'CLKOUTDCM4', 'CLKOUTDCM5', 'DO', 'DRDY'},
    'DCM_SP': {'CLK0', 'CLK180', 'CLK270', 'CLK2X', 'CLK2X180', 'CLK90', 'CLKDV',
               'CLKFX', 'CLKFX180', 'LOCKED', 'PSDONE', 'STATUS'},
    'DCM_CLKGEN': {'CLKFX', 'CLKFX180', 'CLKFXDV', 'LOCKED', 'PROGDONE', 'STATUS'},
    'BUFG': {'O'}, 'BUFGP': {'O'}, 'BUFGCE': {'O'}, 'BUFGCE_1': {'O'}, 'BUFGMUX': {'O'},
    'BUFGMUX_1': {'O'}, 'BUFH': {'O'}, 'BUFIO2FB': {'O'},
    'BUFIO2': {'DIVCLK', 'IOCLK', 'SERDESSTROBE'},
    'BUFPLL': {'IOCLK', 'LOCK', 'SERDESSTROBE'},
    'ODDR2': {'Q'}, 'IDDR2': {'Q0', 'Q1'},
    'OSERDES2': {'OQ', 'SHIFTOUT1', 'SHIFTOUT2', 'SHIFTOUT3', 'SHIFTOUT4', 'TQ'},
    'IODELAY2': {'BUSY', 'DATAOUT', 'DATAOUT2', 'DOUT', 'TOUT'},
    'IOBUF': {'O'}, 'OBUFT': {'O'}, 'IOBUFDS': {'O'}, 'OBUFTDS': {'O', 'OB'},
}
CUT_IGNORE_PINS = {'IOBUF': {'IO'}, 'IOBUFDS': {'IO', 'IOB'}}
IGNORE_TYPES = {'PULLUP', 'PULLDOWN', 'KEEPER'}
BUF_TYPES = {'BUF', 'IBUF', 'IBUFG', 'OBUF', 'IBUFDS', 'IBUFGDS'}

BB_OUT_RE = re.compile(r'^(dout[ab]?|q|full|empty|almost_full|almost_empty|valid|'
                       r'overflow|underflow|data_count|rd_data_count|wr_data_count|'
                       r'prog_full|prog_empty|wr_ack|sbiterr|dbiterr|locked|'
                       r'clk_out\d*)$', re.I)

LUT_RE = re.compile(r'^LUT([1-6])(_L|_D)?$')
MUXF_RE = re.compile(r'^MUXF[5-8](_L|_D)?$')
MUXCY_RE = re.compile(r'^MUXCY(_L|_D)?$')
XORCY_RE = re.compile(r'^XORCY(_L)?$')


def comb_nodes(cell):
    """Combinational cell -> list of (out pin, op, [in pins], param), or None."""
    t = cell.typ
    m = LUT_RE.match(t)
    if m:
        k = int(m.group(1))
        init = literal_int(cell.params.get('INIT', "0")) & ((1 << (1 << k)) - 1)
        ins = ['I%d' % j for j in range(k)]
        outs = {'': ['O'], '_L': ['LO'], '_D': ['O', 'LO']}[m.group(2) or '']
        return [(o, 'LUT', ins, init) for o in outs]
    if t == 'LUT6_2':
        init = literal_int(cell.params.get('INIT', "0")) & ((1 << 64) - 1)
        return [('O6', 'LUT', ['I%d' % j for j in range(6)], init),
                ('O5', 'LUT', ['I%d' % j for j in range(5)], init & 0xFFFFFFFF)]
    m = MUXF_RE.match(t)
    if m:
        outs = {'': ['O'], '_L': ['LO'], '_D': ['O', 'LO']}[m.group(1) or '']
        return [(o, 'MUX', ['S', 'I0', 'I1'], None) for o in outs]
    m = MUXCY_RE.match(t)
    if m:
        outs = {'': ['O'], '_L': ['LO'], '_D': ['O', 'LO']}[m.group(1) or '']
        return [(o, 'MUX', ['S', 'DI', 'CI'], None) for o in outs]
    m = XORCY_RE.match(t)
    if m:
        outs = {'': ['O'], '_L': ['LO']}[m.group(1) or '']
        return [(o, 'XOR', ['CI', 'LI'], None) for o in outs]
    if t == 'INV':
        return [('O', 'INV', ['I'], None)]
    if t in BUF_TYPES:
        return [('O', 'BUF', ['I'], None)]
    if t == 'OBUFDS':
        return [('O', 'BUF', ['I'], None), ('OB', 'INV', ['I'], None)]
    return None


def classify(typ):
    if typ in ('GND', 'VCC'):
        return 'const'
    if typ in IGNORE_TYPES:
        return 'ignore'
    if ff_info(typ) is not None:
        return 'ff'
    if typ in CUT_OUT:
        return 'cut'
    if comb_nodes(Cell(typ, '', {}, [])) is not None:
        return 'comb'
    if re.search(r'[a-z]', typ):
        return 'bb'
    return None


def pin_base(pinbit):
    k = pinbit.find('[')
    return pinbit if k < 0 else pinbit[:k]


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------

class CutCell(object):
    __slots__ = ('typ', 'raw', 'norm', 'params', 'inputs', 'outputs', 'ff', 'kind')

    def __init__(self, cell, kind):
        self.typ = cell.typ
        self.raw = cell.name
        self.norm = cell.norm
        self.params = cell.params
        self.inputs = {}      # pinbit -> net id
        self.outputs = {}     # pinbit -> var name
        self.ff = ff_info(cell.typ) if kind == 'ff' else None
        self.kind = kind


class Model(object):
    def __init__(self, label, parsed, strip):
        self.label = label
        self.net_id = {}
        self.net_name = []
        self.drv = []
        self.nodes = {}
        self.cuts = {}
        self.out_ports = []    # (checkpoint name, net id)
        self.port_dirs = {}
        self.type_counts = Counter()
        self.undriven_used = set()
        self.warnings = []
        self._build(parsed, strip)

    def net(self, name):
        i = self.net_id.get(name)
        if i is None:
            i = len(self.net_name)
            self.net_id[name] = i
            self.net_name.append(name)
            d = None
            if name.startswith('#'):
                d = ('c', 1 if name == '#1' else 0)
                if name in ('#x', '#z'):
                    self.warnings.append('constant %s treated as 0' % name)
            self.drv.append(d)
        return i

    def const(self, v):
        return self.net('#1' if v else '#0')

    def set_drv(self, nid, d, who):
        if self.drv[nid] is not None:
            raise NetlistError('%s: net %r has two drivers (%r, %s)'
                               % (self.label, self.net_name[nid], self.drv[nid], who))
        self.drv[nid] = d

    def _build(self, P, strip):
        inouts = []
        for name, d, bits in P.ports:
            for b in bits:
                cpname = 'port:' + b.replace(' [', '[')
                self.port_dirs[cpname] = d
                nid = self.net(b)
                if d == 'input':
                    self.set_drv(nid, ('v', cpname), 'port')
                elif d == 'inout':
                    inouts.append((cpname, nid))
                else:
                    self.out_ports.append((cpname, nid))
        for l, r in P.assigns:
            li, ri = self.net(l), self.net(r)
            self.set_drv(li, ('n',), 'assign')
            self.nodes[li] = ('BUF', (ri,), None)
        unknown = Counter()
        bbs = []
        for c in P.cells:
            self.type_counts[c.typ] += 1
            norm = c.name
            changed = True
            while changed:
                changed = False
                for s in strip:
                    if s and norm.startswith(s):
                        norm = norm[len(s):]
                        changed = True
            c.norm = norm
            k = classify(c.typ)
            if k is None:
                unknown[c.typ] += 1
                continue
            if k == 'ignore':
                continue
            pins = dict(c.pins)
            if k == 'const':
                pin = 'G' if c.typ == 'GND' else 'P'
                if pin in pins:
                    self.set_drv(self.net(pins[pin]), ('c', 1 if c.typ == 'VCC' else 0), c.name)
                continue
            if k == 'comb':
                for out, op, ins, param in comb_nodes(c):
                    if out not in pins:
                        continue
                    in_ids = []
                    for p in ins:
                        if p not in pins:
                            self.warnings.append('%s %s: unconnected input %s treated as 0'
                                                 % (c.typ, c.name, p))
                            in_ids.append(self.const(0))
                        else:
                            in_ids.append(self.net(pins[p]))
                    o = self.net(pins[out])
                    self.set_drv(o, ('n',), c.name)
                    self.nodes[o] = (op, tuple(in_ids), param)
                continue
            if c.norm in self.cuts:
                raise NetlistError('%s: two cut cells with normalised name %r'
                                   % (self.label, c.norm))
            cc = CutCell(c, k)
            self.cuts[c.norm] = cc
            if k == 'bb':
                bbs.append((c, cc))
                continue
            outs = {'Q'} if k == 'ff' else CUT_OUT[c.typ]
            ign = CUT_IGNORE_PINS.get(c.typ, set())
            for pb, net in c.pins:
                base = pin_base(pb)
                if base in ign:
                    continue
                nid = self.net(net)
                if base in outs:
                    v = '%s.%s' % (c.norm, pb)
                    cc.outputs[pb] = v
                    self.set_drv(nid, ('v', v), c.name)
                else:
                    cc.inputs[pb] = nid
        if unknown:
            raise NetlistError('%s: unknown primitive type(s), refusing to guess: %s'
                               % (self.label, ', '.join('%s (x%d)' % kv for kv in sorted(unknown.items()))))
        # inout ports: driven by a cell (OBUF used as output) -> output
        # checkpoint; otherwise (IOBUF IO pin, input use) -> free variable
        for cpname, nid in inouts:
            if self.drv[nid] is None:
                self.drv[nid] = ('v', cpname)
            else:
                self.out_ports.append((cpname, nid))
        # black boxes: infer pin directions
        cand = defaultdict(list)
        for c, cc in bbs:
            for pb, net in c.pins:
                nid = self.net(net)
                if self.drv[nid] is None:
                    cand[nid].append((cc, pb))
                else:
                    cc.inputs[pb] = nid
        for nid, lst in cand.items():
            if len(lst) > 1:
                outs = [x for x in lst if BB_OUT_RE.match(pin_base(x[1]))]
                if len(outs) != 1:
                    raise NetlistError('%s: cannot infer the driver of net %r among black-box pins %s'
                                       % (self.label, self.net_name[nid],
                                          ['%s.%s' % (x[0].raw, x[1]) for x in lst]))
            else:
                outs = lst
            ocell, opb = outs[0]
            v = '%s.%s' % (ocell.norm, opb)
            ocell.outputs[opb] = v
            self.drv[nid] = ('v', v)
            for cc, pb in lst:
                if (cc, pb) != (ocell, opb):
                    cc.inputs[pb] = nid
        # undriven nets used by logic become variables; the variable is named
        # after the cut-cell pin it feeds (net names are not stable)
        sinks = defaultdict(list)
        for cc in self.cuts.values():
            for pb, nid in cc.inputs.items():
                if self.drv[nid] is None:
                    sinks[nid].append('%s.%s' % (cc.norm, pb))
        for nid, d in enumerate(self.drv):
            if d is None:
                s = sorted(sinks.get(nid, []))
                v = 'undriven:' + (s[0] if s else self.net_name[nid])
                self.drv[nid] = ('v', v)
                self.undriven_used.add(v)


# --------------------------------------------------------------------------
# Evaluation
# --------------------------------------------------------------------------

FULL = [(1 << (1 << k)) - 1 for k in range(7)]


def lut_eval(init, ins, M):
    def rec(init, k):
        if init == 0:
            return 0
        if init == FULL[k]:
            return M
        k -= 1
        lo = init & FULL[k]
        hi = init >> (1 << k)
        if lo == hi:
            return rec(lo, k)
        x = ins[k]
        return (x & rec(hi, k)) | ((x ^ M) & rec(lo, k))
    return rec(init, len(ins))


class BddLimit(Exception):
    pass


class BDD(object):
    """Minimal ROBDD (no complement edges).  Node 0 = false, 1 = true; the
    variable order is the global variable index (smaller index on top).
    mark() starts a per-checkpoint node budget; exceeding it raises BddLimit."""
    TERM = 1 << 60

    def __init__(self, budget, cap):
        self.v = [self.TERM, self.TERM]
        self.lo = [0, 1]
        self.hi = [0, 1]
        self.unique = {}
        self.cache = {}
        self.budget = budget
        self.cap = cap
        self.start = 2
        self.one = 1
        self.zero = 0

    def size(self):
        return len(self.v)

    def mark(self):
        self.start = len(self.v)

    def mk(self, v, lo, hi):
        if lo == hi:
            return lo
        key = (v, lo, hi)
        n = self.unique.get(key)
        if n is None:
            n = len(self.v)
            if n - self.start > self.budget or n > self.cap:
                raise BddLimit()
            self.v.append(v)
            self.lo.append(lo)
            self.hi.append(hi)
            self.unique[key] = n
        return n

    def var(self, i):
        return self.mk(i, 0, 1)

    def ite(self, f, g, h):
        if f == 1:
            return g
        if f == 0:
            return h
        if g == h:
            return g
        if g == 1 and h == 0:
            return f
        key = (f, g, h)
        r = self.cache.get(key)
        if r is not None:
            return r
        V, LO, HI = self.v, self.lo, self.hi
        top = min(V[f], V[g], V[h])
        if V[f] == top:
            f0, f1 = LO[f], HI[f]
        else:
            f0 = f1 = f
        if V[g] == top:
            g0, g1 = LO[g], HI[g]
        else:
            g0 = g1 = g
        if V[h] == top:
            h0, h1 = LO[h], HI[h]
        else:
            h0 = h1 = h
        r = self.mk(top, self.ite(f0, g0, h0), self.ite(f1, g1, h1))
        self.cache[key] = r
        return r

    def not_(self, f):
        return self.ite(f, 0, 1)

    def and_(self, f, g):
        return self.ite(f, g, 0)

    def or_(self, f, g):
        return self.ite(f, 1, g)

    def xor(self, f, g):
        return self.ite(f, self.not_(g), g)

    def mux(self, s, a1, a0):
        return self.ite(s, a1, a0)

    def lut(self, init, ins):
        def rec(init, k):
            if init == 0:
                return 0
            if init == FULL[k]:
                return 1
            k -= 1
            lo = init & FULL[k]
            hi = init >> (1 << k)
            if lo == hi:
                return rec(lo, k)
            return self.ite(ins[k], rec(hi, k), rec(lo, k))
        return rec(init, len(ins))

    def sat_one(self, f):
        """One satisfying assignment {var index: bit} of f (f != 0)."""
        a = {}
        while f > 1:
            if self.hi[f] != 0:
                a[self.v[f]] = 1
                f = self.hi[f]
            else:
                a[self.v[f]] = 0
                f = self.lo[f]
        return a

    def evaluate(self, f, a):
        while f > 1:
            f = self.hi[f] if a.get(self.v[f], 0) else self.lo[f]
        return f


class Ctx(object):
    def __init__(self, seed, nrand):
        self.alias = {}
        self.var_idx = {}
        self.var_names = []
        self.seed = seed
        self.nrand = nrand
        self.W = nrand + 2
        self.Mr = (1 << self.W) - 1
        self._rand = {}

    def canon(self, v, m):
        """Resolve variable v of model m through that model's alias map."""
        amap = self.alias.get(m.label)
        if not amap:
            return v
        seen = 0
        while v in amap:
            v = amap[v]
            seen += 1
            if seen > 1000:
                raise NetlistError('alias loop at %s' % v)
        return v

    def idx(self, v):
        i = self.var_idx.get(v)
        if i is None:
            i = len(self.var_names)
            self.var_idx[v] = i
            self.var_names.append(v)
        return i

    def rand(self, v):
        r = self._rand.get(v)
        if r is None:
            r = (random.Random('%d|%s' % (self.seed, v)).getrandbits(self.nrand) << 2) | 2
            self._rand[v] = r
        return r


def eval_nets(model, targets, leaf, combine, memo):
    """Generic DFS over the combinational cone.
    leaf(drv) -> value for var/const drivers; combine(op, vals, param) -> value."""
    drv, nodes = model.drv, model.nodes
    for t in targets:
        if t in memo:
            continue
        stack = [t]
        visiting = set()
        while stack:
            n = stack[-1]
            if n in memo:
                stack.pop()
                continue
            d = drv[n]
            if d[0] != 'n':
                memo[n] = leaf(d)
                stack.pop()
                continue
            op, ins, param = nodes[n]
            miss = [x for x in ins if x not in memo]
            if miss:
                if n in visiting:
                    raise NetlistError('%s: combinational loop through net %r'
                                       % (model.label, model.net_name[n]))
                visiting.add(n)
                stack.extend(miss)
                continue
            memo[n] = combine(op, [memo[x] for x in ins], param)
            stack.pop()


def make_value_fns(ctx, envget, M, m):
    def leaf(d):
        if d[0] == 'c':
            return M if d[1] else 0
        return envget(ctx.canon(d[1], m))

    def combine(op, vals, param):
        if op == 'LUT':
            return lut_eval(param, vals, M)
        if op == 'MUX':
            s, i0, i1 = vals
            return (s & i1) | ((s ^ M) & i0)
        if op == 'XOR':
            return vals[0] ^ vals[1]
        if op == 'INV':
            return vals[0] ^ M
        return vals[0]
    return leaf, combine


def support_fns(ctx, m):
    def leaf(d):
        if d[0] == 'c':
            return 0
        return 1 << ctx.idx(ctx.canon(d[1], m))

    def combine(op, vals, param):
        r = 0
        for v in vals:
            r |= v
        return r
    return leaf, combine


# --------------------------------------------------------------------------
# Checkpoints
# --------------------------------------------------------------------------

class Spec(object):
    """Function of one side of a checkpoint: fn(net values, extra var values, M)."""
    __slots__ = ('model', 'nets', 'extras', 'fn', 'desc')

    def __init__(self, model, nets, extras=(), fn=None, desc=''):
        self.model = model
        self.nets = list(nets)
        self.extras = list(extras)
        self.fn = fn
        self.desc = desc


class CP(object):
    __slots__ = ('name', 'a', 'b', 'tag', 'cell')

    def __init__(self, name, a, b, tag, cell=None):
        self.name = name
        self.a = a
        self.b = b
        self.tag = tag
        self.cell = cell


def pin_default(pinbit):
    return 1 if pin_base(pinbit) in ('CE', 'GE') else 0


def pin_spec(model, cc, pinbit, default=None):
    nid = cc.inputs.get(pinbit)
    if nid is None:
        nid = model.const(pin_default(pinbit) if default is None else default)
        return Spec(model, [nid], desc='%s (unconnected)' % pinbit)
    return Spec(model, [nid], desc=model.net_name[nid])


class IntOps(object):
    """Boolean operations on bit vectors (Python ints) of mask M."""
    def __init__(self, M):
        self.M = M
        self.one = M
        self.zero = 0

    def and_(self, a, b):
        return a & b

    def or_(self, a, b):
        return a | b

    def not_(self, a):
        return a ^ self.M

    def mux(self, s, a1, a0):
        return (s & a1) | ((s ^ self.M) & a0)


def make_ns_fn(sync_vals, qconst=None):
    """Next state: sync set/reset (first has priority) over CE ? D : Q."""
    def fn(vals, ex, ops):
        d, ce = vals[0], vals[1]
        q = ex[0] if qconst is None else (ops.one if qconst else ops.zero)
        v = ops.mux(ce, d, q)
        for p, val in reversed(list(zip(vals[2:], sync_vals))):
            v = ops.or_(v, p) if val else ops.and_(v, ops.not_(p))
        return v
    return fn


def ff_specs(model, cc, qconst=None):
    """Normalised behaviour of a flip-flop / latch: dict name -> Spec."""
    f = cc.ff
    r = {}
    r['CLK'] = pin_spec(model, cc, f.clk, 0)
    r['CLR'] = pin_spec(model, cc, 'CLR', 0) if f.clr else Spec(model, [model.const(0)], desc='0')
    r['PRE'] = pin_spec(model, cc, 'PRE', 0) if f.pre else Spec(model, [model.const(0)], desc='0')
    nets = [cc.inputs.get('D', model.const(0)),
            cc.inputs.get(f.ce, model.const(1)) if f.ce else model.const(1)]
    vals = []
    for p, val in f.sync:
        nets.append(cc.inputs.get(p, model.const(0)))
        vals.append(val)
    extras = [] if qconst is not None else [cc.outputs.get('Q', cc.norm + '.Q')]
    desc = '%s: %s' % (cc.typ, ', '.join(
        '%s=%s' % (p, model.net_name[cc.inputs[p]]) for p in sorted(cc.inputs)))
    r['NS'] = Spec(model, nets, extras, make_ns_fn(vals, qconst), desc)
    return r


def norm_param(cc, k):
    v = cc.params.get(k)
    if v is None and cc.ff is not None and k == 'INIT':
        v = cc.ff.init_default
    if v is None:
        return None
    if "'" in v:
        try:
            return str(literal_int(v))
        except Exception:
            return v
    return v


def params_equal(ca, cb):
    if ca.ff is not None and cb.ff is not None:
        keys = set(ca.params) | set(cb.params) | {'INIT'}
    else:
        keys = set(ca.params) | set(cb.params)
    diffs = []
    for k in sorted(keys):
        va, vb = norm_param(ca, k), norm_param(cb, k)
        if va != vb:
            diffs.append('%s: %s vs %s' % (k, va, vb))
    return diffs


def pair_cps(ma, ca, mb, cb, name, force_norm=False):
    """Checkpoints comparing cut cell ca (in ma) with cb (in mb).
    -> (list of CP, list of immediate issue strings)"""
    issues = []
    cps = []
    pd = params_equal(ca, cb)
    if pd:
        issues.append('parameters differ: ' + '; '.join(pd))
    if ca.ff is not None and cb.ff is not None:
        fa, fb = ca.ff, cb.ff
        if fa.latch != fb.latch or fa.neg != fb.neg:
            issues.append('storage kind differs: %s vs %s' % (ca.typ, cb.typ))
            return cps, issues
        if ca.typ == cb.typ and not force_norm:
            for pb in sorted(set(ca.inputs) | set(cb.inputs)):
                cps.append(CP('%s.%s' % (name, pb), pin_spec(ma, ca, pb),
                              pin_spec(mb, cb, pb), 'raw-ff', (ca, cb)))
        else:
            sa, sb = ff_specs(ma, ca), ff_specs(mb, cb)
            for k in ('CLK', 'CLR', 'PRE', 'NS'):
                cps.append(CP('%s:%s' % (name, k), sa[k], sb[k], 'norm-ff', (ca, cb)))
        return cps, issues
    if ca.typ != cb.typ:
        issues.append('cell type differs: %s vs %s' % (ca.typ, cb.typ))
        return cps, issues
    if set(ca.outputs) != set(cb.outputs):
        issues.append('output pins differ: %s vs %s'
                      % (sorted(ca.outputs), sorted(cb.outputs)))
    for pb in sorted(set(ca.inputs) | set(cb.inputs)):
        cps.append(CP('%s.%s' % (name, pb), pin_spec(ma, ca, pb),
                      pin_spec(mb, cb, pb), 'raw', (ca, cb)))
    return cps, issues


class Evaluator(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.sup_memo = {}
        self.rand_memo = {}

    def reset(self):
        self.sup_memo = {}
        self.rand_memo = {}

    def support(self, spec):
        m = spec.model
        memo = self.sup_memo.setdefault(id(m), {})
        leaf, comb = support_fns(self.ctx, m)
        eval_nets(m, spec.nets, leaf, comb, memo)
        s = 0
        for n in spec.nets:
            s |= memo[n]
        for v in spec.extras:
            s |= 1 << self.ctx.idx(self.ctx.canon(v, m))
        return s

    def value(self, spec, envget, M, memos):
        m = spec.model
        memo = memos.setdefault(id(m), {})
        leaf, comb = make_value_fns(self.ctx, envget, M, m)
        eval_nets(m, spec.nets, leaf, comb, memo)
        vals = [memo[n] for n in spec.nets]
        ex = [envget(self.ctx.canon(v, m)) for v in spec.extras]
        if spec.fn is None:
            return vals[0]
        return spec.fn(vals, ex, IntOps(M)) & M

    def bdd_value(self, spec, mgr, memos):
        """Exact function of spec as a BDD node of mgr (raises BddLimit)."""
        m = spec.model
        memo = memos.setdefault(id(m), {})
        ctx = self.ctx

        def leaf(d):
            if d[0] == 'c':
                return 1 if d[1] else 0
            return mgr.var(ctx.idx(ctx.canon(d[1], m)))

        def combine(op, vals, param):
            if op == 'LUT':
                return mgr.lut(param, vals)
            if op == 'MUX':
                s, i0, i1 = vals
                return mgr.ite(s, i1, i0)
            if op == 'XOR':
                return mgr.xor(vals[0], vals[1])
            if op == 'INV':
                return mgr.not_(vals[0])
            return vals[0]
        eval_nets(m, spec.nets, leaf, combine, memo)
        vals = [memo[n] for n in spec.nets]
        ex = [mgr.var(ctx.idx(ctx.canon(v, m))) for v in spec.extras]
        if spec.fn is None:
            return vals[0]
        return spec.fn(vals, ex, mgr)

    def rand_value(self, spec):
        return self.value(spec, self.ctx.rand, self.ctx.Mr, self.rand_memo)


def bits_of(x):
    r = []
    while x:
        low = x & -x
        r.append(low.bit_length() - 1)
        x ^= low
    return r


def popcount(x):
    """Number of set bits (int.bit_count needs Python 3.10)."""
    return bin(x).count('1')


_pat_cache = {}


def pattern(i, k):
    key = (i, k)
    v = _pat_cache.get(key)
    if v is None:
        W = 1 << k
        p = 1 << i
        block = ((1 << p) - 1) << p
        period = 2 * p
        v = block * (((1 << W) - 1) // ((1 << period) - 1))
        _pat_cache[key] = v
    return v


class Result(object):
    __slots__ = ('cp', 'ok', 'mode', 'supa', 'supb', 'cex', 'va', 'vb')


class BddSession(object):
    """A BDD manager with per-model net memos; reset when the node cap is hit."""
    budget = 200000
    cap = 1500000

    def __init__(self, ev):
        self.ev = ev
        self.gen = 0
        self.fallbacks = 0
        self._new()

    def _new(self):
        self.mgr = BDD(self.budget, self.cap)
        self.memos = {}
        self.gen += 1

    def node(self, spec):
        """BDD node of spec, or None if the node budget is exceeded."""
        mgr = self.mgr
        mgr.mark()
        try:
            return self.ev.bdd_value(spec, mgr, self.memos)
        except BddLimit:
            self.fallbacks += 1
            if mgr.size() > self.cap or mgr.size() - mgr.start > self.budget:
                self._new()
            return None
        finally:
            if len(mgr.cache) > 4000000:
                mgr.cache.clear()


def compare_all(cps, ev, maxex):
    """-> list of Result.  Union support <= maxex: exhaustive; otherwise an
    exact BDD comparison; random vectors only if the BDD exceeds its budget."""
    ctx = ev.ctx
    results = []
    groups = defaultdict(list)
    sess = None
    for cp in cps:
        r = Result()
        r.cp = cp
        r.supa = ev.support(cp.a)
        r.supb = ev.support(cp.b)
        r.cex = None
        u = r.supa | r.supb
        if popcount(u) <= maxex:
            r.mode = 'exhaustive'
            groups[u].append(r)
        else:
            if sess is None:
                sess = BddSession(ev)
            fa = sess.node(cp.a)
            fb = sess.node(cp.b) if fa is not None else None
            if fa is not None and fb is not None:
                r.mode = 'bdd'
                r.ok = fa == fb
                if not r.ok:
                    mgr = sess.mgr
                    mgr.mark()
                    try:
                        a = mgr.sat_one(mgr.xor(fa, fb))
                    except BddLimit:
                        a = None
                    if a is not None:
                        r.cex = [(ctx.var_names[i], a.get(i, 0)) for i in bits_of(u)]
                        r.va, r.vb = mgr.evaluate(fa, a), mgr.evaluate(fb, a)
                    else:
                        r.cex = [('(counterexample too large for the BDD)', 0)]
                        r.va = r.vb = -1
                results.append(r)
                continue
            r.mode = 'random'
            va = ev.rand_value(cp.a)
            vb = ev.rand_value(cp.b)
            r.ok = va == vb
            if not r.ok:
                d = va ^ vb
                j = (d & -d).bit_length() - 1
                r.cex = [(ctx.var_names[i], (ctx.rand(ctx.var_names[i]) >> j) & 1)
                         for i in bits_of(u)]
                r.va, r.vb = (va >> j) & 1, (vb >> j) & 1
        results.append(r)
    for u, rs in groups.items():
        idxs = bits_of(u)
        k = len(idxs)
        M = (1 << (1 << k)) - 1
        env = {ctx.var_names[ix]: pattern(n, k) for n, ix in enumerate(idxs)}
        memos = {}
        envget = env.__getitem__
        for r in rs:
            va = ev.value(r.cp.a, envget, M, memos)
            vb = ev.value(r.cp.b, envget, M, memos)
            r.ok = va == vb
            if not r.ok:
                d = va ^ vb
                j = (d & -d).bit_length() - 1
                r.cex = [(ctx.var_names[ix], (j >> n) & 1) for n, ix in enumerate(idxs)]
                r.va, r.vb = (va >> j) & 1, (vb >> j) & 1
    return results


# --------------------------------------------------------------------------
# Register duplicates
# --------------------------------------------------------------------------

DUP_SUFFIX_RE = re.compile(r'^(.*)_\d+$')


def name_candidates(norm):
    r = []
    n = norm
    while True:
        m = DUP_SUFFIX_RE.match(n)
        if not m:
            break
        n = m.group(1)
        r.append(n)
    return r


def same_class(ca, cb):
    return ca.typ == cb.typ and not params_equal(ca, cb) and \
        set(ca.outputs) == set(cb.outputs)


def alias_cps(m, x, p):
    """Checkpoints proving that unmatched cell x is a copy of p (same model)."""
    name = '%s ~ %s' % (x.norm, p.norm)
    if x.ff is not None:
        sx, sp = ff_specs(m, x), ff_specs(m, p)
        return [CP('%s:%s' % (name, k), sx[k], sp[k], 'alias', (x, p))
                for k in ('CLK', 'CLR', 'PRE', 'NS')]
    return [CP('%s.%s' % (name, pb), pin_spec(m, x, pb), pin_spec(m, p, pb), 'alias', (x, p))
            for pb in sorted(set(x.inputs) | set(p.inputs))]


def signature(ev, m, c):
    if c.ff is not None:
        s0 = ff_specs(m, c, qconst=0)
        s1 = ff_specs(m, c, qconst=1)
        specs = [s0['CLK'], s0['CLR'], s0['PRE'], s0['NS'], s1['NS']]
        return tuple(hash(ev.rand_value(s)) for s in specs)
    return tuple((pb, hash(ev.rand_value(pin_spec(m, c, pb)))) for pb in sorted(c.inputs))


def q_var(c):
    return c.outputs.get('Q', c.norm + '.Q')


def build_alias(models, corr, hyp):
    """Per-model alias maps: register correspondence + one-sided copies."""
    amap = {}
    for side, m in enumerate(models):
        a = dict(corr.get(m.label, {}))
        for (s, xn), pn in hyp.items():
            if s != side:
                continue
            x, p = m.cuts[xn], m.cuts[pn]
            for pb, v in x.outputs.items():
                a[v] = p.outputs[pb]
        amap[m.label] = a
    return amap


def register_correspondence(m, matched, ev, maxex, log):
    """Greatest-fixpoint register correspondence inside one netlist.
    Classes start per (latch/FF, clock polarity, INIT); every member's Q is
    replaced by the class representative; a class is split while CLK, CLR, PRE
    or the next state of its members differ (random signatures first, which
    can only split; then the exact partition by the canonical BDD of each
    function; a function over the BDD budget keeps its random signature and
    can then only be merged with an identical signature).
    Representative: the smallest name among the members present in both
    netlists, else the smallest name.  -> (alias map, classes)"""
    ctx = ev.ctx
    ffs = sorted((c for c in m.cuts.values() if c.ff is not None), key=lambda c: c.norm)
    groups = defaultdict(list)
    for c in ffs:
        groups[(c.ff.latch, c.ff.neg, norm_param(c, 'INIT'))].append(c)
    classes = [groups[k] for k in sorted(groups, key=str)]

    def rep_of(cls):
        both = [c for c in cls if c.norm in matched]
        return min(both or cls, key=lambda c: c.norm)

    def alias_for(classes):
        a = {}
        for cls in classes:
            if len(cls) < 2:
                continue
            r = q_var(rep_of(cls))
            for c in cls:
                v = q_var(c)
                if v != r:
                    a[v] = r
        return a

    it = 0
    while True:
        it += 1
        ctx.alias = {m.label: alias_for(classes)}
        ev.reset()
        new_classes = []
        changed = False
        for cls in classes:
            if len(cls) < 2:
                new_classes.append(cls)
                continue
            sub = {}
            order = []
            for c in cls:
                s = ff_specs(m, c)
                sig = tuple(hash(ev.rand_value(s[k])) for k in ('CLK', 'CLR', 'PRE', 'NS'))
                if sig not in sub:
                    sub[sig] = []
                    order.append(sig)
                sub[sig].append(c)
            if len(order) > 1:
                changed = True
            new_classes.extend(sub[s] for s in order)
        classes = new_classes
        if changed:
            continue
        # exact partition: canonical BDD of CLK, CLR, PRE and NS of every
        # member (Q of the members = the representative variable); a
        # component whose BDD exceeds the budget falls back to its random
        # vector (it can then only be merged with an identical vector)
        sess = BddSession(ev)
        nb = nr = 0
        new_classes = []
        changed = False
        for cls in classes:
            if len(cls) < 2:
                new_classes.append(cls)
                continue
            sub = {}
            order = []
            for c in cls:
                s = ff_specs(m, c)
                key = []
                for k in ('CLK', 'CLR', 'PRE', 'NS'):
                    node = sess.node(s[k])
                    if node is None:
                        nr += 1
                        key.append(('r', hash(ev.rand_value(s[k]))))
                    else:
                        nb += 1
                        key.append(('b', sess.gen, node))
                key = tuple(key)
                if key not in sub:
                    sub[key] = []
                    order.append(key)
                sub[key].append(c)
            if len(order) > 1:
                changed = True
            new_classes.extend(sub[k] for k in order)
        nsplit = len(new_classes) - len(classes)
        classes = new_classes
        log('  %s: iteration %d: exact check (BDD %d, random fallback %d functions): '
            '%d class(es) split off; %d classes with >1 member'
            % (m.label, it, nb, nr, nsplit, sum(1 for c in classes if len(c) > 1)))
        if not changed:
            break
    amap = alias_for(classes)
    ctx.alias = {}
    ev.reset()
    return amap, [(rep_of(c), c) for c in classes if len(c) > 1]


def find_aliases(models, matched, ev, log, corr=None, exclude=()):
    ctx = ev.ctx
    corr = corr or {}
    hyp = {}          # (side, xnorm) -> pnorm
    rejected = set()  # (side, xnorm, pnorm)
    for side, m in enumerate(models):
        for xn, x in m.cuts.items():
            if xn in matched or (side, xn) in exclude:
                continue
            for cn in name_candidates(xn):
                if cn in matched and same_class(x, m.cuts[cn]):
                    hyp[(side, xn)] = cn
                    break
    it = 0
    while True:
        it += 1
        ctx.alias = build_alias(models, corr, hyp)
        ev.reset()
        bad = []
        for (side, xn), pn in hyp.items():
            m = models[side]
            for cp in alias_cps(m, m.cuts[xn], m.cuts[pn]):
                if ev.rand_value(cp.a) != ev.rand_value(cp.b):
                    bad.append((side, xn))
                    break
        if bad:
            for k in bad:
                rejected.add((k[0], k[1], hyp[k]))
                del hyp[k]
            log('  alias iteration %d: %d candidate(s) rejected' % (it, len(bad)))
            continue
        # signature search for the remaining unmatched cells
        added = 0
        for side, m in enumerate(models):
            rest = [x for xn, x in m.cuts.items()
                    if xn not in matched and (side, xn) not in hyp
                    and (side, xn) not in exclude]
            if not rest:
                continue
            types = set(x.typ for x in rest)
            index = defaultdict(list)
            for pn in matched:
                p = m.cuts[pn]
                if p.typ in types:
                    index[(p.typ, signature(ev, m, p))].append(p)
            for x in rest:
                for p in index.get((x.typ, signature(ev, m, x)), []):
                    if (side, x.norm, p.norm) not in rejected and same_class(x, p):
                        hyp[(side, x.norm)] = p.norm
                        added += 1
                        break
        log('  alias iteration %d: %d alias(es), %d added by signature'
            % (it, len(hyp), added))
        if not added:
            return hyp


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def fmt_sup(ctx, s):
    names = sorted(ctx.var_names[i] for i in bits_of(s))
    return '{%s} (%d)' % (', '.join(names), len(names))


def dump_types(paths):
    for p in paths:
        P = parse_netlist(p)
        c = Counter(x.typ for x in P.cells)
        print('%s: module %s, %d ports, %d cells, %d assigns'
              % (p, P.module, len(P.ports), len(P.cells), len(P.assigns)))
        for t in sorted(c):
            print('  %-14s %6d  %s' % (t, c[t], classify(t) or 'UNKNOWN'))


EPILOG = '''exit codes:
  0  EQUIVALENT
  1  NOT EQUIVALENT (mismatch, failed alias check, cell-level issue or a used
     unmatched cut cell)
  2  no verdict: usage error, unreadable/unsupported netlist, internal failure

Validate the checker on your netlists first: BASE.v against itself must give
EQUIVALENT, and a mutant of BASE.v (make_mutant.py) must give NOT EQUIVALENT.'''


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors='backslashreplace')
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(
        description='Register-cut-point equivalence of two flat netgen Verilog netlists '
                    '(Xilinx ISE/XST post-synthesis).',
        epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='+', help='BASE.v NEW.v (or files for --dump-types)')
    ap.add_argument('--strip', action='append', default=[], metavar='PREFIX',
                    help='instance name prefix to remove before matching (repeatable)')
    ap.add_argument('--seed', type=int, default=1, help='seed of the random vectors')
    ap.add_argument('--max-exhaustive', type=int, default=16,
                    help='largest support checked exhaustively; larger ones use BDDs')
    ap.add_argument('--random', type=int, default=4096, help='number of random assignments')
    ap.add_argument('--bdd-budget', type=int, default=200000,
                    help='BDD node budget per function before falling back to random vectors')
    ap.add_argument('--max-notes', type=int, default=20,
                    help='how many informational notes of each kind to print (0 = all)')
    ap.add_argument('--dump-types', action='store_true', help='list cell types and exit')
    a = ap.parse_args(argv)

    try:
        if a.dump_types:
            dump_types(a.files)
            return 0
        if len(a.files) != 2:
            ap.error('need BASE.v and NEW.v')
        return run(a)
    except NetlistError as e:
        print('ERROR: %s' % e)
        return 2
    except OSError as e:
        print('ERROR: %s' % e)
        return 2
    except Exception:
        # never let a crash look like a verdict (exit 1 = NOT EQUIVALENT)
        import traceback
        traceback.print_exc()
        print('ERROR: internal failure, no verdict')
        return 2


def run(a):
    t0 = time.time()
    sys.setrecursionlimit(20000)
    BddSession.budget = a.bdd_budget

    def log(s):
        print(s)
        sys.stdout.flush()

    log('netlist_equiv: base=%s' % a.files[0])
    log('               new =%s' % a.files[1])
    log('strip=%s seed=%d max-exhaustive=%d random=%d'
        % (a.strip, a.seed, a.max_exhaustive, a.random))
    models = []
    for label, f in zip(('base', 'new'), a.files):
        P = parse_netlist(f)
        m = Model(label, P, a.strip)
        models.append(m)
        kinds = Counter()
        for t, n in m.type_counts.items():
            kinds[classify(t)] += n
        log('%s: module %s, %d cells (%s), %d cut cells, %d comb nets'
            % (label, P.module, sum(m.type_counts.values()),
               ', '.join('%s %d' % kv for kv in sorted(kinds.items())),
               len(m.cuts), len(m.nodes)))
        bbt = sorted(set(c.typ for c in m.cuts.values() if c.kind == 'bb'))
        if bbt:
            log('  black boxes (pin directions inferred): %s' % ', '.join(bbt))
        for w in sorted(set(m.warnings)):
            log('  warning: %s' % w)
    A, B = models
    ctx = Ctx(a.seed, a.random)
    ev = Evaluator(ctx)

    matched = sorted(set(A.cuts) & set(B.cuts))
    only = [sorted(set(A.cuts) - set(B.cuts)), sorted(set(B.cuts) - set(A.cuts))]
    log('cut cells: base %d, new %d, matched by name %d, base-only %d, new-only %d'
        % (len(A.cuts), len(B.cuts), len(matched), len(only[0]), len(only[1])))

    mset = set(matched)
    log('register correspondence (per netlist):')
    corr = {}
    corr_classes = []
    exclude = set()
    for side, m in enumerate(models):
        amap, classes = register_correspondence(m, mset, ev, a.max_exhaustive, log)
        corr[m.label] = amap
        corr_classes.append(classes)
        for r, cls in classes:
            for c in cls:
                if c is not r and c.norm not in mset:
                    exclude.add((side, c.norm))

    log('register duplicates (one-sided, remaining cells):')
    hyp = find_aliases(models, mset, ev, log, corr, exclude)

    # final alias map
    ctx.alias = build_alias(models, corr, hyp)
    ev.reset()

    # checkpoints
    issues = []          # (name, text)
    cps = []
    for n in matched:
        c, iss = pair_cps(A, A.cuts[n], B, B.cuts[n], n)
        cps.extend(c)
        for s in iss:
            issues.append((n, s))
    pa = dict(A.out_ports)
    pb = dict(B.out_ports)
    for p in sorted(set(pa) | set(pb)):
        if p not in pa or p not in pb:
            issues.append((p, 'output port only in %s' % ('new' if p in pb else 'base')))
            continue
        cps.append(CP(p, Spec(A, [pa[p]], desc=A.net_name[pa[p]]),
                      Spec(B, [pb[p]], desc=B.net_name[pb[p]]), 'port'))
    for p in sorted(set(A.port_dirs) | set(B.port_dirs)):
        if A.port_dirs.get(p) != B.port_dirs.get(p) and p in A.port_dirs and p in B.port_dirs:
            issues.append((p, 'port direction differs: %s vs %s' % (A.port_dirs[p], B.port_dirs[p])))
    acps = []
    for (side, xn), pn in sorted(hyp.items()):
        m = models[side]
        acps.extend(alias_cps(m, m.cuts[xn], m.cuts[pn]))

    log('comparing %d checkpoints + %d alias checkpoints ...' % (len(cps), len(acps)))
    res = compare_all(cps, ev, a.max_exhaustive)
    ares = compare_all(acps, ev, a.max_exhaustive)

    # raw FF pin differences: decide by the normalised behaviour
    raw_fail_cells = {}
    for r in res:
        if not r.ok and r.cp.tag == 'raw-ff':
            raw_fail_cells.setdefault(r.cp.cell[0].norm, []).append(r)
    norm_cps = []
    for n in sorted(raw_fail_cells):
        c, _ = pair_cps(A, A.cuts[n], B, B.cuts[n], n, force_norm=True)
        norm_cps.extend(c)
    nres = compare_all(norm_cps, ev, a.max_exhaustive)
    norm_bad = set(r.cp.cell[0].norm for r in nres if not r.ok)

    mismatches = []
    notes_raw = []
    for r in res:
        if r.ok:
            continue
        if r.cp.tag == 'raw-ff' and r.cp.cell[0].norm not in norm_bad:
            notes_raw.append(r)
            continue
        mismatches.append(r)
    mismatches.extend(r for r in nres if not r.ok)
    alias_bad = [r for r in ares if not r.ok]

    # usage of unmatched cells
    used = [0, 0]
    for r in res + ares + nres:
        used[0] |= r.supa if r.cp.a.model is A else 0
        used[0] |= r.supb if r.cp.b.model is A else 0
        used[1] |= r.supa if r.cp.a.model is B else 0
        used[1] |= r.supb if r.cp.b.model is B else 0
    aliased = [[], []]
    unmatched = [[], []]
    for side, m in enumerate(models):
        for xn in only[side]:
            c = m.cuts[xn]
            if (side, xn) in hyp:
                aliased[side].append((xn, hyp[(side, xn)], 'copy'))
                continue
            if c.ff is not None:
                t = ctx.canon(q_var(c), m)
                tn = t[:-2] if t.endswith('.Q') else t
                if t != q_var(c) and tn in mset:
                    aliased[side].append((xn, tn, 'correspondence'))
                    continue
            u = any(v in ctx.var_idx and (used[side] >> ctx.var_idx[v]) & 1
                    for v in c.outputs.values())
            unmatched[side].append((xn, c.typ, u))

    sup_notes = [r for r in res if r.ok and r.supa != r.supb]
    allres = res + nres
    n_ex = sum(1 for r in allres if r.mode == 'exhaustive')
    n_rn = sum(1 for r in allres if r.mode == 'random')
    a_ex = sum(1 for r in ares if r.mode == 'exhaustive')

    log('')
    log('=== SUMMARY ===')
    log('cut cells matched: %d' % len(matched))
    log('register correspondence classes with >1 member: base %d (%d FFs), new %d (%d FFs)'
        % (len(corr_classes[0]), sum(len(c) for _, c in corr_classes[0]),
           len(corr_classes[1]), sum(len(c) for _, c in corr_classes[1])))
    log('cut cells aliased (one-netlist-only copies): base %d, new %d'
        % (len(aliased[0]), len(aliased[1])))
    log('cut cells unmatched: base %d (used %d), new %d (used %d)'
        % (len(unmatched[0]), sum(1 for x in unmatched[0] if x[2]),
           len(unmatched[1]), sum(1 for x in unmatched[1] if x[2])))
    n_bd = sum(1 for r in allres if r.mode == 'bdd')
    log('checkpoints compared: %d (exhaustive %d, bdd %d, random %d); of them FF next-state re-checks %d'
        % (len(allres), n_ex, n_bd, n_rn, len(nres)))
    a_bd = sum(1 for r in ares if r.mode == 'bdd')
    log('alias checkpoints: %d (exhaustive %d, bdd %d, random %d), failed %d'
        % (len(ares), a_ex, a_bd, len(ares) - a_ex - a_bd, len(alias_bad)))
    log('cell-level issues (type/parameter/port): %d' % len(issues))
    mis_cells = set(r.cp.cell[0].norm if r.cp.cell else r.cp.name for r in mismatches)
    log('mismatches: %d checkpoint(s) in %d cut cell(s)/port(s)' % (len(mismatches), len(mis_cells)))
    log('notes: raw FF pin differs but next state equal: %d; equal function with different structural support: %d'
        % (len(notes_raw), len(sup_notes)))
    log('mode per checkpoint kind:')
    kc = Counter((r.cp.tag, r.mode) for r in allres)
    for k in sorted(kc):
        log('  %-8s %-10s %d' % (k[0], k[1], kc[k]))

    log('')
    log('=== REGISTER CORRESPONDENCE CLASSES (representative <- members) ===')
    for side in (0, 1):
        for r, cls in corr_classes[side]:
            log('  %s: %s <- %s (%s)' % (('base', 'new')[side], r.norm,
                                         ', '.join(c.norm for c in cls if c is not r),
                                         '/'.join(sorted(set(c.typ for c in cls)))))
    log('')
    log('=== ALIASES (one-netlist-only cell -> partner) ===')
    for side in (0, 1):
        for xn, pn, how in aliased[side]:
            log('  %s: %s -> %s (%s, %s)' % (('base', 'new')[side], xn, pn,
                                             models[side].cuts[xn].typ, how))
    log('')
    log('=== UNMATCHED CUT CELLS ===')
    for side in (0, 1):
        for xn, t, u in unmatched[side]:
            log('  %s: %s (%s) %s' % (('base', 'new')[side], xn, t, 'USED' if u else 'unused'))
    log('')
    log('=== CELL-LEVEL ISSUES ===')
    for n, s in issues:
        log('  %s: %s' % (n, s))

    def show(r):
        cp = r.cp
        log('  %s [%s, %s]' % (cp.name, cp.tag, r.mode))
        log('    base(%s): %s' % (cp.a.model.label, cp.a.desc))
        log('    new (%s): %s' % (cp.b.model.label, cp.b.desc))
        log('    support %s: %s' % (cp.a.model.label, fmt_sup(ctx, r.supa)))
        log('    support %s: %s' % (cp.b.model.label, fmt_sup(ctx, r.supb)))
        if r.cex is not None:
            log('    counterexample: %s' % ' '.join('%s=%d' % kv for kv in sorted(r.cex)))
            log('    value: %s=%d %s=%d' % (cp.a.model.label, r.va, cp.b.model.label, r.vb))

    log('')
    log('=== MISMATCHES ===')
    for r in mismatches:
        show(r)
    if alias_bad:
        log('')
        log('=== ALIAS CHECK FAILURES ===')
        for r in alias_bad:
            show(r)

    def limited(lst):
        return lst if a.max_notes == 0 else lst[:a.max_notes]
    log('')
    log('=== NOTES: raw FF pin differs, next state equal (%d) ===' % len(notes_raw))
    for r in limited(notes_raw):
        log('  %s [%s]' % (r.cp.name, r.mode))
    log('=== NOTES: equal function, different structural support (%d) ===' % len(sup_notes))
    for r in limited(sup_notes):
        da = r.supa & ~r.supb
        db = r.supb & ~r.supa
        log('  %s [%s]: only base %s; only new %s'
            % (r.cp.name, r.mode, fmt_sup(ctx, da), fmt_sup(ctx, db)))
    und = [sorted(A.undriven_used), sorted(B.undriven_used)]
    if und[0] or und[1]:
        log('=== NOTES: undriven nets (free variables) base %d, new %d ===' % (len(und[0]), len(und[1])))
        for side in (0, 1):
            for n in limited(und[side]):
                log('  %s: %s' % (('base', 'new')[side], n))

    bad_unmatched = sum(1 for s in (0, 1) for x in unmatched[s] if x[2])
    ok = not mismatches and not alias_bad and not issues and not bad_unmatched
    log('')
    log('RESULT: %s (%.1f s)' % ('EQUIVALENT' if ok else 'NOT EQUIVALENT', time.time() - t0))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
