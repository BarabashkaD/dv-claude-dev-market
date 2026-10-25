"""Real CMake/Ninja regression tests for v2 multi-repository profiles."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HOOK = Path(__file__).resolve().parents[1] / 'hooks' / 'clangd_guard.py'
spec = importlib.util.spec_from_file_location('guard', HOOK)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class MultiRepoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='guard multi é ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cmake = self.root / 'superbuild'
        self.cmake.mkdir()
        self.src = self.root / 'sibling' / 'src'
        self.src.mkdir(parents=True)
        self.main = self.src / 'main.cpp'
        self.main.write_text('int main() {return 0;}\n')
        self.excluded = self.src / 'other_platform.cpp'
        self.excluded.write_text('int other_platform() {return 0;}\n')
        (self.src / 'api.hpp').write_text('#pragma once\n')
        (self.cmake / 'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.20)
project(multi LANGUAGES CXX)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
add_executable(app ../sibling/src/main.cpp)
''')
        self.profile = {
            'version': 2, 'workspaceRoot': '.', 'cmakeSourceRoot': 'superbuild',
            'configuration': 'Debug', 'buildDir': 'build/debug', 'autoConfigure': True,
            'configure': {'command': ['cmake', '-S', 'superbuild', '-B', 'build/debug', '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Debug'], 'cwd': '.', 'timeoutSeconds': 60},
            'configureInputs': ['superbuild/CMakeLists.txt'], 'environmentVariables': ['CC', 'CXX'],
            'sourceRoots': ['sibling/src'],
            'excludedSources': [{'path': 'sibling/src/other_platform.cpp', 'reason': 'Other-platform implementation, not selected for Debug fixture'}],
        }
        self.config = self.root / '.clangd-guard.json'
        self.env = {**os.environ, 'CLANGD_GUARD_CONFIG': str(self.config), 'CLANGD_GUARD_STATE_DIR': str(self.root / 'user-state')}
        self.save()
        self.approve()

    def save(self):
        self.config.write_text(json.dumps(self.profile))

    def approve(self):
        result = subprocess.run([sys.executable, str(HOOK), '--approve', '--project-dir', str(self.root)], env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def run_guard(self, targets=None):
        payload = {'tool_name': 'LSP', 'cwd': str(self.root), 'tool_input': {'files': [{'file_path': str(p)} for p in (targets or [self.main])]}}
        result = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def require_tools(self):
        if not all(shutil.which(tool) for tool in ('cmake', 'ninja')) or not any(shutil.which(tool) for tool in ('g++', 'clang++', 'cl')):
            self.skipTest('real CMake/Ninja/compiler unavailable')

    def state(self):
        return json.loads((self.root / 'build/debug/.clangd-guard/state.json').read_text())

    def test_sibling_guarded_and_legitimate_exclusion_reported(self):
        self.require_tools()
        self.assertEqual(self.run_guard(), '')
        state = self.state()
        self.assertEqual(state['cmake_source_root'], str(self.cmake))
        self.assertIn(str(self.excluded), state['source_members'])
        self.assertIn(str(self.excluded), state['excluded_sources'])
        self.assertEqual(self.run_guard(), '')
        self.assertEqual(self.state(), state)
        self.assertIn('NOT VALIDATED in Debug', self.run_guard([self.excluded]))
        self.assertEqual(self.run_guard([self.src / 'api.hpp']), '')
        self.main.write_text('int main() {return 1;}\n')
        self.assertEqual(self.run_guard(), '')
        self.assertEqual(self.state(), state)

    def test_new_unlisted_source_is_not_silently_excluded(self):
        self.require_tools()
        self.assertEqual(self.run_guard(), '')
        state = self.state()
        (self.src / 'new.cpp').write_text('int added(){return 1;}\n')
        self.assertIn('translation units are absent', self.run_guard())
        self.assertEqual(self.state(), state)

    def test_new_source_added_to_cmake_reconfigures(self):
        self.require_tools()
        self.assertEqual(self.run_guard(), '')
        (self.src / 'new.cpp').write_text('int added(){return 1;}\n')
        with (self.cmake / 'CMakeLists.txt').open('a') as f:
            f.write('target_sources(app PRIVATE ../sibling/src/new.cpp)\n')
        self.assertEqual(self.run_guard(), '')
        self.assertIn(str(self.src / 'new.cpp'), self.state()['database_members'])
        (self.src / 'new.cpp').unlink()
        result = self.run_guard()
        self.assertIn('deny', result)

    def test_wrong_cmake_root_never_blesses_database(self):
        self.require_tools()
        self.profile['cmakeSourceRoot'] = '.'
        self.save(); self.approve()
        self.assertIn('selected CMake source root', self.run_guard())
        self.assertFalse((self.root / 'build/debug/.clangd-guard/state.json').exists())

    def test_wrong_configuration_and_multiconfig_rejected(self):
        self.require_tools()
        self.profile['configuration'] = 'Release'
        self.save(); self.approve()
        self.assertIn('CMAKE_BUILD_TYPE', self.run_guard())
        self.profile['configuration'] = 'Debug'
        self.profile['configure']['command'].append('-DCMAKE_CONFIGURATION_TYPES=Debug;Release')
        self.save(); self.approve()
        self.assertIn('single-configuration', self.run_guard())

    def test_configuration_switch_requires_approval(self):
        self.require_tools()
        self.assertEqual(self.run_guard(), '')
        self.profile['configuration'] = 'Release'
        self.profile['configure']['command'][-1] = '-DCMAKE_BUILD_TYPE=Release'
        self.save()
        self.assertIn('profile changed after approval', self.run_guard())
        self.approve()
        self.assertEqual(self.run_guard(), '')
        self.assertEqual(self.state()['configuration'], 'Release')

    def test_stale_exclusion_now_compiled_rejected(self):
        self.require_tools()
        self.assertEqual(self.run_guard(), '')
        with (self.cmake / 'CMakeLists.txt').open('a') as f:
            f.write('target_sources(app PRIVATE ../sibling/src/other_platform.cpp)\n')
        self.assertIn('excluded source is compiled', self.run_guard())

    def test_removed_exclusion_requires_profile_review(self):
        self.require_tools()
        self.assertEqual(self.run_guard(), '')
        self.excluded.unlink()
        self.assertIn('excluded source no longer exists', self.run_guard())

    def test_scope_and_mixed_payload_never_bypass(self):
        for target in (self.root / 'outside.cpp', self.root.parent / 'escape.cpp', self.root / 'untracked.hpp'):
            result = self.run_guard([self.main, target])
            self.assertIn('NOT VALIDATED', result)
            self.assertIn('deny', result)
        self.assertFalse((self.root / 'build').exists())

    def test_exclusion_does_not_authorize_query_or_configure(self):
        self.assertIn('NOT VALIDATED in Debug', self.run_guard([self.excluded]))
        self.assertFalse((self.root / 'build').exists())

    def test_v2_failed_configure_preserves_state(self):
        self.require_tools()
        self.assertEqual(self.run_guard(), '')
        original = self.state()
        self.profile['configure']['command'] = [sys.executable, '-c', 'raise SystemExit(7)']
        self.save(); self.approve()
        self.assertIn('configure failed with exit code 7', self.run_guard())
        self.assertEqual(self.state(), original)

    def test_v2_file_membership_is_not_optional(self):
        self.profile['sourceExtensions'] = ['.h']
        (self.src / 'new.cpp').write_text('int missing(){return 0;}\n')
        self.save()
        self.assertIn('sourceExtensions must include', self.run_guard())
        self.assertFalse((self.root / 'build').exists())

    def test_symlink_root_escape_rejected(self):
        link = self.root / 'escaped'
        try:
            link.symlink_to(self.root.parent, target_is_directory=True)
        except OSError:
            self.skipTest('symlinks unavailable')
        self.profile['sourceRoots'].append('escaped')
        self.save()
        self.assertIn('within workspaceRoot', self.run_guard())

    def test_profile_rejects_invalid_exclusions_and_roots(self):
        cases = [
            {'sourceRoots': ['missing']}, {'sourceRoots': ['..']},
            {'cmakeSourceRoot': '..'}, {'projectRoot': '.'},
            {'sourceExtensions': ['.h']},
            {'excludedSources': [{'path': 'sibling/src/*.cpp', 'reason': 'bad glob'}]},
            {'excludedSources': [{'path': '../escape.cpp', 'reason': 'escape'}]},
            {'excludedSources': [{'path': 'sibling/src/other_platform.cpp', 'reason': ''}]},
            {'excludedSources': [{'path': 'sibling/src/other_platform.cpp', 'reason': 'one'}] * 2},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                raw = {**self.profile, **changes}
                with self.assertRaises(guard.GuardError):
                    guard._validate_profile(raw, self.config, self.root)


if __name__ == '__main__':
    unittest.main()
