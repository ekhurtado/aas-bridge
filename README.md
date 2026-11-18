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
- English and Spanish CLI output.

The distribution and the CLI command are `aas-bridge`; the importable package is
`aas_bridge` under `src/aas_bridge/` (a hyphen is not valid in a Python import
name). The cache directory and `AASBRIDGE_CACHE_DIR` keep their historical names.

## Requirements

- Python 3.11 or newer.
- Network access on the first migration of a new file: the gate installs the
  source-dialect basyx to build the baseline. Baselines are cached, so repeated
  migrations of the same file are offline.

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
aas-bridge --version
aas-bridge check <file.aasx> [--lang {en,es}]
aas-bridge migrate <file.aasx> [--lang {en,es}] [--report <path>]
```

`--lang` defaults to the system locale when it is English or Spanish, otherwise
English. Exit codes:

| Code | Meaning |
|---|---|
| `0` | Success, including "already AAS 3.1 — no migration needed" |
| `1` | User/input error (missing file, not an AASX, undetectable version, JSON parts) |
| `2` | Usage error |
| `3` | Evidence-gate failure |
| `4` | Internal error |

Examples:

```bash
aas-bridge check machine.aasx --lang es
aas-bridge migrate machine.aasx --report machine.report.json
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

## Development

```bash
python -m pytest -m "not integration"   # offline unit suite
python -m pytest                        # includes the corpus gate (swaps basyx)
ruff check .
ruff format --check .
python -m build
mypy src/aas_bridge                    # optional
```

The `aas_v3-0/` and `aas_v3-1/` folders are read-only corpus fixtures; tests copy
them to temporary directories before touching them.

## Licence

GPL-3.0-only. See `LICENSE`.
