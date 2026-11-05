"""Small synthetic netlists in the format of Xilinx netgen (-ofmt verilog -w).

They are written for the tests only; no real design is involved.  Instance
and net names follow netgen's habits: escaped identifiers with a trailing
space for hierarchical or `<n>` names, bus bits as `\\name [i]` or `name[i]`,
INIT parameters as `.INIT ( 8'hF8 )`, a `glbl` module at the end.
"""

import importlib.util
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), 'skills', 'proving-netlist-equivalence', 'scripts')

PLAIN = re.compile(r'^[A-Za-z_][A-Za-z0-9_$]*$')


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SCRIPTS, name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def lut_init(k, fn):
    """INIT of a k-input LUT computing fn(I0, ..., Ik-1)."""
    v = 0
    for j in range(1 << k):
        if fn(*[(j >> i) & 1 for i in range(k)]):
            v |= 1 << j
    return v


def init_lit(k, v):
    w = 1 << k
    return "%d'h%0*X" % (w, (w + 3) // 4, v)


def r(name):
    """Reference to a scalar net or an instance name."""
    return name if PLAIN.match(name) else '\\' + name + ' '


def rb(name, i):
    """Reference to bit i of a declared bus."""
    return ('%s[%d]' % (name, i)) if PLAIN.match(name) else '\\%s [%d]' % (name, i)


class Netlist(object):
    def __init__(self, module):
        self.module = module
        self.ports = []      # (dir, name, width)
        self.wires = []      # (name, width)
        self.cells = []      # text blocks

    def port(self, d, name, width=None):
        self.ports.append((d, name, width))

    def wire(self, name, width=None):
        self.wires.append((name, width))

    def cell(self, typ, name, pins, params=None):
        lines = []
        if params:
            plist = ',\n'.join('    .%s ( %s )' % kv for kv in params.items())
            lines.append('  %s #(\n%s)\n  %s (' % (typ, plist, r(name)))
        else:
            lines.append('  %s   %s (' % (typ, r(name)))
        lines.append(',\n'.join('    .%s(%s)' % (p, n) for p, n in pins))
        lines.append('  );')
        self.cells.append('\n'.join(lines))

    def lut(self, name, ins, out, init):
        k = len(ins)
        self.cell('LUT%d' % k, name, [('I%d' % j, n) for j, n in enumerate(ins)] + [('O', out)],
                  {'INIT': init_lit(k, init)})

    def text(self):
        names = ', '.join(p[1] for p in self.ports)
        out = ['// synthetic netgen-style netlist for unit tests',
               '`timescale 1 ns/1 ps', '',
               'module %s (' % self.module, '  %s' % names, ');']
        for d, n, w in self.ports:
            out.append('  %s %s%s;' % (d, '[%d : 0] ' % (w - 1) if w else '', r(n)))
        for n, w in self.wires:
            out.append('  wire %s%s;' % ('[%d : 0] ' % (w - 1) if w else '', r(n)))
        out.extend(self.cells)
        out.append('')
        out.append('endmodule')
        out.append('')
        out.append('`ifndef GLBL\n`define GLBL\n`timescale  1 ps / 1 ps\n\nmodule glbl ();\n'
                   '  parameter ROC_WIDTH = 100000;\n  wire GSR;\n  reg GSR_int;\n'
                   '  initial begin\n    GSR_int = 1\'b1;\n  end\nendmodule\n`endif\n')
        return '\n'.join(out)


VARIANTS = ('base', 'refactor', 'flip', 'swap', 'ce', 'removed')


def design(variant='base'):
    """The main test design.

    base      reference netlist
    refactor  equivalent: every internal net renamed, internal instances under
              a new prefix u_core/ (use --strip u_core/), LUT inputs permuted
              with the INIT adjusted, a LUT5 re-partitioned into two LUT3, a
              duplicated register (r2_1) feeding an output, FDR with the sync
              reset absorbed into the D logic of an FD, a carry chain partly
              replaced by a LUT
    flip      one INIT bit of the LUT in front of r1 flipped
    swap      two inputs of that LUT swapped, INIT kept
    ce        the clock enable of r1 connected to another signal
    removed   register r3 removed, its output port driven by its D signal
    """
    assert variant in VARIANTS
    ref = variant == 'refactor'
    pfx = 'u_core/' if ref else ''

    def nm(x):
        return 'u_core/%s_9' % x if ref else x

    nl = Netlist('top')
    for p in ('clk', 'rst', 'en', 'a', 'b', 'c', 'd'):
        nl.port('input', p)
    for p in ('y1', 'y2', 'y3', 'z'):
        nl.port('output', p)
    nl.port('output', 's', 3)
    sumbus = nm('sum')
    nl.wire(sumbus, 3)
    nl.wire(nm('sq'), 3)

    clk = 'clk_BUFGP'
    nl.cell('BUFGP', 'clk_BUFGP', [('I', 'clk'), ('O', clk)])
    ib = {}
    for p in ('rst', 'en', 'a', 'b', 'c', 'd'):
        ib[p] = '%s_IBUF_%d' % (p, 7 if ref else 0)
        nl.cell('IBUF', '%s_IBUF' % p, [('I', p), ('O', ib[p])])
    gnd = r(nm('N0'))
    nl.cell('GND', 'XST_GND', [('G', gnd)])
    a, b, c, d, en, rst = ib['a'], ib['b'], ib['c'], ib['d'], ib['en'], ib['rst']

    # r1 <= en ? (a & b) | c : r1
    f1 = r(nm('f1'))
    if ref:
        nl.lut(pfx + 'f1<0>', [c, a, b], f1, lut_init(3, lambda i0, i1, i2: (i1 & i2) | i0))
    elif variant == 'swap':
        nl.lut('f1<0>', [a, c, b], f1, lut_init(3, lambda i0, i1, i2: (i0 & i1) | i2))
    else:
        init = lut_init(3, lambda i0, i1, i2: (i0 & i1) | i2)
        if variant == 'flip':
            init ^= 1
        nl.lut('f1<0>', [a, b, c], f1, init)
    r1q = r(nm('r1q'))
    nl.cell('FDE', pfx + 'r1', [('C', clk), ('CE', b if variant == 'ce' else en),
                                ('D', f1), ('Q', r1q)], {'INIT': "1'b0"})

    # r2 <= (a ^ b ^ c) & (d | r1)
    g = r(nm('g'))
    if ref:
        x3 = r(nm('x3'))
        nl.lut(pfx + 'x3<0>', [a, b, c], x3, lut_init(3, lambda i0, i1, i2: i0 ^ i1 ^ i2))
        nl.lut(pfx + 'g<0>', [x3, d, r1q], g, lut_init(3, lambda x, dd, q: x & (dd | q)))
    else:
        nl.lut('g<0>', [a, b, c, d, r1q], g,
               lut_init(5, lambda i0, i1, i2, i3, i4: (i0 ^ i1 ^ i2) & (i3 | i4)))
    r2q = r(nm('r2q'))
    nl.cell('FD', pfx + 'r2', [('C', clk), ('D', g), ('Q', r2q)])
    zsrc = r2q
    if ref:
        r21q = r(nm('r2_1q'))
        nl.cell('FD', pfx + 'r2_1', [('C', clk), ('D', g), ('Q', r21q)])
        zsrc = r21q

    # r3 <= rst ? 0 : a
    r3q = r(nm('r3q'))
    if ref:
        n3 = r(nm('r3_rstpot'))
        nl.lut(pfx + 'r3_rstpot', [a, rst], n3, lut_init(2, lambda aa, rr: aa & (1 - rr)))
        nl.cell('FD', pfx + 'r3', [('C', clk), ('D', n3), ('Q', r3q)])
    elif variant != 'removed':
        nl.cell('FDR', 'r3', [('C', clk), ('D', a), ('R', rst), ('Q', r3q)])
    else:
        r3q = a

    # {s2, s1, s0} <= {b, a} + {d, c}: carry chain
    p0, p1, cy0 = r(nm('p0')), r(nm('p1')), r(nm('cy0'))
    xor2 = lut_init(2, lambda i0, i1: i0 ^ i1)
    nl.lut(pfx + 'Madd_lut<0>', [a, c], p0, xor2)
    nl.lut(pfx + 'Madd_lut<1>', [b, d], p1, xor2)
    nl.cell('MUXCY', pfx + 'Madd_cy<0>', [('CI', gnd), ('DI', a), ('S', p0), ('O', cy0)])
    if ref:
        nl.lut(pfx + 'Madd_sum<0>', [c, a], rb(sumbus, 0), xor2)
    else:
        nl.cell('XORCY', 'Madd_xor<0>', [('CI', gnd), ('LI', p0), ('O', rb(sumbus, 0))])
    nl.cell('XORCY', pfx + 'Madd_xor<1>', [('CI', cy0), ('LI', p1), ('O', rb(sumbus, 1))])
    nl.cell('MUXCY', pfx + 'Madd_cy<1>', [('CI', cy0), ('DI', b), ('S', p1), ('O', rb(sumbus, 2))])
    for i in range(3):
        nl.cell('FD', pfx + 'sreg_%d' % i, [('C', clk), ('D', rb(sumbus, i)), ('Q', rb(nm('sq'), i))])

    for port, src in (('y1', r1q), ('y2', r2q), ('y3', r3q), ('z', zsrc)):
        nl.cell('OBUF', '%s_OBUF' % port, [('I', src), ('O', port)])
    for i in range(3):
        nl.cell('OBUF', 's_%d_OBUF' % i, [('I', rb(nm('sq'), i)), ('O', rb('s', i))])
    return nl.text()


def wide_and_design(wrong=False):
    """A register w whose clock enable is the AND of 24 inputs, next to a
    register k that only holds its value.  Under random vectors w looks like
    k (its enable is practically never 1); an exact check separates them.
    wrong=True drives output yw from k instead of w."""
    nl = Netlist('wide')
    nl.port('input', 'clk')
    nl.port('input', 'a')
    nl.port('input', 'e', 24)
    nl.port('output', 'yw')
    nl.port('output', 'yk')
    nl.cell('BUFGP', 'clk_BUFGP', [('I', 'clk'), ('O', 'clk_BUFGP')])
    and6 = lut_init(6, lambda *x: all(x))
    outs = []
    for g in range(4):
        o = r('ce_and<%d>' % g)
        nl.lut('ce_and<%d>' % g, [rb('e', 6 * g + j) for j in range(6)], o, and6)
        outs.append(o)
    nl.lut('ce_and<4>', outs, 'ce', lut_init(4, lambda *x: all(x)))
    nl.cell('FDE', 'w', [('C', 'clk_BUFGP'), ('CE', 'ce'), ('D', 'a'), ('Q', 'w_q')])
    nl.cell('FD', 'k', [('C', 'clk_BUFGP'), ('D', 'k_q'), ('Q', 'k_q')])
    nl.cell('OBUF', 'yw_OBUF', [('I', 'k_q' if wrong else 'w_q'), ('O', 'yw')])
    nl.cell('OBUF', 'yk_OBUF', [('I', 'k_q'), ('O', 'yk')])
    return nl.text()
