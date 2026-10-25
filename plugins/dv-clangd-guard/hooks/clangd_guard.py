#!/usr/bin/env python3
"""Guard explicit Claude LSP calls with a configured CMake freshness check.

The hook deliberately does not install clangd, delete indexes, guess a CMake
build directory, or use a shell.  A project profile opts into the exact
configure command and build tree that the user trusts.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterable


STATE_VERSION = 1
DEFAULT_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".hxx",
    ".m",
    ".mm",
}


class GuardError(RuntimeError):
    pass


def _path(value: str, base: Path) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base / candidate
    return candidate.resolve(strict=False)


def _display(path: Path) -> str:
    return str(path)


def _read_json(path: Path, label: str) -> dict[str, Any] | list[Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise GuardError(f"{label} is missing: {_display(path)}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GuardError(f"{label} is unreadable or malformed: {_display(path)}") from exc


def _find_profile(payload: dict[str, Any]) -> tuple[dict[str, Any], Path, Path]:
    cwd = _path(str(payload.get("cwd") or os.getcwd()), Path.cwd())
    project_dir = _path(
        str(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("project_directory") or cwd),
        Path.cwd(),
    )
    configured = os.environ.get("CLANGD_GUARD_CONFIG")
    candidates = [_path(configured, Path.cwd())] if configured else []
    candidates.extend([cwd / ".clangd-guard.json", project_dir / ".clangd-guard.json"])
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve(strict=False)
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_file():
            profile = _read_json(candidate, "clangd-guard profile")
            if not isinstance(profile, dict):
                raise GuardError(f"clangd-guard profile must be an object: {_display(candidate)}")
            return profile, candidate, project_dir
    raise GuardError(
        "No explicit .clangd-guard.json profile found for this project. "
        "Run the dv-clangd-guard setup skill before using the LSP."
    )


def _validate_profile(profile: dict[str, Any], config_path: Path, project_dir: Path) -> dict[str, Any]:
    if profile.get("version") != 1:
        raise GuardError("clangd-guard profile must set version to 1")
    root = _path(str(profile.get("projectRoot", ".")), config_path.parent)
    if not root.is_dir():
        raise GuardError(f"configured projectRoot is not a directory: {_display(root)}")
    configured_build = profile.get("buildDir")
    if not isinstance(configured_build, str) or not configured_build:
        raise GuardError("clangd-guard profile must set an explicit buildDir")
    build_dir = _path(configured_build, root)

    auto_configure = profile.get("autoConfigure", False)
    if not isinstance(auto_configure, bool):
        raise GuardError("autoConfigure must be true or false")
    configure = profile.get("configure")
    if auto_configure:
        if not isinstance(configure, dict):
            raise GuardError("autoConfigure requires an explicit configure object")
        command = configure.get("command")
        if (
            not isinstance(command, list)
            or not command
            or any(not isinstance(part, str) or not part for part in command)
        ):
            raise GuardError("configure.command must be a non-empty argv list; shell strings are not allowed")
        configure_cwd = _path(str(configure.get("cwd", ".")), root)
        if not configure_cwd.is_dir():
            raise GuardError(f"configure.cwd is not a directory: {_display(configure_cwd)}")
        timeout = configure.get("timeoutSeconds", 120)
        if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 1800:
            raise GuardError("configure.timeoutSeconds must be between 0 and 1800")
    else:
        command = None
        configure_cwd = root
        timeout = 0

    inputs = profile.get("configureInputs", [])
    if not isinstance(inputs, list) or any(not isinstance(value, str) or not value for value in inputs):
        raise GuardError("configureInputs must be a list of non-empty paths")
    environment = profile.get("environmentVariables", [])
    if not isinstance(environment, list) or any(not isinstance(value, str) or not value for value in environment):
        raise GuardError("environmentVariables must be a list of names")
    source_roots = profile.get("sourceRoots", [])
    if not isinstance(source_roots, list) or any(not isinstance(value, str) or not value for value in source_roots):
        raise GuardError("sourceRoots must be a list of paths")
    extensions = profile.get("sourceExtensions", sorted(DEFAULT_EXTENSIONS))
    if not isinstance(extensions, list) or any(not isinstance(value, str) or not value.startswith(".") for value in extensions):
        raise GuardError("sourceExtensions must be a list of dot-prefixed extensions")

    state_dir = build_dir / ".clangd-guard"
    return {
        "profile": profile,
        "config_path": config_path.resolve(strict=False),
        "project_dir": project_dir,
        "project_root": root,
        "build_dir": build_dir,
        "database": build_dir / "compile_commands.json",
        "cache": build_dir / "CMakeCache.txt",
        "state_dir": state_dir,
        "state_path": state_dir / "state.json",
        "lock_path": state_dir / "configure.lock",
        "auto_configure": auto_configure,
        "configure_command": command,
        "configure_cwd": configure_cwd,
        "configure_timeout": float(timeout),
        "configure_inputs": [_path(value, root) for value in inputs],
        "environment_variables": environment,
        "source_roots": [_path(value, root) for value in source_roots],
        "source_extensions": set(extensions),
    }


def _iter_files(path: Path, ignored_dir: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    if not path.is_dir():
        return
    for current, directories, files in os.walk(path, topdown=True, followlinks=False):
        current_path = Path(current).resolve(strict=False)
        directories[:] = [
            name
            for name in directories
            if name != ".git"
            and _path(name, current_path) != ignored_dir
            and not _path(name, current_path).is_relative_to(ignored_dir)
        ]
        for name in files:
            candidate = current_path / name
            if candidate.is_file() and not candidate.is_symlink():
                yield candidate


def _digest_file(path: Path) -> str:
    if not path.is_file():
        return "<missing>"
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise GuardError(f"cannot read configure input: {_display(path)}") from exc
    return digest.hexdigest()


def _input_fingerprints(paths: Iterable[Path], build_dir: Path) -> dict[str, str]:
    fingerprints: dict[str, str] = {}
    for path in paths:
        path = path.resolve(strict=False)
        files = list(_iter_files(path, build_dir))
        if not files:
            fingerprints[_display(path)] = "<missing>"
            continue
        for file_path in sorted(set(files)):
            fingerprints[_display(file_path)] = _digest_file(file_path)
    return fingerprints


def _environment_fingerprints(names: Iterable[str]) -> dict[str, str | None]:
    return {name: os.environ.get(name) for name in names}


def _database_members(database: Path) -> tuple[str, list[str]]:
    if not database.is_file():
        return "<missing>", []
    try:
        raw = database.read_bytes()
    except OSError as exc:
        raise GuardError(f"cannot read compile database: {_display(database)}") from exc
    digest = hashlib.sha256(raw).hexdigest()
    try:
        entries = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GuardError(f"compile database is malformed: {_display(database)}") from exc
    if not isinstance(entries, list):
        raise GuardError(f"compile database must be a JSON array: {_display(database)}")
    members: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or not isinstance(entry.get("file"), str) or not entry["file"]:
            raise GuardError(f"compile database entry {index} has no file path: {_display(database)}")
        if not isinstance(entry.get("directory"), str) or not entry["directory"]:
            raise GuardError(f"compile database entry {index} has no directory: {_display(database)}")
        if not isinstance(entry.get("command"), str) and not isinstance(entry.get("arguments"), list):
            raise GuardError(f"compile database entry {index} has no command or arguments: {_display(database)}")
        file_path = Path(entry["file"])
        if not file_path.is_absolute():
            file_path = Path(entry["directory"]) / file_path
        members.append(_display(file_path.resolve(strict=False)))
    return digest, sorted(set(members))


def _source_members(profile: dict[str, Any], database_members: list[str]) -> list[str]:
    if not profile["source_roots"]:
        return database_members
    members: list[str] = []
    for root in profile["source_roots"]:
        for path in _iter_files(root, profile["build_dir"]):
            if path.suffix.lower() in profile["source_extensions"]:
                members.append(_display(path.resolve(strict=False)))
    return sorted(set(members))


def _latest_file_api_inputs(build_dir: Path) -> list[Path]:
    reply_dir = build_dir / ".cmake" / "api" / "v1" / "reply"
    if not reply_dir.is_dir():
        return []
    indexes = sorted(reply_dir.glob("index-*.json"), key=lambda item: item.stat().st_mtime_ns, reverse=True)
    if not indexes:
        return []
    try:
        index = _read_json(indexes[0], "CMake File API reply index")
    except GuardError:
        return []
    if not isinstance(index, dict):
        return []
    result: list[Path] = []
    for obj in index.get("objects", []):
        if not isinstance(obj, dict) or obj.get("kind") != "cmakeFiles":
            continue
        filename = obj.get("jsonFile") or obj.get("json_file") or obj.get("file")
        if not isinstance(filename, str):
            continue
        object_path = reply_dir / filename
        try:
            data = _read_json(object_path, "CMake File API cmakeFiles reply")
        except GuardError:
            continue
        if not isinstance(data, dict):
            continue
        # CMake's cmakeFiles object has a path map for the source/build roots
        # and an `inputs` array for actual files. Relative input paths are
        # relative to the source root, not the build root. Skip only CMake's
        # own modules (`isCMake`), not every `isExternal` file: external
        # toolchains and vendor .cmake files can be real project inputs.
        paths = data.get("paths", {})
        source_root = build_dir
        if isinstance(paths, dict) and isinstance(paths.get("source"), str):
            source_root = _path(paths["source"], build_dir)
        for item in data.get("inputs", []):
            if not isinstance(item, dict) or item.get("isCMake") or item.get("isGenerated"):
                continue
            value = item.get("path")
            if isinstance(value, str) and value:
                result.append(_path(value, source_root if not Path(value).is_absolute() else build_dir))
    return result


def _ensure_file_api_query(build_dir: Path) -> None:
    query = build_dir / ".cmake" / "api" / "v1" / "query" / "client-clangd-guard" / "cmakeFiles-v1"
    try:
        query.parent.mkdir(parents=True, exist_ok=True)
        query.touch(exist_ok=True)
    except OSError as exc:
        raise GuardError(f"cannot create CMake File API query: {_display(query)}") from exc


def _load_state(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    state = _read_json(path, "clangd-guard state")
    if not isinstance(state, dict) or state.get("version") != STATE_VERSION:
        raise GuardError(f"clangd-guard state is invalid: {_display(path)}")
    return state


def _current_inputs(profile: dict[str, Any], state: dict[str, Any] | None) -> list[Path]:
    paths = [profile["config_path"], *profile["configure_inputs"]]
    if state:
        paths.extend(Path(value) for value in state.get("configure_inputs", []))
    return list(dict.fromkeys(path.resolve(strict=False) for path in paths))


def _freshness(profile: dict[str, Any], state: dict[str, Any] | None) -> tuple[bool, str]:
    if state is None:
        return False, "no successful configure state exists"
    if state.get("project_root") != _display(profile["project_root"]):
        return False, "project root changed"
    if state.get("build_dir") != _display(profile["build_dir"]):
        return False, "build directory changed"
    try:
        database_digest, database_members = _database_members(profile["database"])
    except GuardError as exc:
        return False, str(exc)
    if database_digest == "<missing>":
        return False, "compile_commands.json is missing"
    if database_digest != state.get("database_sha256"):
        return False, "compile_commands.json changed or was replaced"
    if database_members != state.get("database_members", []):
        return False, "compile database source membership changed"
    cache_digest = _digest_file(profile["cache"])
    if cache_digest != state.get("cache_sha256", "<missing>"):
        return False, "CMakeCache.txt changed or was replaced"
    if _source_members(profile, database_members) != state.get("source_members", []):
        return False, "configured source membership changed"
    current_inputs = _input_fingerprints(_current_inputs(profile, state), profile["build_dir"])
    if current_inputs != state.get("input_fingerprints", {}):
        return False, "a tracked CMake/configure input changed"
    current_environment = _environment_fingerprints(profile["environment_variables"])
    if current_environment != state.get("environment_fingerprints", {}):
        return False, "a tracked configure environment variable changed"
    return True, "fresh"


class _ConfigureLock:
    def __init__(self, path: Path, timeout: float = 10.0) -> None:
        self.path = path
        self.timeout = timeout
        self.owned = False

    def __enter__(self) -> "_ConfigureLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                descriptor = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                    handle.write(f"pid={os.getpid()}\n")
                self.owned = True
                return self
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise GuardError(f"another configure is still running; lock timed out: {_display(self.path)}")
                time.sleep(0.05)
            except OSError as exc:
                raise GuardError(f"cannot acquire configure lock: {_display(self.path)}") from exc

    def __exit__(self, *_: object) -> None:
        if self.owned:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass


def _run_configure(profile: dict[str, Any], old_state: dict[str, Any] | None) -> dict[str, Any]:
    profile["build_dir"].mkdir(parents=True, exist_ok=True)
    _ensure_file_api_query(profile["build_dir"])
    with _ConfigureLock(profile["lock_path"]):
        latest_state = _load_state(profile["state_path"])
        fresh, _ = _freshness(profile, latest_state)
        if fresh:
            return latest_state or {}
        input_paths_before = _current_inputs(profile, latest_state or old_state)
        input_fingerprints_before = _input_fingerprints(input_paths_before, profile["build_dir"])
        try:
            completed = subprocess.run(
                profile["configure_command"],
                cwd=str(profile["configure_cwd"]),
                env=os.environ.copy(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=profile["configure_timeout"],
                shell=False,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise GuardError(
                f"configure timed out after {profile['configure_timeout']:g}s; old compile database remains blocked"
            ) from exc
        except OSError as exc:
            raise GuardError(f"could not start configure command: {exc}") from exc
        if completed.returncode != 0:
            details = (completed.stderr or completed.stdout or "").strip()
            if len(details) > 1200:
                details = details[-1200:]
            suffix = f": {details}" if details else ""
            raise GuardError(f"configure failed with exit code {completed.returncode}{suffix}")

        input_fingerprints_after = _input_fingerprints(input_paths_before, profile["build_dir"])
        if input_fingerprints_after != input_fingerprints_before:
            raise GuardError("tracked configure inputs changed during configure; run the LSP again after changes settle")
        database_digest, database_members = _database_members(profile["database"])
        if database_digest == "<missing>":
            raise GuardError("configure succeeded but did not produce compile_commands.json")
        discovered = _latest_file_api_inputs(profile["build_dir"])
        all_inputs = list(dict.fromkeys([*input_paths_before, *discovered]))
        state = {
            "version": STATE_VERSION,
            "project_root": _display(profile["project_root"]),
            "build_dir": _display(profile["build_dir"]),
            "configure_inputs": [_display(path) for path in all_inputs],
            "input_fingerprints": _input_fingerprints(all_inputs, profile["build_dir"]),
            "environment_fingerprints": _environment_fingerprints(profile["environment_variables"]),
            "database_sha256": database_digest,
            "database_members": database_members,
            "cache_sha256": _digest_file(profile["cache"]),
            "source_members": _source_members(profile, database_members),
            "configured_at": time.time(),
        }
        _write_state(profile["state_path"], state)
        return state


def _write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=".state-", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            json.dump(state, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise GuardError(f"cannot atomically write guard state: {_display(path)}") from exc
    finally:
        if temporary and temporary.exists():
            try:
                temporary.unlink()
            except OSError:
                pass


def _deny(reason: str) -> int:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"dv-clangd-guard: {reason}",
                }
            }
        )
    )
    return 0


def main(stdin: str | None = None) -> int:
    raw = sys.stdin.read() if stdin is None else stdin
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise GuardError("hook input must be a JSON object")
        profile_raw, config_path, project_dir = _find_profile(payload)
        profile = _validate_profile(profile_raw, config_path, project_dir)
        state = _load_state(profile["state_path"])
        fresh, reason = _freshness(profile, state)
        if fresh:
            return 0
        if not profile["auto_configure"]:
            return _deny(f"LSP blocked: {reason}. Configure the selected build explicitly, then retry.")
        _run_configure(profile, state)
        fresh_after, reason_after = _freshness(profile, _load_state(profile["state_path"]))
        if not fresh_after:
            raise GuardError(f"configure completed but freshness validation failed: {reason_after}")
        return 0
    except GuardError as exc:
        # Expected policy failures are structured denies. A process crash or a
        # missing interpreter still exits non-zero and is blocked by
        # onFailure=block in the hook definition.
        return _deny(str(exc))
    except Exception as exc:  # onFailure=block handles a crash or missing interpreter too.
        print(f"dv-clangd-guard blocked the LSP: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
