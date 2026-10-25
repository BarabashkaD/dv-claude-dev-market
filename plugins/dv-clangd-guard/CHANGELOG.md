# Changelog

## 0.2.0

- Add v2 profiles separating guarded `workspaceRoot` from `cmakeSourceRoot`.
- Match the selected single configuration against `CMAKE_BUILD_TYPE` and reject
  multi-config caches instead of implying every variant has been checked.
- Support exact, reviewed configuration exclusions with reasons while retaining
  filesystem membership tracking. Excluded-file queries report NOT VALIDATED;
  stale exclusions and new unclassified translation units fail closed.
- Deny v2 queries outside approved workspace/source roots, including mixed
  requests and headers. Preserve v1 behavior for existing single-root profiles.
- Document explicit migration, Windows wrapper input tracking, profile approval
  versus freshness, and configuration-specific validation.
- Add real multi-repository CMake/Ninja regression coverage and make legacy tests
  skip unavailable build tools cleanly rather than raising FileNotFoundError.

## 0.1.0

- Initial explicit CMake database freshness guard and setup skill.
