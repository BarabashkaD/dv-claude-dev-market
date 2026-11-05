#!/usr/bin/env python3
"""make_mutant.py - write a one-cell mutant of a netgen Verilog netlist, to
prove that netlist_equiv.py detects a real logic change on YOUR netlists.

Usage:
    python -B make_mutant.py BASE.v MUTANT.v --mode flip|swap [--instance NAME]

  flip  flip INIT bit 0 of a LUT
  swap  swap two inputs of a LUT whose function is not symmetric in them
        (the INIT is kept, so the function really changes)

Without --instance the first LUT (in file order) is picked whose output
drives the D pin of a flip-flop and whose inputs are distinct cut variables
(register outputs or input ports, possibly through buffers/inverters), so
the change is observable at that D pin and the mutant must compare NOT
EQUIVALENT.  The changed instance and its D-pin flip-flop are printed.

Then run:  python -B netlist_equiv.py BASE.v MUTANT.v   -> must exit 1.

Exit codes: 0 mutant written; 2 no suitable LUT, unknown instance or input
error.  Python 3.8 or newer, standard library only.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import netlist_equiv as ne  # noqa: E402

PLAIN_ID = re.compile(r'^[A-Za-z_][A-Za-z0-9_$]*$')
LUTK_RE = re.compile(r'^LUT([1-6])$')


def swapped_init(init, k, i, j):
    """INIT of the LUT whose inputs i and j are exchanged."""
    r = 0
    for n in range(1 << k):
        bi, bj = (n >> i) & 1, (n >> j) & 1
        m = n & ~((1 << i) | (1 << j)) | (bi << j) | (bj << i)
        if (init >> m) & 1:
            r |= 1 << n
    return r


def cut_source(model, nid):
    """Cut variable behind a net through BUF/INV nodes, or None."""
    seen = 0
    while seen < 64:
        d = model.drv[nid]
        if d is None:
            return None
        if d[0] == 'v':
            return d[1]
        if d[0] != 'n':
            return None
        op, ins, _ = model.nodes[nid]
        if op not in ('BUF', 'INV'):
            return None
        nid = ins[0]
        seen += 1
    return None


def pick(parsed, model, mode, instance):
    dsink = {}
    for c in parsed.cells:
        if ne.ff_info(c.typ):
            pins = dict(c.pins)
            if 'D' in pins:
                dsink.setdefault(pins['D'], c.name)
    for c in parsed.cells:
        if instance is not None and c.name != instance:
            continue
        m = LUTK_RE.match(c.typ)
        if not m:
            if instance is not None:
                raise ne.NetlistError('instance %s is a %s, not a LUT1..LUT6' % (c.name, c.typ))
            continue
        k = int(m.group(1))
        pins = dict(c.pins)
        init = ne.literal_int(c.params.get('INIT', '0')) & ((1 << (1 << k)) - 1)
        if instance is None:
            if pins.get('O') not in dsink:
                continue
            srcs = [cut_source(model, model.net_id[pins['I%d' % j]])
                    if 'I%d' % j in pins else None for j in range(k)]
            if None in srcs or len(set(srcs)) != k:
                continue
        if mode == 'flip':
            return c, k, init, None
        for i in range(k):
            for j in range(i + 1, k):
                if swapped_init(init, k, i, j) != init and \
                        'I%d' % i in pins and 'I%d' % j in pins:
                    return c, k, init, (i, j)
        if instance is not None:
            raise ne.NetlistError('LUT %s is symmetric in every input pair' % c.name)
    if instance is not None:
        raise ne.NetlistError('instance %s not found' % instance)
    raise ne.NetlistError('no LUT drives a flip-flop D pin from distinct cut variables'
                          '%s; choose one with --instance' % (
                              ' with an asymmetric input pair' if mode == 'swap' else ''))


def instance_block(text, c):
    ref = ('\\' + c.name + ' ') if not PLAIN_ID.match(c.name) else c.name
    pat = re.compile(r'(?:(?<=\s)|^)' + re.escape(ref) + r'\s*\(', re.M)
    mo = pat.search(text)
    if not mo:
        raise ne.NetlistError('instance %s not found in the text' % c.name)
    start = text.rindex(c.typ, 0, mo.start())
    end = text.index(';', mo.end()) + 1
    return start, end


def main(argv=None):
    ap = argparse.ArgumentParser(description='Write a one-LUT mutant of a netgen netlist.')
    ap.add_argument('base')
    ap.add_argument('out')
    ap.add_argument('--mode', choices=('flip', 'swap'), required=True)
    ap.add_argument('--instance', help='LUT instance name as in the netlist (without backslash)')
    a = ap.parse_args(argv)
    try:
        P = ne.parse_netlist(a.base)
        M = ne.Model('base', ne.parse_netlist(a.base), [])
        c, k, init, pair = pick(P, M, a.mode, a.instance)
        with open(a.base, encoding='latin-1', newline='') as f:
            text = f.read()
        start, end = instance_block(text, c)
        block = text[start:end]
        if pair is None:
            mo = re.search(r"\.INIT\s*\(\s*(\d*'[hHbB][0-9A-Fa-f_]+)\s*\)", block)
            if not mo:
                raise ne.NetlistError('no INIT literal in instance %s' % c.name)
            width = 1 << k
            new = "%d'h%0*X" % (width, (width + 3) // 4, init ^ 1)
            nb = block[:mo.start(1)] + new + block[mo.end(1):]
            what = 'INIT %s -> %s' % (mo.group(1), new)
        else:
            i, j = pair
            pi = re.search(r'\.I%d\s*\(([^()]*)\)' % i, block)
            pj = re.search(r'\.I%d\s*\(([^()]*)\)' % j, block)
            if not pi or not pj:
                raise ne.NetlistError('cannot locate pins I%d/I%d of %s' % (i, j, c.name))
            spans = sorted([(pi.start(1), pi.end(1), pj.group(1)),
                            (pj.start(1), pj.end(1), pi.group(1))])
            nb = block
            for s, e, rep in reversed(spans):
                nb = nb[:s] + rep + nb[e:]
            what = 'I%d (%s) <-> I%d (%s), INIT kept' % (i, pi.group(1).strip(), j,
                                                       pj.group(1).strip())
        out = text[:start] + nb + text[end:]
        # self-check: the mutant parses and the cell really changed
        with open(a.out, 'w', encoding='latin-1', newline='') as f:
            f.write(out)
        Q = ne.parse_netlist(a.out)
        after = [x for x in Q.cells if x.name == c.name]
        if len(after) != 1 or (after[0].params, after[0].pins) == (c.params, c.pins):
            raise ne.NetlistError('mutation of %s did not take effect' % c.name)
        sinks = [x.name for x in P.cells if ne.ff_info(x.typ)
                 and dict(x.pins).get('D') == dict(c.pins).get('O')]
        print('%s: %s %s: %s; drives D of %s' % (a.mode, c.typ, c.name, what,
                                                ', '.join(sinks) or '(no flip-flop)'))
        print('wrote %s' % a.out)
        return 0
    except (ne.NetlistError, OSError) as e:
        print('ERROR: %s' % e)
        return 2


if __name__ == '__main__':
    sys.exit(main())
