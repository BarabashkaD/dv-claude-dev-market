# Validation scope

Status: 2.0.0 is an evolving, incomplete skill collection. Static checks, shell and unit tests, a limited GUI smoke run and headless API checks are listed below. Live modelling rounds and Bambu Studio runs were not performed.

## 2.0.0 checks

Static and automated:

- Repository checks `check_plugins` (manifests, catalogs, versions, frontmatter) and `check_public` (public-data scan) pass, in CI mode and with a private denylist and allowlists.
- `pytest` over the repository tools and the skill tests, including the GUI-macro template tests.
- A shell test of the quiet wrapper `fc-quiet.sh`.
- `claude plugin validate` for both plugins and for the repository marketplace.
- Both plugin manifests and both catalogs parse, and versions match across the Codex manifest, the Claude manifest and the Claude catalog.

GUI smoke runs (controller-run, FreeCAD 1.1.4 on macOS, one at a time, on a temporary copy of the user profile): the GUI-macro template ran on an empty document and on a document with a Box and an `App::Link`. Both runs reported `ok: true`, wrote the PNG, the process exited by itself in about 4 s, and the input file was unchanged.

Headless API checks done while authoring: `UnifySameDomain` with `keepShapes`, `limitTolerance`, and the section example on a small prismatic part.

## Not qualified

- Live modelling rounds with the skills, or with the worker agent.
- Bambu Studio import, slicing, layer review and printer dispatch.
- Inputs with `XLink` references.
- Large or BSpline-heavy bodies.
- GUI runs on Linux or Windows.
- Native Desktop/Codex installation and live plugin discovery.
- Physical fit, strength, life or cooling tests.

Documentation and template checks are not execution qualification. No runtime compatibility or physical-performance PASS is claimed.

## Earlier releases

1.3.0 was a documentation update checked by JSON parsing, matching versions and manual workflow walkthroughs. 1.2.0 packaging checks covered manifests, frontmatter, relative links, PNG decoding, the retained Apache-2.0 LICENSE and a manual privacy review; the Claude CLI validation of the legacy marketplace passed. Source documentation links have not all been revalidated.
