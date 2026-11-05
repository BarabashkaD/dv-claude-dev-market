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


PLUGIN_VERSION = "0.3.0"
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
    version = profile.get("version")
    if version not in (1, 2):
        raise GuardError("clangd-guard profile must set version to 1 or 2")
    if version == 2:
        if "projectRoot" in profile:
            raise GuardError("v2 uses workspaceRoot and cmakeSourceRoot, not projectRoot")
        for key in ("workspaceRoot", "cmakeSourceRoot", "configuration"):
            if not isinstance(profile.get(key), str) or not profile[key].strip():
                raise GuardError(f"v2 requires an explicit {key}")
    elif any(key in profile for key in ("workspaceRoot", "cmakeSourceRoot", "configuration", "excludedSources")):
        raise GuardError("workspace/configuration fields require profile version 2")
    root = _path(str(profile.get("workspaceRoot" if version == 2 else "projectRoot", ".")), config_path.parent)
    cmake_root = _path(profile["cmakeSourceRoot"], root) if version == 2 else root
    configuration = profile.get("configuration") if version == 2 else None
    if not cmake_root.is_dir() or not cmake_root.is_relative_to(root):
        raise GuardError("cmakeSourceRoot must be an existing directory within workspaceRoot")
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

    if version == 2 and not TRANSLATION_UNIT_EXTENSIONS.issubset(extensions):
        raise GuardError("v2 sourceExtensions must include every supported translation-unit extension; use reviewed excludedSources instead")

    resolved_source_roots = [_path(value, root) for value in source_roots]
    exclusions: dict[str, str] = {}
    if version == 2:
        if any(not path.is_dir() or not path.is_relative_to(root) for path in resolved_source_roots):
            raise GuardError("v2 sourceRoots must be existing directories within workspaceRoot")
        if any(path == build_dir or path.is_relative_to(build_dir) for path in resolved_source_roots):
            raise GuardError("sourceRoots must not be inside the selected build directory")
        excluded_sources = profile.get("excludedSources", [])
        if not isinstance(excluded_sources, list):
            raise GuardError("excludedSources must be a list of exact paths and reasons")
        for item in excluded_sources:
            if not isinstance(item, dict) or set(item) != {"path", "reason"}:
                raise GuardError("each excludedSources entry must contain only path and reason")
            value, reason = item["path"], item["reason"]
            if not isinstance(value, str) or not value or any(char in value for char in "*?[]"):
                raise GuardError("excludedSources paths must be exact paths, not globs")
            if not isinstance(reason, str) or not reason.strip():
                raise GuardError("each excluded source needs a non-empty configuration-specific reason")
            path = _path(value, root)
            if path.suffix.lower() not in TRANSLATION_UNIT_EXTENSIONS or not any(path.is_relative_to(src) for src in resolved_source_roots):
                raise GuardError("excludedSources must name translation units within sourceRoots")
            key = _display(path)
            if key in exclusions:
                raise GuardError(f"duplicate excluded source: {key}")
            exclusions[key] = reason.strip()

    state_dir = build_dir / ".clangd-guard"
    return {
        "profile": profile,
        "profile_version": version,
        "cmake_source_root": cmake_root,
        "configuration": configuration,
        "excluded_sources": exclusions,
        "config_path": config_path.resolve(strict=False),
        "project_dir": project_dir,
        "project_root": root,
        "build_dir": build_dir,
        "database": build_dir / "compile_commands.json",
        "cache": build_dir / "CMakeCache.txt",
        "trust_path": _trust_path(config_path),
        "state_dir": state_dir,
        "state_path": state_dir / "state.json",
        "lock_path": state_dir / "configure.lock",
        "auto_configure": auto_configure,
        "configure_command": command,
        "configure_cwd": configure_cwd,
        "configure_timeout": float(timeout),
        "configure_inputs": [_path(value, root) for value in inputs],
        "environment_variables": environment,
        "source_roots": resolved_source_roots,
        "source_extensions": set(extensions),
    }


