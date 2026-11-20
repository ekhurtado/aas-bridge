# AAS Bridge

AAS Bridge detects, diagnoses and migrates AASX packages across AAS metamodel
versions, and proves every migration with an evidence gate. It targets the
failure mode where an AASX file authored by another toolchain generation loads
as an empty object store, silently: the tool names the version mismatch, applies
the approved transformation, and refuses to emit a file it cannot prove.

Phase 1 ships the headless core and the command-line interface:

- version detection for AAS 3.0 and 3.1 packages from XML namespace
  declarations (both `xmlns="..."` and `xmlns:aas="..."` forms);
- JSON AAS parts are detect-only via a top-level `@context`;
- the V3.0 → V3.1 upgrade as a namespace-declaration relabel with a
  byte-preserving OPC/ZIP rebuild;
- an evidence gate that loads the original with the source-dialect basyx
  (`basyx-python-sdk==2.0.1`), transforms, loads the adapted file with the target
  dialect (`basyx-python-sdk~=2.2`) and compares object counts, identifiers and
  semanticIds before and after a round-trip;
- a stable JSON migration report (`schema_version: 1`);
- English and Spanish CLI output;
- `smia`: guidance for the SMIA release you run (installed metadata, verified
  table, PyPI probe) and an honest per-file verdict;
- `update`: official AAS release check plus download of the pinned metamodel
  artifacts with a deterministic `manifest.json`;
- an interactive shell (bare `aas-bridge`) with session language selection.

The distribution and the CLI command are `aas-bridge`; the importable package is
`aas_bridge` under `src/aas_bridge/` (a hyphen is not valid in a Python import
name). The cache directory and `AASBRIDGE_CACHE_DIR` keep their historical names.

Current release: **0.2.0** (`aas-bridge --version`).

## Requirements

- Python 3.11 or newer.
- Network access on the first migration of a new file: the gate installs the
  source-dialect basyx to build the baseline. Baselines are cached, so repeated
  migrations of the same file are offline.
- Network access is optional for `smia` (the PyPI probe) and `update` (the
  official release check and artifact download); both degrade visibly offline.
  `check`, `migrate` and the installed-SMIA guidance work fully offline.

## Install

```bash
pip install -e .
```

Development extras (tests, lint, type checking, build):

```bash
pip install -e ".[dev]"
```

## Usage

```bash
aas-bridge                     # opens the interactive shell
aas-bridge shell               # explicit alias of the shell
aas-bridge --version
aas-bridge check <file.aasx> [--lang {en,es}]
aas-bridge migrate <file.aasx> [--lang {en,es}] [--report <path>]
aas-bridge smia [file.aasx] [--lang {en,es}]
aas-bridge update [--lang {en,es}]
```

`--lang` defaults to the system locale when it is English or Spanish, otherwise
English. Exit codes:

| Code | Meaning |
|---|---|
| `0` | Success, including "already AAS 3.1 — no migration needed" and the offline `update` state |
| `1` | User/input error (missing file, not an AASX, undetectable version, JSON parts) |
| `2` | Usage error |
| `3` | Evidence-gate failure |
| `4` | Internal error |

`smia` exits `0` whenever it produces a diagnosis (including the visible
`unverified` state) and `1` only for a missing or undetectable file. `update`
exits `0` when it ran, including the degraded offline state; check and fetch
failures are per-item statuses, not process failures. The shell always exits `0`
on `exit`/`quit`, EOF or Ctrl+C; command failures print an error and the loop
continues.

Examples:

```bash
aas-bridge check machine.aasx --lang es
aas-bridge migrate machine.aasx --report machine.report.json
aas-bridge smia machine.aasx
aas-bridge update
```

A migrated package is written next to the input as `<name>-adapted.aasx`. The
input file is never modified. An input that already declares AAS 3.1 is a
first-class success: no output file, no gate run, exit code 0.

JSON AAS parts are out of scope for migration in this release: they are
detected, but `migrate` refuses them because the current gate cannot prove a
JSON rewrite (basyx ignores `@context`). `check` is a diagnosis command: it
exits 0 whenever it can report a version, including JSON packages (with a
detect-only note); `migrate` exits 1 for JSON parts.

## What the evidence gate guarantees

For every V3.0 → V3.1 migration, AAS Bridge:

1. loads the original with the source-dialect basyx and records the object
   counts (AAS / Submodels / ConceptDescriptions), a hash of the sorted
   identifiers and a hash of the sorted semanticIds; a baseline of 0 objects is a
   failure, never a success;
