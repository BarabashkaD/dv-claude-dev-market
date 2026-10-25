#!/usr/bin/env python3
"""Guard explicit Claude LSP calls with a configured CMake freshness check.

The hook deliberately does not install clangd, delete indexes, guess a CMake
build directory, or use a shell.  A project profile opts into the exact
configure command and build tree that the user trusts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterable
from urllib.parse import unquote, urlparse


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
TRANSLATION_UNIT_EXTENSIONS = {".c", ".cc", ".cpp", ".cxx", ".m", ".mm"}
TARGET_PATH_KEYS = {"file", "filePath", "file_path", "path", "uri", "documentUri", "document_uri"}


class GuardError(RuntimeError):
    pass


def _path(value: str, base: Path) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base / candidate
    return candidate.resolve(strict=False)


def _display(path: Path) -> str:
    return str(path)


def _target_path(value: str, base: Path) -> Path | None:
    if value.startswith("file://"):
        parsed = urlparse(value)
        value = unquote(parsed.path)
        if len(value) >= 3 and value[0] == "/" and value[2] == ":":
            value = value[1:]
    candidate = Path(value)
    if not candidate.suffix.lower() in DEFAULT_EXTENSIONS:
        return None
    return _path(value, base)


def _payload_target_paths(value: Any, base: Path) -> Iterable[Path]:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in TARGET_PATH_KEYS and isinstance(item, str):
                target = _target_path(item, base)
                if target:
                    yield target
            elif isinstance(item, (dict, list)):
                yield from _payload_target_paths(item, base)
    elif isinstance(value, list):
        for item in value:
            yield from _payload_target_paths(item, base)


def _should_guard(payload: dict[str, Any]) -> bool:
    if payload.get("tool_name") != "LSP":
        return False
    base = _path(str(payload.get("cwd") or os.getcwd()), Path.cwd())
    return any(_payload_target_paths(payload.get("tool_input", {}), base))


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
            or any(not isinstance(part, str) or not part.strip() for part in command)
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
    if not source_roots:
        raise GuardError("sourceRoots must name bounded source directories; membership cannot be verified without them")
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
        "trust_path": config_path.parent / ".clangd-guard.trust.json",
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
    if not isinstance(entries, list) or not entries:
        raise GuardError(f"compile database must be a JSON array: {_display(database)}")
    members: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or not isinstance(entry.get("file"), str) or not entry["file"]:
            raise GuardError(f"compile database entry {index} has no file path: {_display(database)}")
        if not isinstance(entry.get("directory"), str) or not entry["directory"]:
            raise GuardError(f"compile database entry {index} has no directory: {_display(database)}")
        command = entry.get("command")
        arguments = entry.get("arguments")
        if isinstance(command, str):
            valid_command = bool(command.strip())
        else:
            valid_command = (
                isinstance(arguments, list)
                and bool(arguments)
                and all(isinstance(argument, str) and argument.strip() for argument in arguments)
            )
        if not valid_command:
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


def _source_coverage(profile: dict[str, Any], database_members: list[str]) -> str | None:
    if not profile["source_roots"]:
        return "sourceRoots must be configured to verify translation-unit membership"
    database_set = set(database_members)
    missing = [
        member
        for member in _source_members(profile, database_members)
        if Path(member).suffix.lower() in TRANSLATION_UNIT_EXTENSIONS and member not in database_set
    ]
    if missing:
        preview = ", ".join(missing[:3])
        if len(missing) > 3:
            preview += ", ..."
        return f"translation units are absent from compile_commands.json: {preview}"
    return None


def _latest_file_api_index(build_dir: Path) -> Path | None:
    reply_dir = build_dir / ".cmake" / "api" / "v1" / "reply"
    if not reply_dir.is_dir():
        return None
    indexes = sorted(reply_dir.glob("index-*.json"), key=lambda item: item.stat().st_mtime_ns, reverse=True)
    return indexes[0] if indexes else None


def _file_api_index_digest(build_dir: Path) -> str:
    index = _latest_file_api_index(build_dir)
    return _digest_file(index) if index else "<missing>"


def _cache_home_directory(cache: Path) -> Path | None:
    if not cache.is_file():
        return None
    try:
        for line in cache.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("CMAKE_HOME_DIRECTORY:") and "=" in line:
                return Path(line.split("=", 1)[1]).resolve(strict=False)
    except OSError as exc:
        raise GuardError(f"cannot read CMake cache: {_display(cache)}") from exc
    return None


def _configuration_identity(profile: dict[str, Any]) -> tuple[str, str]:
    cache_home = _cache_home_directory(profile["cache"])
    if cache_home != profile["project_root"]:
        raise GuardError(
            "selected build is not configured for the selected projectRoot; "
            "run the configured CMake command or choose the matching build directory"
        )
    file_api_digest = _file_api_index_digest(profile["build_dir"])
    if file_api_digest == "<missing>":
        raise GuardError("selected build has no current CMake File API reply; configure it with the guard query present")
    return _digest_file(profile["cache"]), file_api_digest


def _latest_file_api_inputs(build_dir: Path) -> list[Path]:
    reply_dir = build_dir / ".cmake" / "api" / "v1" / "reply"
    index_path = _latest_file_api_index(build_dir)
    if not index_path:
        return []
    try:
        index = _read_json(index_path, "CMake File API reply index")
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
    try:
        cache_digest, file_api_digest = _configuration_identity(profile)
    except GuardError as exc:
        return False, str(exc)
    if cache_digest != state.get("cache_sha256"):
        return False, "CMakeCache.txt changed or was replaced"
    if file_api_digest != state.get("file_api_index_sha256"):
        return False, "CMake File API reply changed or was replaced"
    if _source_members(profile, database_members) != state.get("source_members", []):
        return False, "configured source membership changed"
    coverage_reason = _source_coverage(profile, database_members)
    if coverage_reason:
        return False, coverage_reason
    current_inputs = _input_fingerprints(_current_inputs(profile, state), profile["build_dir"])
    if current_inputs != state.get("input_fingerprints", {}):
        return False, "a tracked CMake/configure input changed"
    current_environment = _environment_fingerprints(profile["environment_variables"])
    if current_environment != state.get("environment_fingerprints", {}):
        return False, "a tracked configure environment variable changed"
    return True, "fresh"


def _profile_sha256(profile: dict[str, Any]) -> str:
    return _digest_file(profile["config_path"])


def _require_trust(profile: dict[str, Any]) -> None:
    trust_path = profile["trust_path"]
    try:
        trust = _read_json(trust_path, "clangd-guard approval seal")
    except GuardError as exc:
        raise GuardError(
            "autoConfigure is disabled until this profile is explicitly approved; "
            f"run the setup skill or --approve to create {_display(trust_path)}"
        ) from exc
    if not isinstance(trust, dict):
        raise GuardError(f"clangd-guard approval seal is invalid: {_display(trust_path)}")
    if (
        trust.get("version") != 1
        or trust.get("config_path") != _display(profile["config_path"])
        or trust.get("config_sha256") != _profile_sha256(profile)
    ):
        raise GuardError(
            "clangd-guard profile changed after approval; review it and run the setup approval step again"
        )


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
        source_members_before = _source_members(profile, [])
        database_before = _digest_file(profile["database"])
        cache_before = _digest_file(profile["cache"])
        file_api_before = _file_api_index_digest(profile["build_dir"])
        configure_started_ns = time.time_ns()
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
        source_members_after = _source_members(profile, database_members)
        if source_members_after != source_members_before:
            raise GuardError("source membership changed during configure; run the LSP again after changes settle")
        coverage_reason = _source_coverage(profile, database_members)
        if coverage_reason:
            raise GuardError(coverage_reason)
        cache_digest, file_api_digest = _configuration_identity(profile)
        if (
            database_digest == database_before
            and cache_digest == cache_before
            and file_api_digest == file_api_before
            and _latest_file_api_index(profile["build_dir"]).stat().st_mtime_ns < configure_started_ns
        ):
            raise GuardError(
                "configure did not produce fresh evidence for the selected build; "
                "an old database cannot be blessed"
            )
        discovered = _latest_file_api_inputs(profile["build_dir"])
        discovered_set = {path.resolve(strict=False) for path in discovered}
        if old_state and any(path not in set(input_paths_before) for path in discovered_set):
            raise GuardError(
                "configure discovered a new File API input; add it to configureInputs and approve the profile before retrying"
            )
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
            "cache_sha256": cache_digest,
            "file_api_index_sha256": file_api_digest,
            "source_members": _source_members(profile, database_members),
            "configured_at": time.time(),
        }
        _write_state(profile["state_path"], state)
        return state


def _record_manual_state(profile: dict[str, Any]) -> dict[str, Any]:
    """Record evidence after a user ran the configured build command manually."""
    if not profile["build_dir"].is_dir():
        raise GuardError(f"selected build directory is missing: {_display(profile['build_dir'])}")
    _ensure_file_api_query(profile["build_dir"])
    with _ConfigureLock(profile["lock_path"]):
        database_digest, database_members = _database_members(profile["database"])
        coverage_reason = _source_coverage(profile, database_members)
        if coverage_reason:
            raise GuardError(coverage_reason)
        cache_digest, file_api_digest = _configuration_identity(profile)
        discovered = _latest_file_api_inputs(profile["build_dir"])
        old_state = _load_state(profile["state_path"])
        all_inputs = list(dict.fromkeys([*_current_inputs(profile, old_state), *discovered]))
        state = {
            "version": STATE_VERSION,
            "project_root": _display(profile["project_root"]),
            "build_dir": _display(profile["build_dir"]),
            "configure_inputs": [_display(path) for path in all_inputs],
            "input_fingerprints": _input_fingerprints(all_inputs, profile["build_dir"]),
            "environment_fingerprints": _environment_fingerprints(profile["environment_variables"]),
            "database_sha256": database_digest,
            "database_members": database_members,
            "cache_sha256": cache_digest,
            "file_api_index_sha256": file_api_digest,
            "source_members": _source_members(profile, database_members),
            "configured_at": time.time(),
        }
        _write_state(profile["state_path"], state)
        return state


def _write_state(path: Path, state: dict[str, Any]) -> None:
    _write_json_atomic(path, state)


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=".state-", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            json.dump(value, handle, indent=2, sort_keys=True)
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


def _approve_profile(profile: dict[str, Any]) -> None:
    _write_json_atomic(
        profile["trust_path"],
        {
            "version": 1,
            "config_path": _display(profile["config_path"]),
            "config_sha256": _profile_sha256(profile),
            "approved_at": time.time(),
        },
    )


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
        if not _should_guard(payload):
            return 0
        profile_raw, config_path, project_dir = _find_profile(payload)
        profile = _validate_profile(profile_raw, config_path, project_dir)
        target_base = _path(str(payload.get("cwd") or os.getcwd()), Path.cwd())
        targets = list(_payload_target_paths(payload.get("tool_input", {}), target_base))
        if not any(target.is_relative_to(profile["project_root"]) for target in targets):
            return 0
        state = _load_state(profile["state_path"])
        fresh, reason = _freshness(profile, state)
        if fresh:
            return 0
        if not profile["auto_configure"]:
            return _deny(f"LSP blocked: {reason}. Configure the selected build explicitly, then retry.")
        _require_trust(profile)
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
    parser = argparse.ArgumentParser(description="dv-clangd-guard hook and explicit setup recovery helper")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--approve", action="store_true", help="approve the current profile for automatic configure")
    mode.add_argument("--record", action="store_true", help="record a manually configured build as fresh evidence")
    parser.add_argument("--project-dir", default=os.getcwd(), help="project directory containing the profile")
    parser.add_argument("--config", help="explicit .clangd-guard.json path")
    args = parser.parse_args()
    if args.approve or args.record:
        if args.config:
            os.environ["CLANGD_GUARD_CONFIG"] = args.config
        try:
            payload = {"cwd": args.project_dir, "project_directory": args.project_dir}
            profile_raw, config_path, project_dir = _find_profile(payload)
            profile = _validate_profile(profile_raw, config_path, project_dir)
            if args.approve:
                _approve_profile(profile)
                print(f"Approved profile: {_display(profile['config_path'])}")
            else:
                _record_manual_state(profile)
                print(f"Recorded fresh build evidence: {_display(profile['build_dir'])}")
            raise SystemExit(0)
        except Exception as exc:
            print(f"dv-clangd-guard setup failed: {exc}", file=sys.stderr)
            raise SystemExit(1)
    raise SystemExit(main())