def _trust_path(config_path: Path) -> Path:
    """Return a per-user approval path, never a path controlled by the repo."""
    configured_state = os.environ.get("CLANGD_GUARD_STATE_DIR")
    if configured_state:
        state_root = _path(configured_state, Path.cwd())
    elif os.name == "nt":
        state_root = _path(os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local"), Path.cwd())
    elif sys.platform == "darwin":
        state_root = Path.home() / "Library" / "Application Support"
    else:
        state_root = _path(os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state"), Path.cwd())
    key = hashlib.sha256(str(config_path.resolve(strict=False)).encode("utf-8")).hexdigest()
    return state_root / "dv-clangd-guard" / "trust" / f"{key}.json"


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
    exclusions = profile["excluded_sources"]
    for member in exclusions:
        if not Path(member).is_file():
            return f"excluded source no longer exists; review the profile: {member}"
        if member in database_set:
            return f"excluded source is compiled in {profile['configuration']}; review the exclusion: {member}"
    missing = [
        member
        for member in _source_members(profile, database_members)
        if Path(member).suffix.lower() in TRANSLATION_UNIT_EXTENSIONS and member not in database_set and member not in exclusions
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
    if cache_home != profile["cmake_source_root"]:
        raise GuardError(
            "selected build is not configured for the selected CMake source root; "
            "run the configured CMake command or choose the matching build directory"
        )
    if profile["profile_version"] == 2:
        cache = profile["cache"].read_text(encoding="utf-8", errors="replace")
        values = {}
        for line in cache.splitlines():
            if not line.startswith(("#", "//")) and ":" in line and "=" in line:
                key, value = line.split("=", 1)
                values[key.split(":", 1)[0]] = value
        if values.get("CMAKE_CONFIGURATION_TYPES"):
            raise GuardError("v2 requires a single-configuration build/database; use a separate Ninja build per configuration")
        if values.get("CMAKE_BUILD_TYPE") != profile["configuration"]:
            raise GuardError("selected build CMAKE_BUILD_TYPE does not match the approved configuration")
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
    if profile["profile_version"] == 2 and (
        state.get("cmake_source_root") != _display(profile["cmake_source_root"])
        or state.get("configuration") != profile["configuration"]
    ):
        return False, "CMake source root or selected configuration changed"
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


def _target_scope_reason(profile: dict[str, Any], targets: Iterable[Path]) -> str | None:
    if profile["profile_version"] != 2:
        return None
    for target in targets:
        if not target.is_relative_to(profile["project_root"]):
            return f"NOT VALIDATED: queried file is outside workspaceRoot: {_display(target)}"
        if not any(target.is_relative_to(root) for root in profile["source_roots"]):
            return f"NOT VALIDATED: queried file is outside approved sourceRoots: {_display(target)}"
        reason = profile["excluded_sources"].get(_display(target))
        if reason:
            return (
                f"NOT VALIDATED in {profile['configuration']}: {_display(target)} ({reason}). "
                "Use a matching configuration/database; this exclusion never permits an LSP query."
            )
    return None


def _target_membership_reason(targets: Iterable[Path], state: dict[str, Any] | None) -> str | None:
    """Require queried translation units to be represented in the fresh DB."""
    if state is None:
        return "no validated compile database exists for the queried translation unit"
    members = set(state.get("database_members", []))
    missing = [
        _display(target)
        for target in targets
        if target.suffix.lower() in TRANSLATION_UNIT_EXTENSIONS and _display(target) not in members
    ]
    if missing:
        return (
            "NOT VALIDATED: queried translation unit is not represented in the selected compile_commands.json: "
            + ", ".join(missing[:3])
        )
    return None


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
        input_paths = _current_inputs(profile, latest_state or old_state)
        deadline = time.monotonic() + profile["configure_timeout"]
        for attempt in range(2):
            input_fingerprints_before = _input_fingerprints(input_paths, profile["build_dir"])
            source_members_before = _source_members(profile, [])
            database_before = _digest_file(profile["database"])
            cache_before = _digest_file(profile["cache"])
            file_api_before = _file_api_index_digest(profile["build_dir"])
            configure_started_ns = time.time_ns()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise GuardError("configure budget was exhausted while discovering CMake inputs")
            try:
                completed = subprocess.run(
                    profile["configure_command"],
                    cwd=str(profile["configure_cwd"]),
                    env=os.environ.copy(),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=min(profile["configure_timeout"], remaining),
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

            input_fingerprints_after = _input_fingerprints(input_paths, profile["build_dir"])
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
            latest_index = _latest_file_api_index(profile["build_dir"])
            if (
                latest_index is None
                or (
                    database_digest == database_before
                    and cache_digest == cache_before
                    and file_api_digest == file_api_before
                    and latest_index.stat().st_mtime_ns < configure_started_ns
                )
            ):
                raise GuardError(
                    "configure did not produce fresh evidence for the selected build; "
                    "an old database cannot be blessed"
                )
            discovered = _latest_file_api_inputs(profile["build_dir"])
            discovered_set = {path.resolve(strict=False) for path in discovered}
            new_discovered = [path for path in discovered_set if path not in set(input_paths)]
            if new_discovered:
                if old_state or attempt:
                    raise GuardError(
                        "configure discovered a new File API input; add it to configureInputs and approve the profile before retrying"
                    )
                input_paths = list(dict.fromkeys([*input_paths, *sorted(new_discovered)]))
                continue
            all_inputs = list(dict.fromkeys([*input_paths, *discovered]))
            state = {
                "version": STATE_VERSION,
                "project_root": _display(profile["project_root"]),
                "cmake_source_root": _display(profile["cmake_source_root"]),
                "configuration": profile["configuration"],
                "excluded_sources": profile["excluded_sources"],
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
        raise GuardError("configure did not produce a stable CMake input set")


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


def _sample(items: list[Any], limit: int) -> dict[str, Any]:
    """Bound report detail without truncating counts or altering validation."""
    return {"total": len(items), "items": items[:limit], "omitted": max(0, len(items) - limit)}


def diagnose(project_dir: str, limit: int = 20) -> tuple[dict[str, Any], int]:
    """Inspect only. Never configure, approve, lock, create queries, or write state.

    This is an observation, not a hook decision or live clangd attestation.
    Reads are not an atomic filesystem snapshot; concurrent changes can race it.
    """
    report: dict[str, Any] = {
        "reportVersion": 1, "pluginVersion": PLUGIN_VERSION,
        "hookPath": str(Path(__file__).resolve()), "readOnly": True,
        "status": "inspection_complete", "checks": {},
        "limitations": [
            "Not a hook allow decision; queried-file scope and membership still apply.",
            "Does not prove this hook is registered or that live clangd loaded this database or a particular command.",
            "Not an atomic snapshot; rerun after concurrent configure or file changes settle.",
            "Paths and exclusion reasons may contain private project details; review before sharing.",
        ],
    }
    checks = report["checks"]
    payload = {"cwd": project_dir, "project_directory": project_dir}
    try:
        raw, config_path, selected_dir = _find_profile(payload)
    except GuardError as exc:
        missing = str(exc).startswith("No explicit .clangd-guard.json")
        checks["profile"] = {"status": "missing" if missing else "invalid", "reason": str(exc)}
        report["status"] = "profile_unavailable"
        return report, 1
    try:
        profile = _validate_profile(raw, config_path, selected_dir)
    except GuardError as exc:
        checks["profile"] = {"status": "invalid", "path": str(config_path), "reason": str(exc)}
        report["status"] = "profile_unavailable"
        return report, 1
    checks["profile"] = {"status": "valid", "path": str(config_path), "version": profile["profile_version"]}
    report["scope"] = {
        "workspaceRoot": str(profile["project_root"]),
        "cmakeSourceRoot": str(profile["cmake_source_root"]),
        "buildDir": str(profile["build_dir"]),
        "configuration": profile["configuration"],
        "sourceRoots": _sample([str(p) for p in profile["source_roots"]], limit),
        "autoConfigure": profile["auto_configure"],
    }
    try:
        _require_trust(profile)
        checks["approval"] = {"status": "approved"}
    except GuardError:
        # Do not expose the per-user seal or its contents.
        checks["approval"] = {"status": "missing_or_invalid", "reason": "No matching approval seal for this profile."}
    state = None
    try:
        state = _load_state(profile["state_path"])
        checks["state"] = {"status": "present" if state is not None else "absent"}
    except GuardError as exc:
        checks["state"] = {"status": "invalid", "reason": str(exc)}
    try:
        _configuration_identity(profile)
        checks["configurationIdentity"] = {"status": "valid"}
    except GuardError as exc:
        checks["configurationIdentity"] = {
            "status": "not_configured" if not profile["cache"].is_file() else "invalid",
            "reason": str(exc),
        }
    report["coverage"] = {"status": "unavailable", "reason": "A readable, valid database is required for coverage comparison."}
    try:
        digest, members = _database_members(profile["database"])
        if digest == "<missing>":
            checks["database"] = {"status": "missing", "path": str(profile["database"])}
        else:
            entries = _read_json(profile["database"], "compile database")
            # Parse again for entry counts only, never emit commands/arguments.
            counts: dict[str, int] = {}
            for entry in entries:
                file_path = _path(entry["file"], Path(entry["directory"]))
                key = str(file_path)
                counts[key] = counts.get(key, 0) + 1
            duplicates = [{"path": key, "entries": count} for key, count in sorted(counts.items()) if count > 1]
            checks["database"] = {
                "status": "valid", "path": str(profile["database"]), "sha256": digest,
                "entries": len(entries), "uniqueFiles": len(members),
                "duplicateEntries": len(entries) - len(members),
                "filesWithMultipleCommands": _sample(duplicates, limit),
            }
            scanned = {p for p in _source_members(profile, members) if Path(p).suffix.lower() in TRANSLATION_UNIT_EXTENSIONS}
            member_set = set(members)
            exclusions = profile["excluded_sources"]
            missing = sorted(scanned - member_set - set(exclusions))
            stale = sorted(p for p in exclusions if p not in scanned or p in member_set)
            outside = sorted(p for p in members if not any(Path(p).is_relative_to(root) for root in profile["source_roots"]))
            in_build = sorted(p for p in members if Path(p).is_relative_to(profile["build_dir"]))
            non_tu = sorted(p for p in members if Path(p).suffix.lower() not in TRANSLATION_UNIT_EXTENSIONS)
            reason = _source_coverage(profile, members)
            report["coverage"] = {
                "status": "valid" if reason is None else "invalid", "reason": reason,
                "scannedTranslationUnits": len(scanned),
                "representedScannedTranslationUnits": len(scanned & member_set),
                "expectedTranslationUnits": len(scanned - set(exclusions)),
                "missingSources": _sample(missing, limit),
                "excludedSources": _sample([{"path": p, "reason": r} for p, r in sorted(exclusions.items())], limit),
                "staleExclusions": _sample(stale, limit),
                "databaseFilesOutsideSourceRoots": _sample(outside, limit),
                "databaseFilesInBuildDirectory": _sample(in_build, limit),
                "nonTranslationUnitDatabaseFiles": _sample(non_tu, limit),
                "note": "Categories can overlap. In-build paths are not proof of generation. Multiple commands do not prove clangd validates every variant.",
            }
    except (GuardError, KeyError, TypeError, ValueError) as exc:
        checks["database"] = {"status": "invalid", "reason": str(exc)}
    if checks["state"]["status"] == "invalid":
        checks["freshness"] = {"status": "unknown", "reason": "State is invalid; no freshness claim is possible."}
    else:
        try:
            fresh, reason = _freshness(profile, state)
            checks["freshness"] = {"status": "fresh" if fresh else "stale", "reason": reason}
        except GuardError as exc:
            checks["freshness"] = {"status": "unknown", "reason": str(exc)}
    return report, 0


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
        scope_reason = _target_scope_reason(profile, targets)
        if scope_reason:
            raise GuardError(scope_reason)
        if profile["profile_version"] == 1 and not any(target.is_relative_to(profile["project_root"]) for target in targets):
            return 0
        state = _load_state(profile["state_path"])
        fresh, reason = _freshness(profile, state)
        if fresh:
            target_reason = _target_membership_reason(targets, state)
            if target_reason:
                raise GuardError(target_reason)
            return 0
        if not profile["auto_configure"]:
            return _deny(f"LSP blocked: {reason}. Review and approve an autoConfigure profile so the guard can establish fresh state; manual configure or --approve alone cannot record freshness.")
        _require_trust(profile)
        _run_configure(profile, state)
        fresh_after, reason_after = _freshness(profile, _load_state(profile["state_path"]))
        if not fresh_after:
            raise GuardError(f"configure completed but freshness validation failed: {reason_after}")
        target_reason = _target_membership_reason(targets, _load_state(profile["state_path"]))
        if target_reason:
            raise GuardError(target_reason)
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
    parser = argparse.ArgumentParser(description="dv-clangd-guard hook and explicit profile approval helper")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--approve", action="store_true", help="approve the current profile for automatic configure")
    mode.add_argument("--diagnose", action="store_true", help="print a read-only JSON diagnostic report; never configure or approve")
    parser.add_argument("--detail-limit", type=int, default=20, help="maximum items per diagnostic detail list (1-100; default 20)")
    parser.add_argument("--project-dir", default=os.getcwd(), help="project directory containing the profile")
    parser.add_argument("--config", help="explicit .clangd-guard.json path")
    args = parser.parse_args()
    if args.diagnose:
        if not 1 <= args.detail_limit <= 100:
            parser.error("--detail-limit must be between 1 and 100")
        if args.config:
            os.environ["CLANGD_GUARD_CONFIG"] = args.config
        try:
            report, code = diagnose(args.project_dir, args.detail_limit)
            print(json.dumps(report, indent=2, sort_keys=True))
            raise SystemExit(code)
        except Exception:
            # Avoid echoing command arguments or environment values from exceptions.
            print(json.dumps({"reportVersion": 1, "pluginVersion": PLUGIN_VERSION,
                              "readOnly": True, "status": "inspection_error",
                              "reason": "Inspection failed; check file access and concurrent changes."}))
            raise SystemExit(2)
    if args.approve:
        if args.config:
            os.environ["CLANGD_GUARD_CONFIG"] = args.config
        try:
            payload = {"cwd": args.project_dir, "project_directory": args.project_dir}
            profile_raw, config_path, project_dir = _find_profile(payload)
            profile = _validate_profile(profile_raw, config_path, project_dir)
            _approve_profile(profile)
            print(f"Approved profile: {_display(profile['config_path'])}")
            raise SystemExit(0)
        except Exception as exc:
            print(f"dv-clangd-guard setup failed: {exc}", file=sys.stderr)
            raise SystemExit(1)
    raise SystemExit(main())
