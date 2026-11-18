---
name: python-testing
description: >
  Use when adding or changing pytest tests, fixtures, corpus regression, integration markers or
  golden reports. Do NOT use for package I/O implementation (use aasx-core) or running declared
  checks only (use verification-gate).
version: 1.0.0
consumers:
  - code-executor
---

# Python Testing

## Activation Criteria

- **Applies when:** adding or changing unit/integration tests, fixtures, corpus regression,
  golden JSON reports or test configuration for AAS Bridge.
- **Does NOT apply when:** implementing the code under test (`aasx-core`,
  `basyx-evidence-gate`, `nicegui-frontend`) or running the declared checks only
  (`verification-gate`).

## Environment & Prerequisites

- Read `.ai/CONVENTIONS.md` §4, the SPEC's test/verification sections, `pyproject.toml` (once it
  exists) and the corpus layout (`aas_v3-0/`, `aas_v3-1/`).
- `pytest` is installed (local 9.1.1); `pytest-cov`/`pytest-asyncio` only if the SPEC declares
  them.
- Fixtures live under `tests/fixtures/`; the corpus folders are read-only.

## Technical Guidelines & Best Practices

1. **Unit tests are fast and hermetic.** No network, no Docker, no real subprocess; use
   `tmp_path` and small in-memory fixtures.
2. **Integration tests are marked.** `@pytest.mark.integration`; they may use an ephemeral venv
   or a subprocess. Network tests are separately marked `@pytest.mark.network` and never run in
   the default suite.
3. **Corpus regression.** The 6 AASX files are fixtures; expected counts/IDs live in tests, not
   in the corpus. Never mutate the corpus.
4. **Golden reports.** Deterministic JSON under `tests/fixtures/golden/`; compare parsed JSON,
   not raw bytes, unless the SPEC says otherwise.
5. **One behaviour per test.** Name it after the behaviour: `test_detects_prefixed_v31_namespace`.
6. **Determinism.** Sort collections, freeze dates, avoid real clocks/network/randomness; use
   fixed seeds if randomness is unavoidable.
7. **Edge cases first.** Test the failure paths: corrupt package, missing declaration, gate
   mismatch, offline probe, invalid UI input.
8. **Coverage of the contract.** Detection, transformation, gate, CLI output, UI core and i18n
   keys; do not chase a percentage.
9. **Windows-safe.** Use `pathlib`, handle CRLF/encoding, avoid POSIX-only assertions.
10. **No flaky sleeps.** Use events/timeouts; mark a genuinely slow test `integration`.

## Execution Workflow

1. **Inspect:** identify the behaviour and the SPEC's verification; find the closest existing
   test/fixture; decide unit vs integration; list the positive and negative cases.
2. **Execute:** write the failing test first; add the smallest fixture; implement only test code
   (the executor implements the production code); run the focused test.
3. **Verify:** run `python -m pytest` (or the declared focused command); confirm no network in
   unit tests; confirm the fixture is unchanged; check determinism by re-running; add the golden
   report if required.

## Edge Cases & Resilience

- **Binary/large fixtures:** keep them under `tests/fixtures/`; do not copy the corpus; use
  hashes for identity.
- **Encoding/BOM:** test both UTF-8 and BOM cases explicitly.
- **Time/date:** inject a clock or freeze the value; never assert `now()`.
- **Network:** mark `network`; mock the client for unit tests.
- **Docker:** mark `integration` and skip with a reason when Docker is unavailable.
- **Flaky test:** fix the race or mark `integration`; never add a bare `sleep`.

## Error Prevention & Anti-Patterns

- ⚠️ **Network in unit tests:** a probe that hits PyPI in the default suite.
  ✔️ Mock it or mark `network`; keep the default suite offline.
- ⚠️ **Mutating fixtures:** writing into `aas_v3-0/`/`aas_v3-1/`.
  ✔️ Copy to `tmp_path`; treat the corpus as read-only.
- ⚠️ **Asserting implementation details:** testing a private helper instead of the contract.
  ✔️ Test the public behaviour and the observable output.
- ⚠️ **Flaky tests:** `time.sleep` and order-dependent assertions.
  ✔️ Use events, deterministic ordering and isolation.
- ⚠️ **Skipping without a reason:** `@pytest.mark.skip`.
  ✔️ Add `reason=` and, when conditional, a marker with a clear condition.
