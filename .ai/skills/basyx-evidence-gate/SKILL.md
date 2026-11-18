---
name: basyx-evidence-gate
description: >
  Use when implementing or changing basyx probes or the evidence gate: ephemeral venv, dialect
  matrix, baseline/round-trip, emit-only-on-pass. Do NOT use for package transformation
  (use aasx-core) or test design (use python-testing).
version: 1.0.0
consumers:
  - code-executor
---

# basyx Evidence Gate

## Activation Criteria

- **Applies when:** implementing or changing `aasbridge/probes/`, `aasbridge/engine/gate.py`,
  the basyx dialect matrix, the baseline comparison, the round-trip or the emit-only-on-pass
  behaviour.
- **Does NOT apply when:** implementing package I/O (`aasx-core`), GUI (`nicegui-frontend`) or
  writing the test suite (`python-testing`).

## Environment & Prerequisites

- Read `.ai/ARCHITECTURE.md` §3, `.ai/ECOSYSTEM_COMPATIBILITY.md` §1 and §4,
  `.ai/CONVENTIONS.md` §4 and §7, and the SPEC's gate steps.
- basyx versions: source-dialect probe `basyx-python-sdk==2.0.1`, target `==2.2.0` (or the
  versions declared in the SPEC).
- An ephemeral venv per probe; the 6-file corpus is read-only.
- No network in unit tests; network/integration tests are marked.

## Technical Guidelines & Best Practices

1. **basyx is the only validator.** The gate loads with basyx; it never re-implements the
   metamodel.
2. **Probe the dialect, do not assume it.** In an ephemeral venv:
   `python -m venv <tmp>` → `pip install basyx-python-sdk==<version>` →
   `from basyx.aas.adapter.xml import xml_serialization; print(xml_serialization.NS_AAS)`.
   Cache the result with the version and date.
3. **Baseline first.** Load the original with the source-dialect basyx; record object counts,
   identifiers and semanticIds (sorted, deterministic).
4. **Target load + compare.** Load the adapted file with the target-dialect basyx; compare the
   baseline; a mismatch is a gate failure.
5. **Round-trip.** Re-read the adapted file after the target load; the second read must match.
6. **Emit only on pass.** A file that fails the baseline, the compare or the round-trip is not
   emitted; return the failure with evidence.
7. **Offline-degraded.** If the probe cannot run, use the cached matrix and show the offline
   state; never silently claim a live probe.
8. **No basyx modification.** Never patch, monkey-patch or vendor a modified basyx.
9. **Deterministic and bounded.** Sort IDs, use timeouts, clean the ephemeral venv, and avoid
   unbounded memory on large packages.
10. **Evidence record.** Every gate result includes the source/target versions, the baseline
    counts, the compare result and the round-trip result.

## Execution Workflow

1. **Inspect:** identify the source/target versions, the corpus file, the expected baseline and
   whether a cached probe exists. Confirm the input is readable and the target basyx is available.
2. **Execute:** create the ephemeral venv if needed; probe `NS_AAS`; load the original with the
   source dialect; capture the baseline; load the adapted file with the target dialect; compare;
   round-trip; record the result.
3. **Verify:** assert equal counts/IDs/semanticIds; assert the round-trip; assert the original
   input hash is unchanged; run the gate tests; record the exact commands and versions.

## Edge Cases & Resilience

- **Version not installable / no network:** use the cached matrix; mark the probe as offline.
- **basyx import changes:** probe `NS_AAS` from the installed version; fail with an actionable
  message if the import path moved.
- **Empty object store:** treat it as a mismatch; never as a successful load.
- **Timeout or memory pressure:** bound the run, clean up and report a gate error.
- **Windows paths:** use `pathlib` and short temp paths; clean the venv.
- **Corrupt input:** fail before the baseline; do not emit.

## Error Prevention & Anti-Patterns

- ⚠️ **Trusting the converter:** emitting the adapted file because PE/basyx "should" read it.
  ✔️ Prove it with the baseline + target load + round-trip.
- ⚠️ **No baseline:** comparing only the target load.
  ✔️ Capture the source-dialect baseline first.
- ⚠️ **Silent pass:** swallowing a mismatch.
  ✔️ Fail the gate and record the diff.
- ⚠️ **Hardcoded dialect:** a constant namespace in the code.
  ✔️ Import `NS_AAS` from the pinned basyx.
- ⚠️ **Network in unit tests:** a probe that requires PyPI.
  ✔️ Cache the matrix; keep network tests marked and optional.
