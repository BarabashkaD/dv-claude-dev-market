from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unittest
import shutil


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
HOOK = PLUGIN_ROOT / "hooks" / "clangd_guard.py"
REPOSITORY_ROOT = PLUGIN_ROOT.parents[1]


class ClangdGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        # The managed Windows runner can expose a read-only package temp
        # directory. Keep the isolated fixture under the checked-out workspace
        # instead; TemporaryDirectory still removes it after every test.
        self.temp = tempfile.TemporaryDirectory(prefix="clangd guard é ", dir=str(REPOSITORY_ROOT))
        self.root = Path(self.temp.name) / "project space é"
        self.root.mkdir(parents=True)
        (self.root / "src").mkdir()
        (self.root / "include").mkdir()
        (self.root / "cmake").mkdir()
        (self.root / "src" / "main.cpp").write_text('#include "answer.hpp"\nint main() { return answer(); }\n', encoding="utf-8")
        (self.root / "include" / "answer.hpp").write_text("inline int answer() { return 0; }\n", encoding="utf-8")
        (self.root / "cmake" / "Options.cmake").write_text("set(DV_GUARD_OPTION ON)\n", encoding="utf-8")
        (self.root / "CMakeLists.txt").write_text(
            textwrap.dedent(
                """
                cmake_minimum_required(VERSION 3.20)
                project(guard_fixture LANGUAGES CXX)
                include(cmake/Options.cmake)
                set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
                add_executable(guard_fixture src/main.cpp)
                target_include_directories(guard_fixture PRIVATE include)
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        (self.root / "CMakePresets.json").write_text(
            json.dumps(
                {
                    "version": 6,
                    "configurePresets": [
                        {
                            "name": "debug",
                            "generator": "Ninja",
                            "binaryDir": "${sourceDir}/build/debug",
                            "cacheVariables": {"CMAKE_EXPORT_COMPILE_COMMANDS": "ON"},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.config = self.root / ".clangd-guard.json"
        self.state_root = Path(self.temp.name) / "user-state"
        self.write_profile()
        self.approve_profile()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_profile(self, **changes: object) -> None:
        profile = {
            "version": 1,
            "projectRoot": ".",
            "buildDir": "build/debug",
            "autoConfigure": True,
            "configure": {
                "command": ["cmake", "--preset", "debug"],
                "cwd": ".",
                "timeoutSeconds": 30,
            },
            "configureInputs": ["CMakeLists.txt", "CMakePresets.json"],
            "environmentVariables": ["CC", "CXX"],
            "sourceRoots": ["src", "include"],
        }
        profile.update(changes)
        self.config.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    def approve_profile(self) -> None:
        result = subprocess.run(
            [sys.executable, str(HOOK), "--approve", "--project-dir", str(self.root)],
            text=True,
            capture_output=True,
            env={**os.environ, "CLANGD_GUARD_CONFIG": str(self.config), "CLANGD_GUARD_STATE_DIR": str(self.state_root)},
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def run_guard(self, *, cwd: Path | None = None, target: Path | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["CLAUDE_PROJECT_DIR"] = str(self.root)
        env["CLANGD_GUARD_CONFIG"] = str(self.config)
        env["CLANGD_GUARD_STATE_DIR"] = str(self.state_root)
        payload = {
            "cwd": str(cwd or self.root),
            "project_directory": str(self.root),
            "tool_name": "LSP",
            "tool_input": {"file_path": str(target or self.root / "src" / "main.cpp")},
        }
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def state(self) -> dict[str, object]:
        return json.loads((self.root / "build" / "debug" / ".clangd-guard" / "state.json").read_text(encoding="utf-8"))

    def require_cmake_fixture(self) -> None:
        if subprocess.run(["cmake", "--version"], capture_output=True).returncode != 0:
            self.skipTest("cmake is not installed")
        if subprocess.run(["ninja", "--version"], capture_output=True).returncode != 0:
            self.skipTest("ninja is not installed")
        compiler_found = any(shutil.which(candidate) for candidate in ("c++", "clang++", "g++", "cl"))
        if not compiler_found:
            self.skipTest("no C++ compiler is available for the real CMake fixture")
        profile = json.loads(self.config.read_text(encoding="utf-8"))
        profile["configure"]["timeoutSeconds"] = 180
        self.config.write_text(json.dumps(profile, indent=2), encoding="utf-8")
        self.approve_profile()

    def test_first_call_configures_real_fixture_and_second_call_is_noop(self) -> None:
        self.require_cmake_fixture()
        first = self.run_guard()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, "", first.stdout)
        first_state = self.state()
        second = self.run_guard()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(second.stdout, "")
        self.assertEqual(first_state, self.state())

    def test_source_body_edit_does_not_reconfigure_but_membership_does(self) -> None:
        self.require_cmake_fixture()
        self.assertEqual(self.run_guard().returncode, 0)
        original = self.state()
        (self.root / "src" / "main.cpp").write_text("int main() { return 0; }\n", encoding="utf-8")
        self.assertEqual(self.run_guard().returncode, 0)
        self.assertEqual(original["configured_at"], self.state()["configured_at"])
        (self.root / "src" / "new.cpp").write_text("int new_function() { return 1; }\n", encoding="utf-8")
        blocked = self.run_guard()
        self.assertEqual(blocked.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', blocked.stdout)
        self.assertEqual(original, self.state())

    def test_nested_cmake_input_is_discovered_and_triggers_configure(self) -> None:
        self.require_cmake_fixture()
        self.assertEqual(self.run_guard().returncode, 0)
        original = self.state()
        self.assertIn(str((self.root / "cmake" / "Options.cmake").resolve()), original["configure_inputs"])
        time.sleep(0.01)
        (self.root / "cmake" / "Options.cmake").write_text("set(DV_GUARD_OPTION OFF)\n", encoding="utf-8")
        self.assertEqual(self.run_guard().returncode, 0)
        self.assertGreater(self.state()["configured_at"], original["configured_at"])

    def test_first_configure_rechecks_new_file_api_input(self) -> None:
        script = self.root / "discover_input.py"
        marker = self.root / "configure-count.txt"
        script.write_text(
            textwrap.dedent(
                f"""
                import json, pathlib
                root = pathlib.Path.cwd()
                marker = pathlib.Path({str(marker)!r})
                marker.write_text(str(int(marker.read_text() or '0') + 1) if marker.exists() else '1', encoding='utf-8')
                build = root / 'build' / 'debug'
                build.mkdir(parents=True, exist_ok=True)
                (build / 'compile_commands.json').write_text(json.dumps([{{'directory': str(build), 'file': str(root / 'src' / 'main.cpp'), 'command': 'c++ -c main.cpp'}}]), encoding='utf-8')
                (build / 'CMakeCache.txt').write_text('CMAKE_HOME_DIRECTORY:INTERNAL=' + str(root) + '\\n', encoding='utf-8')
                reply = build / '.cmake' / 'api' / 'v1' / 'reply'
                reply.mkdir(parents=True, exist_ok=True)
                (reply / 'cmakeFiles-v1-test.json').write_text(json.dumps({{'kind': 'cmakeFiles', 'paths': {{'source': str(root), 'build': str(build)}}, 'inputs': [{{'path': 'CMakeLists.txt'}}, {{'path': 'cmake/Options.cmake', 'isExternal': True}}]}}), encoding='utf-8')
                (reply / 'index-test.json').write_text(json.dumps({{'objects': [{{'kind': 'cmakeFiles', 'jsonFile': 'cmakeFiles-v1-test.json'}}]}}), encoding='utf-8')
                """
            ),
            encoding="utf-8",
        )
        self.write_profile(
            configure={"command": [sys.executable, str(script)], "cwd": ".", "timeoutSeconds": 30},
            configureInputs=["CMakeLists.txt", "CMakePresets.json", "discover_input.py"],
        )
        self.approve_profile()
        result = self.run_guard()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(marker.read_text(encoding="utf-8"), "2")
        self.assertIn(str((self.root / "cmake" / "Options.cmake").resolve()), self.state()["configure_inputs"])

    def test_malformed_and_replaced_database_are_blocked_without_auto_configure(self) -> None:
        self.require_cmake_fixture()
        self.assertEqual(self.run_guard().returncode, 0)
        original = self.state()
        self.write_profile(autoConfigure=False)
        database = self.root / "build" / "debug" / "compile_commands.json"
        database.write_text("{not json", encoding="utf-8")
        malformed = self.run_guard()
        self.assertEqual(malformed.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', malformed.stdout)
        self.assertEqual(original, self.state())
        database.write_text("[]", encoding="utf-8")
        replaced = self.run_guard()
        self.assertEqual(replaced.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', replaced.stdout)
        self.assertEqual(original, self.state())

    def test_failed_configure_does_not_bless_old_database(self) -> None:
        self.require_cmake_fixture()
        self.assertEqual(self.run_guard().returncode, 0)
        original = self.state()
        fail = self.root / "fail_configure.py"
        fail.write_text("raise SystemExit('intentional configure failure')\n", encoding="utf-8")
        self.write_profile(
            configure={"command": [sys.executable, str(fail)], "cwd": ".", "timeoutSeconds": 30}
        )
        self.approve_profile()
        result = self.run_guard()
        self.assertEqual(result.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', result.stdout)
        self.assertEqual(original, self.state())

    def test_successful_command_cannot_bless_a_different_build_identity(self) -> None:
        seed = self.root / "seed.py"
        seed.write_text(
            textwrap.dedent(
                f"""
                import json, pathlib
                root = pathlib.Path.cwd()
                build = root / 'build' / 'debug'
                build.mkdir(parents=True, exist_ok=True)
                (build / 'compile_commands.json').write_text(json.dumps([{{'directory': str(build), 'file': str(root / 'src' / 'main.cpp'), 'command': 'c++ -c main.cpp'}}]), encoding='utf-8')
                (build / 'CMakeCache.txt').write_text('CMAKE_HOME_DIRECTORY:INTERNAL=' + str(root) + '\\n', encoding='utf-8')
                reply = build / '.cmake' / 'api' / 'v1' / 'reply'
                reply.mkdir(parents=True, exist_ok=True)
                (reply / 'cmakeFiles-v1-test.json').write_text(json.dumps({{'kind': 'cmakeFiles', 'paths': {{'source': str(root), 'build': str(build)}}, 'inputs': [{{'path': 'CMakeLists.txt'}}]}}))
                (reply / 'index-test.json').write_text(json.dumps({{'objects': [{{'kind': 'cmakeFiles', 'jsonFile': 'cmakeFiles-v1-test.json'}}]}}))
                """
            ),
            encoding="utf-8",
        )
        self.write_profile(
            configure={"command": [sys.executable, str(seed)], "cwd": ".", "timeoutSeconds": 30},
            configureInputs=["CMakeLists.txt", "CMakePresets.json", "seed.py"],
        )
        self.approve_profile()
        first = self.run_guard()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, "", first.stdout)
        original = self.state()
        wrong_root = self.root / "another-project"
        wrong_root.mkdir()
        wrong_configure = self.root / "wrong_build.py"
        wrong_configure.write_text(
            f"from pathlib import Path; Path({str(self.root / 'build' / 'debug' / 'CMakeCache.txt')!r}).write_text('CMAKE_HOME_DIRECTORY:INTERNAL=' + {str(wrong_root)!r} + '\\n')\n",
            encoding="utf-8",
        )
        (self.root / "trigger.cmake").write_text("set(TRIGGER ON)\n", encoding="utf-8")
        self.write_profile(
            configure={"command": [sys.executable, str(wrong_configure)], "cwd": ".", "timeoutSeconds": 30},
            configureInputs=["CMakeLists.txt", "CMakePresets.json", "trigger.cmake"],
        )
        self.approve_profile()
        result = self.run_guard()
        self.assertEqual(result.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', result.stdout)
        self.assertEqual(original, self.state())

    def test_repo_supplied_trust_file_is_ignored(self) -> None:
        for trust in self.state_root.rglob("*.json"):
            trust.unlink()
        (self.root / ".clangd-guard.trust.json").write_text("{}\n", encoding="utf-8")
        result = self.run_guard()
        self.assertEqual(result.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', result.stdout)
        self.assertFalse((self.root / "build" / "debug" / ".clangd-guard" / "state.json").exists())

    def test_queried_translation_unit_outside_source_roots_is_denied(self) -> None:
        seed = self.root / "seed.py"
        seed.write_text(
            textwrap.dedent(
                """
                import json, pathlib
                root = pathlib.Path.cwd()
                build = root / 'build' / 'debug'
                build.mkdir(parents=True, exist_ok=True)
                (build / 'compile_commands.json').write_text(json.dumps([{'directory': str(build), 'file': str(root / 'src' / 'main.cpp'), 'command': 'c++ -c main.cpp'}]), encoding='utf-8')
                (build / 'CMakeCache.txt').write_text('CMAKE_HOME_DIRECTORY:INTERNAL=' + str(root) + '\\n', encoding='utf-8')
                reply = build / '.cmake' / 'api' / 'v1' / 'reply'
                reply.mkdir(parents=True, exist_ok=True)
                (reply / 'cmakeFiles-v1-test.json').write_text(json.dumps({'kind': 'cmakeFiles', 'paths': {'source': str(root), 'build': str(build)}, 'inputs': [{'path': 'CMakeLists.txt'}]}))
                (reply / 'index-test.json').write_text(json.dumps({'objects': [{'kind': 'cmakeFiles', 'jsonFile': 'cmakeFiles-v1-test.json'}]}))
                """
            ),
            encoding="utf-8",
        )
        self.write_profile(
            configure={"command": [sys.executable, str(seed)], "cwd": ".", "timeoutSeconds": 30},
            configureInputs=["CMakeLists.txt", "CMakePresets.json", "seed.py"],
        )
        self.approve_profile()
        self.assertEqual(self.run_guard().returncode, 0)
        extra = self.root / "generated" / "extra.cpp"
        extra.parent.mkdir()
        extra.write_text("int extra() { return 0; }\n", encoding="utf-8")
        blocked = self.run_guard(target=extra)
        self.assertEqual(blocked.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', blocked.stdout)

    def test_timeout_and_crash_fail_closed(self) -> None:
        self.require_cmake_fixture()
        self.assertEqual(self.run_guard().returncode, 0)
        original = self.state()
        slow = self.root / "slow_configure.py"
        slow.write_text("import time; time.sleep(2)\n", encoding="utf-8")
        self.write_profile(
            configure={"command": [sys.executable, str(slow)], "cwd": ".", "timeoutSeconds": 0.05}
        )
        self.approve_profile()
        timed_out = self.run_guard()
        self.assertEqual(timed_out.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', timed_out.stdout)
        self.assertEqual(original, self.state())
        crash = self.root / "crash_configure.py"
        crash.write_text("raise RuntimeError('intentional crash')\n", encoding="utf-8")
        self.write_profile(
            configure={"command": [sys.executable, str(crash)], "cwd": ".", "timeoutSeconds": 30}
        )
        self.approve_profile()
        crashed = self.run_guard()
        self.assertEqual(crashed.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', crashed.stdout)
        self.assertEqual(original, self.state())

    def test_concurrent_calls_serialize_and_recheck(self) -> None:
        script = self.root / "slow_success.py"
        database = self.root / "build" / "debug" / "compile_commands.json"
        marker = self.root / "configure-count.txt"
        script.write_text(
            textwrap.dedent(
                f"""
                import json, pathlib, time
                marker = pathlib.Path({str(marker)!r})
                count = int(marker.read_text() or '0') if marker.exists() else 0
                marker.write_text(str(count + 1))
                time.sleep(0.3)
                root = pathlib.Path.cwd()
                db = root / 'build' / 'debug' / 'compile_commands.json'
                db.parent.mkdir(parents=True, exist_ok=True)
                db.write_text(json.dumps([{{'directory': str(db.parent), 'file': str(root / 'src' / 'main.cpp'), 'command': 'c++ -c main.cpp'}}]))
                reply = root / 'build' / 'debug' / '.cmake' / 'api' / 'v1' / 'reply'
                reply.mkdir(parents=True, exist_ok=True)
                (reply / 'cmakeFiles-v1-test.json').write_text(json.dumps({{'kind': 'cmakeFiles', 'paths': {{'source': str(root), 'build': str(db.parent)}}, 'inputs': [{{'path': 'CMakeLists.txt'}}]}}))
                (reply / 'index-test.json').write_text(json.dumps({{'objects': [{{'kind': 'cmakeFiles', 'jsonFile': 'cmakeFiles-v1-test.json'}}]}}))
                """
            ),
            encoding="utf-8",
        )
        self.write_profile(
            configure={"command": [sys.executable, str(script)], "cwd": ".", "timeoutSeconds": 30},
            configureInputs=["CMakeLists.txt", "CMakePresets.json", "slow_success.py"],
        )
        self.approve_profile()
        database.parent.mkdir(parents=True, exist_ok=True)
        database.write_text(
            json.dumps([{"directory": str(database.parent), "file": str(self.root / "src" / "main.cpp"), "command": "c++ -c main.cpp"}]),
            encoding="utf-8",
        )
        (self.root / "build" / "debug" / "CMakeCache.txt").write_text(
            f"CMAKE_HOME_DIRECTORY:INTERNAL={self.root}", encoding="utf-8"
        )
        self.write_file_api_reply()
        results: list[subprocess.CompletedProcess[str]] = []

        def invoke() -> None:
            results.append(self.run_guard())

        first = threading.Thread(target=invoke)
        second = threading.Thread(target=invoke)
        first.start()
        time.sleep(0.05)
        second.start()
        first.join()
        second.join()
        self.assertEqual(len(results), 2)
        self.assertTrue(all(result.returncode == 0 for result in results), results)
        self.assertEqual(marker.read_text(encoding="utf-8"), "1", [result.stdout + result.stderr for result in results])

    def test_hook_payload_without_profile_returns_structured_deny(self) -> None:
        self.config.unlink()
        result = self.run_guard()
        self.assertEqual(result.returncode, 0)
        decision = json.loads(result.stdout)
        self.assertEqual(decision["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_unrelated_or_outside_lsp_targets_are_not_guarded(self) -> None:
        python_payload = {
            "cwd": str(self.root),
            "project_directory": str(self.root),
            "tool_name": "LSP",
            "tool_input": {"file_path": str(self.root / "script.py")},
        }
        env = os.environ.copy()
        env["CLAUDE_PROJECT_DIR"] = str(self.root)
        env["CLANGD_GUARD_CONFIG"] = str(self.config)
        skipped = subprocess.run(
            [sys.executable, str(HOOK)], input=json.dumps(python_payload), text=True, capture_output=True, env=env
        )
        self.assertEqual(skipped.returncode, 0)
        self.assertEqual(skipped.stdout, "")
        outside = dict(python_payload)
        outside["tool_input"] = {"file_path": str(Path(self.temp.name) / "outside.cpp")}
        skipped_outside = subprocess.run(
            [sys.executable, str(HOOK)], input=json.dumps(outside), text=True, capture_output=True, env=env
        )
        self.assertEqual(skipped_outside.returncode, 0)
        self.assertEqual(skipped_outside.stdout, "")

    def write_file_api_reply(self) -> None:
        reply = self.root / "build" / "debug" / ".cmake" / "api" / "v1" / "reply"
        reply.mkdir(parents=True, exist_ok=True)
        (reply / "cmakeFiles-v1-test.json").write_text(
            json.dumps(
                {
                    "kind": "cmakeFiles",
                    "paths": {"source": str(self.root), "build": str(reply.parents[3])},
                    "inputs": [{"path": "CMakeLists.txt"}],
                }
            ),
            encoding="utf-8",
        )
        (reply / "index-test.json").write_text(
            json.dumps({"objects": [{"kind": "cmakeFiles", "jsonFile": "cmakeFiles-v1-test.json"}]}),
            encoding="utf-8",
        )

    def test_manifests_and_hook_contract(self) -> None:
        plugin = json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads((REPOSITORY_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        hooks = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        self.assertIn("clangd-lsp@claude-plugins-official", plugin["dependencies"])
        self.assertIn("claude-plugins-official", marketplace["allowCrossMarketplaceDependenciesOn"])
        self.assertIn("dv-clangd-guard", {entry["name"] for entry in marketplace["plugins"]})
        hook = hooks["hooks"]["PreToolUse"][0]["hooks"][0]
        self.assertEqual(hooks["hooks"]["PreToolUse"][0]["matcher"], "LSP")
        self.assertEqual(hook["onFailure"], "block")
        self.assertEqual(hook["timeout"], 1830)
        self.assertEqual(hook["args"][0], "${CLAUDE_PLUGIN_ROOT}/hooks/clangd_guard.py")


if __name__ == "__main__":
    unittest.main()
