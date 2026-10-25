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
        (self.root / "compile_commands.json.in").write_text(
            "[{\"directory\":\"@CMAKE_BINARY_DIR@\",\"file\":\"@CMAKE_SOURCE_DIR@/src/main.cpp\",\"command\":\"c++ -c main.cpp\"}]\n",
            encoding="utf-8",
        )
        (self.root / "CMakeLists.txt").write_text(
            textwrap.dedent(
                """
                cmake_minimum_required(VERSION 3.20)
                project(guard_fixture NONE)
                include(cmake/Options.cmake)
                configure_file("${CMAKE_SOURCE_DIR}/compile_commands.json.in"
                  "${CMAKE_BINARY_DIR}/compile_commands.json" @ONLY)
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
        self.write_profile()

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

    def run_guard(self, *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["CLAUDE_PROJECT_DIR"] = str(self.root)
        env["CLANGD_GUARD_CONFIG"] = str(self.config)
        payload = {"cwd": str(cwd or self.root), "project_directory": str(self.root), "tool_name": "LSP"}
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

    def test_first_call_configures_real_fixture_and_second_call_is_noop(self) -> None:
        self.require_cmake_fixture()
        first = self.run_guard()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, "")
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
        self.assertEqual(self.run_guard().returncode, 0)
        self.assertGreater(self.state()["configured_at"], original["configured_at"])

    def test_nested_cmake_input_is_discovered_and_triggers_configure(self) -> None:
        self.require_cmake_fixture()
        self.assertEqual(self.run_guard().returncode, 0)
        original = self.state()
        self.assertIn(str((self.root / "cmake" / "Options.cmake").resolve()), original["configure_inputs"])
        time.sleep(0.01)
        (self.root / "cmake" / "Options.cmake").write_text("set(DV_GUARD_OPTION OFF)\n", encoding="utf-8")
        self.assertEqual(self.run_guard().returncode, 0)
        self.assertGreater(self.state()["configured_at"], original["configured_at"])

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
        result = self.run_guard()
        self.assertEqual(result.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', result.stdout)
        self.assertEqual(original, self.state())

    def test_timeout_and_crash_fail_closed(self) -> None:
        self.require_cmake_fixture()
        self.assertEqual(self.run_guard().returncode, 0)
        original = self.state()
        slow = self.root / "slow_configure.py"
        slow.write_text("import time; time.sleep(2)\n", encoding="utf-8")
        self.write_profile(
            configure={"command": [sys.executable, str(slow)], "cwd": ".", "timeoutSeconds": 0.05}
        )
        timed_out = self.run_guard()
        self.assertEqual(timed_out.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', timed_out.stdout)
        self.assertEqual(original, self.state())
        crash = self.root / "crash_configure.py"
        crash.write_text("raise RuntimeError('intentional crash')\n", encoding="utf-8")
        self.write_profile(
            configure={"command": [sys.executable, str(crash)], "cwd": ".", "timeoutSeconds": 30}
        )
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
                db = pathlib.Path({str(database)!r})
                db.parent.mkdir(parents=True, exist_ok=True)
                db.write_text(json.dumps([{{'directory': str(db.parent), 'file': str(pathlib.Path({str(self.root / 'src' / 'main.cpp')!r})), 'command': 'c++ -c main.cpp'}}]))
                """
            ),
            encoding="utf-8",
        )
        self.write_profile(
            configure={"command": [sys.executable, str(script)], "cwd": ".", "timeoutSeconds": 30},
            configureInputs=["CMakeLists.txt", "CMakePresets.json", "slow_success.py"],
        )
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
        self.assertEqual(marker.read_text(encoding="utf-8"), "1")

    def test_live_hook_payload_without_profile_returns_structured_deny(self) -> None:
        self.config.unlink()
        result = self.run_guard()
        self.assertEqual(result.returncode, 0)
        decision = json.loads(result.stdout)
        self.assertEqual(decision["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")

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
        self.assertEqual(hook["args"][0], "${CLAUDE_PLUGIN_ROOT}/hooks/clangd_guard.py")


if __name__ == "__main__":
    unittest.main()
