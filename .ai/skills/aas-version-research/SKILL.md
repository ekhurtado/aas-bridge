---
name: aas-version-research
description: >
  Use when a plan depends on AAS/basyx/PE/SMIA version facts, a new release, a compatibility
  claim or an ECOSYSTEM_COMPATIBILITY.md update. Do NOT use for general library API docs
  (use context7/web docs) or for implementing the fact (use code-executor).
version: 1.0.0
consumers:
  - architect
---

# AAS Version Research

## Activation Criteria

- **Applies when:** a SPEC, decision or diagnosis depends on an AAS metamodel version, a
  basyx/PE/SMIA release, a compatibility claim, a corpus baseline or a new IDTA artifact.
- **Does NOT apply when:** the task is general library API documentation (use context7/web), or
  the implementation of a version fact (the executor; use `aasx-core`/`basyx-evidence-gate`).

## Environment & Prerequisites

- Read `.ai/ECOSYSTEM_COMPATIBILITY.md` (the evidence ledger), `.ai/ARCHITECTURE.md` §3 and the
  relevant decisions in `.ai/history/DECISIONS.md`.
- Official sources: IDTA AAS specifications/change notes, `eclipse-basyx/basyx-python-sdk`
  releases, `eclipse-aaspe/package-explorer` releases, PyPI JSON for SMIA.
- Optional empirical probe: an ephemeral venv with the target basyx version; the corpus folders
  are read-only fixtures.
- Network access may be unavailable; the skill must work offline with the vendored evidence.

## Technical Guidelines & Best Practices

1. **Evidence over documentation.** A claim is only accepted if it traces to a probe, a corpus
   test or an official source with a date.
2. **Date every fact.** Record the fetch/probe date next to the row or bullet.
3. **Official + empirical.** Prefer the official matrix, then corroborate with a local probe when
   the fact affects implementation (e.g. `NS_AAS` dialect).
4. **Distinguish declarations from versioned IRIs.** The AASX payload declares its version in
   `xmlns`; external IRIs such as IEC 61360 `.../3/0` are not declarations.
5. **Never delete evidence.** Supersede with a dated note; keep the history.
6. **Mark uncertainty.** Use `unverified` or `pending probe`; never present a
   guess as a fact.
7. **Keep the matrix small.** basyx↔AAS, PE↔AAS, SMIA latest and the corpus baselines are the
   core tables; link details to the source.
8. **Offline is a state, not a failure.** Use the vendored ledger, show that online features are
   degraded, and do not block the plan if the existing evidence suffices.

## Execution Workflow

1. **Inspect:** state the exact question (which version, which tool, which pair, which document);
   search the existing evidence by table/ID; decide whether a probe or a fetch is needed.
2. **Execute:** fetch the official source or run the probe; capture the exact version/date;
   compare with the existing row; update the matrix or add a dated note; record the source URL.
3. **Verify:** cross-check the probe against the official claim; if they conflict, keep both,
   explain the conflict and prefer the probe for runtime decisions. Link the fact to the SPEC or
   decision that depends on it. Confirm no evidence was deleted.

## Edge Cases & Resilience

- **Conflicting sources:** record both, state which wins and why (probe > release notes).
- **Network unavailable:** use the vendored evidence and mark the online check as degraded.
- **Version not installed / probe fails:** mark `unverified`; do not infer the dialect.
- **Release notes are ambiguous:** run the probe or leave the fact out of the SPEC.
- **New AAS version:** record the IDTA changelog `nc` column; a non-additive change becomes a
  blocking rule candidate, never an automatic relabel.

## Error Prevention & Anti-Patterns

- ⚠️ **Memory-based fact:** “basyx 2.2 reads 3.0” without evidence.
  ✔️ Probe or cite the official source with a date.
- ⚠️ **Scraping release notes as truth:** treating a changelog summary as the runtime behaviour.
  ✔️ Corroborate with the probe.
- ⚠️ **Hardcoding `NS_AAS`:** copying the namespace into the design or code.
  ✔️ Import it from the pinned basyx; record the dialect in the evidence ledger.
- ⚠️ **Deleting evidence:** removing an outdated row.
  ✔️ Supersede it with a dated note.
- ⚠️ **Undated claim:** a matrix row without a source/date.
  ✔️ Add the source and date or mark it `unverified`.
