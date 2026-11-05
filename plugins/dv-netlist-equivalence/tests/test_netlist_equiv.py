"""Unit tests of netlist_equiv.py and make_mutant.py on synthetic netlists.

Run: python -m unittest discover -s plugins/dv-netlist-equivalence/tests -v
"""

import contextlib
import io
import os
import re
import subprocess
import sys
import tempfile
import unittest

import netgen_fixtures as fx

ne = fx.load('netlist_equiv')
mut = fx.load('make_mutant')


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='netlist equiv ')
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, text):
        p = os.path.join(self.tmp.name, name)
        with open(p, 'w', encoding='latin-1', newline='\n') as f:
            f.write(text)
        return p

    def run_tool(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            rc = ne.main(list(argv))
        return rc, out.getvalue()

    def compare(self, base_text, new_text, *opts):
        b = self.write('base.v', base_text)
        n = self.write('new.v', new_text)
        return self.run_tool(b, n, *opts)

    @staticmethod
    def section(out, title):
        """Lines of one '=== TITLE ...' section of the report."""
        m = re.search(r'^=== %s[^\n]*\n(.*?)(?=^===|^RESULT|\Z)' % re.escape(title),
                      out, re.S | re.M)
        return m.group(1) if m else ''

    def assertVerdict(self, rc, out, equivalent):
        if equivalent:
            self.assertEqual(rc, 0, out)
            self.assertIn('RESULT: EQUIVALENT', out)
        else:
            self.assertEqual(rc, 1, out)
            self.assertIn('RESULT: NOT EQUIVALENT', out)


class SelfAndRefactor(Case):
    def test_self_compare_is_equivalent(self):
        rc, out = self.compare(fx.design('base'), fx.design('base'))
        self.assertVerdict(rc, out, True)
        self.assertIn('mismatches: 0 checkpoint(s)', out)
        self.assertIn('random 0)', out)

    def test_equivalent_refactor(self):
        rc, out = self.compare(fx.design('base'), fx.design('refactor'), '--strip', 'u_core/')
        self.assertVerdict(rc, out, True)
        # every register is matched after the prefix is stripped
        self.assertIn('matched by name 7, base-only 0, new-only 1', out)
        # the duplicated register is folded into its original
        self.assertIn('new: r2 <- r2_1 (FD)', out)
        self.assertIn('new: r2_1 -> r2 (FD, correspondence)', out)
        # FDR vs FD with the reset in the D logic: normalised next state
        self.assertRegex(out, r'norm-ff\s+exhaustive\s+4')
        self.assertEqual(self.section(out, 'UNMATCHED CUT CELLS').strip(), '')

    def test_refactor_without_strip_is_not_equivalent(self):
        rc, out = self.compare(fx.design('base'), fx.design('refactor'))
        self.assertVerdict(rc, out, False)
        self.assertIn('base: r1 (FDE) USED', self.section(out, 'UNMATCHED CUT CELLS'))


class Mutants(Case):
    def mutant(self, variant):
        rc, out = self.compare(fx.design('base'), fx.design(variant))
        self.assertVerdict(rc, out, False)
        return out, self.section(out, 'MISMATCHES')

    def test_flipped_init_bit(self):
        out, mis = self.mutant('flip')
        self.assertIn('r1.D [raw-ff, exhaustive]', mis)
        self.assertIn('counterexample: port:a=0 port:b=0 port:c=0', mis)
        self.assertIn('value: base=0 new=1', mis)

    def test_swapped_lut_inputs(self):
        out, mis = self.mutant('swap')
        self.assertIn('r1.D [raw-ff, exhaustive]', mis)

    def test_changed_clock_enable(self):
        out, mis = self.mutant('ce')
        self.assertIn('r1.CE [raw-ff, exhaustive]', mis)
        self.assertIn('r1:NS [norm-ff', mis)

    def test_removed_register(self):
        out, mis = self.mutant('removed')
        self.assertIn('port:y3 [port, exhaustive]', mis)
        self.assertIn('base: r3 (FDR) USED', self.section(out, 'UNMATCHED CUT CELLS'))


class WideAndEnable(Case):
    def test_random_vectors_cannot_tell_w_from_k(self):
        """Precondition of the next tests: under the hypothesis w == k the
        random signatures of the next-state functions are equal."""
        path = self.write('wide.v', fx.wide_and_design())
        m = ne.Model('base', ne.parse_netlist(path), [])
        ctx = ne.Ctx(1, 4096)
        ctx.alias = {'base': {'w.Q': 'k.Q'}}
        ev = ne.Evaluator(ctx)
        sw, sk = ne.ff_specs(m, m.cuts['w']), ne.ff_specs(m, m.cuts['k'])
        for key in ('CLK', 'CLR', 'PRE', 'NS'):
            self.assertEqual(ev.rand_value(sw[key]), ev.rand_value(sk[key]), key)
        self.assertGreater(ne.popcount(ev.support(sw['NS'])), 16)

    def test_correspondence_does_not_merge_wide_enable_register(self):
        rc, out = self.compare(fx.wide_and_design(), fx.wide_and_design())
        self.assertVerdict(rc, out, True)
        self.assertEqual(self.section(out, 'REGISTER CORRESPONDENCE CLASSES').strip(), '')
        # the random signatures did not split w from k; the exact (BDD) step did
        self.assertRegex(out, r'base: iteration 1: exact check \(BDD \d+, random fallback 0 '
                              r'functions\): 1 class\(es\) split off')

    def test_output_moved_to_constant_register_is_detected(self):
        rc, out = self.compare(fx.wide_and_design(), fx.wide_and_design(wrong=True))
        self.assertVerdict(rc, out, False)
        self.assertIn('port:yw [port, exhaustive]', self.section(out, 'MISMATCHES'))


class InputErrors(Case):
    def test_unknown_cell_type_fails_loudly(self):
        text = fx.design('base').replace(
            '  OBUF   y1_OBUF (',
            '  FOOBAR42   mystery (\n    .I(a_IBUF_0),\n    .O(junk)\n  );\n  OBUF   y1_OBUF (', 1)
        self.assertIn('FOOBAR42', text)
        rc, out = self.compare(fx.design('base'), text)
        self.assertEqual(rc, 2, out)
        self.assertIn('unknown primitive type(s), refusing to guess: FOOBAR42 (x1)', out)
        self.assertNotIn('RESULT:', out)

    def test_dump_types_marks_unknown(self):
        text = fx.design('base').replace('BUFGP   clk_BUFGP', 'BUFGQ   clk_BUFGP')
        rc, out = self.run_tool('--dump-types', self.write('x.v', text))
        self.assertEqual(rc, 0)
        self.assertRegex(out, r'BUFGQ\s+1\s+UNKNOWN')
        self.assertRegex(out, r'FDE\s+1\s+ff')

    def test_hierarchical_netlist_is_refused(self):
        text = fx.design('base') + '\nmodule sub (a);\n  input a;\nendmodule\n'
        rc, out = self.compare(text, text)
        self.assertEqual(rc, 2, out)
        self.assertIn('hierarchical netlist', out)

    def test_missing_file_is_no_verdict(self):
        b = self.write('base.v', fx.design('base'))
        rc, out = self.run_tool(b, os.path.join(self.tmp.name, 'missing.v'))
        self.assertEqual(rc, 2, out)

    def test_help_documents_exit_codes(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit) as cm:
                ne.main(['--help'])
        self.assertEqual(cm.exception.code, 0)
        self.assertIn('exit codes', out.getvalue())
        self.assertIn('--strip', out.getvalue())


class MakeMutant(Case):
    def make(self, mode):
        b = self.write('base.v', fx.design('base'))
        m = os.path.join(self.tmp.name, 'mutant_%s.v' % mode)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = mut.main([b, m, '--mode', mode])
        self.assertEqual(rc, 0, out.getvalue())
        self.assertIn('drives D of r1', out.getvalue())
        return b, m

    def test_flip_mutant_is_detected(self):
        b, m = self.make('flip')
        rc, out = self.run_tool(b, m)
        self.assertVerdict(rc, out, False)
        self.assertIn('r1.D [raw-ff', self.section(out, 'MISMATCHES'))

    def test_swap_mutant_is_detected(self):
        b, m = self.make('swap')
        rc, out = self.run_tool(b, m)
        self.assertVerdict(rc, out, False)
        self.assertIn('r1.D [raw-ff', self.section(out, 'MISMATCHES'))

    def test_swapped_init_helper(self):
        f = fx.lut_init(3, lambda i0, i1, i2: (i0 & i1) | i2)
        g = fx.lut_init(3, lambda i0, i1, i2: (i2 & i1) | i0)
        self.assertEqual(mut.swapped_init(f, 3, 0, 2), g)
        self.assertEqual(mut.swapped_init(f, 3, 0, 1), f)


class CommandLine(Case):
    def test_cli_exit_codes(self):
        script = os.path.join(fx.SCRIPTS, 'netlist_equiv.py')
        b = self.write('base.v', fx.design('base'))
        n = self.write('new.v', fx.design('refactor'))
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        ok = subprocess.run([sys.executable, '-B', script, b, n, '--strip', 'u_core/'],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        self.assertEqual(ok.returncode, 0, ok.stdout.decode('latin-1'))
        bad = subprocess.run([sys.executable, '-B', script, b, n],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        self.assertEqual(bad.returncode, 1, bad.stdout.decode('latin-1'))


if __name__ == '__main__':
    unittest.main()