2. applies only the approved rule (`v3_0_to_v3_1/namespace-relabel`) and rebuilds
   the OPC/ZIP package copying every untouched part byte-for-byte;
3. loads the adapted package with the target dialect, verifies that the installed
   basyx reports the registry's target namespace, and re-serialises/re-loads the
   object store as a round-trip check;
4. emits the adapted file only when the target load reproduces the baseline and
   the round-trip succeeds. Otherwise the file is removed and the command exits
   with code 3.

The basyx swap happens in the project venv and is always restored to
`basyx-python-sdk~=2.2`; each basyx load runs in a subprocess, so the main
process never imports the SDK. Gate executions are serialized with a lock file
and baselines are cached under `AASBRIDGE_CACHE_DIR`
(`%LOCALAPPDATA%\aasbridge\cache` on Windows, `~/.cache/aasbridge` elsewhere).

## Interactive shell

Bare `aas-bridge` (or `aas-bridge shell`) opens a standard-library shell — no
extra dependency. The bilingual banner is shown only on entry; the prompt is
`aas-bridge> `. It supports the same commands plus session helpers:

```text
check <file>                        diagnose an AASX package
migrate <file> [--report <path>]    migrate with the evidence gate
smia [file]                         SMIA guidance and per-file verdict
update                              official release check + artifact fetch
lang [en|es]                        show or change the session language
version                             show the tool version
help [command]                      show the help
exit | quit                         leave the shell
```

Quote paths that contain spaces (`migrate "C:\dir with space\f.aasx"`); Windows
backslashes are preserved. A failing command prints its error and the shell keeps
running.

## SMIA guidance

`aas-bridge smia` resolves the SMIA release you run in this order:

1. the SMIA installed in the current environment (`importlib.metadata`; offline
   and authoritative — only this environment is inspected);
2. the verified registry table of ten PyPI releases (fetched 2026-11-19);
3. a per-version PyPI JSON probe, when the version is missing from the table;
4. `unverified` — printed visibly, exit code 0, with an actionable note.

When SMIA is not installed the command prompts for a version (Enter skips it).
The output shows the SMIA version, its `basyx-python-sdk` pin, the AAS versions
that pin can read (basyx 1.x/2.0.x → AAS 3.0; 2.1+ → AAS 3.1) and the
provenance. With a file it adds an honest verdict: compatible, upgrade with
`aas-bridge migrate`, "downgrade V3.1→V3.0 is not available yet (Phase 2)" plus
the AASX Package Explorer / SMIA-upgrade alternatives, or
undetectable/inconsistent (run `aas-bridge check`). `smia` never writes files.

## Official AAS releases (`update`)

`aas-bridge update` checks the GitHub Releases feed of
`admin-shell-io/aas-specs-metamodel` (dated and machine-readable), classifies the
AAS lines (covered, known but uncovered, and **NEW** non-prerelease lines), fetches
the pinned metamodel artifacts and writes a deterministic `manifest.json`.

| AAS line | Tag | Artifacts |
|---|---|---|
| 3.0 | `IDTA-01001-3-0-1_schemasV3.0.9` (2024-11-15) | XSD + JSON Schema |
| 3.1 | `v3.1.2` (2025-11-10) | XSD + JSON Schema + changelog |

The metamodel schemas are fetched for every line; the 3.0 line publishes no
documentation folder, so its changelog does not exist at the pinned tag (verified
2026-11-19; ISS-014). Artifacts land under `AASBRIDGE_REGISTRY_DIR`
(`%LOCALAPPDATA%\aasbridge\registry` on Windows,
`~/.local/share/aasbridge/registry` elsewhere) as `<label>/<filename>`, with a
`manifest.json` recording URL, tag, sha256, size, ISO dates, per-item status,
CC-BY-4.0 licence and IDTA attribution.

Offline is a degraded state, not an error: the status is printed, the manifest is
still written with `online: false` and non-`fetched` statuses, and the command
exits 0. Fetching never creates or activates a migration rule (Phase 4): `update`
only writes the data directory.

## Development

```bash
python -m pytest -m "not integration"   # offline unit suite
python -m pytest                        # includes the corpus gate (swaps basyx)
python -m pytest -m network             # opt-in: real PyPI/GitHub probes
ruff check .
ruff format --check .
python -m build
mypy src/aas_bridge                    # optional
```

The `aas_v3-0/` and `aas_v3-1/` folders are read-only corpus fixtures; tests copy
them to temporary directories before touching them.

## Licence

GPL-3.0-only. See `LICENSE`.
